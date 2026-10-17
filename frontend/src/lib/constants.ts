// Conservation category display + color. Hues follow the IUCN Red List
// convention (red → orange → gold) but use surface-safe steps that stay legible
// on light and dark chart surfaces. Bars are always text-labeled, so color is
// reinforcing, never the sole channel (red/orange/gold collapse under CVD).
export const CATEGORY_META: Record<
  string,
  { label: string; color: string; colorDark: string }
> = {
  CR: { label: 'Critically Endangered', color: '#dc2626', colorDark: '#f87171' },
  EN: { label: 'Endangered', color: '#ea580c', colorDark: '#fb923c' },
  VU: { label: 'Vulnerable', color: '#ca8a04', colorDark: '#eab308' },
  NT: { label: 'Near Threatened', color: '#65a30d', colorDark: '#a3e635' },
  LC: { label: 'Least Concern', color: '#16a34a', colorDark: '#4ade80' },
}

export const CATEGORY_ORDER = ['CR', 'EN', 'VU', 'NT', 'LC'] as const

// Population trend display + color (semantic status hues).
export const TREND_META: Record<
  string,
  { color: string; colorDark: string }
> = {
  Increasing: { color: '#2e9e5b', colorDark: '#4ade80' },
  Stable: { color: '#2563eb', colorDark: '#60a5fa' },
  Decreasing: { color: '#dc2626', colorDark: '#f87171' },
  Unknown: { color: '#6b7280', colorDark: '#9ca3af' },
}

export const TREND_ORDER = [
  'Increasing',
  'Stable',
  'Decreasing',
  'Unknown',
] as const

export function categoryLabel(code: string | null | undefined): string {
  if (!code) return 'Unknown'
  return CATEGORY_META[code]?.label ?? code
}

export function categoryColor(
  code: string | null | undefined,
  isDark = false,
): string {
  const meta = code ? CATEGORY_META[code] : undefined
  if (!meta) return isDark ? '#9ca3af' : '#6b7280'
  return isDark ? meta.colorDark : meta.color
}

export function trendColor(
  trend: string | null | undefined,
  isDark = false,
): string {
  const meta = trend ? TREND_META[trend] : undefined
  if (!meta) return isDark ? '#9ca3af' : '#6b7280'
  return isDark ? meta.colorDark : meta.color
}
