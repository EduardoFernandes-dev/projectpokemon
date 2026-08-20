export default function LoadingState({ label = 'Loading...' }) {
  return (
    <div className="loading-state" role="status" aria-live="polite">
      <div className="skeleton-grid" aria-hidden="true">
        {Array.from({ length: 12 }).map((_, i) => (
          <div key={i} className="skeleton-card" />
        ))}
      </div>
      <p>{label}</p>
    </div>
  )
}
