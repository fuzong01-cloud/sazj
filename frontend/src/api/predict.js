import { API_BASE_URL } from './health'
import { getAuthHeaders } from './auth'

export async function predictImage(file) {
  const body = new FormData()
  body.append('file', file)

  const response = await fetch(`${API_BASE_URL}/predict`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body,
  })

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const message = data?.detail?.message || data?.message || `识别失败：HTTP ${response.status}`
    throw new Error(message)
  }

  return data
}
