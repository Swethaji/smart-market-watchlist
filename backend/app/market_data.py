"""
Market data provider: Finnhub (https://finnhub.io).

`get_quote(ticker, db)` is the function the rest of the app should call:

  1. It tries a live call to Finnhub for the current price, plus a
     best-effort call to Twelve Data for volume (Finnhub's free tier
     doesn't include volume for stocks).
  2. If the live call fails for any reason (network error, rate limit,
     bad ticker, etc.) AND a database session was passed in, it falls back
     to the most recent PriceSnapshot already stored for that ticker.
  3. If there's neither a live quote nor a cached snapshot, it raises
     MarketDataUnavailable with a message explaining why.

Manual end-to-end test (hits the real API):
    cd backend
    source .venv/bin/activate   # or: .venv\\Scripts\\activate on Windows
    python -m app.market_data
"""
from datetime import datetime, timezone
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.config import FINNHUB_API_KEY, TWELVEDATA_API_KEY

FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
TWELVEDATA_BASE_URL = "https://api.twelvedata.com"
REQUEST_TIMEOUT_SECONDS = 6


class MarketDataUnavailable(Exception):
    """Raised when there's neither a live quote nor a cached snapshot to use."""


def _fetch_live_price(ticker: str) -> dict:
    """
    Call Finnhub's /quote endpoint for price + day open/high/low.
    Raises on missing API key, network errors, timeouts, HTTP 429 (rate
    limit), or any other non-2xx response -- callers catch this and fall
    back to cached data.
    """
    if not FINNHUB_API_KEY:
        raise MarketDataUnavailable(
            "FINNHUB_API_KEY is not set (check backend/.env)"
        )

    response = httpx.get(
        f"{FINNHUB_BASE_URL}/quote",
        params={"symbol": ticker, "token": FINNHUB_API_KEY},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    if response.status_code == 429:
        raise RuntimeError(f"Finnhub rate limit hit while fetching '{ticker}'")
    response.raise_for_status()

    data = response.json()
    # An unrecognized symbol comes back as HTTP 200 with all-zero fields
    # rather than an error status, so treat that as "no data" too.
    if not data.get("c") and not data.get("t"):
        raise RuntimeError(f"Finnhub returned no data for ticker '{ticker}'")

    return {
        "price": data["c"],
        "day_open": data.get("o"),
        "day_high": data.get("h"),
        "day_low": data.get("l"),
    }


def _fetch_live_volume(ticker: str) -> Optional[int]:
    """
    Volume lookup via Twelve Data's /quote endpoint.

    Finnhub's /quote has no volume field, and its /stock/candle endpoint
    (which does) returns HTTP 403 on a free-tier key -- volume for stocks
    is a paid-plan feature there. Twelve Data's free tier includes volume
    directly, so it's used here as a volume-only source; Finnhub remains
    the source for price/open/high/low.

    Returns None (instead of raising) on any failure -- volume is a
    nice-to-have here, not worth failing the whole quote over.
    """
    if not TWELVEDATA_API_KEY:
        return None
    try:
        response = httpx.get(
            f"{TWELVEDATA_BASE_URL}/quote",
            params={"symbol": ticker, "apikey": TWELVEDATA_API_KEY},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        # Twelve Data returns HTTP 200 even for errors (bad symbol, rate
        # limit, bad key), with a "status": "error" body instead.
        if data.get("status") == "error" or "code" in data:
            return None
        volume = data.get("volume")
        return int(volume) if volume not in (None, "") else None
    except Exception:
        return None


def _fallback_from_cache(db: Session, ticker: str) -> dict:
    """Return the most recent PriceSnapshot row for a ticker, if one exists."""
    from sqlalchemy.exc import SQLAlchemyError

    from app.models import PriceSnapshot  # local import avoids a circular import

    try:
        snapshot = (
            db.query(PriceSnapshot)
            .filter(PriceSnapshot.ticker == ticker)
            .order_by(PriceSnapshot.captured_at.desc())
            .first()
        )
    except SQLAlchemyError as db_error:
        # e.g. the price_snapshots table doesn't exist yet because the API
        # server (which creates tables on startup) has never run.
        raise MarketDataUnavailable(
            f"Could not read cached data for '{ticker}': {db_error}"
        ) from db_error
    if snapshot is None:
        raise MarketDataUnavailable(
            f"No live data and no cached PriceSnapshot for '{ticker}'"
        )
    return {
        "ticker": ticker,
        "price": snapshot.price,
        "volume": snapshot.volume,
        "day_open": snapshot.day_open,
        "day_high": snapshot.day_high,
        "day_low": snapshot.day_low,
        "captured_at": snapshot.captured_at,
        "source": "cache",
    }


def get_quote(ticker: str, db: Optional[Session] = None) -> dict:
    """
    Get the current quote for `ticker`.

    Tries Finnhub first. If that fails and `db` was provided, falls back
    to the latest cached PriceSnapshot for that ticker. Raises
    MarketDataUnavailable if neither source has anything to return.
    """
    ticker = ticker.upper().strip()

    try:
        price_data = _fetch_live_price(ticker)
        volume = _fetch_live_volume(ticker)
        return {
            "ticker": ticker,
            "price": price_data["price"],
            "volume": volume,
            "day_open": price_data["day_open"],
            "day_high": price_data["day_high"],
            "day_low": price_data["day_low"],
            "captured_at": datetime.now(timezone.utc),
            "source": "live",
        }
    except Exception as live_error:
        if db is None:
            raise MarketDataUnavailable(
                f"Live fetch failed for '{ticker}' and no DB session was "
                f"given to check the cache: {live_error}"
            ) from live_error
        try:
            return _fallback_from_cache(db, ticker)
        except MarketDataUnavailable:
            raise MarketDataUnavailable(
                f"Live fetch failed for '{ticker}' ({live_error}) and there "
                f"is no cached PriceSnapshot to fall back to."
            ) from live_error


if __name__ == "__main__":
    # Manual end-to-end check: `python -m app.market_data`
    from app.database import Base, SessionLocal, engine
    from app import models  # noqa: F401  (registers tables with Base)

    Base.metadata.create_all(bind=engine)  # in case the API server hasn't run yet
    db = SessionLocal()
    try:
        result = get_quote("AAPL", db=db)
        print(result)
    except MarketDataUnavailable as e:
        print(f"Unavailable: {e}")
    finally:
        db.close()
