import { Link } from 'react-router-dom'
import { useTms } from '../hooks/usePokemon'
import { formatPokemonName, typeIconUrl, typeColors } from '../utils/typeColors'
import LoadingState from '../components/LoadingState'
import ErrorState from '../components/ErrorState'

export default function TmsPage() {
  const query = useTms()
  const colors = typeColors()

  if (query.isLoading) return <LoadingState label="Loading TMs..." />
  if (query.isError) return <ErrorState error={query.error} onRetry={query.refetch} />

  const tms = query.data?.results ?? []

  return (
    <main className="app-main">
      <div className="page-content">
        <h2 className="page-title">TMs (latest game)</h2>
        <p className="page-subtitle">
          Technical Machines of the most recent game, click one to see what the move does.
        </p>
        <div className="tm-grid">
          {tms.map((tm) => {
            const color = colors[tm.type] || '#888'
            return (
              <Link key={tm.number} to={`/move/${tm.move_id}`} className="tm-card" title={tm.move}>
                <span className="tm-number">{tm.number.toUpperCase()}</span>
                <img className="tm-icon" src={typeIconUrl(tm.type)} alt={tm.type} style={{ background: color }} />
                <span className="tm-move">{formatPokemonName(tm.move)}</span>
              </Link>
            )
          })}
        </div>
      </div>
    </main>
  )
}
