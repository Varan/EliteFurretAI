# -*- coding: utf-8 -*-
from unittest.mock import MagicMock

import pytest
from poke_env.environment import DoubleBattle, Effect, Field, Move, Pokemon

from elitefurretai.battle_inference.inference_utils import (
    get_ability_and_identifier,
    get_pokemon,
    get_priority_and_identifier,
    get_residual_and_identifier,
    get_segments,
    get_showdown_identifier,
    is_ability_event,
    standardize_pokemon_ident,
)


def test_get_segments(residual_logs, edgecase_logs, uturn_logs):
    segments = get_segments(edgecase_logs[0])
    assert segments["preturn_switch"][0] == [
        "",
        "switch",
        "p1a: Indeedee",
        "Indeedee, L50, M",
        "100/100",
    ]
    assert segments["preturn_switch"][-1] == [
        "",
        "-weather",
        "RainDance",
        "[from] ability: Drizzle",
        "[of] p1b: Pelipper",
    ]
    assert (
        len(
            set(segments.keys())
            & set(
                [
                    "switch",
                    "battle_mechanic",
                    "move",
                    "state_upkeep",
                    "residual",
                    "preturn_switch",
                ]
            )
        )
        == 1
    )

    segments = get_segments(edgecase_logs[1])
    assert segments["move"][0] == [
        "",
        "move",
        "p2a: Heracross",
        "Seismic Toss",
        "p1a: Indeedee",
    ]
    assert segments["move"][-1] == [
        "",
        "-fieldstart",
        "move: Trick Room",
        "[of] p1a: Indeedee",
    ]
    assert (
        len(
            set(segments.keys())
            & set(
                [
                    "switch",
                    "battle_mechanic",
                    "move",
                    "state_upkeep",
                    "residual",
                    "preturn_switch",
                ]
            )
        )
        == 2
    )

    segments = get_segments(edgecase_logs[2])
    assert segments["switch"][0] == [
        "",
        "switch",
        "p2b: Grimmsnarl",
        "Grimmsnarl, L50, M",
        "170/170",
    ]
    assert segments["battle_mechanic"][0] == [
        "",
        "-terastallize",
        "p2a: Heracross",
        "Ghost",
    ]
    assert segments["battle_mechanic"][-1] == [
        "",
        "-terastallize",
        "p1a: Indeedee",
        "Psychic",
    ]
    assert segments["move"][0] == [
        "",
        "move",
        "p2a: Heracross",
        "Endure",
        "p2a: Heracross",
    ]
    assert segments["move"][-1] == ["", "-damage", "p1a: Indeedee", "2/100"]
    assert (
        len(
            set(segments.keys())
            & set(
                [
                    "switch",
                    "battle_mechanic",
                    "move",
                    "state_upkeep",
                    "residual",
                    "preturn_switch",
                ]
            )
        )
        == 4
    )

    segments = get_segments(edgecase_logs[3])
    assert segments["move"][0] == [
        "",
        "move",
        "p2b: Grimmsnarl",
        "Thunder Wave",
        "p1b: Pelipper",
        "[miss]",
    ]
    assert segments["move"][-1] == ["", "-fail", "p1a: Indeedee"]
    assert (
        len(
            set(segments.keys())
            & set(
                [
                    "switch",
                    "battle_mechanic",
                    "move",
                    "state_upkeep",
                    "residual",
                    "preturn_switch",
                ]
            )
        )
        == 2
    )

    segments = get_segments(edgecase_logs[4])
    assert segments["move"][0] == [
        "",
        "move",
        "p2a: Heracross",
        "Endure",
        "p2a: Heracross",
    ]
    assert segments["move"][-1] == ["", "-fail", "p1a: Indeedee"]
    assert (
        len(
            set(segments.keys())
            & set(
                [
                    "switch",
                    "battle_mechanic",
                    "move",
                    "state_upkeep",
                    "residual",
                    "preturn_switch",
                ]
            )
        )
        == 2
    )

    segments = get_segments(edgecase_logs[5])
    assert segments["move"][0] == [
        "",
        "move",
        "p2b: Grimmsnarl",
        "Scary Face",
        "",
        "[still]",
    ]
    assert segments["move"][-1] == ["", "-fail", "p1a: Indeedee"]
    assert segments["state_upkeep"] == [
        ["", "-weather", "Snow", "[upkeep]"],
        ["", "-fieldend", "move: Trick Room"],
        ["", "-fieldend", "move: Psychic Terrain"],
    ]
    assert (
        len(
            set(segments.keys())
            & set(
                [
                    "switch",
                    "battle_mechanic",
                    "move",
                    "state_upkeep",
                    "residual",
                    "preturn_switch",
                ]
            )
        )
        == 2
    )

    segments = get_segments(edgecase_logs[6])
    assert segments["switch"][0] == [
        "",
        "switch",
        "p2a: Drednaw",
        "Drednaw, L50, F",
        "197/197",
    ]
    assert segments["switch"][-1] == [
        "",
        "-weather",
        "RainDance",
        "[from] ability: Drizzle",
        "[of] p1a: Pelipper",
    ]
    assert segments["move"][0] == [
        "",
        "move",
        "p2b: Grimmsnarl",
        "Thunder Wave",
        "p2a: Drednaw",
    ]
    assert segments["move"][-1] == ["", "-activate", "p1a: Pelipper", "trapped"]
    assert (
        len(
            set(segments.keys())
            & set(
                [
                    "switch",
                    "battle_mechanic",
                    "move",
                    "state_upkeep",
                    "residual",
                    "preturn_switch",
                ]
            )
        )
        == 3
    )

    segments = get_segments(edgecase_logs[7])
    assert segments["move"][0] == [
        "",
        "move",
        "p1a: Pelipper",
        "Whirlpool",
        "p1b: Farigiraf",
    ]
    assert segments["move"][-1] == ["", "-miss", "p2a: Drednaw", "p1a: Pelipper"]
    assert segments["residual"][0] == [
        "",
        "-damage",
        "p1b: Farigiraf",
        "67/100",
        "[from] move: Whirlpool",
        "[partiallytrapped]",
    ]
    assert len(segments["residual"]) == 1
    assert (
        len(
            set(segments.keys())
            & set(
                [
                    "switch",
                    "battle_mechanic",
                    "move",
                    "state_upkeep",
                    "residual",
                    "preturn_switch",
                ]
            )
        )
        == 3
    )

    segments = get_segments(edgecase_logs[8])
    assert segments["move"][0] == ["", "move", "p1a: Pelipper", "U-turn", "p2a: Drednaw"]
    assert segments["move"][-1] == [
        "",
        "-fieldstart",
        "move: Grassy Terrain",
        "[from] ability: Grassy Surge",
        "[of] p1b: Rillaboom",
    ]
    assert segments["residual"][0] == [
        "",
        "-heal",
        "p2a: Drednaw",
        "187/197 par",
        "[from] Grassy Terrain",
    ]
    assert segments["residual"][-1] == [
        "",
        "-heal",
        "p2a: Drednaw",
        "197/197 par",
        "[from] item: Leftovers",
    ]
    assert segments["preturn_switch"] == [
        ["", "switch", "p1a: Farigiraf", "Farigiraf, L50, F", "56/100"]
    ]
    assert (
        len(
            set(segments.keys())
            & set(
                [
                    "switch",
                    "battle_mechanic",
                    "move",
                    "state_upkeep",
                    "residual",
                    "preturn_switch",
                ]
            )
        )
        == 4
    )

    segments = get_segments(edgecase_logs[9])
    assert segments["activation"] == [
        ["", "-activate", "p1a: Farigiraf", "item: Quick Claw"]
    ]
    assert segments["move"][0] == [
        "",
        "move",
        "p1a: Farigiraf",
        "Mean Look",
        "p2a: Drednaw",
    ]
    assert segments["move"][-1] == ["", "-unboost", "p1a: Farigiraf", "spa", "1"]
    assert segments["residual"][0] == [
        "",
        "-heal",
        "p1a: Farigiraf",
        "33/100",
        "[from] Grassy Terrain",
    ]
    assert segments["residual"][-1] == [
        "",
        "-heal",
        "p1a: Farigiraf",
        "33/100",
        "[from] Grassy Terrain",
    ]
    assert segments["preturn_switch"] == [
        ["", "switch", "p2a: Heracross", "Heracross, L50, M, tera:Ghost", "155/155"],
        ["", "-enditem", "p2a: Heracross", "Grassy Seed"],
        ["", "-boost", "p2a: Heracross", "def", "1", "[from] item: Grassy Seed"],
    ]
    assert (
        len(
            set(segments.keys())
            & set(
                [
                    "switch",
                    "battle_mechanic",
                    "move",
                    "state_upkeep",
                    "residual",
                    "preturn_switch",
                ]
            )
        )
        == 4
    )

    segments = get_segments(edgecase_logs[10])
    assert segments["move"][0] == [
        "",
        "move",
        "p2a: Heracross",
        "Vacuum Wave",
        "",
        "[still]",
    ]
    assert segments["move"][-1] == ["", "faint", "p1a: Farigiraf"]
    assert segments["preturn_switch"] == [
        ["", "switch", "p1a: Pelipper", "Pelipper, L50, F", "40/100"],
        ["", "-weather", "RainDance", "[from] ability: Drizzle", "[of] p1a: Pelipper"],
    ]
    assert (
        len(
            set(segments.keys())
            & set(
                [
                    "switch",
                    "battle_mechanic",
                    "move",
                    "state_upkeep",
                    "residual",
                    "preturn_switch",
                ]
            )
        )
        == 3
    )

    segments = get_segments(edgecase_logs[11])
    assert segments["move"][0] == [
        "",
        "move",
        "p1b: Rillaboom",
        "Frenzy Plant",
        "p1a: Pelipper",
    ]
    assert segments["move"][-1] == ["", "-unboost", "p2a: Heracross", "spa", "1"]
    assert segments["residual"][0] == [
        "",
        "-heal",
        "p1b: Rillaboom",
        "78/100",
        "[from] Grassy Terrain",
    ]
    assert segments["residual"][-1] == [
        "",
        "-heal",
        "p2a: Heracross",
        "106/155",
        "[from] Grassy Terrain",
    ]
    assert (
        len(
            set(segments.keys())
            & set(
                [
                    "switch",
                    "battle_mechanic",
                    "move",
                    "state_upkeep",
                    "residual",
                    "preturn_switch",
                ]
            )
        )
        == 3
    )

    segments = get_segments(edgecase_logs[14])
    assert segments["move"][0] == [
        "",
        "move",
        "p2a: Heracross",
        "Endure",
        "p2a: Heracross",
    ]
    assert segments["move"][-1] == [
        "",
        "-damage",
        "p2b: Teddiursa",
        "62/167",
        "[from] item: Life Orb",
    ]
    assert (
        len(
            set(segments.keys())
            & set(
                [
                    "switch",
                    "battle_mechanic",
                    "move",
                    "state_upkeep",
                    "residual",
                    "preturn_switch",
                ]
            )
        )
        == 1
    )

    segments = get_segments(edgecase_logs[15])
    print(segments)
    assert segments["activation"][0] == [
        "",
        "-activate",
        "p2a: Rillaboom",
        "item: Quick Claw",
    ]
    assert segments["activation"][-1] == ["", ""]
    assert segments["switch"][0] == [
        "",
        "switch",
        "p1b: Wo-Chien",
        "Wo-Chien, L50, tera:Dark",
        "50/160",
    ]
    assert segments["switch"][-1] == ["", "-ability", "p1b: Wo-Chien", "Tablets of Ruin"]
    assert (
        len(
            set(segments.keys())
            & set(
                [
                    "activation",
                    "switch",
                    "battle_mechanic",
                    "move",
                    "state_upkeep",
                    "residual",
                    "preturn_switch",
                ]
            )
        )
        == 5
    )

    assert len(get_segments(residual_logs[0])) == 1
    assert len(get_segments(residual_logs[1])) == 1
    assert len(get_segments(residual_logs[2])) == 1
    assert len(get_segments(residual_logs[3])) == 1
    assert len(get_segments(residual_logs[4])) == 1

    segments = get_segments(residual_logs[5])
    assert segments["preturn_switch"][0] == [
        "",
        "switch",
        "p1a: Raichu",
        "Raichu, L50, F",
        "167/167",
    ]
    assert segments["preturn_switch"][-1] == [
        "",
        "-weather",
        "Sandstorm",
        "[from] ability: Sand Stream",
        "[of] p1b: Tyranitar",
    ]
    assert len(segments["preturn_switch"]) == 5
    assert (
        len(
            set(segments.keys())
            & set(
                [
                    "switch",
                    "battle_mechanic",
                    "move",
                    "state_upkeep",
                    "residual",
                    "preturn_switch",
                ]
            )
        )
        == 1
    )

    segments = get_segments(residual_logs[6])
    assert segments["switch"][0] == [
        "",
        "switch",
        "p1a: Furret",
        "Furret, L50, F",
        "160/160",
    ]
    assert segments["switch"][-1] == [
        "",
        "-item",
        "p2b: Amoonguss",
        "Sitrus Berry",
        "[from] ability: Frisk",
        "[of] p1a: Furret",
        "[identify]",
    ]
    assert segments["battle_mechanic"][0] == ["", "-terastallize", "p2a: Pikachu", "Bug"]
    assert segments["battle_mechanic"][-1] == [
        "",
        "-terastallize",
        "p1b: Tyranitar",
        "Electric",
    ]
    assert segments["move"][0] == [
        "",
        "move",
        "p2a: Pikachu",
        "Thunderbolt",
        "p1b: Tyranitar",
    ]
    assert segments["move"][-1] == ["", "-damage", "p2a: Pikachu", "39/100"]
    assert segments["residual"][0] == [
        "",
        "-damage",
        "p1a: Furret",
        "150/160",
        "[from] Sandstorm",
    ]
    assert segments["residual"][-1] == [
        "",
        "-status",
        "p1b: Tyranitar",
        "brn",
        "[from] item: Flame Orb",
    ]
    assert (
        len(
            set(segments.keys())
            & set(
                [
                    "switch",
                    "battle_mechanic",
                    "move",
                    "state_upkeep",
                    "residual",
                    "preturn_switch",
                ]
            )
        )
        == 5
    )

    segments = get_segments(residual_logs[12])
    assert segments["switch"][0] == [
        "",
        "switch",
        "p2a: Charizard",
        "Charizard, L50, F",
        "42/100",
    ]
    assert len(segments["switch"]) == 1
    assert segments["move"][0] == [
        "",
        "move",
        "p2b: Amoonguss",
        "Pollen Puff",
        "p1b: Tyranitar",
    ]
    assert segments["move"][-1] == ["", "faint", "p1a: Sentret"]
    assert segments["residual"][0] == [
        "",
        "-heal",
        "p1b: Tyranitar",
        "44/207 brn",
        "[from] Grassy Terrain",
    ]
    assert segments["residual"][-1] == [
        "",
        "-damage",
        "p1b: Tyranitar",
        "32/207 brn",
        "[from] brn",
    ]
    assert (
        len(
            set(segments.keys())
            & set(
                [
                    "switch",
                    "battle_mechanic",
                    "move",
                    "state_upkeep",
                    "residual",
                    "preturn_switch",
                ]
            )
        )
        == 3
    )

    segments = get_segments(residual_logs[18])
    assert segments["move"][0] == [
        "",
        "move",
        "p1b: Furret",
        "Double-Edge",
        "p2a: Pikachu",
    ]
    assert segments["move"][-1] == ["", "faint", "p1b: Furret"]

    # Now go to uturn logs to test when we have a uturn and an empty log from the request
    segments = get_segments(uturn_logs[0])
    assert segments["move"][0] == ["", "move", "p1a: Tyranitar", "Protect", "", "[still]"]
    assert segments["move"][-1] == [
        "",
        "-sidestart",
        "p2: CustomPlayer 1",
        "move: Tailwind",
    ]
    assert segments["residual"][0] == [
        "",
        "-heal",
        "p1a: Tyranitar",
        "153/175",
        "[from] item: Leftovers",
    ]
    assert segments["residual"][-1] == ["", "-fieldend", "move: Trick Room"]
    assert segments["preturn_switch"] == [
        ["", "switch", "p1b: Grimmsnarl", "Grimmsnarl, L50, M", "202/202"]
    ]
    assert segments["init"]
    assert segments["turn"]
    assert len(segments["turn"]) == 1
    assert len(segments) == 5

    segments = get_segments(uturn_logs[1])
    print(segments)
    assert segments["switch"][0] == ["", "switch", "p1b: Chi-Yu", "Chi-Yu, L50", "162/162"]
    assert segments["switch"][-1] == ["", "-item", "p1b: Chi-Yu", "Air Balloon"]
    assert segments["battle_mechanic"] == [
        ["", "-terastallize", "p2a: Rillaboom", "Ghost"]
    ]
    assert segments["move"][0] == ["", "-activate", "p2a: Rillaboom", "confusion"]
    assert segments["move"][-1] == ["", "-fail", "p1a: Wo-Chien"]
    assert segments["residual"][0] == [
        "",
        "-damage",
        "p2a: Rillaboom",
        "6/100 brn",
        "[from] Sandstorm",
    ]
    assert segments["residual"][-1] == [
        "",
        "-damage",
        "p2a: Rillaboom",
        "6/100 brn",
        "[from] brn",
    ]


