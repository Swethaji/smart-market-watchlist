# Smart Market Watchlist

A 24-hour hackathon project. Instead of just showing live stock prices, the
app remembers what each stock looked like the last time you checked it, and
shows a ranked "what's changed since you last looked" digest -- flagging
moves that are unusual for *that specific stock's* normal volatility,
confirmed by volume, plus events like 52-week highs/lows.

## Stack

- **Frontend:** React (Vite)
- **Backend:** FastAPI (Python)
- **Database:** SQLite (via SQLAlchemy)

## Project structure

```
smart-market-watchlist/
├── backend/
│   ├── app/
│   │   ├── main.py       # FastAPI app + /health endpoint
│   │   ├── config.py     # settings, loaded from .env
│   │   ├── database.py   # SQLAlchemy engine/session setup
│   │   ├── models.py     # DB schema: User, WatchlistItem, PriceSnapshot, LastChecked
│   │   ├── schemas.py    # Pydantic request/response shapes
│   │   └── routers/      # (empty for now) API route modules go here
│   ├── requirements.txt
│   └── .env.example
└── frontend/              # React + Vite app (not scaffolded yet)
```

## Status

- [x] Folder structure
- [x] FastAPI skeleton with `/health`
- [x] Database schema (User, WatchlistItem, PriceSnapshot, LastChecked)
- [x] Python dependencies installed (`backend/.venv`, verified `/health` responds and tables are created)
- [x] Frontend scaffolded with Vite + React (`npm install` done, `npm run build` verified)
- [ ] Market-data API key configured (awaiting choice of provider + key)
- [ ] Pushed to GitHub (remote `origin` is set to https://github.com/Swethaji/smart-market-watchlist — push manually, see below)

## Running the backend

```bash
cd backend
source .venv/bin/activate   # venv already created; if missing: python3 -m venv .venv
uvicorn app.main:app --reload
```

Then visit `http://127.0.0.1:8000/health` and `http://127.0.0.1:8000/docs`.

## Running the frontend

```bash
cd frontend
npm run dev
```

Vite will print a local URL (default `http://localhost:5173`), already allowed by the backend's CORS settings.

## Pushing to GitHub

The local repo already has `origin` pointed at
`https://github.com/Swethaji/smart-market-watchlist`. Push from a machine
with your own GitHub credentials:

```bash
git push -u origin main
```

## Database schema

| Table            | Purpose                                                                 |
|------------------|--------------------------------------------------------------------------|
| `users`          | One row per app user.                                                    |
| `watchlist_items`| Which tickers a user is watching.                                        |
| `price_snapshots`| Historical price/volume readings per ticker -- used to know the latest price and to learn each stock's normal volatility / 52-week range. |
| `last_checked`   | Per (user, ticker) checkpoint of what the stock looked like the last time that user viewed it -- this is what powers the "what changed since you last looked" digest. |

Tables are created automatically on backend startup (`Base.metadata.create_all`).
For a hackathon this is simpler than managing migrations; a real project
would use Alembic instead.
