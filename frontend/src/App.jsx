import { useEffect, useState, useCallback } from 'react'
import { identify, getWatchlist, addTicker, removeTicker, getDigest } from './api'
import IdentifyGate from './components/IdentifyGate'
import AddTickerForm from './components/AddTickerForm'
import DigestCard from './components/DigestCard'
import './App.css'

const EMAIL_STORAGE_KEY = 'smart-market-watchlist:email'

function App() {
  const [email, setEmail] = useState(() => {
    try {
      return localStorage.getItem(EMAIL_STORAGE_KEY) || null
    } catch {
      return null // localStorage can throw in some browser contexts -- fail open
    }
  })
  const [watchlist, setWatchlist] = useState([])
  const [digest, setDigest] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const loadEverything = useCallback(async (userEmail) => {
    setLoading(true)
    setError(null)
    try {
      const [items, digestEntries] = await Promise.all([
        getWatchlist(userEmail),
        getDigest(userEmail),
      ])
      setWatchlist(items)
      setDigest(digestEntries)
    } catch (err) {
      setError(err.message || 'Could not load your watchlist.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (email) loadEverything(email)
  }, [email, loadEverything])

  async function handleIdentified(newEmail) {
    await identify(newEmail)
    try {
      localStorage.setItem(EMAIL_STORAGE_KEY, newEmail)
    } catch {
      // per-viewer convenience only -- fine if it can't be saved
    }
    setEmail(newEmail)
  }

  async function handleAdd(ticker) {
    await addTicker(email, ticker)
    await loadEverything(email)
  }

  async function handleRemove(itemId) {
    await removeTicker(email, itemId)
    await loadEverything(email)
  }

  function handleSwitchUser() {
    try {
      localStorage.removeItem(EMAIL_STORAGE_KEY)
    } catch {
      // ignore
    }
    setEmail(null)
    setWatchlist([])
    setDigest([])
  }

  if (!email) {
    return <IdentifyGate onIdentified={handleIdentified} />
  }

  // Match each digest entry back to its watchlist item id, so the card's
  // remove button knows what to delete (the digest response only carries
  // tickers, not ids -- see backend/app/schemas.py).
  const itemIdByTicker = Object.fromEntries(watchlist.map((item) => [item.ticker, item.id]))

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Smart Market Watchlist</h1>
        <div className="header-right">
          <span className="user-email">{email}</span>
          <button type="button" className="link-btn" onClick={handleSwitchUser}>
            Switch user
          </button>
        </div>
      </header>

      <main>
        <AddTickerForm onAdd={handleAdd} />

        {error && <p className="error-text">{error}</p>}

        {loading && digest.length === 0 ? (
          <p className="muted">Loading your watchlist…</p>
        ) : watchlist.length === 0 ? (
          <p className="muted">Your watchlist is empty. Add a ticker above to get started.</p>
        ) : (
          <>
            <div className="digest-header">
              <h2>What's changed since you last looked</h2>
              <button type="button" onClick={() => loadEverything(email)} disabled={loading}>
                {loading ? 'Refreshing…' : 'Refresh'}
              </button>
            </div>
            <div className="digest-list">
              {digest.map((entry) => (
                <DigestCard
                  key={entry.ticker}
                  entry={entry}
                  onRemove={() => handleRemove(itemIdByTicker[entry.ticker])}
                />
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  )
}

export default App
