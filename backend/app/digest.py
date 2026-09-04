"""
The digest engine: turns "here's a fresh quote" into "here's whether that's
worth your attention", per ticker, for one user's whole watchlist.

This is the core of the product idea. The approach, in plain terms:

  1. Get a fresh quote for the ticker (app/market_data.py).
  2. Compare it to the user's LastChecked checkpoint for that ticker (if
     they've looked at it before).
  3. Figure out whether the size of that move is unusual *for this
     specific stock*, using that stock's own recent history (stored in
     PriceSnapshot) rather than one fixed threshold for every ticker.
  4. Check whether volume backs the move up (a move on unusually high
     volume is more likely to mean something).
  5. Check whether it's a new high/low relative to everything we've
     recorded for that ticker so far.
  6. Rank every entry by how much of the above fired, most notable first.

Two constants control the "how unusual is unusual" and "how much extra
volume counts as confirmation" thresholds -- tune these if the demo needs
it, they're deliberately simple round numbers rather than anything
statistically rigorous (this is a 24-hour build, not a quant desk).
"""
import statistics
from typing import List, Optional

from sqlalchemy.orm import Session

from app.crud import get_last_checked, upsert_last_checked
from app.market_data import MarketDataUnavailable, get_quote
from app.models import PriceSnapshot, User, WatchlistItem
from app.schemas import DigestEntry

# A move is flagged "unusual" once it's at least this many multiples of
# the ticker's own normal daily move size.
UNUSUAL_MOVE_THRESHOLD = 2.0

# Volume counts as "confirming" a move once it's at least this many
# multiples of the ticker's recent average volume.
VOLUME_CONFIRM_THRESHOLD = 1.5

# How many recent snapshots to use when learning a ticker's "normal" daily
# move size and average volume. More history = a steadier baseline; this
# is capped mainly so the query stays cheap.
HISTORY_LOOKBACK = 60

# Need at least this many stored snapshots before we trust a volatility
# baseline enough to flag anything as "unusual". Below this, we simply
# don't have enough of this ticker's own history yet.
MIN_SNAPSHOTS_FOR_BASELINE = 3


