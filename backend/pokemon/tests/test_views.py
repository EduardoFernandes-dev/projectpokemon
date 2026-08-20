"""Testes dos endpoints, client e índice fake (sem rede, sem PokeAPI real)."""

import pytest
from django.conf import settings
from rest_framework.test import APIClient

import pokemon.views as views
from pokemon.services.pokeapi import PokeAPIError

BASE = settings.POKEAPI_BASE_URL

# ── Dados canned ────────────────────────────────────────────────────────────

SUMMARY = [
    {"id": 1, "name": "bulbasaur", "types": ["grass", "poison"], "sprite": f"{BASE}/s/1.png"},
    {"id": 4, "name": "charmander", "types": ["fire"], "sprite": f"{BASE}/s/4.png"},
    {"id": 6, "name": "charizard", "types": ["fire", "flying"], "sprite": f"{BASE}/s/6.png"},
    {"id": 25, "name": "pikachu", "types": ["electric"], "sprite": f"{BASE}/s/25.png"},
    {"id": 151, "name": "mew", "types": ["psychic"], "sprite": f"{BASE}/s/151.png"},
]


class FakeIndex:
    """Substituto do PokemonIndex para as views, regista as chamadas."""

    def __init__(self, summary):
        self.summary_data = summary
        self.calls = []

    def search(self, query, type_names=None, generation=None):
        self.calls.append(("search", query, type_names, generation))
        pokemon = [p for p in self.summary_data if query in p["name"]]
        if type_names:
            required = set(type_names)
            pokemon = [p for p in pokemon if required.issubset(p["types"])]
        return pokemon

    def list_pokemon(self, limit, offset, type_names=None, generation=None):
        self.calls.append(("list", limit, offset, type_names, generation))
        pokemon = self.summary_data
        if type_names:
            required = set(type_names)
            pokemon = [p for p in pokemon if required.issubset(p["types"])]
        return pokemon[offset : offset + limit], len(pokemon)


# Relações de tipos (subconjunto real) indexadas pelo id PokeAPI.
_TYPE_RELATIONS = {
    3: (
        "flying",
        {
            "double_damage_from": ["electric", "rock", "ice"],
            "half_damage_from": ["grass", "fighting", "bug"],
            "no_damage_from": ["ground"],
        },
    ),
    5: (
        "ground",
        {
            "double_damage_from": ["water", "grass", "ice"],
            "half_damage_from": ["poison", "rock"],
            "no_damage_from": ["electric"],
        },
    ),
    6: (
        "rock",
        {
            "double_damage_from": ["water", "grass", "fighting", "ground", "steel"],
            "half_damage_from": ["normal", "fire", "poison", "flying"],
            "no_damage_from": [],
        },
    ),
    10: (
        "fire",
        {
            "double_damage_from": ["water", "ground", "rock"],
            "half_damage_from": ["grass", "bug", "fire", "ice", "steel", "fairy"],
            "no_damage_from": [],
        },
    ),
    11: (
        "water",
        {
            "double_damage_from": ["electric", "grass"],
            "half_damage_from": ["fire", "water", "ice", "steel"],
            "no_damage_from": [],
        },
    ),
    12: (
        "grass",
        {
            "double_damage_from": ["fire", "ice", "poison", "flying", "bug"],
            "half_damage_from": ["water", "grass", "electric", "ground"],
            "no_damage_from": [],
        },
    ),
    13: (
        "electric",
        {
            "double_damage_from": ["ground"],
            "half_damage_from": ["flying", "electric", "steel"],
            "no_damage_from": [],
        },
    ),
}


