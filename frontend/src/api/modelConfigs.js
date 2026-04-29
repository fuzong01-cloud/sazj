import { getAuthHeaders } from './auth'
import { API_BASE_URL } from './health'

function parseError(data, fallback) {
  return data?.detail?.message || data?.detail || data?.message || fallback
}

export async function fetchModelConfigs() {
  const response = await fetch(`${API_BASE_URL}/model-configs`, {
    headers: getAuthHeaders(),
  })
  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(parseError(data, `模型配置获取失败：HTTP ${response.status}`))
  }

  return data
}

export async function createModelConfig(payload) {
  const response = await fetch(`${API_BASE_URL}/model-configs`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify(payload),
  })
  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(parseError(data, `模型配置创建失败：HTTP ${response.status}`))
  }

  return data
}

export async function updateModelConfig(id, payload) {
  const response = await fetch(`${API_BASE_URL}/model-configs/${id}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify(payload),
  })
  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(parseError(data, `模型配置更新失败：HTTP ${response.status}`))
  }

  return data
}

export async function deleteModelConfig(id) {
  const response = await fetch(`${API_BASE_URL}/model-configs/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(parseError(data, `模型配置删除失败：HTTP ${response.status}`))
  }
}
