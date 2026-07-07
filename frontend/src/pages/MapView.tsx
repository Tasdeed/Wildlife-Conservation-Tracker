import { useSearchParams } from 'react-router-dom'
import useSWR from 'swr'
import { getLocations } from '../lib/api'
import { ErrorState, Spinner } from '../components/States'
import SpeciesMap from '../components/SpeciesMap'
import {
  CATEGORY_META,
  CATEGORY_ORDER,
  categoryColor,
  categoryLabel,
} from '../lib/constants'
import { useIsDark } from '../lib/useIsDark'

export default function MapView() {
  const isDark = useIsDark()
  const [searchParams, setSearchParams] = useSearchParams()
  const category = searchParams.get('category') ?? ''

  const { data, error, isLoading } = useSWR(['locations', category], () =>
    getLocations({ category: category || undefined }),
  )

  function setCategory(next: string) {
    const params = new URLSearchParams()
    if (next) params.set('category', next)
    setSearchParams(params)
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
            Range map
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Country-level ranges from IUCN assessments, plotted at country centroids
            (approximate — marker size reflects species count).
          </p>
        </div>

        {/* Category filter */}
        <div className="flex gap-1">
          {['', ...CATEGORY_ORDER].map((c) => (
            <button
              key={c || 'all'}
              type="button"
              onClick={() => setCategory(c)}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                category === c
                  ? 'bg-emerald-600 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700'
              }`}
            >
              {c || 'All'}
            </button>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 text-xs text-slate-600 dark:text-slate-300">
        {CATEGORY_ORDER.map((c) => (
          <span key={c} className="inline-flex items-center gap-1.5">
            <span
              className="h-3 w-3 rounded-full"
              style={{ backgroundColor: categoryColor(c, isDark), opacity: 0.7 }}
              aria-hidden
            />
            {c} · {categoryLabel(c)}
          </span>
        ))}
        <span className="text-slate-400">Marker color = most-severe category at that point.</span>
      </div>

      {isLoading && <Spinner label="Loading ranges…" />}
      {error && <ErrorState error={error} />}
      {data && data.length === 0 && (
        <p className="rounded-lg border border-slate-200 bg-white p-6 text-center text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
          No location data yet. Run <code>populate_locations.py</code> on the backend.
        </p>
      )}
      {data && data.length > 0 && (
        <>
          <SpeciesMap locations={data} />
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {data.length} location markers · {CATEGORY_META[category]?.label ?? 'all categories'}
          </p>
        </>
      )}
    </div>
  )
}
