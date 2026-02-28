export default function PriceTicker({ prices = {}, onSelectSymbol }) {
  const symbols = Object.keys(prices).filter(Boolean)
  if (symbols.length === 0) return null

  return (
    <div className="flex flex-wrap gap-3 font-mono">
      {symbols.map((symbol) => {
        const item = prices[symbol]
        const price = item?.price != null ? String(item.price) : '—'
        const changePercent = item?.change_percent != null ? Number(item.change_percent) : null
        const isPositive = changePercent != null && changePercent >= 0
        const isNegative = changePercent != null && changePercent < 0

        return (
          <button
            key={symbol}
            type="button"
            onClick={() => onSelectSymbol?.(symbol)}
            className="flex min-w-[120px] flex-col rounded border border-zinc-600/60 bg-zinc-800/80 px-4 py-3 text-left text-white shadow-sm transition-shadow hover:border-zinc-500/80 hover:shadow-md hover:shadow-amber-500/10 focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:ring-offset-2 focus:ring-offset-zinc-900"
          >
            <div className="text-xs uppercase tracking-wider text-zinc-400">{symbol}</div>
            <div className="mt-1 text-xl tabular-nums text-white">{price}</div>
            <div className="mt-0.5 flex items-center gap-1 text-sm">
              {changePercent != null ? (
                <>
                  <span
                    className={`tabular-nums ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}
                    aria-hidden
                  >
                    {isPositive ? '▲' : '▼'}
                  </span>
                  <span
                    className={`tabular-nums ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}
                  >
                    {isPositive ? '+' : ''}
                    {changePercent.toFixed(2)}%
                  </span>
                </>
              ) : (
                <span className="text-zinc-500">—</span>
              )}
            </div>
          </button>
        )
      })}
    </div>
  )
}
