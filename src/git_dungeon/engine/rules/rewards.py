"""
M1.3 Rewards System - 奖励与流派系统
奖励选择受 commit 特征影响，引入流派倾向系统
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

from ..rng import RNG
from ..model import GameState, EnemyState


class RewardType(Enum):
    """奖励类型"""
    GOLD = "gold"
    CARD_CHOICE = "card_choice"
    RELIC = "relic"
    HEAL = "heal"
    REMOVE_CARD = "remove_card"
    UPGRADE_CARD = "upgrade_card"


@dataclass
class RewardOption:
    """单个奖励选项"""
    reward_type: RewardType
    value: Any  # gold数量 / card_id列表 / relic_id / heal量
    description: str = ""


@dataclass
class RewardBundle:
    """奖励包 - 一组奖励"""
    gold_delta: int = 0
    card_choices: List[str] = field(default_factory=list)  # card_id 列表 (3选1)
    relic_drop: Optional[str] = None  # relic_id
    heal: int = 0
    remove_card: bool = False
    upgrade_card: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "gold_delta": self.gold_delta,
            "card_choices": self.card_choices,
            "relic_drop": self.relic_drop,
            "heal": self.heal,
            "remove_card": self.remove_card,
            "upgrade_card": self.upgrade_card
        }


@dataclass
class ArchetypeBias:
    """流派倾向系统"""
    # 各流派权重
    debug_weight: float = 0.0
    test_weight: float = 0.0
    refactor_weight: float = 0.0
    
    # 玩家选择的卡牌/遗物 tags
    selected_tags: Dict[str, int] = field(default_factory=dict)  # tag -> count
    
    def record_choice(self, card_tags: List[str], relic_tags: List[str] = None) -> None:
        """记录玩家选择，更新倾向"""
        for tag in card_tags:
            self.selected_tags[tag] = self.selected_tags.get(tag, 0) + 1
        
        if relic_tags:
            for tag in relic_tags:
                self.selected_tags[tag] = self.selected_tags.get(tag, 0) + 1
        
        # 更新流派权重
        tag_to_weight = {
            "debug": "debug_weight",
            "offensive": "debug_weight",
            "test": "test_weight",
            "defensive": "test_weight",
            "refactor": "refactor_weight",
            "risk": "refactor_weight",
        }
        
        for tag, weight_name in tag_to_weight.items():
            if tag in self.selected_tags:
                current = getattr(self, weight_name, 0)
                setattr(self, weight_name, current + self.selected_tags[tag] * 0.1)
    
    def get_weight(self, archetype: str) -> float:
        """获取某流派的权重"""
        mapping = {
            "debug_beatdown": self.debug_weight,
            "test_shrine": self.test_weight,
            "refactor_risk": self.refactor_weight,
        }
        return mapping.get(archetype, 0.0)
    
    def normalize_weights(self) -> None:
        """归一化权重"""
        total = self.debug_weight + self.test_weight + self.refactor_weight
        if total > 0:
            self.debug_weight /= total
            self.test_weight /= total
            self.refactor_weight /= total


class RewardsEngine:
    """奖励引擎 - 根据 commit 特征和流派倾向生成奖励"""
    
    def __init__(self, rng: RNG, content_registry = None):
        self.rng = rng
        self.content_registry = content_registry
    
    def generate_post_battle_rewards(
        self,
        state: GameState,
        enemy: EnemyState
    ) -> RewardBundle:
        """生成战斗后奖励"""
        rewards = RewardBundle()
        
        # 1. 金币奖励 (基于敌人类型)
        rewards.gold_delta = self._calculate_gold(enemy)
        
        # 2. 卡牌奖励 (基于 commit 特征)
        rewards.card_choices = self._select_card_pool(state, enemy)
        
        # 3. 遗物奖励 (基于敌人类型和章节)
        rewards.relic_drop = self._maybe_drop_relic(state, enemy)
        
        # 4. 治疗 (可选)
        if state.player.character.current_hp < state.player.character.stats.hp.value * 0.5:
            rewards.heal = min(10, state.player.character.stats.hp.value - state.player.character.current_hp)
        
        return rewards
    
    def _calculate_gold(self, enemy: EnemyState) -> int:
        """计算金币奖励"""
        base_gold = 10
        
        # BOSS 额外金币
        if enemy.is_boss:
            base_gold *= 3
        
        # 敌人类型加成
        type_bonus = {
            "merge": 1.5,
            "refactor": 1.2,
            "fix": 1.1,
            "feat": 1.0,
            "docs": 0.8,
        }
        
        multiplier = type_bonus.get(enemy.enemy_type, 1.0)
        
        # 添加随机波动 (±20%)
        import random
        fluctuation = 0.8 + self.rng.random() * 0.4
        
        return int(base_gold * multiplier * fluctuation)
    
    def _select_card_pool(self, state: GameState, enemy: EnemyState) -> List[str]:
        """选择卡牌奖励池 (3选1)"""
        # 如果没有 content registry，返回默认卡牌
        if not self.content_registry:
            return ["strike", "defend", "debug_strike"]
        
        # 基于 commit 特征调整权重
        card_pool = []
        
        # 大 diff：高费高伤卡
        large_diff = enemy.attack > 8 or enemy.max_hp > 40
        
        # 夜间提交：爆发卡
        # (简化: 随机选择)
        
        # merge：精英卡
        is_merge = enemy.enemy_type == "merge"
        
        # 获取卡牌
        all_cards = list(self.content_registry.cards.values())
        
        if not all_cards:
            return ["strike", "defend", "debug_strike"]
        
        # 筛选候选卡牌
        candidates = []
        
        for card in all_cards:
            # 过滤掉已有卡牌
            if card.id in state.player.deck.draw_pile:
                continue
            
            # 基于特征选择
            if large_diff and "offensive" in card.tags:
                candidates.append(card)
            elif is_merge and card.rarity.value in ["rare", "epic"]:
                candidates.append(card)
            elif "basic" in card.tags:
                candidates.append(card)
        
        # 如果候选不足，补充基础卡
        if len(candidates) < 3:
            for card in all_cards:
                if len(candidates) >= 3:
                    break
                if card not in candidates and "basic" in card.tags:
                    candidates.append(card)
        
        # 随机选择 3 张
        if candidates:
            choices = self.rng.choices(candidates, k=min(3, len(candidates)))
            return [c.id for c in choices]
        
        return ["strike", "defend", "debug_strike"]
    
    def _maybe_drop_relic(self, state: GameState, enemy: EnemyState) -> Optional[str]:
        """决定是否掉落遗物"""
        if not self.content_registry:
            return None
        
        # BOSS 或 merge 更高几率
        base_chance = 0.1 if enemy.is_boss or enemy.enemy_type == "merge" else 0.05
        
        if self.rng.random() < base_chance:
            # 掉落遗物
            relics = list(self.content_registry.relics.values())
            if relics:
                # 基于流派倾向选择
                bias = getattr(state, 'archetype_bias', None)
                if bias and bias.selected_tags:
                    # 倾向测试遗物
                    test_relics = [r for r in relics if "test" in r.id or "defensive" in r.id]
                    if test_relics and bias.test_weight > bias.debug_weight:
                        chosen = self.rng.choice(test_relics)
                        return chosen.id
                
                # 随机选择
                chosen = self.rng.choice(relics)
                return chosen.id
        
        return None


class ArchetypeEngine:
    """流派引擎 - 管理玩家流派倾向和卡组构建"""
    
    def __init__(self, rng: RNG, content_registry = None):
        self.rng = rng
        self.content_registry = content_registry
    
    def get_starter_deck(self, archetype_id: str) -> List[str]:
        """获取流派起始套牌"""
        if not self.content_registry:
            # 默认起始套牌
            return ["strike", "strike", "strike", "defend", "defend", "defend"]
        
        archetype = self.content_registry.get_archetype(archetype_id)
        if archetype:
            return archetype.starter_cards.copy()
        
        return ["strike", "strike", "strike", "defend", "defend", "defend"]
    
    def get_starter_relics(self, archetype_id: str) -> List[str]:
        """获取流派起始遗物"""
        if not self.content_registry:
            return ["git_init"]
        
        archetype = self.content_registry.get_archetype(archetype_id)
        if archetype:
            return archetype.starter_relics.copy()
        
        return ["git_init"]
    
    def calculate_archetype_weights(
        self,
        state: GameState,
        card_choices: List[str]
    ) -> Dict[str, float]:
        """计算流派权重 (用于奖励选择)"""
        bias = getattr(state, 'archetype_bias', None)
        
        if not bias:
            return {"debug_beatdown": 1.0, "test_shrine": 1.0, "refactor_risk": 1.0}
        
        # 返回各流派权重
        return {
            "debug_beatdown": max(0.1, bias.debug_weight + 1.0),
            "test_shrine": max(0.1, bias.test_weight + 1.0),
            "refactor_risk": max(0.1, bias.refactor_weight + 1.0),
        }
    
    def select_card_with_bias(
        self,
        state: GameState,
        choices: List[str]
    ) -> str:
        """根据流派倾向选择卡牌"""
        if not choices:
            return ""
        
        if len(choices) == 1:
            return choices[0]
        
        # 计算各流派权重
        weights = self.calculate_archetype_weights(state, choices)
        
        # 基于权重选择
        total = sum(weights.values())
        probs = [w / total for w in weights.values()]
        
        # 随机选择流派
        import random
        archetype = random.choices(list(weights.keys()), weights=probs, k=1)[0]
        
        # 在该流派偏好的卡牌中选择
        if self.content_registry:
            archetype_obj = self.content_registry.get_archetype(archetype)
            if archetype_obj and archetype_obj.starter_cards:
                # 优先选择流派相关卡牌
                matching = [c for c in choices if c in archetype_obj.starter_cards]
                if matching:
                    return self.rng.choice(matching)
        
        # 随机选择
        return self.rng.choice(choices)


def create_rewards_engine(rng: RNG, content_registry = None) -> RewardsEngine:
    """创建奖励引擎"""
    return RewardsEngine(rng, content_registry)


def create_archetype_engine(rng: RNG, content_registry = None) -> ArchetypeEngine:
    """创建流派引擎"""
    return ArchetypeEngine(rng, content_registry)
