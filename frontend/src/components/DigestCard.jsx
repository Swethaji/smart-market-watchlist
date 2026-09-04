function formatPct(value) {
  if (value === null || value === undefined) return null
  const pct = value * 100
  const sign = pct > 0 ? '+' : ''
  return `${sign}${pct.toFixed(2)}%`
}

function formatVolume(volume) {
  if (!volume) return '—'
  if (volume >= 1_000_000) return `${(volume / 1_000_000).toFixed(1)}M`
  if (volume >= 1_000) return `${(volume / 1_000).toFixed(0)}K`
  return String(volume)
}

function formatPrice(price) {
  return price === null || price === undefined ? null : `$${price.toFixed(2)}`
}

export default function DigestCard({ entry, rank, onRemove }) {
  const pctChange = entry.pct_change_since_last_check
  const isUp = pctChange !== null && pctChange !== undefined && pctChange > 0
  const isDown = pctChange !== null && pctChange !== undefined && pctChange < 0
  const direction = isUp ? '▲' : isDown ? '▼' : ''

  return (
    <div className={`digest-card${entry.is_unusual_move ? ' unusual' : ''}`}>
      {entry.is_unusual_move && rank === 0 && <div className="top-pick">Most notable</div>}

      <div className="digest-card-header">
        <span className="ticker">{entry.ticker}</span>
        {entry.current_price !== null && entry.current_price !== undefined && (
          <span className="price">{formatPrice(entry.current_price)}</span>
        )}
        <button
          type="button"
          className="remove-btn"
          onClick={onRemove}
          title={`Remove ${entry.ticker} from watchlist`}
        >
          ×
        </button>
      </div>

      {pctChange !== null && pctChange !== undefined ? (
        <>
          <div className={`pct-change ${isUp ? 'up' : isDown ? 'down' : ''}`}>
            <span className="direction">{direction}</span>
            {formatPct(pctChange)}
            <span className="since">since you last looked</span>
          </div>
          {entry.price_at_last_check !== null && entry.price_at_last_check !== undefined && (
            <div className="compare-note">
              was {formatPrice(entry.price_at_last_check)} at your last check
            </div>
          )}
        </>
      ) : (
        entry.note && <div className="note">{entry.note}</div>
      )}

      <div className="badges">
        {entry.is_unusual_move && <span className="badge badge-unusual">Unusual move</span>}
        {entry.volume_confirmed && <span className="badge badge-volume">Volume confirmed</span>}
        {entry.is_52_week_high && <span className="badge badge-high">New high</span>}
        {entry.is_52_week_low && <span className="badge badge-low">New low</span>}
        {entry.data_source === 'cache' && <span className="badge badge-cache">Cached data</span>}
        {entry.data_source === 'unavailable' && <span className="badge badge-error">Data unavailable</span>}
      </div>

      <div className="digest-card-footer">
        <span>Volume: {formatVolume(entry.current_volume)}</span>
        {entry.normal_daily_move_pct !== null && entry.normal_daily_move_pct !== undefined && (
          <span>Normal daily move for {entry.ticker}: ~{(entry.normal_daily_move_pct * 100).toFixed(2)}%</span>
        )}
      </div>
    </div>
  )
}
