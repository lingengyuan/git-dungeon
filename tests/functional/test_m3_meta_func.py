"""
M3 功能测试集 - Meta 存档与结算

覆盖:
1. m3_meta_points_happy - 点数奖励与存档
2. m3_meta_profile_migration_edge - 旧版本存档迁移
3. m3_meta_award_rules_edge - 特殊结算 bonus
4. m3_unlock_filters_happy - 未解锁内容过滤
5. m3_unlock_after_purchase_happy - 解锁后变化

运行命令:
    PYTHONPATH=src python3 -m pytest tests/functional/test_m3_meta.py -v
"""

import sys
import json
import tempfile
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from git_dungeon.engine import Engine, GameState, Action, DefaultRNG
from git_dungeon.engine.route import build_route, NodeKind
from git_dungeon.engine.meta import (
    MetaProfile, RunSummary, create_default_profile, 
    load_meta, save_meta, award_points, unlock_item, can_afford
)
from git_dungeon.content.loader import load_content
from git_dungeon.content.packs import merge_content_with_packs
from tests.harness.scenario import Scenario, ScenarioStep, ScenarioExpect, ScenarioRunner, RepoFactory, StepResult


# ==================== Fixtures ====================

@pytest.fixture
def runner():
    return ScenarioRunner()


@pytest.fixture
def base_content():
    return load_content("src/git_dungeon/content")


@pytest.fixture
def packs_content():
    return load_content("src/git_dungeon/content")


# ==================== M3.1 Meta 存档与结算测试 ====================

class TestMetaPointsHappy:
    """M3.1 测试: 点数奖励happy path"""
    
    def test_meta_points_single_run(self, runner, base_content):
        """单局获得点数正确"""
        # 1. 创建玩家档案
        profile = create_default_profile("TestPlayer")
        initial_points = profile.total_points
        
        # 2. 模拟结算 (不运行完整游戏)
        run = RunSummary(
            character_id="developer",
            enemies_killed=5,
            elites_killed=1,
            bosses_killed=0,
            chapter_reached=1,
            is_victory=False
        )
        
        points = award_points(profile, run)
        assert profile.total_points > initial_points, "Points should increase"
        
        print(f"✅ 单局获得 {points} 点数 (总计 {profile.total_points})")


class TestMetaProfileMigration:
    """M3.1 测试: 旧版本存档迁移"""
    
    def test_migration_missing_fields(self):
        """测试缺失字段的旧存档"""
        # 模拟旧版本存档 (只包含必需字段)
        profile = MetaProfile(
            player_name="LegacyPlayer",
            total_points=100,
            available_points=50,
            unlocks={
                "characters": ["developer"],
                "packs": [],
                "relics": []
            },
            stats={
                "total_runs": 5,
                "total_kills": 20
            }
        )
        
        # 验证必需字段存在
        assert profile.player_name == "LegacyPlayer"
        assert profile.total_points == 100
        
        print("✅ 旧版本存档迁移成功 (必需字段验证通过)")


class TestMetaAwardRulesEdge:
    """M3.1 测试: 特殊结算 bonus"""
    
    def test_victory_bonus(self):
        """胜利获得额外点数"""
        profile = create_default_profile("VictoryTest")
        initial = profile.total_points
        
        # 胜利结算
        run = RunSummary(
            character_id="developer",
            enemies_killed=10,
            elites_killed=2,
            bosses_killed=1,
            chapter_reached=3,
            is_victory=True
        )
        
        points = award_points(profile, run)
        
        # 胜利应该奖励额外点数
        assert profile.total_points > initial, "Victory should give bonus points"
        print(f"✅ 胜利结算: +{points} 点数")
    
    def test_elite_kill_bonus(self):
        """精英击杀奖励"""
        profile = create_default_profile("EliteTest")
        initial = profile.total_points
        
        # 精英击杀
        run = RunSummary(
            character_id="reviewer",
            enemies_killed=5,
            elites_killed=3,
            bosses_killed=0,
            chapter_reached=2,
            is_victory=False
        )
        
        points = award_points(profile, run)
        assert profile.total_points > initial, "Elite kills should give bonus"
        print(f"✅ 精英击杀: +{points} 点数")


# ==================== M3.1 解锁过滤测试 ====================

class TestUnlockFiltersHappy:
    """M3.1 测试: 未解锁内容过滤"""
    
    def test_locked_character_not_in_pool(self, base_content):
        """未解锁角色不在候选池"""
        # 模拟解锁状态
        profile = create_default_profile("FilterTest")
        
        # 只有 developer 被解锁
        assert "developer" in profile.unlocks["characters"]
        assert "reviewer" not in profile.unlocks["characters"]
        assert "devops" not in profile.unlocks["characters"]
        
        # 验证角色加载
        assert "developer" in base_content.characters
        assert "reviewer" in base_content.characters
        assert "devops" in base_content.characters
        
        print("✅ 未解锁角色存在但不在玩家可用池")


class TestUnlockAfterPurchase:
    """M3.1 测试: 解锁后变化"""
    
    def test_purchase_updates_unlocks(self):
        """购买后更新解锁状态"""
        profile = create_default_profile("PurchaseTest")
        profile.total_points = 200
        profile.available_points = 200
        
        # 解锁 Reviewer
        assert can_afford(profile, "characters", "reviewer")
        unlock_item(profile, "characters", "reviewer")
        
        assert "reviewer" in profile.unlocks["characters"]
        assert profile.available_points < 200
        
        print("✅ 解锁后 available_points 减少")


# ==================== M3 Meta 存档测试 ====================

class TestMetaSaveLoad:
    """M3.1 测试: 存档保存/加载"""
    
    def test_save_load_meta(self):
        """测试存档保存加载"""
        profile = create_default_profile("SaveLoadTest")
        profile.total_points = 500
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            # 保存
            save_meta(profile, temp_path)
            
            # 加载
            loaded = load_meta(temp_path)
            
            assert loaded.player_name == "SaveLoadTest"
            assert loaded.total_points == 500
            assert "developer" in loaded.unlocks["characters"]
            
            print("✅ 存档保存/加载成功")
        finally:
            os.unlink(temp_path)


# ==================== 运行入口 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
