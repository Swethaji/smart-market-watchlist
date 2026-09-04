# Smart Market Watchlist

A watchlist app that goes beyond showing live stock prices: it remembers
what each stock looked like the last time you checked it, and shows a
ranked **"what's changed since you last looked"** digest -- flagging moves
that are unusual for *that specific stock's* normal volatility, confirmed
by volume, plus new highs/lows.

## Why

Most watchlists just show you a live price grid, and it's on you to notice
what actually matters. This app instead remembers your last visit per
ticker and, on your next visit, tells you what changed and how unusual it
was -- so a 2% move in a normally-quiet stock gets surfaced above a 2% move
in a stock that swings 5% every day.

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
│   │       ├── watchlist.py   # watchlist CRUD + GET /watchlist/digest
│   │       └── dev.py         # POST /dev/seed-demo -- plants demo data, see "Try it out" below
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
Vite prints a local URL (default `http://localhost:5173`) -- open it, enter any email, and add a ticker.

Both need `backend/.env` to hold `FINNHUB_API_KEY` and `TWELVEDATA_API_KEY` (see `.env.example`) -- git-ignored, never commit real keys.

## Try it out

A brand-new ticker always starts with "nothing to compare yet" -- there's
no prior visit to diff against, and no price history yet to judge what's
normal. To see the actual digest logic (unusual move / volume confirmed /
new high) without waiting for real history to accumulate, use the
dev-only seeding endpoint:

1. Add a ticker in the app (e.g. `AAPL`), or let step 2 add it for you.
2. Open `http://127.0.0.1:8000/docs`, find **POST /dev/seed-demo**, and
   run it with your email and `ticker=AAPL`. This plants ~9 days of quiet
   fake history ending about 10% below the ticker's real current price,
   and backdates your checkpoint to that lower price.
3. Refresh the app. The card should show a realistic double-digit percent
   jump, flagged **Unusual move** and **New high** (and **Volume
   confirmed** if live volume clears the threshold).
4. Try it again with a couple more tickers (e.g. `MSFT`, `GOOG`) to see
   several ranked entries at once -- the most notable move sorts first.

`/dev/seed-demo` is clearly a demo/dev tool, not something a real product
would ship -- see the docstring in `backend/app/routers/dev.py`.

## How the digest works

Every ticker on your watchlist gets a fresh quote (live if reachable, otherwise the last cached reading), which is compared against your `LastChecked` checkpoint for that ticker -- what it looked like the last time you viewed it. Calling `GET /watchlist/digest` (which is what loading/refreshing the app does) is itself "checking" -- it updates the checkpoint, so the *next* call compares against *this* one.

A move counts as **unusual** once it's at least 2x that ticker's own recent daily volatility (learned from its stored `PriceSnapshot` history, not one fixed threshold for every stock). It counts as **volume confirmed** once volume is at least 1.5x that ticker's recent average. Both thresholds are simple, tunable constants at the top of `backend/app/digest.py`.

**Caveat:** "52-week high/low" is really "highest/lowest since this app started recording it," since there isn't a year of real history yet. It becomes accurate over time as `PriceSnapshot` rows accumulate (one gets added per ticker per live digest call).

## Database schema

| Table            | Purpose                                                                 |
|------------------|--------------------------------------------------------------------------|
| `users`          | One row per app user (identified by email only, no password).            |
| `watchlist_items`| Which tickers a user is watching.                                        |
| `price_snapshots`| Historical price/volume readings per ticker -- the source of each ticker's volatility baseline and running high/low. |
| `last_checked`   | Per (user, ticker) checkpoint of what the stock looked like the last time that user viewed it. |

Tables are created automatically on backend startup (`Base.metadata.create_all`);
a larger project would use a migration tool like Alembic instead so schema
changes are tracked and reversible.

## API endpoints

| Method & path              | Purpose                                      |
|-----------------------------|-----------------------------------------------|
| `GET /health`                | Liveness check                                |
| `POST /users/identify`       | Find-or-create a user by email                |
| `GET /watchlist?email=`      | List a user's watched tickers                 |
| `POST /watchlist?email=`     | Add a ticker (`{"ticker": "AAPL"}`)           |
| `DELETE /watchlist/{id}?email=` | Remove a ticker                            |
| `GET /watchlist/digest?email=`  | The ranked "what's changed" digest (see above) |
| `POST /dev/seed-demo?email=&ticker=` | Dev-only: plants demo history, see "Try it out" |

## Known limitations

- **No real authentication** -- a user is just an email, no password or session. Fine for a demo, not for production.
- **No background refresh job** -- price history only grows when someone actually loads the app; there's no scheduled poller building history in the background.
- **52-week high/low is approximate** -- see the caveat above.
- **Runs locally only** -- there's no hosted deployment yet; running it requires starting both the backend and frontend on your own machine.
