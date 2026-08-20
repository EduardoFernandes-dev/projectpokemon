import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  ApiError,
  getGenerations,
  getMoveDetail,
  getPokemonDetail,
  getPokemonList,
  getTms,
  getTypes,
  searchPokemon,
} from '../services/api'

function mockFetchOnce(status, body) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: status >= 200 && status < 300,
      status,
      json: () => Promise.resolve(body),
    }),
  )
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('api', () => {
  it('searchPokemon constrói o URL com a query codificada', async () => {
    mockFetchOnce(200, { results: [] })
    await searchPokemon('pikachu')
    expect(fetch).toHaveBeenCalledWith('/api/pokemon/search/?q=pikachu')
  })

  it('getPokemonList envia limit/offset e filtros', async () => {
    mockFetchOnce(200, { count: 1, results: [] })
    await getPokemonList(60, 120, { type: ['fire'], generation: 'generation-i' })
    expect(fetch).toHaveBeenCalledWith(
      '/api/pokemon/?limit=60&offset=120&type=fire&generation=generation-i',
    )
  })

  it('getPokemonList envia vários tipos como parâmetros repetidos', async () => {
    mockFetchOnce(200, { count: 1, results: [] })
    await getPokemonList(60, 0, { type: ['poison', 'grass'] })
    expect(fetch).toHaveBeenCalledWith(
      '/api/pokemon/?limit=60&offset=0&type=poison&type=grass',
    )
  })

  it('getPokemonList omite filtros vazios', async () => {
    mockFetchOnce(200, { count: 0, results: [] })
    await getPokemonList(20, 0, {})
    expect(fetch).toHaveBeenCalledWith('/api/pokemon/?limit=20&offset=0')
  })

  it('getPokemonDetail usa o identifier', async () => {
    mockFetchOnce(200, { id: 6 })
    await getPokemonDetail(6)
    expect(fetch).toHaveBeenCalledWith('/api/pokemon/6/')
  })

  it('getTypes e getGenerations apontam aos endpoints certos', async () => {
    mockFetchOnce(200, { results: [] })
    await getTypes()
    expect(fetch).toHaveBeenCalledWith('/api/types/')
    await getGenerations()
    expect(fetch).toHaveBeenCalledWith('/api/generations/')
  })

  it('getTms e getMoveDetail apontam aos endpoints certos', async () => {
    mockFetchOnce(200, { results: [] })
    await getTms()
    expect(fetch).toHaveBeenCalledWith('/api/tms/')
    await getMoveDetail(36)
    expect(fetch).toHaveBeenCalledWith('/api/moves/36/')
  })

  it('propaga a mensagem de erro do backend', async () => {
    mockFetchOnce(404, { error: 'Recurso não encontrado na PokeAPI.' })
    await expect(getPokemonDetail(99999)).rejects.toMatchObject({
      status: 404,
      message: 'Recurso não encontrado na PokeAPI.',
    })
  })

  it('usa detail quando não há campo error', async () => {
    mockFetchOnce(429, { detail: 'Request was throttled.' })
    await expect(searchPokemon('pikachu')).rejects.toMatchObject({
      status: 429,
      message: 'Request was throttled.',
    })
  })

  it('lança ApiError com mensagem genérica quando o corpo não é JSON', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: () => Promise.reject(new Error('não é JSON')),
      }),
    )
    const error = await searchPokemon('pikachu').catch((e) => e)
    expect(error).toBeInstanceOf(ApiError)
    expect(error.status).toBe(500)
  })

  it('lança ApiError sem ligação quando fetch falha', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('network down')))
    const error = await searchPokemon('pikachu').catch((e) => e)
    expect(error).toBeInstanceOf(ApiError)
    expect(error.status).toBe(0)
  })
})
