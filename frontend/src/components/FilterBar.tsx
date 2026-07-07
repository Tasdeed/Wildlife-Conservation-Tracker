import { CATEGORY_META, CATEGORY_ORDER, TREND_ORDER } from '../lib/constants'

export interface Filters {
  category: string
  trend: string
  limit: string
}

interface FilterBarProps {
  filters: Filters
  onChange: (next: Partial<Filters>) => void
  onReset: () => void
}

const selectClass =
  'rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-900 shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100'

export default function FilterBar({ filters, onChange, onReset }: FilterBarProps) {
  const hasFilters = filters.category || filters.trend

  return (
    <div className="flex flex-wrap items-end gap-3">
      <label className="flex flex-col gap-1 text-xs font-medium text-slate-500 dark:text-slate-400">
        Category
        <select
          className={selectClass}
          value={filters.category}
          onChange={(e) => onChange({ category: e.target.value })}
        >
          <option value="">All</option>
          {CATEGORY_ORDER.map((c) => (
            <option key={c} value={c}>
              {c} — {CATEGORY_META[c].label}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1 text-xs font-medium text-slate-500 dark:text-slate-400">
        Population trend
        <select
          className={selectClass}
          value={filters.trend}
          onChange={(e) => onChange({ trend: e.target.value })}
        >
          <option value="">All</option>
          {TREND_ORDER.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1 text-xs font-medium text-slate-500 dark:text-slate-400">
        Limit
        <select
          className={selectClass}
          value={filters.limit}
          onChange={(e) => onChange({ limit: e.target.value })}
        >
          {['24', '48', '96', ''].map((l) => (
            <option key={l || 'all'} value={l}>
              {l || 'All'}
            </option>
          ))}
        </select>
      </label>

      {hasFilters && (
        <button
          type="button"
          onClick={onReset}
          className="rounded-md px-3 py-1.5 text-sm font-medium text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
        >
          Clear
        </button>
      )}
    </div>
  )
}
