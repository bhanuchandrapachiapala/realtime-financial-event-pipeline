export default function StatsBar({ stats }) {
  if (!stats) return null

  const {
    events_last_hour = 0,
    anomalies_24h = 0,
    symbols_tracked = [],
    pipeline_status = 'unknown',
  } = stats

  const isActive = String(pipeline_status).toLowerCase() === 'operational' || String(pipeline_status).toLowerCase() === 'active'
  const symbolCount = Array.isArray(symbols_tracked) ? symbols_tracked.length : 0

  return (
    <div className="flex flex-wrap gap-3 font-mono text-sm">
      <div className="flex-1 min-w-[140px] rounded border border-zinc-600/60 bg-zinc-800/80 px-4 py-3 text-white shadow-sm">
        <div className="text-zinc-400 text-xs uppercase tracking-wider">Events / Hour</div>
        <div className="mt-0.5 text-lg tabular-nums text-white">{events_last_hour}</div>
      </div>
      <div className="flex-1 min-w-[140px] rounded border border-zinc-600/60 bg-zinc-800/80 px-4 py-3 text-white shadow-sm">
        <div className="text-zinc-400 text-xs uppercase tracking-wider">Symbols Tracked</div>
        <div className="mt-0.5 text-lg tabular-nums text-white">{symbolCount}</div>
      </div>
      <div className="flex-1 min-w-[140px] rounded border border-zinc-600/60 bg-zinc-800/80 px-4 py-3 text-white shadow-sm">
        <div className="text-zinc-400 text-xs uppercase tracking-wider">Anomalies 24h</div>
        <div
          className={`mt-0.5 text-lg tabular-nums ${anomalies_24h > 0 ? 'text-red-400' : 'text-white'}`}
        >
          {anomalies_24h}
        </div>
      </div>
      <div className="flex-1 min-w-[140px] rounded border border-zinc-600/60 bg-zinc-800/80 px-4 py-3 text-white shadow-sm">
        <div className="text-zinc-400 text-xs uppercase tracking-wider">Pipeline Status</div>
        <div className="mt-0.5 flex items-center gap-2">
          <span
            className={`h-2 w-2 shrink-0 rounded-full ${isActive ? 'bg-emerald-500' : 'bg-red-500'}`}
            aria-hidden
          />
          <span className="tabular-nums">{isActive ? 'Active' : 'Down'}</span>
        </div>
      </div>
    </div>
  )
}