def test_get_residual_and_identifier():
    assert get_residual_and_identifier(
        [
            "",
            "-damage",
            "p1b: Farigiraf",
            "135/195",
            "[from] move: Bind",
            "[partiallytrapped]",
        ]
    ) == ("Bind", "p1: Farigiraf")
    assert get_residual_and_identifier(
        ["", "-activate", "p1a: Chansey", "ability: Healer"]
    ) == ("Healer", "p1: Chansey")
    assert get_residual_and_identifier(
        ["", "-activate", "p1a: Farigaraf", "ability: Cud Chew"]
    ) == ("Cud Chew", "p1: Farigaraf")
    assert get_residual_and_identifier(
        ["", "-end", "p2a: Regigigas", "Slow Start", "[silent]"]
    ) == ("Slow Start", "p2: Regigigas")
    assert get_residual_and_identifier(
        ["", "-heal", "p1a: Smeargle", "94/162", "[from] Ingrain"]
    ) == ("Ingrain", "p1: Smeargle")
    assert get_residual_and_identifier(
        ["", "-ability", "p1b: Espathra", "Speed Boost", "boost"]
    ) == ("Speed Boost", "p1: Espathra")
    assert get_residual_and_identifier(
        ["", "-ability", "p1a: Smeargle", "Moody", "boost"]
    ) == ("Moody", "p1: Smeargle")
    assert get_residual_and_identifier(
        [
            "",
            "-damage",
            "p2a: Blastoise",
            "88/100 brn",
            "[from] Leech Seed",
            "[of] p1b: Wo-Chien",
        ]
    ) == ("Leech Seed", "p2: Blastoise")
    assert get_residual_and_identifier(
        ["", "-damage", "p2a: Blastoise", "50/100 psn", "[from] psn"]
    ) == ("psn", "p2: Blastoise")
    assert get_residual_and_identifier(
        ["", "-heal", "p2b: Drednaw", "51/100 par", "[from] Grassy Terrain"]
    ) == ("Grassy Terrain", "p2: Drednaw")
    assert get_residual_and_identifier(
        ["", "-damage", "p2a: Drednaw", "76/100", "[from] Salt Cure"]
    ) == ("Salt Cure", "p2: Drednaw")
    assert get_residual_and_identifier(
        ["", "-heal", "p1a: Smeargle", "43/162", "[from] Aqua Ring"]
    ) == ("Aqua Ring", "p1: Smeargle")
    assert get_residual_and_identifier(
        ["", "-heal", "p2a: Blastoise", "56/100 brn", "[from] ability: Rain Dish"]
    ) == ("Rain Dish", "p2: Blastoise")
    assert get_residual_and_identifier(
        ["", "-heal", "p1b: Farigiraf", "72/195", "[from] item: Leftovers"]
    ) == ("Leftovers", "p1: Farigiraf")
    assert get_residual_and_identifier(
        ["", "-item", "p1a: Tropius", "Sitrus Berry", "[from] ability: Harvest"]
    ) == ("Harvest", "p1: Tropius")
    assert get_residual_and_identifier(
        ["", "-damage", "p2a: Grimmsnarl", "24/100", "[from] item: Black Sludge"]
    ) == ("Black Sludge", "p2: Grimmsnarl")
    assert get_residual_and_identifier(
        ["", "-status", "p2a: Blastoise", "brn", "[from] item: Flame Orb"]
    ) == ("Flame Orb", "p2: Blastoise")
    assert get_residual_and_identifier(
        ["", "-damage", "p1a: Smeargle", "64/162", "[from] item: Sticky Barb"]
    ) == ("Sticky Barb", "p1: Smeargle")
    assert get_residual_and_identifier(
        ["", "-status", "p1b: Espathra", "tox", "[from] item: Toxic Orb"]
    ) == ("Toxic Orb", "p1: Espathra")
    assert get_residual_and_identifier(
        ["", "-damage", "p1b: Furret", "25/160", "[from] Sandstorm"]
    ) == ("Sandstorm", "p1: Furret")
    assert get_residual_and_identifier(
        ["", "-damage", "p1b: Tyranitar", "32/207 brn", "[from] brn"]
    ) == ("brn", "p1: Tyranitar")
    assert get_residual_and_identifier(["", "-start", "p1b: Wo-Chien", "perish0"]) == (
        "Perish Song",
        "p1: Wo-Chien",
    )
    assert get_residual_and_identifier(["", "-start", "p1b: Wo-Chien", "perish1"]) == (
        "Perish Song",
        "p1: Wo-Chien",
    )
    assert get_residual_and_identifier(["", "-start", "p1b: Wo-Chien", "perish2"]) == (
        "Perish Song",
        "p1: Wo-Chien",
    )
    assert get_residual_and_identifier(["", "-start", "p1a: Espathra", "perish3"]) == (
        "Perish Song",
        "p1: Espathra",
    )
    assert get_residual_and_identifier(
        ["", "-weather", "RainDance", "[from] ability: Drizzle", "[of] p1b: Tyranitar"]
    ) == (None, None)


