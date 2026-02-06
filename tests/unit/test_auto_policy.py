"""Unit tests for deterministic auto-combat policy."""

from git_dungeon.engine.auto_policy import (
    ACTION_ATTACK,
    ACTION_DEFEND,
    AutoCombatContext,
    RuleBasedAutoPolicy,
)


def _base_context() -> AutoCombatContext:
    return AutoCombatContext(
        seed=2026,
        turn_number=2,
        player_hp=70,
        player_max_hp=100,
        player_mp=20,
        player_attack=12,
        enemy_hp=40,
        enemy_max_hp=80,
        enemy_attack_hint=15,
        skill_mp_cost=10,
        skill_damage_bonus=5,
        can_escape=True,
        is_boss=False,
        threat_hint=False,
    )


def test_policy_is_deterministic_for_same_seed_and_state() -> None:
    """Same input context should always produce the same choice."""
    policy = RuleBasedAutoPolicy()
    ctx = _base_context()
    first = policy.choose_action(ctx)
    for _ in range(10):
        assert policy.choose_action(ctx) == first


def test_low_hp_prefers_defend() -> None:
    """Low HP + high incoming threat should choose defensive action."""
    policy = RuleBasedAutoPolicy()
    ctx = _base_context()
    low_hp_ctx = AutoCombatContext(
        seed=ctx.seed,
        turn_number=ctx.turn_number,
        player_hp=15,
        player_max_hp=100,
        player_mp=ctx.player_mp,
        player_attack=ctx.player_attack,
        enemy_hp=ctx.enemy_hp,
        enemy_max_hp=ctx.enemy_max_hp,
        enemy_attack_hint=55,
        skill_mp_cost=ctx.skill_mp_cost,
        skill_damage_bonus=ctx.skill_damage_bonus,
        can_escape=False,
        is_boss=True,
        threat_hint=True,
    )
    assert policy.choose_action(low_hp_ctx) == ACTION_DEFEND


def test_low_mp_falls_back_to_attack() -> None:
    """When skill cost is not affordable, policy should use conservative attack."""
    policy = RuleBasedAutoPolicy()
    ctx = _base_context()
    low_mp_ctx = AutoCombatContext(
        seed=ctx.seed,
        turn_number=ctx.turn_number,
        player_hp=ctx.player_hp,
        player_max_hp=ctx.player_max_hp,
        player_mp=3,
        player_attack=ctx.player_attack,
        enemy_hp=ctx.enemy_hp,
        enemy_max_hp=ctx.enemy_max_hp,
        enemy_attack_hint=ctx.enemy_attack_hint,
        skill_mp_cost=10,
        skill_damage_bonus=ctx.skill_damage_bonus,
        can_escape=False,
        is_boss=False,
        threat_hint=False,
    )
    assert policy.choose_action(low_mp_ctx) == ACTION_ATTACK

