"""
Difficulty scaling rules for Git Dungeon.

Defines difficulty parameters that scale with chapter and difficulty level.
"""

from dataclasses import dataclass
from typing import Dict
from enum import Enum


class DifficultyLevel(Enum):
    """Difficulty level enum."""
    NORMAL = "normal"
    HARD = "hard"


@dataclass
class EnemyScaling:
    """Scaling parameters for enemies."""
    hp_multiplier: float = 1.0      # HP scaling per chapter
    damage_multiplier: float = 1.0  # Damage scaling per chapter
    armor_multiplier: float = 1.0   # Armor/defense scaling per chapter


@dataclass
class RewardScaling:
    """Scaling parameters for rewards."""
    gold_multiplier: float = 1.0          # Gold rewards scaling
    relic_drop_chance: float = 0.1        # Base relic drop chance
    card_reward_chance: float = 0.5       # Card reward chance
    elite_relic_bonus: float = 0.2        # Extra relic chance for elites


@dataclass
class EventScaling:
    """Scaling parameters for events."""
    risk_multiplier: float = 1.0          # Risk magnitude scaling
    reward_multiplier: float = 1.0        # Reward magnitude scaling
    heal_multiplier: float = 1.0          # Heal amount scaling


@dataclass  
class DifficultyParams:
    """Complete difficulty parameters for a chapter."""
    chapter_index: int
    difficulty: DifficultyLevel
    
    # Enemy scaling
    enemy_scaling: EnemyScaling
    
    # Reward scaling
    reward_scaling: RewardScaling
    
    # Event scaling
    event_scaling: EventScaling
    
    # Elite/Boss probability
    elite_chance: float
    boss_chance: float
    
    # Route length
    node_count: int = 10
    elite_max: int = 2
    boss_count: int = 1


# Difficulty presets for each level
DIFFICULTY_PRESETS: Dict[DifficultyLevel, Dict[int, DifficultyParams]] = {}


def _init_difficulty_presets() -> None:
    """Initialize difficulty presets for all chapters and levels."""
    for level in DifficultyLevel:
        if level == DifficultyLevel.NORMAL:
            base_enemy_hp = 1.0
            base_enemy_dmg = 1.0
            base_elite_chance = 0.15
            base_boss_chance = 0.05
            base_relic_drop = 0.10
        else:  # HARD
            base_enemy_hp = 1.3
            base_enemy_dmg = 1.2
            base_elite_chance = 0.25
            base_boss_chance = 0.08
            base_relic_drop = 0.15
        
        DIFFICULTY_PRESETS[level] = {}
        
        for chapter in range(5):  # 0-4 (5 chapters)
            chapter_mult = 1.0 + (chapter * 0.15)  # 15% scaling per chapter
            
            enemy_scale = EnemyScaling(
                hp_multiplier=base_enemy_hp * chapter_mult,
                damage_multiplier=base_enemy_dmg * (1.0 + chapter * 0.1),
            )
            
            reward_scale = RewardScaling(
                gold_multiplier=1.0 + (chapter * 0.1),
                relic_drop_chance=base_relic_drop * (1.0 + chapter * 0.1),
            )
            
            event_scale = EventScaling(
                risk_multiplier=1.0 + (chapter * 0.1),
                reward_multiplier=1.0 + (chapter * 0.1),
            )
            
            DIFFICULTY_PRESETS[level][chapter] = DifficultyParams(
                chapter_index=chapter,
                difficulty=level,
                enemy_scaling=enemy_scale,
                reward_scaling=reward_scale,
                event_scaling=event_scale,
                elite_chance=base_elite_chance * (1.0 + chapter * 0.1),
                boss_chance=base_boss_chance * (1.0 + chapter * 0.2),
                node_count=10 + chapter,  # Slightly longer per chapter
                elite_max=2 + chapter // 2,
                boss_count=1 + (chapter >= 2),
            )


_init_difficulty_presets()


def get_difficulty(chapter_index: int, level: DifficultyLevel = DifficultyLevel.NORMAL) -> DifficultyParams:
    """Get difficulty parameters for a specific chapter and level.
    
    Args:
        chapter_index: The chapter number (0-indexed)
        level: The difficulty level
        
    Returns:
        DifficultyParams for the given chapter/level
    """
    return DIFFICULTY_PRESETS[level][chapter_index]


def apply_enemy_scaling(base_hp: int, base_damage: int, params: DifficultyParams) -> tuple[int, int]:
    """Apply difficulty scaling to enemy stats.
    
    Args:
        base_hp: Base HP before scaling
        base_damage: Base damage before scaling
        params: Difficulty parameters
        
    Returns:
        Tuple of (scaled_hp, scaled_damage)
    """
    scale = params.enemy_scaling
    scaled_hp = int(base_hp * scale.hp_multiplier)
    scaled_damage = int(base_damage * scale.damage_multiplier)
    return scaled_hp, scaled_damage


def apply_reward_scaling(base_gold: int, params: DifficultyParams) -> int:
    """Apply difficulty scaling to reward amounts.
    
    Args:
        base_gold: Base gold amount before scaling
        params: Difficulty parameters
        
    Returns:
        Scaled gold amount
    """
    return int(base_gold * params.reward_scaling.gold_multiplier)


def should_spawn_elite(rng, params: DifficultyParams) -> bool:
    """Determine if an enemy should be elite based on difficulty.
    
    Args:
        rng: Random number generator
        params: Difficulty parameters
        
    Returns:
        True if should spawn elite
    """
    return rng.random() < params.elite_chance


def should_spawn_boss(rng, params: DifficultyParams) -> bool:
    """Determine if a node should be boss based on difficulty.
    
    Args:
        rng: Random number generator
        params: Difficulty parameters
        
    Returns:
        True if should spawn boss
    """
    return rng.random() < params.boss_chance
