# progression_rules.py - Progression/leveling rules (pure logic, testable)

from dataclasses import dataclass
from typing import Dict, Any

from git_dungeon.engine.rng import RNG, random_stat_bonus


@dataclass
class ProgressionRules:
    """Progression rule system - pure logic, fully testable"""
    
    rng: RNG
    
    # Leveling constants
    BASE_EXP_TO_LEVEL: int = 100
    EXP_GROWTH_FACTOR: float = 1.5
    
    # Stat growth per level
    HP_PER_LEVEL: int = 20
    MP_PER_LEVEL: int = 10
    ATK_PER_LEVEL: int = 2
    DEF_PER_LEVEL: int = 1
    
    # Chapter rewards
    BASE_CHAPTER_GOLD: int = 50
    GOLD_GROWTH_FACTOR: float = 1.2
    BASE_CHAPTER_EXP: int = 200
    EXP_GROWTH_FACTOR: float = 1.3
    
    def calculate_exp_to_next_level(self, current_level: int) -> int:
        """
        Calculate EXP required for next level.
        
        Args:
            current_level: Current level
            
        Returns:
            EXP needed for next level
        """
        return int(self.BASE_EXP_TO_LEVEL * (self.EXP_GROWTH_FACTOR ** (current_level - 1)))
    
    def calculate_level_up_stats(self, new_level: int) -> Dict[str, int]:
        """
        Calculate stat gains for leveling up.
        
        Args:
            new_level: The new level (after leveling up)
            
        Returns:
            Dictionary with stat gains
        """
        old_level = new_level - 1
        
        return {
            "hp_gain": self.HP_PER_LEVEL,
            "mp_gain": self.MP_PER_LEVEL,
            "atk_gain": self.ATK_PER_LEVEL + (new_level // 5),  # Extra ATK every 5 levels
            "def_gain": self.DEF_PER_LEVEL,
            "crit_gain": 1 if new_level % 5 == 0 else 0,  # Extra crit every 5 levels
            "speed_gain": 1 if new_level % 3 == 0 else 0,  # Extra speed every 3 levels
        }
    
    def calculate_chapter_gold(self, chapter_index: int) -> int:
        """
        Calculate gold reward for completing a chapter.
        
        Args:
            chapter_index: Chapter number (0-based)
            
        Returns:
            Gold reward amount
        """
        return int(self.BASE_CHAPTER_GOLD * (self.GOLD_GROWTH_FACTOR ** chapter_index))
    
    def calculate_chapter_exp(self, chapter_index: int) -> int:
        """
        Calculate EXP reward for completing a chapter.
        
        Args:
            chapter_index: Chapter number (0-based)
            
        Returns:
            EXP reward amount
        """
        return int(self.BASE_CHAPTER_EXP * (self.EXP_GROWTH_FACTOR ** chapter_index))
    
    def calculate_enemy_difficulty(
        self,
        commit_changes: int,
        commit_type: str,
        chapter_index: int
    ) -> Dict[str, Any]:
        """
        Calculate enemy stats based on commit characteristics.
        
        Args:
            commit_changes: Number of lines changed
            commit_type: Type of commit (feat, fix, docs, etc.)
            chapter_index: Current chapter for scaling
            
        Returns:
            Dictionary with HP, ATK, DEF, EXP, gold
        """
        # Base stats from commit changes
        base_hp = max(20, commit_changes * 2)
        base_atk = max(5, commit_changes // 5)
        base_def = max(1, commit_changes // 10)
        
        # Type modifiers
        type_modifiers = {
            "feat": {"hp": 1.0, "atk": 1.2, "def": 1.0, "exp": 1.2},
            "fix": {"hp": 0.8, "atk": 1.5, "def": 0.8, "exp": 1.5},
            "docs": {"hp": 0.5, "atk": 0.3, "def": 0.5, "exp": 0.5},
            "refactor": {"hp": 1.2, "atk": 0.8, "def": 1.5, "exp": 1.0},
            "test": {"hp": 0.7, "atk": 0.6, "def": 1.2, "exp": 0.8},
            "chore": {"hp": 0.6, "atk": 0.5, "def": 0.6, "exp": 0.6},
            "merge": {"hp": 2.0, "atk": 1.5, "def": 1.5, "exp": 2.0},
            "revert": {"hp": 1.5, "atk": 1.8, "def": 1.0, "exp": 1.8},
        }
        
        modifier = type_modifiers.get(commit_type, type_modifiers["feat"])
        
        # Apply chapter scaling
        chapter_multiplier = 1 + (chapter_index * 0.1)
        
        hp = int(base_hp * modifier["hp"] * chapter_multiplier)
        atk = int(base_atk * modifier["atk"] * chapter_multiplier)
        defense = int(base_def * modifier["def"] * chapter_multiplier)
        exp_reward = int(20 * modifier["exp"] * chapter_multiplier)
        gold_reward = int(10 * modifier["exp"] * chapter_multiplier)
        
        return {
            "hp": hp,
            "max_hp": hp,
            "attack": atk,
            "defense": defense,
            "exp_reward": exp_reward,
            "gold_reward": gold_reward,
        }
    
    def calculate_stat_with_variance(
        self,
        base: int,
        variance: float = 0.1
    ) -> int:
        """
        Calculate stat with random variance.
        
        Args:
            base: Base stat value
            variance: Variance percentage (0.1 = ±10%)
            
        Returns:
            Modified stat value
        """
        return random_stat_bonus(self.rng, base, variance)
    
    def get_total_stats_for_level(self, level: int) -> Dict[str, int]:
        """
        Get total stats for a given level.
        
        Args:
            level: Character level
            
        Returns:
            Dictionary with total stats
        """
        hp = 100 + (level - 1) * self.HP_PER_LEVEL
        mp = 50 + (level - 1) * self.MP_PER_LEVEL
        atk = 10 + (level - 1) * self.ATK_PER_LEVEL
        defense = 5 + (level - 1) * self.DEF_PER_LEVEL
        crit = 10 + (level - 1) // 5  # +1 crit every 5 levels
        evasion = 5 + (level - 1) // 5
        speed = 10 + (level - 1) // 3
        
        return {
            "hp": hp,
            "mp": mp,
            "attack": atk,
            "defense": defense,
            "critical": crit,
            "evasion": evasion,
            "speed": speed,
        }
    
    def get_exp_curve(self, max_level: int = 100) -> Dict[int, int]:
        """
        Generate full EXP curve up to max level.
        
        Args:
            max_level: Maximum level
            
        Returns:
            Dictionary mapping level -> EXP to reach that level
        """
        curve = {}
        cumulative = 0
        
        for level in range(1, max_level + 1):
            exp_for_next = self.calculate_exp_to_next_level(level)
            cumulative += exp_for_next
            curve[level] = cumulative
        
        return curve
