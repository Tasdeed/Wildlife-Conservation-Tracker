// Mirrors the Flask API response shapes (backend/app.py).

export type Category = 'CR' | 'EN' | 'VU' | string
export type Trend = 'Increasing' | 'Stable' | 'Decreasing' | 'Unknown' | string

// Species.to_dict() — backend/app.py:63
export interface Species {
  id: number
  taxon_id: number | null
  scientific_name: string
  common_name: string | null
  kingdom: string | null
  phylum: string | null
  class: string | null
  order: string | null
  family: string | null
  category: Category | null
  population_trend: Trend | null
}

export interface SpeciesListResponse {
  count: number
  species: Species[]
}

// GET /api/predict/<id> — backend/app.py:206
export interface Prediction {
  species_id: number
  scientific_name: string
  common_name: string | null
  actual_trend: Trend | null
  predicted_trend: Trend
  confidence: number
  confidence_scores: Record<string, number>
  features_used: Record<string, string>
}

// GET /api/model/stats — backend/app.py:238
export interface ModelStats {
  total_species: number
  population_trends: Record<string, number>
  categories: Record<string, number>
  model_info: {
    type: string
    n_estimators: number | null
    features: string[]
    classes: string[]
  }
}

export interface SpeciesFilters {
  category?: string
  trend?: string
  limit?: number
}

// GET /api/locations — added in Phase 4 (backend)
export interface SpeciesLocation {
  species_id: number
  scientific_name: string
  category: Category | null
  trend: Trend | null
  lat: number
  lng: number
  country: string | null
}
