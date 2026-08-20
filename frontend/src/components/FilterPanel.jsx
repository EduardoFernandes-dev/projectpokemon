import { useGenerations, useTypes } from '../hooks/usePokemon'
import { typeColors, typeIconUrl } from '../utils/typeColors'

export const GEN_LABELS = {
  'generation-i': 'Gen 1',
  'generation-ii': 'Gen 2',
  'generation-iii': 'Gen 3',
  'generation-iv': 'Gen 4',
  'generation-v': 'Gen 5',
  'generation-vi': 'Gen 6',
  'generation-vii': 'Gen 7',
  'generation-viii': 'Gen 8',
  'generation-ix': 'Gen 9',
}

export default function FilterPanel({ filters, onChange }) {
  const typesQuery = useTypes()
  const generationsQuery = useGenerations()

  const types = (typesQuery.data?.results ?? []).filter(
    (t) =>
      t.name !== 'unknown' &&
      t.name !== 'shadow' &&
      t.name !== 'stellar', // tipo de Terastal, nenhum Pokémon o tem como tipo base
  )
  const generations = generationsQuery.data?.results ?? []
  const colors = typeColors()

  const selectedTypes = filters.type ?? []

  const handleChange = (patch) => onChange({ ...filters, ...patch })

  const toggleType = (name) => {
    if (selectedTypes.includes(name)) {
      // remover, a ordem não importa para o filtro
      handleChange({ type: selectedTypes.filter((t) => t !== name) })
    } else if (selectedTypes.length < 2) {
      handleChange({ type: [...selectedTypes, name] })
    } else {
      // já há 2 selecionados → substituir o primeiro (comportamento dos jogos)
      handleChange({ type: [selectedTypes[1], name] })
    }
  }

  return (
    <div className="filter-panel">
      <div className="filter-group" role="group" aria-label="Filter by type">
        <span className="filter-group-label">Type</span>
        <div className="filter-chips">
          <button
            type="button"
            className={`filter-chip ${selectedTypes.length === 0 ? 'active' : ''}`}
            onClick={() => handleChange({ type: [] })}
            aria-pressed={selectedTypes.length === 0}
          >
            All
          </button>
          {types.map((t) => (
            <button
              key={t.name}
              type="button"
              className={`filter-chip type ${selectedTypes.includes(t.name) ? 'active' : ''}`}
              style={{ backgroundColor: colors[t.name] || '#888' }}
              onClick={() => toggleType(t.name)}
              aria-pressed={selectedTypes.includes(t.name)}
              title={t.name}
            >
              <img src={typeIconUrl(t.name)} alt={t.name} className="type-icon" />
            </button>
          ))}
        </div>
      </div>

      <div className="filter-group" role="group" aria-label="Filter by generation">
        <span className="filter-group-label">Generation</span>
        <div className="filter-chips">
          <button
            type="button"
            className={`filter-chip ${!filters.generation ? 'active' : ''}`}
            onClick={() => handleChange({ generation: '' })}
            aria-pressed={!filters.generation}
          >
            All
          </button>
          {generations.map((g) => (
            <button
              key={g.name}
              type="button"
              className={`filter-chip ${filters.generation === g.name ? 'active' : ''}`}
              onClick={() => handleChange({ generation: g.name })}
              aria-pressed={filters.generation === g.name}
            >
              {GEN_LABELS[g.name] || g.name.replace('generation-', 'Gen ').toUpperCase()}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
