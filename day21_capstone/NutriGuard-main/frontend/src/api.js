const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const apiRequest = async (path, options = {}) => {
  const headers = {
    'ngrok-skip-browser-warning': 'true',
    ...(options.headers || {}),
  }
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers })
  const data = await response.json()
  if (!response.ok) throw new Error(data.detail || 'Request failed')
  return data
}
