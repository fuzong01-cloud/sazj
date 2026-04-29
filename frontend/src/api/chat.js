import { getAuthHeaders } from './auth'
import { API_BASE_URL } from './health'

export async function askAssistant(payload) {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify(payload),
  })
  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const message = data?.detail?.message || data?.detail || data?.message || `AI 助手调用失败：HTTP ${response.status}`
    throw new Error(message)
  }

  return data
}
