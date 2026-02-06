"""Deterministic auto-combat policy for CLI auto mode."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

ACTION_ATTACK = "1"
ACTION_DEFEND = "2"
ACTION_SKILL = "3"
ACTION_ESCAPE = "4"

ACTION_LABELS = {
    ACTION_ATTACK: "attack",
    ACTION_DEFEND: "defend",
    ACTION_SKILL: "skill",
    ACTION_ESCAPE: "escape",
}

REST_ACTION_HEAL = "heal"
REST_ACTION_FOCUS = "focus"


@dataclass(frozen=True)
class AutoPolicyConfig:
    """Policy thresholds and weights for reproducible decision making."""

    low_hp_threshold: float = 0.30
    critical_hp_threshold: float = 0.18
    high_threat_damage_ratio: float = 0.45
    danger_damage_ratio: float = 0.65
    finisher_enemy_hp_ratio: float = 0.40
    skill_damage_multiplier: float = 2.0
    attack_base_bonus: int = 5
    rest_heal_threshold: float = 0.55
    shop_gold_reserve_ratio: float = 0.35
    shop_min_score: float = 0.4
    shop_cost_weight: float = 1.2
    event_hp_weight: float = 0.20
    event_gold_weight: float = 0.05
    event_resource_weight: float = 0.8
    event_risk_penalty: float = 2.5
    event_low_hp_heal_bonus: float = 4.0
    event_low_hp_damage_penalty: float = 0.25


@dataclass(frozen=True)
class AutoCombatContext:
    """Minimal combat context consumed by an auto policy."""

    seed: int
    turn_number: int
    player_hp: int
    player_max_hp: int
    player_mp: int
    player_attack: int
    enemy_hp: int
    enemy_max_hp: int
    enemy_attack_hint: int
    skill_mp_cost: int
    skill_damage_bonus: int
    can_escape: bool
    is_boss: bool = False
    threat_hint: bool = False

    @property
    def player_hp_ratio(self) -> float:
        if self.player_max_hp <= 0:
            return 0.0
        return self.player_hp / self.player_max_hp

    @property
    def enemy_hp_ratio(self) -> float:
        if self.enemy_max_hp <= 0:
            return 0.0
        return self.enemy_hp / self.enemy_max_hp

    @property
    def can_use_skill(self) -> bool:
        return self.player_mp >= self.skill_mp_cost

    @property
    def expected_skill_damage(self) -> int:
        base = self.player_attack + self.skill_damage_bonus
        return max(1, int(base * 2))


class AutoCombatPolicy(Protocol):
    """Strategy interface for auto-combat decisions."""

    def choose_action(self, ctx: AutoCombatContext) -> str:
        """Return one action from ACTION_* constants."""


class AutoDecisionPolicy(Protocol):
    """Extensible strategy interface for combat + node decisions."""

    def choose_action(self, ctx: AutoCombatContext) -> str:
        """Return one combat action from ACTION_* constants."""

    def choose_event_choice(self, ctx: AutoEventContext) -> int:
        """Return selected event choice index."""

    def choose_rest_action(self, ctx: AutoRestContext) -> str:
        """Return one rest action from REST_ACTION_* constants."""

    def choose_shop_option(self, ctx: AutoShopContext) -> int | None:
        """Return shop option index, or None to skip purchase."""


@dataclass(frozen=True)
class AutoEventOptionContext:
    """Scored summary of one event choice."""

    choice_id: str
    hp_delta: int = 0
    gold_delta: int = 0
    resource_delta: float = 0.0
    risk_level: int = 0


@dataclass(frozen=True)
class AutoEventContext:
    """Event decision input for deterministic auto-play."""

    seed: int
    chapter_index: int
    node_index: int
    player_hp: int
    player_max_hp: int
    player_gold: int
    options: tuple[AutoEventOptionContext, ...]

    @property
    def player_hp_ratio(self) -> float:
        if self.player_max_hp <= 0:
            return 0.0
        return self.player_hp / self.player_max_hp


@dataclass(frozen=True)
class AutoRestContext:
    """Rest node decision input."""

    seed: int
    chapter_index: int
    node_index: int
    player_hp: int
    player_max_hp: int

    @property
    def player_hp_ratio(self) -> float:
        if self.player_max_hp <= 0:
            return 0.0
        return self.player_hp / self.player_max_hp


@dataclass(frozen=True)
class AutoShopOptionContext:
    """Summary of one shop offer."""

    option_id: str
    cost: int
    value_score: float
    hp_delta: int = 0


@dataclass(frozen=True)
class AutoShopContext:
    """Shop node decision input."""

    seed: int
    chapter_index: int
    node_index: int
    player_hp: int
    player_max_hp: int
    player_gold: int
    options: tuple[AutoShopOptionContext, ...]

    @property
    def player_hp_ratio(self) -> float:
        if self.player_max_hp <= 0:
            return 0.0
        return self.player_hp / self.player_max_hp


class RuleBasedAutoPolicy:
    """Simple deterministic strategy for CLI auto mode (V1)."""

    def __init__(self, config: AutoPolicyConfig | None = None) -> None:
        self.config = config or AutoPolicyConfig()

    def choose_action(self, ctx: AutoCombatContext) -> str:
        """Pick an action deterministically from the current combat context."""
        candidates = [ACTION_ATTACK, ACTION_DEFEND]
        if ctx.can_use_skill:
            candidates.append(ACTION_SKILL)
        if ctx.can_escape and not ctx.is_boss:
            candidates.append(ACTION_ESCAPE)

        scores = {action: 0.0 for action in candidates}
        scores[ACTION_ATTACK] = 1.0
        if ACTION_DEFEND in scores:
            scores[ACTION_DEFEND] = 1.1
        if ACTION_SKILL in scores:
            scores[ACTION_SKILL] = 1.4
        if ACTION_ESCAPE in scores:
            scores[ACTION_ESCAPE] = 0.4

        low_hp = ctx.player_hp_ratio <= self.config.low_hp_threshold
        critical_hp = ctx.player_hp_ratio <= self.config.critical_hp_threshold
        high_threat = self._is_high_threat(ctx)

        if low_hp and ACTION_DEFEND in scores:
            scores[ACTION_DEFEND] += 4.0
        if critical_hp and ACTION_DEFEND in scores:
            scores[ACTION_DEFEND] += 5.0
        if high_threat and ACTION_DEFEND in scores:
            scores[ACTION_DEFEND] += 4.5

        if ACTION_ESCAPE in scores and critical_hp and ctx.turn_number >= 3:
            scores[ACTION_ESCAPE] += 4.5
        if ACTION_ESCAPE in scores and low_hp and high_threat:
            scores[ACTION_ESCAPE] += 2.0

        if ACTION_SKILL in scores:
            predicted_skill_damage = max(
                1,
                int((ctx.player_attack + ctx.skill_damage_bonus) * self.config.skill_damage_multiplier),
            )
            if ctx.enemy_hp <= predicted_skill_damage:
                scores[ACTION_SKILL] += 5.0
            elif ctx.enemy_hp_ratio <= self.config.finisher_enemy_hp_ratio:
                scores[ACTION_SKILL] += 2.0
            if low_hp and high_threat:
                scores[ACTION_SKILL] -= 1.0

        if not ctx.can_use_skill:
            scores[ACTION_ATTACK] += 1.5
        if not low_hp and not high_threat:
            scores[ACTION_ATTACK] += 1.0

        best_score = max(scores.values())
        best = [action for action, score in scores.items() if score == best_score]
        return self._break_tie(best, ctx)

    def choose_event_choice(self, ctx: AutoEventContext) -> int:
        """Pick one event choice index deterministically."""
        if not ctx.options:
            return 0

        low_hp = ctx.player_hp_ratio <= self.config.low_hp_threshold
        scored: list[tuple[int, float]] = []
        for idx, option in enumerate(ctx.options):
            score = 0.0
            score += option.hp_delta * self.config.event_hp_weight
            score += option.gold_delta * self.config.event_gold_weight
            score += option.resource_delta * self.config.event_resource_weight
            score -= option.risk_level * self.config.event_risk_penalty

            if low_hp and option.hp_delta > 0:
                score += self.config.event_low_hp_heal_bonus
            if low_hp and option.hp_delta < 0:
                score -= abs(option.hp_delta) * self.config.event_low_hp_damage_penalty

            scored.append((idx, score))

        best_score = max(score for _, score in scored)
        best_indices = [idx for idx, score in scored if score == best_score]
        return self._break_index_tie(
            best_indices,
            seed=ctx.seed,
            chapter_index=ctx.chapter_index,
            node_index=ctx.node_index,
            pivot=ctx.player_hp + ctx.player_gold,
        )

    def choose_rest_action(self, ctx: AutoRestContext) -> str:
        """Select rest action from REST_ACTION_* constants."""
        if ctx.player_hp_ratio <= self.config.rest_heal_threshold:
            return REST_ACTION_HEAL
        return REST_ACTION_FOCUS

    def choose_shop_option(self, ctx: AutoShopContext) -> int | None:
        """Select a shop option index or None when skipping purchase."""
        if not ctx.options:
            return None

        low_hp = ctx.player_hp_ratio <= self.config.low_hp_threshold
        reserve_gold = 0 if low_hp else int(ctx.player_gold * self.config.shop_gold_reserve_ratio)
        affordable: list[tuple[int, AutoShopOptionContext]] = [
            (idx, option)
            for idx, option in enumerate(ctx.options)
            if option.cost <= ctx.player_gold
        ]
        if not affordable:
            return None

        scored: list[tuple[int, float]] = []
        for idx, option in affordable:
            spend_ratio = option.cost / max(1, ctx.player_gold)
            score = option.value_score - (spend_ratio * self.config.shop_cost_weight)
            if (ctx.player_gold - option.cost) < reserve_gold:
                score -= 1.5
            if low_hp and option.hp_delta > 0:
                score += 2.0
            scored.append((idx, score))

        best_idx, best_score = max(scored, key=lambda item: item[1])
        if best_score < self.config.shop_min_score:
            return None
        best_indices = [idx for idx, score in scored if score == best_score]
        return self._break_index_tie(
            best_indices,
            seed=ctx.seed,
            chapter_index=ctx.chapter_index,
            node_index=ctx.node_index,
            pivot=ctx.player_gold + ctx.player_hp,
            fallback=best_idx,
        )

    def _is_high_threat(self, ctx: AutoCombatContext) -> bool:
        if ctx.threat_hint:
            return True
        if ctx.player_max_hp <= 0:
            return True
        incoming_ratio = ctx.enemy_attack_hint / ctx.player_max_hp
        if incoming_ratio >= self.config.high_threat_damage_ratio:
            return True
        if ctx.player_hp > 0 and (ctx.enemy_attack_hint / ctx.player_hp) >= self.config.danger_damage_ratio:
            return True
        return False

    @staticmethod
    def _break_tie(candidates: list[str], ctx: AutoCombatContext) -> str:
        if len(candidates) == 1:
            return candidates[0]
        ordered = sorted(candidates)
        stable_value = (
            (ctx.seed * 131)
            + (ctx.turn_number * 17)
            + (ctx.player_hp * 7)
            + (ctx.enemy_hp * 11)
        )
        return ordered[stable_value % len(ordered)]

    @staticmethod
    def _break_index_tie(
        candidates: list[int],
        *,
        seed: int,
        chapter_index: int,
        node_index: int,
        pivot: int,
        fallback: int = 0,
    ) -> int:
        if not candidates:
            return fallback
        if len(candidates) == 1:
            return candidates[0]
        ordered = sorted(candidates)
        stable_value = (seed * 131) + (chapter_index * 17) + (node_index * 19) + (pivot * 7)
        return ordered[stable_value % len(ordered)]
