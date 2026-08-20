"""Construção do payload de detalhe de um Pokémon.

Junta os recursos da PokeAPI (pokemon + species) com os cálculos locais:
fraquezas/resistências (typechart), melhores naturezas (natures) e moves
com nível/TM (filtrados pelo jogo mais recente).

Desempenho (ProjectPokemon-Desempenho §3): os fetches dos moves e das
abilities são paralelizados (ThreadPoolExecutor), um Pokémon com 150+
moves passava ~9s em série; em paralelo fica ~1s. O requests.Session é
thread-safe para GETs, e o cache do Django protege as escritas.
"""

from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from .natures import STRATEGIES, best_natures
from .pokeapi import PokeAPIClientProtocol, PokeAPIError
from .typechart import build_type_relations, partition_effectiveness, type_effectiveness

logger = logging.getLogger(__name__)

_VERSION_GROUP_ID_RE = re.compile(r"/version-group/(\d+)/")

# Workers para os fetches paralelos da PokeAPI (I/O-bound, não CPU).
# 20 workers: 158 moves ≈ 8 rondas × ~150ms ≈ 1.2s (vs 9.6s em série).
_MOVE_FETCH_WORKERS = 20


def _latest_move_entries(pokemon: dict[str, Any]) -> list[dict[str, Any]]:
    """Para cada move, escolhe o detalhe do version_group mais recente.

    A ordem dos version-groups na PokeAPI é cronológica pelo id do URL
    (/version-group/30/ = Scarlet/Violet, o mais recente da gen 9).
    """
    entries: list[dict[str, Any]] = []
    for move_entry in pokemon.get("moves", []):
        details = move_entry.get("version_group_details", [])
        if not details:
            continue
        best = max(details, key=lambda d: _version_group_order(d["version_group"]["url"]))
        entries.append(
            {
                "name": move_entry["move"]["name"],
                "url": move_entry["move"].get("url"),
                "method": best["move_learn_method"]["name"],
                # 0 = aprende ao nascer → exibir como nível 1.
                "level": max(best["level_learned_at"], 1),
            }
        )
    return entries


def _version_group_order(url: str) -> int:
    match = _VERSION_GROUP_ID_RE.search(url)
    return int(match.group(1)) if match else 0


def _move_detail(client: PokeAPIClientProtocol, url: str | None) -> dict[str, Any]:
    """Detalhe de um move: tipo, classe de dano e power (cacheado por URL).

    Formato real (PokeAPI /move/{id}): type.name, damage_class.name
    (physical/special/status), power (None para moves de status). Se o fetch
    falhar, devolve dados vazios, o frontend mostra o nome na mesma.
    """
    if not url:
        return {}
    try:
        data = client.fetch(url)
    except PokeAPIError:
        return {}
    return {
        "id": data.get("id"),
        "type": data.get("type", {}).get("name"),
        "damage_class": data.get("damage_class", {}).get("name"),
        "power": data.get("power"),
    }


