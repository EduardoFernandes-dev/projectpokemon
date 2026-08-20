"""Testes do PokemonIndex, construção do sumário, pesquisa e filtros.

Usa um PokeAPIClient fake: o índice deve funcionar apenas com os métodos
``get_list``/``get_resource`` (sem rede, sem formatação interna da PokeAPI).
"""

import pytest

from pokemon.services.index import PokemonIndex, slugify
from pokemon.services.pokeapi import PokeAPIError

POKEMON_LIST = [
    {"name": "bulbasaur", "url": "https://pokeapi.co/api/v2/pokemon/1/"},
    {"name": "charmander", "url": "https://pokeapi.co/api/v2/pokemon/4/"},
    {"name": "charizard", "url": "https://pokeapi.co/api/v2/pokemon/6/"},
    {"name": "pikachu", "url": "https://pokeapi.co/api/v2/pokemon/25/"},
    {"name": "mr-mime", "url": "https://pokeapi.co/api/v2/pokemon/122/"},
]

TYPES_DATA = {
    1: {"name": "electric", "pokemon": [{"pokemon": {"name": "pikachu"}}]},
    2: {
        "name": "fire",
        "pokemon": [{"pokemon": {"name": "charmander"}}, {"pokemon": {"name": "charizard"}}],
    },
    3: {"name": "grass", "pokemon": [{"pokemon": {"name": "bulbasaur"}}]},
    4: {"name": "poison", "pokemon": [{"pokemon": {"name": "bulbasaur"}}]},
    5: {"name": "psychic", "pokemon": [{"pokemon": {"name": "mew"}}]},
}


class FakePokeClient:
    """Implementa só o que o PokemonIndex usa, registando as chamadas."""

    def __init__(self, pokemon_list, types_data, generations, generation_species):
        self.pokemon_list = pokemon_list
        self.types_data = types_data
        self.generations = generations
        self.generation_species = generation_species
        self.calls = []

    def get_list(self, resource, limit=100000, offset=0):
        self.calls.append(("list", resource))
        if resource == "pokemon":
            return {"count": len(self.pokemon_list), "results": self.pokemon_list}
        if resource == "type":
            return {"count": 18, "results": [{"name": t["name"]} for t in self.types_data.values()]}
        if resource == "generation":
            return {"count": len(self.generations), "results": self.generations}
        raise AssertionError(f"get_list inesperado: {resource}")

    def get_resource(self, resource, identifier, ttl=None):
        self.calls.append(("resource", resource, identifier))
        if resource == "type":
            i = int(identifier)
            return self.types_data.get(i, {"name": f"type-{i}", "pokemon": []})
        if resource == "generation":
            return self.generation_species.get(int(identifier), {"pokemon_species": []})
        raise AssertionError(f"get_resource inesperado: {resource}")

    def fetch(self, url, ttl=None):
        raise AssertionError("fetch não deveria ser usado pelo índice")


@pytest.fixture
def index():
    generations = [{"name": "generation-i", "url": "https://pokeapi.co/api/v2/generation/1/"}]
    species = {1: {"pokemon_species": [{"name": "pikachu"}, {"name": "mr. mime"}]}}
    client = FakePokeClient(POKEMON_LIST, TYPES_DATA, generations, species)
    return PokemonIndex(client), client


class TestSlugify:
    def test_species_name_matches_pokemon_name(self):
        assert slugify("mr. mime") == "mr-mime"
        assert slugify("Type: Null") == "type-null"
        assert slugify("pikachu") == "pikachu"


class TestSummary:
    def test_builds_enriched_summary_sorted_by_id(self, index):
        pokemon_index, _ = index
        summary = pokemon_index.summary()
        assert [p["id"] for p in summary] == [1, 4, 6, 25, 122]
        assert summary[2]["name"] == "charizard"
        assert summary[2]["types"] == ["fire"]
        assert summary[3]["sprite"].endswith("/25.png")
        assert summary[0]["types"] == ["grass", "poison"]

    def test_summary_is_cached(self, index):
        pokemon_index, client = index
        pokemon_index.summary()
        pokemon_index.summary()
        # 18 tipos + 1 lista, apenas uma passagem à PokeAPI fake
        assert len([c for c in client.calls if c[0] == "resource"]) == 18
        assert len([c for c in client.calls if c[0] == "list"]) == 1

    def test_summary_cache_cleared_between_tests(self, index):
        # o conftest limpa o cache; reconstruir volta a chamar a fonte
        pokemon_index, client = index
        pokemon_index.summary()
        assert len([c for c in client.calls if c[0] == "resource"]) == 18


class TestSearch:
    def test_finds_substring_case_insensitive(self, index):
        pokemon_index, _ = index
        assert [p["name"] for p in pokemon_index.search("char")] == ["charmander", "charizard"]

    def test_no_matches(self, index):
        pokemon_index, _ = index
        assert pokemon_index.search("xyz") == []


class TestList:
    def test_pagination(self, index):
        pokemon_index, _ = index
        page, total = pokemon_index.list_pokemon(limit=2, offset=1)
        assert total == 5
        assert [p["name"] for p in page] == ["charmander", "charizard"]

    def test_type_filter(self, index):
        pokemon_index, _ = index
        page, total = pokemon_index.list_pokemon(limit=100, offset=0, type_names=["fire"])
        assert total == 2
        assert [p["name"] for p in page] == ["charmander", "charizard"]

    def test_two_type_filter_order_insensitive(self, index):
        pokemon_index, _ = index
        # bulbasaur é grass+poison, pedir os dois em qualquer ordem devolve-o
        for types in (["grass", "poison"], ["poison", "grass"]):
            page, total = pokemon_index.list_pokemon(limit=100, offset=0, type_names=types)
            assert total == 1
            assert page[0]["name"] == "bulbasaur"
        # fire+grass não existe em nenhum Pokémon do índice
        _, total = pokemon_index.list_pokemon(limit=100, offset=0, type_names=["fire", "grass"])
        assert total == 0

    def test_invalid_type_raises_400(self, index):
        pokemon_index, _ = index
        with pytest.raises(PokeAPIError) as excinfo:
            pokemon_index.list_pokemon(limit=100, offset=0, type_names=["shadow"])
        assert excinfo.value.status == 400

    def test_generation_filter_by_name(self, index):
        pokemon_index, _ = index
        page, total = pokemon_index.list_pokemon(limit=100, offset=0, generation="generation-i")
        assert total == 2
        assert [p["name"] for p in page] == ["pikachu", "mr-mime"]  # 'mr. mime' → 'mr-mime'

    def test_generation_filter_by_number(self, index):
        pokemon_index, _ = index
        _, total = pokemon_index.list_pokemon(limit=100, offset=0, generation="1")
        assert total == 2

    def test_invalid_generation_raises_400(self, index):
        pokemon_index, _ = index
        with pytest.raises(PokeAPIError) as excinfo:
            pokemon_index.list_pokemon(limit=100, offset=0, generation="generation-xx")
        assert excinfo.value.status == 400
