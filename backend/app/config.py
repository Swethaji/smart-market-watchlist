"""
App configuration.

Everything the app needs to know that could change between your laptop,
a teammate's laptop, or a deployed server lives here, read from environment
variables (or a local .env file) instead of being hard-coded.

For the hackathon we keep this simple: a handful of plain settings loaded
with python-dotenv. If the project grows past the weekend, this is the
natural place to swap in pydantic-settings for validation.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load variables from a .env file in backend/ if one exists.
# .env is git-ignored on purpose -- it's where API keys and secrets live,
# and secrets should never be committed to the repo.
BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

# SQLite database file. Defaults to backend/watchlist.db.
DATABASE_URL = os.getenv(
    "DATABASE_URL", f"sqlite:///{BACKEND_DIR / 'watchlist.db'}"
)

# Comma-separated list of origins allowed to call this API (the Vite dev
# server runs on 5173 by default).
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
).split(",")

# Finnhub API key (https://finnhub.io/dashboard) -- used by app/market_data.py
# to fetch live quotes. Set the real value in backend/.env (git-ignored),
# never commit it.
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")

# Twelve Data API key (https://twelvedata.com) -- used as a volume-only
# fallback, since Finnhub's free tier doesn't include volume for stocks.
TWELVEDATA_API_KEY = os.getenv("TWELVEDATA_API_KEY", "")
