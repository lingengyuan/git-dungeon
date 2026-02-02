"""
M5 成就系统 - 目标感与挑战

定义和管理游戏成就，包括成就条件、检查和奖励
"""

import os
import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Set
from datetime import datetime


@dataclass
class AchievementDef:
    """成就定义"""
    id: str
    name: str
    description: str
    category: str  # combat, exploration, collection, special
    points: int  # 成就点数奖励
    
    # 条件类型和阈值
    condition_type: str  # enemy_kills, damage_dealt, cards_played, etc.
    condition_threshold: int
    condition_operator: str = "gte"  # gte, eq, lte, gt, lt
    
    # 额外条件（可选）
    extra_conditions: Optional[Dict[str, Any]] = None
    
    # 稀有度
    rarity: str = "common"  # common, rare, epic, legendary
    
    # 隐藏成就（需要解锁后才显示）
    hidden: bool = False
    
    # 生效章节（0 = 全局）
    min_chapter: int = 0
    
    def check_condition(self, value: int) -> bool:
        """检查条件是否满足"""
        if self.condition_operator == "gte":
            return value >= self.condition_threshold
        elif self.condition_operator == "eq":
            return value == self.condition_threshold
        elif self.condition_operator == "lte":
            return value <= self.condition_threshold
        elif self.condition_operator == "gt":
            return value > self.condition_threshold
        elif self.condition_operator == "lt":
            return value < self.condition_threshold
        return False


# 成就定义集合
ACHIEVEMENT_DEFINITIONS: Dict[str, AchievementDef] = {
    # === 战斗成就 ===
    "first_blood": AchievementDef(
        id="first_blood",
        name="First Blood",
        description="击杀第一个敌人",
        category="combat",
        points=10,
        condition_type="enemy_kills",
        condition_threshold=1,
    ),
    "elite_hunter": AchievementDef(
        id="elite_hunter",
        name="Elite Hunter",
        description="击杀 10 个精英敌人",
        category="combat",
        points=30,
        condition_type="elite_kills",
        condition_threshold=10,
    ),
    "boss_slayer": AchievementDef(
        id="boss_slayer",
        name="Boss Slayer",
        description="首次击杀 BOSS",
        category="combat",
        points=50,
        condition_type="boss_kills",
        condition_threshold=1,
    ),
    "no_damage_elite": AchievementDef(
        id="no_damage_elite",
        name="Perfect Elite",
        description="无伤击杀精英敌人",
        category="combat",
        points=60,
        condition_type="max_damage_taken_elite",
        condition_threshold=0,
    ),
    "no_damage_boss": AchievementDef(
        id="no_damage_boss",
        name="Boss Master",
        description="无伤击杀 BOSS",
        category="combat",
        points=100,
        condition_type="max_damage_taken_boss",
        condition_threshold=0,
        rarity="legendary",
    ),
    "speed_runner": AchievementDef(
        id="speed_runner",
        name="Speed Runner",
        description="10 回合内击杀 BOSS",
        category="combat",
        points=80,
        condition_type="boss_turn_count",
        condition_threshold=10,
        condition_operator="lte",
        rarity="rare",
    ),
    "combo_master": AchievementDef(
        id="combo_master",
        name="Combo Master",
        description="单次战斗打出 10 连击",
        category="combat",
        points=40,
        condition_type="max_combo",
        condition_threshold=10,
        rarity="rare",
    ),
    
    # === 探索成就 ===
    "chapter_victor": AchievementDef(
        id="chapter_victor",
        name="Chapter Victor",
        description="完成第一章",
        category="exploration",
        points=40,
        condition_type="chapters_completed",
        condition_threshold=1,
    ),
    "chapter_2_complete": AchievementDef(
        id="chapter_2_complete",
        name="Making Progress",
        description="完成第二章",
        category="exploration",
        points=60,
        condition_type="chapters_completed",
        condition_threshold=2,
    ),
    "explorer": AchievementDef(
        id="explorer",
        name="Explorer",
        description="探索 20 个不同节点",
        category="exploration",
        points=30,
        condition_type="nodes_visited",
        condition_threshold=20,
    ),
    "event_master": AchievementDef(
        id="event_master",
        name="Event Master",
        description="经历 15 个不同事件",
        category="exploration",
        points=35,
        condition_type="events_experienced",
        condition_threshold=15,
    ),
    
    # === 收集成就 ===
    "card_collector": AchievementDef(
        id="card_collector",
        name="Card Collector",
        description="收集 20 张不同卡牌",
        category="collection",
        points=25,
        condition_type="unique_cards",
        condition_threshold=20,
    ),
    "relic_hoarder": AchievementDef(
        id="relic_hoarder",
        name="Relic Hoarder",
        description="收集 10 个遗物",
        category="collection",
        points=25,
        condition_type="total_relics",
        condition_threshold=10,
    ),
    "deck_builder": AchievementDef(
        id="deck_builder",
        name="Deck Builder",
        description="构建包含 30 张牌的牌组",
        category="collection",
        points=35,
        condition_type="max_deck_size",
        condition_threshold=30,
        rarity="rare",
    ),
    
    # === 特殊成就 ===
    "tech_debt_survivor": AchievementDef(
        id="tech_debt_survivor",
        name="Tech Debt Survivor",
        description="TechDebt 达到 30 但仍击杀 BOSS",
        category="special",
        points=70,
        condition_type="tech_debt_survived",
        condition_threshold=30,
        rarity="epic",
    ),
    "test_enthusiast": AchievementDef(
        id="test_enthusiast",
        name="Test Enthusiast",
        description="只用 Test 系列卡牌通关一章",
        category="special",
        points=50,
        condition_type="test_only_chapter",
        condition_threshold=1,
        rarity="rare",
    ),
    "debug_god": AchievementDef(
        id="debug_god",
        name="Debug God",
        description="单局造成 500 点伤害",
        category="special",
        points=45,
        condition_type="total_damage_dealt",
        condition_threshold=500,
        rarity="rare",
    ),
    "survivor": AchievementDef(
        id="survivor",
        name="Survivor",
        description="以不足 10 点生命值击败 BOSS",
        category="special",
        points=55,
        condition_type="boss_finish_hp",
        condition_threshold=10,
        condition_operator="lte",
        rarity="epic",
    ),
    
    # === 挑战成就 (Hard+ only) ===
    "hard_mode_victory": AchievementDef(
        id="hard_mode_victory",
        name="Hard Mode Victory",
        description="在 Hard 难度下获得胜利",
        category="special",
        points=100,
        condition_type="hard_victory",
        condition_threshold=1,
        rarity="legendary",
    ),
    "perfectionist": AchievementDef(
        id="perfectionist",
        name="Perfectionist",
        description="在一次通关中不丢失任何生命值",
        category="special",
        points=90,
        condition_type="total_damage_taken",
        condition_threshold=0,
        rarity="legendary",
        hidden=True,
    ),
}


