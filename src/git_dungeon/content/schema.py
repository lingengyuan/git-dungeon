"""
Content schema definitions for Git Dungeon.
所有内容定义（卡牌/遗物/事件/敌人/流派）都应在此定义。
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class CardType(Enum):
    """卡牌类型"""
    ATTACK = "attack"
    SKILL = "skill"
    POWER = "power"


class CardRarity(Enum):
    """卡牌稀有度"""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class RelicTier(Enum):
    """遗物稀有度"""
    STARTER = "starter"
    BOSS = "boss"
    RARE = "rare"
    UNCOMMON = "uncommon"
    COMMON = "common"


class EnemyType(Enum):
    """敌人类型（基于 commit 类型）"""
    FEAT = "feat"       # 新功能
    FIX = "fix"         # Bug 修复
    DOCS = "docs"       # 文档
    REFACTOR = "refactor"  # 重构
    MERGE = "merge"     # 合并
    CHORE = "chore"     # 杂项
    STYLE = "style"     # 格式
    TEST = "test"       # 测试
    PERF = "perf"       # 性能
    REVERT = "revert"   # 回滚


class IntentType(Enum):
    """敌人意图类型"""
    ATTACK = "attack"
    DEFEND = "defend"
    BUFF = "buff"
    DEBUFF = "debuff"
    CHARGE = "charge"  # 蓄力
    ESCAPE = "escape"


class StatusType(Enum):
    """状态效果类型"""
    # 进攻类
    VULNERABLE = "vulnerable"  # 易伤（受伤+50%）
    BURN = "burn"  # 灼烧（回合末掉血）
    WEAK = "weak"  # 虚弱（攻击力下降）
    
    # 防御类
    BLOCK = "block"  # 护甲
    THORNS = "thorns"  # 反伤
    
    # 资源类
    CHARGE = "charge"  # 充能（下回合+能量）
    FOCUS = "focus"  # 专注（抽牌/找牌增益）
    
    # 负面类
    TECH_DEBT = "tech_debt"  # 技术债（降低能量上限）
    BUG = "bug"  # Bug（持续掉血/降低抽牌）


@dataclass
class Effect:
    """卡牌效果定义"""
    type: str  # "damage", "block", "draw", "energy", "status", "heal"
    value: int
    target: str = "enemy"  # "enemy", "self", "all"
    status: Optional[str] = None  # 状态类型
    status_value: int = 0  # 状态层数


@dataclass
class CardDef:
    """卡牌定义"""
    id: str
    name_key: str  # i18n key, e.g., "card.strike.name"
    desc_key: str  # i18n key, e.g., "card.strike.desc"
    card_type: CardType
    cost: int  # 能量费用
    rarity: CardRarity
    effects: List[Effect] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)  # e.g., ["offensive", "debug"]
    upgrade_id: Optional[str] = None  # 升级后的卡牌ID
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, CardDef):
            return self.id == other.id
        return False


@dataclass
class RelicDef:
    """遗物定义"""
    id: str
    name_key: str
    desc_key: str
    tier: RelicTier
    effects: Dict[str, Any] = field(default_factory=dict)  # 遗物效果参数
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, RelicDef):
            return self.id == other.id
        return False


@dataclass
class StatusDef:
    """状态效果定义"""
    id: str
    name_key: str
    desc_key: str
    status_type: StatusType
    max_stacks: int = 999  # 最大层数
    duration_type: str = "indefinite"  # "indefinite", "turn", "permanent"
    
    def on_apply(self, target, value: int) -> None:
        """应用状态时触发"""
        pass
    
    def on_turn_start(self, target) -> None:
        """回合开始时触发"""
        pass
    
    def on_turn_end(self, target) -> None:
        """回合结束时触发"""
        pass
    
    def on_take_damage(self, target, damage: int) -> int:
        """受到伤害时触发，返回修正后的伤害"""
        return damage


class EnemyTier(Enum):
    """敌人难度层级"""
    NORMAL = "normal"
    ELITE = "elite"
    BOSS = "boss"


@dataclass
class EnemyDef:
    """敌人定义"""
    id: str
    name_key: str
    enemy_type: EnemyType
    base_hp: int
    base_damage: int
    base_block: int = 0
    tier: EnemyTier = EnemyTier.NORMAL
    ai_pattern: str = "basic"  # "basic", "aggressive", "defensive", "cycle"
    status_resist: List[str] = field(default_factory=list)  # 抵抗的状态
    status_vulnerable: List[str] = field(default_factory=list)  # 弱点的状态
    intent_preference: List[IntentType] = field(default_factory=list)  # 意图偏好
    is_boss: bool = False  # 是否为 BOSS (兼容旧字段)
    gold_multiplier: float = 1.0  # 金币倍率
    exp_multiplier: float = 1.0  # 经验倍率
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, EnemyDef):
            return self.id == other.id
        return False


@dataclass
class IntentDef:
    """敌人意图定义"""
    intent_type: IntentType
    value: int  # 伤害值或护甲值等
    status: Optional[StatusType] = None
    status_value: int = 0


@dataclass
class ArchetypeDef:
    """流派定义"""
    id: str
    name_key: str
    desc_key: str
    tags: List[str] = field(default_factory=list)  # 关联的卡牌/遗物 tags
    starter_cards: List[str] = field(default_factory=list)  # 起始卡牌ID列表
    starter_relics: List[str] = field(default_factory=list)  # 起始遗物ID列表


@dataclass
class EventEffect:
    """事件效果定义"""
    opcode: str  # 效果操作码: gain_gold, lose_gold, heal, take_damage, add_card, remove_card, upgrade_card, add_relic, remove_relic, apply_status, trigger_battle, modify_bias, set_flag
    value: Any  # 效果值
    target: str = "player"  # player, enemy, all
    condition: Optional[Dict[str, Any]] = None  # 条件


@dataclass
class EventChoice:
    """事件选项定义"""
    id: str
    text_key: str  # 选项描述 i18n key
    effects: List[EventEffect] = field(default_factory=list)  # 效果列表
    condition: Optional[Dict[str, Any]] = None  # 显示条件


@dataclass
class EventDef:
    """事件定义"""
    id: str
    name_key: str
    desc_key: str
    choices: List[EventChoice] = field(default_factory=list)  # 选项列表
    conditions: Dict[str, Any] = field(default_factory=dict)  # 全局触发条件
    weights: Dict[str, int] = field(default_factory=dict)  # 权重配置
    route_tags: List[str] = field(default_factory=list)  # 关联的路径标签


@dataclass
class CharacterAbility:
    """角色能力定义"""
    id: str
    name_key: str
    desc_key: str
    trigger: str  # on_turn_start, on_turn_end, on_damage_taken, etc.
    effect: str  # clear_negative_status, add_energy_or_draw, etc.
    value: int = 0


@dataclass
class CharacterStats:
    """角色基础属性"""
    hp: int = 100
    energy: int = 3
    start_relics: int = 1


@dataclass
class CharacterDef:
    """角色定义"""
    id: str
    name_key: str
    desc_key: str
    starter_cards: List[str] = field(default_factory=list)
    starter_relics: List[str] = field(default_factory=list)
    abilities: List[CharacterAbility] = field(default_factory=list)
    stats: CharacterStats = field(default_factory=CharacterStats)
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, CharacterDef):
            return self.id == other.id
        return False


@dataclass
class ContentPack:
    """内容包定义 (M3.3)"""
    id: str
    name_key: str
    desc_key: str
    archetype: str  # 关联流派
    rarity: str  # uncommon/rare/epic
    points_cost: int = 150
    
    # 内容
    cards: List[CardDef] = field(default_factory=list)
    relics: List[RelicDef] = field(default_factory=list)
    events: List[EventDef] = field(default_factory=list)
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, ContentPack):
            return self.id == other.id
        return False


@dataclass
class ContentRegistry:
    """内容注册表 - 聚合所有内容定义"""
    cards: Dict[str, CardDef] = field(default_factory=dict)
    relics: Dict[str, RelicDef] = field(default_factory=dict)
    statuses: Dict[str, StatusDef] = field(default_factory=dict)
    enemies: Dict[str, EnemyDef] = field(default_factory=dict)
    archetypes: Dict[str, ArchetypeDef] = field(default_factory=dict)
    events: Dict[str, EventDef] = field(default_factory=dict)
    characters: Dict[str, CharacterDef] = field(default_factory=dict)  # M3
    packs: Dict[str, ContentPack] = field(default_factory=dict)  # M3.3
    
    def get_card(self, card_id: str) -> Optional[CardDef]:
        return self.cards.get(card_id)
    
    def get_relic(self, relic_id: str) -> Optional[RelicDef]:
        return self.relics.get(relic_id)
    
    def get_enemy(self, enemy_id: str) -> Optional[EnemyDef]:
        return self.enemies.get(enemy_id)
    
    def get_archetype(self, archetype_id: str) -> Optional[ArchetypeDef]:
        return self.archetypes.get(archetype_id)
    
    def get_character(self, character_id: str) -> Optional[CharacterDef]:
        return self.characters.get(character_id)
    
    def get_pack(self, pack_id: str) -> Optional[ContentPack]:
        return self.packs.get(pack_id)
    
    def get_packs_by_archetype(self, archetype: str) -> List[ContentPack]:
        return [p for p in self.packs.values() if p.archetype == archetype]
    
    def get_cards_by_tag(self, tag: str) -> List[CardDef]:
        return [c for c in self.cards.values() if tag in c.tags]
    
    def get_enemies_by_type(self, enemy_type: EnemyType) -> List[EnemyDef]:
        return [e for e in self.enemies.values() if e.enemy_type == enemy_type]
