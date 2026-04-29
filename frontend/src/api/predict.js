import { getAuthHeaders } from './auth'
import { API_BASE_URL } from './health'

export async function predictImage(file, environment = null) {
  const body = new FormData()
  body.append('file', file)
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
    const message = data?.detail?.message || data?.message || `识别失败：HTTP ${response.status}`
    throw new Error(message)
  }

  return data
}
