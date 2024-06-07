# -*- coding: utf-8 -*-
"""This module defines a random players baseline
"""

import datetime
import re

# -*- coding: utf-8 -*-
from logging import Logger
from typing import Any, Dict, Iterator, List, Optional, Union

import orjson
from poke_env.data import GenData
from poke_env.environment.battle import Battle
from poke_env.environment.double_battle import DoubleBattle
from poke_env.environment.move import Move
from poke_env.environment.observed_pokemon import ObservedPokemon
from poke_env.environment.pokemon import Pokemon
from poke_env.environment.pokemon_gender import PokemonGender
from poke_env.environment.pokemon_type import PokemonType
from poke_env.stats import compute_raw_stats

from elitefurretai.model_utils.battle_data import BattleData


class DataProcessor:
    _omniscient: bool = False
    _double_data: bool = False
    _gen_data: Dict[int, GenData] = {}
    _write_tag: str = "eliteFurretAIGenerated"

    def __init__(self, omniscient: bool = False, double_data: bool = False):
        self._omniscient = omniscient
        self._double_data = double_data

    def stream_data(self, files: List[str]) -> Iterator[BattleData]:
        for filepath in files:
            with open(filepath, "r") as f:
                json = orjson.loads(f.read())
                yield self.json_to_battledata(json, perspective="p1")
                if self._double_data:
                    yield self.json_to_battledata(json, perspective="p2")

    def load_data(self, files: List[str]) -> Dict[str, BattleData]:
        data = {}
        for bd in self.stream_data(files):
            data[bd.roomid] = bd

        return data

    def json_to_battledata(
        self, battle_json: Dict[str, Any], perspective: str = "p1"
    ) -> BattleData:

        # Generate battle from JSON file
        battle = self.json_to_battle(battle_json, perspective)

        # Create metadata from hash, may create collissions, but it's necessary
        # without storing these directly in a DB
        hashed_roomid = "battle-{format}{num}".format(
            format=battle.format, num=hash(str(battle_json) + perspective)
        )

        # Load any necessary data
        if battle.gen not in self._gen_data:
            self._gen_data[battle.gen] = GenData.from_gen(battle.gen)

        # Prepare variables
        can_see_p1_team = perspective == "p1" or self._omniscient
        can_see_p2_team = perspective == "p2" or self._omniscient
        p1_team: List[ObservedPokemon] = []
        p2_team: List[ObservedPokemon] = []
        p1_teampreview_team: List[ObservedPokemon] = []
        p2_teampreview_team: List[ObservedPokemon] = []

        # If this module wrote the json
        if battle_json.get(self._write_tag, False):

            p1_teampreview_team = self._prepare_team(
                battle_json.get("p1teampreviewteam", []), battle.gen, can_see_p1_team
            )
            p2_teampreview_team = self._prepare_team(
                battle_json.get("p2teampreviewteam", []), battle.gen, can_see_p2_team
            )
            p1_team = self._prepare_team(
                battle_json.get("p1team", []), battle.gen, can_see_p1_team
            )
            p2_team = self._prepare_team(
                battle_json.get("p2team", []), battle.gen, can_see_p2_team
            )

        # If Showdown wrote the json
        else:
            p1_teampreview_team = self._prepare_team(
                battle_json["p1team"], battle.gen, can_see_p1_team
            )
            p2_teampreview_team = self._prepare_team(
                battle_json["p2team"], battle.gen, can_see_p2_team
            )
            for log in battle_json["inputLog"]:
                if ">p1 team" in log:
                    choices = map(
                        lambda x: int(x) - 1, log.replace(">p1 team ", "").split(", ")
                    )
                    team = [battle_json["p1team"][choice] for choice in choices]
                    p1_team = self._prepare_team(
                        team_list=team, gen=battle.gen, omniscient=can_see_p1_team
                    )
                elif ">p2 team" in log:
                    choices = map(
                        lambda x: int(x) - 1, log.replace(">p2 team ", "").split(", ")
                    )
                    team = [battle_json["p2team"][choice] for choice in choices]
                    p2_team = self._prepare_team(
                        team_list=team, gen=battle.gen, omniscient=can_see_p2_team
                    )

        return BattleData(
            roomid=battle_json.get("roomid", hashed_roomid),
            format=battle_json["format"],
            p1=battle_json["p1"],
            p2=battle_json["p2"],
            p1rating=battle_json["p1rating"],
            p2rating=battle_json["p2rating"],
            p1_teampreview_team=p1_teampreview_team,
            p2_teampreview_team=p2_teampreview_team,
            p1_team=p1_team,
            p2_team=p2_team,
            score=battle_json["score"],
            winner=battle_json["winner"],
            end_type=battle_json["endType"],
            observations=battle.observations,
        )

    @staticmethod
    def json_to_battle(
        battle_json, perspective: str = "p1"
    ) -> Union[Battle, DoubleBattle]:
        match = re.match("(gen[0-9])", str(battle_json.get("format")))
        if match is None:
            raise ValueError(
                "Could not parse gen from battle json's format: {format}".format(
                    format=battle_json.get("format")
                )
            )
        gen = int(match.groups()[0][-1])

        battle = None
        if "vgc" in str(battle_json.get("format")) or "doubles" in str(
            battle_json.get("format")
        ):
            battle = DoubleBattle(
                "tag", battle_json[perspective], Logger("elitefurretai"), gen=gen
            )
        else:
            battle = Battle(
                "tag", battle_json[perspective], Logger("elitefurretai"), gen=gen
            )

        battle.player_role = perspective
        battle.opponent_username = battle_json["p2" if perspective == "p1" else "p1"]

        logs = battle_json["log"]
        for log in logs:
            split_message = log.split("|")

            # Implement parts that parse_message can't deal with
            if (
                len(split_message) == 1
                or split_message == ["", ""]
                or split_message[1] == "t:"
            ):
                continue
            elif split_message[1] == "win":
                battle.won_by(split_message[2])
            elif split_message[1] == "tie":
                battle.tied()
            else:
                battle.parse_message(split_message)

        return battle

    def _prepare_team(
        self, team_list: List[Dict[str, Any]], gen: int, omniscient: bool = False
    ) -> List[ObservedPokemon]:

        team = []
        for mon_info in team_list:
            team.append(self._prepare_mon(mon_info, gen, omniscient))

        return team

    def _prepare_mon(
        self, mon_info: Dict[str, Any], gen: int, omniscient: bool = False
    ) -> ObservedPokemon:
        species = mon_info["species"].lower().replace("-", "").replace(" ", "")

        ability = None
        tera = None
        item = None
        moves = {}
        stats = ObservedPokemon.initial_stats()

        if omniscient:
            # Get stats if EliteFurretAI wrote the stats, otherwise use official data format
            stats = mon_info.get("stats")
            if stats is None:
                stats = dict(
                    zip(
                        ["hp", "atk", "def", "spa", "spd", "spe"],
                        compute_raw_stats(
                            species,
                            list(mon_info["evs"].values()),
                            list(mon_info["ivs"].values()),
                            mon_info["level"],
                            mon_info.get("nature", "serious").lower(),
                            self._gen_data[gen],
                        ),
                    )
                )

            # These are things we wouldn't know if we don't have omniscience
            ability = mon_info["ability"]
            if "teraType" in mon_info:
                tera = PokemonType.from_name(str(mon_info.get("teraType")))
            item = mon_info["item"]
            moves = {str(m): Move(m, gen=gen) for m in mon_info["moves"]}

        gender = None
        if mon_info.get("gender", None) == "M":
            gender = PokemonGender.MALE
        elif mon_info.get("gender", None) == "F":
            gender = PokemonGender.FEMALE
        else:
            gender = PokemonGender.NEUTRAL

        return ObservedPokemon(
            species=species,
            stats=stats,
            moves=moves,
            ability=ability,
            item=item,
            gender=gender,
            tera_type=tera,
            shiny=mon_info.get("shiny", None),
            level=mon_info["level"],
        )

    # Return -1 on evs and ivs, because it's near impossible to recreate stats in a time-efficient way
    # Instead, I just write the stats directly
    @staticmethod
    def pokemon_to_json(mon: Pokemon) -> Dict[str, Any]:
        stats: Dict[str, Optional[int]] = {"hp": mon.max_hp}
        if mon.stats:
            stats.update(mon.stats)

        return {
            "name": mon.species,
            "species": mon.species,
            "item": mon.item,
            "ability": mon.ability,
            "moves": list(mon.moves.keys()),
            "nature": "serious",
            "evs": {"hp": -1, "atk": -1, "def": -1, "spa": -1, "spd": -1, "spe": -1},
            "ivs": {"hp": -1, "atk": -1, "def": -1, "spa": -1, "spd": -1, "spe": -1},
            "stats": stats,
        }

    # I write stats and teampreview differently
    def battle_to_json(self, battle: Union[Battle, DoubleBattle]) -> bytes:

        p1team = battle.team if battle.player_role == "p1" else battle.opponent_team
        p2team = battle.opponent_team if battle.player_role == "p1" else battle.team
        p1teampreviewteam = (
            battle.teampreview_team
            if battle.player_role == "p1"
            else battle.opponent_teampreview_team
        )
        p2teampreviewteam = (
            battle.opponent_teampreview_team
            if battle.player_role == "p1"
            else battle.teampreview_team
        )

        json = {
            "winner": battle.player_username if battle.won else battle.opponent_username,
            "turns": battle.turn,
            "p1": (
                battle.player_username
                if battle.player_role == "p1"
                else battle.opponent_username
            ),
            "p2": (
                battle.opponent_username
                if battle.player_role == "p1"
                else battle.player_username
            ),
            "p1team": [
                DataProcessor.pokemon_to_json(mon) for species, mon in p1team.items()
            ],
            "p2team": [
                DataProcessor.pokemon_to_json(mon) for species, mon in p2team.items()
            ],
            "p1teampreviewteam": [
                DataProcessor.pokemon_to_json(mon)
                for species, mon in p1teampreviewteam.items()
            ],
            "p2teampreviewteam": [
                DataProcessor.pokemon_to_json(mon)
                for species, mon in p2teampreviewteam.items()
            ],
            "score": [
                len(list(filter(lambda x: not x[1].fainted, p1team.items()))),
                len(list(filter(lambda x: not x[1].fainted, p2team.items()))),
            ],
            "inputLog": None,
            "log": [
                "|".join(split_message)
                for turn in sorted(battle.observations.keys())
                for split_message in battle.observations[turn].events
            ],
            "p1rating": None,
            "p2rating": None,
            "endType": (  # Don't yet have ability to tell if forfeited
                "normal" if battle.won else "forced"
            ),
            "ladderError": False,
            "timestamp": datetime.datetime.now().strftime("%a %b %d %Y %H:%M:%S GMT%z"),
            self._write_tag: True,
            "format": battle.format,
            "id": battle.battle_tag,
        }

        return orjson.dumps(json)

    @property
    def omniscient(self) -> bool:
        """
        :return: Whether the BattleData object should know hidden information
            from the opponents (eg has omniscient view). This only applies to data
            that has omniscient perspective to begin with.
        :rtype: bool
        """
        return self._omniscient

    @property
    def double_data(self) -> bool:
        """
        :return: Whether we should return two BattleData objects for each battle.
            One for each player's perspective (to get double the data)
        :rtype: bool
        """
        return self._double_data
