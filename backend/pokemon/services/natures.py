"""Melhores naturezas por estratégia, heurística sobre os stats base.

Abordagem (ProjectPokemon-Dados §8):
1. Estratégia define o stat a aumentar (attack / special-attack / speed);
   "bulky" aumenta o melhor stat defensivo;
2. O stat a baixar é o *mais fraco* do Pokémon entre os candidatos possíveis
   (exclui o boost e o HP, as naturezas nunca afetam HP);
3. Devolve a natureza correspondente + alternativa (2º candidato mais fraco).

Os dados das naturezas vêm da PokeAPI (/nature/{1..25}), agregados em cache.
"""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.cache import cache

from .pokeapi import PokeAPIClientProtocol

NATURE_MAP_CACHE_KEY = "pokedex:nature-map"
TOTAL_NATURES = 25

# Estratégias expostas à API (chaves estáveis para o frontend).
STRATEGIES: tuple[str, ...] = ("physical", "special", "fast", "bulky")

_STRATEGY_BOOST = {
    "physical": "attack",
    "special": "special-attack",
    "fast": "speed",
}

_STRATEGY_LABEL = {
    "physical": "Physical",
    "special": "Special",
    "fast": "Fast (sweeper)",
    "bulky": "Bulky",
}

_STAT_LABELS = {
    "hp": "HP",
    "attack": "Attack",
    "defense": "Defense",
    "special-attack": "Sp. Atk",
    "special-defense": "Sp. Def",
    "speed": "Speed",
}


def get_nature_map(client: PokeAPIClientProtocol) -> dict[tuple[str, str], str]:
    """(stat aumentado, stat baixado) → nome da natureza (agregado cacheado)."""
    cached = cache.get(NATURE_MAP_CACHE_KEY)
    if cached is not None:
        return {tuple(k): v for k, v in cached.items()}

    mapping: dict[tuple[str, str], str] = {}
    for i in range(1, TOTAL_NATURES + 1):
        nature = client.get_resource("nature", str(i))
        increased = nature.get("increased_stat")
        decreased = nature.get("decreased_stat")
        if increased and decreased:
            mapping[(increased["name"], decreased["name"])] = nature["name"]

    cache.set(NATURE_MAP_CACHE_KEY, mapping, timeout=settings.POKEAPI_CACHE_TTL)
    return mapping


def _reason(strategy: str, boost: str, lower: str) -> str:
    return (
        f"{_STRATEGY_LABEL[strategy]}: raises {_STAT_LABELS.get(boost, boost)} "
        f"and lowers {_STAT_LABELS.get(lower, lower)} (your weakest stat)."
    )


def best_natures(
    client: PokeAPIClientProtocol,
    stats: dict[str, int],
    strategy: str,
) -> list[dict[str, Any]]:
    """Naturezas recomendadas para uma estratégia. Devolve 1–2 sugestões."""
    if strategy not in STRATEGIES:
        raise ValueError(f"Estratégia desconhecida: {strategy}")

    if strategy == "bulky":
        boost = (
            "defense"
            if stats.get("defense", 0) >= stats.get("special-defense", 0)
            else "special-defense"
        )
    else:
        boost = _STRATEGY_BOOST[strategy]

    # Candidatos a "stat a baixar": tudo exceto o boost e o HP (não afetado por naturezas).
    candidates = [s for s in stats if s not in (boost, "hp")]
    if not candidates:
        return []
    ordered = sorted(candidates, key=lambda s: stats[s])

    nature_map = get_nature_map(client)
    suggestions = []
    for lower_candidate in ordered[:2]:
        nature = nature_map.get((boost, lower_candidate))
        if nature:
            suggestions.append(
                {
                    "nature": nature,
                    "boost": boost,
                    "lower": lower_candidate,
                    "reason": _reason(strategy, boost, lower_candidate),
                }
            )
    return suggestions
