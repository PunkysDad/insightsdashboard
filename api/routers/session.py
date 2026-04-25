import sqlite3
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent.rag import stream_response
from api.dependencies import get_db
from insight_engine.engine import DB_PATH, run as run_insight_engine

router = APIRouter()

SSE_MEDIA_TYPE = "text/event-stream"
SSE_DATA_PREFIX = "data: "
SSE_DONE_PAYLOAD = "[DONE]"


class StartSessionRequest(BaseModel):
    client_id: str


class MessageRequest(BaseModel):
    message: str
    conversation_history: list[dict] = []


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.post("/start")
def start_session(
    request: StartSessionRequest,
    db: sqlite3.Connection = Depends(get_db),
):
    session_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO sessions (session_id, client_id, started_at, status) VALUES (?, ?, ?, ?)",
        (session_id, request.client_id, _utcnow_iso(), "active"),
    )
    db.commit()
    return {"session_id": session_id, "client_id": request.client_id, "status": "active"}


@router.post("/{session_id}/message")
def send_message(
    session_id: str,
    request: MessageRequest,
    db: sqlite3.Connection = Depends(get_db),
):
    row = db.execute(
        "SELECT client_id, status FROM sessions WHERE session_id = ?",
        (session_id,),
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if row["status"] != "active":
        raise HTTPException(status_code=400, detail="Session is not active")

    client_id = row["client_id"]

    db.execute(
        "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
        (session_id, "user", request.message, _utcnow_iso()),
    )
    db.commit()

    async def event_stream():
        accumulated: list[str] = []
        async for chunk in stream_response(
            session_id, request.conversation_history, request.message, client_id
        ):
            yield chunk
            payload = chunk.removeprefix(SSE_DATA_PREFIX).rstrip("\n")
            if payload != SSE_DONE_PAYLOAD:
                accumulated.append(payload)

        full_text = "".join(accumulated)
        write_conn = sqlite3.connect(DB_PATH)
        try:
            write_conn.execute(
                "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (session_id, "assistant", full_text, _utcnow_iso()),
            )
            write_conn.commit()
        finally:
            write_conn.close()

    return StreamingResponse(event_stream(), media_type=SSE_MEDIA_TYPE)


@router.post("/{session_id}/close")
def close_session(
    session_id: str,
    background_tasks: BackgroundTasks,
    db: sqlite3.Connection = Depends(get_db),
):
    row = db.execute(
        "SELECT session_id FROM sessions WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")

    db.execute(
        "UPDATE sessions SET closed_at = ?, status = ? WHERE session_id = ?",
        (_utcnow_iso(), "closed", session_id),
    )
    db.commit()

    background_tasks.add_task(run_insight_engine, session_id)
    return {"session_id": session_id, "status": "closed", "insight_engine": "queued"}
