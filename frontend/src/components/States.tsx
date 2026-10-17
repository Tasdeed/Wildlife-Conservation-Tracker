import { useEffect, useState } from 'react'

// Both free tiers sleep: Render's web service after 15 minutes idle, Neon's
// compute after 5. A first request following a quiet period therefore waits on
// two cold starts and can take most of a minute. Under a few seconds that is
// just a spinner; past that, saying so is the difference between "waking up"
// and "broken".
const SLOW_AFTER_MS = 4000

export function Spinner({ label = 'Loading…' }: { label?: string }) {
  const [slow, setSlow] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setSlow(true), SLOW_AFTER_MS)
    return () => clearTimeout(timer)
  }, [])

  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-slate-500">
      <div className="flex items-center gap-3">
        <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-emerald-600" />
        <span className="text-sm">{label}</span>
      </div>
      {slow && (
        <p className="max-w-xs text-center text-xs leading-relaxed text-slate-400 dark:text-slate-500">
          Waking the server — it sleeps when idle on a free tier, so this can
          take up to a minute. Only the first visit after a quiet period waits.
        </p>
      )}
    </div>
  )
}

export function ErrorState({ error }: { error: unknown }) {
  const message = error instanceof Error ? error.message : String(error)
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
      <p className="font-medium">Couldn’t load data</p>
      <p className="mt-1 opacity-90">{message}</p>
      {import.meta.env.DEV ? (
        <p className="mt-2 text-xs opacity-70">
          Is the backend running at{' '}
          <code>{import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:5001'}</code>?
        </p>
      ) : (
        <p className="mt-2 text-xs opacity-70">
          The API sleeps when idle on a free tier and can take a minute to wake.
          Refreshing usually fixes it.
        </p>
      )}
    </div>
  )
}