class FakeClient:
    """Substituto do PokeAPIClient com dados canned do Charizard (#6)."""

    def __init__(self):
        self.calls = []
        self.not_found = set()

    def _type_data(self, i):
        if i in _TYPE_RELATIONS:
            name, relations = _TYPE_RELATIONS[i]
            return {"name": name, "damage_relations": relations}
        return {"name": f"type-{i}", "damage_relations": {}}

    def get_resource(self, resource, identifier, ttl=None):
        self.calls.append((resource, identifier))
        if resource == "pokemon":
            if identifier in self.not_found:
                raise PokeAPIError("Recurso não encontrado na PokeAPI.", status=404)
            return POKEMON_6
        if resource == "type":
            return self._type_data(int(identifier))
        if resource == "nature":
            return NATURES.get(identifier, {"increased_stat": None, "decreased_stat": None})
        if resource == "move":
            if identifier in self.not_found:
                raise PokeAPIError("Recurso não encontrado na PokeAPI.", status=404)
            return {
                "id": 36,
                "name": "take-down",
                "type": {"name": "normal"},
                "damage_class": {"name": "physical"},
                "power": 90,
                "accuracy": 85,
                "pp": 20,
                "priority": 0,
                "effect_entries": [
                    {
                        "language": {"name": "en"},
                        "short_effect": "Inflicts recoil damage.",
                        "effect": "Inflicts regular damage.  User takes 1/4 the damage it inflicts in recoil.",
                    }
                ],
                "flavor_text_entries": [
                    {
                        "language": {"name": "en"},
                        "version_group": {"name": "scarlet-violet"},
                        "flavor_text": "A reckless, full-body charge attack...",
                    }
                ],
            }
        raise AssertionError(f"get_resource inesperado: {resource}")

    def get_list(self, resource, limit=100000, offset=0):
        if resource == "pokemon":
            return {
                "count": 3,
                "results": [
                    {"name": "charmander", "url": f"{BASE}/pokemon/4"},
                    {"name": "charmeleon", "url": f"{BASE}/pokemon/5"},
                    {"name": "charizard", "url": f"{BASE}/pokemon/6"},
                    {"name": "charizard-mega-x", "url": f"{BASE}/pokemon/10034"},
                    {"name": "charizard-mega-y", "url": f"{BASE}/pokemon/10035"},
                ],
            }
        if resource == "machine":
            return {
                "count": 2,
                "results": [
                    {"url": f"{BASE}/machine/100"},
                    {"url": f"{BASE}/machine/101"},
                ],
            }
        raise AssertionError(f"get_list inesperado: {resource}")

    def fetch(self, url, ttl=None):
        self.calls.append(("fetch", url))
        if url == f"{BASE}/pokemon-species/6":
            return SPECIES_6
        if url == f"{BASE}/evolution-chain/2":
            return EVOLUTION_CHAIN_6
        if url == f"{BASE}/machine/100":
            return {
                "version_group": {"name": "red-blue"},
                "item": {"name": "tm01"},
                "move": {"name": "mega-punch", "url": f"{BASE}/move/5"},
            }
        if url == f"{BASE}/machine/101":
            return {
                "version_group": {"name": "scarlet-violet"},
                "item": {"name": "tm01"},
                "move": {"name": "take-down", "url": f"{BASE}/move/36"},
            }
        if url == f"{BASE}/move/36":
            return {
                "id": 36,
                "name": "take-down",
                "type": {"name": "normal"},
                "damage_class": {"name": "physical"},
                "power": 90,
                "accuracy": 85,
                "pp": 20,
                "priority": 0,
                "effect_entries": [
                    {
                        "language": {"name": "en"},
                        "short_effect": "Inflicts recoil damage.",
                        "effect": "Inflicts regular damage.  User takes 1/4 the damage it inflicts in recoil.",
                    }
                ],
                "flavor_text_entries": [
                    {
                        "language": {"name": "en"},
                        "version_group": {"name": "scarlet-violet"},
                        "flavor_text": "A reckless, full-body charge attack...",
                    }
                ],
            }
        if url == f"{BASE}/ability/66":
            return {
                "name": "blaze",
                "effect_entries": [
                    {
                        "language": {"name": "en"},
                        "short_effect": (
                            "Strengthens Fire moves to inflict 1.5× damage "
                            "at 1/3 max HP or less."
                        ),
                    }
                ],
            }
        if url in (f"{BASE}/move/53", f"{BASE}/move/126", f"{BASE}/move/52"):
            move_id = int(url.rstrip("/").split("/")[-1])
            return {
                "id": move_id,
                "type": {"name": "fire"},
                "damage_class": {"name": "special"},
                "power": 90,
            }
        raise AssertionError(f"fetch inesperado: {url}")


