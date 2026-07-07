import { useSearchParams } from 'react-router-dom'
import useSWR from 'swr'
import { getSpecies } from '../lib/api'
import type { SpeciesFilters } from '../lib/types'
import { ErrorState, Spinner } from '../components/States'
import SpeciesCard from '../components/SpeciesCard'
import FilterBar, { type Filters } from '../components/FilterBar'

const DEFAULT_LIMIT = '48'

export default function SpeciesBrowser() {
  const [searchParams, setSearchParams] = useSearchParams()

  const filters: Filters = {
    category: searchParams.get('category') ?? '',
    trend: searchParams.get('trend') ?? '',
    limit: searchParams.get('limit') ?? DEFAULT_LIMIT,
  }

  const apiFilters: SpeciesFilters = {
    category: filters.category || undefined,
    trend: filters.trend || undefined,
    limit: filters.limit ? Number(filters.limit) : undefined,
  }

  const { data, error, isLoading } = useSWR(
    ['species', apiFilters.category, apiFilters.trend, apiFilters.limit],
    () => getSpecies(apiFilters),
  )

  function updateFilters(next: Partial<Filters>) {
    const merged = { ...filters, ...next }
    const params = new URLSearchParams()
    if (merged.category) params.set('category', merged.category)
    if (merged.trend) params.set('trend', merged.trend)
    if (merged.limit && merged.limit !== DEFAULT_LIMIT) params.set('limit', merged.limit)
    setSearchParams(params)
  }

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Species</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Browse and filter tracked species. Select any card for details and a trend prediction.
        </p>
      </div>

      <FilterBar
        filters={filters}
        onChange={updateFilters}
        onReset={() => setSearchParams(new URLSearchParams())}
      />

      {isLoading && <Spinner label="Loading species…" />}
      {error && <ErrorState error={error} />}

      {data && (
        <>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {data.count} {data.count === 1 ? 'species' : 'species'} shown
          </p>
          {data.count === 0 ? (
            <p className="rounded-lg border border-slate-200 bg-white p-6 text-center text-sm text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
              No species match these filters.
            </p>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {data.species.map((s) => (
                <SpeciesCard key={s.id} species={s} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
