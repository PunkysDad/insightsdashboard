import json
from collections import Counter
from pathlib import Path

from fastapi import APIRouter, HTTPException

from insight_engine.engine import INSIGHTS_DIR

router = APIRouter()


def _load_all_insights() -> list[dict]:
    insights_dir: Path = INSIGHTS_DIR
    if not insights_dir.exists():
        return []

    items: list[dict] = []
    for path in insights_dir.glob("*.json"):
        try:
            items.append(json.loads(path.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    return items


@router.get("/dashboard/sessions")
def list_sessions() -> list[dict]:
    items = _load_all_insights()
    items.sort(key=lambda x: x.get("processed_at", ""), reverse=True)
    return items


@router.get("/dashboard/sessions/{session_id}")
def get_session(session_id: str) -> dict:
    path = INSIGHTS_DIR / f"{session_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Session insight not found")
    return json.loads(path.read_text())


@router.get("/dashboard/overview")
def overview() -> dict:
    items = _load_all_insights()

    intent_counter: Counter[str] = Counter()
    interest_counter: Counter[str] = Counter()
    sentiment_counter: Counter[str] = Counter()
    party_counter: Counter[str] = Counter()
    listings_counter: Counter[str] = Counter()
    gaps_counter: Counter[str] = Counter()
    unanswered_counter: Counter[str] = Counter()
    travel_windows: list[str] = []

    for item in items:
        if intent := item.get("visitor_intent"):
            intent_counter[intent] += 1
        if sentiment := item.get("sentiment"):
            sentiment_counter[sentiment] += 1
        if party := item.get("party_composition"):
            party_counter[party] += 1
        for interest in item.get("interests") or []:
            interest_counter[interest] += 1
        for listing in item.get("listings_referenced") or []:
            listings_counter[listing] += 1
        for gap in item.get("content_gaps") or []:
            gaps_counter[gap] += 1
        for question in item.get("unanswered_questions") or []:
            unanswered_counter[question] += 1
        if (window := item.get("travel_window")) is not None:
            travel_windows.append(window)

    def top_n(counter: Counter[str], key_name: str, n: int = 10) -> list[dict]:
        return [{key_name: name, "count": count} for name, count in counter.most_common(n)]

    return {
        "total_sessions": len(items),
        "intent_breakdown": dict(intent_counter),
        "interest_breakdown": dict(interest_counter),
        "sentiment_breakdown": dict(sentiment_counter),
        "party_breakdown": dict(party_counter),
        "top_listings": top_n(listings_counter, "name"),
        "top_content_gaps": top_n(gaps_counter, "gap"),
        "travel_windows": travel_windows,
        "top_unanswered": top_n(unanswered_counter, "question"),
    }
