export function Spinner({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-slate-500">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-emerald-600" />
      <span className="text-sm">{label}</span>
    </div>
  )
}

export function ErrorState({ error }: { error: unknown }) {
  const message = error instanceof Error ? error.message : String(error)
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
      <p className="font-medium">Couldn’t load data</p>
      <p className="mt-1 opacity-90">{message}</p>
      <p className="mt-2 text-xs opacity-70">
        Is the backend running at{' '}
        <code>{import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:5001'}</code>?
      </p>
    </div>
  )
}
