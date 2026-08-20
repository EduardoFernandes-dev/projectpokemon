const API_BASE = '/api'

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request(url) {
  let res
  try {
    res = await fetch(url)
  } catch {
    throw new ApiError('No connection to the server. Try again.', 0)
  }

  if (!res.ok) {
    let message = `Erro ${res.status}`
    try {
      const body = await res.json()
      if (body?.error) message = body.error
      else if (body?.detail) message = body.detail
    } catch {
      // corpo não-JSON → mantém a mensagem genérica
    }
    throw new ApiError(message, res.status)
  }
  return res.json()
}

// Normaliza o filtro de tipos: aceita array (novo) ou string (estado antigo).
const TYPES_AS_ARRAY = (filters) =>
  Array.isArray(filters.type) ? filters.type : filters.type ? [filters.type] : []

export function searchPokemon(query, filters = {}) {
  const params = new URLSearchParams({ q: query })
  for (const t of TYPES_AS_ARRAY(filters)) params.append('type', t)
  if (filters.generation) params.set('generation', filters.generation)
  return request(`${API_BASE}/pokemon/search/?${params.toString()}`)
}

export function getPokemonDetail(identifier) {
  return request(`${API_BASE}/pokemon/${identifier}/`)
}

export function getPokemonList(limit = 60, offset = 0, filters = {}) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  for (const t of TYPES_AS_ARRAY(filters)) params.append('type', t)
  if (filters.generation) params.set('generation', filters.generation)
  return request(`${API_BASE}/pokemon/?${params.toString()}`)
}

export function getTypes() {
  return request(`${API_BASE}/types/`)
}

export function getGenerations() {
  return request(`${API_BASE}/generations/`)
}

export function getTms() {
  return request(`${API_BASE}/tms/`)
}

export function getMoveDetail(identifier) {
  return request(`${API_BASE}/moves/${identifier}/`)
}
