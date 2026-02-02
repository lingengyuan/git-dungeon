# model.py - Core data models for the game state (M1: Deck/Energy/Status)

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from enum import Enum
import uuid


# ==================== M1 新增枚举 ====================

class CardType(Enum):
    """卡牌类型"""
    ATTACK = "attack"
    SKILL = "skill"
    POWER = "power"


class StatusType(Enum):
    """状态效果类型"""
    # 进攻类
    VULNERABLE = "vulnerable"  # 易伤
    BURN = "burn"  # 灼烧
    WEAK = "weak"  # 虚弱
    
    # 防御类
    BLOCK = "block"  # 护甲
    THORNS = "thorns"  # 反伤
    
    # 资源类
    CHARGE = "charge"  # 充能
    FOCUS = "focus"  # 专注
    
    # 负面类
    TECH_DEBT = "tech_debt"  # 技术债
    BUG = "bug"  # Bug


class IntentType(Enum):
    """敌人意图类型"""
    ATTACK = "attack"
    DEFEND = "defend"
    BUFF = "buff"
    DEBUFF = "debuff"
    CHARGE = "charge"
    ESCAPE = "escape"


# ==================== 原有枚举 (保留兼容性) ====================

class EntityType(Enum):
    """Entity types in the game"""
    PLAYER = "player"
    ENEMY = "enemy"
    ITEM = "item"
    NPC = "npc"


class CombatActionType(Enum):
    """Player combat actions"""
    ATTACK = "attack"
    DEFEND = "defend"
    SKILL = "skill"
    ITEM = "item"
    ESCAPE = "escape"


class ItemRarity(Enum):
    """Item rarity levels"""
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    CORRUPTED = "corrupted"


@dataclass
class Stat:
    """A single stat value"""
    base: int
    modifier: int = 0
    
    @property
    def value(self) -> int:
        return self.base + self.modifier
    
    def add_modifier(self, amount: int) -> None:
        self.modifier += amount
    
    def remove_modifier(self, amount: int) -> None:
        self.modifier = max(0, self.modifier - amount)
    
    def reset_modifiers(self) -> None:
        self.modifier = 0


@dataclass
class Stats:
    """All character stats"""
    hp: Stat = field(default_factory=lambda: Stat(100))
    mp: Stat = field(default_factory=lambda: Stat(50))
    attack: Stat = field(default_factory=lambda: Stat(10))
    defense: Stat = field(default_factory=lambda: Stat(5))
    speed: Stat = field(default_factory=lambda: Stat(10))
    critical: Stat = field(default_factory=lambda: Stat(10))  # 0-100
    evasion: Stat = field(default_factory=lambda: Stat(5))   # 0-100
    luck: Stat = field(default_factory=lambda: Stat(5))      # 0-100


# ==================== M1 数据类 (在 CharacterState 之前定义) ====================

@dataclass
class StatusStack:
    """状态堆叠 (M1)"""
    status_type: str
    stacks: int = 1
    max_stacks: int = 999
    duration: int = -1  # -1 表示永久
    
    def add(self, amount: int = 1) -> None:
        """添加层数"""
        self.stacks = min(self.stacks + amount, self.max_stacks)
    
    def remove(self, amount: int = 1) -> None:
        """移除层数"""
        self.stacks = max(self.stacks - amount, 0)
    
    @property
    def is_active(self) -> bool:
        """是否激活"""
        return self.stacks > 0 and (self.duration == -1 or self.duration > 0)
    
    def tick(self) -> bool:
        """回合结算，返回是否应移除"""
        if self.duration > 0:
            self.duration -= 1
        return self.duration == 0


@dataclass
class CardInstance:
    """卡牌实例（运行时）"""
    card_id: str
    upgrade_level: int = 0
    is_exhausted: bool = False
    is_discarded: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "card_id": self.card_id,
            "upgrade_level": self.upgrade_level,
            "is_exhausted": self.is_exhausted,
            "is_discarded": self.is_discarded
        }


