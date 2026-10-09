import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8001',
  timeout: 15000,
})

export const analyzeTranscript = async (payload) => {
  const response = await api.post('/api/analyze', payload)
  return response.data
}

export const getScenarios = async () => {
  const response = await api.get('/api/scenarios')
  return response.data
}
