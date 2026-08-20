import { useState } from 'react'
import { Link } from 'react-router-dom'
import { formatPokemonName, typeColors, typeIconUrl } from '../utils/typeColors'

/**
 * Card da grelha, baseado no resumo do índice (id, name, types, sprite),
 * sem fetch de detalhe por card (matava a performance da grelha de 1025).
 */
export default function PokemonCard({ pokemon }) {
  const [imgError, setImgError] = useState(false)
  const colors = typeColors()
  const types = pokemon.types ?? []

  return (
    <Link
      to={`/pokemon/${pokemon.id}`}
      className={`pokemon-card ${types[0] ? `type-${types[0]}` : ''}`}
    >
      <div className="pokemon-card-id">#{String(pokemon.id).padStart(3, '0')}</div>
      <div className="pokemon-card-sprite">
        {!imgError ? (
          <img
            src={pokemon.sprite}
            alt={pokemon.name}
            loading="lazy"
            decoding="async"
            width={96}
            height={96}
            onError={() => setImgError(true)}
          />
        ) : (
          <div className="pokemon-card-placeholder">?</div>
        )}
      </div>
      <h3 className="pokemon-card-name">{formatPokemonName(pokemon.name)}</h3>
      {types.length > 0 && (
        <div className="pokemon-card-types">
          {types.map((t) => (
            <span
              key={t}
              className="type-badge"
              style={{ backgroundColor: colors[t] || '#888' }}
            >
              <img
                src={typeIconUrl(t)}
                alt={t}
                title={t}
                loading="lazy"
                className="type-icon"
              />
            </span>
          ))}
        </div>
      )}
    </Link>
  )
}