POKEMON_6 = {
    "id": 6,
    "name": "charizard",
    "height": 17,
    "weight": 905,
    "base_experience": 240,
    "sprites": {
        "front_default": f"{BASE}/sprites/6.png",
        "front_shiny": f"{BASE}/sprites/6-shiny.png",
        "versions": {
            "generation-v": {
                "black-white": {
                    "animated": {
                        "front_default": f"{BASE}/sprites/6.gif",
                        "front_shiny": f"{BASE}/sprites/6-shiny.gif",
                    }
                }
            }
        },
        "other": {"official-artwork": {"front_default": f"{BASE}/artwork/6.png"}},
    },
    "cries": {"latest": f"{BASE}/cries/6.ogg"},
    "types": [
        {"type": {"name": "fire"}, "slot": 1},
        {"type": {"name": "flying"}, "slot": 2},
    ],
    "stats": [
        {"stat": {"name": "hp"}, "base_stat": 78, "effort": 0},
        {"stat": {"name": "attack"}, "base_stat": 84, "effort": 0},
        {"stat": {"name": "defense"}, "base_stat": 78, "effort": 0},
        {"stat": {"name": "special-attack"}, "base_stat": 109, "effort": 3},
        {"stat": {"name": "special-defense"}, "base_stat": 85, "effort": 0},
        {"stat": {"name": "speed"}, "base_stat": 100, "effort": 0},
    ],
    "abilities": [
        {
            "ability": {"name": "blaze", "url": f"{BASE}/ability/66"},
            "is_hidden": False,
            "slot": 1,
        }
    ],
    "moves": [
        {
            "move": {"name": "flamethrower", "url": f"{BASE}/move/53"},
            "version_group_details": [
                {
                    "level_learned_at": 34,
                    "move_learn_method": {"name": "level-up"},
                    "version_group": {"url": f"{BASE}/version-group/30/"},
                },
                {
                    "level_learned_at": 0,
                    "move_learn_method": {"name": "machine"},
                    "version_group": {"url": f"{BASE}/version-group/2/"},
                },
            ],
        },
        {
            "move": {"name": "fire-blast", "url": f"{BASE}/move/126"},
            "version_group_details": [
                {
                    "level_learned_at": 0,
                    "move_learn_method": {"name": "machine"},
                    "version_group": {"url": f"{BASE}/version-group/30/"},
                }
            ],
        },
        {
            "move": {"name": "ember", "url": f"{BASE}/move/52"},
            "version_group_details": [
                {
                    "level_learned_at": 1,
                    "move_learn_method": {"name": "level-up"},
                    "version_group": {"url": f"{BASE}/version-group/30/"},
                }
            ],
        },
    ],
    "species": {"url": f"{BASE}/pokemon-species/6"},
}

SPECIES_6 = {
    "name": "charizard",
    "generation": {"name": "generation-i"},
    "habitat": {"name": "mountain"},
    "is_legendary": False,
    "is_mythical": False,
    "genera": [{"language": {"name": "en"}, "genus": "Flame Pokémon"}],
    "flavor_text_entries": [
        {
            "language": {"name": "en"},
            "flavor_text": "It spits fire that is hot enough to melt boulders.",
            "version": {"name": "red"},
        }
    ],
    "egg_groups": [{"name": "monster"}, {"name": "dragon"}],
    "hatch_counter": 20,
    "capture_rate": 45,
    "base_happiness": 50,
    "growth_rate": {"name": "medium-slow"},
    "gender_rate": 1,
    "color": {"name": "red"},
    "pokedex_numbers": [
        {"pokedex": {"name": "national"}, "entry_number": 6},
        {"pokedex": {"name": "kanto"}, "entry_number": 6},
    ],
    "evolution_chain": {"url": f"{BASE}/evolution-chain/2"},
}

