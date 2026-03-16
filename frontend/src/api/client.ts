import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL}/api/v1`
  : '/api/v1'

export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

// Inject API key from localStorage if present
api.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem('scanarr_api_key')
  if (apiKey) {
    config.headers['X-Api-Key'] = apiKey
  }
  return config
})

// Global error handler
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      // Could redirect to login page here
      console.warn('Unauthenticated — check your API key or credentials')
    }
    return Promise.reject(err)
  },
)

export default api
