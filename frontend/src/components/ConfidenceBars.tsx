import { trendColor } from '../lib/constants'
import { useIsDark } from '../lib/useIsDark'

interface ConfidenceBarsProps {
  scores: Record<string, number>
  predicted: string
}

// Horizontal probability bars, one per class, highest first. The predicted class
// is marked with a ring + label so it doesn't rely on bar length alone.
export default function ConfidenceBars({ scores, predicted }: ConfidenceBarsProps) {
  const isDark = useIsDark()
  const entries = Object.entries(scores).sort((a, b) => b[1] - a[1])

  return (
    <ul className="flex flex-col gap-3">
      {entries.map(([cls, prob]) => {
        const pct = Math.round(prob * 100)
        const isPredicted = cls === predicted
        return (
          <li key={cls} className="grid grid-cols-[9rem_1fr_auto] items-center gap-3">
            <span className="flex items-center gap-1.5 whitespace-nowrap text-sm text-slate-700 dark:text-slate-300">
              {cls}
              {isPredicted && (
                <span className="rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300">
                  pred
                </span>
              )}
            </span>
            <span className="relative h-3 rounded-full bg-slate-100 dark:bg-slate-800">
              <span
                className="absolute inset-y-0 left-0 rounded-full transition-[width] duration-500 ease-out"
                style={{
                  width: `${pct}%`,
                  backgroundColor: trendColor(cls, isDark),
                  minWidth: pct > 0 ? '0.75rem' : 0,
                  outline: isPredicted ? '2px solid currentColor' : 'none',
                  outlineOffset: '1px',
                }}
              />
            </span>
            <span className="w-12 text-right text-sm font-medium tabular-nums text-slate-900 dark:text-slate-100">
              {pct}%
            </span>
          </li>
        )
      })}
    </ul>
  )
}
