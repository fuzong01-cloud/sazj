import { API_BASE_URL } from './health'

const TOKEN_KEY = 'sazj_access_token'

export function getAccessToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setAccessToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token)
  } else {
    localStorage.removeItem(TOKEN_KEY)
  }
}

export function getAuthHeaders() {
  const token = getAccessToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function registerUser(payload) {
  return submitAuth('/auth/register', payload)
}

export async function loginUser(payload) {
  return submitAuth('/auth/login', payload)
}

export async function fetchMe() {
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    headers: getAuthHeaders(),
  })
  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const message = data?.detail?.message || data?.detail || data?.message || `当前用户获取失败：HTTP ${response.status}`
    throw new Error(message)
  }

  return data
}

export async function updateProfile(payload) {
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify(payload),
  })
  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const message = data?.detail?.message || data?.detail || data?.message || `用户资料保存失败：HTTP ${response.status}`
    throw new Error(message)
  }

  return data
}

export async function changePassword(payload) {
  const response = await fetch(`${API_BASE_URL}/auth/me/password`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    const message = data?.detail?.message || data?.detail || data?.message || `密码修改失败：HTTP ${response.status}`
    throw new Error(message)
  }
}

export async function uploadAvatar(file) {
  const body = new FormData()
  body.append('file', file)

  const response = await fetch(`${API_BASE_URL}/auth/me/avatar`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body,
  })
  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const message = data?.detail?.message || data?.detail || data?.message || `头像上传失败：HTTP ${response.status}`
    throw new Error(message)
  }

  return data
}

async function submitAuth(path, payload) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    const message = data?.detail?.message || data?.detail || data?.message || `认证失败：HTTP ${response.status}`
    throw new Error(message)
  }

  setAccessToken(data.access_token)
  return data
}
