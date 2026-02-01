# engine.py - Core game engine (pure logic, no I/O)

from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime

from .model import GameState, PlayerState, EnemyState, ChapterState, Action
from .events import (
    GameEvent, EventType,
    battle_started, damage_dealt,
    exp_gained, level_up,
    enemy_defeated, item_dropped,
    chapter_completed, error,
    player_action, gold_gained, status_applied,
    chapter_started, game_ended
)
from .rng import RNG, DefaultRNG
from .rules.combat_rules import CombatRules
from .rules.progression_rules import ProgressionRules


@dataclass
class Engine:
    """
    Core game engine - pure logic layer.
    
    Input: Player action + RNG + current state
    Output: New state + list of GameEvent[]
    
    All rules are deterministic and testable.
    """
    
    rng: RNG = None
    save_version: int = 2
    
    def __post_init__(self):
        if self.rng is None:
            self.rng = DefaultRNG()
        self.combat_rules = CombatRules(rng=self.rng)
        self.progression_rules = ProgressionRules(rng=self.rng)
    
    def apply(
        self,
        state: GameState,
        action: Action
    ) -> Tuple[GameState, List[GameEvent]]:
        """
        Apply an action to the game state.
        
        Args:
            state: Current game state
            action: Player action to apply
            
        Returns:
            Tuple of (new_state, events)
        """
        events = []
        
        # Route to appropriate handler
        handler_name = f"_handle_{action.action_type}_action"
        handler = getattr(self, handler_name, self._handle_unknown_action)
        
        new_state, action_events = handler(state, action)
        events.extend(action_events)
        
        # Update timestamp
        new_state.updated_at = datetime.now().isoformat()
        
        return new_state, events
    
    def _handle_combat_action(
        self,
        state: GameState,
        action: Action
    ) -> Tuple[GameState, List[GameEvent]]:
        """Handle combat-related actions"""
        events = []
        action_name = action.action_name
        
        player = state.player.character
        
        # Start combat if not in combat
        if action_name == "start_combat":
            if state.in_combat:
                return state, [GameEvent(
                    type=EventType.ERROR,
                    data={"message": "Already in combat"}
                )]
            
            # Create enemy from commit (would need commit info passed in)
            enemy = self._create_enemy_from_commit(state)
            if enemy is None:
                return state, [GameEvent(
                    type=EventType.ERROR,
                    data={"message": "No enemy to fight"}
                )]
            
            state.in_combat = True
            state.current_enemy = enemy
            
            events.append(battle_started(
                enemy_id=enemy.entity_id,
                enemy_name=enemy.name,
                hp=enemy.current_hp,
                max_hp=enemy.max_hp
            ))
            
            return state, events
        
        # Handle combat actions
        if not state.in_combat:
            return state, [GameEvent(
                type=EventType.ERROR,
                data={"message": "Not in combat"}
            )]
        
        enemy = state.current_enemy
        if enemy is None:
            return state, [GameEvent(
                type=EventType.ERROR,
                data={"message": "No enemy"}
            )]
        
        # Player turn
        if action_name == "attack":
            # Calculate damage
            is_critical, multiplier = self.combat_rules.roll_critical(
                player.stats.critical.value, 1.5
            )
            base_damage = player.stats.attack.value + 5
            damage = int(base_damage * multiplier)
            
            # Apply damage to enemy
            actual_damage = enemy.take_damage(damage)
            
            events.append(damage_dealt(
                src=player.entity_id,
                src_type="player",
                dst=enemy.entity_id,
                dst_type="enemy",
                amount=actual_damage,
                is_critical=is_critical
            ))
            
            # Check if enemy defeated
            if not enemy.is_alive:
                events.extend(self._handle_enemy_defeated(state, enemy))
                state.in_combat = False
                state.current_enemy = None
                state.enemies_defeated.append(enemy.commit_hash)
            
        elif action_name == "defend":
            # Defend reduces next damage by 50%
            player.is_defending = True
            events.append(GameEvent(
                type=EventType.STATUS_APPLIED,
                data={
                    "target": player.entity_id,
                    "status": "defending",
                    "duration": 1
                }
            ))
            
        elif action_name == "skill":
            skill_id = action.data.get("skill_id", "basic_skill")
            mp_cost = action.data.get("mp_cost", 10)
            
            if not player.consume_mp(mp_cost):
                return state, [GameEvent(
                    type=EventType.ERROR,
                    data={"message": "Not enough MP"}
                )]
            
            # Skill is 2x damage
            is_critical, multiplier = self.combat_rules.roll_critical(
                player.stats.critical.value, 2.0
            )
            base_damage = (player.stats.attack.value + 5) * 2
            damage = int(base_damage * multiplier)
            
            actual_damage = enemy.take_damage(damage)
            
            events.append(GameEvent(
                type=EventType.PLAYER_ACTION,
                data={
                    "action": "skill",
                    "skill_id": skill_id,
                    "mp_cost": mp_cost
                }
            ))
            events.append(damage_dealt(
                src=player.entity_id,
                src_type="player",
                dst=enemy.entity_id,
                dst_type="enemy",
                amount=actual_damage,
                is_critical=is_critical
            ))
            
            if not enemy.is_alive:
                events.extend(self._handle_enemy_defeated(state, enemy))
                state.in_combat = False
                state.current_enemy = None
                state.enemies_defeated.append(enemy.commit_hash)
            
        elif action_name == "escape":
            # 70% chance to escape
            if self.combat_rules.roll_escape(0.7):
                events.append(GameEvent(
                    type=EventType.BATTLE_ENDED,
                    data={"result": "escaped"}
                ))
                state.in_combat = False
                state.current_enemy = None
            else:
                events.append(GameEvent(
                    type=EventType.ERROR,
                    data={"message": "Escape failed"}
                ))
        
        # Enemy turn (if enemy still alive)
        if state.in_combat and enemy.is_alive:
            enemy_damage = enemy.attack
            
            # Apply defense if player is defending
            if getattr(player, 'is_defending', False):
                enemy_damage = enemy_damage // 2
                player.is_defending = False
            
            actual_damage = player.take_damage(enemy_damage)
            
            events.append(damage_dealt(
                src=enemy.entity_id,
                src_type="enemy",
                dst=player.entity_id,
                dst_type="player",
                amount=actual_damage
            ))
            
            # Check if player defeated
            if not player.is_alive:
                state.is_game_over = True
                state.is_victory = False
                events.append(GameEvent(
                    type=EventType.GAME_ENDED,
                    data={"result": "defeat", "enemies_defeated": len(state.enemies_defeated)}
                ))
        
        return state, events
    
    def _handle_chapter_action(
        self,
        state: GameState,
        action: Action
    ) -> Tuple[GameState, List[GameEvent]]:
        """Handle chapter-related actions"""
        events = []
        action_name = action.action_name
        
        if action_name == "start_chapter":
            # Start a new chapter
            chapter_data = action.data
            chapter = ChapterState(
                chapter_id=chapter_data.get("chapter_id", "default"),
                chapter_name=chapter_data.get("chapter_name", "Unknown"),
                chapter_index=chapter_data.get("chapter_index", 0),
                enemies_in_chapter=chapter_data.get("enemies_in_chapter", 10),
            )
            state.current_chapter = chapter
            events.append(GameEvent(
                type=EventType.CHAPTER_STARTED,
                data={
                    "chapter_id": chapter.chapter_id,
                    "chapter_name": chapter.chapter_name
                }
            ))
            
        elif action_name == "complete_chapter":
            # Chapter completed
            if state.current_chapter:
                state.current_chapter.is_completed = True
                state.chapters_completed.append(state.current_chapter.chapter_id)
                
                # Calculate rewards
                gold_reward = self.progression_rules.calculate_chapter_gold(
                    state.current_chapter.chapter_index
                )
                exp_reward = self.progression_rules.calculate_chapter_exp(
                    state.current_chapter.chapter_index
                )
                
                state.player.gold += gold_reward
                did_level_up, new_level = state.player.character.gain_experience(exp_reward)
                
                events.append(chapter_completed(
                    chapter_id=state.current_chapter.chapter_id,
                    chapter_name=state.current_chapter.chapter_name,
                    enemies_defeated=state.current_chapter.enemies_defeated,
                    gold_reward=gold_reward,
                    exp_reward=exp_reward,
                    next_chapter_id=None
                ))
                
                if did_level_up:
                    stats = self.progression_rules.calculate_level_up_stats(new_level)
                    events.append(level_up(
                        new_level=new_level,
                        old_level=new_level - 1,
                        hp_gain=stats["hp_gain"],
                        mp_gain=stats["mp_gain"],
                        atk_gain=stats["atk_gain"],
                        def_gain=stats["def_gain"]
                    ))
        
        return state, events
    
    def _handle_shop_action(
        self,
        state: GameState,
        action: Action
    ) -> Tuple[GameState, List[GameEvent]]:
        """Handle shop-related actions"""
        events = []
        action_name = action.action_name
        
        if action_name == "enter_shop":
            events.append(GameEvent(
                type=EventType.SHOP_ENTERED,
                data={"shop_id": action.data.get("shop_id", "default")}
            ))
            
        elif action_name == "buy_item":
            item = action.data.get("item")
            price = action.data.get("price", 0)
            
            if state.player.gold >= price:
                state.player.gold -= price
                state.player.inventory.append(item)
                events.append(GameEvent(
                    type=EventType.ITEM_PURCHASED,
                    data={
                        "item_id": item.get("id"),
                        "item_name": item.get("name"),
                        "price": price
                    }
                ))
            else:
                events.append(GameEvent(
                    type=EventType.ERROR,
                    data={"message": "Not enough gold"}
                ))
        
        return state, events
    
    def _handle_unknown_action(
        self,
        state: GameState,
        action: Action
    ) -> Tuple[GameState, List[GameEvent]]:
        """Handle unknown actions"""
        return state, [GameEvent(
            type=EventType.ERROR,
            data={"message": f"Unknown action type: {action.action_type}"}
        )]
    
    def _create_enemy_from_commit(self, state: GameState) -> Optional[EnemyState]:
        """Create enemy state from commit (simplified - needs commit info)"""
        # This is a placeholder - actual implementation would use commit info
        return EnemyState(
            entity_id=f"enemy_{state.current_commit_index}",
            name=f"Enemy #{state.current_commit_index}",
            enemy_type="feature",
            commit_hash="",
            commit_message="",
            current_hp=20,
            max_hp=20,
            attack=5,
            defense=2,
            exp_reward=25,
            gold_reward=10
        )
    
    def _handle_enemy_defeated(
        self,
        state: GameState,
        enemy: EnemyState
    ) -> List[GameEvent]:
        """Handle enemy being defeated"""
        events = []
        
        # Grant EXP
        did_level_up, new_level = state.player.character.gain_experience(enemy.exp_reward)
        
        events.append(exp_gained(
            amount=enemy.exp_reward,
            reason="enemy_defeated",
            total_exp=state.player.character.experience,
            exp_to_next=state.player.character.experience_to_next
        ))
        
        if did_level_up:
            stats = self.progression_rules.calculate_level_up_stats(new_level)
            events.append(level_up(
                new_level=new_level,
                old_level=new_level - 1,
                hp_gain=stats["hp_gain"],
                mp_gain=stats["mp_gain"],
                atk_gain=stats["atk_gain"],
                def_gain=stats["def_gain"]
            ))
        
        # Grant gold
        state.player.gold += enemy.gold_reward
        events.append(GameEvent(
            type=EventType.GOLD_GAINED,
            data={
                "amount": enemy.gold_reward,
                "reason": "enemy_defeated"
            }
        ))
        
        # Enemy defeated event
        events.append(enemy_defeated(
            enemy_id=enemy.entity_id,
            enemy_name=enemy.name,
            enemy_type=enemy.enemy_type,
            exp_reward=enemy.exp_reward,
            gold_reward=enemy.gold_reward
        ))
        
        # Update chapter progress
        if state.current_chapter:
            state.current_chapter.enemies_defeated += 1
        
        return events
