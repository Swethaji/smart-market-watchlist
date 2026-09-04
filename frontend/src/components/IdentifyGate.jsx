import { useState } from 'react'

// The whole "login" system for this hackathon build: type an email, we
// find-or-create a matching user on the backend. No password.
export default function IdentifyGate({ onIdentified }) {
  const [email, setEmail] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    const trimmed = email.trim()
    if (!trimmed) return

    setSubmitting(true)
    setError(null)
    try {
      await onIdentified(trimmed)
    } catch (err) {
      setError(err.message || 'Could not reach the backend.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="identify-screen">
      <div className="identify-card">
        <span className="logo-mark identify-logo" aria-hidden="true">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M3 17l6-6 4 4 8-8" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M15 7h6v6" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </span>
        <h1>Smart Market Watchlist</h1>
        <p className="subtitle">
          Enter your email to load your watchlist. No password needed for this demo.
        </p>
        <form onSubmit={handleSubmit}>
          <input
            type="email"
            required
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoFocus
          />
          <button type="submit" disabled={submitting}>
            {submitting ? 'Loading…' : 'Continue'}
          </button>
        </form>
        {error && <p className="error-text">{error}</p>}
      </div>
    </div>
  )
}
