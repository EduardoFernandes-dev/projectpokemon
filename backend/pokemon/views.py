"""Views da app pokemon, proxy da PokeAPI com cache e erros normalizados.

Regras (ProjectPokemon-Arquitetura §4.2): as views recebem o pedido, chamam um
serviço e devolvem a resposta. Toda a lógica vive em ``services/``.
"""

from __future__ import annotations

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .services.index import PokemonIndex
from .services.machines import get_latest_machines, get_move_detail
from .services.pokeapi import PokeAPIClient, PokeAPIError
from .services.pokedex import get_pokemon_detail

_client = PokeAPIClient()
_index = PokemonIndex(_client)


def _error(message: str, code: int = 502) -> Response:
    return Response({"error": message}, status=code)


def _parse_int(value: str | None, default: int, minimum: int, maximum: int | None = None) -> int:
    try:
        parsed = int(value) if value is not None else default
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid numeric parameter.") from exc
    if parsed < minimum or (maximum is not None and parsed > maximum):
        raise ValueError(
            f"Parameter outside the allowed range ({minimum}"
            f"{f'–{maximum}' if maximum is not None else '+'})."
        )
    return parsed


def _parse_type_filters(request) -> list[str] | None:
    """Lê os filtros de tipo, aceita repetido (?type=a&type=b) ou vírgula.

    Devolve None quando não há filtros; lista vazia nunca é devolvida.
    """
    raw = request.GET.getlist("type")
    names: list[str] = []
    for value in raw:
        names.extend(part.strip().lower() for part in value.split(",") if part.strip())
    return names or None


@api_view(["GET"])
def search_pokemon(request):
    """GET /api/pokemon/search/?q=<nome>&type=&generation=, pesquisa com filtros.

    A pesquisa sobre a lista completa cacheada aceita os mesmos filtros da
    listagem (tipo e/ou geração), aplicam-se aos resultados encontrados.
    """
    query = (request.GET.get("q") or "").strip().lower()
    if not query:
        return _error("Parameter 'q' is required.", 400)
    if len(query) > 50:
        return _error("Search too long (max 50 characters).", 400)

    type_names = _parse_type_filters(request)
    generation = (request.GET.get("generation") or "").strip().lower() or None

    try:
        results = _index.search(query, type_names=type_names, generation=generation)
    except PokeAPIError as exc:
        return _error(str(exc), exc.status or 502)

    return Response({"query": query, "count": len(results), "results": results})


@api_view(["GET"])
def list_pokemon(request):
    """GET /api/pokemon/?limit=&offset=&type=&generation=, lista paginada e filtrada."""
    try:
        limit = _parse_int(request.GET.get("limit"), default=20, minimum=1, maximum=100)
        offset = _parse_int(request.GET.get("offset"), default=0, minimum=0)
    except ValueError as exc:
        return _error(str(exc), 400)

    type_names = _parse_type_filters(request)
    generation = (request.GET.get("generation") or "").strip().lower() or None

    try:
        results, total = _index.list_pokemon(
            limit=limit, offset=offset, type_names=type_names, generation=generation
        )
    except PokeAPIError as exc:
        return _error(str(exc), exc.status or 502)

    return Response({"count": total, "results": results})


@api_view(["GET"])
def pokemon_detail(request, identifier):
    """GET /api/pokemon/<id|nome>/, detalhe completo com cálculos locais."""
    # Validação anti-SSRF ao nível da view (defesa em profundidade, Segurança §2).
    try:
        PokeAPIClient.validate_identifier(identifier)
    except PokeAPIError as exc:
        return _error(str(exc), exc.status or 502)

    try:
        data = get_pokemon_detail(_client, identifier)
    except PokeAPIError as exc:
        return _error(str(exc), exc.status or 502)
    return Response(data)


@api_view(["GET"])
def type_list(request):
    """GET /api/types/, lista de tipos (cacheada)."""
    try:
        data = _client.get_list("type")
    except PokeAPIError as exc:
        return _error(str(exc), exc.status or 502)
    return Response({"count": data["count"], "results": data["results"]})


@api_view(["GET"])
def generation_list(request):
    """GET /api/generations/, lista de gerações (cacheada)."""
    try:
        data = _client.get_list("generation")
    except PokeAPIError as exc:
        return _error(str(exc), exc.status or 502)
    return Response({"count": data["count"], "results": data["results"]})


@api_view(["GET"])
def tm_list(request):
    """GET /api/tms/, máquinas (TMs) do jogo mais recente."""
    try:
        machines = get_latest_machines(_client)
    except PokeAPIError as exc:
        return _error(str(exc), exc.status or 502)
    return Response({"count": len(machines), "results": machines})


@api_view(["GET"])
def move_detail(request, identifier):
    """GET /api/moves/<id|nome>/, detalhe de um move (stats + descrições)."""
    try:
        PokeAPIClient.validate_identifier(identifier)
    except PokeAPIError as exc:
        return _error(str(exc), exc.status or 502)
    try:
        data = get_move_detail(_client, identifier)
    except PokeAPIError as exc:
        return _error(str(exc), exc.status or 502)
    return Response(data)
