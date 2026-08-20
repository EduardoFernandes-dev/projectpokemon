import { useInfiniteQuery, useQuery } from '@tanstack/react-query'
import {
  getGenerations,
  getMoveDetail,
  getPokemonDetail,
  getPokemonList,
  getTms,
  getTypes,
  searchPokemon,
} from '../services/api'

const PAGE_SIZE = 60

// Dados estáticos → staleTime generoso (ProjectPokemon-Desempenho §3.1).
const STATIC_STALE_TIME = 24 * 60 * 60 * 1000

// Versão do formato do payload de detalhe (moves com type/damage_class/power).
// Incrementar quando o backend mudar o payload, invalida a cache antiga.
const PAYLOAD_VERSION = 2

// Normaliza o filtro de tipos para a queryKey: array ordenado (ordem irrelevante).
const SORTED_TYPES = (filters) => {
  const types = Array.isArray(filters.type)
    ? filters.type
    : filters.type
      ? [filters.type]
      : []
  return [...types].sort()
}

export function usePokemonSearch(query, filters = {}) {
  const q = query.trim()
  return useQuery({
    queryKey: ['pokemon-search', q, SORTED_TYPES(filters), filters.generation],
    queryFn: () => searchPokemon(q, filters),
    enabled: q.length > 0,
    staleTime: 60_000,
  })
}

export function usePokemonList(filters = {}) {
  return useInfiniteQuery({
    queryKey: ['pokemon-list', SORTED_TYPES(filters), filters.generation],
    queryFn: ({ pageParam }) => getPokemonList(PAGE_SIZE, pageParam, filters),
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) =>
      allPages.length * PAGE_SIZE < lastPage.count
        ? allPages.length * PAGE_SIZE
        : undefined,
    staleTime: STATIC_STALE_TIME,
  })
}

export function usePokemonDetail(identifier) {
  return useQuery({
    // Versão do payload: incrementar quando o backend muda o formato dos
    // dados de detalhe, força um refetch (a cache antiga de 24h ficava
    // com moves sem type/damage_class/power).
    queryKey: ['pokemon-detail', identifier, PAYLOAD_VERSION],
    queryFn: () => getPokemonDetail(identifier),
    staleTime: STATIC_STALE_TIME,
    retry: (count, error) => (error?.status === 404 ? false : count < 2),
  })
}

export function useTypes() {
  return useQuery({ queryKey: ['types'], queryFn: getTypes, staleTime: Infinity })
}

export function useGenerations() {
  return useQuery({ queryKey: ['generations'], queryFn: getGenerations, staleTime: Infinity })
}

export function useTms() {
  return useQuery({ queryKey: ['tms'], queryFn: getTms, staleTime: STATIC_STALE_TIME })
}

export function useMoveDetail(identifier) {
  return useQuery({
    queryKey: ['move-detail', identifier],
    queryFn: () => getMoveDetail(identifier),
    staleTime: STATIC_STALE_TIME,
    retry: (count, error) => (error?.status === 404 ? false : count < 2),
  })
}