def test_get_ability_and_identifier():
    assert get_ability_and_identifier(
        [
            "",
            "-item",
            "p2a: Gardevoir",
            "Iron Ball",
            "[from] ability: Frisk",
            "[of] p1a: Furret",
        ]
    ) == ("Frisk", "p1: Furret")
    assert get_ability_and_identifier(
        ["", "-weather", "Sandstorm", "[from] ability: Sand Stream", "[of] p1b: Tyranitar"]
    ) == ("Sand Stream", "p1: Tyranitar")
    assert get_ability_and_identifier(
        [
            "",
            "-fieldstart",
            "move: Electric Terrain",
            "[from] ability: Electric Surge",
            "[of] p1a: Pincurchin",
        ]
    ) == ("Electric Surge", "p1: Pincurchin")
    assert get_ability_and_identifier(
        [
            "",
            "-ability",
            "p2a: Gardevoir",
            "Sand Stream",
            "[from] ability: Trace",
            "[of] p1b: Tyranitar",
        ]
    ) == ("Sand Stream", "p2: Gardevoir")
    assert get_ability_and_identifier(
        ["", "-activate", "p2b: Fluttermane", "ability: Protosynthesis"]
    ) == ("Protosynthesis", "p2: Fluttermane")
    assert get_ability_and_identifier(
        ["", "-copyboost", "p2a: Flamigo", "p2b: Furret", "[from] ability: Costar"]
    ) == ("Costar", "p2: Flamigo")
    assert get_ability_and_identifier(
        [
            "",
            "-activate",
            "p2b: Hypno",
            "ability: Forewarn",
            "darkpulse",
            "[of] p1a: Chi-Yu",
        ]
    ) == ("Forewarn", "p2: Hypno")
    assert get_ability_and_identifier(["", "-ability", "p1b: Calyrex", "As One"]) == (
        "As One",
        "p1: Calyrex",
    )
    assert get_ability_and_identifier(["", "-ability", "p1b: Calyrex", "Unnerve"]) == (
        "Unnerve",
        "p1: Calyrex",
    )
    assert get_ability_and_identifier(
        ["", "-ability", "p2b: Weezing", "Neutralizing Gas"]
    ) == ("Neutralizing Gas", "p2: Weezing")