def _move_details(
    client: PokeAPIClientProtocol, entries: list[dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    """Detalhes de vários moves em paralelo (I/O-bound).

    Um Pokémon pode ter 150+ moves, em série eram ~150 round-trips à
    PokeAPI (~9s); em paralelo com 10 workers fica ~1s. A cache-first do
    PokeAPIClient continua a valer (cada move só é pedido uma vez).
    """
    urls = [e["url"] for e in entries if e.get("url")]
    if not urls:
        return {}
    with ThreadPoolExecutor(max_workers=_MOVE_FETCH_WORKERS) as pool:
        fetched = list(pool.map(lambda url: _move_detail(client, url), urls))
    return dict(zip(urls, fetched))


def get_latest_moves(
    client: PokeAPIClientProtocol, pokemon: dict[str, Any]
) -> dict[str, Any]:
    """Moves por leveling e TM no jogo mais recente (ProjectPokemon-Dados §9)."""
    entries = _latest_move_entries(pokemon)
    details = _move_details(client, entries)
    level_up = sorted(
        (
            {"level": e["level"], "name": e["name"], **details.get(e["url"], {})}
            for e in entries
            if e["method"] == "level-up"
        ),
        key=lambda m: (m["level"], m["name"]),
    )
    machines = sorted(
        (
            {"name": e["name"], **details.get(e["url"], {})}
            for e in entries
            if e["method"] == "machine"
        ),
        key=lambda m: m["name"],
    )
    return {
        "level_up": level_up,
        "machines": machines,
        "total": len(level_up) + len(machines),
    }


def _species_payload(species: dict[str, Any]) -> dict[str, Any]:
    flavor = _english_flavor_text(species.get("flavor_text_entries", []))
    return {
        "name": species["name"],
        "genus": _english_genus(species.get("genera", [])),
        "generation": species["generation"]["name"],
        "habitat": species["habitat"]["name"] if species.get("habitat") else None,
        "is_legendary": species.get("is_legendary", False),
        "is_mythical": species.get("is_mythical", False),
        "flavor_text": flavor["text"] if flavor else None,
        "flavor_text_version": flavor["version"] if flavor else None,
        # Criação & treino (secções Breeding/Training do Pokémon Database)
        "egg_groups": [g["name"] for g in species.get("egg_groups", [])],
        "hatch_counter": species.get("hatch_counter"),
        "capture_rate": species.get("capture_rate"),
        "base_happiness": species.get("base_happiness"),
        "growth_rate": (
            species["growth_rate"]["name"] if species.get("growth_rate") else None
        ),
        "gender_rate": species.get("gender_rate"),
        "color": species.get("color", {}).get("name"),
        "pokedex_numbers": [
            {"pokedex": p["pokedex"]["name"], "entry": p["entry_number"]}
            for p in species.get("pokedex_numbers", [])
        ],
    }


def _english_genus(genera: list[dict[str, Any]]) -> str | None:
    """Categoria da espécie em inglês (ex.: 'Flame Pokémon')."""
    for entry in genera:
        if entry.get("language", {}).get("name") == "en":
            return entry.get("genus")
    return None


def _english_flavor_text(entries: list[dict[str, Any]]) -> dict[str, str] | None:
    for entry in entries:
        if entry.get("language", {}).get("name") == "en":
            return {
                "text": entry.get("flavor_text", "").replace("\n", " ").replace("\f", " "),
                "version": entry.get("version", {}).get("name"),
            }
    return None


def _evolution_chain_payload(chain: dict[str, Any]) -> list[dict[str, Any]]:
    """Cadeia evolutiva em formato plano: [{id, name, evolves_from}].

    A PokeAPI devolve uma árvore (chain → evolves_to → ...). Achata-a em
    níveis: os antecessores do Pokémon atual primeiro, depois ele, depois
    os sucessores, a ordem é por nível na árvore.

    Cada nó ganha `evolves_from`: de quem evoluiu e como ({id, name,
    trigger, item, min_level}). Os evolution_details da PokeAPI vivem no
    nó filho; são anexados ao filho como a descrição da sua origem, o
    frontend mostra um texto curto ("Evolves from Charmander, Lv. 16") ao
    lado da cadeia, e nada para Pokémon de primeira forma.
    """

    def _node_id(node: dict[str, Any]) -> int:
        return int(node["species"]["url"].rstrip("/").split("/")[-1])

    def _method(details: dict[str, Any] | None) -> dict[str, Any] | None:
        if not details:
            return None
        trigger = (details.get("trigger") or {}).get("name")
        if not trigger:
            return None
        item = (details.get("item") or {}).get("name")
        return {
            "trigger": trigger,
            "item": item,
            "min_level": details.get("min_level"),
        }

    def _walk(
        node: dict[str, Any],
        depth: int,
        evolves_from: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        out = [
            {
                "id": _node_id(node),
                "name": node["species"]["name"],
                "depth": depth,
                "evolves_from": evolves_from,
            }
        ]
        for child in node.get("evolves_to", []) or []:
            method = _method((child.get("evolution_details") or [{}])[0])
            child_from: dict[str, Any] | None = (
                {
                    "id": _node_id(node),
                    "name": node["species"]["name"],
                    **method,
                }
                if method
                else None
            )
            out.extend(_walk(child, depth + 1, child_from))
        return out

    return _walk(chain.get("chain", {}), 0, None)


def _mega_evolutions(
    client: PokeAPIClientProtocol, base_name: str
) -> list[dict[str, Any]]:
    """Megas de um Pokémon, a partir da lista completa (cacheada).

    As megas não fazem parte da evolution chain da PokeAPI, são entradas
    separadas na lista de Pokémon, com o nome `<base>-mega[-x]` (ex.:
    charizard-mega-x, blastoise-mega). Filtra a lista completa (cacheada
    30 dias) por prefixo e devolve [{id, name}].
    """
    data = client.get_list("pokemon")
    prefix = f"{base_name}-mega"
    out: list[dict[str, Any]] = []
    for entry in data.get("results", []):
        name = entry.get("name", "")
        if not name.startswith(prefix):
            continue
        url = entry.get("url", "")
        try:
            pokemon_id = int(url.rstrip("/").split("/")[-1])
        except (ValueError, AttributeError):
            continue
        out.append({"id": pokemon_id, "name": name})
    return out


def _ability_payloads(
    client: PokeAPIClientProtocol, abilities: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Habilidades com descrição curta (effect_entries EN, cacheado).

    Cada ability tem um URL próprio na PokeAPI (/ability/{id}); o short_effect
    é a explicação que as Pokédex mostram (ex.: blaze → "Strengthens Fire
    moves...").
    """
    out: list[dict[str, Any]] = []
    for a in abilities:
        name = a["ability"]["name"]
        description = None
        url = a["ability"].get("url")
        if url:
            try:
                data = client.fetch(url)
            except PokeAPIError:
                data = {}
            for entry in data.get("effect_entries", []):
                if entry.get("language", {}).get("name") == "en":
                    description = entry.get("short_effect")
                    break
        out.append(
            {
                "name": name,
                "is_hidden": a["is_hidden"],
                "slot": a["slot"],
                "description": description,
            }
        )
    return out


def get_pokemon_detail(client: PokeAPIClientProtocol, identifier: str) -> dict[str, Any]:
    """Payload completo do detalhe, proxy + cálculos locais."""
    pokemon = client.get_resource("pokemon", identifier)
    species_url = pokemon.get("species", {}).get("url")
    if not species_url:
        raise PokeAPIError("Species data missing on PokeAPI.", status=502)
    species = client.fetch(species_url)

    types = [t["type"]["name"] for t in pokemon["types"]]
    relations = build_type_relations(client)
    effectiveness = type_effectiveness(types, relations)

    stats = {s["stat"]["name"]: s["base_stat"] for s in pokemon["stats"]}

    evolution_chain: list[dict[str, Any]] = []
    chain_url = species.get("evolution_chain", {}).get("url")
    if chain_url:
        evolution_chain = _evolution_chain_payload(client.fetch(chain_url))

    ev_yield = {s["stat"]["name"]: s["effort"] for s in pokemon["stats"] if s["effort"] > 0}

    payload = {
        "id": pokemon["id"],
        "name": pokemon["name"],
        "height": pokemon["height"],
        "weight": pokemon["weight"],
        "base_experience": pokemon["base_experience"],
        "ev_yield": ev_yield,
        "evolution_chain": evolution_chain,
        "mega_evolutions": _mega_evolutions(client, pokemon["name"]),
        "sprites": {
            "front_default": pokemon["sprites"]["front_default"],
            "front_shiny": pokemon["sprites"]["front_shiny"],
            "animated": (
                pokemon["sprites"]["versions"]["generation-v"]["black-white"]["animated"][
                    "front_default"
                ]
                if "generation-v" in pokemon["sprites"]["versions"]
                else None
            ),
            "animated_shiny": (
                pokemon["sprites"]["versions"]["generation-v"]["black-white"]["animated"][
                    "front_shiny"
                ]
                if "generation-v" in pokemon["sprites"]["versions"]
                else None
            ),
            "official_artwork": pokemon["sprites"]["other"]["official-artwork"]["front_default"],
        },
        "cry": pokemon["cries"]["latest"] if "cries" in pokemon else None,
        "types": [{"name": t["type"]["name"], "slot": t["slot"]} for t in pokemon["types"]],
        "stats": [
            {
                "name": s["stat"]["name"],
                "base_stat": s["base_stat"],
                "effort": s["effort"],
            }
            for s in pokemon["stats"]
        ],
        "abilities": _ability_payloads(client, pokemon["abilities"]),
        "species": _species_payload(species),
        "type_effectiveness": partition_effectiveness(effectiveness),
        "best_natures": {
            strategy: best_natures(client, stats, strategy) for strategy in STRATEGIES
        },
        "moves": get_latest_moves(client, pokemon),
    }
    return payload
