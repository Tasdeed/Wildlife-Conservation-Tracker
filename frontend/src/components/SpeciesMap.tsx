import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import { Link } from 'react-router-dom'
import type { SpeciesLocation } from '../lib/types'
import { categoryColor } from '../lib/constants'
import { useIsDark } from '../lib/useIsDark'

interface Group {
  lat: number
  lng: number
  country: string | null
  items: SpeciesLocation[]
}

// Most-severe category wins the marker color when several species share a point.
const SEVERITY: Record<string, number> = { CR: 5, EN: 4, VU: 3, NT: 2, LC: 1 }

function dominantCategory(items: SpeciesLocation[]): string | null {
  return items.reduce<string | null>((best, it) => {
    const b = best ? SEVERITY[best] ?? 0 : 0
    const c = it.category ? SEVERITY[it.category] ?? 0 : 0
    return c > b ? it.category : best
  }, null)
}

function groupByPoint(locations: SpeciesLocation[]): Group[] {
  const map = new Map<string, Group>()
  for (const loc of locations) {
    const key = `${loc.lat},${loc.lng}`
    const existing = map.get(key)
    if (existing) existing.items.push(loc)
    else map.set(key, { lat: loc.lat, lng: loc.lng, country: loc.country, items: [loc] })
  }
  return [...map.values()]
}

export default function SpeciesMap({ locations }: { locations: SpeciesLocation[] }) {
  const isDark = useIsDark()
  const groups = groupByPoint(locations)

  const tileUrl = isDark
    ? 'https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png'
    : 'https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png'

  return (
    <MapContainer
      center={[15, 10]}
      zoom={2}
      minZoom={2}
      worldCopyJump
      className="h-[70vh] w-full rounded-xl"
      style={{ background: isDark ? '#1a1a19' : '#eaeaea' }}
    >
      <TileLayer
        url={tileUrl}
        attribution='&copy; OpenStreetMap &copy; CARTO'
      />
      {groups.map((g) => {
        const color = categoryColor(dominantCategory(g.items), isDark)
        const radius = Math.min(6 + g.items.length * 1.5, 20)
        return (
          <CircleMarker
            key={`${g.lat},${g.lng}`}
            center={[g.lat, g.lng]}
            radius={radius}
            pathOptions={{
              color,
              fillColor: color,
              fillOpacity: 0.55,
              weight: 1.5,
            }}
          >
            <Popup>
              <div className="max-h-56 overflow-y-auto">
                <p className="mb-1 font-semibold">
                  {g.country ?? 'Unknown'} · {g.items.length}{' '}
                  {g.items.length === 1 ? 'species' : 'species'}
                </p>
                <ul className="space-y-1">
                  {g.items.map((it) => (
                    <li key={it.species_id}>
                      <Link
                        to={`/species/${it.species_id}`}
                        className="text-emerald-700 hover:underline"
                      >
                        {it.scientific_name}
                      </Link>{' '}
                      <span className="text-slate-400">({it.category ?? '—'})</span>
                    </li>
                  ))}
                </ul>
              </div>
            </Popup>
          </CircleMarker>
        )
      })}
    </MapContainer>
  )
}
