import { useCallback, useEffect, useState } from 'react'
import AnomalyFeed from './components/AnomalyFeed'
import PriceChart from './components/PriceChart'
import PriceTicker from './components/PriceTicker'
import QueryPanel from './components/QueryPanel'
import StatsBar from './components/StatsBar'
import {
  getAnomalies,
  getLatestPrices,
  getPriceHistory,
  getStats,
} from './services/api'

function App() {
  const [prices, setPrices] = useState({})
  const [anomalies, setAnomalies] = useState([])
  const [stats, setStats] = useState(null)
  const [priceHistory, setPriceHistory] = useState([])
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL')
  const [timeRange, setTimeRange] = useState(24)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [autoRefresh, setAutoRefresh] = useState(true)

  const fetchDashboard = useCallback(async () => {
    try {
      setError(null)
      const [pricesRes, statsRes, anomaliesRes] = await Promise.all([
        getLatestPrices(),
        getStats(),
        getAnomalies(20),
      ])
      setPrices(pricesRes.data?.prices ?? {})
      setStats(statsRes.data ?? null)
      setAnomalies(anomaliesRes.data?.anomalies ?? [])
    } catch (err) {
      setError(err?.response?.data?.error || err?.message || 'Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchPriceHistory = useCallback(async () => {
    if (!selectedSymbol) return
    try {
      const res = await getPriceHistory(selectedSymbol, timeRange)
      setPriceHistory(res.data?.prices ?? [])
    } catch (err) {
      setPriceHistory([])
    }
  }, [selectedSymbol, timeRange])

  useEffect(() => {
    fetchDashboard()
  }, [fetchDashboard])

  useEffect(() => {
    if (!autoRefresh) return
    const id = setInterval(fetchDashboard, 60_000)
    return () => clearInterval(id)
  }, [autoRefresh, fetchDashboard])

  useEffect(() => {
    fetchPriceHistory()
  }, [fetchPriceHistory])

  const activeRangeKey = timeRange === 1 ? '1h' : timeRange === 6 ? '6h' : '24h'
  const handleRangeSelect = useCallback((key) => {
    setTimeRange(key === '1h' ? 1 : key === '6h' ? 6 : 24)
  }, [])

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="mx-auto max-w-7xl px-4 py-6">
        {/* Header */}
        <header className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="flex items-center gap-2 font-mono text-2xl font-bold tracking-tight">
              <span aria-hidden>⚡</span> FinPulse
            </h1>
            <p className="mt-0.5 font-mono text-sm text-zinc-400">
              Real-Time Financial Event Processing Engine
            </p>
          </div>
          <button
            type="button"
            onClick={() => setAutoRefresh((v) => !v)}
            className={`rounded border px-3 py-1.5 font-mono text-sm transition-colors ${
              autoRefresh
                ? 'border-amber-500/60 bg-amber-500/20 text-amber-400'
                : 'border-zinc-600 bg-zinc-800 text-zinc-400'
            }`}
          >
            Auto-refresh {autoRefresh ? 'ON' : 'OFF'}
          </button>
        </header>

        {/* Error banner */}
        {error && (
          <div
            className="mb-4 flex animate-fade-in items-center justify-between rounded border border-red-500/50 bg-red-950/30 px-4 py-3 font-mono text-sm text-red-200"
            role="alert"
          >
            <span>{error}</span>
            <button
              type="button"
              onClick={() => setError(null)}
              className="shrink-0 rounded p-1 text-red-400 hover:bg-red-500/20 hover:text-red-300"
              aria-label="Dismiss error"
            >
              ✕
            </button>
          </div>
        )}

        {/* Loading overlay */}
        {loading && (
          <div className="mb-6 flex justify-center py-12">
            <div
              className="h-10 w-10 animate-spin rounded-full border-2 border-amber-500/30 border-t-amber-500"
              aria-hidden
            />
          </div>
        )}

        {/* Main content with fade-in when data is present */}
        {!loading && (
          <div className="animate-fade-in space-y-6">
            <StatsBar stats={stats} />

            <section>
              <h2 className="mb-2 font-mono text-xs uppercase tracking-wider text-zinc-500">
                Live prices
              </h2>
              <PriceTicker prices={prices} onSelectSymbol={setSelectedSymbol} />
            </section>

            <section>
              <PriceChart
                symbol={selectedSymbol}
                priceHistory={priceHistory}
                activeRange={activeRangeKey}
                onRangeSelect={handleRangeSelect}
              />
            </section>

            <section className="grid grid-cols-1 gap-6 lg:grid-cols-3">
              <div className="lg:col-span-2">
                <AnomalyFeed anomalies={anomalies} />
              </div>
              <div>
                <QueryPanel />
              </div>
            </section>
          </div>
        )}

        {/* Footer */}
        <footer className="mt-12 border-t border-zinc-800 py-6 font-mono text-center text-sm text-zinc-500">
          <p>Built by Bhanu Chandra Pachipala</p>
          <p className="mt-1">Powered by AWS Kinesis · Lambda · DynamoDB</p>
        </footer>
      </div>
    </div>
  )
}

export default App
