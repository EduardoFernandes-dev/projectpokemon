"""Configuração da app pokemon, pré-aquecimento da cache no arranque."""

from __future__ import annotations

import threading

from django.apps import AppConfig
from django.conf import settings


class PokemonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pokemon"

    def ready(self) -> None:
        """Pré-aquece a cache dos agregados partilhados (types + natures).

        Os 18 tipos e as 25 naturezas são os mesmos para todos os Pokémon, sem este warm-up, o primeiro detalhe depois de um reinício pagava
        ~43 fetches à PokeAPI em série. Corre em background para não atrasar
        o arranque do servidor; falhas são silenciosas (a cache-first normal
        trata do resto).
        """
        # Não dispara pedidos de rede durante os testes (pytest-django
        # também chama ready()).
        if getattr(settings, "TESTING", False):
            return
        try:
            threading.Thread(target=self._warm_cache, daemon=True).start()
        except Exception:  # pragma: no cover, nunca deve impedir o arranque
            pass

    @staticmethod
    def _warm_cache() -> None:  # pragma: no cover, smoke test cobre o fluxo
        try:
            from .services.pokeapi import PokeAPIClient
            from .services.typechart import build_type_relations

            client = PokeAPIClient()
            # 1) Types (18 fetches, agregado cacheado)
            build_type_relations(client)
            # 2) Natures (25 fetches, agregado cacheado)
            from .services.natures import get_nature_map

            get_nature_map(client)
        except Exception:
            # Sem rede ou PokeAPI em baixo → a cache-first normal re-tenta
            # por pedido; o warm-up é apenas uma otimização.
            pass
