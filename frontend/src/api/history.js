import { getAuthHeaders } from './auth'
import { API_BASE_URL } from './health'

export async function fetchHistory(limit = 10, offset = 0) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  const response = await fetch(`${API_BASE_URL}/conversations?${params.toString()}`, {
    headers: getAuthHeaders(),
  })
  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const message = data?.detail?.message || data?.detail || data?.message || `历史记录获取失败：HTTP ${response.status}`
    throw new Error(message)
  }

  return data
}

export async function fetchHistoryRecord(id) {
  const response = await fetch(`${API_BASE_URL}/conversations/${id}`, {
    headers: getAuthHeaders(),
  })
  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const message = data?.detail?.message || data?.detail || data?.message || `历史详情获取失败：HTTP ${response.status}`
    throw new Error(message)
  }

  return data
}

export async function deleteHistoryRecord(id) {
  const response = await fetch(`${API_BASE_URL}/conversations/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    const message = data?.detail?.message || data?.detail || data?.message || `历史记录删除失败：HTTP ${response.status}`
    throw new Error(message)
  }
}

export async function renameHistoryRecord(id, title) {
  const response = await fetch(`${API_BASE_URL}/conversations/${id}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify({ title }),
  })
  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const message = data?.detail?.message || data?.detail || data?.message || `历史记录重命名失败：HTTP ${response.status}`
    throw new Error(message)
  }

  return data
}
