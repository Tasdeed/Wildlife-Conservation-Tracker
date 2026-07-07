import { categoryColor, categoryLabel, trendColor } from '../lib/constants'
import { useIsDark } from '../lib/useIsDark'

export function CategoryBadge({ code }: { code: string | null }) {
  const isDark = useIsDark()
  const color = categoryColor(code, isDark)
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold"
      style={{ color, borderColor: color }}
      title={categoryLabel(code)}
    >
      <span className="h-2 w-2 rounded-full" style={{ backgroundColor: color }} aria-hidden />
      {code ?? 'N/A'}
    </span>
  )
}

export function TrendBadge({ trend }: { trend: string | null }) {
  const isDark = useIsDark()
  const color = trendColor(trend, isDark)
  return (
    <span
      className="inline-flex items-center gap-1.5 text-xs font-medium"
      style={{ color }}
    >
      <span className="h-2 w-2 rounded-full" style={{ backgroundColor: color }} aria-hidden />
      {trend ?? 'Unknown'}
    </span>
  )
}
