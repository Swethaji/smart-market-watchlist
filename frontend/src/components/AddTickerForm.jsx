import { useState } from 'react'

export default function AddTickerForm({ onAdd }) {
  const [ticker, setTicker] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    const trimmed = ticker.trim()
    if (!trimmed) return

    setSubmitting(true)
    setError(null)
    try {
      await onAdd(trimmed)
      setTicker('')
    } catch (err) {
      setError(err.message || 'Could not add ticker.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="add-ticker-form" onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Add a ticker, e.g. AAPL"
        value={ticker}
        onChange={(e) => setTicker(e.target.value.toUpperCase())}
        maxLength={10}
      />
      <button type="submit" disabled={submitting}>
        {submitting ? 'Adding…' : 'Add'}
      </button>
      {error && <p className="error-text">{error}</p>}
    </form>
  )
}
