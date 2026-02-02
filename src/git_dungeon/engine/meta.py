"""
M3 元进度系统 - 存档、解锁、角色系统

管理玩家进度、成就、解锁内容
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class MetaProfile:
    """玩家元进度档案"""
    profile_id: str = ""
    player_name: str = "Player"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_played: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # 进度点数
    total_points: int = 0
    available_points: int = 0
    
    # 已解锁内容
    unlocks: Dict[str, List[str]] = field(default_factory=lambda: {
        "characters": [],      # 已解锁角色
        "starter_bundles": [], # 已解锁起始包
        "packs": [],          # 已解锁内容包
        "achievements": []    # 已解锁成就
    })
    
    # 统计
    stats: Dict[str, Any] = field(default_factory=lambda: {
        "total_runs": 0,
        "victories": 0,
        "enemies_killed": 0,
        "elites_killed": 0,
        "bosses_killed": 0,
        "cards_collected": 0,
        "relics_collected": 0,
        "max_chapter_reached": 0,
        "favorite_archetype": "",
        "play_time_seconds": 0
    })
    
    # 设置
    settings: Dict[str, Any] = field(default_factory=lambda: {
        "auto_save": True,
        "default_character": "developer",
        "difficulty": "normal"
    })
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化"""
        return {
            "profile_id": self.profile_id,
            "player_name": self.player_name,
            "created_at": self.created_at,
            "last_played": self.last_played,
            "total_points": self.total_points,
            "available_points": self.available_points,
            "unlocks": self.unlocks,
            "stats": self.stats,
            "settings": self.settings
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetaProfile":
        """反序列化"""
        profile = cls()
        profile.profile_id = data.get("profile_id", "")
        profile.player_name = data.get("player_name", "Player")
        profile.created_at = data.get("created_at", profile.created_at)
        profile.last_played = data.get("last_played", profile.last_played)
        profile.total_points = data.get("total_points", 0)
        profile.available_points = data.get("available_points", 0)
        profile.unlocks = data.get("unlocks", {"characters": [], "starter_bundles": [], "packs": [], "achievements": []})
        profile.stats = data.get("stats", {})
        profile.settings = data.get("settings", {})
        return profile


@dataclass
class RunSummary:
    """单局游戏总结"""
    run_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    character_id: str = ""
    archetype: str = ""
    chapter_reached: int = 0
    enemies_killed: int = 0
    elites_killed: int = 0
    bosses_killed: int = 0
    gold_earned: int = 0
    cards_obtained: List[str] = field(default_factory=list)
    relics_obtained: List[str] = field(default_factory=list)
    death_reason: str = ""  # damage/tech_debt/burn/other
    is_victory: bool = False
    
    # 关键卡牌/遗物
    key_cards: List[str] = field(default_factory=list)
    key_relics: List[str] = field(default_factory=list)
    
    # 流派倾向
    final_archetype_bias: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RunSummary":
        return cls(**data)


# 解锁定义
UNLOCK_DEFINITIONS = {
    "characters": {
        "developer": {"name": "Developer", "points": 0, "desc": "均衡型角色"},
        "reviewer": {"name": "Reviewer", "points": 100, "desc": "净化 TechDebt/防御型"},
        "devops": {"name": "DevOps", "points": 200, "desc": "管道流：资源/抽牌/护甲"}
    },
    "starter_bundles": {
        "debug_starter": {"name": "Debug Starter", "points": 50, "desc": "Debug 爆发流起手"},
        "test_starter": {"name": "Test Starter", "points": 50, "desc": "Test 护盾流起手"},
        "refactor_starter": {"name": "Refactor Starter", "points": 50, "desc": "Refactor 代价流起手"}
    },
    "packs": {
        "debug_pack": {"name": "Debug Pack", "points": 150, "desc": "Debug 卡牌包"},
        "test_pack": {"name": "Test Pack", "points": 150, "desc": "Test 卡牌包"},
        "refactor_pack": {"name": "Refactor Pack", "points": 150, "desc": "Refactor 卡牌包"}
    },
    "achievements": {
        "first_blood": {"name": "First Blood", "points": 10, "desc": "首次击杀敌人"},
        "elite_hunter": {"name": "Elite Hunter", "points": 30, "desc": "击杀 10 个精英"},
        "boss_slayer": {"name": "Boss Slayer", "points": 50, "desc": "首次击杀 BOSS"},
        "chapter_victor": {"name": "Chapter Victor", "points": 40, "desc": "完成第一章"},
        "card_collector": {"name": "Card Collector", "points": 25, "desc": "收集 20 张不同卡牌"},
        "relic_hoarder": {"name": "Relic Hoarder", "points": 25, "desc": "收集 10 个遗物"},
        "no_damage_elite": {"name": "Perfect Elite", "points": 60, "desc": "无伤击杀精英"}
    }
}


def load_meta(path: str) -> Optional[MetaProfile]:
    """加载元进度存档"""
    if not os.path.exists(path):
        return None
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return MetaProfile.from_dict(data)
    except Exception as e:
        print(f"⚠️  加载存档失败: {e}")
        return None


def save_meta(profile: MetaProfile, path: str) -> bool:
    """保存元进度存档"""
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(profile.to_dict(), f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠️  保存存档失败: {e}")
        return False


def award_points(profile: MetaProfile, run: RunSummary) -> int:
    """根据单局表现奖励点数"""
    points = 0
    
    # 基础分：每击杀 1 敌 = 1 point
    points += run.enemies_killed
    
    # 精英击杀额外分
    points += run.elites_killed * 2
    
    # BOSS 击杀额外分
    points += run.bosses_killed * 5
    
    # 章节进度分
    points += run.chapter_reached * 10
    
    # 胜利额外分
    if run.is_victory:
        points += 50
    
    # 首次击杀 BOSS
    if run.bosses_killed > 0 and profile.stats.get("bosses_killed", 0) == 0:
        points += 25
        profile.unlocks["achievements"].append("boss_slayer")
    
    # 无伤精英
    # (需要在游戏中记录，此处简化)
    
    # 更新统计
    profile.stats["total_runs"] += 1
    profile.stats["enemies_killed"] += run.enemies_killed
    profile.stats["elites_killed"] += run.elites_killed
    profile.stats["bosses_killed"] += run.bosses_killed
    profile.stats["cards_collected"] += len(run.cards_obtained)
    profile.stats["relics_collected"] += len(run.relics_obtained)
    profile.stats["max_chapter_reached"] = max(
        profile.stats.get("max_chapter_reached", 0),
        run.chapter_reached
    )
    
    if run.is_victory:
        profile.stats["victories"] += 1
    
    # 更新流派倾向
    if run.final_archetype_bias:
        max_archetype = max(run.final_archetype_bias.items(), key=lambda x: x[1])
        profile.stats["favorite_archetype"] = max_archetype[0]
    
    # 更新点数
    profile.total_points += points
    profile.available_points += points
    profile.last_played = datetime.now().isoformat()
    
    return points


def get_available_unlocks(profile: MetaProfile) -> Dict[str, List[Dict[str, Any]]]:
    """获取可解锁内容列表"""
    available: Dict[str, List[Dict[str, Any]]] = {}
    
    for category, items in UNLOCK_DEFINITIONS.items():
        available[category] = []
        for item_id, item_def in items.items():
            if item_id not in profile.unlocks.get(category, []):
                item_def["id"] = item_id
                item_def["locked"] = True
                available[category].append(item_def)
    
    return available


def can_afford(profile: MetaProfile, category: str, item_id: str) -> bool:
    """检查是否可以解锁"""
    if category not in UNLOCK_DEFINITIONS:
        return False
    if item_id not in UNLOCK_DEFINITIONS[category]:
        return False

    cost = UNLOCK_DEFINITIONS[category][item_id]["points"]  # type: ignore[union-attr]
    return profile.available_points >= cost  # type: ignore[operator]


def unlock_item(profile: MetaProfile, category: str, item_id: str) -> bool:
    """解锁内容"""
    # 检查是否已解锁
    if item_id in profile.unlocks.get(category, []):
        return False

    if not can_afford(profile, category, item_id):
        return False

    cost = UNLOCK_DEFINITIONS[category][item_id]["points"]  # type: ignore[union-attr]
    profile.available_points -= cost  # type: ignore[operator]
    profile.unlocks.setdefault(category, []).append(item_id)
    return True


def format_points(points: int) -> str:
    """格式化点数显示"""
    return f"{points} pts"


def format_progress(profile: MetaProfile, category: str) -> str:
    """格式化进度显示"""
    total = len(UNLOCK_DEFINITIONS.get(category, {}))
    unlocked = len(profile.unlocks.get(category, []))
    return f"{unlocked}/{total}"


def create_default_profile(name: str = "Player") -> MetaProfile:
    """创建默认玩家档案"""
    import uuid
    return MetaProfile(
        profile_id=str(uuid.uuid4()),
        player_name=name,
        unlocks={
            "characters": ["developer"],  # 默认解锁 Developer
            "starter_bundles": [],
            "packs": [],
            "achievements": []
        }
    )
