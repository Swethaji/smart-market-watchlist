"""
Database setup (SQLAlchemy + SQLite).

This file wires up:
  - `engine`      -- the actual connection to the SQLite file on disk
  - `SessionLocal` -- a factory that hands out one DB "session" (a unit of
                      work) per request
  - `Base`        -- the class every table model in models.py inherits from
  - `get_db`      -- a FastAPI dependency that opens a session for a
                      request and always closes it afterwards, even if the
                      request raises an error

You generally won't need to edit this file again -- new tables go in
models.py, and endpoints just import `get_db`.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import DATABASE_URL

# `check_same_thread` is a SQLite-specific quirk: by default SQLite only
# allows the thread that created a connection to use it, but FastAPI can
# handle a request on a different thread. Disabling that check is safe here
# because SQLAlchemy's session-per-request pattern still keeps each request
# isolated.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session, closes it when the request ends."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
