import { API_BASE_URL } from './health'

export async function fetchWeather(latitude, longitude, locationLabel = '') {
  const params = new URLSearchParams({
    latitude: String(latitude),
    longitude: String(longitude),
  })
  if (locationLabel) params.set('location_label', locationLabel)

  const response = await fetch(`${API_BASE_URL}/weather?${params.toString()}`)
  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const message = data?.detail?.message || data?.detail || data?.message || `天气获取失败：HTTP ${response.status}`
    throw new Error(message)
  }

  return data.weather
}
