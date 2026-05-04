"""Shared combat step helpers for route battles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from git_dungeon.engine.auto_policy import ACTION_ATTACK, ACTION_DEFEND, ACTION_ESCAPE, ACTION_SKILL
from git_dungeon.engine.model import EnemyState, GameState
from git_dungeon.engine.rng import RNG
from git_dungeon.engine.rules.boss_rules import BossState, BossSystem
from git_dungeon.engine.rules.combat_rules import CombatRules


class EnemyLike(Protocol):
    name: str
    current_hp: int
    max_hp: int
    attack: int
    is_alive: bool

    def take_damage(self, amount: int) -> int:
        """Apply damage and return actual amount."""


@dataclass(frozen=True)
class CombatStepResult:
    action: str
    accepted: bool
    message: str
    player_damage: int = 0
    enemy_damage: int = 0
    enemy_action: str = ""
    critical: bool = False
    defended: bool = False
    escaped: bool = False
    battle_over: bool = False
    won: bool = False
    player_defeated: bool = False
    tags: tuple[str, ...] = ()


def resolve_combat_step(
    state: GameState,
    enemy: EnemyLike,
    action: str,
    *,
    rng: RNG,
    combat_rules: CombatRules,
    is_boss: bool = False,
    boss_system: BossSystem | None = None,
) -> CombatStepResult:
    """Resolve one player action plus any enemy response."""
    player = state.player.character
    tags: list[str] = []
    player_damage = 0
    enemy_damage = 0
    enemy_action = ""
    critical = False
    defended = False

    if action == ACTION_ATTACK:
        crit_mult = 1.5
        base_bonus = 10 if is_boss else 5
        critical, mult = combat_rules.roll_critical(player.stats.critical.value, crit_mult)
        player_damage = enemy.take_damage(int((player.stats.attack.value + base_bonus) * mult))
        if critical:
            tags.append("CRIT")
        if not enemy.is_alive:
            tags.append("KILL")
            return CombatStepResult(
                action=action,
                accepted=True,
                message=f"Attack hit for {player_damage}",
                player_damage=player_damage,
                critical=critical,
                battle_over=True,
                won=True,
                tags=tuple(tags),
            )
    elif action == ACTION_DEFEND:
        player.is_defending = True  # type: ignore[attr-defined]
        tags.append("DEFEND")
        defended = True
    elif action == ACTION_SKILL:
        cost = 15 if is_boss else 10
        if player.current_mp < cost:
            return CombatStepResult(
                action=action,
                accepted=False,
                message=f"Need {cost} MP, have {player.current_mp}",
            )
        player.current_mp -= cost
        base_bonus = 15 if is_boss else 5
        critical, mult = combat_rules.roll_critical(player.stats.critical.value, 2.0)
        player_damage = enemy.take_damage(int((player.stats.attack.value + base_bonus) * 2 * mult))
        if critical:
            tags.append("CRIT")
        if not enemy.is_alive:
            tags.append("KILL")
            return CombatStepResult(
                action=action,
                accepted=True,
                message=f"Skill hit for {player_damage}",
                player_damage=player_damage,
                critical=critical,
                battle_over=True,
                won=True,
                tags=tuple(tags),
            )
    elif action == ACTION_ESCAPE:
        if is_boss:
            return CombatStepResult(
                action=action,
                accepted=False,
                message="Cannot escape from Boss battle",
            )
        if combat_rules.roll_escape(0.7):
            tags.append("ESCAPE")
            state.in_combat = False
            return CombatStepResult(
                action=action,
                accepted=True,
                message="Escaped",
                escaped=True,
                battle_over=True,
                won=False,
                tags=tuple(tags),
            )
        tags.append("ESCAPE_FAIL")
    else:
        return resolve_combat_step(
            state,
            enemy,
            ACTION_ATTACK,
            rng=rng,
            combat_rules=combat_rules,
            is_boss=is_boss,
            boss_system=boss_system,
        )

    if enemy.is_alive:
        damage = _enemy_damage(state, enemy, rng, is_boss=is_boss, boss_system=boss_system)
        enemy_action = "attack"
        if getattr(player, "is_defending", False):
            damage = damage // 2
            player.is_defending = False  # type: ignore[attr-defined]
            defended = True

        enemy_damage = player.take_damage(damage)
        if player.stats.hp.value > 0 and (player.current_hp / player.stats.hp.value) <= 0.2:
            tags.append("LOW_HP")
        if not player.is_alive:
            tags.append("DEFEAT")
            return CombatStepResult(
                action=action,
                accepted=True,
                message="Player defeated",
                player_damage=player_damage,
                enemy_damage=enemy_damage,
                enemy_action=enemy_action,
                critical=critical,
                defended=defended,
                battle_over=True,
                won=False,
                player_defeated=True,
                tags=tuple(tags),
            )

    return CombatStepResult(
        action=action,
        accepted=True,
        message="Turn resolved",
        player_damage=player_damage,
        enemy_damage=enemy_damage,
        enemy_action=enemy_action,
        critical=critical,
        defended=defended,
        battle_over=False,
        won=False,
        tags=tuple(tags),
    )


def _enemy_damage(
    state: GameState,
    enemy: EnemyLike,
    rng: RNG,
    *,
    is_boss: bool,
    boss_system: BossSystem | None,
) -> int:
    if is_boss and isinstance(enemy, BossState) and boss_system is not None:
        player = state.player.character
        hp_percent = player.current_hp / player.stats.hp.value if player.stats.hp.value > 0 else 0
        action = enemy.get_next_action(rng, hp_percent)
        return max(1, boss_system.calculate_boss_damage(enemy, action) - player.stats.defense.value)
    normal_enemy = enemy
    if isinstance(normal_enemy, EnemyState):
        return normal_enemy.attack
    return max(1, int(enemy.attack))
