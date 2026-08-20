import { useEffect, useMemo, useState } from 'react'
import { useWindowVirtualizer } from '@tanstack/react-virtual'
import ErrorState from './ErrorState'
import LoadingState from './LoadingState'
import PokemonCard from './PokemonCard'

// Altura estimada de cada linha: card real (238px, medido) + espaçamento vertical (32px).
// Medido no browser: card=238px; ROW_HEIGHT tem de igualar card+padding ou as linhas sobrepõem-se.
const ROW_HEIGHT = 270
const CARD_MIN_WIDTH = 170

function chunk(items, size) {
  const rows = []
  for (let i = 0; i < items.length; i += size) rows.push(items.slice(i, i + size))
  return rows
}

function useColumns() {
  const [cols, setCols] = useState(() =>
    Math.max(2, Math.floor(window.innerWidth / CARD_MIN_WIDTH)),
  )
  useEffect(() => {
    const onResize = () =>
      setCols(Math.max(2, Math.floor(window.innerWidth / CARD_MIN_WIDTH)))
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])
  return cols
}

/**
 * Grelha virtualizada com scroll infinito (ProjectPokemon-Desempenho §3.3).
 * Recebe o objeto devolvido por usePokemonList (useInfiniteQuery).
 */
export default function PokemonGrid({ query }) {
  const cols = useColumns()

  const items = useMemo(
    () => (query.data?.pages ?? []).flatMap((page) => page.results ?? []),
    [query.data],
  )
  const rows = useMemo(() => chunk(items, cols), [items, cols])

  const virtualizer = useWindowVirtualizer({
    count: rows.length,
    // Altura estimada da linha = card (~205px) + espaçamento vertical (32px) + folga.
    // (measureElement foi removido: partia a renderização da grelha no Firefox/Zen.)
    estimateSize: () => ROW_HEIGHT,
    overscan: 5,
  })

  // Scroll infinito: carregar mais quando nos aproximamos do fim.
  const lastVisibleIndex = virtualizer.range?.endIndex ?? 0
  useEffect(() => {
    if (
      lastVisibleIndex >= rows.length - 3 &&
      query.hasNextPage &&
      !query.isFetchingNextPage
    ) {
      query.fetchNextPage()
    }
  }, [lastVisibleIndex, rows.length, query])

  if (query.isLoading) return <LoadingState label="Loading Pokédex..." />
  if (query.isError) return <ErrorState error={query.error} onRetry={() => query.refetch()} />
  if (items.length === 0)
    return <div className="no-results">No Pokémon match these filters.</div>

  return (
    <div className="virtual-grid" style={{ height: virtualizer.getTotalSize() }}>
      {virtualizer.getVirtualItems().map((row) => (
        <div
          key={row.key}
          className="pokemon-grid-row"
          style={{
            transform: `translateY(${row.start}px)`,
            gridTemplateColumns: `repeat(${cols}, 1fr)`,
          }}
        >
          {rows[row.index].map((pokemon) => (
            <PokemonCard key={pokemon.id} pokemon={pokemon} />
          ))}
        </div>
      ))}
      {query.isFetchingNextPage && (
        <div className="loading-state small">Loading more...</div>
      )}
    </div>
  )
}
