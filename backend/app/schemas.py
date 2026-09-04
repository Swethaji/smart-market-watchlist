"""
Pydantic schemas: the shapes of data that go in/out of the API (JSON).

These are deliberately separate from the SQLAlchemy models in models.py.
models.py describes rows in the database; schemas.py describes the JSON
the frontend sends and receives. Keeping them separate means we can, e.g.,
hide internal fields from API responses or accept slightly different data
on the way in than what we store.

Only a health-check schema is wired up right now. The commented schemas
below are a starting point for the watchlist/snapshot/last-checked
endpoints we'll build next -- uncomment and adjust as those endpoints are
built.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: str
    service: str


# --- Starting points for upcoming endpoints ---------------------------------
#
# class UserOut(BaseModel):
#     model_config = ConfigDict(from_attributes=True)
#     id: int
#     email: str
#     created_at: datetime
#
#
# class WatchlistItemCreate(BaseModel):
#     ticker: str
#
#
# class WatchlistItemOut(BaseModel):
#     model_config = ConfigDict(from_attributes=True)
#     id: int
#     ticker: str
#     added_at: datetime
#
#
# class PriceSnapshotOut(BaseModel):
#     model_config = ConfigDict(from_attributes=True)
#     ticker: str
#     price: float
#     volume: int | None
#     captured_at: datetime
#
#
# class LastCheckedOut(BaseModel):
#     model_config = ConfigDict(from_attributes=True)
#     ticker: str
#     checked_at: datetime
#     price_at_check: float
#     volume_at_check: int | None