EVOLUTION_CHAIN_6 = {
    "chain": {
        "species": {"name": "charmander", "url": f"{BASE}/pokemon-species/4"},
        "evolution_details": [],
        "evolves_to": [
            {
                "species": {"name": "charmeleon", "url": f"{BASE}/pokemon-species/5"},
                "evolution_details": [
                    {"min_level": 16, "trigger": {"name": "level-up"}}
                ],
                "evolves_to": [
                    {
                        "species": {"name": "charizard", "url": f"{BASE}/pokemon-species/6"},
                        "evolution_details": [
                            {
                                "min_level": None,
                                "trigger": {"name": "use-item"},
                                "item": {"name": "fire-stone"},
                            }
                        ],
                        "evolves_to": [],
                    }
                ],
            }
        ],
    }
}

NATURES = {
    "1": {
        "name": "adamant",
        "increased_stat": {"name": "attack"},
        "decreased_stat": {"name": "special-attack"},
    },
    "2": {
        "name": "jolly",
        "increased_stat": {"name": "speed"},
        "decreased_stat": {"name": "special-attack"},
    },
    "7": {
        "name": "lonely",
        "increased_stat": {"name": "attack"},
        "decreased_stat": {"name": "defense"},
    },
    "8": {
        "name": "hasty",
        "increased_stat": {"name": "speed"},
        "decreased_stat": {"name": "defense"},
    },
    "9": {"name": "hardy", "increased_stat": None, "decreased_stat": None},
}


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def fake_index(monkeypatch):
    index = FakeIndex(SUMMARY)
    monkeypatch.setattr(views, "_index", index)
    return index


