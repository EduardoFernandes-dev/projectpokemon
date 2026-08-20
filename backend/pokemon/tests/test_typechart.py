"""Testes do type chart, função pura de efetividade + particionamento."""

from pokemon.services.typechart import (
    build_type_relations,
    partition_effectiveness,
    type_effectiveness,
)

# Relações sintéticas (subconjunto real da PokeAPI, gen 1).
RELATIONS = {
    "fighting": {
        "double_damage_from": ["flying", "psychic", "fairy"],
        "half_damage_from": ["bug", "rock", "dark"],
        "no_damage_from": [],
    },
    "normal": {
        "double_damage_from": ["fighting"],
        "half_damage_from": [],
        "no_damage_from": ["ghost"],
    },
    "fire": {
        "double_damage_from": ["water", "ground", "rock"],
        "half_damage_from": ["grass", "bug", "fire", "ice", "steel", "fairy"],
        "no_damage_from": [],
    },
    "water": {
        "double_damage_from": ["electric", "grass"],
        "half_damage_from": ["fire", "water", "ice", "steel"],
        "no_damage_from": [],
    },
    "grass": {
        "double_damage_from": ["fire", "ice", "poison", "flying", "bug"],
        "half_damage_from": ["water", "grass", "electric", "ground"],
        "no_damage_from": [],
    },
    "ground": {
        "double_damage_from": ["water", "grass", "ice"],
        "half_damage_from": ["poison", "rock"],
        "no_damage_from": ["electric"],
    },
    "flying": {
        "double_damage_from": ["electric", "rock", "ice"],
        "half_damage_from": ["grass", "fighting", "bug"],
        "no_damage_from": ["ground"],
    },
    "electric": {
        "double_damage_from": ["ground"],
        "half_damage_from": ["flying", "electric", "steel"],
        "no_damage_from": [],
    },
    "rock": {
        "double_damage_from": ["water", "grass", "fighting", "ground", "steel"],
        "half_damage_from": ["normal", "fire", "poison", "flying"],
        "no_damage_from": [],
    },
    "ghost": {
        "double_damage_from": ["ghost", "dark"],
        "half_damage_from": ["poison", "bug"],
        "no_damage_from": ["normal", "fighting"],
    },
    "ice": {
        "double_damage_from": ["fire", "fighting", "rock", "steel"],
        "half_damage_from": ["ice"],
        "no_damage_from": [],
    },
}


class TestTypeEffectiveness:
    def test_single_type_simple(self):
        eff = type_effectiveness(["fire"], RELATIONS)
        assert eff["water"] == 2.0
        assert eff["grass"] == 0.5
        assert eff["fire"] == 0.5

    def test_charizard_fire_flying(self):
        eff = type_effectiveness(["fire", "flying"], RELATIONS)
        assert eff["rock"] == 4.0  # 2×2
        assert eff["ground"] == 0.0  # fire 2×, flying 0× → imune
        assert eff["water"] == 2.0
        assert eff["electric"] == 2.0  # flying fraco a electric
        assert eff["grass"] == 0.25  # 0.5×0.5

    def test_ground_immune_to_electric(self):
        eff = type_effectiveness(["ground"], RELATIONS)
        assert eff["electric"] == 0.0

    def test_normal_vs_ghost_immune(self):
        eff = type_effectiveness(["normal"], RELATIONS)
        assert eff["ghost"] == 0.0
        assert eff["fighting"] == 2.0

    def test_double_weakness_4x(self):
        eff = type_effectiveness(["fire", "rock"], RELATIONS)
        assert eff["water"] == 4.0


class TestPartition:
    def test_partition_charizard(self):
        eff = type_effectiveness(["fire", "flying"], RELATIONS)
        parts = partition_effectiveness(eff)
        weakness_types = {w["type"]: w["multiplier"] for w in parts["weaknesses"]}
        assert weakness_types["rock"] == 4.0
        assert weakness_types["water"] == 2.0
        assert "ground" in {i["type"] for i in parts["immunities"]}
        assert {"type": "grass", "multiplier": 0.25} in parts["resistances"]

    def test_partition_sorted(self):
        eff = type_effectiveness(["fire"], RELATIONS)
        parts = partition_effectiveness(eff)
        multis = [w["multiplier"] for w in parts["weaknesses"]]
        assert multis == sorted(multis, reverse=True)


class FakeTypeClient:
    """Devolve damage_relations no formato REAL da PokeAPI (objetos name/url).

    Todos os 18 ids têm o nome real do tipo (para o mapa de atacantes ficar
    completo, como na PokeAPI); só fire/flying têm relações preenchidas.
    """

    TYPE_NAMES = {
        1: "normal",
        2: "fighting",
        3: "flying",
        4: "poison",
        5: "ground",
        6: "rock",
        7: "bug",
        8: "ghost",
        9: "steel",
        10: "fire",
        11: "water",
        12: "grass",
        13: "electric",
        14: "psychic",
        15: "ice",
        16: "dragon",
        17: "dark",
        18: "fairy",
    }

    RELATIONS = {
        10: {
            "double_damage_from": [
                {"name": "water", "url": "/type/11/"},
                {"name": "rock", "url": "/type/6/"},
            ],
            "half_damage_from": [{"name": "grass", "url": "/type/12/"}],
            "no_damage_from": [],
        },
        3: {
            "double_damage_from": [{"name": "rock", "url": "/type/6/"}],
            "half_damage_from": [],
            "no_damage_from": [{"name": "ground", "url": "/type/5/"}],
        },
    }

    def get_resource(self, resource, identifier, ttl=None):
        assert resource == "type"
        i = int(identifier)
        return {
            "name": self.TYPE_NAMES.get(i, f"type-{i}"),
            "damage_relations": self.RELATIONS.get(i, {}),
        }

    def get_list(self, resource, limit=100000, offset=0):
        raise AssertionError("get_list não usado por build_type_relations")

    def fetch(self, url, ttl=None):
        raise AssertionError("fetch não usado por build_type_relations")


def test_build_type_relations_normalizes_pokeapi_format():
    """Regressão: a PokeAPI devolve listas de objetos {'name', 'url'}."""
    relations = build_type_relations(FakeTypeClient())
    assert relations["fire"]["double_damage_from"] == ["water", "rock"]
    assert relations["fire"]["half_damage_from"] == ["grass"]
    assert relations["flying"]["no_damage_from"] == ["ground"]

    eff = type_effectiveness(["fire", "flying"], relations)
    assert eff["water"] == 2.0
    assert eff["rock"] == 4.0
    assert eff["ground"] == 0.0
