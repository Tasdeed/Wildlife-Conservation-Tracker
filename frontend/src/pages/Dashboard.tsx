import useSWR from 'swr'
import { getModelStats } from '../lib/api'
import { ErrorState, Spinner } from '../components/States'
import StatCard from '../components/StatCard'
import BarChart, { type BarDatum } from '../components/BarChart'
import {
  CATEGORY_META,
  CATEGORY_ORDER,
  TREND_ORDER,
  categoryColor,
  categoryLabel,
  trendColor,
} from '../lib/constants'
import { useIsDark } from '../lib/useIsDark'

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
      <h2 className="mb-4 text-sm font-semibold text-slate-700 dark:text-slate-200">{title}</h2>
      {children}
    </section>
  )
}

export default function Dashboard() {
  const isDark = useIsDark()
  const { data, error, isLoading } = useSWR('model-stats', getModelStats)

  if (isLoading) return <Spinner label="Loading conservation stats…" />
  if (error) return <ErrorState error={error} />
  if (!data) return null

  const categoryData: BarDatum[] = CATEGORY_ORDER.filter(
    (c) => c in data.categories,
  ).map((c) => ({
    key: c,
    label: `${c} · ${CATEGORY_META[c].label}`,
    value: data.categories[c] ?? 0,
    color: categoryColor(c, isDark),
  }))

  const trendData: BarDatum[] = TREND_ORDER.filter(
    (t) => t in data.population_trends,
  ).map((t) => ({
    key: t,
    label: t,
    value: data.population_trends[t] ?? 0,
    color: trendColor(t, isDark),
  }))

  const { model_info } = data

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">Overview</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          IUCN Red List species tracked in this database, with model-predicted population trends.
        </p>
      </div>

      {/* Stat tiles */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Total species" value={data.total_species.toLocaleString()} />
        {CATEGORY_ORDER.map((c) => (
          <StatCard
            key={c}
            label={c}
            value={(data.categories[c] ?? 0).toLocaleString()}
            sublabel={categoryLabel(c)}
            accent={categoryColor(c, isDark)}
          />
        ))}
      </div>

      {/* Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Section title="By conservation category">
          <BarChart data={categoryData} valueSuffix="species" />
        </Section>
        <Section title="By population trend">
          <BarChart data={trendData} valueSuffix="species" />
        </Section>
      </div>

      {/* Model info */}
      <Section title="Prediction model">
        <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm sm:grid-cols-3">
          <div>
            <dt className="text-slate-500 dark:text-slate-400">Type</dt>
            <dd className="font-medium text-slate-900 dark:text-slate-100">{model_info.type}</dd>
          </div>
          <div>
            <dt className="text-slate-500 dark:text-slate-400">Trees</dt>
            <dd className="font-medium text-slate-900 dark:text-slate-100">
              {model_info.n_estimators ?? '—'}
            </dd>
          </div>
          <div>
            <dt className="text-slate-500 dark:text-slate-400">Classes</dt>
            <dd className="font-medium text-slate-900 dark:text-slate-100">
              {model_info.classes.join(', ') || '—'}
            </dd>
          </div>
          <div className="col-span-2 sm:col-span-3">
            <dt className="text-slate-500 dark:text-slate-400">Features</dt>
            <dd className="mt-1 flex flex-wrap gap-1.5">
              {model_info.features.map((f) => (
                <span
                  key={f}
                  className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                >
                  {f}
                </span>
              ))}
            </dd>
          </div>
        </dl>
      </Section>
    </div>
  )
}
