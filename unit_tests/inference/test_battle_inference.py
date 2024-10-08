# -*- coding: utf-8 -*-
from unittest.mock import MagicMock

from elitefurretai.inference.battle_inference import BattleInference


def test_battle_inference():
    mock = MagicMock()
    mock.gen = 9
    mock.player_username = "elitefurretai"
    battle_inference = BattleInference(mock)
    assert battle_inference
