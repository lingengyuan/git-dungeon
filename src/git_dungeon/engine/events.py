# events.py - GameEvent definitions (JSON serializable, simple classes)

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List
from datetime import datetime
from enum import Enum
import uuid

if TYPE_CHECKING:
    from git_dungeon.engine.model import GameState
    from git_dungeon.engine.rng import RNG


class EventType(Enum):
    """Event types for game events (M1: 添加战斗状态机事件)"""
    # Lifecycle
    GAME_STARTED = "game_started"
    GAME_SAVED = "game_saved"
    GAME_LOADED = "game_loaded"
    GAME_ENDED = "game_ended"
    
    # Combat
    BATTLE_STARTED = "battle_started"
    BATTLE_ENDED = "battle_ended"
    PLAYER_ACTION = "player_action"
    ENEMY_ACTION = "enemy_action"
    DAMAGE_DEALT = "damage_dealt"
    STATUS_APPLIED = "status_applied"
    STATUS_REMOVED = "status_removed"
    CRITICAL_HIT = "critical_hit"
    EVADED = "evaded"
    # M1: 战斗状态机事件
    TURN_STARTED = "turn_started"
    TURN_ENDED = "turn_ended"
    CARDS_DRAWN = "cards_drawn"
    CARD_PLAYED = "card_played"
    ENEMY_INTENT_REVEALED = "enemy_intent_revealed"
    
    # Progression
    EXP_GAINED = "exp_gained"
    LEVEL_UP = "level_up"
    STAT_CHANGED = "stat_changed"
    
    # Loot & Economy
    ITEM_DROPPED = "item_dropped"
    ITEM_PICKED_UP = "item_picked_up"
    ITEM_EQUIPPED = "item_equipped"
    ITEM_CONSUMED = "item_consumed"
    GOLD_GAINED = "gold_gained"
    GOLD_SPENT = "gold_spent"
    
    # Chapter
    CHAPTER_STARTED = "chapter_started"
    CHAPTER_COMPLETED = "chapter_completed"
    ENEMY_DEFEATED = "enemy_defeated"
    
    # Shop
    SHOP_ENTERED = "shop_entered"
    SHOP_EXITED = "shop_exited"
    ITEM_PURCHASED = "item_purchased"
    ITEM_SOLD = "item_sold"
    
    # BOSS
    BOSS_SPAWNED = "boss_spawned"
    BOSS_DEFEATED = "boss_defeated"
    BOSS_ABILITY = "boss_ability"
    
    # Errors
    ERROR = "error"
    WARNING = "warning"


@dataclass
class GameEvent:
    """Game event (simple dict-based for flexibility)"""
    type: EventType
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "type": self.type.value,
            "timestamp": self.timestamp,
            "data": self.data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameEvent":
        return cls(
            type=EventType(data["type"]),
            event_id=data.get("event_id", ""),
            timestamp=data.get("timestamp", ""),
            data=data.get("data", {})
        )
    
    def summary(self) -> str:
        return f"{self.type.value}: {self._format_data()}"
    
    def _format_data(self) -> str:
        if not self.data:
            return ""
        key_parts = []
        for k, v in self.data.items():
            if isinstance(v, (int, float, str)):
                key_parts.append(f"{k}={v}")
        return ", ".join(key_parts[:3])


# Factory functions for creating events
def battle_started(enemy_id: str, enemy_name: str, hp: int, max_hp: int) -> GameEvent:
    return GameEvent(
        type=EventType.BATTLE_STARTED,
        data={
            "enemy_id": enemy_id,
            "enemy_name": enemy_name,
            "enemy_hp": hp,
            "enemy_max_hp": max_hp
        }
    )


def battle_ended(result: str, details: Dict = None) -> GameEvent:
    return GameEvent(
        type=EventType.BATTLE_ENDED,
        data={
            "result": result,
            "details": details or {}
        }
    )


