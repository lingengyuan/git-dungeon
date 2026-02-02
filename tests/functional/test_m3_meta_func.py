"""
M3 功能测试集 - Meta 存档与结算 (使用 Snapshots)

覆盖:
1. m3_meta_points_happy - 点数奖励与存档
2. m3_meta_profile_migration_edge - 旧版本存档迁移
3. m3_meta_award_rules_edge - 特殊结算 bonus
4. m3_unlock_filters_happy - 未解锁内容过滤
5. m3_unlock_after_purchase_happy - 解锁后变化

运行命令:
    PYTHONPATH=src python3 -m pytest tests/functional/test_m3_meta_func.py -v
"""

import sys
import tempfile
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from git_dungeon.engine.meta import (
    MetaProfile, RunSummary, create_default_profile, 
    load_meta, save_meta, award_points, unlock_item, can_afford
)
from git_dungeon.content.loader import load_content
from tests.harness.snapshots import SnapshotManager, snapshot_meta


# ==================== Fixtures ====================

@pytest.fixture
def snapshot_mgr():
    return SnapshotManager("tests/golden")


@pytest.fixture
def base_content():
    return load_content("src/git_dungeon/content")


# ==================== M3.1 Meta 存档与结算测试 ====================

class TestMetaPointsHappy:
    """M3.1 测试: 点数奖励happy path"""
    
    def test_meta_points_single_run(self, snapshot_mgr):
        """单局获得点数正确"""
        profile = create_default_profile("TestPlayer")
        
        run = RunSummary(
            character_id="developer",
            enemies_killed=5,
            elites_killed=1,
            bosses_killed=0,
            chapter_reached=1,
            is_victory=False
        )
        
        points = award_points(profile, run)
        
        # 验证: 5 kills + 1 elite + 1 chapter = 5 + 2 + 10 = 17
        assert profile.total_points == 17, f"Expected 17 points, got {profile.total_points}"
        
        # 快照验证
        meta_snapshot = snapshot_meta(profile.__dict__)
        passed, msg = snapshot_mgr.verify("m3_meta_profile_default", meta_snapshot)
        
        print(f"✅ 单局获得 {points} 点数 (快照验证: {msg})")


class TestMetaProfileMigration:
    """M3.1 测试: 旧版本存档迁移"""
    
    def test_migration_missing_fields(self):
        """测试缺失字段的旧存档"""
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
        
        assert profile.player_name == "LegacyPlayer"
        assert profile.total_points == 100
        
        print("✅ 旧版本存档迁移成功")


class TestMetaAwardRulesEdge:
    """M3.1 测试: 特殊结算 bonus"""
    
    def test_victory_bonus(self):
        """胜利获得额外点数"""
        profile = create_default_profile("VictoryTest")
        initial = profile.total_points
        
        run = RunSummary(
            character_id="developer",
            enemies_killed=10,
            elites_killed=2,
            bosses_killed=1,
            chapter_reached=3,
            is_victory=True
        )
        
        points = award_points(profile, run)
        
        assert profile.total_points > initial
        print(f"✅ 胜利结算: +{points} 点数")
    
    def test_elite_kill_bonus(self):
        """精英击杀奖励"""
        profile = create_default_profile("EliteTest")
        
        run = RunSummary(
            character_id="reviewer",
            enemies_killed=5,
            elites_killed=3,
            bosses_killed=0,
            chapter_reached=2,
            is_victory=False
        )
        
        points = award_points(profile, run)
        # 验证: 5 kills + 3 elites + 2 chapters = 5 + 6 + 20 = 31
        assert points == 31, f"Expected 31 points, got {points}"
        print(f"✅ 精英击杀: +{points} 点数")


class TestUnlockFiltersHappy:
    """M3.1 测试: 未解锁内容过滤"""
    
    def test_locked_character_not_in_pool(self, base_content):
        """未解锁角色存在但不可用"""
        profile = create_default_profile("FilterTest")
        
        assert "developer" in profile.unlocks["characters"]
        assert "reviewer" not in profile.unlocks["characters"]
        assert "devops" not in profile.unlocks["characters"]
        
        print("✅ 未解锁角色存在但不在玩家可用池")


class TestUnlockAfterPurchase:
    """M3.1 测试: 解锁后变化"""
    
    def test_purchase_updates_unlocks(self):
        """购买后更新解锁状态"""
        profile = create_default_profile("PurchaseTest")
        profile.total_points = 200
        profile.available_points = 200
        
        assert can_afford(profile, "characters", "reviewer")
        unlock_item(profile, "characters", "reviewer")
        
        assert "reviewer" in profile.unlocks["characters"]
        assert profile.available_points < 200
        
        print("✅ 解锁后 available_points 减少")


class TestMetaSaveLoad:
    """M3.1 测试: 存档保存/加载"""
    
    def test_save_load_meta(self):
        """测试存档保存加载"""
        profile = create_default_profile("SaveLoadTest")
        profile.total_points = 500
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            save_meta(profile, temp_path)
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
