import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const PERIODS = [
  { key: '1h', label: '1h' },
  { key: '6h', label: '6h' },
  { key: '24h', label: '24h' },
]

function parsePrice(value) {
  if (value == null) return 0
  const n = Number(value)
  return Number.isFinite(n) ? n : 0
}

function formatTime(ts) {
  if (!ts) return ''
  try {
    const d = new Date(ts)
    return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
  } catch {
    return String(ts)
  }
}

export default function PriceChart({
  symbol,
  priceHistory = [],
  activeRange = '24h',
  onRangeSelect,
}) {
  const hasSymbol = Boolean(symbol?.trim())
  const data = (Array.isArray(priceHistory) ? priceHistory : [])
    .map((item) => ({
      ...item,
      price: parsePrice(item?.price),
      timestamp: item?.timestamp ?? '',
      timeLabel: formatTime(item?.timestamp),
    }))
    .filter((d) => d.timeLabel !== '' || d.timestamp !== '')

  const firstPrice = data.length > 0 ? data[0].price : 0
  const lastPrice = data.length > 0 ? data[data.length - 1].price : 0
  const isUp = lastPrice > firstPrice
  const lineColor = isUp ? '#34d399' : '#f87171' // emerald-400 / red-400

  if (!hasSymbol) {
    return (
      <div className="rounded border border-zinc-600/60 bg-zinc-800/80 p-8 font-mono text-center text-zinc-400">
        Select a symbol above to view chart
      </div>
    )
  }

  return (
    <div className="rounded border border-zinc-600/60 bg-zinc-800/80 p-4 font-mono">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold uppercase tracking-wider text-white">{symbol}</h2>
        <div className="flex gap-1">
          {PERIODS.map(({ key, label }) => (
            <button
              key={key}
              type="button"
              onClick={() => onRangeSelect?.(key)}
              className={`rounded px-3 py-1.5 text-xs font-medium transition-colors ${
                activeRange === key
                  ? 'bg-zinc-600 text-white'
                  : 'bg-zinc-700/60 text-zinc-400 hover:bg-zinc-600 hover:text-white'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      {data.length === 0 ? (
        <div className="flex h-64 items-center justify-center text-zinc-500 text-sm">
          No price history for this range
        </div>
      ) : (
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
              <defs>
                <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={lineColor} stopOpacity={0.35} />
                  <stop offset="100%" stopColor={lineColor} stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="timeLabel"
                tick={{ fill: '#a1a1aa', fontSize: 11 }}
                axisLine={{ stroke: '#52525b' }}
                tickLine={{ stroke: '#52525b' }}
              />
              <YAxis
                dataKey="price"
                domain={['auto', 'auto']}
                tick={{ fill: '#a1a1aa', fontSize: 11 }}
                axisLine={{ stroke: '#52525b' }}
                tickLine={{ stroke: '#52525b' }}
                tickFormatter={(v) => (Number.isFinite(v) ? String(Number(v).toFixed(2)) : '')}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (!active || !payload?.length) return null
                  const p = payload[0]?.payload
                  return (
                    <div className="rounded border border-zinc-600 bg-zinc-800 px-3 py-2 text-xs text-white shadow-xl">
                      <div className="text-zinc-400">{formatTime(p?.timestamp)}</div>
                      <div className="mt-0.5 tabular-nums">
                        Price: <span className="text-white">{p?.price != null ? Number(p.price).toFixed(2) : '—'}</span>
                      </div>
                    </div>
                  )
                }}
              />
              <Area
                type="monotone"
                dataKey="price"
                stroke={lineColor}
                strokeWidth={2}
                fill="url(#priceGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
