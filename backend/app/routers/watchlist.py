"""
Watchlist management (add/list/remove tickers) and the digest endpoint --
the core "what's changed since you last looked" feature.

There's no session/auth in this hackathon build, so every endpoint here
takes the user's email as a query parameter (?email=you@example.com) to
say who's asking. _current_user() below turns that into a User row,
creating one on first use.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud import get_or_create_user
from app.database import get_db
from app.digest import build_digest
from app.models import User, WatchlistItem
from app.schemas import DigestEntry, WatchlistItemCreate, WatchlistItemOut

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


def _current_user(
    email: str = Query(..., description="Identifies the user (see POST /users/identify)"),
    db: Session = Depends(get_db),
) -> User:
    return get_or_create_user(db, email)


@router.get("", response_model=List[WatchlistItemOut])
def list_watchlist(user: User = Depends(_current_user), db: Session = Depends(get_db)):
    return (
        db.query(WatchlistItem)
        .filter(WatchlistItem.user_id == user.id)
        .order_by(WatchlistItem.added_at)
        .all()
    )


@router.post("", response_model=WatchlistItemOut, status_code=201)
def add_to_watchlist(
    payload: WatchlistItemCreate,
    user: User = Depends(_current_user),
    db: Session = Depends(get_db),
):
    ticker = payload.ticker.strip().upper()
    if not ticker:
        raise HTTPException(status_code=400, detail="ticker cannot be empty")

    item = WatchlistItem(user_id=user.id, ticker=ticker)
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"{ticker} is already on your watchlist")
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def remove_from_watchlist(
    item_id: int, user: User = Depends(_current_user), db: Session = Depends(get_db)
):
    item = (
        db.query(WatchlistItem)
        .filter(WatchlistItem.id == item_id, WatchlistItem.user_id == user.id)
        .first()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="watchlist item not found")
    db.delete(item)
    db.commit()


@router.get("/digest", response_model=List[DigestEntry])
def get_digest(user: User = Depends(_current_user), db: Session = Depends(get_db)):
    """
    What's changed on this user's watchlist since they last checked,
    ranked most-notable first. Calling this updates each ticker's
    LastChecked checkpoint, so the *next* call compares against what this
    one just returned.
    """
    return build_digest(db, user)
