import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
})

export function getLatestPrices() {
  return api.get('/prices')
}

export function getPriceHistory(symbol, hours = 24) {
  return api.get(`/prices/${encodeURIComponent(symbol)}`, { params: { hours } })
}

export function getAnomalies(limit = 20) {
  return api.get('/anomalies', { params: { limit } })
}

export function getCandles(symbol, limit = 50) {
  return api.get(`/candles/${encodeURIComponent(symbol)}`, { params: { limit } })
}

export function getStats() {
  return api.get('/stats')
}