def test_standardize_pokemon_ident():
    assert standardize_pokemon_ident("[of] p2a: Gardevoir") == "p2: Gardevoir"
    assert standardize_pokemon_ident("p2a: Gardevoir") == "p2: Gardevoir"
    assert standardize_pokemon_ident("[of] p1b: Wo-Chien") == "p1: Wo-Chien"
    assert standardize_pokemon_ident("p1b: Wo-Chien") == "p1: Wo-Chien"


def test_get_pokemon():
    battle = MagicMock()
    battle.team = {"p1: Furret": True}
    battle.opponent_team = {"p2: Furret": True}

    assert get_pokemon("p1a: Furret", battle)
    assert get_pokemon("p1b: Furret", battle)
    assert get_pokemon("p1: Furret", battle)
    assert get_pokemon("p2a: Furret", battle)
    assert get_pokemon("p2b: Furret", battle)
    assert get_pokemon("p2: Furret", battle)

    with pytest.raises(ValueError):
        get_pokemon("furret", battle)


def test_is_ability_event():
    assert is_ability_event(["", "-ability", "p1b: Aerodactyl", "Unnerve"])
    assert is_ability_event(
        ["", "-activate", "p1a: Iron Valiant", "ability: Quark Drive", "[fromitem]"]
    )
    assert is_ability_event(
        [
            "",
            "-item",
            "p1b: Landorus",
            "Life Orb",
            "[from] ability: Frisk",
            "[of] p2a: Furret",
        ]
    )
    assert is_ability_event(["", "-activate", "p2a: Terapagos", "ability: Tera Shift"])
    assert is_ability_event(["", "-ability", "p1b: Calyrex", "As One"])
    assert is_ability_event(["", "-ability", "p1b: Calyrex", "Unnerve"])
    assert is_ability_event(["", "-ability", "p2b: Weezing", "Neutralizing Gas"])
    assert is_ability_event(
        [
            "",
            "-activate",
            "p2b: Hypno",
            "ability: Forewarn",
            "Dark Pulse",
            "[of] p1a: Furret",
        ]
    )
    assert is_ability_event(
        ["", "-weather", "Sandstorm", "[from] ability: Sand Stream", "[of] p1b: Tyranitar"]
    )
    assert is_ability_event(
        ["", "-copyboost", "p1a: Flamigo", "p1b: Furret", "[from] ability: Costar"]
    )
    assert is_ability_event(
        [
            "",
            "-clearboost",
            "p1a: Furret",
            "[from] ability: Curious Medicine",
            "[of] p2b: Slowking-Galar",
        ]
    )
    assert not is_ability_event(["", "move", "p2b: Furret", "Absolute Destruction"])
    assert not is_ability_event(["", "switch", "p2b: Furret"])
    assert not is_ability_event(["", ""])


