import { Link, useParams } from 'react-router-dom'
import useSWR from 'swr'
import { getPrediction, getSpeciesById } from '../lib/api'
import { ErrorState, Spinner } from '../components/States'
import { CategoryBadge, TrendBadge } from '../components/Badges'
import ConfidenceBars from '../components/ConfidenceBars'
import { categoryLabel } from '../lib/constants'

const TAXONOMY_FIELDS = [
  ['Kingdom', 'kingdom'],
  ['Phylum', 'phylum'],
  ['Class', 'class'],
  ['Order', 'order'],
  ['Family', 'family'],
] as const

export default function SpeciesDetail() {
  const { id } = useParams<{ id: string }>()
  const {
    data: species,
    error: speciesError,
    isLoading: speciesLoading,
  } = useSWR(id ? ['species', id] : null, () => getSpeciesById(id!))

  // Prediction may legitimately fail (model not loaded); handle separately.
  const { data: prediction, error: predictionError } = useSWR(
    id ? ['prediction', id] : null,
    () => getPrediction(id!),
    { shouldRetryOnError: false },
  )

  if (speciesLoading) return <Spinner label="Loading species…" />
  if (speciesError) return <ErrorState error={speciesError} />
  if (!species) return null

  const trendsAgree =
    prediction &&
    species.population_trend &&
    prediction.predicted_trend === species.population_trend

  return (
    <div className="flex flex-col gap-6">
      <Link
        to="/species"
        className="text-sm text-emerald-700 hover:underline dark:text-emerald-400"
      >
        ← Back to species
      </Link>

      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
            {species.common_name || species.scientific_name}
          </h1>
          <p className="mt-0.5 text-lg italic text-slate-500 dark:text-slate-400">
            {species.scientific_name}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <CategoryBadge code={species.category} />
          <TrendBadge trend={species.population_trend} />
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Taxonomy + status */}
        <section className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="mb-4 text-sm font-semibold text-slate-700 dark:text-slate-200">
            Taxonomy & status
          </h2>
          <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
            {TAXONOMY_FIELDS.map(([label, key]) => (
              <div key={key}>
                <dt className="text-slate-500 dark:text-slate-400">{label}</dt>
                <dd className="font-medium text-slate-900 dark:text-slate-100">
                  {(species[key] as string | null) || '—'}
                </dd>
              </div>
            ))}
            <div>
              <dt className="text-slate-500 dark:text-slate-400">Category</dt>
              <dd className="font-medium text-slate-900 dark:text-slate-100">
                {categoryLabel(species.category)}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500 dark:text-slate-400">Recorded trend</dt>
              <dd className="font-medium text-slate-900 dark:text-slate-100">
                {species.population_trend || 'Unknown'}
              </dd>
            </div>
          </dl>
        </section>

        {/* ML prediction */}
        <section className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="mb-4 text-sm font-semibold text-slate-700 dark:text-slate-200">
            Model prediction
          </h2>

          {predictionError && (
            <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-300">
              Prediction unavailable:{' '}
              {predictionError instanceof Error ? predictionError.message : 'unknown error'}
            </p>
          )}

          {!prediction && !predictionError && <Spinner label="Predicting…" />}

          {prediction && (
            <div className="flex flex-col gap-4">
              <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
                <div>
                  <span className="text-slate-500 dark:text-slate-400">Predicted: </span>
                  <TrendBadge trend={prediction.predicted_trend} />
                </div>
                <div>
                  <span className="text-slate-500 dark:text-slate-400">Recorded: </span>
                  <TrendBadge trend={prediction.actual_trend} />
                </div>
                {species.population_trend && (
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      trendsAgree
                        ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300'
                        : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'
                    }`}
                  >
                    {trendsAgree ? 'matches record' : 'differs from record'}
                  </span>
                )}
              </div>

              <div>
                <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
                  Class confidence
                </p>
                <ConfidenceBars
                  scores={prediction.confidence_scores}
                  predicted={prediction.predicted_trend}
                />
              </div>

              <p className="text-xs text-slate-400 dark:text-slate-500">
                Predicted from taxonomy and conservation category — a weak signal for population
                direction, so treat confidence loosely.
              </p>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
