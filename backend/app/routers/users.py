"""
User identification.

No passwords or sessions here -- email is the whole identity system for
this hackathon build. The frontend calls POST /users/identify once (on
load, or when the user types their email) to get a user id, then passes
that email as a query parameter on every watchlist call.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import get_or_create_user
from app.database import get_db
from app.schemas import IdentifyRequest, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/identify", response_model=UserOut)
def identify(payload: IdentifyRequest, db: Session = Depends(get_db)) -> UserOut:
    """Find the user with this email, or create one if it's new."""
    return get_or_create_user(db, payload.email)
