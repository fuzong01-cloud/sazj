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

export async function streamPredictImage(
  file,
  environment = null,
  providerId = null,
  conversationId = null,
  prompt = '',
  deepThinking = false,
  handlers = {},
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

  const response = await fetch(`${API_BASE_URL}/predict/stream`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body,
  })

  if (!response.ok || !response.body) {
    const data = await response.json().catch(() => ({}))
    const message = data?.detail?.message || data?.detail || data?.message || `识别失败：HTTP ${response.status}`
    const error = new Error(message)
    error.conversationId = data?.detail?.conversation_id
    throw error
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const frames = buffer.split('\n\n')
    buffer = frames.pop() || ''
    for (const frame of frames) {
      const line = frame
        .split('\n')
        .find((item) => item.startsWith('data:'))
      if (!line) continue
      const event = JSON.parse(line.replace(/^data:\s*/, ''))
      if (event.type === 'meta') handlers.onMeta?.(event)
      if (event.type === 'reasoning') handlers.onReasoning?.(event.text || '')
      if (event.type === 'content') handlers.onContent?.(event.text || '')
      if (event.type === 'result') handlers.onResult?.(event.result)
      if (event.type === 'error') {
        const error = new Error(event.message || '图片识别失败')
        error.conversationId = event.conversation_id
        throw error
      }
      if (event.type === 'done') handlers.onDone?.(event)
    }
  }
}
