import { useMemo } from 'react'

function formatRelativeTime(isoString) {
  if (!isoString) return '—'
  try {
    const date = new Date(isoString)
    const now = new Date()
    const sec = Math.floor((now - date) / 1000)
    if (sec < 60) return 'just now'
    const min = Math.floor(sec / 60)
    if (min < 60) return `${min} minute${min !== 1 ? 's' : ''} ago`
    const hr = Math.floor(min / 60)
    if (hr < 24) return `${hr} hour${hr !== 1 ? 's' : ''} ago`
    const day = Math.floor(hr / 24)
    return `${day} day${day !== 1 ? 's' : ''} ago`
  } catch {
    return '—'
  }
}

function formatPrice(value) {
  if (value == null || value === '') return '—'
  const n = Number(value)
  return Number.isFinite(n) ? n.toFixed(2) : String(value)
}

export default function AnomalyFeed({ anomalies = [] }) {
  const sorted = useMemo(() => {
    const list = Array.isArray(anomalies) ? [...anomalies] : []
    return list.sort((a, b) => {
      const ta = new Date(a?.detected_at || 0).getTime()
      const tb = new Date(b?.detected_at || 0).getTime()
      return tb - ta
    })
  }, [anomalies])

  return (
    <div className="flex max-h-[400px] flex-col rounded border border-zinc-600/60 bg-zinc-800/80 font-mono">
      <div className="shrink-0 border-b border-zinc-600/60 px-4 py-2">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
          Anomaly feed
        </h3>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto p-2">
        {sorted.length === 0 ? (
          <div className="flex flex-1 items-center justify-center py-12 text-center text-sm text-zinc-500">
            No anomalies detected — markets are calm
          </div>
        ) : (
          <ul className="space-y-2">
            {sorted.map((item, index) => {
              const direction = String(item?.direction || '').toUpperCase()
              const severity = String(item?.severity || '').toUpperCase()
              const isSpike = direction === 'SPIKE'
              const isHigh = severity === 'HIGH'
              const borderClass = isHigh
                ? 'border-l-red-500'
                : 'border-l-amber-400'
              return (
                <li
                  key={`${item?.symbol}-${item?.detected_at}-${index}`}
                  className={`rounded border border-zinc-600/60 border-l-4 bg-zinc-800/90 px-3 py-2 ${borderClass}`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="font-semibold uppercase text-white">
                      {item?.symbol ?? '—'}
                    </span>
                    <span className="text-xs text-zinc-500">
                      {formatRelativeTime(item?.detected_at)}
                    </span>
                  </div>
                  <div className="mt-1.5 flex flex-wrap items-center gap-2">
                    <span
                      className={`rounded px-1.5 py-0.5 text-xs font-medium ${
                        isSpike ? 'bg-amber-500/20 text-amber-400' : 'bg-red-500/20 text-red-400'
                      }`}
                    >
                      {direction || '—'}
                    </span>
                    <span
                      className={`rounded px-1.5 py-0.5 text-xs font-medium ${
                        isHigh ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400'
                      }`}
                    >
                      {severity || '—'}
                    </span>
                  </div>
                  <div className="mt-1.5 grid grid-cols-2 gap-x-4 gap-y-0.5 text-xs text-zinc-400">
                    <span>Price: <span className="tabular-nums text-white">{formatPrice(item?.current_price)}</span></span>
                    <span>Deviation: <span className="tabular-nums text-white">{formatPrice(item?.deviation_percent)}%</span></span>
                    <span>Z-score: <span className="tabular-nums text-white">{formatPrice(item?.z_score)}</span></span>
                  </div>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </div>
  )
}
