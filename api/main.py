# Run with: uvicorn api.main:app --reload --port 8080
from fastapi import FastAPI

from api.routers.session import router as session_router
from insight_engine.engine import init_db

app = FastAPI(title="DestinationIQ API", version="0.1.0")

app.include_router(session_router, prefix="/session")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
