"""Combat system for the game."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .character import get_character, StatType
from .entity import Entity
from git_dungeon.config import GameConfig
from git_dungeon.utils.exceptions import GameError
from git_dungeon.utils.logger import setup_logger

logger = setup_logger(__name__)


class DamageType(Enum):
    """Types of damage."""

    PHYSICAL = "physical"
    MAGICAL = "magical"
    TRUE = "true"  # Ignores defense


class CombatResult(Enum):
    """Combat result types."""

    PLAYER_WIN = "player_win"
    ENEMY_WIN = "enemy_win"
    DRAW = "draw"
    ESCAPE = "escape"


@dataclass
class CombatAction:
    """Represents a combat action."""

    action_type: str  # "attack", "skill", "item", "defend", "escape"
    source: Entity
    target: Entity
    damage: int = 0
    healing: int = 0
    mp_cost: int = 0
    description: str = ""
    is_critical: bool = False
    is_evaded: bool = False
    status_effects: list = field(default_factory=list)


class CombatSystem:
    """System for handling combat between entities."""

    def __init__(self, config: Optional[GameConfig] = None):
        """Initialize combat system.

        Args:
            config: Game configuration
        """
        self.config = config or GameConfig()
        self.combat_log: list[CombatAction] = []
        self.current_combat: Optional[CombatEncounter] = None

    def start_combat(
        self,
        player: Entity,
        enemy: Entity,
    ) -> "CombatEncounter":
        """Start a combat encounter.

        Args:
            player: Player entity
            enemy: Enemy entity

        Returns:
            CombatEncounter instance
        """
        self.current_combat = CombatEncounter(
            combat_system=self,
            player=player,
            enemy=enemy,
        )
        return self.current_combat

    def calculate_damage(
        self,
        attacker: Entity,
        defender: Entity,
        base_damage: int,
        damage_type: DamageType = DamageType.PHYSICAL,
        critical_chance: Optional[float] = None,
    ) -> tuple[int, bool]:
        """Calculate damage between attacker and defender.

        Args:
            attacker: Attacking entity
            defender: Defending entity
            base_damage: Base damage value
            damage_type: Type of damage
            critical_chance: Override critical chance

        Returns:
            Tuple of (damage, is_critical)
        """
        attacker_char = get_character(attacker)
        defender_char = get_character(defender)

        # Get attack stat
        attack_stat = attacker_char.stats.get(StatType.ATTACK)
        defense_stat = defender_char.stats.get(StatType.DEFENSE)

        # Calculate base damage with attack
        damage = base_damage + attack_stat.value

        # Apply defense (unless true damage)
        if damage_type != DamageType.TRUE:
            damage = max(1, damage - defense_stat.value)

        # Check for critical hit
        is_critical = False
        crit_chance = critical_chance if critical_chance is not None else 0

        if attacker_char.stats:
            crit_chance = attacker_char.stats.critical.value / 100

        import random

        if random.random() < crit_chance:
            damage = round(damage * 1.5)
            is_critical = True

        # Apply luck modifier
        if attacker_char.stats:
            luck_mod = attacker_char.stats.luck.value / 100
            damage = round(damage * (1 + luck_mod * 0.1))

        return damage, is_critical

    def check_evasion(self, attacker: Entity, defender: Entity) -> bool:
        """Check if defender evades the attack.

        Args:
            attacker: Attacking entity
            defender: Defending entity

        Returns:
            True if attack is evaded
        """
        defender_char = get_character(defender)

        if not defender_char.stats:
            return False

        evasion = defender_char.stats.evasion.value
        import random

        return random.random() < (evasion / 100)

    def execute_action(
        self,
        action: CombatAction,
    ) -> CombatResult:
        """Execute a combat action.

        Args:
            action: Combat action to execute

        Returns:
            CombatResult
        """
        self.combat_log.append(action)

        # Check for evasion first
        if self.check_evasion(action.source, action.target):
            action.is_evaded = True
            return CombatResult.DRAW

        # Apply damage
        if action.damage > 0:
            target_char = get_character(action.target)
            target_char.take_damage(action.damage)

        # Apply healing
        if action.healing > 0:
            source_char = get_character(action.source)
            source_char.heal(action.healing)

        # Check if target is dead
        target_char = get_character(action.target)
        if target_char.is_dead:
            return CombatResult.PLAYER_WIN

        return CombatResult.DRAW

    def get_combat_summary(self) -> dict:
        """Get a summary of the current combat."""
        if not self.current_combat:
            return {}

        player_char = get_character(self.current_combat.player)
        enemy_char = get_character(self.current_combat.enemy)

        return {
            "player_hp": player_char.current_hp,
            "player_max_hp": player_char.stats.hp.value if player_char.stats else 0,
            "player_mp": player_char.current_mp,
            "player_max_mp": player_char.stats.mp.value if player_char.stats else 0,
            "enemy_hp": enemy_char.current_hp,
            "enemy_max_hp": enemy_char.stats.hp.value if enemy_char.stats else 0,
            "enemy_name": enemy_char.name,
            "turn": self.current_combat.turn_number,
            "log_count": len(self.combat_log),
        }


class CombatEncounter:
    """Represents an active combat encounter."""

    def __init__(
        self,
        combat_system: CombatSystem,
        player: Entity,
        enemy: Entity,
    ):
        """Initialize combat encounter.

        Args:
            combat_system: Combat system reference
            player: Player entity
            enemy: Enemy entity
        """
        self.combat_system = combat_system
        self.player = player
        self.enemy = enemy
        self.turn_number = 1
        self.turn_phase: str = "player"  # "player", "enemy", "resolution"
        self.ended: bool = False
        self.result: Optional[CombatResult] = None

    @property
    def is_player_turn(self) -> bool:
        """Check if it's player's turn."""
        return self.turn_phase == "player"

    def player_action(self, action: str, **kwargs) -> CombatResult:
        """Execute a player action.

        Args:
            action: Action type
            **kwargs: Action parameters (source, target, damage, healing, etc.)

        Returns:
            CombatResult
        """
        if self.turn_phase != "player":
            raise GameError("Not player's turn")

        # Create action - use kwargs for source/target if provided
        combat_action = CombatAction(
            action_type=action,
            source=kwargs.get("source", self.player),
            target=kwargs.get("target", self.enemy),
            damage=kwargs.get("damage", 0),
            healing=kwargs.get("healing", 0),
            description=kwargs.get("description", ""),
        )

        # Execute action
        result = self.combat_system.execute_action(combat_action)

        # Check if combat ended
        if result == CombatResult.PLAYER_WIN:
            self.end_combat(result)
            return result

        # Next phase
        self.turn_phase = "enemy"
        return result

    def enemy_turn(self) -> CombatResult:
        """Execute enemy turn.

        Returns:
            CombatResult
        """
        if self.turn_phase != "enemy":
            raise GameError("Not enemy's turn")

        enemy_char = get_character(self.enemy)

        # Simple AI: attack player
        damage = enemy_char.stats.attack.value if enemy_char.stats else 10

        combat_action = CombatAction(
            action_type="attack",
            source=self.enemy,
            target=self.player,
            damage=damage,
            description=f"{enemy_char.name} attacks!",
        )

        result = self.combat_system.execute_action(combat_action)

        if result == CombatResult.PLAYER_WIN:
            # Enemy won, so player lost
            self.end_combat(CombatResult.ENEMY_WIN)
            return CombatResult.ENEMY_WIN

        # Next turn
        self.turn_phase = "player"
        self.turn_number += 1
        return CombatResult.DRAW

    def end_combat(self, result: CombatResult) -> None:
        """End the combat encounter.

        Args:
            result: Final combat result
        """
        self.ended = True
        self.result = result
        self.turn_phase = "resolution"

        # Grant experience if player won
        if result == CombatResult.PLAYER_WIN:
            enemy_char = get_character(self.enemy)
            player_entity = get_character(self.player)
            player_entity.gain_experience(enemy_char.experience)

        # Note: game_state.current_combat is cleared by game_engine.player_action

    def get_state(self) -> dict:
        """Get current combat state."""
        return {
            "turn_number": self.turn_number,
            "turn_phase": self.turn_phase,
            "ended": self.ended,
            "result": self.result.value if self.result else None,
        }
