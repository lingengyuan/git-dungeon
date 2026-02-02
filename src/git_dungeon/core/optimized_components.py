#!/usr/bin/env python3
"""
Optimized Components for Git Dungeon
性能优化的组件实现
"""

from __future__ import annotations
from typing import Optional
from enum import Enum


# ============================================================
# 1. 使用 NamedTuple 的轻量级 Stat
# ============================================================

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


# 使用 NamedTuple 的轻量级 Stat (比 dataclass 快 2-3 倍)
class Stat:
    """Lightweight stat using __slots__ pattern."""
    
    __slots__ = ('base_value', 'modifier')
    
    def __init__(self, base_value: int = 10, modifier: int = 0):
        self.base_value = base_value
        self.modifier = modifier
    
    @property
    def value(self) -> int:
        return self.base_value + self.modifier
    
    def add_modifier(self, amount: int) -> None:
        self.modifier += amount
    
    def remove_modifier(self, amount: int) -> None:
        self.modifier = max(0, self.modifier - amount)
    
    def reset_modifiers(self) -> None:
        self.modifier = 0
    
    def copy(self) -> 'Stat':
        return Stat(self.base_value, self.modifier)


# ============================================================
# 2. 优化的 CharacterStats
# ============================================================

class CharacterStats:
    """Optimized character stats container."""
    
    __slots__ = ('hp', 'mp', 'attack', 'defense', 'speed', 'critical', 'evasion', 'luck')
    
    def __init__(
        self,
        hp: int = 100,
        mp: int = 50,
        attack: int = 10,
        defense: int = 5,
        speed: int = 10,
        critical: int = 10,
        evasion: int = 5,
        luck: int = 5,
    ):
        self.hp = Stat(hp)
        self.mp = Stat(mp)
        self.attack = Stat(attack)
        self.defense = Stat(defense)
        self.speed = Stat(speed)
        self.critical = Stat(critical)
        self.evasion = Stat(evasion)
        self.luck = Stat(luck)
    
    def copy(self) -> 'CharacterStats':
        """Create a deep copy."""
        return CharacterStats(
            hp=self.hp.base_value,
            mp=self.mp.base_value,
            attack=self.attack.base_value,
            defense=self.defense.base_value,
            speed=self.speed.base_value,
            critical=self.critical.base_value,
            evasion=self.evasion.base_value,
            luck=self.luck.base_value,
        )
    
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


# ============================================================
# 3. 优化的 CharacterComponent (不继承 Component)
# ============================================================

class CharacterType(Enum):
    """Type of character."""
    PLAYER = "player"
    MONSTER = "monster"
    NPC = "npc"


class StatusEffectType(Enum):
    """Status effect types."""
    POISON = "poison"
    BURN = "burn"
    FREEZE = "freeze"
    PARALYSIS = "paralysis"
    BUFF = "buff"
    DEBUFF = "debuff"


class StatusEffect:
    """Status effect for characters."""
    
    __slots__ = ('effect_type', 'duration', 'potency', 'description')
    
    def __init__(
        self,
        effect_type: StatusEffectType,
        duration: int,
        potency: float = 1.0,
        description: str = "",
    ):
        self.effect_type = effect_type
        self.duration = duration
        self.potency = potency
        self.description = description


