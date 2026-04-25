import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

BASE_URL = "http://localhost:8081"
INSIGHTS_DIR = Path("data/insights")
TEST_CLIENT_ID = "test-client-abq"
TEST_MESSAGE = "What are some authentic New Mexican restaurants in Albuquerque?"
INSIGHT_WAIT_SECONDS = 3


def main() -> None:
    start_resp = httpx.post(
        f"{BASE_URL}/session/start",
        json={"client_id": TEST_CLIENT_ID},
        timeout=10.0,
    )
    start_resp.raise_for_status()
    session = start_resp.json()
    session_id = session["session_id"]
    print(f"[start] {session}")

    print("\n[message] streaming response:")
    with httpx.stream(
        "POST",
        f"{BASE_URL}/session/{session_id}/message",
        json={"message": TEST_MESSAGE, "conversation_history": []},
        timeout=120.0,
    ) as stream_resp:
        stream_resp.raise_for_status()
        for line in stream_resp.iter_lines():
            if not line.startswith("data: "):
                continue
            payload = line[len("data: "):]
            if payload == "[DONE]":
                print("\n[message] [DONE]")
                break
            print(payload, end="", flush=True)

    close_resp = httpx.post(
        f"{BASE_URL}/session/{session_id}/close",
        timeout=10.0,
    )
    close_resp.raise_for_status()
    print(f"\n[close] {close_resp.json()}")

    print(f"\n[wait] sleeping {INSIGHT_WAIT_SECONDS}s for insight engine...")
    time.sleep(INSIGHT_WAIT_SECONDS)

    insight_path = INSIGHTS_DIR / f"{session_id}.json"
    if insight_path.exists():
        print(f"\n[insight] {insight_path}")
        print(insight_path.read_text())
    else:
        print(f"\n[insight] file not found yet at {insight_path} — engine may still be running")


if __name__ == "__main__":
    main()
