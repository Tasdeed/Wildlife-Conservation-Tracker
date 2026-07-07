import { Link } from 'react-router-dom'
import type { Species } from '../lib/types'
import { CategoryBadge, TrendBadge } from './Badges'

export default function SpeciesCard({ species }: { species: Species }) {
  return (
    <Link
      to={`/species/${species.id}`}
      className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 transition-shadow hover:shadow-md dark:border-slate-800 dark:bg-slate-900"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate font-medium text-slate-900 dark:text-slate-100">
            {species.common_name || species.scientific_name}
          </p>
          <p className="truncate text-sm italic text-slate-500 dark:text-slate-400">
            {species.scientific_name}
          </p>
        </div>
        <CategoryBadge code={species.category} />
      </div>
      <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
        <span className="truncate">{species.class || species.phylum || species.kingdom || '—'}</span>
        <TrendBadge trend={species.population_trend} />
      </div>
    </Link>
  )
}
