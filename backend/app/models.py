"""
Database schema (SQLAlchemy ORM models).

Four tables, matching the core idea of the app:

- User            one row per person using the app
- WatchlistItem    which tickers a user is watching
- PriceSnapshot    a history of price/volume readings for a ticker, used to
                    (a) know the "current" price and (b) build a baseline
                    of what's normal for that specific stock, so we can
                    tell an unusual move apart from an average day
- LastChecked      a checkpoint: "the last time this user looked at this
                    ticker, here's what it looked like". Comparing a fresh
                    PriceSnapshot against a user's LastChecked row is what
                    powers the "what's changed since you last looked" digest.

Each class below becomes a real SQL table the first time the app starts
(see main.py, which calls Base.metadata.create_all).
"""
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """A person using the watchlist app."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    watchlist_items = relationship(
        "WatchlistItem", back_populates="user", cascade="all, delete-orphan"
    )
    last_checked_entries = relationship(
        "LastChecked", back_populates="user", cascade="all, delete-orphan"
    )


class WatchlistItem(Base):
    """One ticker that a user has added to their watchlist."""

    __tablename__ = "watchlist_items"
    __table_args__ = (
        # A user can only watch a given ticker once (no duplicate rows).
        UniqueConstraint("user_id", "ticker", name="uq_watchlist_user_ticker"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ticker = Column(String, nullable=False, index=True)  # e.g. "AAPL"
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="watchlist_items")


class PriceSnapshot(Base):
    """
    A single price/volume reading for a ticker at a point in time.

    We accumulate these over time (e.g. once a day, or once per poll of a
    market-data API) to build two things per ticker:
      1. The latest known price/volume.
      2. A history to compute "normal" daily volatility and 52-week
         high/low from, so we can flag moves that are unusual for THIS
         stock specifically rather than using one fixed threshold for
         every ticker.
    """

    __tablename__ = "price_snapshots"
    __table_args__ = (
        Index("ix_price_snapshots_ticker_time", "ticker", "captured_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, nullable=False, index=True)

    price = Column(Float, nullable=False)  # last/close price at capture time
    volume = Column(BigInteger, nullable=True)

    # Optional OHLC detail, useful once we pull daily bars from a market
    # data API. Nullable so a simple "just the latest price" snapshot works
    # too.
    day_open = Column(Float, nullable=True)
    day_high = Column(Float, nullable=True)
    day_low = Column(Float, nullable=True)

    captured_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class LastChecked(Base):
    """
    Checkpoint of what a ticker looked like the last time a specific user
    checked it. One row per (user, ticker) pair -- updated ("upserted") each
    time the user views that ticker, not appended to.

    This is the "memory" that makes the app's core feature possible: to
    build the "what's changed since you last looked" digest, we compare a
    ticker's latest PriceSnapshot against the user's LastChecked row for
    that ticker.
    """

    __tablename__ = "last_checked"
    __table_args__ = (
        UniqueConstraint("user_id", "ticker", name="uq_last_checked_user_ticker"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ticker = Column(String, nullable=False, index=True)

    checked_at = Column(DateTime(timezone=True), server_default=func.now())
    price_at_check = Column(Float, nullable=False)
    volume_at_check = Column(BigInteger, nullable=True)

    user = relationship("User", back_populates="last_checked_entries")
