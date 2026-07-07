interface StatCardProps {
  label: string
  value: number | string
  sublabel?: string
  accent?: string
}

export default function StatCard({ label, value, sublabel, accent }: StatCardProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center gap-2">
        {accent && (
          <span
            className="h-2.5 w-2.5 rounded-full"
            style={{ backgroundColor: accent }}
            aria-hidden
          />
        )}
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
          {label}
        </p>
      </div>
      <p className="mt-2 text-3xl font-semibold tabular-nums text-slate-900 dark:text-slate-100">
        {value}
      </p>
      {sublabel && (
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{sublabel}</p>
      )}
    </div>
  )
}
