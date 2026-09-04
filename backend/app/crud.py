"""
Small, reusable database read/write helpers shared by more than one router.

Nothing fancy here on purpose -- this is a hackathon build. Each function
does one obvious thing so routers stay thin and easy to read.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models import LastChecked, User


def get_or_create_user(db: Session, email: str) -> User:
    """
    Find the user with this email, or create one if this is their first
    time. There's no password/session here -- for the hackathon, email is
    the whole identity system.
    """
    email = email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if user is not None:
        return user

    user = User(email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_last_checked(db: Session, user_id: int, ticker: str) -> Optional[LastChecked]:
    return (
        db.query(LastChecked)
        .filter(LastChecked.user_id == user_id, LastChecked.ticker == ticker)
        .first()
    )


def upsert_last_checked(
    db: Session,
    user_id: int,
    ticker: str,
    price: float,
    volume: Optional[int],
) -> LastChecked:
    """
    Record "here's what this ticker looked like when the user just viewed
    it" -- overwriting any previous checkpoint for this (user, ticker),
    not appending a new row. This is what the next digest call compares
    against.
    """
    row = get_last_checked(db, user_id, ticker)
    if row is None:
        row = LastChecked(user_id=user_id, ticker=ticker)
        db.add(row)

    row.price_at_check = price
    row.volume_at_check = volume
    row.checked_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(row)
    return row
