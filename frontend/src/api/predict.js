import { getAuthHeaders } from './auth'
import { API_BASE_URL } from './health'

export async function predictImage(
  file,
  environment = null,
  providerId = null,
  conversationId = null,
  prompt = '',
  deepThinking = false,
) {
  const body = new FormData()
  body.append('file', file)
  if (providerId) body.append('provider_id', String(providerId))
  if (conversationId) body.append('conversation_id', String(conversationId))
  if (prompt) body.append('prompt', prompt)
  body.append('deep_thinking', deepThinking ? 'true' : 'false')
  if (environment?.latitude !== undefined && environment?.longitude !== undefined) {
    body.append('latitude', String(environment.latitude))
    body.append('longitude', String(environment.longitude))
    if (environment.location_label) body.append('location_label', environment.location_label)
  }

  const response = await fetch(`${API_BASE_URL}/predict`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body,
  })

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const message = data?.detail?.message || data?.detail || data?.message || `识别失败：HTTP ${response.status}`
    const error = new Error(message)
    error.conversationId = data?.detail?.conversation_id
    throw error
  }

  return data
}