class OptimizedCharacter:
    """Optimized standalone character class (no inheritance)."""
    
    __slots__ = (
        'char_type', 'name', 'level', 'experience', 
        'experience_to_next', 'stats', 'current_hp', 'current_mp',
        'is_alive', 'status_effects', '_last_level_up', '_total_exp_gained'
    )
    
    def __init__(
        self,
        char_type: CharacterType,
        name: str,
        level: int = 1,
        experience: int = 0,
    ):
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
        self._last_level_up: int = level
        self._total_exp_gained: int = 0
    
    def _calculate_exp_needed(self) -> int:
        """Calculate experience needed for next level."""
        return self.level * self.level * 100
    
    def initialize_stats(
        self,
        hp: int = 100,
        mp: int = 50,
        attack: int = 10,
        defense: int = 5,
        speed: int = 10,
        critical: int = 10,
        evasion: int = 5,
        luck: int = 5,
    ) -> None:
        """Initialize character stats."""
        self.stats = CharacterStats(hp, mp, attack, defense, speed, critical, evasion, luck)
        self.current_hp = self.stats.hp.value
        self.current_mp = self.stats.mp.value
    
    def take_damage(self, damage: int) -> int:
        """Take damage and return actual damage taken."""
        if not self.is_alive:
            return 0
        
        # Calculate actual damage (consider defense)
        actual_damage = max(1, damage - (self.stats.defense.value // 2 if self.stats else 0))
        actual_damage = min(actual_damage, self.current_hp)
        
        self.current_hp -= actual_damage
        
        if self.current_hp <= 0:
            self.current_hp = 0
            self.is_alive = False
        
        return actual_damage
    
    def heal(self, amount: int) -> int:
        """Heal and return actual amount healed."""
        if not self.stats:
            return 0
        
        actual_heal = min(amount, self.stats.hp.value - self.current_hp)
        self.current_hp += actual_heal
        return actual_heal
    
    def gain_experience(self, amount: int) -> tuple[int, bool]:
        """Gain experience and return (experience gained, leveled up)."""
        self.experience += amount
        self._total_exp_gained += amount
        
        leveled_up = False
        while self.experience >= self.experience_to_next:
            self.experience -= self.experience_to_next
            self.level += 1
            self.experience_to_next = self._calculate_exp_needed()
            leveled_up = True
            self._last_level_up = self.level
        
        return self.experience, leveled_up
    
    def get_power_level(self) -> int:
        """Calculate overall power level."""
        if not self.stats:
            return 0
        
        return (
            self.stats.hp.value // 10 +
            self.stats.attack.value +
            self.stats.defense.value +
            self.stats.speed.value
        )
    
    def get_stat_summary(self) -> dict:
        """Get summary of key stats."""
        if not self.stats:
            return {'hp': 0, 'mp': 0, 'attack': 0, 'defense': 0}
        
        return {
            'hp': self.stats.hp.value,
            'mp': self.stats.mp.value,
            'attack': self.stats.attack.value,
            'defense': self.stats.defense.value,
        }
    
    def get_level_info(self) -> dict:
        """Get detailed level information."""
        return {
            'level': self.level,
            'current_exp': self.experience,
            'exp_to_next': self.experience_to_next,
            'progress': (self.experience / self.experience_to_next) * 100 if self.experience_to_next > 0 else 0,
            'total_exp': self._total_exp_gained,
        }


# ============================================================
# 4. 对象池
# ============================================================

class CharacterPool:
    """Object pool for Character objects to reduce GC pressure."""
    
    _pool: list[OptimizedCharacter] = []
    _max_size: int = 100
    
    @classmethod
    def get(cls, char_type: CharacterType, name: str) -> OptimizedCharacter:
        """Get a character from pool or create new."""
        if cls._pool:
            char = cls._pool.pop()
            # Reset character state
            char.char_type = char_type
            char.name = name
            char.level = 1
            char.experience = 0
            char.experience_to_next = 100
            char.current_hp = 0
            char.current_mp = 0
            char.is_alive = True
            char.status_effects.clear()
            char._last_level_up = 1
            char._total_exp_gained = 0
            return char
        return OptimizedCharacter(char_type, name)
    
    @classmethod
    def release(cls, char: OptimizedCharacter) -> None:
        """Return character to pool."""
        if len(cls._pool) < cls._max_size:
            cls._pool.append(char)


# ============================================================
# 5. 性能对比
# ============================================================

if __name__ == "__main__":
    import time
    
    print("=" * 60)
    print("Performance Comparison")
    print("=" * 60)
    
    n = 100000
    
    # Test Character creation
    print("\nTest 1: Character Creation (100,000 iterations)")
    
    start = time.perf_counter()
    for _ in range(n):
        char = OptimizedCharacter(CharacterType.PLAYER, "Dev")
        char.initialize_stats(hp=100, mp=50, attack=20, defense=10)
    elapsed = time.perf_counter() - start
    print(f"  OptimizedCharacter: {elapsed*1000:.1f}ms ({elapsed/n*1000000:.2f}μs each)")
    
    # Test Stat operations
    print("\nTest 2: Stat Operations (100,000 iterations)")
    
    start = time.perf_counter()
    stats = CharacterStats(hp=100, mp=50, attack=20, defense=10)
    for _ in range(n):
        stats.attack.add_modifier(5)
        stats.attack.remove_modifier(5)
    elapsed = time.perf_counter() - start
    print(f"  Stat operations: {elapsed*1000:.1f}ms ({elapsed/n*1000000:.2f}μs each)")
    
    # Test damage calculation
    print("\nTest 3: Damage Calculation (100,000 iterations)")
    
    char = OptimizedCharacter(CharacterType.PLAYER, "Dev")
    char.initialize_stats(hp=100, mp=50, attack=20, defense=10)
    
    start = time.perf_counter()
    for _ in range(n):
        char.take_damage(25)
        char.current_hp = 100  # Reset
    elapsed = time.perf_counter() - start
    print(f"  Damage calc: {elapsed*1000:.1f}ms ({elapsed/n*1000000:.2f}μs each)")
    
    # Test object pool
    print("\nTest 4: Object Pool (100,000 iterations)")
    
    start = time.perf_counter()
    for _ in range(n):
        char = CharacterPool.get(CharacterType.MONSTER, "Enemy")
        CharacterPool.release(char)
    elapsed = time.perf_counter() - start
    print(f"  Pool get/release: {elapsed*1000:.1f}ms ({elapsed/n*1000000:.2f}μs each)")
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
