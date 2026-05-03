# Run with: uvicorn api.main:app --reload --port 8081
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers.dashboard import router as dashboard_router
from api.routers.session import router as session_router
from insight_engine.engine import init_db

app = FastAPI(title="DestinationIQ API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(session_router, prefix="/session")
app.include_router(dashboard_router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
