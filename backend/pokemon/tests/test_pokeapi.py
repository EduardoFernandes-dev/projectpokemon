"""Testes do PokeAPIClient, validação anti-SSRF, cache e erros normalizados."""

import pytest
import requests
import responses
from django.conf import settings
from django.core.cache import cache

from pokemon.services.pokeapi import PokeAPIClient, PokeAPIError

BASE = settings.POKEAPI_BASE_URL


@pytest.fixture
def client():
    return PokeAPIClient()


class TestIdentifierValidation:
    def test_accepts_integer(self, client):
        assert client.validate_identifier("25") == "25"

    def test_accepts_slug(self, client):
        assert client.validate_identifier("Pikachu") == "pikachu"

    @pytest.mark.parametrize(
        "bad",
        [
            "https://evil.example/x",
            "../etc/passwd",
            "a" * 65,
            "pika chu",
            "6;drop",
            "//pokeapi.co/x",
        ],
    )
    def test_rejects_unsafe_identifiers(self, client, bad):
        with pytest.raises(PokeAPIError) as excinfo:
            client.validate_identifier(bad)
        assert excinfo.value.status == 400

    def test_rejects_unsafe_url(self, client):
        with pytest.raises(PokeAPIError):
            client.fetch("https://evil.example/api/v2/pokemon/6")


class TestFetch:
    @responses.activate
    def test_fetch_hits_api_and_caches(self, client):
        url = f"{BASE}/pokemon/6"
        responses.get(url, json={"id": 6, "name": "charizard"}, status=200)
        assert client.fetch(url) == {"id": 6, "name": "charizard"}
        # segunda chamada → cache, sem novo pedido
        client.fetch(url)
        assert len(responses.calls) == 1

    @responses.activate
    def test_cache_respects_ttl(self, client):
        url = f"{BASE}/pokemon/25"
        responses.get(url, json={"id": 25}, status=200)
        client.fetch(url, ttl=0)  # TTL 0 → não guarda
        client.fetch(url, ttl=0)
        assert len(responses.calls) == 2

    @responses.activate
    def test_404_raises_with_status(self, client):
        responses.get(f"{BASE}/pokemon/99999", json={"detail": "Not found"}, status=404)
        with pytest.raises(PokeAPIError) as excinfo:
            client.get_resource("pokemon", "99999")
        assert excinfo.value.status == 404

    @responses.activate
    def test_server_error_becomes_502(self, client):
        responses.get(f"{BASE}/pokemon/6", status=500)
        with pytest.raises(PokeAPIError) as excinfo:
            client.get_resource("pokemon", "6")
        assert excinfo.value.status == 502

    def test_error_response_never_cached(self, client):
        # Falha de rede → PokeAPIError; a chave do cache não pode ficar preenchida.
        with responses.RequestsMock() as rsps:
            rsps.get(f"{BASE}/pokemon/6", body=requests.ConnectionError("boom"))
            with pytest.raises(PokeAPIError):
                client.fetch(f"{BASE}/pokemon/6")
        assert cache.get(f"pokeapi:{BASE}/pokemon/6") is None
