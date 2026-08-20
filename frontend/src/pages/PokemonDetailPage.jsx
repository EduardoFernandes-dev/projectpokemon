import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from 'recharts'
import ErrorState from '../components/ErrorState'
import LoadingState from '../components/LoadingState'
import { usePokemonDetail } from '../hooks/usePokemon'
import { formatPokemonName, formatTypeName, typeColors, typeColorWithAlpha, typeIconUrl } from '../utils/typeColors'

const STAT_LABELS = {
  hp: 'HP',
  attack: 'ATK',
  defense: 'DEF',
  'special-attack': 'SPA',
  'special-defense': 'SPD',
  speed: 'SPE',
}

const GROWTH_RATE_LABELS = {
  'medium-slow': 'Medium slow',
  'medium-fast': 'Medium fast',
  slow: 'Slow',
  fast: 'Fast',
  'erratic': 'Erratic',
  'fluctuating': 'Fluctuating',
}

const POKEDEX_LABELS = {
  national: 'National',
  kanto: 'Kanto',
  johto: 'Johto',
  hoenn: 'Hoenn',
  sinnoh: 'Sinnoh',
  unova: 'Unova',
  kaloscentral: 'Kalos (Central)',
  kaloscoastal: 'Kalos (Coastal)',
  kalosmountain: 'Kalos (Mountain)',
  alola: 'Alola',
  galar: 'Galar',
  isleofarmor: 'Isle of Armor',
  crowntundra: 'Crown Tundra',
  hisui: 'Hisui',
  paldea: 'Paldea',
  kitakami: 'Kitakami',
  blueberry: 'Blueberry',
  letsgokanto: "Let's Go Kanto",
  letsgoeevee: "Let's Go Eevee",
  letsgopikachu: "Let's Go Pikachu",
  conquestgallery: 'Conquest',
}

const POKEDEX_LABEL = (name) => {
  // remove prefixos de variante (original-, updated-, extended-) → região base
  const key = name
    .replace(/^(original|updated|extended)-/, '')
    .replaceAll('-', '')
    .toLowerCase()
  return POKEDEX_LABELS[key] || name
}

const SPRITE_URL = (id) =>
  `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${id}.png`

