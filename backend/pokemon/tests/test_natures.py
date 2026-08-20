"""Testes das naturezas, heurística determinística sobre stats base.

O client fake usa mapeamentos reais da PokeAPI (nomes de naturezas corretos
para cada combinação boost/lower), para os testes validarem a lógica real.
"""

from pokemon.services.natures import best_natures


class FakeNatureClient:
    """Client fake com as naturezas relevantes (nomes reais da PokeAPI)."""

    # (boost, lower) → nome, subconjunto real:
    # adamant: atk↑/spa↓ · lonely: atk↑/def↓ · modest: spa↑/atk↓ · mild: spa↑/def↓
    # jolly: spe↑/spa↓ · hasty: spe↑/def↓ · sassy: spd↑/spe↓ · careful: spd↑/spa↓
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
        "3": {
            "name": "modest",
            "increased_stat": {"name": "special-attack"},
            "decreased_stat": {"name": "attack"},
        },
        "4": {
            "name": "mild",
            "increased_stat": {"name": "special-attack"},
            "decreased_stat": {"name": "defense"},
        },
        "5": {
            "name": "sassy",
            "increased_stat": {"name": "special-defense"},
            "decreased_stat": {"name": "speed"},
        },
        "6": {
            "name": "careful",
            "increased_stat": {"name": "special-defense"},
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
        "9": {
            "name": "naughty",
            "increased_stat": {"name": "attack"},
            "decreased_stat": {"name": "special-defense"},
        },
        "10": {"name": "hardy", "increased_stat": None, "decreased_stat": None},
    }

    def get_resource(self, resource, identifier, ttl=None):
        assert resource == "nature"
        return self.NATURES.get(identifier, {"increased_stat": None, "decreased_stat": None})

    def get_list(self, resource, limit=100000, offset=0):
        raise AssertionError("get_list não usado por best_natures")

    def fetch(self, url, ttl=None):
        raise AssertionError("fetch não usado por best_natures")


STATS_PHYSICAL = {
    "hp": 80,
    "attack": 130,
    "defense": 90,
    "special-attack": 60,
    "special-defense": 85,
    "speed": 100,
}

STATS_SPECIAL = {
    "hp": 80,
    "attack": 60,
    "defense": 90,
    "special-attack": 130,
    "special-defense": 85,
    "speed": 100,
}

STATS_SLOW_TANK = {
    "hp": 160,
    "attack": 110,
    "defense": 90,
    "special-attack": 65,
    "special-defense": 110,
    "speed": 30,
}


def test_physical_boosts_attack_lowers_special_attack():
    suggestions = best_natures(FakeNatureClient(), STATS_PHYSICAL, "physical")
    assert suggestions[0]["boost"] == "attack"
    assert suggestions[0]["lower"] == "special-attack"  # stat mais fraco
    assert suggestions[0]["nature"] == "adamant"


def test_physical_alternative_lowers_second_weakest():
    suggestions = best_natures(FakeNatureClient(), STATS_PHYSICAL, "physical")
    assert len(suggestions) >= 2
    # 2º stat mais fraco (excluindo attack e hp): special-defense 85 < defense 90
    assert suggestions[1]["nature"] == "naughty"  # (attack, special-defense)


def test_special_boosts_special_attack_lowers_attack():
    suggestions = best_natures(FakeNatureClient(), STATS_SPECIAL, "special")
    assert suggestions[0]["boost"] == "special-attack"
    assert suggestions[0]["lower"] == "attack"
    assert suggestions[0]["nature"] == "modest"


def test_fast_boosts_speed():
    suggestions = best_natures(FakeNatureClient(), STATS_PHYSICAL, "fast")
    assert suggestions[0]["boost"] == "speed"
    assert suggestions[0]["lower"] == "special-attack"
    assert suggestions[0]["nature"] == "jolly"


def test_hp_never_chosen_as_lower_stat():
    # STATS_PHYSICAL tem HP=80 (mais baixo que defense 90), HP não pode ser baixado.
    suggestions = best_natures(FakeNatureClient(), STATS_PHYSICAL, "physical")
    assert suggestions[0]["lower"] != "hp"


def test_bulky_boosts_best_defensive_stat_and_lowers_speed():
    suggestions = best_natures(FakeNatureClient(), STATS_SLOW_TANK, "bulky")
    assert suggestions[0]["boost"] == "special-defense"  # 110 >= 90
    assert suggestions[0]["lower"] == "speed"  # stat mais fraco do tank
    assert suggestions[0]["nature"] == "sassy"


def test_bulky_alternative():
    suggestions = best_natures(FakeNatureClient(), STATS_SLOW_TANK, "bulky")
    assert suggestions[1]["nature"] == "careful"  # (special-defense, special-attack)


def test_reason_mentions_strategy():
    import pytest

    with pytest.raises(ValueError):
        best_natures(FakeNatureClient(), STATS_PHYSICAL, "ninja")
