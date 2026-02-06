"""Gameplay mutator presets."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MutatorConfig:
    """Tuning multipliers for one mutator profile."""

    id: str
    enemy_hp_multiplier: float = 1.0
    enemy_atk_multiplier: float = 1.0
    exp_multiplier: float = 1.0
    gold_multiplier: float = 1.0
    summary: str = "Standard rules"


MUTATOR_CONFIGS = {
    "none": MutatorConfig(id="none"),
    "hard": MutatorConfig(
        id="hard",
        enemy_hp_multiplier=1.25,
        enemy_atk_multiplier=1.2,
        exp_multiplier=0.9,
        gold_multiplier=0.9,
        summary="Enemies scale up, rewards scale down",
    ),
}


def get_mutator_config(mutator: str) -> MutatorConfig:
    key = mutator.strip().lower()
    if key not in MUTATOR_CONFIGS:
        supported = ", ".join(sorted(MUTATOR_CONFIGS.keys()))
        raise ValueError(f"Unknown mutator '{mutator}'. Supported values: {supported}")
    return MUTATOR_CONFIGS[key]


def apply_enemy_mutator(base_hp: int, base_atk: int, config: MutatorConfig) -> tuple[int, int]:
    hp = max(1, int(base_hp * config.enemy_hp_multiplier))
    atk = max(1, int(base_atk * config.enemy_atk_multiplier))
    return hp, atk


def apply_reward_mutator(base_exp: int, base_gold: int, config: MutatorConfig) -> tuple[int, int]:
    exp = max(0, int(base_exp * config.exp_multiplier))
    gold = max(0, int(base_gold * config.gold_multiplier))
    return exp, gold
