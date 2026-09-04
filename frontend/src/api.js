// Small fetch wrapper for the FastAPI backend. No auth/session -- every
// watchlist call passes the user's email as a query parameter, and the
// backend finds-or-creates a user row for it (see backend/app/crud.py).

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })

  if (!response.ok) {
    let detail = response.statusText
    try {
      const body = await response.json()
      detail = body.detail || detail
    } catch {
      // response wasn't JSON -- fall back to statusText above
    }
    throw new Error(detail)
  }

  if (response.status === 204) return null
  return response.json()
}

export function identify(email) {
  return request('/users/identify', {
    method: 'POST',
    body: JSON.stringify({ email }),
  })
}

export function getWatchlist(email) {
  return request(`/watchlist?email=${encodeURIComponent(email)}`)
}

export function addTicker(email, ticker) {
  return request(`/watchlist?email=${encodeURIComponent(email)}`, {
    method: 'POST',
    body: JSON.stringify({ ticker }),
  })
}

export function removeTicker(email, itemId) {
  return request(`/watchlist/${itemId}?email=${encodeURIComponent(email)}`, {
    method: 'DELETE',
  })
}

export function getDigest(email) {
  return request(`/watchlist/digest?email=${encodeURIComponent(email)}`)
}
