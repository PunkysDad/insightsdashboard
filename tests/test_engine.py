import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from insight_engine.engine import DB_PATH, init_db, run


TEST_SESSION_ID = "test-session-abq-001"
TEST_CLIENT_ID = "visit-albuquerque"


def seed_test_session(db_path: Path) -> None:
    base = datetime.now(timezone.utc) - timedelta(minutes=10)
    ts = lambda offset: (base + timedelta(seconds=offset)).isoformat()

    messages = [
        ("user", "Hi! We're planning a trip to Albuquerque for my husband and me in late October. Any tips?", ts(0)),
        ("assistant", "Welcome! Late October is a wonderful time to visit Albuquerque — the Balloon Fiesta wraps up in early October but the weather stays mild. Are you interested in Old Town, hiking, or dining recommendations?", ts(30)),
        ("user", "Dining for sure. We love authentic New Mexican food. Any must-try spots?", ts(60)),
        ("assistant", "You can't go wrong with El Pinto for a classic experience, or Sadie's of New Mexico for green chile enthusiasts. Frontier Restaurant near UNM is a local institution for breakfast.", ts(90)),
        ("user", "Great. Also — is the Dia de los Muertos Marigold Parade happening this year and what's the exact date?", ts(120)),
        ("assistant", "I don't have confirmed dates for this year's Marigold Parade. I'd recommend checking the South Valley Muertos y Marigolds Facebook page for the most current schedule.", ts(150)),
    ]

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO sessions (session_id, client_id, started_at, status) VALUES (?, ?, ?, ?)",
            (TEST_SESSION_ID, TEST_CLIENT_ID, ts(0), "active"),
        )
        conn.executemany(
            "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            [(TEST_SESSION_ID, role, content, created_at) for role, content, created_at in messages],
        )
        conn.commit()
    finally:
        conn.close()


def cleanup_test_session(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("DELETE FROM messages WHERE session_id = ?", (TEST_SESSION_ID,))
        conn.execute("DELETE FROM sessions WHERE session_id = ?", (TEST_SESSION_ID,))
        conn.commit()
    finally:
        conn.close()


def main() -> None:
    load_dotenv()
    init_db()
    seed_test_session(DB_PATH)

    try:
        output_path = run(TEST_SESSION_ID)
        print("\n--- Insight JSON ---")
        print(output_path.read_text())
    finally:
        cleanup_test_session(DB_PATH)
        print("\n[test] cleaned up test session and messages")


if __name__ == "__main__":
    main()