def test_get_priority_and_identifier():
    gen = 9
    logger = MagicMock()
    battle = DoubleBattle("tag", "username", logger, gen=gen)

    furret = Pokemon(gen=9, species="furret")
    furret._moves = {
        "tailwind": Move("tailwind", gen),
        "grassyglide": Move("grassyglide", gen),
        "gigadrain": Move("gigadrain", gen),
        "trickroom": Move("trickroom", gen),
        "quickattack": Move("quickattack", gen),
        "gigaimpact": Move("gigaimpact", gen),
        "pursuit": Move("pursuit", gen),
    }

    battle.team = {"p1: Furret": furret}

    # Test regular priorities
    assert get_priority_and_identifier(
        ["", "move", "p1a: Furret", "Trick Room"], battle
    ) == ("p1: Furret", -7)
    assert get_priority_and_identifier(
        ["", "move", "p1a: Furret", "Quick Attack", "p2b: Arceus"], battle
    ) == ("p1: Furret", 1)
    assert get_priority_and_identifier(
        ["", "move", "p1a: Furret", "Tailwind"], battle
    ) == ("p1: Furret", 0)

    # Test Pursuit
    assert get_priority_and_identifier(["", "move", "p1a: Furret", "Pursuit"], battle) == (
        "p1: Furret",
        None,
    )

    # Test Gale Wings
    furret.set_hp_status("100/100", store=True)
    furret._ability = "galewings"
    assert get_priority_and_identifier(
        ["", "move", "p1a: Furret", "Tailwind"], battle
    ) == ("p1: Furret", 1)
    furret.set_hp_status("99/100", store=True)
    assert get_priority_and_identifier(
        ["", "move", "p1a: Furret", "Tailwind"], battle
    ) == ("p1: Furret", 0)

    # Test Prankster
    furret._ability = "prankster"
    assert get_priority_and_identifier(
        ["", "move", "p1a: Furret", "Tailwind"], battle
    ) == ("p1: Furret", 1)

    # Test Mycelium Might
    furret._ability = "myceliummight"
    assert get_priority_and_identifier(
        ["", "move", "p1a: Furret", "Tailwind"], battle
    ) == ("p1: Furret", None)

    # Test Stall
    furret._ability = "stall"
    assert get_priority_and_identifier(
        ["", "move", "p1a: Furret", "Tailwind"], battle
    ) == ("p1: Furret", None)

    # Test Triage
    furret._ability = "triage"
    assert get_priority_and_identifier(
        ["", "move", "p1a: Furret", "Giga Drain"], battle
    ) == ("p1: Furret", 3)

    # Test Grassy Glide
    assert get_priority_and_identifier(
        ["", "move", "p1a: Furret", "Grassy Glide", "p2b: Arceus"], battle
    ) == ("p1: Furret", 0)
    battle._fields = {Field.GRASSY_TERRAIN: 0}
    assert get_priority_and_identifier(
        ["", "move", "p1a: Furret", "Grassy Glide", "p2b: Arceus"], battle
    ) == ("p1: Furret", 1)

    # Test various effects that should nullify priority predictions
    assert get_priority_and_identifier(
        ["", "move", "p1a: Furret", "Giga Impact"], battle
    ) == ("p1: Furret", 0)
    furret._effects = {Effect.QUASH: 1}
    assert get_priority_and_identifier(
        ["", "move", "p1a: Furret", "Giga Impact"], battle
    ) == ("p1: Furret", None)
    furret._effects = {Effect.AFTER_YOU: 1}
    assert get_priority_and_identifier(
        ["", "move", "p1a: Furret", "Giga Impact"], battle
    ) == ("p1: Furret", None)
    furret._effects = {Effect.QUICK_CLAW: 1}
    assert get_priority_and_identifier(
        ["", "move", "p1a: Furret", "Giga Impact"], battle
    ) == ("p1: Furret", None)
    furret._effects = {Effect.CUSTAP_BERRY: 1}
    assert get_priority_and_identifier(
        ["", "move", "p1a: Furret", "Giga Impact"], battle
    ) == ("p1: Furret", None)
    furret._effects = {Effect.DANCER: 1}
    assert get_priority_and_identifier(
        ["", "move", "p1a: Furret", "Giga Impact"], battle
    ) == ("p1: Furret", None)
    furret._effects = {Effect.QUICK_DRAW: 1}
    assert get_priority_and_identifier(
        ["", "move", "p1a: Furret", "Giga Impact"], battle
    ) == ("p1: Furret", None)

    # Test Lagging Tail
    furret._effects = {}
    furret._item = "laggingtail"
    assert get_priority_and_identifier(
        ["", "move", "p1a: Furret", "Giga Impact"], battle
    ) == ("p1: Furret", None)

    # Test Full Incense
    furret._item = "fullincense"
    assert get_priority_and_identifier(
        ["", "move", "p1a: Furret", "Giga Impact"], battle
    ) == ("p1: Furret", None)


def test_get_showdown_identifier():
    furret = Pokemon(gen=9, species="furret")
    calyrex = Pokemon(gen=9, species="calyrex")
    calyrexshadow = Pokemon(gen=9, species="calyrexshadow")
    weezinggalar = Pokemon(gen=9, species="weezinggalar")
    weezing = Pokemon(gen=9, species="weezing")
    wochien = Pokemon(gen=9, species="wochien")
    assert get_showdown_identifier(furret, "p1") == "p1: Furret"
    assert get_showdown_identifier(calyrex, "p1") == "p1: Calyrex"
    assert get_showdown_identifier(calyrexshadow, "p1") == "p1: Calyrex"
    assert get_showdown_identifier(weezinggalar, "p1") == "p1: Weezing"
    assert get_showdown_identifier(weezing, "p1") == "p1: Weezing"
    assert get_showdown_identifier(wochien, "p2") == "p2: Wo-Chien"

    with pytest.raises(ValueError):
        get_showdown_identifier(furret, None)