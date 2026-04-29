import { API_BASE_URL } from './health'

export async function fetchEnabledProviders(providerType = '') {
  const params = new URLSearchParams()
  if (providerType) params.set('provider_type', providerType)

  const suffix = params.toString() ? `?${params.toString()}` : ''
  const response = await fetch(`${API_BASE_URL}/providers/enabled${suffix}`)
  const data = await response.json().catch(() => [])

  if (!response.ok) {
    const message = data?.detail?.message || data?.detail || data?.message || `模型列表获取失败：HTTP ${response.status}`
    throw new Error(message)
  }

  return data
}
