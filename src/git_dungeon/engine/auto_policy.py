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
