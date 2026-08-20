const TYPE_COLORS = {
  normal: '#A8A77A',
  fire: '#EE8130',
  water: '#6390F0',
  electric: '#F7D02C',
  grass: '#7AC74C',
  ice: '#96D9D6',
  fighting: '#C22E28',
  poison: '#A33EA1',
  ground: '#E2BF65',
  flying: '#A98FF3',
  psychic: '#F95587',
  bug: '#A6B91A',
  rock: '#B6A136',
  ghost: '#735797',
  dragon: '#6F35FC',
  dark: '#705746',
  steel: '#B7B7CE',
  fairy: '#D685AD',
}

export function typeColors() {
  return TYPE_COLORS
}

/**
 * Ícone oficial do tipo (SVG usado nos jogos Pokémon recentes).
 * Fonte: repositório duiker101/pokemon-type-svg-icons (mesmos ícones
 * de tipo que aparecem dentro dos jogos da Gen 8/9).
 */
export function typeIconUrl(name) {
  return `https://raw.githubusercontent.com/duiker101/pokemon-type-svg-icons/master/icons/${name}.svg`
}

/**
 * Cor de um tipo em rgba com a opacidade dada, para fundos translúcidos
 * (ex.: linha de move com a cor do seu tipo).
 */
export function typeColorWithAlpha(name, alpha) {
  const hex = TYPE_COLORS[name] || '#888888'
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

export function formatTypeName(name) {
  return name.replaceAll('-', ' ')
}

/**
 * Nome de Pokémon apresentável: capitaliza cada palavra e troca hífenes
 * por espaços, "charizard-mega-x" → "Charizard Mega X".
 */
export function formatPokemonName(name) {
  return name
    .split('-')
    .map((part) => (part ? part[0].toUpperCase() + part.slice(1) : part))
    .join(' ')
}
