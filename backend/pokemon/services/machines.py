"""Máquinas (TMs) do jogo mais recente + detalhe de moves.

As TMs não têm endpoint próprio na PokeAPI com filtro por jogo, a lista
`/machine` tem 2372 entradas (todas as gerações) e cada máquina aponta
para um `version_group`. Este módulo varre essa lista (em paralelo, com
cache de longa duração) e guarda apenas as do jogo mais recente
(scarlet-violet, gen 9).

O detalhe de um move (`/move/{id}`) é direto: type, damage_class, power,
accuracy, pp e as descrições (short_effect, effect, flavor_text).
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

from django.conf import settings
from django.core.cache import cache

from .pokeapi import PokeAPIClientProtocol

MACHINES_CACHE_KEY = "pokedex:latest-machines"
_MACHINE_WORKERS = 20


def _machine_summary(
    client: PokeAPIClientProtocol, url: str
) -> tuple[str, str, str, str, int] | None:
    """(version_group, item, move_name, move_url, machine_id), ou None."""
    try:
        data = client.fetch(url)
    except Exception:
        return None
    vg = (data.get("version_group") or {}).get("name")
    item = (data.get("item") or {}).get("name")
    move = data.get("move") or {}
    if not (vg and item and move.get("name")):
        return None
    try:
        machine_id = int(url.rstrip("/").split("/")[-1])
    except (ValueError, AttributeError):
        machine_id = 0
    return vg, item, move["name"], move.get("url", ""), machine_id


def _move_brief(client: PokeAPIClientProtocol, url: str) -> dict[str, Any]:
    """Tipo/classe/power de um move a partir do seu URL (fetch cacheado)."""
    try:
        data = client.fetch(url)
    except Exception:
        return {}
    return {
        "type": (data.get("type") or {}).get("name"),
        "damage_class": (data.get("damage_class") or {}).get("name"),
        "power": data.get("power"),
    }


def get_latest_machines(client: PokeAPIClientProtocol) -> list[dict[str, Any]]:
    """TMs do jogo mais recente (cache 30 dias).

    Cada máquina inclui o resumo do move que ensina (tipo, classe, power)
    para a grelha de TMs no frontend. A varredura das 2372 máquinas e dos
    respetivos moves corre em paralelo; a primeira chamada após um
    reinício é a única lenta (~30s), as seguintes são cache-hit.
    """
    cached = cache.get(MACHINES_CACHE_KEY)
    if cached is not None:
        return cached

    listing = client.get_list("machine")
    urls = [e["url"] for e in listing.get("results", [])]
    with ThreadPoolExecutor(max_workers=_MACHINE_WORKERS) as pool:
        summaries = [
            s for s in pool.map(_machine_summary, [client] * len(urls), urls) if s
        ]

    # jogo principal mais recente = o que tem mais máquinas (a gen atual,
    # scarlet-violet, tem 229; os spin-offs recentes têm 50–130). Em caso
    # de empate, o maior ID de máquina desempata.
    by_game: dict[str, tuple[int, list[tuple[str, str, str]]]] = {}
    for vg, item, move_name, move_url, machine_id in summaries:
        max_id, items = by_game.setdefault(vg, (0, []))
        if machine_id > max_id:
            by_game[vg] = (machine_id, items)
        items.append((item, move_name, move_url))
    latest_game = max(
        by_game,
        key=lambda g: (len(by_game[g][1]), by_game[g][0]),
    )

    game_machines = by_game[latest_game][1]
    move_urls = [url for _, _, url in game_machines]
    with ThreadPoolExecutor(max_workers=_MACHINE_WORKERS) as pool:
        briefs = list(pool.map(lambda u: _move_brief(client, u), move_urls))

    machines: list[dict[str, Any]] = []
    for (item, move_name, move_url), brief in zip(game_machines, briefs):
        try:
            move_id = int(move_url.rstrip("/").split("/")[-1])
        except (ValueError, AttributeError):
            move_id = None
        machines.append(
            {
                "number": item,  # ex.: "tm01"
                "move": move_name,
                "move_id": move_id,
                **brief,
            }
        )

    machines.sort(key=lambda m: m["number"])
    cache.set(MACHINES_CACHE_KEY, machines, timeout=settings.POKEAPI_LIST_CACHE_TTL)
    return machines


def _effect_texts(data: dict[str, Any]) -> tuple[str | None, str | None]:
    """(short_effect, effect) em inglês dos effect_entries do move."""
    short = None
    full = None
    for entry in data.get("effect_entries", []):
        if entry.get("language", {}).get("name") != "en":
            continue
        short = short or entry.get("short_effect")
        full = full or entry.get("effect")
    return short, full


def get_move_detail(client: PokeAPIClientProtocol, identifier: str) -> dict[str, Any]:
    """Detalhe de um move: stats + descrições em inglês (cacheado)."""
    data = client.get_resource("move", identifier)
    flavor = None
    for entry in data.get("flavor_text_entries", []):
        if entry.get("language", {}).get("name") == "en" and entry.get("version_group", {}).get(
            "name"
        ) in ("scarlet-violet", "sword-shield"):
            flavor = entry.get("flavor_text", "").replace("\n", " ").replace("\x0c", " ")
            break
    short_effect, effect = _effect_texts(data)
    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "type": (data.get("type") or {}).get("name"),
        "damage_class": (data.get("damage_class") or {}).get("name"),
        "power": data.get("power"),
        "accuracy": data.get("accuracy"),
        "pp": data.get("pp"),
        "priority": data.get("priority", 0),
        "short_effect": short_effect,
        "effect": effect,
        "flavor_text": flavor,
    }
