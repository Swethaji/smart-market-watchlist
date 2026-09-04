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

export default function DigestCard({ entry, onRemove }) {
  const pctChange = entry.pct_change_since_last_check
  const isUp = pctChange !== null && pctChange !== undefined && pctChange > 0
  const isDown = pctChange !== null && pctChange !== undefined && pctChange < 0

  return (
    <div className={`digest-card${entry.is_unusual_move ? ' unusual' : ''}`}>
      <div className="digest-card-header">
        <span className="ticker">{entry.ticker}</span>
        {entry.current_price !== null && entry.current_price !== undefined && (
          <span className="price">${entry.current_price.toFixed(2)}</span>
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
        <div className={`pct-change ${isUp ? 'up' : isDown ? 'down' : ''}`}>
          {formatPct(pctChange)} <span className="since">since you last looked</span>
        </div>
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
