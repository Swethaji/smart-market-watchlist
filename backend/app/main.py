"""
FastAPI application entry point.

Run it (from backend/, after installing requirements.txt) with:

    uvicorn app.main:app --reload

Then visit:
  http://127.0.0.1:8000/health        -- health check (this file)
  http://127.0.0.1:8000/docs          -- interactive API docs (auto-generated)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.database import Base, engine
from app.schemas import HealthResponse

# Import models so SQLAlchemy knows about every table before create_all()
# runs. (If a model module is never imported, its table never gets
# created -- this import is what registers User/WatchlistItem/etc. with
# Base.metadata.)
from app import models  # noqa: F401
from app.routers import dev, users, watchlist

app = FastAPI(
    title="Smart Market Watchlist API",
    description="Backend for a watchlist that remembers what changed since you last looked.",
    version="0.1.0",
)

# Allow the Vite dev server (frontend) to call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """
    Create any tables that don't exist yet.

    Fine for a hackathon; a real project would use a migration tool
    (e.g. Alembic) instead so schema changes are tracked and reversible.
    """
    Base.metadata.create_all(bind=engine)


@app.get("/health", response_model=HealthResponse, tags=["meta"])
def health_check() -> HealthResponse:
    """Simple liveness check: if this responds, the API process is up."""
    return HealthResponse(status="ok", service="smart-market-watchlist-api")


app.include_router(users.router)
app.include_router(watchlist.router)
app.include_router(dev.router)