const GEN_NUMBER = {
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

const STRATEGY_LABELS = {
  physical: 'Physical',
  special: 'Special',
  fast: 'Fast',
  bulky: 'Bulky',
}

const MAX_STAT = 255

function playCry(cry, ref) {
  if (!cry) return
  try {
    ref.current?.pause()
    ref.current = new Audio(cry)
    ref.current.volume = 0.3
    ref.current.play().catch(() => {})
  } catch {
    // autoplay bloqueado, o botão 🔊 permite reproduzir manualmente
  }
}

export default function PokemonDetailPage() {
  const { id } = useParams()
  const { data: detail, isLoading, isError, error, refetch } = usePokemonDetail(id)

  const [showShiny, setShowShiny] = useState(false)
  const [imgError, setImgError] = useState(false)
  const [movesTab, setMovesTab] = useState('level-up')
  const cryRef = useRef(null)

  useEffect(() => {
    setShowShiny(false)
    setImgError(false)
    setMovesTab('level-up')
    if (detail?.cry) playCry(detail.cry, cryRef)
    return () => {
      cryRef.current?.pause()
      cryRef.current = null
    }
  }, [detail?.cry, id])

  if (isLoading) {
    return (
      <main className="app-main">
        <div className="back-link back-link-placeholder" aria-hidden="true" />
        <DetailSkeleton />
      </main>
    )
  }

  if (isError) {
    return (
      <main className="app-main">
        <ErrorState error={error} onRetry={refetch} />
      </main>
    )
  }

  if (!detail) return null

  const colors = typeColors()
  const primaryColor = colors[detail.types[0]?.name] || '#888'
  const mainSprite = showShiny
    ? detail.sprites.animated_shiny || detail.sprites.front_shiny
    : detail.sprites.animated || detail.sprites.front_default
  const mainIsAnimated = showShiny ? !!detail.sprites.animated_shiny : !!detail.sprites.animated

  return (
    <main className="app-main">
      <Link to="/" className="back-link">
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
        Back to Pokédex
      </Link>

      <article className="detail-page">
        <header
          className="detail-header"
          style={{
            background: `linear-gradient(135deg, ${primaryColor}, ${primaryColor}dd)`,
          }}
        >
          <div className="detail-id">#{String(detail.id).padStart(3, '0')}</div>
          <h2 className="detail-name">{formatPokemonName(detail.name)}</h2>
          {detail.species?.genus && (
            <div className="detail-genus">{detail.species.genus}</div>
          )}
          <div className="detail-types-row">
            {detail.types.map((t) => (
              <span key={t.slot} className="type-badge large" style={{ backgroundColor: colors[t.name] || '#888' }}>
                <img src={typeIconUrl(t.name)} alt={t.name} title={t.name} className="type-icon large" />
              </span>
            ))}
          </div>
        </header>

        {/* Sprites + som */}
        <div className="detail-sprites">
          <div className="sprite-main">
            {mainSprite && !imgError ? (
              <img
                src={mainSprite}
                alt={detail.name}
                className={mainIsAnimated ? 'sprite-animated' : 'sprite-static'}
                onError={() => setImgError(true)}
              />
            ) : (
              <img
                src={detail.sprites.official_artwork || detail.sprites.front_default}
                alt={detail.name}
                className="sprite-static"
              />
            )}
          </div>
          <div className="sprite-secondary">
            <button
              type="button"
              className={`sprite-thumb ${!showShiny ? 'active' : ''}`}
              onClick={() => setShowShiny(false)}
              aria-label="Normal sprite"
              aria-pressed={!showShiny}
            >
              <img src={detail.sprites.front_default} alt="" />
            </button>
            <button
              type="button"
              className={`sprite-thumb ${showShiny ? 'active' : ''}`}
              onClick={() => setShowShiny(true)}
              aria-label="Shiny sprite"
              aria-pressed={showShiny}
            >
              <img src={detail.sprites.front_shiny} alt="" />
            </button>
          </div>
          {detail.cry && (
            <button
              type="button"
              className="cry-button"
              onClick={() => playCry(detail.cry, cryRef)}
              aria-label="Play Pokémon cry"
              title="Play sound"
            >
              🔊
            </button>
          )}
        </div>

        {/* Evolution chain */}
        {(detail.evolution_chain?.length > 1 || detail.mega_evolutions?.length > 0) && (
          <section className="detail-section">
            <h3>Evolution Chain</h3>
            <EvolutionChain
              chain={detail.evolution_chain}
              megas={detail.mega_evolutions ?? []}
              currentId={detail.id}
              primaryColor={primaryColor}
            />
          </section>
        )}

        {/* Breeding & training */}
        <section className="detail-section">
          <h3>Breeding &amp; Training</h3>
          <div className="training-grid">
            <div className="training-item">
              <span className="info-label">Egg groups</span>
              <span className="egg-badges">
                {detail.species?.egg_groups?.length
                  ? detail.species.egg_groups.map((g) => (
                      <span key={g} className="egg-badge">
                        {formatTypeName(g)}
                      </span>
                    ))
                  : ', '}
              </span>
            </div>
            <div className="training-item">
              <span className="info-label">Gender</span>
              <GenderRatio genderRate={detail.species?.gender_rate} />
            </div>
            <div className="training-item">
              <span className="info-label">Catch rate</span>
              <span>{detail.species?.capture_rate ?? ', '}</span>
            </div>
            <div className="training-item">
              <span className="info-label">Base friendship</span>
              <span>{detail.species?.base_happiness ?? ', '}</span>
            </div>
            <div className="training-item">
              <span className="info-label">Growth rate</span>
              <span>
                {detail.species?.growth_rate
                  ? GROWTH_RATE_LABELS[detail.species.growth_rate] || detail.species.growth_rate
                  : ', '}
              </span>
            </div>
            {Object.keys(detail.ev_yield || {}).length > 0 && (
              <div className="training-item">
                <span className="info-label">EV yield</span>
                <span>
                  {Object.entries(detail.ev_yield)
                    .map(([stat, val]) => `${val} ${STAT_LABELS[stat] || stat}`)
                    .join(' · ')}
                </span>
              </div>
            )}
          </div>
        </section>

        {/* Base Stats, radar hexagonal com números */}
        <section className="detail-section">
          <h3>Base Stats</h3>
          <StatsRadar stats={detail.stats} primaryColor={primaryColor} />
          <div className="stat-total">
            Total: {detail.stats.reduce((sum, s) => sum + s.base_stat, 0)}
          </div>
        </section>

        {/* Weaknesses & resistances */}
        <section className="detail-section">
          <h3>Weaknesses &amp; Resistances</h3>
          <EffectivenessGroup label="Weaknesses" items={detail.type_effectiveness.weaknesses} colors={colors} />
          <EffectivenessGroup label="Resistances" items={detail.type_effectiveness.resistances} colors={colors} />
          <EffectivenessGroup label="Immunities" items={detail.type_effectiveness.immunities.map((i) => ({ ...i, multiplier: 0 }))} colors={colors} />
        </section>

        {/* Info */}
        <section className="detail-section">
          <div className="info-grid">
            <div className="info-item">
              <div className="info-body">
                <span className="info-label">Height</span>
                <span className="info-value">{(detail.height / 10).toFixed(1)} m</span>
              </div>
            </div>
            <div className="info-item">
              <div className="info-body">
                <span className="info-label">Weight</span>
                <span className="info-value">{(detail.weight / 10).toFixed(1)} kg</span>
              </div>
            </div>
            <div className="info-item">
              <div className="info-body">
                <span className="info-label">Base Exp.</span>
                <span className="info-value">{detail.base_experience || ', '}</span>
              </div>
            </div>
            {detail.species?.pokedex_numbers?.length > 0 && (
              <div className="info-item pokedex-numbers-cell">
                <div className="info-body">
                  <span className="info-label">Dex no. by region</span>
                  <span className="pokedex-numbers">
                    {detail.species.pokedex_numbers
                      .filter((p) => p.pokedex !== 'national')
                      .slice(0, 4)
                      .map((p) => (
                        <span key={p.pokedex} className="pokedex-number">
                          {POKEDEX_LABEL(p.pokedex)}: {p.entry}
                        </span>
                      ))}
                  </span>
                </div>
              </div>
            )}
            <div className="info-item">
              <div className="info-body">
                <span className="info-label">Habitat</span>
                <span className="info-value">{detail.species?.habitat || ', '}</span>
              </div>
            </div>
            <div className="info-item">
              <div className="info-body">
                <span className="info-label">Generation</span>
                <span className="info-value">
                  {GEN_NUMBER[detail.species?.generation] ||
                    detail.species?.generation?.replace('generation-', 'Gen ') ||
                    ', '}
                </span>
              </div>
            </div>
            <div className="info-item">
              <div className="info-body">
                <span className="info-label">Rarity</span>
                <span className="info-value">
                  {detail.species?.is_legendary
                    ? 'Legendary'
                    : detail.species?.is_mythical
                      ? 'Mythical'
                      : 'Common'}
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* Abilities */}
        <section className="detail-section">
          <h3>Abilities</h3>
          <div className="abilities-list">
            {detail.abilities.map((a) => (
              <div
                key={a.name}
                className={`ability-card ${a.is_hidden ? 'hidden' : ''}`}
              >
                <span className="ability-badge">
                  {formatTypeName(a.name)}
                  {a.is_hidden && ' (H)'}
                </span>
                {a.description && (
                  <p className="ability-description">{a.description}</p>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* Best natures */}
        <section className="detail-section">
          <h3>Best Natures</h3>
          <div className="natures-grid">
            {Object.entries(detail.best_natures).map(([strategy, suggestions]) => (
              <div key={strategy} className="nature-card">
                <div className="nature-strategy">
                  {STRATEGY_LABELS[strategy] || strategy}
                </div>
                {suggestions.length > 0 ? (
                  suggestions.map((n, i) => (
                    <div key={n.nature} className={`nature-row ${i === 0 ? 'primary' : ''}`}>
                      <div className="nature-top">
                        <span className="nature-name">{formatTypeName(n.nature)}</span>
                        <span className="nature-modifiers">
                          ↑ {n.boost} · ↓ {n.lower}
                        </span>
                      </div>
                      <p className="nature-reason">{n.reason}</p>
                    </div>
                  ))
                ) : (
                  <p className="muted">No suggestions for this strategy.</p>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* Moves */}
        <section className="detail-section">
          <h3>Moves ({detail.moves.total})</h3>
          <div className="moves-tabs" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={movesTab === 'level-up'}
              className={`moves-tab ${movesTab === 'level-up' ? 'active' : ''}`}
              onClick={() => setMovesTab('level-up')}
            >
              Level-up ({detail.moves.level_up.length})
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={movesTab === 'machines'}
              className={`moves-tab ${movesTab === 'machines' ? 'active' : ''}`}
              onClick={() => setMovesTab('machines')}
            >
              TMs ({detail.moves.machines.length})
            </button>
          </div>

          {movesTab === 'level-up' ? (
            <div className="moves-level-list">
              <div className="move-row move-header" aria-hidden="true">
                <span className="move-prefix">Lv</span>
                <span className="move-type-icon" />
                <span className="move-name">Move</span>
                <span className="move-class">Class</span>
                <span className="move-power">Power</span>
              </div>
              {detail.moves.level_up.length > 0 ? (
                detail.moves.level_up.map((m) => (
                  <MoveRow
                    key={`${m.level}-${m.name}`}
                    move={m}
                    colors={colors}
                    prefix={`Lv ${m.level}`}
                  />
                ))
              ) : (
                <p className="muted">No level-up moves in the latest game.</p>
              )}
            </div>
          ) : (
            <div className="moves-grid">
              <div className="move-row move-header" aria-hidden="true">
                <span className="move-prefix">TM</span>
                <span className="move-type-icon" />
                <span className="move-name">Move</span>
                <span className="move-class">Class</span>
                <span className="move-power">Power</span>
              </div>
              {detail.moves.machines.length > 0 ? (
                detail.moves.machines.map((m) => (
                  <MoveRow key={m.name} move={m} colors={colors} prefix="TM" />
                ))
              ) : (
                <p className="muted">No TMs in the latest game.</p>
              )}
            </div>
          )}
        </section>

        {/* Flavor text */}
        {detail.species?.flavor_text && (
          <section className="detail-section flavor-text">
            <p>{detail.species.flavor_text}</p>
            {detail.species.flavor_text_version && (
              <span className="flavor-version">
                {detail.species.flavor_text_version}
              </span>
            )}
          </section>
        )}
      </article>
    </main>
  )
}

function EffectivenessGroup({ label, items, colors }) {
  if (!items || items.length === 0) return null
  const kind = label === 'Weaknesses' ? 'weak' : label === 'Immunities' ? 'immune' : 'resist'
  return (
    <div className="eff-group">
      <span className="eff-label">{label}</span>
      <div className="eff-chips">
        {items.map((item) => (
          <span
            key={item.type}
            className={`eff-chip ${kind}`}
            style={{ backgroundColor: colors[item.type] || '#888' }}
          >
            <img
              src={typeIconUrl(item.type)}
              alt={item.type}
              title={item.type}
              className="type-icon"
            />
            {item.multiplier != null && item.multiplier !== 0 && (
              <span className="eff-multiplier">×{item.multiplier}</span>
            )}
          </span>
        ))}
      </div>
    </div>
  )
}

/**
 * Skeleton da página de detalhe, imita o layout real (header, sprites,
 * grelha de info, secções) para o carregamento não parecer uma grelha
 * de cards vazios.
 */
function DetailSkeleton() {
  return (
    <article className="detail-page" aria-hidden="true">
      <div className="detail-header sk-header" />
      <div className="detail-sprites sk-sprites">
        <div className="sk-block sk-big" />
        <div className="sk-col">
          <div className="sk-block sk-thumb" />
          <div className="sk-block sk-thumb" />
        </div>
      </div>
      <div className="detail-section">
        <div className="sk-line sk-title" />
        <div className="sk-grid">
          <div className="sk-block sk-cell" />
          <div className="sk-block sk-cell" />
          <div className="sk-block sk-cell" />
          <div className="sk-block sk-cell" />
        </div>
      </div>
      <div className="detail-section">
        <div className="sk-line sk-title" />
        <div className="sk-block sk-rows" />
        <div className="sk-block sk-rows" />
      </div>
      <div className="detail-section">
        <div className="sk-line sk-title" />
        <div className="sk-block sk-rows" />
      </div>
    </article>
  )
}

function EvolutionChain({ chain, currentId, primaryColor, megas = [] }) {
  // group by depth: predecessors → current → successors
  const groups = chain.reduce((acc, node) => {
    if (!acc[node.depth]) acc[node.depth] = []
    acc[node.depth].push(node)
    return acc
  }, {})

  const current = chain.find((n) => n.id === currentId)

  const fromLabel = (f) => {
    if (f.trigger === 'level-up' && f.min_level) return `Lv. ${f.min_level}`
    if (f.trigger === 'use-item' && f.item) return formatPokemonName(f.item)
    if (f.trigger === 'trade') return 'trade'
    return formatPokemonName(f.trigger || 'evolving')
  }

  return (
    <div className="evolution-chain-wrap">
      <div className="evolution-chain">
        {Object.entries(groups).map(([depth, nodes], gi) => (
          <div key={depth} className="evo-group">
            {gi > 0 && <span className="evo-arrow">→</span>}
            <div className="evo-nodes">
              {nodes.map((node) => {
                const isCurrent = node.id === currentId
                const content = (
                  <>
                    <img src={SPRITE_URL(node.id)} alt={node.name} loading="lazy" />
                    <span className="evo-name">{formatPokemonName(node.name)}</span>
                    {isCurrent && (
                      <span className="evo-current" style={{ backgroundColor: primaryColor }}>
                        Current
                      </span>
                    )}
                  </>
                )
                return isCurrent ? (
                  <div key={node.id} className="evo-node current">
                    {content}
                  </div>
                ) : (
                  <Link
                    key={node.id}
                    to={`/pokemon/${node.id}`}
                    className="evo-node evo-link"
                    title={`Go to ${node.name}`}
                  >
                    {content}
                  </Link>
                )
              })}
            </div>
          </div>
        ))}
        {megas.length > 0 && (
          <div className="evo-group">
            <span className="evo-arrow">→</span>
            <div className="evo-nodes">
              {megas.map((mega) => (
                <Link
                  key={mega.id}
                  to={`/pokemon/${mega.id}`}
                  className="evo-node evo-link mega-node"
                  title={`Go to ${mega.name}`}
                >
                  <img src={SPRITE_URL(mega.id)} alt={mega.name} loading="lazy" />
                  <span className="evo-name">{formatPokemonName(mega.name)}</span>
                  <span className="evo-mega-badge">Mega</span>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
      {current?.evolves_from && (
        <p className="evo-from-note">
          Evolves from {formatPokemonName(current.evolves_from.name)}, {' '}
          {fromLabel(current.evolves_from)}
        </p>
      )}
    </div>
  )
}

/**
 * Linha/card de um move, como as Pokédex web:
 * ícone do tipo (com a cor do tipo), nome, classe de dano e power.
 * Moves de status não têm power → mostram ", ".
 */
function MoveRow({ move, colors, prefix }) {
  const type = move.type
  const damageClass = move.damage_class
  const hasPower = move.power != null
  // Fallback honesto: sem dados, mostra ", " em vez de inventar uma classe.
  const classLabel =
    damageClass === 'physical'
      ? 'Physical'
      : damageClass === 'special'
        ? 'Special'
        : damageClass === 'status'
          ? 'Status'
          : ', '

  const rowStyle = {
    backgroundColor: type
      ? typeColorWithAlpha(type, 0.16)
      : 'rgba(255, 255, 255, 0.04)',
  }

  const content = (
    <>
      <span className="move-prefix">{prefix}</span>
      <span
        className="move-type-icon"
        style={{ backgroundColor: type ? colors[type] || '#888' : 'transparent' }}
        title={type}
      >
        {type ? (
          <img src={typeIconUrl(type)} alt={type} className="type-icon" />
        ) : (
          ', '
        )}
      </span>
      <span className="move-name">{formatTypeName(move.name)}</span>
      <span
        className={`move-class ${damageClass || 'unknown'}`}
        title={
          damageClass === 'physical'
            ? 'Physical damage'
            : damageClass === 'special'
              ? 'Special damage'
              : damageClass === 'status'
                ? 'Status move (no damage)'
                : undefined
        }
      >
        {classLabel}
      </span>
      <span className="move-power">
        {hasPower ? move.power : ', '}
      </span>
    </>
  )

  if (move.id) {
    return (
      <Link to={`/move/${move.id}`} className="move-row" style={rowStyle} title={`See ${move.name}`}>
        {content}
      </Link>
    )
  }
  return (
    <div className="move-row" style={rowStyle}>
      {content}
    </div>
  )
}

function GenderRatio({ genderRate }) {
  if (genderRate == null || genderRate === -1) {
    return <span>Genderless</span>
  }
  const female = (genderRate / 8) * 100
  const male = 100 - female
  return (
    <span className="gender-ratio">
      <span className="gender-bar">
        <span className="gender-male" style={{ width: `${male}%` }} />
        <span className="gender-female" style={{ width: `${female}%` }} />
      </span>
      <span className="gender-labels">
        <span>♂ {male}%</span>
        <span>♀ {female}%</span>
      </span>
    </span>
  )
}

/**
 * Gráfico radar hexagonal dos 6 stats base (recharts).
 * Cada ponta é um stat; o número aparece junto à ponta para leitura exata.
 */
function StatsRadar({ stats, primaryColor }) {
  const data = stats.map((s) => ({
    subject: STAT_LABELS[s.name] || s.name,
    value: s.base_stat,
  }))

  const customTick = ({ payload, x, y, textAnchor }) => {
    const stat = data.find((d) => d.subject === payload.value)
    return (
      <g>
        <text
          x={x}
          y={y - 6}
          textAnchor={textAnchor}
          fill="#e0e0e0"
          fontSize={13}
          fontWeight={700}
        >
          {stat?.value}
        </text>
        <text x={x} y={y + 14} textAnchor={textAnchor} fill="#888" fontSize={10}>
          {payload.value}
        </text>
      </g>
    )
  }

  return (
    <div className="stats-radar">
      <ResponsiveContainer width="100%" height={320}>
        <RadarChart data={data} outerRadius="72%">
          <PolarGrid stroke="rgba(255,255,255,0.18)" />
          <PolarAngleAxis dataKey="subject" tick={customTick} />
          <PolarRadiusAxis domain={[0, MAX_STAT]} tick={false} axisLine={false} />
          <Radar
            dataKey="value"
            stroke={primaryColor}
            fill={primaryColor}
            fillOpacity={0.35}
            strokeWidth={2}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}
