# engine.py - Core game engine (M1: 战斗状态机 + 敌人意图)

from dataclasses import dataclass
from typing import List, Tuple, Optional
from datetime import datetime

from .model import (
    GameState, EnemyState, ChapterState, Action,
    IntentType, EnemyIntent
)
from .events import (
    GameEvent, EventType,
    battle_started, damage_dealt,
    exp_gained, level_up,
    enemy_defeated, chapter_completed
)
from .rng import RNG, DefaultRNG
from .rules.combat_rules import CombatRules
from .rules.progression_rules import ProgressionRules


@dataclass
class Engine:
    """
    Core game engine - pure logic layer (M1: 战斗状态机).
    
    M1 战斗流程: start_turn -> draw_phase -> player_action -> enemy_intent -> resolve -> end_turn
    
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
        """Apply an action to the game state."""
        events = []
        
        handler_name = f"_handle_{action.action_type}_action"
        handler = getattr(self, handler_name, self._handle_unknown_action)
        
        new_state, action_events = handler(state, action)
        events.extend(action_events)
        
        new_state.updated_at = datetime.now().isoformat()
        
        return new_state, events
    
    # ==================== M1 战斗状态机 ====================
    
    def _handle_combat_action(
        self,
        state: GameState,
        action: Action
    ) -> Tuple[GameState, List[GameEvent]]:
        """Handle combat-related actions (M1: 扩展支持状态机)"""
        events = []
        action_name = action.action_name
        
        # M1: 回合开始
        if action_name == "start_turn":
            return self._start_turn(state)
        
        # M1: 抽牌
        if action_name == "draw_card":
            return self._draw_cards(state, action.data.get("count", 5))
        
        # M1: 出牌
        if action_name == "play_card":
            return self._play_card(state, action.data.get("card_index", 0))
        
        # M1: 结束回合
        if action_name == "end_turn":
            return self._end_turn(state)
        
        # M1: 生成敌人意图
        if action_name == "plan_enemy_intent":
            return self._plan_enemy_intent(state)
        
        # 原有战斗逻辑（向后兼容）
        if action_name == "start_combat":
            return self._start_combat_legacy(state)
        
        if action_name == "attack":
            return self._attack(state)
        
        if action_name == "defend":
            return self._defend(state)
        
        if action_name == "skill":
            return self._skill(state, action)
        
        if action_name == "escape":
            return self._escape(state)
        
        return state, [GameEvent(
            type=EventType.ERROR,
            data={"message": f"Unknown combat action: {action_name}"}
        )]
    
    def _start_turn(self, state: GameState) -> Tuple[GameState, List[GameEvent]]:
        """M1: 回合开始 - 重置能量、抽牌、生成敌人意图"""
        events = []
        
        if not state.in_combat:
            return state, [GameEvent(
                type=EventType.ERROR,
                data={"message": "Not in combat"}
            )]
        
        # 回合数+1
        state.turn_number += 1
        state.turn_phase = "player"
        
        # 重置能量
        state.player.energy.start_turn()
        
        # 抽牌 (默认5张)
        draw_count = 5 + state.player.character.statuses.get("focus", 0)
        drawn, remaining = state.player.deck.draw(draw_count)
        
        events.append(GameEvent(
            type=EventType.TURN_STARTED,
            data={
                "turn_number": state.turn_number,
                "cards_drawn": len(drawn),
                "energy": state.player.energy.current_energy
            }
        ))
        
        # 生成敌人意图
        intent = self._generate_enemy_intent(state)
        if state.current_enemy:
            state.current_enemy.intent = intent
        
        return state, events
    
    def _draw_cards(self, state: GameState, count: int) -> Tuple[GameState, List[GameEvent]]:
        """M1: 抽牌"""
        events = []
        
        if not state.in_combat:
            return state, [GameEvent(
                type=EventType.ERROR,
                data={"message": "Not in combat"}
            )]
        
        drawn, remaining = state.player.deck.draw(count)
        
        events.append(GameEvent(
            type=EventType.CARDS_DRAWN,
            data={
                "count": len(drawn),
                "hand_size": len(state.player.deck.hand)
            }
        ))
        
        return state, events
    
    def _play_card(self, state: GameState, card_index: int) -> Tuple[GameState, List[GameEvent]]:
        """M1: 出牌"""
        events = []
        
        if not state.in_combat:
            return state, [GameEvent(
                type=EventType.ERROR,
                data={"message": "Not in combat"}
            )]
        
        deck = state.player.deck
        
        if card_index < 0 or card_index >= len(deck.hand):
            return state, [GameEvent(
                type=EventType.ERROR,
                data={"message": "Invalid card index"}
            )]
        
        card = deck.hand[card_index]
        
        # 检查能量 (简化: 默认费用1)
        cost = 1  # 从 card 数据获取
        
        if not state.player.energy.consume(cost):
            return state, [GameEvent(
                type=EventType.ERROR,
                data={"message": "Not enough energy"}
            )]
        
        # 出牌
        played_card = deck.play_card(card_index)
        
        events.append(GameEvent(
            type=EventType.CARD_PLAYED,
            data={
                "card_id": played_card.card_id if played_card else "unknown",
                "cost": cost,
                "energy_remaining": state.player.energy.current_energy
            }
        ))
        
        # 执行卡牌效果 (简化: 基础攻击)
        if state.current_enemy:
            damage = 6  # 从 card.effects 计算
            actual_damage = state.current_enemy.take_damage(damage)
            
            events.append(damage_dealt(
                src=state.player.character.entity_id,
                src_type="player",
                dst=state.current_enemy.entity_id,
                dst_type="enemy",
                amount=actual_damage,
                is_critical=False
            ))
            
            # 检查敌人是否死亡
            if not state.current_enemy.is_alive:
                events.extend(self._handle_enemy_defeated(state, state.current_enemy))
                state.in_combat = False
                state.current_enemy = None
        
        return state, events
    
    def _end_turn(self, state: GameState) -> Tuple[GameState, List[GameEvent]]:
        """M1: 回合结束 - 弃牌、触发状态、敌人行动"""
        events = []
        
        if not state.in_combat:
            return state, [GameEvent(
                type=EventType.ERROR,
                data={"message": "Not in combat"}
            )]
        
        state.turn_phase = "enemy"
        
        # 弃置手牌
        discarded = state.player.deck.discard_hand()
        
        # 回合结束状态结算
        self._tick_statuses(state.player.character, is_enemy_turn=False)
        
        events.append(GameEvent(
            type=EventType.TURN_ENDED,
            data={
                "cards_discarded": len(discarded),
                "turn_number": state.turn_number
            }
        ))
        
        # 敌人行动
        if state.current_enemy and state.current_enemy.is_alive:
            events.extend(self._execute_enemy_action(state))
        
        return state, events
    
    def _generate_enemy_intent(self, state: GameState) -> Optional[EnemyIntent]:
        """M1: 生成敌人意图"""
        if not state.current_enemy:
            return None
        
        enemy = state.current_enemy
        turn = state.turn_number
        
        # 基于回合数选择意图
        intent_map = {
            1: IntentType.ATTACK,
            2: IntentType.DEFEND,
            3: IntentType.ATTACK,
            4: IntentType.BUFF,
            5: IntentType.ATTACK,
        }
        
        intent_type = intent_map.get(turn % 5 + 1, IntentType.ATTACK)
        
        # 计算数值
        value = enemy.attack
        if intent_type == IntentType.DEFEND:
            value = 5 + turn
        
        return EnemyIntent(intent_type=intent_type, value=value)
    
    def _plan_enemy_intent(self, state: GameState) -> Tuple[GameState, List[GameEvent]]:
        """M1: 规划敌人意图"""
        events = []
        
        if state.current_enemy:
            intent = self._generate_enemy_intent(state)
            state.current_enemy.intent = intent
            
            events.append(GameEvent(
                type=EventType.ENEMY_INTENT_REVEALED,
                data={
                    "enemy_id": state.current_enemy.entity_id,
                    "intent": intent.to_dict() if intent else None
                }
            ))
        
        return state, events
    
    def _execute_enemy_action(self, state: GameState) -> List[GameEvent]:
        """M1: 执行敌人行动"""
        events = []
        
        enemy = state.current_enemy
        if not enemy or not enemy.is_alive:
            return events
        
        intent = enemy.intent
        
        if intent is None:
            # 默认攻击
            intent = EnemyIntent(IntentType.ATTACK, value=enemy.attack)
        
        # 执行意图
        if intent.intent_type == IntentType.ATTACK:
            # 攻击
            damage = intent.value
            actual_damage = state.player.character.take_damage(damage)
            
            events.append(damage_dealt(
                src=enemy.entity_id,
                src_type="enemy",
                dst=state.player.character.entity_id,
                dst_type="player",
                amount=actual_damage
            ))
            
            # 检查玩家死亡
            if not state.player.character.is_alive:
                state.is_game_over = True
                state.is_victory = False
                events.append(GameEvent(
                    type=EventType.GAME_ENDED,
                    data={"result": "defeat"}
                ))
        
        elif intent.intent_type == IntentType.DEFEND:
            # 防御
            enemy.block = intent.value
            events.append(GameEvent(
                type=EventType.STATUS_APPLIED,
                data={"target": enemy.entity_id, "status": "block", "value": enemy.block}
            ))
        
        elif intent.intent_type == IntentType.DEBUFF:
            # 上 debuff
            status = intent.status or "vulnerable"
            stacks = intent.status_value
            state.player.character.statuses[status] = \
                state.player.character.statuses.get(status, 0) + stacks
            events.append(GameEvent(
                type=EventType.STATUS_APPLIED,
                data={"target": "player", "status": status, "value": stacks}
            ))
        
        # 清除临时状态
        enemy.block = 0
        
        return events
    
    def _tick_statuses(self, character, is_enemy_turn: bool = True) -> None:
        """M1: 状态回合结算"""
        statuses = character.statuses
        
        # 清除回合结束状态
        if "block" in statuses:
            del statuses["block"]
        
        # 燃烧每回合掉血
        if "burn" in statuses:
            burn_stacks = statuses.get("burn", 0)
            if burn_stacks > 0:
                character.current_hp = max(0, character.current_hp - burn_stacks)
                if character.current_hp <= 0:
                    character.is_alive = False
        
        # 减少持续回合状态
        for status in ["vulnerable", "weak", "charge", "focus"]:
            if status in statuses:
                statuses[status] = max(0, statuses[status] - 1)
                if statuses[status] == 0:
                    del statuses[status]
    
    # ==================== 原有战斗逻辑（向后兼容）=================
    
    def _start_combat_legacy(self, state: GameState) -> Tuple[GameState, List[GameEvent]]:
        """原有战斗开始（兼容旧代码，M1: 初始化套牌）"""
        events = []
        
        if state.in_combat:
            return state, [GameEvent(
                type=EventType.ERROR,
                data={"message": "Already in combat"}
            )]
        
        enemy = self._create_enemy_from_commit(state)
        if enemy is None:
            return state, [GameEvent(
                type=EventType.ERROR,
                data={"message": "No enemy to fight"}
            )]
        
        # M1: 初始化玩家套牌（如果为空）
        if state.player.deck.total_cards == 0:
            from git_dungeon.engine.model import CardInstance
            starter_cards = [
                "strike", "strike", "strike",
                "defend", "defend", "defend"
            ]
            state.player.deck.draw_pile = [
                CardInstance(card_id=card_id) for card_id in starter_cards
            ]
        
        state.in_combat = True
        state.current_enemy = enemy
        state.turn_number = 1
        
        events.append(battle_started(
            enemy_id=enemy.entity_id,
            enemy_name=enemy.name,
            hp=enemy.current_hp,
            max_hp=enemy.max_hp
        ))
        
        return state, events
    
    def _attack(self, state: GameState) -> Tuple[GameState, List[GameEvent]]:
        """攻击"""
        events = []
        
        if not state.in_combat or not state.current_enemy:
            return state, [GameEvent(type=EventType.ERROR, data={"message": "Not in combat"})]
        
        player = state.player.character
        enemy = state.current_enemy
        
        is_critical, multiplier = self.combat_rules.roll_critical(
            player.stats.critical.value, 1.5
        )
        damage = int((player.stats.attack.value + 5) * multiplier)
        actual_damage = enemy.take_damage(damage)
        
        events.append(damage_dealt(
            src=player.entity_id, src_type="player",
            dst=enemy.entity_id, dst_type="enemy",
            amount=actual_damage, is_critical=is_critical
        ))
        
        if not enemy.is_alive:
            events.extend(self._handle_enemy_defeated(state, enemy))
            state.in_combat = False
            state.current_enemy = None
        
        return state, events
    
    def _defend(self, state: GameState) -> Tuple[GameState, List[GameEvent]]:
        """防御"""
        events = []
        
        if not state.in_combat:
            return state, [GameEvent(type=EventType.ERROR, data={"message": "Not in combat"})]
        
        # M1: 使用 Block 状态
        state.player.character.statuses["block"] = \
            state.player.character.statuses.get("block", 0) + 5
        
        events.append(GameEvent(
            type=EventType.STATUS_APPLIED,
            data={"target": "player", "status": "block", "value": 5}
        ))
        
        return state, events
    
    def _skill(self, state: GameState, action: Action) -> Tuple[GameState, List[GameEvent]]:
        """技能"""
        events = []
        
        if not state.in_combat or not state.current_enemy:
            return state, [GameEvent(type=EventType.ERROR, data={"message": "Not in combat"})]
        
        mp_cost = action.data.get("mp_cost", 10)
        if not state.player.character.consume_mp(mp_cost):
            return state, [GameEvent(type=EventType.ERROR, data={"message": "Not enough MP"})]
        
        player = state.player.character
        enemy = state.current_enemy
        
        is_critical, multiplier = self.combat_rules.roll_critical(
            player.stats.critical.value, 2.0
        )
        damage = int((player.stats.attack.value + 5) * 2 * multiplier)
        actual_damage = enemy.take_damage(damage)
        
        events.append(GameEvent(type=EventType.PLAYER_ACTION, data={"action": "skill"}))
        events.append(damage_dealt(
            src=player.entity_id, src_type="player",
            dst=enemy.entity_id, dst_type="enemy",
            amount=actual_damage, is_critical=is_critical
        ))
        
        if not enemy.is_alive:
            events.extend(self._handle_enemy_defeated(state, enemy))
            state.in_combat = False
            state.current_enemy = None
        
        return state, events
    
    def _escape(self, state: GameState) -> Tuple[GameState, List[GameEvent]]:
        """逃跑"""
        events = []
        
        if not state.in_combat:
            return state, [GameEvent(type=EventType.ERROR, data={"message": "Not in combat"})]
        
        if self.combat_rules.roll_escape(0.7):
            events.append(GameEvent(type=EventType.BATTLE_ENDED, data={"result": "escaped"}))
            state.in_combat = False
            state.current_enemy = None
        else:
            events.append(GameEvent(type=EventType.ERROR, data={"message": "Escape failed"}))
        
        return state, events
    
    # ==================== 其他 Action Handler ====================
    
    def _handle_chapter_action(
        self,
        state: GameState,
        action: Action
    ) -> Tuple[GameState, List[GameEvent]]:
        """Handle chapter-related actions"""
        events = []
        action_name = action.action_name
        
        if action_name == "start_chapter":
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
                data={"chapter_id": chapter.chapter_id, "chapter_name": chapter.chapter_name}
            ))
            
        elif action_name == "complete_chapter":
            if state.current_chapter:
                state.current_chapter.is_completed = True
                state.chapters_completed.append(state.current_chapter.chapter_id)
                
                gold_reward = self.progression_rules.calculate_chapter_gold(state.current_chapter.chapter_index)
                exp_reward = self.progression_rules.calculate_chapter_exp(state.current_chapter.chapter_index)
                
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
                        new_level=new_level, old_level=new_level - 1,
                        hp_gain=stats["hp_gain"], mp_gain=stats["mp_gain"],
                        atk_gain=stats["atk_gain"], def_gain=stats["def_gain"]
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
                    data={"item_id": item.get("id"), "item_name": item.get("name"), "price": price}
                ))
            else:
                events.append(GameEvent(type=EventType.ERROR, data={"message": "Not enough gold"}))
        
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
        """Create enemy state from commit"""
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
                new_level=new_level, old_level=new_level - 1,
                hp_gain=stats["hp_gain"], mp_gain=stats["mp_gain"],
                atk_gain=stats["atk_gain"], def_gain=stats["def_gain"]
            ))
        
        state.player.gold += enemy.gold_reward
        events.append(GameEvent(
            type=EventType.GOLD_GAINED,
            data={"amount": enemy.gold_reward, "reason": "enemy_defeated"}
        ))
        
        events.append(enemy_defeated(
            enemy_id=enemy.entity_id,
            enemy_name=enemy.name,
            enemy_type=enemy.enemy_type,
            exp_reward=enemy.exp_reward,
            gold_reward=enemy.gold_reward
        ))
        
        if state.current_chapter:
            state.current_chapter.enemies_defeated += 1
        
        return events