@dataclass
class DeckState:
    """套牌状态"""
    hand: List[CardInstance] = field(default_factory=list)
    draw_pile: List[CardInstance] = field(default_factory=list)
    discard_pile: List[CardInstance] = field(default_factory=list)
    exhaust_pile: List[CardInstance] = field(default_factory=list)
    
    def draw(self, count: int = 1) -> Tuple[List[CardInstance], List[CardInstance]]:
        """抽牌，返回 (drawn, remaining_draw)"""
        drawn = []
        for _ in range(count):
            if not self.draw_pile:
                if not self.discard_pile:
                    break  # 无牌可抽
                # 洗弃牌堆到抽牌堆
                self.draw_pile = self.discard_pile.copy()
                self.discard_pile = []
            
            if self.draw_pile:
                card = self.draw_pile.pop(0)
                self.hand.append(card)
                drawn.append(card)
        
        return drawn, self.draw_pile
    
    def play_card(self, card_index: int) -> Optional[CardInstance]:
        """出牌，返回打出的卡牌"""
        if 0 <= card_index < len(self.hand):
            card = self.hand.pop(card_index)
            card.is_discarded = True
            self.discard_pile.append(card)
            return card
        return None
    
    def exhaust_card(self, card_index: int) -> Optional[CardInstance]:
        """消耗牌"""
        if 0 <= card_index < len(self.hand):
            card = self.hand.pop(card_index)
            card.is_exhausted = True
            self.exhaust_pile.append(card)
            return card
        return None
    
    def discard_hand(self) -> List[CardInstance]:
        """弃置所有手牌"""
        discarded = self.hand.copy()
        for card in discarded:
            card.is_discarded = True
        self.discard_pile.extend(discarded)
        self.hand.clear()
        return discarded
    
    def reshuffle_discard(self) -> None:
        """洗混弃牌堆到抽牌堆"""
        self.draw_pile.extend(self.discard_pile)
        self.discard_pile.clear()
    
    @property
    def total_cards(self) -> int:
        """总牌数"""
        return len(self.draw_pile) + len(self.discard_pile) + len(self.hand) + len(self.exhaust_pile)


@dataclass
class EnergyState:
    """能量状态"""
    max_energy: int = 3
    current_energy: int = 3
    energy_gained_this_turn: int = 0
    
    def start_turn(self) -> None:
        """回合开始，重置能量"""
        self.current_energy = self.max_energy
        self.energy_gained_this_turn = 0
    
    def consume(self, amount: int) -> bool:
        """消耗能量"""
        if self.current_energy >= amount:
            self.current_energy -= amount
            return True
        return False
    
    def gain(self, amount: int) -> None:
        """获得能量"""
        self.current_energy += amount
        self.energy_gained_this_turn += amount
    
    @property
    def can_afford(self, cost: int) -> bool:
        """是否能支付"""
        return self.current_energy >= cost


@dataclass
class EnemyIntent:
    """敌人意图"""
    intent_type: IntentType
    value: int = 0  # 伤害值或护甲值
    status: Optional[str] = None
    status_value: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent_type": self.intent_type.value,
            "value": self.value,
            "status": self.status,
            "status_value": self.status_value
        }


@dataclass
class CharacterState:
    """Base state for any character (player or enemy)"""
    entity_id: str
    entity_type: EntityType
    name: str
    level: int = 1
    current_hp: int = 100
    current_mp: int = 50
    stats: Stats = field(default_factory=Stats)
    experience: int = 0
    experience_to_next: int = 100
    is_alive: bool = True
    # M1: 状态系统
    statuses: Dict[str, int] = field(default_factory=dict)  # status_type -> stacks
    
    def take_damage(self, amount: int) -> int:
        """Take damage, return actual damage taken (M1: 易伤 + 护甲)"""
        # M1: 护甲减免先
        block = self.statuses.get("block", 0)
        after_block = max(0, amount - block)
        
        # M1: 易伤效果 - 受伤+25%每层
        vulnerable_stacks = self.statuses.get("vulnerable", 0)
        damage_multiplier = 1.0 + (vulnerable_stacks * 0.25)
        actual = max(1, int(after_block * damage_multiplier))
        
        self.current_hp = max(0, self.current_hp - actual)
        if self.current_hp <= 0:
            self.is_alive = False
        return actual
    
    def heal(self, amount: int) -> int:
        """Heal HP, return actual healed amount"""
        actual = min(amount, self.stats.hp.value - self.current_hp)
        self.current_hp += actual
        return actual
    
    def consume_mp(self, amount: int) -> bool:
        """Consume MP, return True if successful"""
        if self.current_mp >= amount:
            self.current_mp -= amount
            return True
        return False
    
    def gain_experience(self, amount: int) -> tuple:
        """Gain experience, return (did_level_up, new_level)"""
        self.experience += amount
        leveled_up = False
        
        while self.experience >= self.experience_to_next:
            self.experience -= self.experience_to_next
            self.experience_to_next = int(self.experience_to_next * 1.5)
            self.level += 1
            leveled_up = True
        
        return leveled_up, self.level


@dataclass
class PlayerState:
    """Player game state (M1: 添加 Deck/Energy 系统)"""
    character: CharacterState = field(default_factory=lambda: CharacterState(
        entity_id="player",
        entity_type=EntityType.PLAYER,
        name="Developer"
    ))
    gold: int = 0
    inventory: List[Dict[str, Any]] = field(default_factory=list)
    equipped_weapon: Optional[Dict[str, Any]] = None
    equipped_armor: Optional[Dict[str, Any]] = None
    skills: List[str] = field(default_factory=list)  # Skill IDs
    achievements: List[str] = field(default_factory=list)
    # M1: Deck 系统
    deck: DeckState = field(default_factory=DeckState)  # 套牌状态
    energy: EnergyState = field(default_factory=EnergyState)  # 能量状态
    relics: List[str] = field(default_factory=list)  # 持有的遗物 ID 列表


