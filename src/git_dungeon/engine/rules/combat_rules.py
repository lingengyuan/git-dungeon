# combat_rules.py - Combat rules (pure logic, testable)

from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from git_dungeon.engine.rng import RNG, random_between, roll_chance


@dataclass
class CombatRules:
    """Combat rule system - pure logic, fully testable"""
    
    rng: RNG
    
    # Combat constants
    CRITICAL_CHANCE_BASE: float = 10.0  # Base crit chance %
    CRITICAL_MULTIPLIER: float = 1.5    # Crit damage multiplier
    EVADE_CHANCE_BASE: float = 5.0      # Base evade chance %
    
    def calculate_damage(
        self,
        attacker_attack: int,
        defender_defense: int,
        base_damage: int = 10,
        is_critical: bool = False
    ) -> int:
        """
        Calculate damage with defense reduction.
        
        Standard formula: base_damage + attack - defense
        
        Args:
            attacker_attack: Attacker's attack stat
            defender_defense: Defender's defense stat
            base_damage: Base damage from the attack
            is_critical: Whether this is a critical hit
            
        Returns:
            Final damage amount (minimum 1)
        """
        damage = base_damage + attacker_attack - defender_defense
        if is_critical:
            damage = int(damage * self.CRITICAL_MULTIPLIER)
        
        # Minimum 1 damage
        return max(1, damage)
    
    def roll_critical(self, crit_chance: float, multiplier: float = None) -> tuple:
        """
        Roll for critical hit.
        
        Args:
            crit_chance: Critical chance (0-100)
            multiplier: Optional override for crit multiplier
            
        Returns:
            (is_critical, multiplier)
        """
        if multiplier is None:
            multiplier = self.CRITICAL_MULTIPLIER
        
        is_crit = roll_chance(self.rng, crit_chance)
        return is_crit, multiplier if is_crit else 1.0
    
    def roll_evade(self, attacker_accuracy: float, defender_evasion: float) -> bool:
        """
        Roll for evasion.
        
        Args:
            attacker_accuracy: Attack accuracy chance
            defender_evasion: Defender evasion chance
            
        Returns:
            True if attack is evaded
        """
        # Hit chance = accuracy - evasion
        hit_chance = max(0, attacker_accuracy - defender_evasion)
        return not roll_chance(self.rng, hit_chance)
    
    def roll_escape(self, escape_chance: float) -> bool:
        """
        Roll for escape attempt.
        
        Args:
            escape_chance: Chance to escape (0-1)
            
        Returns:
            True if escaped successfully
        """
        return roll_chance(self.rng, escape_chance * 100)
    
    def calculate_combat_result(
        self,
        player_hp: int,
        player_atk: int,
        player_def: int,
        enemy_hp: int,
        enemy_atk: int,
        enemy_def: int,
        player_crit: float = 10.0,
        player_escape: float = 0.7
    ) -> Dict[str, Any]:
        """
        Simulate a complete combat encounter.
        
        Returns combat statistics for analysis.
        """
        result = {
            "player_wins": False,
            "turns": 0,
            "player_damage_dealt": 0,
            "player_damage_taken": 0,
            "critical_hits": 0,
            "evaded_attacks": 0,
            "escaped": False,
        }
        
        temp_player_hp = player_hp
        temp_enemy_hp = enemy_hp
        turns = 0
        escaped = False
        
        while temp_player_hp > 0 and temp_enemy_hp > 0 and turns < 100:
            turns += 1
            
            # Player turn
            is_crit, multiplier = self.roll_critical(player_crit, 1.5)
            player_dmg = self.calculate_damage(
                player_atk, enemy_def, is_crit
            )
            temp_enemy_hp = max(0, temp_enemy_hp - player_dmg)
            result["player_damage_dealt"] += player_dmg
            if is_crit:
                result["critical_hits"] += 1
            
            if temp_enemy_hp <= 0:
                result["player_wins"] = True
                break
            
            # Enemy turn
            enemy_dmg = self.calculate_damage(enemy_atk, player_def)
            temp_player_hp = max(0, temp_player_hp - enemy_dmg)
            result["player_damage_taken"] += enemy_dmg
            
            # Check for escape (every 3 turns)
            if turns % 3 == 0 and roll_chance(self.rng, player_escape * 100):
                escaped = True
                result["escaped"] = True
                break
        
        result["turns"] = turns
        result["final_player_hp"] = temp_player_hp
        result["final_enemy_hp"] = temp_enemy_hp
        
        return result
    
    def simulate_many_battles(
        self,
        player_hp: int,
        player_atk: int,
        enemy_hp: int,
        enemy_atk: int,
        num_battles: int = 1000
    ) -> Dict[str, Any]:
        """
        Simulate many battles for balance testing.
        
        Returns statistics about win rates and damage.
        """
        wins = 0
        total_damage_dealt = 0
        total_damage_taken = 0
        total_turns = 0
        
        for _ in range(num_battles):
            # Copy RNG state for each battle
            rng = self.rng.copy()
            temp_player_hp = player_hp
            temp_enemy_hp = enemy_hp
            turns = 0
            
            while temp_player_hp > 0 and temp_enemy_hp > 0 and turns < 100:
                turns += 1
                
                # Player attack
                is_crit, _ = self.roll_critical(10.0, 1.5)
                player_dmg = self.calculate_damage(player_atk, 2, is_crit)
                temp_enemy_hp = max(0, temp_enemy_hp - player_dmg)
                total_damage_dealt += player_dmg
                
                if temp_enemy_hp <= 0:
                    wins += 1
                    break
                
                # Enemy attack
                enemy_dmg = self.calculate_damage(enemy_atk, 5)
                temp_player_hp = max(0, temp_player_hp - enemy_dmg)
                total_damage_taken += enemy_dmg
                
                turns += 1
            
            total_turns += turns
        
        return {
            "win_rate": wins / num_battles,
            "avg_damage_dealt": total_damage_dealt / num_battles,
            "avg_damage_taken": total_damage_taken / num_battles,
            "avg_turns": total_turns / num_battles,
            "total_battles": num_battles,
            "total_wins": wins,
        }
