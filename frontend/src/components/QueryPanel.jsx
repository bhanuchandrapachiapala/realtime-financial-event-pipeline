import { useState } from 'react'

const PRESET_QUERIES = [
  {
    label: 'Avg price by symbol',
    sql: `SELECT symbol, AVG(CAST(price AS DOUBLE)) AS avg_price
FROM live_prices
GROUP BY symbol
ORDER BY avg_price DESC;`,
  },
  {
    label: 'Max price spikes',
    sql: `SELECT symbol, MAX(CAST(price AS DOUBLE)) AS max_price, timestamp
FROM live_prices
GROUP BY symbol, timestamp
ORDER BY max_price DESC
LIMIT 10;`,
  },
  {
    label: 'Volume trends',
    sql: `SELECT symbol, SUM(volume) AS total_volume, DATE(timestamp) AS day
FROM live_prices
GROUP BY symbol, DATE(timestamp)
ORDER BY day DESC, total_volume DESC;`,
  },
]

export default function QueryPanel() {
  const [sql, setSql] = useState('')
  const [hasRun, setHasRun] = useState(false)

  function handlePreset(preset) {
    setSql(preset.sql)
    setHasRun(false)
  }

  function handleRun() {
    setHasRun(true)
  }

  return (
    <div className="flex flex-col rounded border border-zinc-600/60 bg-zinc-800/80 font-mono">
      <div className="shrink-0 border-b border-zinc-600/60 px-4 py-2">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
          Athena query (demo)
        </h3>
      </div>
      <div className="flex flex-wrap gap-2 p-3">
        {PRESET_QUERIES.map((preset) => (
          <button
            key={preset.label}
            type="button"
            onClick={() => handlePreset(preset)}
            className="rounded border border-zinc-600 bg-zinc-700/60 px-3 py-1.5 text-xs text-zinc-300 transition-colors hover:bg-zinc-600 hover:text-white"
          >
            {preset.label}
          </button>
        ))}
      </div>
      <div className="px-3 pb-3">
        <textarea
          value={sql}
          onChange={(e) => setSql(e.target.value)}
          placeholder="Enter SQL or use a preset above..."
          rows={6}
          className="w-full rounded border border-zinc-600 bg-zinc-900/80 px-3 py-2 text-sm text-white placeholder-zinc-500 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
          spellCheck={false}
        />
        <div className="mt-2 flex justify-end">
          <button
            type="button"
            onClick={handleRun}
            className="rounded bg-amber-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 focus:ring-offset-zinc-800"
          >
            Run Query
          </button>
        </div>
      </div>
      <div className="min-h-[120px] border-t border-zinc-600/60 p-3">
        <div className="mb-2 text-xs uppercase tracking-wider text-zinc-500">
          Results
        </div>
        {!hasRun ? (
          <div className="flex items-center justify-center rounded border border-dashed border-zinc-600 bg-zinc-900/40 py-8 text-sm text-zinc-500">
            Run a query to see results (Athena integration optional)
          </div>
        ) : (
          <div className="rounded border border-zinc-600 bg-zinc-900/40 p-4 text-sm text-zinc-500">
            Placeholder: results would appear here when Athena is connected.
          </div>
        )}
      </div>
    </div>
  )
}
