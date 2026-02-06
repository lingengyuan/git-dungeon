"""Unit tests for deterministic auto-combat policy."""

from git_dungeon.engine.auto_policy import (
    ACTION_ATTACK,
    ACTION_DEFEND,
    AutoCombatContext,
    AutoEventContext,
    AutoEventOptionContext,
    AutoRestContext,
    AutoShopContext,
    AutoShopOptionContext,
    REST_ACTION_HEAL,
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


def test_event_policy_prefers_healing_when_low_hp() -> None:
    policy = RuleBasedAutoPolicy()
    ctx = AutoEventContext(
        seed=42,
        chapter_index=1,
        node_index=2,
        player_hp=18,
        player_max_hp=100,
        player_gold=40,
        options=(
            AutoEventOptionContext(choice_id="heal", hp_delta=20, gold_delta=0, resource_delta=0.0, risk_level=0),
            AutoEventOptionContext(choice_id="greed", hp_delta=-10, gold_delta=30, resource_delta=0.0, risk_level=1),
        ),
    )
    assert policy.choose_event_choice(ctx) == 0


def test_rest_policy_uses_heal_under_threshold() -> None:
    policy = RuleBasedAutoPolicy()
    ctx = AutoRestContext(
        seed=1,
        chapter_index=0,
        node_index=3,
        player_hp=35,
        player_max_hp=100,
    )
    assert policy.choose_rest_action(ctx) == REST_ACTION_HEAL


def test_shop_policy_skips_when_affordable_value_is_too_low() -> None:
    policy = RuleBasedAutoPolicy()
    ctx = AutoShopContext(
        seed=2026,
        chapter_index=0,
        node_index=4,
        player_hp=80,
        player_max_hp=100,
        player_gold=90,
        options=(
            AutoShopOptionContext(option_id="tiny", cost=70, value_score=0.1, hp_delta=0),
            AutoShopOptionContext(option_id="minor", cost=50, value_score=0.2, hp_delta=0),
        ),
    )
    assert policy.choose_shop_option(ctx) is None
