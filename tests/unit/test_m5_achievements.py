"""M5 成就系统测试"""

import pytest
import tempfile
import os
import json

from src.git_dungeon.engine.achievements import (
    AchievementDef,
    AchievementProgress,
    AchievementManager,
    ACHIEVEMENT_DEFINITIONS,
    load_achievements,
    save_achievements,
    format_achievement_display,
    get_achievement_summary,
)


class TestAchievementDef:
    """成就定义测试"""
    
    def test_check_condition_gte(self):
        """测试 >= 条件"""
        ach = AchievementDef(
            id="test",
            name="Test",
            description="Test",
            category="combat",
            points=10,
            condition_type="kills",
            condition_threshold=5,
            condition_operator="gte"
        )
        assert ach.check_condition(5) is True
        assert ach.check_condition(10) is True
        assert ach.check_condition(4) is False
    
    def test_check_condition_eq(self):
        """测试 == 条件"""
        ach = AchievementDef(
            id="test",
            name="Test",
            description="Test",
            category="combat",
            points=10,
            condition_type="exact",
            condition_threshold=3,
            condition_operator="eq"
        )
        assert ach.check_condition(3) is True
        assert ach.check_condition(2) is False
        assert ach.check_condition(4) is False
    
    def test_check_condition_lte(self):
        """测试 <= 条件"""
        ach = AchievementDef(
            id="test",
            name="Test",
            description="Test",
            category="combat",
            points=10,
            condition_type="max_turns",
            condition_threshold=10,
            condition_operator="lte"
        )
        assert ach.check_condition(10) is True
        assert ach.check_condition(5) is True
        assert ach.check_condition(11) is False
    
    def test_check_condition_gt(self):
        """测试 > 条件"""
        ach = AchievementDef(
            id="test",
            name="Test",
            description="Test",
            category="combat",
            points=10,
            condition_type="damage",
            condition_threshold=100,
            condition_operator="gt"
        )
        assert ach.check_condition(101) is True
        assert ach.check_condition(100) is False
        assert ach.check_condition(99) is False
    
    def test_check_condition_lt(self):
        """测试 < 条件"""
        ach = AchievementDef(
            id="test",
            name="Test",
            description="Test",
            category="combat",
            points=10,
            condition_type="hp_left",
            condition_threshold=10,
            condition_operator="lt"
        )
        assert ach.check_condition(9) is True
        assert ach.check_condition(10) is False
        assert ach.check_condition(11) is False


class TestAchievementProgress:
    """成就进度测试"""
    
    def test_is_unlocked(self):
        """测试解锁状态"""
        progress = AchievementProgress(achievement_id="test")
        assert progress.is_unlocked() is False
        
        progress.unlocked_at = "2024-01-01T00:00:00"
        assert progress.is_unlocked() is True
    
    def test_update(self):
        """测试更新"""
        progress = AchievementProgress(achievement_id="test")
        
        result = progress.update(5)
        assert result is True
        assert progress.current_value == 5
        
        # 已解锁后不再更新
        progress.unlocked_at = "2024-01-01T00:00:00"
        result = progress.update(10)
        assert result is False


class TestAchievementManager:
    """成就管理器测试"""
    
    def test_init_empty(self):
        """测试空初始化"""
        manager = AchievementManager()
        assert len(manager.get_unlocked()) == 0
        # 排除隐藏成就
        hidden_count = sum(1 for ach in ACHIEVEMENT_DEFINITIONS.values() if ach.hidden)
        assert len(manager.get_locked()) == len(ACHIEVEMENT_DEFINITIONS) - hidden_count
    
    def test_init_with_unlocked(self):
        """测试带已解锁成就初始化"""
        manager = AchievementManager(profile_achievements=["first_blood", "elite_hunter"])
        assert "first_blood" in manager.get_unlocked()
        assert "elite_hunter" in manager.get_unlocked()
        assert len(manager.get_unlocked()) == 2
    
    def test_check_and_unlock(self):
        """测试检查和解锁"""
        manager = AchievementManager()
        
        # 尚未解锁
        assert "first_blood" not in manager.get_unlocked()
        
        # 触发解锁条件
        newly_unlocked = manager.check_and_unlock("enemy_kills", 1)
        assert "first_blood" in newly_unlocked
        assert "first_blood" in manager.get_unlocked()
    
    def test_check_and_unlock_multiple(self):
        """测试批量解锁（使用相同 condition_type）"""
        manager = AchievementManager()
        
        # 测试 chapter_victor (1 chapter) 和 chapter_2_complete (2 chapters)
        newly_unlocked = manager.check_and_unlock("chapters_completed", 2)
        assert "chapter_victor" in newly_unlocked  # 1 chapter
        assert "chapter_2_complete" in newly_unlocked  # 2 chapters
        
        # 已解锁的不会再出现
        newly_unlocked = manager.check_and_unlock("chapters_completed", 5)
        assert len(newly_unlocked) == 0
    
    def test_update_stat(self):
        """测试统计更新"""
        manager = AchievementManager()
        
        # 分次更新（update_stat 会累加并检查）
        # 1 chapter 解锁 chapter_victor
        newly = manager.update_stat("chapters_completed", 1)
        assert "chapter_victor" in manager.get_unlocked()
        assert "chapter_victor" in newly
        
        # 再 1 chapter（累计 2）解锁 chapter_2_complete
        newly = manager.update_stat("chapters_completed", 1)
        assert "chapter_2_complete" in newly
    
    def test_calculate_points(self):
        """测试点数计算"""
        manager = AchievementManager(profile_achievements=["first_blood", "elite_hunter"])
        
        points = manager.calculate_points()
        # first_blood: 10, elite_hunter: 30 = 40
        assert points == 40
    
    def test_get_by_category(self):
        """测试按类别获取"""
        manager = AchievementManager()
        
        combat_achievements = manager.get_by_category("combat")
        assert len(combat_achievements) > 0
        for ach in combat_achievements:
            assert ach.category == "combat"
    
    def test_get_unlocked_by_category(self):
        """测试按类别获取已解锁"""
        manager = AchievementManager(profile_achievements=["first_blood", "elite_hunter", "boss_slayer"])
        
        combat = manager.get_unlocked_by_category("combat")
        assert "first_blood" in combat
        assert "elite_hunter" in combat
        assert "boss_slayer" in combat
        
        exploration = manager.get_unlocked_by_category("exploration")
        assert len(exploration) == 0
    
    def test_session_stats(self):
        """测试会话统计"""
        manager = AchievementManager()
        
        manager.update_stat("damage_dealt", 100)
        manager.update_stat("damage_dealt", 200)  # total: 300
        
        stats = manager.get_session_stats()
        assert stats["damage_dealt"] == 300
    
    def test_to_dict(self):
        """测试序列化"""
        manager = AchievementManager(profile_achievements=["first_blood"])
        manager.get_progress("first_blood").current_value = 5
        
        data = manager.to_dict()
        
        assert "first_blood" in data["unlocked"]
        assert data["progress"]["first_blood"]["current_value"] == 5
    
    def test_from_dict(self):
        """测试反序列化"""
        data = {
            "unlocked": ["first_blood", "elite_hunter"],
            "progress": {
                "first_blood": {"current_value": 5, "unlocked_at": "2024-01-01"},
                "elite_hunter": {"current_value": 10, "unlocked_at": None}
            }
        }
        
        manager = AchievementManager.from_dict(data)
        
        assert "first_blood" in manager.get_unlocked()
        assert "elite_hunter" in manager.get_unlocked()
        assert manager.get_progress("first_blood").current_value == 5
        assert manager.get_progress("elite_hunter").current_value == 10


