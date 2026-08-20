import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import FilterPanel from '../components/FilterPanel'

vi.mock('../services/api', () => ({
  getTypes: vi.fn().mockResolvedValue({
    results: [
      { name: 'fire' },
      { name: 'water' },
      { name: 'grass' },
      { name: 'poison' },
      { name: 'unknown' }, // deve ser filtrado
    ],
  }),
  getGenerations: vi.fn().mockResolvedValue({
    results: [{ name: 'generation-i' }, { name: 'generation-ii' }],
  }),
}))

function renderPanel() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <FilterPanel filters={{ type: [], generation: '' }} onChange={vi.fn()} />
    </QueryClientProvider>,
  )
}

describe('FilterPanel', () => {
  it('carrega tipos (com ícones) e gerações (sem unknown/shadow)', async () => {
    renderPanel()
    // esperar que os dados do react-query cheguem aos chips
    await screen.findByRole('img', { name: 'fire' })

    expect(screen.getByRole('img', { name: 'fire' })).toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'water' })).toBeInTheDocument()
    expect(screen.queryByRole('img', { name: 'unknown' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Gen 1' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Gen 2' })).toBeInTheDocument()
  })

  it('propaga a seleção de um tipo ao clicar no chip', async () => {
    const onChange = vi.fn()
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={queryClient}>
        <FilterPanel filters={{ type: [], generation: '' }} onChange={onChange} />
      </QueryClientProvider>,
    )

    const fireChip = await screen.findByRole('img', { name: 'fire' })
    fireEvent.click(fireChip)
    await waitFor(() =>
      expect(onChange).toHaveBeenCalledWith({ type: ['fire'], generation: '' }),
    )
  })

  it('seleciona até 2 tipos e ignora ordem (poison+grass ≡ grass+poison)', async () => {
    const onChange = vi.fn()
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const { rerender } = render(
      <QueryClientProvider client={queryClient}>
        <FilterPanel filters={{ type: [], generation: '' }} onChange={onChange} />
      </QueryClientProvider>,
    )

    // clicar poison → ['poison']
    const poisonChip = await screen.findByRole('img', { name: 'poison' })
    fireEvent.click(poisonChip)
    await waitFor(() =>
      expect(onChange).toHaveBeenLastCalledWith({ type: ['poison'], generation: '' }),
    )

    // estado interno atualizado com poison selecionado; clicar grass → ['poison', 'grass']
    rerender(
      <QueryClientProvider client={queryClient}>
        <FilterPanel
          filters={{ type: ['poison'], generation: '' }}
          onChange={onChange}
        />
      </QueryClientProvider>,
    )
    const grassChip = await screen.findByRole('img', { name: 'grass' })
    fireEvent.click(grassChip)
    await waitFor(() =>
      expect(onChange).toHaveBeenLastCalledWith({ type: ['poison', 'grass'], generation: '' }),
    )

    // tocar num selecionado remove-o
    rerender(
      <QueryClientProvider client={queryClient}>
        <FilterPanel
          filters={{ type: ['poison', 'grass'], generation: '' }}
          onChange={onChange}
        />
      </QueryClientProvider>,
    )
    fireEvent.click(await screen.findByRole('img', { name: 'poison' }))
    await waitFor(() =>
      expect(onChange).toHaveBeenLastCalledWith({ type: ['grass'], generation: '' }),
    )
  })

  it('propaga a seleção de geração ao clicar no chip', async () => {
    const onChange = vi.fn()
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={queryClient}>
        <FilterPanel filters={{ type: [], generation: '' }} onChange={onChange} />
      </QueryClientProvider>,
    )

    const genChip = await screen.findByRole('button', { name: 'Gen 2' })
    fireEvent.click(genChip)
    await waitFor(() =>
      expect(onChange).toHaveBeenCalledWith({ type: [], generation: 'generation-ii' }),
    )
  })
})