@dataclass
class AchievementProgress:
    """成就进度追踪"""
    achievement_id: str
    current_value: int = 0
    unlocked_at: Optional[str] = None
    unlocked_in_run: bool = False
    
    def is_unlocked(self) -> bool:
        return self.unlocked_at is not None
    
    def update(self, value: int) -> bool:
        """更新进度，返回是否刚刚解锁"""
        if self.unlocked_at:
            return False
        self.current_value = value
        return True


class AchievementManager:
    """成就管理器"""
    
    def __init__(self, profile_achievements: Optional[List[str]] = None):
        """初始化成就管理器
        
        Args:
            profile_achievements: 已解锁的成就ID列表
        """
        self._progress: Dict[str, AchievementProgress] = {}
        self._unlocked: Set[str] = set(profile_achievements or [])
        self._session_stats: Dict[str, int] = {}
        
        # 初始化所有成就的进度跟踪
        for ach_id, ach_def in ACHIEVEMENT_DEFINITIONS.items():
            if ach_id not in self._progress:
                progress = AchievementProgress(achievement_id=ach_id)
                if ach_id in self._unlocked:
                    progress.unlocked_at = "unknown"  # 旧成就
                self._progress[ach_id] = progress
    
    def get_unlocked(self) -> List[str]:
        """获取已解锁成就列表"""
        return list(self._unlocked)
    
    def get_locked(self) -> List[AchievementDef]:
        """获取未解锁成就定义"""
        return [
            ach for ach_id, ach in ACHIEVEMENT_DEFINITIONS.items()
            if ach_id not in self._unlocked and not ach.hidden
        ]
    
    def get_progress(self, achievement_id: str) -> Optional[AchievementProgress]:
        """获取成就进度"""
        return self._progress.get(achievement_id)
    
    def check_and_unlock(self, condition_type: str, value: int) -> List[str]:
        """检查条件并解锁成就
        
        Args:
            condition_type: 条件类型
            value: 当前累计值
            
        Returns:
            新解锁的成就ID列表
        """
        newly_unlocked: List[str] = []
        
        for ach_id, ach_def in ACHIEVEMENT_DEFINITIONS.items():
            if ach_id in self._unlocked:
                continue
            
            if ach_def.condition_type == condition_type:
                # 使用累计值检查
                if ach_def.check_condition(value):
                    self._unlock_achievement(ach_id)
                    newly_unlocked.append(ach_id)
        
        return newly_unlocked
    
    def _unlock_achievement(self, achievement_id: str) -> bool:
        """解锁成就"""
        if achievement_id in self._unlocked:
            return False
        
        self._unlocked.add(achievement_id)
        
        if achievement_id in self._progress:
            self._progress[achievement_id].unlocked_at = datetime.now().isoformat()
        
        return True
    
    def update_stat(self, stat_type: str, amount: int) -> List[str]:
        """更新统计并检查成就
        
        Args:
            stat_type: 统计类型
            amount: 增量
            
        Returns:
            新解锁的成就ID列表
        """
        # 更新会话统计
        self._session_stats[stat_type] = self._session_stats.get(stat_type, 0) + amount
        
        # 检查成就
        return self.check_and_unlock(stat_type, self._session_stats[stat_type])
    
    def update_run_stat(self, stat_type: str, amount: int) -> List[str]:
        """更新本局统计（会重置）"""
        return self.update_stat(f"run_{stat_type}", amount)
    
    def get_session_stats(self) -> Dict[str, int]:
        """获取会话统计"""
        return self._session_stats.copy()
    
    def calculate_points(self) -> int:
        """计算已解锁成就的总点数"""
        return sum(
            ACHIEVEMENT_DEFINITIONS[ach_id].points
            for ach_id in self._unlocked
            if ach_id in ACHIEVEMENT_DEFINITIONS
        )
    
    def get_by_category(self, category: str) -> List[AchievementDef]:
        """按类别获取成就定义"""
        return [
            ach for ach in ACHIEVEMENT_DEFINITIONS.values()
            if ach.category == category
        ]
    
    def get_unlocked_by_category(self, category: str) -> List[str]:
        """按类别获取已解锁成就"""
        return [
            ach_id for ach_id in self._unlocked
            if ach_id in ACHIEVEMENT_DEFINITIONS
            and ACHIEVEMENT_DEFINITIONS[ach_id].category == category
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化"""
        return {
            "unlocked": list(self._unlocked),
            "progress": {
                ach_id: {
                    "current_value": prog.current_value,
                    "unlocked_at": prog.unlocked_at
                }
                for ach_id, prog in self._progress.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AchievementManager":
        """反序列化"""
        manager = cls(profile_achievements=data.get("unlocked", []))
        
        progress_data = data.get("progress", {})
        for ach_id, prog_data in progress_data.items():
            if ach_id in manager._progress:
                manager._progress[ach_id].current_value = prog_data.get("current_value", 0)
                manager._progress[ach_id].unlocked_at = prog_data.get("unlocked_at")
        
        return manager


def load_achievements(path: str) -> Optional[AchievementManager]:
    """加载成就进度"""
    if not os.path.exists(path):
        return None
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return AchievementManager.from_dict(data)
    except Exception as e:
        print(f"⚠️  加载成就失败: {e}")
        return None


def save_achievements(manager: AchievementManager, path: str) -> bool:
    """保存成就进度"""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(manager.to_dict(), f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️  保存成就失败: {e}")
        return False


def format_achievement_display(achievement: AchievementDef, progress: Optional[AchievementProgress] = None) -> str:
    """格式化成就显示"""
    status = "✅" if progress and progress.is_unlocked() else "🔒"
    rarity_emoji = {
        "common": "⚪",
        "rare": "🔵",
        "epic": "🟣",
        "legendary": "🟡"
    }.get(achievement.rarity, "⚪")
    
    if progress and not progress.is_unlocked():
        progress_text = f" ({progress.current_value}/{achievement.condition_threshold})"
    else:
        progress_text = ""
    
    return f"{status} {rarity_emoji} **{achievement.name}**{progress_text}\n   {achievement.description}"


def get_achievement_summary(manager: AchievementManager) -> str:
    """生成成就总结"""
    total = len(ACHIEVEMENT_DEFINITIONS)
    unlocked = len(manager.get_unlocked())
    points = manager.calculate_points()
    
    lines = [
        f"🏆 成就: {unlocked}/{total}",
        f"⭐ 总点数: {points}"
    ]
    
    # 按类别统计
    categories = {}
    for ach_id, ach_def in ACHIEVEMENT_DEFINITIONS.items():
        categories.setdefault(ach_def.category, {"total": 0, "unlocked": 0})
        categories[ach_def.category]["total"] += 1
        if ach_id in manager.get_unlocked():
            categories[ach_def.category]["unlocked"] += 1
    
    for cat, counts in sorted(categories.items()):
        lines.append(f"   {cat}: {counts['unlocked']}/{counts['total']}")
    
    return "\n".join(lines)
