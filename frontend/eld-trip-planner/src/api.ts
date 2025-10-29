import axios from 'axios'
import type { RouteData } from './types'

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 20000,
})

export async function getRouteAndLogs(payload: {
  current_location: string
  pickup_location: string
  dropoff_location: string
  current_cycle_hours: number
}): Promise<RouteData> {
  const res = await api.post('/api/route/', payload)
  return res.data as RouteData
}
