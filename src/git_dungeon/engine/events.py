# events.py - GameEvent definitions (JSON serializable, simple classes)

from dataclasses import dataclass, field
from typing import Any, Dict, List
from datetime import datetime
from enum import Enum
import uuid


class EventType(Enum):
    """Event types for game events"""
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