def _recent_snapshots(db: Session, ticker: str, limit: int = HISTORY_LOOKBACK) -> List[PriceSnapshot]:
    """Most recent snapshots for a ticker, oldest first (for day-over-day comparisons)."""
    rows = (
        db.query(PriceSnapshot)
        .filter(PriceSnapshot.ticker == ticker)
        .order_by(PriceSnapshot.captured_at.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(rows))


def _normal_daily_move_pct(snapshots: List[PriceSnapshot]) -> Optional[float]:
    """
    This ticker's own baseline: the standard deviation of its day-over-day
    percent price changes, using whatever snapshot history we've built up.
    Returns None if there isn't enough history yet to trust the number.
    """
    if len(snapshots) < MIN_SNAPSHOTS_FOR_BASELINE:
        return None

    daily_returns = []
    for previous, current in zip(snapshots, snapshots[1:]):
        if previous.price:
            daily_returns.append((current.price - previous.price) / previous.price)

    if len(daily_returns) < 2:
        return None

    baseline = statistics.stdev(daily_returns)
    return baseline if baseline > 0 else None


def _average_volume(snapshots: List[PriceSnapshot]) -> Optional[float]:
    volumes = [s.volume for s in snapshots if s.volume]
    if not volumes:
        return None
    return statistics.mean(volumes)


def _is_new_high_or_low(
    current_price: float,
    current_day_high: Optional[float],
    current_day_low: Optional[float],
    snapshots: List[PriceSnapshot],
) -> tuple[bool, bool]:
    """
    Whether this reading is the highest/lowest we've seen for this ticker
    across all the history we've collected.

    Honest caveat: this is "highest/lowest since we started tracking it",
    not a true 52-week high/low (we don't have a year of history yet on a
    hackathon timeline) -- it converges toward the real thing the longer
    the app runs.
    """
    if len(snapshots) < 2:
        return False, False  # nothing to compare against yet

    historical_highs = [s.day_high if s.day_high is not None else s.price for s in snapshots]
    historical_lows = [s.day_low if s.day_low is not None else s.price for s in snapshots]

    candidate_high = current_day_high if current_day_high is not None else current_price
    candidate_low = current_day_low if current_day_low is not None else current_price

    is_high = candidate_high >= max(historical_highs)
    is_low = candidate_low <= min(historical_lows)
    return is_high, is_low


def _build_entry(db: Session, user: User, ticker: str) -> DigestEntry:
    try:
        quote = get_quote(ticker, db=db)
    except MarketDataUnavailable as e:
        return DigestEntry(
            ticker=ticker,
            data_source="unavailable",
            is_first_check=get_last_checked(db, user.id, ticker) is None,
            is_unusual_move=False,
            volume_confirmed=False,
            is_52_week_high=False,
            is_52_week_low=False,
            note=str(e),
        )

    # Build the baseline from history recorded *before* this reading.
    history = _recent_snapshots(db, ticker)
    normal_move = _normal_daily_move_pct(history)
    avg_volume = _average_volume(history)
    is_high, is_low = _is_new_high_or_low(
        quote["price"], quote.get("day_high"), quote.get("day_low"), history
    )

    # Persist this reading as a new data point -- but only for genuinely
    # fresh (live) data, so re-showing a cached fallback doesn't get
    # counted as a new observation.
    if quote["source"] == "live":
        db.add(
            PriceSnapshot(
                ticker=ticker,
                price=quote["price"],
                volume=quote.get("volume"),
                day_open=quote.get("day_open"),
                day_high=quote.get("day_high"),
                day_low=quote.get("day_low"),
            )
        )
        db.commit()

    last_checked = get_last_checked(db, user.id, ticker)

    pct_change = None
    move_score = None
    is_unusual = False
    volume_confirmed = False
    note = None

    if last_checked is None:
        note = "First time checking this ticker -- nothing to compare yet."
    else:
        if last_checked.price_at_check:
            pct_change = (quote["price"] - last_checked.price_at_check) / last_checked.price_at_check

        if normal_move is None:
            note = f"Not enough price history yet to judge what's a normal move for {ticker}."
        elif pct_change is not None:
            move_score = pct_change / normal_move
            is_unusual = abs(move_score) >= UNUSUAL_MOVE_THRESHOLD

        if quote.get("volume") and avg_volume:
            volume_confirmed = quote["volume"] >= VOLUME_CONFIRM_THRESHOLD * avg_volume

    # Whether or not there's anything notable, record that the user has
    # now seen this ticker -- this checkpoint is what the *next* digest
    # call compares against.
    upsert_last_checked(db, user.id, ticker, quote["price"], quote.get("volume"))

    return DigestEntry(
        ticker=ticker,
        current_price=quote["price"],
        current_volume=quote.get("volume"),
        data_source=quote["source"],
        is_first_check=last_checked is None,
        price_at_last_check=last_checked.price_at_check if last_checked else None,
        last_checked_at=last_checked.checked_at if last_checked else None,
        pct_change_since_last_check=pct_change,
        normal_daily_move_pct=normal_move,
        move_score=move_score,
        is_unusual_move=is_unusual,
        volume_confirmed=volume_confirmed,
        is_52_week_high=is_high,
        is_52_week_low=is_low,
        note=note,
    )


def _rank_key(entry: DigestEntry) -> tuple:
    """
    Higher = more worth the user's attention. Unusual moves first, then
    however unusual they are, with volume confirmation and new highs/lows
    acting as tiebreaker boosts.
    """
    magnitude = abs(entry.move_score) if entry.move_score is not None else 0.0
    boost = (2.0 if (entry.is_52_week_high or entry.is_52_week_low) else 0.0) + (
        1.0 if entry.volume_confirmed else 0.0
    )
    return (entry.is_unusual_move, magnitude + boost)


def build_digest(db: Session, user: User) -> List[DigestEntry]:
    """
    The main entry point: one ranked DigestEntry per ticker on the user's
    watchlist, most notable first. Calling this is what "checking the
    watchlist" means -- it updates each ticker's LastChecked checkpoint as
    a side effect, so the *next* call is comparing against *this* one.
    """
    items = db.query(WatchlistItem).filter(WatchlistItem.user_id == user.id).all()
    entries = [_build_entry(db, user, item.ticker) for item in items]
    entries.sort(key=_rank_key, reverse=True)
    return entries
