import json
import os
import pathlib
import sqlite3
from datetime import datetime, timezone

import anthropic
from dotenv import load_dotenv

load_dotenv()

MODELS = {
    "insight": "claude-haiku-4-5-20251001",
    "agent": "claude-haiku-4-5-20251001",
    "reporting": "claude-sonnet-4-6",
}

INSIGHTS_DIR = pathlib.Path("data/insights")
DB_PATH = pathlib.Path("db/destinationiq.db")
SCHEMA_PATH = pathlib.Path("db/schema.sql")

EXTRACTION_INSTRUCTIONS = """You are an analyst extracting structured insights from a visitor conversation with a destination assistant.

Conversation transcript:
{transcript}

Extract the following fields and return ONLY valid JSON. No markdown fences, no preamble, no commentary:

{{
  "visitor_intent": string — primary reason for the visit: trip_planning | on_site | general_browsing | event_research | group_travel | unknown,
  "travel_window": string — when they plan to visit, or null if not mentioned,
  "party_composition": string — solo | couple | family | group | unknown,
  "interests": list of strings — destination categories mentioned: dining | hotels | events | activities | nightlife | outdoors | shopping | arts | unknown,
  "listings_referenced": list of strings — specific venue/hotel/event names mentioned, empty list if none,
  "unanswered_questions": list of strings — questions the assistant could not answer confidently or deflected, empty list if none,
  "content_gaps": list of strings — topics the visitor asked about where the assistant lacked specific information, empty list if none,
  "sentiment": string — positive | neutral | negative | mixed,
  "session_summary": string — 2-3 sentence plain English summary of the conversation
}}"""


def init_db(db_path: pathlib.Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    schema_sql = SCHEMA_PATH.read_text()
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()


def load_transcript(session_id: str, db_path: pathlib.Path = DB_PATH) -> list[dict]:
    conn = sqlite3.connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT role, content, created_at FROM messages WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,),
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        raise ValueError(f"No messages found for session_id={session_id}")

    return [dict(row) for row in rows]


def build_extraction_prompt(transcript: list[dict]) -> str:
    formatted = "\n".join(f"{msg['role'].upper()}: {msg['content']}" for msg in transcript)
    return EXTRACTION_INSTRUCTIONS.format(transcript=formatted)


def extract_insights(session_id: str, db_path: pathlib.Path = DB_PATH) -> dict:
    transcript = load_transcript(session_id, db_path=db_path)
    prompt = build_extraction_prompt(transcript)

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODELS["insight"],
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.content[0].text

    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[-1]
    if raw_text.endswith("```"):
        raw_text = raw_text.rsplit("\n", 1)[0]
    raw_text = raw_text.strip()

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Failed to parse model response as JSON: {exc}. Raw response: {raw_text!r}"
        ) from exc

    parsed["session_id"] = session_id
    parsed["processed_at"] = datetime.now(timezone.utc).isoformat()
    return parsed


def write_insights(insights: dict, insights_dir: pathlib.Path = INSIGHTS_DIR) -> pathlib.Path:
    insights_dir.mkdir(parents=True, exist_ok=True)
    output_path = insights_dir / f"{insights['session_id']}.json"
    output_path.write_text(json.dumps(insights, indent=2))
    return output_path


def run(session_id: str) -> pathlib.Path:
    insights = extract_insights(session_id)
    output_path = write_insights(insights)
    print(f"[insight_engine] session {session_id} → {output_path}")
    return output_path