@pytest.fixture
def fake_client(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(views, "_client", client)
    return client


# ── Search ──────────────────────────────────────────────────────────────────


class TestSearch:
    def test_search_finds_substring(self, api_client, fake_index):
        resp = api_client.get("/api/pokemon/search/", {"q": "izard"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 1
        assert body["results"][0]["name"] == "charizard"

    def test_search_filters_by_type(self, api_client, fake_index):
        # "char" → charmander (fire) e charizard (fire/flying); filtro fire mantém ambos,
        # filtro electric devolve vazio
        resp = api_client.get(
            "/api/pokemon/search/", {"q": "char", "type": "fire"}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 2
        assert {r["name"] for r in body["results"]} == {"charmander", "charizard"}

        resp = api_client.get(
            "/api/pokemon/search/", {"q": "char", "type": "electric"}
        )
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    def test_search_filters_by_two_types_order_insensitive(self, api_client, fake_index):
        # bulbasaur é grass+poison; pedir ambos (em qualquer ordem) devolve-o;
        # pedir fire+grass não devolve nada (nenhum Pokémon tem os dois)
        for params in (
            {"q": "bulb", "type": ["grass", "poison"]},
            {"q": "bulb", "type": ["poison", "grass"]},
        ):
            resp = api_client.get("/api/pokemon/search/", params)
            assert resp.status_code == 200
            body = resp.json()
            assert body["count"] == 1
            assert body["results"][0]["name"] == "bulbasaur"

        resp = api_client.get("/api/pokemon/search/", {"q": "bulb", "type": ["fire", "grass"]})
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    def test_search_passes_generation_filter(self, api_client, fake_index):
        resp = api_client.get(
            "/api/pokemon/search/", {"q": "char", "generation": "generation-i"}
        )
        assert resp.status_code == 200
        assert ("search", "char", None, "generation-i") in fake_index.calls

    def test_search_empty_query_is_400(self, api_client, fake_index):
        assert api_client.get("/api/pokemon/search/").status_code == 400
        assert api_client.get("/api/pokemon/search/", {"q": "  "}).status_code == 400

    def test_search_too_long_is_400(self, api_client, fake_index):
        resp = api_client.get("/api/pokemon/search/", {"q": "a" * 51})
        assert resp.status_code == 400
        assert "error" in resp.json()

    def test_search_normalizes_case(self, api_client, fake_index):
        resp = api_client.get("/api/pokemon/search/", {"q": "PikA"})
        assert resp.status_code == 200
        assert resp.json()["results"][0]["name"] == "pikachu"


# ── List ────────────────────────────────────────────────────────────────────


class TestList:
    def test_list_passes_pagination(self, api_client, fake_index):
        resp = api_client.get("/api/pokemon/", {"limit": 2, "offset": 2})
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 5
        assert [p["name"] for p in body["results"]] == ["charizard", "pikachu"]

    def test_list_invalid_limit_is_400(self, api_client, fake_index):
        assert api_client.get("/api/pokemon/", {"limit": 0}).status_code == 400
        assert api_client.get("/api/pokemon/", {"limit": 101}).status_code == 400
        assert api_client.get("/api/pokemon/", {"limit": "abc"}).status_code == 400

    def test_list_forwards_type_filter(self, api_client, fake_index):
        resp = api_client.get("/api/pokemon/", {"type": "fire"})
        assert resp.status_code == 200
        assert fake_index.calls[-1] == ("list", 20, 0, ["fire"], None)
        assert [p["name"] for p in resp.json()["results"]] == ["charmander", "charizard"]

    def test_list_forwards_two_type_filters(self, api_client, fake_index):
        resp = api_client.get("/api/pokemon/", {"type": ["grass", "poison"]})
        assert resp.status_code == 200
        assert fake_index.calls[-1] == ("list", 20, 0, ["grass", "poison"], None)
        assert [p["name"] for p in resp.json()["results"]] == ["bulbasaur"]

    def test_list_forwards_generation_filter(self, api_client, fake_index):
        api_client.get("/api/pokemon/", {"generation": "generation-i"})
        assert fake_index.calls[-1] == ("list", 20, 0, None, "generation-i")


# ── Detail ──────────────────────────────────────────────────────────────────


class TestDetail:
    def test_detail_returns_enriched_payload(self, api_client, fake_client):
        resp = api_client.get("/api/pokemon/6/")
        assert resp.status_code == 200
        data = resp.json()

        assert data["name"] == "charizard"
        assert data["cry"].endswith("/cries/6.ogg")
        assert data["sprites"]["animated"].endswith("/sprites/6.gif")
        assert data["sprites"]["animated_shiny"].endswith("/sprites/6-shiny.gif")

        # espécie: categoria, descrição com jogo de origem
        assert data["species"]["genus"] == "Flame Pokémon"
        assert data["species"]["flavor_text_version"] == "red"
        assert data["species"]["egg_groups"] == ["monster", "dragon"]
        assert data["species"]["hatch_counter"] == 20
        assert data["species"]["capture_rate"] == 45
        assert data["species"]["gender_rate"] == 1
        assert data["species"]["growth_rate"] == "medium-slow"
        assert data["species"]["pokedex_numbers"][0] == {"pokedex": "national", "entry": 6}

        # EV yield (só stats com effort > 0)
        assert data["ev_yield"] == {"special-attack": 3}

        # megas do charizard (formas separadas na lista de Pokémon)
        assert data["mega_evolutions"] == [
            {"id": 10034, "name": "charizard-mega-x"},
            {"id": 10035, "name": "charizard-mega-y"},
        ]

        # cadeia evolutiva: charmander (primeira forma, sem origem) →
        # charmeleon (Lv 16) → charizard (fire stone)
        assert data["evolution_chain"] == [
            {
                "id": 4,
                "name": "charmander",
                "depth": 0,
                "evolves_from": None,
            },
            {
                "id": 5,
                "name": "charmeleon",
                "depth": 1,
                "evolves_from": {
                    "id": 4,
                    "name": "charmander",
                    "trigger": "level-up",
                    "item": None,
                    "min_level": 16,
                },
            },
            {
                "id": 6,
                "name": "charizard",
                "depth": 2,
                "evolves_from": {
                    "id": 5,
                    "name": "charmeleon",
                    "trigger": "use-item",
                    "item": "fire-stone",
                    "min_level": None,
                },
            },
        ]

        # fraquezas/resistências (rock ×4, ground imune)
        weaknesses = {w["type"]: w["multiplier"] for w in data["type_effectiveness"]["weaknesses"]}
        assert weaknesses["rock"] == 4.0
        assert weaknesses["water"] == 2.0
        immunities = {i["type"] for i in data["type_effectiveness"]["immunities"]}
        assert "ground" in immunities

        # moves: level-up ordenado + TMs do jogo mais recente (version-group 30),
        # com tipo, classe de dano e power
        assert data["moves"]["level_up"] == [
            {
                "id": 52,
                "level": 1,
                "name": "ember",
                "type": "fire",
                "damage_class": "special",
                "power": 90,
            },
            {
                "id": 53,
                "level": 34,
                "name": "flamethrower",
                "type": "fire",
                "damage_class": "special",
                "power": 90,
            },
        ]
        assert data["moves"]["machines"] == [
            {
                "id": 126,
                "name": "fire-blast",
                "type": "fire",
                "damage_class": "special",
                "power": 90,
            }
        ]

        # naturezas: físico → (attack, defense) = lonely (defense é o stat mais fraco)
        physical = data["best_natures"]["physical"]
        assert physical[0]["nature"] == "lonely"
        assert physical[0]["boost"] == "attack"

        # stats e habilidades mantidos + descrição da habilidade
        assert len(data["stats"]) == 6
        assert data["abilities"][0]["name"] == "blaze"
        assert data["abilities"][0]["description"].startswith(
            "Strengthens Fire moves"
        )

    def test_detail_404_is_normalized(self, api_client, fake_client):
        fake_client.not_found.add("99999")
        resp = api_client.get("/api/pokemon/99999/")
        assert resp.status_code == 404
        assert "error" in resp.json()

    def test_detail_invalid_identifier_is_400(self, api_client, fake_client):
        resp = api_client.get("/api/pokemon/6%3Bdrop/")
        assert resp.status_code == 400
        assert "error" in resp.json()


class TestMachines:
    """Endpoints de TMs e detalhe de moves."""

    def test_tm_list_returns_latest_game(self, api_client, fake_client):
        # machine/100 é red-blue (id menor), machine/101 é scarlet-violet (maior)
        resp = api_client.get("/api/tms/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["results"][0] == {
            "number": "tm01",
            "move": "take-down",
            "move_id": 36,
            "type": "normal",
            "damage_class": "physical",
            "power": 90,
        }

    def test_move_detail_returns_stats_and_effects(self, api_client, fake_client):
        resp = api_client.get("/api/moves/36/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "take-down"
        assert data["type"] == "normal"
        assert data["damage_class"] == "physical"
        assert data["power"] == 90
        assert data["accuracy"] == 85
        assert data["pp"] == 20
        assert data["short_effect"] == "Inflicts recoil damage."
        assert data["flavor_text"].startswith("A reckless")

    def test_move_detail_invalid_identifier_is_400(self, api_client, fake_client):
        resp = api_client.get("/api/moves/6%3Bdrop/")
        assert resp.status_code == 400
        assert "error" in resp.json()
