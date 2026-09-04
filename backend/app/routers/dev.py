"""
Dev-only helpers -- NOT something a real product would ship. This exists
purely so a hackathon demo doesn't have to wait for real price history to
accumulate before the "unusual move" / "volume confirmed" / "new high"
badges have anything interesting to show.
"""
import random
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.crud import upsert_last_checked
from app.database import get_db
from app.market_data import MarketDataUnavailable, get_quote
from app.models import PriceSnapshot, User, WatchlistItem
from app.routers.watchlist import _current_user

router = APIRouter(prefix="/dev", tags=["dev-only"])


@router.post("/seed-demo")
def seed_demo(
    ticker: str = Query(..., description="Ticker to plant fake history for, e.g. AAPL"),
    user: User = Depends(_current_user),
    db: Session = Depends(get_db),
):
    """
    Plants ~9 days of quiet, low-volatility fake history for `ticker`
    ending about 10% below its current price, adds it to the user's
    watchlist if it isn't already there, and sets their LastChecked
    checkpoint to that lower price -- so the next digest call reads as a
    believable "you missed a big, volume-confirmed move to a new high".

    Uses the ticker's *real* current price as the anchor when reachable,
    so the seeded history stays plausible; falls back to a flat $100 if
    live data isn't reachable.

    Deliberately does NOT call the digest itself -- that would immediately
    consume (overwrite) the checkpoint this just planted, before you ever
    see it. Go refresh the app instead; *that* call is what should show
    the big jump.
    """
    ticker = ticker.strip().upper()

    if not db.query(WatchlistItem).filter_by(user_id=user.id, ticker=ticker).first():
        db.add(WatchlistItem(user_id=user.id, ticker=ticker))
        db.commit()

    try:
        anchor_price = get_quote(ticker, db=db)["price"]
    except MarketDataUnavailable:
        anchor_price = 100.0

    base_price = anchor_price * 0.90
    now = datetime.now(timezone.utc)

    for i in range(9):
        price = base_price * (1 + random.uniform(-0.008, 0.008))
        db.add(
            PriceSnapshot(
                ticker=ticker,
                price=price,
                volume=int(900_000 + random.uniform(-30_000, 30_000)),
                day_open=price - 0.4,
                day_high=price + 0.6,
                day_low=price - 0.6,
                captured_at=now - timedelta(days=9 - i),
            )
        )
    db.commit()

    upsert_last_checked(db, user.id, ticker, price=base_price, volume=900_000)

    return {
        "seeded_ticker": ticker,
        "seeded_checkpoint_price": round(base_price, 2),
        "next_step": f"Go refresh the app -- {ticker}'s digest card should now show a jump up to its real current price.",
    }
