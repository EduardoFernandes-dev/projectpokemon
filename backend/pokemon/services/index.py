"""Índice da Pokédex, mapa id → {id, name, types, sprite} para todos os Pokémon.

Estratégia (ProjectPokemon-Dados §3, ADR-005): a PokeAPI não tem um endpoint de
"lista com tipos". Em vez de N+1 chamadas por Pokémon, o índice é construído a
partir de poucos recursos cacheados:

- ``/pokemon?limit=100000`` → lista completa de nomes (1 chamada);
- ``/type/{1..18}`` → tipos por Pokémon (18 chamadas).

Total: 19 chamadas PokeAPI uma única vez; depois 100% cache. Para 1025 Pokémon,
filtrar em memória é trivial (<5ms), sem necessidade de base de dados.
"""

from __future__ import annotations

import re
from typing import Any

from django.conf import settings
from django.core.cache import cache

from .pokeapi import PokeAPIClient, PokeAPIClientProtocol, PokeAPIError

SUMMARY_CACHE_KEY = "pokedex:summary"
SPRITE_BASE = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon"
TOTAL_TYPES = 18  # tipos canónicos (gen 1–9); "stellar"/"unknown" ficam de fora
_MAX_SEARCH_RESULTS = 100

_POKEMON_ID_RE = re.compile(r"/pokemon/(\d+)/")
_GENERATION_ID_RE = re.compile(r"/generation/(\d+)/")


def slugify(name: str) -> str:
    """Normaliza nomes da PokeAPI ('mr. mime' → 'mr-mime') para comparar."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


class PokemonIndex:
    def __init__(self, client: PokeAPIClientProtocol | None = None) -> None:
        self.client = client or PokeAPIClient()

    # ── Construção do índice ────────────────────────────────────────────────
    def _types_by_pokemon(self) -> dict[str, list[str]]:
        """name do Pokémon → lista de tipos, a partir de /type/{1..18} (cacheado)."""
        mapping: dict[str, list[str]] = {}
        for i in range(1, TOTAL_TYPES + 1):
            type_data = self.client.get_resource("type", str(i))
            for entry in type_data.get("pokemon", []):
                name = entry["pokemon"]["name"]
                mapping.setdefault(name, []).append(type_data["name"])
        return mapping

    def summary(self) -> list[dict[str, Any]]:
        cached = cache.get(SUMMARY_CACHE_KEY)
        if cached is not None:
            return cached

        types_by_name = self._types_by_pokemon()
        summary: list[dict[str, Any]] = []
        for entry in self.client.get_list("pokemon").get("results", []):
            match = _POKEMON_ID_RE.search(entry["url"])
            if not match:
                continue
            pid = int(match.group(1))
            summary.append(
                {
                    "id": pid,
                    "name": entry["name"],
                    "types": types_by_name.get(entry["name"], []),
                    "sprite": f"{SPRITE_BASE}/{pid}.png",
                }
            )
        summary.sort(key=lambda p: p["id"])
        cache.set(SUMMARY_CACHE_KEY, summary, timeout=settings.POKEAPI_LIST_CACHE_TTL)
        return summary

    # ── Operações usadas pelas views ────────────────────────────────────────
    def search(
        self,
        query: str,
        type_names: list[str] | None = None,
        generation: str | None = None,
    ) -> list[dict[str, Any]]:
        """Pesquisa por substring no nome (case-insensitive), com filtros opcionais.

        Os filtros de tipo/geração aplicam-se aos resultados da pesquisa, o mesmo mecanismo de ``list_pokemon`` (ProjectPokemon-Dados §3).
        """
        matches = [p for p in self.summary() if query in p["name"]]
        matches = self._apply_filters(matches, type_names, generation)
        return matches[:_MAX_SEARCH_RESULTS]

    def _apply_filters(
        self,
        pokemon: list[dict[str, Any]],
        type_names: list[str] | None,
        generation: str | None,
    ) -> list[dict[str, Any]]:
        """Filtra uma lista de resumos por tipo(s) e/ou geração (valida os inputs).

        Com vários tipos, o Pokémon tem de os ter **todos**, a ordem não
        importa (poison+grass ≡ grass+poison).
        """
        if type_names:
            valid = self._valid_type_names()
            unknown = [t for t in type_names if t not in valid]
            if unknown:
                raise PokeAPIError(f"Invalid type: '{unknown[0]}'.", status=400)
            required = set(type_names)
            pokemon = [p for p in pokemon if required.issubset(p["types"])]

        if generation:
            gen_id = self._resolve_generation_id(generation)
            if gen_id is None:
                raise PokeAPIError(f"Invalid generation: '{generation}'.", status=400)
            species = self.client.get_resource("generation", str(gen_id))
            species_slugs = {slugify(s["name"]) for s in species.get("pokemon_species", [])}
            pokemon = [p for p in pokemon if p["name"] in species_slugs]

        return pokemon

    def _resolve_generation_id(self, generation: str) -> int | None:
        """Aceita 'generation-i' (nome PokeAPI) ou o número da geração."""
        if re.fullmatch(r"\d+", generation):
            return int(generation)
        for gen in self.client.get_list("generation").get("results", []):
            if gen["name"] == generation:
                match = _GENERATION_ID_RE.search(gen["url"])
                return int(match.group(1)) if match else None
        return None

    def _valid_type_names(self) -> set[str]:
        data = self.client.get_list("type").get("results", [])
        return {t["name"] for t in data if t["name"] not in {"unknown", "shadow", "stellar"}}

    def list_pokemon(
        self,
        limit: int,
        offset: int,
        type_names: list[str] | None = None,
        generation: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """Lista paginada com filtros por tipo(s) e/ou geração. Devolve (fatia, total)."""
        pokemon = self.summary()
        pokemon = self._apply_filters(pokemon, type_names, generation)

        total = len(pokemon)
        return pokemon[offset : offset + limit], total
