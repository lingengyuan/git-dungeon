"""Tests for mutator presets."""

from git_dungeon.engine.mutators import (
    apply_enemy_mutator,
    apply_reward_mutator,
    get_mutator_config,
)


def test_hard_mutator_scales_enemy_and_rewards() -> None:
    hard = get_mutator_config("hard")
    hp, atk = apply_enemy_mutator(100, 20, hard)
    exp, gold = apply_reward_mutator(80, 50, hard)

    assert hp == 125
    assert atk == 24
    assert exp == 72
    assert gold == 45


def test_unknown_mutator_raises_clear_error() -> None:
    try:
        get_mutator_config("nightmare")
    except ValueError as exc:
        message = str(exc)
        assert "nightmare" in message
        assert "hard" in message
    else:
        raise AssertionError("Expected ValueError for unknown mutator")
