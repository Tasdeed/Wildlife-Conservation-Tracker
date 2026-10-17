import type {
  ModelStats,
  Prediction,
  Species,
  SpeciesFilters,
  SpeciesListResponse,
  SpeciesLocation,
} from './types'

// `||` (not `??`) so an empty-string env var also falls back to localhost.
const BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001'

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`)
  if (!res.ok) {
    let detail = ''
    try {
      const body = await res.json()
      detail = body?.error ? `: ${body.error}` : ''
    } catch {
      // non-JSON error body; ignore
    }
    throw new Error(`Request failed (${res.status})${detail}`)
  }
  return res.json() as Promise<T>
}

export function getModelStats(): Promise<ModelStats> {
  return getJSON<ModelStats>('/api/model/stats')
}

export function getSpecies(filters: SpeciesFilters = {}): Promise<SpeciesListResponse> {
  const params = new URLSearchParams()
  if (filters.category) params.set('category', filters.category)
  if (filters.trend) params.set('trend', filters.trend)
  if (filters.limit != null) params.set('limit', String(filters.limit))
  const qs = params.toString()
  return getJSON<SpeciesListResponse>(`/api/species${qs ? `?${qs}` : ''}`)
}

export function getSpeciesById(id: number | string): Promise<Species> {
  return getJSON<Species>(`/api/species/${id}`)
}

export function getPrediction(id: number | string): Promise<Prediction> {
  return getJSON<Prediction>(`/api/predict/${id}`)
}

// Phase 4 endpoint — returns { count, locations: [...] }.
export async function getLocations(
  filters: SpeciesFilters = {},
): Promise<SpeciesLocation[]> {
  const params = new URLSearchParams()
  if (filters.category) params.set('category', filters.category)
  if (filters.trend) params.set('trend', filters.trend)
  const qs = params.toString()
  const res = await getJSON<{ count: number; locations: SpeciesLocation[] }>(
    `/api/locations${qs ? `?${qs}` : ''}`,
  )
  return res.locations
}
