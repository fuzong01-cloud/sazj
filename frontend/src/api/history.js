import { API_BASE_URL } from './health'

export async function fetchHistory(limit = 20) {
  const params = new URLSearchParams({ limit: String(limit) })
  const response = await fetch(`${API_BASE_URL}/history?${params.toString()}`)
  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const message = data?.detail?.message || data?.detail || data?.message || `历史记录获取失败：HTTP ${response.status}`
    throw new Error(message)
  }

  return data
}
