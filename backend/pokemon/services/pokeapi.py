"""PokeAPIClient, única porta de saída para a PokeAPI.

Responsabilidades (ProjectPokemon-Seguranca §2 e ProjectPokemon-Dados §4):
- Construir URLs apenas a partir de ``POKEAPI_BASE_URL`` (anti-SSRF);
- Validar identifiers (inteiro ou slug) antes de os usar no caminho;
- Cache-first: respostas guardadas no Django cache com TTLs por tipo de recurso;
- Erros normalizados via ``PokeAPIError`` (status 404/502/400).
"""

from __future__ import annotations

import logging
import re
from typing import Any, Protocol

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

_ID_RE = re.compile(r"^[0-9]{1,5}$")
_SLUG_RE = re.compile(r"^[a-z0-9-]{1,64}$")


class PokeAPIClientProtocol(Protocol):
    """Interface mínima usada pelos serviços, permite fakes nos testes."""

    def fetch(self, url: str, ttl: int | None = None) -> dict[str, Any]: ...

    def get_resource(
        self, resource: str, identifier: str, ttl: int | None = None
    ) -> dict[str, Any]: ...

    def get_list(self, resource: str, limit: int = 100000, offset: int = 0) -> dict[str, Any]: ...


class PokeAPIError(Exception):
    """Erro ao contactar a PokeAPI, com status HTTP sugerido para a resposta."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class PokeAPIClient:
    """Client síncrono (requests) com cache-first para a PokeAPI."""

    BASE_URL = settings.POKEAPI_BASE_URL
    TIMEOUT = 10

    def __init__(self, session: requests.Session | None = None) -> None:
        # Sessão partilhada → reutilização de conexões (keep-alive).
        self._session = session or requests.Session()

    # ── Validação (anti-SSRF) ───────────────────────────────────────────────
    @classmethod
    def validate_identifier(cls, identifier: str) -> str:
        ident = str(identifier).strip().lower()
        if not (_ID_RE.match(ident) or _SLUG_RE.match(ident)):
            raise PokeAPIError("Invalid identifier.", status=400)
        return ident

    def _assert_safe_url(self, url: str) -> None:
        if not url.startswith(self.BASE_URL + "/"):
            raise PokeAPIError("External URL not allowed.", status=400)

    # ── Fetch com cache ─────────────────────────────────────────────────────
    def fetch(self, url: str, ttl: int | None = None) -> dict[str, Any]:
        """GET de um recurso com cache. ttl=None → TTL padrão (estático, 7 dias)."""
        self._assert_safe_url(url)
        key = f"pokeapi:{url}"
        cached = cache.get(key)
        if cached is not None:
            return cached

        try:
            resp = self._session.get(url, timeout=self.TIMEOUT)
        except requests.RequestException as exc:
            logger.warning("PokeAPI unreachable: %s", exc)
            raise PokeAPIError("PokeAPI unreachable, try again soon.") from exc

        if resp.status_code == 404:
            raise PokeAPIError("Resource not found on PokeAPI.", status=404)
        if resp.status_code >= 400:
            logger.warning("PokeAPI responded %s for %s", resp.status_code, url)
            raise PokeAPIError(
                f"PokeAPI responded {resp.status_code}, try again soon.",
                status=502,
            )

        data = resp.json()
        timeout = settings.POKEAPI_CACHE_TTL if ttl is None else ttl
        cache.set(key, data, timeout=timeout)
        return data

    def get_resource(
        self, resource: str, identifier: str, ttl: int | None = None
    ) -> dict[str, Any]:
        """GET /{resource}/{identifier} com validação do identifier."""
        ident = self.validate_identifier(identifier)
        return self.fetch(f"{self.BASE_URL}/{resource}/{ident}", ttl=ttl)

    def get_list(self, resource: str, limit: int = 100000, offset: int = 0) -> dict[str, Any]:
        """GET /{resource}?limit=&offset= com cache de longa duração (lista completa)."""
        if not (1 <= int(limit) <= 100000):
            raise PokeAPIError("limit fora do intervalo permitido.", status=400)
        if int(offset) < 0:
            raise PokeAPIError("offset inválido.", status=400)
        url = f"{self.BASE_URL}/{resource}?limit={limit}&offset={offset}"
        return self.fetch(url, ttl=settings.POKEAPI_LIST_CACHE_TTL)
