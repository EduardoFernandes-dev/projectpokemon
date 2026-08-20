import { useState } from 'react'
import ErrorState from '../components/ErrorState'
import FilterPanel, { GEN_LABELS } from '../components/FilterPanel'
import LoadingState from '../components/LoadingState'
import PokemonCard from '../components/PokemonCard'
import PokemonGrid from '../components/PokemonGrid'
import SearchBar from '../components/SearchBar'
import { usePokemonList, usePokemonSearch } from '../hooks/usePokemon'
import { typeColors, typeIconUrl } from '../utils/typeColors'

export default function HomePage() {
  const [query, setQuery] = useState('')
  const [filters, setFilters] = useState({ type: [], generation: '' })
  const colors = typeColors()

  const search = usePokemonSearch(query, filters)
  const list = usePokemonList(filters)

  const hasQuery = query.trim().length > 0
  const hasFilters = (filters.type?.length ?? 0) > 0 || filters.generation !== ''

  return (
    <main className="app-main">
      <SearchBar value={query} onChange={setQuery} loading={search.isFetching} />

      <FilterPanel filters={filters} onChange={setFilters} />

      {hasFilters && (
        <div className="active-filters">
          <span className="active-filters-label">Active filters</span>
          {(filters.type ?? []).map((t) => (
            <button
              key={t}
              type="button"
              className="filter-tag type"
              style={{ backgroundColor: colors[t] || '#888' }}
              onClick={() =>
                setFilters({ ...filters, type: filters.type.filter((x) => x !== t) })
              }
              title="Remove type filter"
            >
              <img src={typeIconUrl(t)} alt="" className="type-icon" />
              <span>{t}</span>
              <span className="filter-tag-x">✕</span>
            </button>
          ))}
          {filters.generation && (
            <button
              type="button"
              className="filter-tag gen"
              onClick={() => setFilters({ ...filters, generation: '' })}
              title="Remove generation filter"
            >
              <span>{GEN_LABELS[filters.generation] || filters.generation}</span>
              <span className="filter-tag-x">✕</span>
            </button>
          )}
        </div>
      )}

      {hasQuery ? (
        <section aria-label="Search results">
          <h2 className="section-title">Results for &quot;{query.trim()}&quot;</h2>
          {search.isLoading ? (
            <LoadingState />
          ) : search.isError ? (
            <ErrorState error={search.error} onRetry={() => search.refetch()} />
          ) : search.data?.results?.length ? (
            <div className="pokemon-grid static-grid">
              {search.data.results.map((pokemon) => (
                <PokemonCard key={pokemon.id} pokemon={pokemon} />
              ))}
            </div>
          ) : (
            <div className="no-results">
              No Pokémon found for &quot;{query.trim()}&quot;
            </div>
          )}
        </section>
      ) : (
        <PokemonGrid query={list} />
      )}
    </main>
  )
}
