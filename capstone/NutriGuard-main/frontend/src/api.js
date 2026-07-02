const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const TOKEN_KEY = 'nutriguard_access_token'
const USER_KEY = 'nutriguard_user'

export const getAuthToken = () => localStorage.getItem(TOKEN_KEY)
export const getStoredUser = () => {
  try {
    const value = localStorage.getItem(USER_KEY)
    return value ? JSON.parse(value) : null
  } catch {
    localStorage.removeItem(USER_KEY)
    return null
  }
}

export const setAuthToken = (token) => {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token)
    return
  }
  localStorage.removeItem(TOKEN_KEY)
}

export const setStoredUser = (user) => {
  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user))
    return
  }
  localStorage.removeItem(USER_KEY)
}

export const apiRequest = async (path, options = {}) => {
  const token = getAuthToken()
  const headers = {
    'ngrok-skip-browser-warning': 'true',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  }
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers })
  const text = await response.text()
  const data = text ? JSON.parse(text) : {}
  if (!response.ok) {
    const error = new Error(data.detail || `Request failed with status ${response.status}`)
    error.status = response.status
    error.data = data
    throw error
  }
  return data
}
