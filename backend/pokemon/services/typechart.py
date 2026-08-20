"""Type chart, cálculo de fraquezas/resistências/imunidades.

A função ``type_effectiveness`` é pura (sem rede): recebe os tipos defensores e
o mapa de relações de cada tipo (``damage_relations`` da PokeAPI) e devolve o
multiplicador de cada tipo atacante (0 / 0.25 / 0.5 / 1 / 2 / 4).
"""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.cache import cache

from .pokeapi import PokeAPIClientProtocol

TYPE_RELATIONS_CACHE_KEY = "pokedex:type-relations"
TOTAL_TYPES = 18

# Relações que interessam para defesa (o atacante é o outro tipo).
_DEFENSIVE_KEYS = ("double_damage_from", "half_damage_from", "no_damage_from")


def _to_names(entries: list[Any]) -> list[str]:
    """A PokeAPI devolve listas de objetos {'name', 'url'}, normaliza para nomes."""
    return [entry["name"] if isinstance(entry, dict) else str(entry) for entry in entries]


def build_type_relations(
    client: PokeAPIClientProtocol,
) -> dict[str, dict[str, list[str]]]:
    """Mapa {tipo → relações defensivas} para os 18 tipos (agregado cacheado)."""
    cached = cache.get(TYPE_RELATIONS_CACHE_KEY)
    if cached is not None:
        return cached

    relations: dict[str, dict[str, list[str]]] = {}
    for i in range(1, TOTAL_TYPES + 1):
        type_data = client.get_resource("type", str(i))
        damage = type_data.get("damage_relations", {})
        relations[type_data["name"]] = {
            key: _to_names(damage.get(key, [])) for key in _DEFENSIVE_KEYS
        }

    cache.set(TYPE_RELATIONS_CACHE_KEY, relations, timeout=settings.POKEAPI_CACHE_TTL)
    return relations


def type_effectiveness(
    defending_types: list[str],
    type_relations: dict[str, dict[str, list[str]]],
) -> dict[str, float]:
    """Multiplicador de cada tipo atacante contra o conjunto de tipos defensores.

    Ex.: ['fire', 'flying'] (Charizard) → 'rock': 4.0, 'ground': 0.0, 'grass': 0.25.
    """
    multipliers: dict[str, float] = {}
    for attacker in type_relations:
        multiplier = 1.0
        for defending in defending_types:
            relations = type_relations.get(defending, {})
            if attacker in relations.get("double_damage_from", []):
                multiplier *= 2.0
            elif attacker in relations.get("half_damage_from", []):
                multiplier *= 0.5
            elif attacker in relations.get("no_damage_from", []):
                multiplier = 0.0
        multipliers[attacker] = multiplier
    return multipliers


def partition_effectiveness(effectiveness: dict[str, float]) -> dict[str, list[dict[str, Any]]]:
    """Divide o mapa em fraquezas (×2/×4), resistências (×½/×¼) e imunidades (×0)."""
    weakness_entries: list[dict[str, Any]] = [
        {"type": t, "multiplier": m} for t, m in effectiveness.items() if m > 1
    ]
    resistance_entries: list[dict[str, Any]] = [
        {"type": t, "multiplier": m} for t, m in effectiveness.items() if 0 < m < 1
    ]
    immunity_entries: list[dict[str, Any]] = [
        {"type": t} for t, m in effectiveness.items() if m == 0
    ]
    weaknesses = sorted(
        weakness_entries, key=lambda item: (-item["multiplier"], item["type"])
    )
    resistances = sorted(
        resistance_entries, key=lambda item: (item["multiplier"], item["type"])
    )
    immunities = sorted(immunity_entries, key=lambda item: item["type"])
    return {
        "weaknesses": weaknesses,
        "resistances": resistances,
        "immunities": immunities,
    }