@dataclass
class EnemyState:
    """Enemy game state (M1: 添加 Intent 系统)"""
    entity_id: str
    name: str
    enemy_type: str  # "feature", "bug", "merge", etc.
    commit_hash: str
    commit_message: str
    current_hp: int
    max_hp: int
    attack: int
    defense: int
    exp_reward: int
    gold_reward: int = 0
    drops: List[Dict[str, Any]] = field(default_factory=list)
    is_alive: bool = True
    is_boss: bool = False
    # M1: Intent 系统
    intent: Optional[EnemyIntent] = None  # 下回合意图
    statuses: Dict[str, int] = field(default_factory=dict)  # 状态效果
    block: int = 0  # 当前护甲
    
    def take_damage(self, amount: int) -> int:
        """Take damage, return actual damage taken"""
        # M1: 护甲减免
        actual_base = max(1, amount - self.defense)
        actual = max(0, actual_base - self.block)
        
        self.current_hp = max(0, self.current_hp - actual)
        if self.current_hp <= 0:
            self.is_alive = False
        return actual


@dataclass
class ChapterState:
    """Chapter/game mode state"""
    chapter_id: str
    chapter_name: str
    chapter_index: int  # 0-based index
    enemies_in_chapter: int
    enemies_defeated: int = 0
    is_completed: bool = False
    gold_reward: int = 0
    exp_reward: int = 0


@dataclass
class GameState:
    """Complete game state"""
    # Metadata
    game_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    save_version: int = 2  # Current save format version
    game_version: str = "2.0.0"
    seed: Optional[int] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Repository info
    repo_path: str = ""
    repo_fingerprint: str = ""  # Hash of repo for identification
    
    # Player
    player: PlayerState = field(default_factory=PlayerState)
    
    # Chapter
    current_chapter: Optional[ChapterState] = None
    current_commit_index: int = 0
    total_commits: int = 0
    
    # Combat
    current_enemy: Optional[EnemyState] = None
    in_combat: bool = False
    # M1: 战斗状态机
    turn_number: int = 0
    turn_phase: str = "player"  # "player", "enemy", "resolution"
    cards_drawn_this_turn: int = 0
    
    # Progress
    enemies_defeated: List[str] = field(default_factory=list)  # List of commit hashes
    chapters_completed: List[str] = field(default_factory=list)
    is_game_over: bool = False
    is_victory: bool = False
    
    # Settings
    difficulty: str = "normal"
    # M1: 流派倾向
    archetype_tags: List[str] = field(default_factory=list)  # 玩家选择的流派标签
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            "game_id": self.game_id,
            "save_version": self.save_version,
            "game_version": self.game_version,
            "seed": self.seed,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "repo_path": self.repo_path,
            "repo_fingerprint": self.repo_fingerprint,
            "player": {
                "character": {
                    "entity_id": self.player.character.entity_id,
                    "name": self.player.character.name,
                    "level": self.player.character.level,
                    "current_hp": self.player.character.current_hp,
                    "current_mp": self.player.character.current_mp,
                    "experience": self.player.character.experience,
                },
                "gold": self.player.gold,
                "inventory": self.player.inventory,
                "skills": self.player.skills,
            },
            "current_chapter": {
                "chapter_id": self.current_chapter.chapter_id if self.current_chapter else None,
                "chapter_name": self.current_chapter.chapter_name if self.current_chapter else None,
                "chapter_index": self.current_chapter.chapter_index if self.current_chapter else 0,
                "enemies_defeated": self.current_chapter.enemies_defeated if self.current_chapter else 0,
            } if self.current_chapter else None,
            "current_commit_index": self.current_commit_index,
            "total_commits": self.total_commits,
            "in_combat": self.in_combat,
            "enemies_defeated": len(self.enemies_defeated),
            "chapters_completed": self.chapters_completed,
            "is_game_over": self.is_game_over,
            "is_victory": self.is_victory,
            "difficulty": self.difficulty,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameState":
        """Deserialize from dict"""
        state = cls()
        state.game_id = data.get("game_id", state.game_id)
        state.save_version = data.get("save_version", state.save_version)
        state.repo_path = data.get("repo_path", "")
        return state


@dataclass
class Action:
    """Player action to be processed by the engine"""
    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action_type: str = ""  # "combat", "shop", "chapter", "ui"
    action_name: str = ""  # "attack", "defend", "buy", "continue"
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "action_name": self.action_name,
            "data": self.data,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Action":
        return cls(
            action_id=data.get("action_id", ""),
            action_type=data.get("action_type", ""),
            action_name=data.get("action_name", ""),
            data=data.get("data", {}),
            timestamp=data.get("timestamp", "")
        )