def damage_dealt(
    src: str, src_type: str,
    dst: str, dst_type: str,
    amount: int,
    is_critical: bool = False,
    is_evaded: bool = False,
    status: str = None
) -> GameEvent:
    return GameEvent(
        type=EventType.DAMAGE_DEALT,
        data={
            "src": src,
            "src_type": src_type,
            "dst": dst,
            "dst_type": dst_type,
            "amount": amount,
            "is_critical": is_critical,
            "is_evaded": is_evaded,
            "status": status
        }
    )


def exp_gained(amount: int, reason: str, total_exp: int, exp_to_next: int) -> GameEvent:
    return GameEvent(
        type=EventType.EXP_GAINED,
        data={
            "amount": amount,
            "reason": reason,
            "total_exp": total_exp,
            "exp_to_next_level": exp_to_next
        }
    )


def level_up(
    new_level: int, old_level: int,
    hp_gain: int, mp_gain: int, atk_gain: int, def_gain: int,
    unlocked_skills: List[str] = None
) -> GameEvent:
    return GameEvent(
        type=EventType.LEVEL_UP,
        data={
            "new_level": new_level,
            "old_level": old_level,
            "hp_gain": hp_gain,
            "mp_gain": mp_gain,
            "atk_gain": atk_gain,
            "def_gain": def_gain,
            "unlocked_skills": unlocked_skills or []
        }
    )


def enemy_defeated(
    enemy_id: str, enemy_name: str, enemy_type: str,
    exp_reward: int = 0, gold_reward: int = 0,
    drops: List[Dict] = None
) -> GameEvent:
    return GameEvent(
        type=EventType.ENEMY_DEFEATED,
        data={
            "enemy_id": enemy_id,
            "enemy_name": enemy_name,
            "enemy_type": enemy_type,
            "exp_reward": exp_reward,
            "gold_reward": gold_reward,
            "drops": drops or []
        }
    )


def chapter_completed(
    chapter_id: str, chapter_name: str,
    enemies_defeated: int, gold_reward: int, exp_reward: int,
    next_chapter_id: str = None
) -> GameEvent:
    return GameEvent(
        type=EventType.CHAPTER_COMPLETED,
        data={
            "chapter_id": chapter_id,
            "chapter_name": chapter_name,
            "enemies_defeated": enemies_defeated,
            "gold_reward": gold_reward,
            "exp_reward": exp_reward,
            "next_chapter_id": next_chapter_id
        }
    )


def item_dropped(
    item_id: str, item_name: str, item_type: str,
    rarity: str, source: str
) -> GameEvent:
    return GameEvent(
        type=EventType.ITEM_DROPPED,
        data={
            "item_id": item_id,
            "item_name": item_name,
            "item_type": item_type,
            "rarity": rarity,
            "source": source
        }
    )


def game_saved(
    save_id: str, save_version: int, game_version: str,
    player_level: int, enemies_defeated: int, current_chapter: str
) -> GameEvent:
    return GameEvent(
        type=EventType.GAME_SAVED,
        data={
            "save_id": save_id,
            "save_version": save_version,
            "game_version": game_version,
            "player_level": player_level,
            "enemies_defeated": enemies_defeated,
            "current_chapter": current_chapter
        }
    )


def error(error_type: str, message: str, recoverable: bool = False) -> GameEvent:
    return GameEvent(
        type=EventType.ERROR,
        data={
            "error_type": error_type,
            "message": message,
            "recoverable": recoverable
        }
    )


def player_action(action: str, details: Dict = None) -> GameEvent:
    return GameEvent(
        type=EventType.PLAYER_ACTION,
        data={
            "action": action,
            "details": details or {}
        }
    )


def gold_gained(amount: int, reason: str) -> GameEvent:
    return GameEvent(
        type=EventType.GOLD_GAINED,
        data={
            "amount": amount,
            "reason": reason
        }
    )


def status_applied(target: str, status: str, duration: int = 1) -> GameEvent:
    return GameEvent(
        type=EventType.STATUS_APPLIED,
        data={
            "target": target,
            "status": status,
            "duration": duration
        }
    )


