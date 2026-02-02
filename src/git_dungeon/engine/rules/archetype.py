"""
M1.3 Archetype System - 流派系统
定义 3 个核心流派，引入倾向系统
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

from ..rng import RNG


class Archetype(Enum):
    """流派枚举"""
    DEBUG_BEATDOWN = "debug_beatdown"  # Debug 爆发流
    TEST_SHRINE = "test_shrine"  # 测试护盾流
    REFACTOR_RISK = "refactor_risk"  # 重构代价流


@dataclass
class ArchetypeDefinition:
    """流派定义"""
    id: str
    name: str
    description: str
    tags: List[str] = field(default_factory=list)  # 关联的卡牌/遗物 tags
    starter_cards: List[str] = field(default_factory=list)
    starter_relics: List[str] = field(default_factory=list)
    
    # 策略特点
    strategy_type: str = "aggressive"  # aggressive / defensive / hybrid
    win_condition: str = "kill_fast"  # kill_fast / survive_long / combo
    key_mechanics: List[str] = field(default_factory=list)


# 预定义流派配置
ARCHETYPE_CONFIGS = {
    "debug_beatdown": {
        "name": "Debug 爆发流",
        "description": "高伤害、快速斩杀，通过易伤和燃烧效果压垮敌人",
        "tags": ["debug", "offensive", "burn"],
        "starter_cards": [
            "debug_strike", "stack_trace", "console_log",
            "strike", "strike", "defend"
        ],
        "starter_relics": ["git_init", "debugger"],
        "strategy_type": "aggressive",
        "win_condition": "kill_fast",
        "key_mechanics": ["vulnerable", "burn", "crit"]
    },
    "test_shrine": {
        "name": "测试护盾流",
        "description": "高防御、持久战，通过护甲和反伤消耗敌人",
        "tags": ["test", "defensive", "thorns"],
        "starter_cards": [
            "test_guard", "integration_wall", "unit_bastion",
            "defend", "defend", "strike"
        ],
        "starter_relics": ["git_init", "test_framework"],
        "strategy_type": "defensive",
        "win_condition": "survive_long",
        "key_mechanics": ["block", "thorns", "heal"]
    },
    "refactor_risk": {
        "name": "重构代价流",
        "description": "高风险高回报，牺牲资源换取爆发伤害",
        "tags": ["refactor", "risk", "offensive"],
        "starter_cards": [
            "refactor_strike", "spaghetti_whip", "quick_patch",
            "strike", "strike", "defend"
        ],
        "starter_relics": ["git_init", "legacy_code"],
        "strategy_type": "hybrid",
        "win_condition": "combo",
        "key_mechanics": ["tech_debt", "charge", "high_damage"]
    }
}


class ArchetypeManager:
    """流派管理器 - 管理玩家流派选择和倾向"""
    
    def __init__(self, rng: RNG = None, content_registry = None):
        self.rng = rng
        self.content_registry = content_registry
        self._archetypes: Dict[str, ArchetypeDefinition] = {}
        self._load_archetypes()
    
    def _load_archetypes(self) -> None:
        """加载流派定义"""
        # 加载预定义流派
        for arch_id, config in ARCHETYPE_CONFIGS.items():
            self._archetypes[arch_id] = ArchetypeDefinition(
                id=arch_id,
                name=config["name"],
                description=config["description"],
                tags=config.get("tags", []),
                starter_cards=config.get("starter_cards", []),
                starter_relics=config.get("starter_relics", []),
                strategy_type=config.get("strategy_type", "aggressive"),
                win_condition=config.get("win_condition", "kill_fast"),
                key_mechanics=config.get("key_mechanics", [])
            )
        
        # 尝试从 content registry 加载
        if self.content_registry:
            for arch_id, arch in self.content_registry.archetypes.items():
                if arch_id not in self._archetypes:
                    self._archetypes[arch_id] = ArchetypeDefinition(
                        id=arch_id,
                        name=arch.name_key,
                        description=arch.desc_key,
                        tags=arch.tags,
                        starter_cards=arch.starter_cards,
                        starter_relics=arch.starter_relics
                    )
    
    def get_archetype(self, archetype_id: str) -> Optional[ArchetypeDefinition]:
        """获取流派定义"""
        return self._archetypes.get(archetype_id)
    
    def list_archetypes(self) -> List[ArchetypeDefinition]:
        """列出所有流派"""
        return list(self._archetypes.values())
    
    def get_archetype_by_tags(self, tags: List[str]) -> Optional[ArchetypeDefinition]:
        """根据 tags 获取最匹配的流派"""
        if not tags:
            return None
        
        best_match = None
        best_score = 0
        
        for arch in self._archetypes.values():
            score = sum(1 for tag in tags if tag in arch.tags)
            if score > best_score:
                best_score = score
                best_match = arch
        
        return best_match
    
    def get_starter_deck(self, archetype_id: str) -> List[str]:
        """获取流派起始套牌"""
        arch = self.get_archetype(archetype_id)
        if arch:
            return arch.starter_cards.copy()
        return ["strike", "strike", "strike", "defend", "defend", "defend"]
    
    def get_starter_relics(self, archetype_id: str) -> List[str]:
        """获取流派起始遗物"""
        arch = self.get_archetype(archetype_id)
        if arch:
            return arch.starter_relics.copy()
        return ["git_init"]


class BiasTracker:
    """倾向追踪器 - 记录玩家选择，更新流派倾向"""
    
    def __init__(self):
        # 各流派权重
        self.debug_weight: float = 0.0
        self.test_weight: float = 0.0
        self.refactor_weight: float = 0.0
        
        # 玩家选择历史
        self.card_selections: List[str] = []
        self.relic_selections: List[str] = []
        
        # 标签统计
        self.tag_counts: Dict[str, int] = {}
    
    def record_card_selection(self, card_id: str, card_tags: List[str]) -> None:
        """记录卡牌选择"""
        self.card_selections.append(card_id)
        
        # 更新标签统计
        for tag in card_tags:
            self.tag_counts[tag] = self.tag_counts.get(tag, 0) + 1
        
        # 更新流派权重
        self._update_weights_from_tags(card_tags)
    
    def record_relic_selection(self, relic_id: str, relic_tags: List[str] = None) -> None:
        """记录遗物选择"""
        self.relic_selections.append(relic_id)
        
        if relic_tags:
            for tag in relic_tags:
                self.tag_counts[tag] = self.tag_counts.get(tag, 0) + 1
    
    def _update_weights_from_tags(self, tags: List[str]) -> None:
        """根据标签更新权重"""
        tag_to_archetype = {
            "debug": "debug",
            "offensive": "debug",
            "burn": "debug",
            "test": "test",
            "defensive": "test",
            "thorns": "test",
            "refactor": "refactor",
            "risk": "refactor",
            "tech_debt": "refactor",
        }
        
        for tag in tags:
            archetype = tag_to_archetype.get(tag)
            if archetype == "debug":
                self.debug_weight += 0.1
            elif archetype == "test":
                self.test_weight += 0.1
            elif archetype == "refactor":
                self.refactor_weight += 0.1
    
    def get_archetype_weights(self) -> Dict[str, float]:
        """获取流派权重"""
        # 归一化
        total = self.debug_weight + self.test_weight + self.refactor_weight
        if total == 0:
            return {
                "debug_beatdown": 1.0,
                "test_shrine": 1.0,
                "refactor_risk": 1.0
            }
        
        return {
            "debug_beatdown": max(0.1, self.debug_weight / total + 0.33),
            "test_shrine": max(0.1, self.test_weight / total + 0.33),
            "refactor_risk": max(0.1, self.refactor_weight / total + 0.33)
        }
    
    def get_dominant_archetype(self) -> str:
        """获取主导流派"""
        weights = self.get_archetype_weights()
        return max(weights, key=weights.get)
    
    def get_recommended_cards(self, count: int = 3) -> List[str]:
        """根据倾向推荐卡牌"""
        dominant = self.get_dominant_archetype()
        
        # 返回主导流派的标签
        if dominant == "debug_beatdown":
            return ["debug", "offensive", "burn"]
        elif dominant == "test_shrine":
            return ["test", "defensive", "thorns"]
        else:
            return ["refactor", "risk", "offensive"]
    
    def to_dict(self) -> Dict[str, any]:
        """序列化"""
        return {
            "debug_weight": self.debug_weight,
            "test_weight": self.test_weight,
            "refactor_weight": self.refactor_weight,
            "card_selections": self.card_selections,
            "relic_selections": self.relic_selections,
            "tag_counts": self.tag_counts
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> "BiasTracker":
        """反序列化"""
        tracker = cls()
        tracker.debug_weight = data.get("debug_weight", 0)
        tracker.test_weight = data.get("test_weight", 0)
        tracker.refactor_weight = data.get("refactor_weight", 0)
        tracker.card_selections = data.get("card_selections", [])
        tracker.relic_selections = data.get("relic_selections", [])
        tracker.tag_counts = data.get("tag_counts", {})
        return tracker


def create_archetype_manager(rng: RNG = None, content_registry = None) -> ArchetypeManager:
    """创建流派管理器"""
    return ArchetypeManager(rng, content_registry)


def create_bias_tracker() -> BiasTracker:
    """创建倾向追踪器"""
    return BiasTracker()
