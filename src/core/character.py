"""Character system for players and monsters."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .component import Component
from .entity import Entity
from ..utils.exceptions import GameError


class CharacterType(Enum):
    """Type of character."""

    PLAYER = "player"
    MONSTER = "monster"
    NPC = "npc"


class StatType(Enum):
    """Character stat types."""

    HP = "hp"
    MP = "mp"
    ATTACK = "attack"
    DEFENSE = "defense"
    SPEED = "speed"
    CRITICAL = "critical"
    EVASION = "evasion"
    LUCK = "luck"


@dataclass
class Stat:
    """A character stat."""

    base_value: int
    modifier: int = 0

    @property
    def value(self) -> int:
        """Get the final value."""
        return self.base_value + self.modifier

    def add_modifier(self, amount: int) -> None:
        """Add a modifier."""
        self.modifier += amount

    def remove_modifier(self, amount: int) -> None:
        """Remove a modifier."""
        self.modifier = max(0, self.modifier - amount)

    def reset_modifiers(self) -> None:
        """Reset all modifiers."""
        self.modifier = 0


@dataclass
class CharacterStats:
    """Container for all character stats."""

    hp: Stat
    mp: Stat
    attack: Stat
    defense: Stat
    speed: Stat
    critical: Stat  # Critical hit chance (0-100)
    evasion: Stat  # Evasion chance (0-100)
    luck: Stat  # Luck factor (0-100)

    @classmethod
    def create(
        cls,
        hp: int,
        mp: int,
        attack: int,
        defense: int,
        speed: int = 10,
        critical: int = 10,
        evasion: int = 5,
        luck: int = 5,
    ) -> "CharacterStats":
        """Create character stats with base values."""
        return cls(
            hp=Stat(hp),
            mp=Stat(mp),
            attack=Stat(attack),
            defense=Stat(defense),
            speed=Stat(speed),
            critical=Stat(critical),
            evasion=Stat(evasion),
            luck=Stat(luck),
        )

    def get(self, stat_type: StatType) -> Stat:
        """Get a stat by type."""
        return getattr(self, stat_type.value)

    def total(self) -> int:
        """Get total of all stats."""
        return (
            self.hp.value
            + self.mp.value
            + self.attack.value
            + self.defense.value
            + self.speed.value
        )

    def reset(self) -> None:
        """Reset all modifiers."""
        self.hp.reset_modifiers()
        self.mp.reset_modifiers()
        self.attack.reset_modifiers()
        self.defense.reset_modifiers()
        self.speed.reset_modifiers()
        self.critical.reset_modifiers()
        self.evasion.reset_modifiers()
        self.luck.reset_modifiers()


class CharacterComponent(Component):
    """Character component for entities that are characters."""

    def __init__(
        self,
        char_type: CharacterType,
        name: str,
        level: int = 1,
        experience: int = 0,
    ):
        """Initialize character component.

        Args:
            char_type: Type of character
            name: Character name
            level: Character level
            experience: Current experience points
        """
        super().__init__()
        self.char_type = char_type
        self.name = name
        self.level = level
        self.experience = experience
        self.experience_to_next = self._calculate_exp_needed()
        self.stats: Optional[CharacterStats] = None
        self.current_hp: int = 0
        self.current_mp: int = 0
        self.is_alive: bool = True
        self.status_effects: list[StatusEffect] = []
        self._last_level_up: int = level  # Track last level for notifications
        self._total_exp_gained: int = 0  # Total experience gained (for stats)

    def _calculate_exp_needed(self) -> int:
        """Calculate experience needed for next level."""
        # Simple formula: level^2 * 100
        return self.level * self.level * 100

    def initialize_stats(
        self,
        hp: int,
        mp: int,
        attack: int,
        defense: int,
        speed: int = 10,
        critical: int = 10,
        evasion: int = 5,
        luck: int = 5,
    ) -> None:
        """Initialize character stats."""
        self.stats = CharacterStats.create(
            hp=hp,
            mp=mp,
            attack=attack,
            defense=defense,
            speed=speed,
            critical=critical,
            evasion=evasion,
            luck=luck,
        )
        self.current_hp = hp
        self.current_mp = mp

    @property
    def is_dead(self) -> bool:
        """Check if character is dead."""
        return not self.is_alive

    def take_damage(self, amount: int) -> int:
        """Take damage.

        Args:
            amount: Amount of damage

        Returns:
            Actual damage taken
        """
        if not self.is_alive:
            return 0

        # Apply defense
        actual_damage = max(1, amount - self.stats.defense.value)

        self.current_hp = max(0, self.current_hp - actual_damage)

        if self.current_hp == 0:
            self.is_alive = False

        return actual_damage

    def heal(self, amount: int) -> int:
        """Heal the character.

        Args:
            amount: Amount to heal

        Returns:
            Actual amount healed
        """
        if not self.stats:
            return 0

        actual_heal = min(amount, self.stats.hp.value - self.current_hp)
        self.current_hp += actual_heal
        return actual_heal

    def use_mp(self, amount: int) -> bool:
        """Use MP.

        Args:
            amount: MP to use

        Returns:
            True if successful, False if not enough MP
        """
        if not self.stats:
            return False

        if self.current_mp >= amount:
            self.current_mp -= amount
            return True
        return False

    def gain_experience(self, amount: int) -> tuple[int, bool]:
        """Gain experience.

        Args:
            amount: Experience gained

        Returns:
            Tuple of (experience gained, leveled up)
        """
        self._total_exp_gained += amount
        self.experience += amount
        leveled_up = False

        while self.experience >= self.experience_to_next:
            self.experience -= self.experience_to_next
            self._level_up()
            leveled_up = True

        return amount, leveled_up

    def _level_up(self) -> None:
        """Level up the character."""
        old_level = self.level
        self.level += 1
        self.experience_to_next = self._calculate_exp_needed()

        # Calculate stat increases (percentage-based)
        stat_increases = {
            'hp': 0.10,      # +10% HP
            'mp': 0.10,      # +10% MP
            'attack': 0.15,  # +15% Attack
            'defense': 0.10, # +10% Defense
            'speed': 0.05,   # +5% Speed
            'critical': 0.10, # +10% Crit chance
            'evasion': 0.10,  # +10% Evasion
            'luck': 0.10,     # +10% Luck
        }

        if self.stats:
            # Apply increases
            for stat_name, increase in stat_increases.items():
                stat = getattr(self.stats, stat_name, None)
                if stat and hasattr(stat, 'base_value'):
                    increase_amount = max(1, int(stat.base_value * increase))
                    stat.base_value += increase_amount

            # Restore to full
            self.current_hp = self.stats.hp.value
            self.current_mp = self.stats.mp.value

        # Track level up for notifications
        self._last_level_up = old_level

    def get_level_info(self) -> dict:
        """Get character level information.

        Returns:
            Dictionary with level info
        """
        return {
            'level': self.level,
            'experience': self.experience,
            'experience_to_next': self.experience_to_next,
            'progress': (
                self.experience / self.experience_to_next * 100
                if self.experience_to_next > 0 else 0
            ),
            'total_exp': self._total_exp_gained,
        }

    def get_stat_summary(self) -> dict:
        """Get summary of all stats.

        Returns:
            Dictionary with stat values
        """
        if not self.stats:
            return {}

        return {
            'hp': self.stats.hp.value,
            'max_hp': self.stats.hp.value,
            'mp': self.stats.mp.value,
            'max_mp': self.stats.mp.value,
            'attack': self.stats.attack.value,
            'defense': self.stats.defense.value,
            'speed': self.stats.speed.value,
            'critical': self.stats.critical.value,
            'evasion': self.stats.evasion.value,
            'luck': self.stats.luck.value,
        }

    def get_power_level(self) -> int:
        """Calculate overall power level.

        Returns:
            Power level as integer
        """
        if not self.stats:
            return 0

        # Weighted power calculation
        return (
            self.stats.hp.value // 10
            + self.stats.mp.value // 10
            + self.stats.attack.value * 2
            + self.stats.defense.value * 2
            + self.stats.speed.value
            + self.stats.critical.value
            + self.stats.evasion.value
            + self.stats.luck.value
        )

    def add_status_effect(self, effect: "StatusEffect") -> None:
        """Add a status effect."""
        self.status_effects.append(effect)

    def remove_status_effect(self, effect_type: type) -> bool:
        """Remove a status effect by type."""
        for i, effect in enumerate(self.status_effects):
            if isinstance(effect, effect_type):
                del self.status_effects[i]
                return True
        return False

    def update(self, delta_time: float) -> None:
        """Update character status effects."""
        # Update status effects
        for effect in self.status_effects[:]:  # Copy list to allow removal
            effect.duration -= delta_time
            if effect.duration <= 0:
                self.remove_status_effect(type(effect))


class StatusEffect:
    """Base status effect class."""

    def __init__(
        self,
        name: str,
        duration: float = 0,
        can_stack: bool = False,
    ):
        """Initialize status effect.

        Args:
            name: Effect name
            duration: Duration in seconds (0 = permanent)
            can_stack: Can multiple instances stack
        """
        self.name = name
        self.duration = duration
        self.can_stack = can_stack
        self.stacks = 1

    def on_apply(self, character: CharacterComponent) -> None:
        """Called when effect is applied."""
        pass

    def on_remove(self, character: CharacterComponent) -> None:
        """Called when effect is removed."""
        pass

    def on_tick(self, character: CharacterComponent, delta_time: float) -> None:
        """Called each update tick."""
        pass


# Convenience function to get character component
def get_character(entity: Entity) -> CharacterComponent:
    """Get character component from entity.

    Args:
        entity: Entity to get character from

    Returns:
        CharacterComponent

    Raises:
        GameError: If entity doesn't have character component
    """
    char = entity.get_component(CharacterComponent)
    if char is None:
        raise GameError(f"Entity {entity.name} is not a character")
    return char