def chapter_started(chapter_id: str, chapter_name: str) -> GameEvent:
    return GameEvent(
        type=EventType.CHAPTER_STARTED,
        data={
            "chapter_id": chapter_id,
            "chapter_name": chapter_name
        }
    )


def game_ended(result: str, enemies_defeated: int = 0) -> GameEvent:
    return GameEvent(
        type=EventType.GAME_ENDED,
        data={
            "result": result,
            "enemies_defeated": enemies_defeated
        }
    )


# ==================== M2.2 事件效果系统 ====================

class EventEffectOpcode:
    """事件效果操作码常量"""
    GAIN_GOLD = "gain_gold"
    LOSE_GOLD = "lose_gold"
    HEAL = "heal"
    TAKE_DAMAGE = "take_damage"
    ADD_CARD = "add_card"
    REMOVE_CARD = "remove_card"
    UPGRADE_CARD = "upgrade_card"
    ADD_RELIC = "add_relic"
    REMOVE_RELIC = "remove_relic"
    APPLY_STATUS = "apply_status"
    TRIGGER_BATTLE = "trigger_battle"
    MODIFY_BIAS = "modify_bias"
    SET_FLAG = "set_flag"


def apply_event_choice(
    run_state: "GameState",
    choice_effects: List[Dict[str, Any]],
    rng: "RNG"
) -> Dict[str, Any]:
    """
    应用事件选择效果
    
    Args:
        run_state: 当前游戏状态
        choice_effects: 效果列表 (从 YAML 加载的 dict)
        rng: 随机数生成器
    
    Returns:
        执行结果 {"success": bool, "effects_applied": [...], "messages": [...], "state_changes": {...}}
    """
    
    result = {
        "success": True,
        "effects_applied": [],
        "messages": [],
        "state_changes": {}
    }
    
    # 确保 route_state 存在
    if run_state.route_state is None:
        run_state.route_state = {
            "current_node_id": "",
            "visited_nodes": [],
            "route_flags": {},
            "event_flags": {}
        }
    
    event_flags = run_state.route_state.setdefault("event_flags", {})
    
    for effect in choice_effects:
        opcode = effect.get("opcode", "")
        value = effect.get("value", 0)
        
        try:
            if opcode == EventEffectOpcode.GAIN_GOLD:
                amount = int(value) if isinstance(value, (int, float)) else 0
                run_state.player.gold += amount
                result["effects_applied"].append(f"gain_gold:{amount}")
                result["messages"].append(f"+{amount} 💰")
                
            elif opcode == EventEffectOpcode.LOSE_GOLD:
                amount = int(value) if isinstance(value, (int, float)) else 0
                run_state.player.gold = max(0, run_state.player.gold - amount)
                result["effects_applied"].append(f"lose_gold:{amount}")
                result["messages"].append(f"-{amount} 💰")
                
            elif opcode == EventEffectOpcode.HEAL:
                amount = int(value) if isinstance(value, (int, float)) else 0
                actual = run_state.player.character.heal(amount)
                result["effects_applied"].append(f"heal:{actual}")
                result["messages"].append(f"+{actual} ❤️")
                
            elif opcode == EventEffectOpcode.TAKE_DAMAGE:
                amount = int(value) if isinstance(value, (int, float)) else 0
                run_state.player.character.current_hp = max(
                    0, run_state.player.character.current_hp - amount
                )
                result["effects_applied"].append(f"take_damage:{amount}")
                result["messages"].append(f"-{amount} ❤️")
                
            elif opcode == EventEffectOpcode.ADD_CARD:
                card_id = str(value)
                # 添加卡牌到抽牌堆
                from git_dungeon.engine.model import CardInstance
                new_card = CardInstance(card_id=card_id, upgrade_level=0)
                run_state.player.deck.draw_pile.append(new_card)
                result["effects_applied"].append(f"add_card:{card_id}")
                result["messages"].append(f"+{card_id} 🃏")
                
            elif opcode == EventEffectOpcode.REMOVE_CARD:
                # value 可以是卡牌ID或选择条件
                card_id = str(value)
                # 从手牌、抽牌堆、弃牌堆中移除
                removed = False
                for pile_name in ["hand", "draw_pile", "discard_pile"]:
                    pile = getattr(run_state.player.deck, pile_name, [])
                    for i, card in enumerate(pile):
                        if card.card_id == card_id:
                            pile.pop(i)
                            removed = True
                            break
                    if removed:
                        break
                result["effects_applied"].append(f"remove_card:{card_id}")
                result["messages"].append(f"-{card_id} 🃏")
                
            elif opcode == EventEffectOpcode.UPGRADE_CARD:
                card_id = str(value)
                # 升级所有匹配的卡牌
                for pile_name in ["hand", "draw_pile", "discard_pile"]:
                    pile = getattr(run_state.player.deck, pile_name, [])
                    for card in pile:
                        if card.card_id == card_id:
                            card.upgrade_level = min(3, card.upgrade_level + 1)
                result["effects_applied"].append(f"upgrade_card:{card_id}")
                result["messages"].append(f"↑{card_id} 🃏")
                
            elif opcode == EventEffectOpcode.ADD_RELIC:
                relic_id = str(value)
                if relic_id not in run_state.player.relics:
                    run_state.player.relics.append(relic_id)
                    result["effects_applied"].append(f"add_relic:{relic_id}")
                    result["messages"].append(f"+{relic_id} 🛡️")
                    
            elif opcode == EventEffectOpcode.REMOVE_RELIC:
                relic_id = str(value)
                if relic_id in run_state.player.relics:
                    run_state.player.relics.remove(relic_id)
                    result["effects_applied"].append(f"remove_relic:{relic_id}")
                    result["messages"].append(f"-{relic_id} 🛡️")
                    
            elif opcode == EventEffectOpcode.APPLY_STATUS:
                status_id = str(value)
                # 应用状态
                current = run_state.player.character.statuses.get(status_id, 0)
                run_state.player.character.statuses[status_id] = current + 1
                result["effects_applied"].append(f"apply_status:{status_id}")
                result["messages"].append(f"+{status_id} 💫")
                
            elif opcode == EventEffectOpcode.TRIGGER_BATTLE:
                # 设置触发战斗标记（实际战斗在引擎中处理）
                battle_type = str(value)  # "normal" or "elite"
                event_flags["trigger_battle"] = battle_type
                result["effects_applied"].append(f"trigger_battle:{battle_type}")
                result["messages"].append(f"⚔️ {battle_type} battle")
                
            elif opcode == EventEffectOpcode.MODIFY_BIAS:
                # 格式: "archetype_id:delta"
                parts = str(value).split(":")
                archetype = parts[0]
                delta = float(parts[1]) if len(parts) > 1 else 0.1
                if "bias" not in run_state.route_state:
                    run_state.route_state["bias"] = {}
                current = run_state.route_state["bias"].get(archetype, 0.0)
                run_state.route_state["bias"][archetype] = current + delta
                result["effects_applied"].append(f"modify_bias:{archetype}:{delta}")
                result["messages"].append(f"📊 {archetype} +{delta}")
                
            elif opcode == EventEffectOpcode.SET_FLAG:
                # 格式: "key:value"
                parts = str(value).split(":", 1)
                key = parts[0]
                flag_value = parts[1] if len(parts) > 1 else True
                event_flags[key] = flag_value
                result["effects_applied"].append(f"set_flag:{key}")
                result["messages"].append(f"🔒 {key}")
                
            else:
                result["effects_applied"].append(f"unknown:{opcode}")
                result["messages"].append(f"?{opcode}")
                
        except Exception as e:
            result["success"] = False
            result["effects_applied"].append(f"error:{opcode}:{str(e)}")
            result["messages"].append(f"❌ {opcode} failed")
    
    # 更新状态变化
    result["state_changes"] = {
        "gold": run_state.player.gold,
        "hp": run_state.player.character.current_hp,
        "max_hp": run_state.player.character.stats.hp.value,
        "relics": len(run_state.player.relics),
        "total_cards": run_state.player.deck.total_cards
    }
    
    return result
