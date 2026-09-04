"""
Pydantic schemas: the shapes of data that go in/out of the API (JSON).

These are deliberately separate from the SQLAlchemy models in models.py.
models.py describes rows in the database; schemas.py describes the JSON
the frontend sends and receives.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: str
    service: str


# --- Users --------------------------------------------------------------
#
# No passwords/sessions for this hackathon build -- a user is identified
# purely by email. IdentifyRequest -> UserOut "logs in" by finding or
# creating a user with that email.


class IdentifyRequest(BaseModel):
    email: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    created_at: datetime


# --- Watchlist items ------------------------------------------------------


class WatchlistItemCreate(BaseModel):
    ticker: str


class WatchlistItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ticker: str
    added_at: datetime


# --- Digest -----------------------------------------------------------
#
# One DigestEntry per watched ticker, returned by GET /watchlist/digest,
# ranked from "most worth your attention" to least.


class DigestEntry(BaseModel):
    ticker: str

    current_price: Optional[float] = None
    current_volume: Optional[int] = None
    data_source: str  # "live" | "cache" | "unavailable"

    is_first_check: bool
    price_at_last_check: Optional[float] = None
    last_checked_at: Optional[datetime] = None

    pct_change_since_last_check: Optional[float] = None
    normal_daily_move_pct: Optional[float] = None  # this ticker's own volatility baseline
    move_score: Optional[float] = None  # pct_change / normal_daily_move -- how unusual, in "how-many-normal-days" units
    is_unusual_move: bool

    volume_confirmed: bool
    is_52_week_high: bool
    is_52_week_low: bool

    note: Optional[str] = None  # human-readable explanation, e.g. why data is missing
