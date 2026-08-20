import { Link, useParams } from 'react-router-dom'
import { useMoveDetail } from '../hooks/usePokemon'
import { formatPokemonName, typeIconUrl, typeColors } from '../utils/typeColors'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'

const CLASS_LABELS = {
  physical: 'Physical',
  special: 'Special',
  status: 'Status',
}

const CLASS_COLORS = {
  physical: '#e03131',
  special: '#9c36b5',
  status: '#868e96',
}

export default function MoveDetailPage() {
  const { id } = useParams()
  const query = useMoveDetail(id)
  const colors = typeColors()

  if (query.isLoading) return <LoadingState label="Loading move..." />
  if (query.isError) return <ErrorState error={query.error} onRetry={query.refetch} />

  const move = query.data
  if (!move) return null

  const color = colors[move.type] || '#888'
  const classLabel = CLASS_LABELS[move.damage_class] || move.damage_class
  const classColor = CLASS_COLORS[move.damage_class] || '#888'

  return (
    <main className="app-main">
      <Link to="/tms" className="back-link">
        <svg
          className="back-arrow"
          viewBox="0 0 24 24"
          width="16"
          height="16"
          aria-hidden="true"
          focusable="false"
        >
          <path
            d="M19 12H5M12 19l-7-7 7-7"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        Back to TMs
      </Link>

      <article className="detail-page">
        <header className="detail-header" style={{ background: `linear-gradient(135deg, ${color}, ${color}dd)` }}>
          <div className="detail-id">Move #{String(move.id).padStart(3, '0')}</div>
          <h2 className="detail-name">{formatPokemonName(move.name)}</h2>
          <div className="detail-types-row">
            <span className="type-badge" style={{ backgroundColor: color }}>
              <img className="type-icon" src={typeIconUrl(move.type)} alt={move.type} />
            </span>
          </div>
        </header>

        <section className="detail-section">
          <h3>Details</h3>
          <div className="info-grid">
            <div className="info-item">
              <div className="info-body">
                <span className="info-label">Type</span>
                <span className="info-value">{formatPokemonName(move.type)}</span>
              </div>
            </div>
            <div className="info-item">
              <div className="info-body">
                <span className="info-label">Class</span>
                <span className="info-value" style={{ color: classColor }}>{classLabel}</span>
              </div>
            </div>
            <div className="info-item">
              <div className="info-body">
                <span className="info-label">Power</span>
                <span className="info-value">{move.power ?? ', '}</span>
              </div>
            </div>
            <div className="info-item">
              <div className="info-body">
                <span className="info-label">Accuracy</span>
                <span className="info-value">{move.accuracy != null ? `${move.accuracy}%` : ', '}</span>
              </div>
            </div>
            <div className="info-item">
              <div className="info-body">
                <span className="info-label">PP</span>
                <span className="info-value">{move.pp ?? ', '}</span>
              </div>
            </div>
            <div className="info-item">
              <div className="info-body">
                <span className="info-label">Priority</span>
                <span className="info-value">{move.priority || 0}</span>
              </div>
            </div>
          </div>
        </section>

        {move.flavor_text && (
          <section className="detail-section">
            <h3>Description</h3>
            <p className="flavor-text">{move.flavor_text}</p>
          </section>
        )}

        {move.effect && (
          <section className="detail-section">
            <h3>Effect</h3>
            <p className="flavor-text">{move.effect}</p>
          </section>
        )}

        {move.short_effect && (
          <section className="detail-section">
            <h3>Short Effect</h3>
            <p className="flavor-text">{move.short_effect}</p>
          </section>
        )}
      </article>
    </main>
  )
}
