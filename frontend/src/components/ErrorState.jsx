export default function ErrorState({ error, onRetry }) {
  const message = error?.message || 'An unexpected error occurred.'
  const isRateLimited = error?.status === 429
  const isUnreachable = error?.status === 502 || error?.status === 0

  return (
    <div className="error-state" role="alert">
      <div className="error-icon" aria-hidden="true">
        ⚠️
      </div>
      <p className="error-message">{message}</p>
      {isRateLimited && (
        <p className="error-hint">
          Too many requests in a short time, wait a moment and try again.
        </p>
      )}
      {isUnreachable && (
        <p className="error-hint">
          The data source (PokeAPI) may be down. Try again soon.
        </p>
      )}
      {onRetry && (
        <button type="button" className="load-more" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  )
}
