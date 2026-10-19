from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load backend/.env explicitly; environment variables already set by the host take precedence.
BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env", override=False)

from api.routes import router  # noqa: E402
from services.triage_store import init_db  # noqa: E402


def get_cors_origins() -> list[str]:
    configured = os.getenv("BACKEND_CORS_ORIGINS", "")
    if configured.strip():
        return [origin.strip() for origin in configured.split(",") if origin.strip()]
    return ["http://localhost:5173", "http://127.0.0.1:5173"]


app = FastAPI(
    title="GCCX Candidate Triage API",
    description=(
        "Candidate search, filtering, persistent shortlist/tags, and AI-generated fit summaries. "
        "AI output is decision support only; hiring decisions remain with humans."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
app.include_router(router)


@app.on_event("startup")
def startup_triage_database() -> None:
    init_db()


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "service": "gccx-candidate-triage", "health": "/health", "docs": "/docs"}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
