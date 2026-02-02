"""
M1.3 + M2.3 Rewards System - 奖励与流派系统
奖励选择受 commit 特征影响，引入流派倾向系统
M2.3: 添加精英/BOSS 节点奖励
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

from ..rng import RNG, DefaultRNG
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
        """生成战斗后奖励 (M2.3: 支持 elite/boss 额外奖励)"""
        rewards = RewardBundle()
        
        # 1. 金币奖励 (基于敌人类型和 tier)
        rewards.gold_delta = self._calculate_gold(enemy)
        
        # 2. 卡牌奖励 (基于 commit 特征)
        rewards.card_choices = self._select_card_pool(state, enemy)
        
        # 3. 遗物奖励 (基于敌人类型和章节)
        rewards.relic_drop = self._maybe_drop_relic(state, enemy)
        
        # M2.3: 精英奖励 - 高概率掉落遗物
        if self._is_elite(enemy):
            if not rewards.relic_drop and self.rng.random() < 0.7:
                # 精英敌人 70% 必掉遗物
                rewards.relic_drop = self._get_elite_relic()
            # 精英卡牌奖励更好
            rewards.card_choices = self._select_elite_card_pool(state, enemy)
        
        # M2.3: BOSS 奖励 - 强遗物 + 3选1
        if enemy.is_boss:
            # BOSS 必掉强遗物
            rewards.relic_drop = self._get_boss_relic()
            # BOSS 3选1 卡牌
            rewards.card_choices = self._select_boss_card_pool(state)
            # BOSS 可选移除一张卡
            rewards.remove_card = True
            # BOSS 可选升级一张卡
            rewards.upgrade_card = True
        
        # 4. 治疗 (可选)
        max_hp = state.player.character.stats.hp.value
        current_hp = state.player.character.current_hp
        if current_hp < max_hp * 0.5:
            # 精英战后回复更多
            heal_amount = 15 if self._is_elite(enemy) else 10
            rewards.heal = min(heal_amount, max_hp - current_hp)
        
        return rewards
    
    def _is_elite(self, enemy: EnemyState) -> bool:
        """判断是否为精英敌人"""
        # 通过名称或属性判断
        if hasattr(enemy, 'tier'):
            from git_dungeon.content.schema import EnemyTier
            return enemy.tier == EnemyTier.ELITE
        # 兼容旧逻辑
        return enemy.attack > 10 or enemy.max_hp > 60
    
    def _calculate_gold(self, enemy: EnemyState) -> int:
        """计算金币奖励"""
        base_gold = 10
        
        # BOSS 额外金币
        if enemy.is_boss:
            base_gold *= 3
        # M2.3: 精英额外金币
        elif self._is_elite(enemy):
            base_gold *= 2
        
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
    
    def _get_elite_relic(self) -> Optional[str]:
        """获取精英敌人掉落遗物"""
        if not self.content_registry:
            return "power_up"
        
        from git_dungeon.content.schema import RelicTier
        eligible = []
        for relic in self.content_registry.relics.values():
            if relic.tier in (RelicTier.UNCOMMON, RelicTier.RARE, RelicTier.BOSS):
                eligible.append(relic.id)
        
        if eligible:
            return self.rng.choice(eligible)
        return None
    
    def _get_boss_relic(self) -> Optional[str]:
        """获取 BOSS 掉落遗物 (必为 rare 或 boss tier)"""
        if not self.content_registry:
            return "boss_relic"
        
        from git_dungeon.content.schema import RelicTier
        eligible = []
        for relic in self.content_registry.relics.values():
            if relic.tier in (RelicTier.RARE, RelicTier.BOSS):
                eligible.append(relic.id)
        
        if eligible:
            return self.rng.choice(eligible)
        return None
    
    def _select_elite_card_pool(self, state: GameState, enemy: EnemyState) -> List[str]:
        """精英敌人卡牌奖励池"""
        if not self.content_registry:
            return ["debug_strike", "test_guard", "refactor_risk"]
        
        all_cards = list(self.content_registry.cards.values())
        candidates = []
        
        for card in all_cards:
            if card.id in state.player.deck.draw_pile:
                continue
            if card.rarity.value in ["rare", "uncommon"]:
                candidates.append(card)
        
        if len(candidates) < 3:
            for card in all_cards:
                if len(candidates) >= 3:
                    break
                if card not in candidates and card.rarity.value == "uncommon":
                    candidates.append(card)
        
        if candidates:
            choices = self.rng.choices(candidates, k=min(3, len(candidates)))
            return [c.id for c in choices]
        
        return ["debug_strike", "test_guard", "refactor_risk"]
    
    def _select_boss_card_pool(self, state: GameState) -> List[str]:
        """BOSS 敌人卡牌奖励池"""
        if not self.content_registry:
            return ["debug_power", "test_relic", "refactor_power"]
        
        all_cards = list(self.content_registry.cards.values())
        candidates = []
        
        for card in all_cards:
            if card.id in state.player.deck.draw_pile:
                continue
            if card.rarity.value == "rare":
                candidates.append(card)
        
        if len(candidates) < 3:
            for card in all_cards:
                if len(candidates) >= 3:
                    break
                if card not in candidates and card.rarity.value == "uncommon":
                    candidates.append(card)
        
        if candidates:
            choices = self.rng.choices(candidates, k=min(3, len(candidates)))
            return [c.id for c in choices]
        
        return ["debug_power", "test_relic", "refactor_power"]
    
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


# ==================== M2.3 精英/BOSS 奖励扩展 ====================

class EliteRewardsEngine:
    """精英和 BOSS 奖励引擎"""
    
    def __init__(self, rng: RNG = None, content_registry = None):
        self.rng = rng or DefaultRNG(seed=0)
        self.content_registry = content_registry
    
    def get_elite_boss_relics(self, tier: str) -> List[str]:
        """获取精英/BOSS 专属遗物"""
        if not self.content_registry:
            return ["power_up", "critical_mass"]
        
        relics = []
        for relic in self.content_registry.relics.values():
            if tier == "boss":
                if relic.tier.value in ["boss", "rare"]:
                    relics.append(relic.id)
            elif tier == "elite":
                if relic.tier.value in ["elite", "rare", "uncommon"]:
                    relics.append(relic.id)
        
        return relics if relics else ["power_up", "critical_mass"]
    
    def get_boss_relic_choices(self) -> List[str]:
        """获取 BOSS 遗物选择 (2选1)"""
        return self.get_elite_boss_relics("boss")[:2]
    
    def _select_elite_card_pool(self, state: GameState, enemy: EnemyState) -> List[str]:
        """精英敌人卡牌奖励池 (更高稀有度)"""
        if not self.content_registry:
            return ["debug_strike", "test_guard", "refactor_risk"]
        
        all_cards = list(self.content_registry.cards.values())
        
        # 优先选择 rare 和 uncommon 卡牌
        candidates = []
        for card in all_cards:
            if card.id in state.player.deck.draw_pile:
                continue
            if card.rarity.value in ["rare", "uncommon"]:
                candidates.append(card)
        
        if len(candidates) < 3:
            # 补充 uncommon 卡牌
            for card in all_cards:
                if len(candidates) >= 3:
                    break
                if card not in candidates and card.rarity.value == "uncommon":
                    candidates.append(card)
        
        if candidates:
            choices = self.rng.choices(candidates, k=min(3, len(candidates)))
            return [c.id for c in choices]
        
        return ["debug_strike", "test_guard", "refactor_risk"]
    
    def _select_boss_card_pool(self, state: GameState) -> List[str]:
        """BOSS 敌人卡牌奖励池 (3选1，高稀有度)"""
        if not self.content_registry:
            return ["debug_power", "test_relic", "refactor_power"]
        
        all_cards = list(self.content_registry.cards.values())
        
        # 优先选择 rare 卡牌
        candidates = []
        for card in all_cards:
            if card.id in state.player.deck.draw_pile:
                continue
            if card.rarity.value == "rare":
                candidates.append(card)
        
        if len(candidates) < 3:
            # 补充 uncommon 卡牌
            for card in all_cards:
                if len(candidates) >= 3:
                    break
                if card not in candidates and card.rarity.value == "uncommon":
                    candidates.append(card)
        
        if candidates:
            choices = self.rng.choices(candidates, k=min(3, len(candidates)))
            return [c.id for c in choices]
        
        return ["debug_power", "test_relic", "refactor_power"]
    
    def _get_random_relic(self, min_tier: str = "common") -> Optional[str]:
        """获取随机遗物 (指定最低稀有度)"""
        if not self.content_registry:
            return "power_up"
        
        tier_order = ["common", "uncommon", "rare", "boss"]
        min_idx = tier_order.index(min_tier) if min_tier in tier_order else 0
        
        eligible = []
        for relic in self.content_registry.relics.values():
            idx = tier_order.index(relic.tier.value) if relic.tier.value in tier_order else 0
            if idx >= min_idx:
                eligible.append(relic.id)
        
        if eligible:
            return self.rng.choice(eligible)
        return None
    
    def calculate_elite_boss_multipliers(self, enemy: EnemyState) -> Dict[str, float]:
        """计算精英/BOSS 的奖励倍率"""
        multipliers = {
            "gold": 1.0,
            "exp": 1.0,
            "relic_chance": 0.1,
            "card_rarity": 1.0,
        }
        
        if self._is_elite(enemy):
            multipliers["gold"] = 2.0
            multipliers["exp"] = 1.5
            multipliers["relic_chance"] = 0.3
            multipliers["card_rarity"] = 1.5
        
        if enemy.is_boss:
            multipliers["gold"] = 3.0
            multipliers["exp"] = 2.0
            multipliers["relic_chance"] = 1.0  # 100% 掉落
            multipliers["card_rarity"] = 2.0
        
        return multipliers
    
    def _is_elite(self, enemy: EnemyState) -> bool:
        """判断是否为精英敌人"""
        if hasattr(enemy, 'tier'):
            from git_dungeon.content.schema import EnemyTier
            return enemy.tier == EnemyTier.ELITE
        return enemy.attack > 10 or enemy.max_hp > 60