class TestAchievementFileIO:
    """成就文件IO测试"""
    
    def test_save_and_load(self):
        """测试保存和加载"""
        manager = AchievementManager(profile_achievements=["first_blood"])
        manager.update_stat("enemy_kills", 5)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "achievements.json")
            
            # 保存
            assert save_achievements(manager, path) is True
            
            # 加载
            loaded = load_achievements(path)
            assert loaded is not None
            assert "first_blood" in loaded.get_unlocked()
            assert loaded.calculate_points() == 10
    
    def test_load_nonexistent(self):
        """测试加载不存在的文件"""
        loaded = load_achievements("/nonexistent/path.json")
        assert loaded is None


class TestAchievementDisplay:
    """成就显示测试"""
    
    def test_format_achievement_display_locked(self):
        """测试格式化未解锁成就"""
        ach = ACHIEVEMENT_DEFINITIONS["first_blood"]
        progress = AchievementProgress(achievement_id="first_blood", current_value=0)
        
        display = format_achievement_display(ach, progress)
        
        assert "🔒" in display
        assert "First Blood" in display
        assert "(0/1)" in display
    
    def test_format_achievement_display_unlocked(self):
        """测试格式化已解锁成就"""
        ach = ACHIEVEMENT_DEFINITIONS["first_blood"]
        progress = AchievementProgress(
            achievement_id="first_blood",
            current_value=1,
            unlocked_at="2024-01-01T00:00:00"
        )
        
        display = format_achievement_display(ach, progress)
        
        assert "✅" in display
        assert "(0/1)" not in display
    
    def test_format_achievement_display_no_progress(self):
        """测试格式化无进度成就"""
        ach = ACHIEVEMENT_DEFINITIONS["first_blood"]
        
        display = format_achievement_display(ach)
        
        assert "First Blood" in display
    
    def test_get_achievement_summary(self):
        """测试成就总结"""
        manager = AchievementManager(profile_achievements=["first_blood"])
        
        summary = get_achievement_summary(manager)
        
        assert "🏆 成就: 1/" in summary
        assert "⭐ 总点数: 10" in summary
        assert "combat:" in summary


class TestAchievementDefinitions:
    """成就定义完整性测试"""
    
    def test_all_definitions_have_required_fields(self):
        """测试所有定义都有必需字段"""
        for ach_id, ach in ACHIEVEMENT_DEFINITIONS.items():
            assert ach.id == ach_id
            assert ach.name
            assert ach.description
            assert ach.category in ["combat", "exploration", "collection", "special"]
            assert ach.points >= 0
            assert ach.condition_type
            assert ach.condition_operator in ["gte", "eq", "lte", "gt", "lt"]
    
    def test_first_blood_exists(self):
        """测试关键成就存在"""
        assert "first_blood" in ACHIEVEMENT_DEFINITIONS
        assert ACHIEVEMENT_DEFINITIONS["first_blood"].condition_type == "enemy_kills"
    
    def test_boss_slayer_exists(self):
        """测试BOSS成就存在"""
        assert "boss_slayer" in ACHIEVEMENT_DEFINITIONS
        assert ACHIEVEMENT_DEFINITIONS["boss_slayer"].condition_type == "boss_kills"
    
    def test_no_damage_elite_exists(self):
        """测试无伤精英成就存在"""
        assert "no_damage_elite" in ACHIEVEMENT_DEFINITIONS
        assert ACHIEVEMENT_DEFINITIONS["no_damage_elite"].condition_threshold == 0
    
    def test_hidden_achievements(self):
        """测试隐藏成就"""
        hidden = [ach for ach in ACHIEVEMENT_DEFINITIONS.values() if ach.hidden]
        # perfectionist 应该是隐藏成就
        assert len(hidden) > 0
        assert any(ach.id == "perfectionist" for ach in hidden)
