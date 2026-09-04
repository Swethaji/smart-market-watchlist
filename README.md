# Smart Market Watchlist

A 24-hour hackathon project. Instead of just showing live stock prices, the
app remembers what each stock looked like the last time you checked it, and
shows a ranked "what's changed since you last looked" digest -- flagging
moves that are unusual for *that specific stock's* normal volatility,
confirmed by volume, plus new highs/lows.

## Stack

- **Frontend:** React (Vite)
- **Backend:** FastAPI (Python)
- **Database:** SQLite (via SQLAlchemy)
- **Market data:** [Finnhub](https://finnhub.io) for price/open/high/low, [Twelve Data](https://twelvedata.com) for volume (Finnhub's free tier doesn't include volume for stocks)

## Project structure

```
smart-market-watchlist/
├── backend/
│   ├── app/
│   │   ├── main.py         # FastAPI app, CORS, table creation, router wiring
│   │   ├── config.py       # settings, loaded from .env
│   │   ├── database.py     # SQLAlchemy engine/session setup
│   │   ├── models.py       # DB schema: User, WatchlistItem, PriceSnapshot, LastChecked
│   │   ├── schemas.py      # Pydantic request/response shapes
│   │   ├── crud.py         # small DB read/write helpers (get-or-create user, upsert LastChecked)
│   │   ├── market_data.py  # get_quote(): live Finnhub+Twelve Data call, falls back to cached PriceSnapshot
│   │   ├── digest.py       # the core feature: ranks "what's changed" per ticker
│   │   └── routers/
│   │       ├── users.py       # POST /users/identify
│   │       └── watchlist.py   # watchlist CRUD + GET /watchlist/digest
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    └── src/
        ├── api.js                    # fetch wrapper for the backend
        ├── App.jsx                   # top-level layout + state
        └── components/
            ├── IdentifyGate.jsx      # email "login" screen
            ├── AddTickerForm.jsx
            └── DigestCard.jsx        # one ranked digest entry
```

## Status

- [x] Folder structure, FastAPI skeleton, DB schema
- [x] Finnhub (price) + Twelve Data (volume) integration, with graceful fallback to cached data
- [x] Watchlist CRUD + digest ranking endpoints
- [x] React frontend: identify, add/remove tickers, ranked digest view
- [x] Pushed to GitHub (https://github.com/Swethaji/smart-market-watchlist)
- [ ] Real auth (currently: email only, no password -- fine for a demo, not for production)
- [ ] True 52-week high/low (currently: highest/lowest *since we started tracking it* -- see caveat below)

## Running it

**Backend** (from `backend/`, Windows PowerShell):
```powershell
python -m venv .venv                                   # first time only
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```
Visit `http://127.0.0.1:8000/health` and `http://127.0.0.1:8000/docs` (interactive API docs).

**Frontend** (from `frontend/`, separate terminal):
```powershell
npm install    # first time only
npm run dev
```
Vite prints a local URL (default `http://localhost:5173`) -- open it, enter any email, add a ticker (e.g. `AAPL`), and the digest loads.

Both need `backend/.env` to hold `FINNHUB_API_KEY` and `TWELVEDATA_API_KEY` (see `.env.example`) -- git-ignored, never commit real keys.

## How the digest works

Every ticker on your watchlist gets a fresh quote (live if reachable, otherwise the last cached reading), which is compared against your `LastChecked` checkpoint for that ticker -- what it looked like the last time you viewed it. Calling `GET /watchlist/digest` (which is what loading/refreshing the app does) is itself "checking" -- it updates the checkpoint, so the *next* call compares against *this* one.

A move counts as **unusual** once it's at least 2x that ticker's own recent daily volatility (learned from its stored `PriceSnapshot` history, not one fixed threshold for every stock). It counts as **volume confirmed** once volume is at least 1.5x that ticker's recent average. Both thresholds are simple, tunable constants at the top of `backend/app/digest.py`.

**Caveat:** "52-week high/low" is really "highest/lowest since this app started recording it" -- there's no year of history on a hackathon timeline. It becomes more accurate the longer the app runs and accumulates `PriceSnapshot` rows (one gets added per ticker per live digest call).

## Database schema

| Table            | Purpose                                                                 |
|------------------|--------------------------------------------------------------------------|
| `users`          | One row per app user (identified by email only, no password).            |
| `watchlist_items`| Which tickers a user is watching.                                        |
| `price_snapshots`| Historical price/volume readings per ticker -- the source of each ticker's volatility baseline and running high/low. |
| `last_checked`   | Per (user, ticker) checkpoint of what the stock looked like the last time that user viewed it. |

Tables are created automatically on backend startup (`Base.metadata.create_all`).
For a hackathon this is simpler than managing migrations; a real project
would use Alembic instead.

## API endpoints

| Method & path              | Purpose                                      |
|-----------------------------|-----------------------------------------------|
| `GET /health`                | Liveness check                                |
| `POST /users/identify`       | Find-or-create a user by email                |
| `GET /watchlist?email=`      | List a user's watched tickers                 |
| `POST /watchlist?email=`     | Add a ticker (`{"ticker": "AAPL"}`)           |
| `DELETE /watchlist/{id}?email=` | Remove a ticker                            |
| `GET /watchlist/digest?email=`  | The ranked "what's changed" digest (see above) |
