export interface BarDatum {
  key: string
  label: string
  value: number
  color: string
}

interface BarChartProps {
  data: BarDatum[]
  /** Optional unit label appended to the accessible/hover description. */
  valueSuffix?: string
}

// Horizontal bar chart built in plain HTML: thin marks, rounded data-ends,
// direct value labels (so identity never rests on color alone), recessive track.
export default function BarChart({ data, valueSuffix }: BarChartProps) {
  const max = Math.max(1, ...data.map((d) => d.value))

  return (
    <ul className="flex flex-col gap-3">
      {data.map((d) => {
        const pct = (d.value / max) * 100
        const suffix = valueSuffix ? ` ${valueSuffix}` : ''
        return (
          <li key={d.key} className="group grid grid-cols-[7rem_1fr_auto] items-center gap-3">
            <span className="truncate text-sm text-slate-600 dark:text-slate-300" title={d.label}>
              {d.label}
            </span>
            <span
              className="relative h-3 rounded-full bg-slate-100 dark:bg-slate-800"
              role="img"
              aria-label={`${d.label}: ${d.value}${suffix}`}
              title={`${d.label}: ${d.value}${suffix}`}
            >
              <span
                className="absolute inset-y-0 left-0 rounded-full transition-[width] duration-500 ease-out group-hover:brightness-110"
                style={{ width: `${pct}%`, backgroundColor: d.color, minWidth: d.value > 0 ? '0.75rem' : 0 }}
              />
            </span>
            <span className="w-10 text-right text-sm font-medium tabular-nums text-slate-900 dark:text-slate-100">
              {d.value}
            </span>
          </li>
        )
      })}
    </ul>
  )
}
