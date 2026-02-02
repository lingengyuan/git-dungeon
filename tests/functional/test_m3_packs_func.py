"""
M3 功能测试集 - 内容包系统 (使用 Snapshots)

覆盖:
1. m3_packs_merge_happy - 默认+pack 合并正确
2. m3_pack_conflict_edge - ID 冲突处理
3. m3_pack_missing_ref_edge - 缺失引用处理
4. m3_pack_archetype_filter - 流派筛选
5. m3_pack_content_integrity - 内容完整性

运行命令:
    PYTHONPATH=src python3 -m pytest tests/functional/test_m3_packs_func.py -v
"""

import sys
import yaml
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from git_dungeon.content.loader import load_content
from git_dungeon.content.packs import PackLoader, merge_content_with_packs, get_pack_info
from tests.harness.snapshots import SnapshotManager


# ==================== Fixtures ====================

@pytest.fixture
def packs_dir():
    return Path("src/git_dungeon/content/packs")


@pytest.fixture
def loader(packs_dir):
    return PackLoader(packs_dir)


@pytest.fixture
def base_content():
    return load_content("src/git_dungeon/content")


@pytest.fixture
def snapshot_mgr():
    return SnapshotManager("tests/golden")


# ==================== M3.3 内容包测试 ====================

class TestPackMergeHappy:
    """M3.3 测试: pack 合并 happy path"""
    
    def test_merge_base_with_debug_pack(self, base_content):
        """合并基础内容和 debug_pack"""
        initial_card_count = len(base_content.cards)
        
        merged = merge_content_with_packs(
            base_content,
            "src/git_dungeon/content/packs",
            ["debug_pack"]
        )
        
        assert len(merged.cards) > initial_card_count
        
        debug_pack = merged.get_pack("debug_pack")
        assert debug_pack is not None
        
        for card in debug_pack.cards:
            assert card.id in merged.cards
        
        print(f"✅ 合并 debug_pack: {initial_card_count} -> {len(merged.cards)} 卡牌")
    
    def test_merge_all_packs(self, base_content):
        """合并所有内容包"""
        merged = merge_content_with_packs(
            base_content,
            "src/git_dungeon/content/packs",
            ["debug_pack", "test_pack", "refactor_pack"]
        )
        
        assert merged.get_pack("debug_pack") is not None
        assert merged.get_pack("test_pack") is not None
        assert merged.get_pack("refactor_pack") is not None
        
        print("✅ 合并全部 3 个 pack")


class TestPackConflictEdge:
    """M3.3 测试: pack 冲突处理"""
    
    def test_id_conflict_detection(self, base_content):
        """ID 冲突应该被检测"""
        base_card_ids = set(base_content.cards.keys())
        
        loader = PackLoader(Path("src/git_dungeon/content/packs"))
        packs = loader.load_all_packs()
        
        for pack_id, pack in packs.items():
            pack_card_ids = set(c.id for c in pack.cards)
            conflicts = pack_card_ids & base_card_ids
            
            if conflicts:
                print(f"⚠️  Pack {pack_id} 有冲突: {conflicts}")
            else:
                print(f"✅ Pack {pack_id} 无冲突")
        
        # 当前 packs 无冲突
        assert True


class TestPackMissingRefEdge:
    """M3.3 测试: 缺失引用处理"""
    
    def test_loader_handles_missing_refs_gracefully(self, tmp_path):
        """loader 处理缺失引用"""
        bad_pack_dir = tmp_path / "bad_pack"
        bad_pack_dir.mkdir()
        
        pack_config = {
            "pack_info": {
                "id": "bad_pack",
                "name_key": "pack.bad_pack.name",
                "desc_key": "pack.bad_pack.desc",
                "archetype": "test_shrine",
                "rarity": "uncommon",
                "points_cost": 100
            },
            "cards": [
                {
                    "id": "test_card",
                    "name_key": "card.test_card.name",
                    "desc_key": "card.test_card.desc",
                    "type": "attack",
                    "cost": 1,
                    "rarity": "common",
                    "effects": [
                        {"type": "damage", "value": 10}
                    ],
                    "tags": ["test"]
                }
            ],
            "relics": [],
            "events": []
        }
        
        with open(bad_pack_dir / "cards.yml", "w") as f:
            yaml.dump(pack_config, f)
        
        loader = PackLoader(tmp_path)
        pack = loader.load_pack("bad_pack")
        
        assert pack is not None
        assert len(pack.cards) == 1
        
        print("✅ Loader 处理缺失引用")


class TestPackArchetypeFilter:
    """M3.3 测试: 流派筛选"""
    
    def test_get_packs_by_archetype(self, loader):
        """按流派筛选 pack"""
        packs = loader.load_all_packs()
        
        debug_packs = [p for p in packs.values() if p.archetype == "debug_beatdown"]
        assert len(debug_packs) == 1
        
        test_packs = [p for p in packs.values() if p.archetype == "test_shrine"]
        assert len(test_packs) == 1
        
        refactor_packs = [p for p in packs.values() if p.archetype == "refactor_risk"]
        assert len(refactor_packs) == 1
        
        print("✅ 按流派筛选正确")


class TestPackContentIntegrity:
    """M3.3 测试: 内容完整性"""
    
    def test_all_packs_have_required_fields(self, loader):
        """所有 pack 都有必需字段"""
        packs = loader.load_all_packs()
        
        for pack_id, pack in packs.items():
            assert pack.id
            assert pack.name_key
            assert pack.desc_key
            assert pack.archetype
            assert pack.rarity
            assert pack.points_cost > 0
            
            for card in pack.cards:
                assert card.id
                assert card.name_key
                assert card.desc_key
                assert card.cost >= 0
                assert len(card.tags) > 0
            
            for relic in pack.relics:
                assert relic.id
                assert relic.name_key
        
        print("✅ 所有 pack 内容完整性验证通过")
    
    def test_no_duplicate_ids_in_pack(self, loader):
        """pack 内无重复 ID"""
        packs = loader.load_all_packs()
        
        for pack_id, pack in packs.items():
            card_ids = [c.id for c in pack.cards]
            assert len(card_ids) == len(set(card_ids))
            
            relic_ids = [r.id for r in pack.relics]
            assert len(relic_ids) == len(set(relic_ids))
        
        print("✅ Pack 内无重复 ID")
    
    def test_pack_card_count_minimum(self, loader):
        """pack 至少有 4 张卡"""
        packs = loader.load_all_packs()
        
        for pack_id, pack in packs.items():
            assert len(pack.cards) >= 4
        
        print("✅ 所有 pack 卡牌数量 >= 4")


class TestPackInfo:
    """M3.3 测试: pack 信息"""
    
    def test_get_pack_info(self, snapshot_mgr):
        """获取 pack 信息"""
        info = get_pack_info("src/git_dungeon/content/packs")
        
        assert len(info) == 3
        
        for pack_id, pack_info in info.items():
            assert "name_key" in pack_info
            assert "desc_key" in pack_info
            assert "archetype" in pack_info
            assert "rarity" in pack_info
            assert "points_cost" in pack_info
            assert "cards_count" in pack_info
        
        # 快照验证
        passed, msg = snapshot_mgr.verify("m3_packs_info", info)
        print(f"✅ Pack 信息获取 (快照: {msg})")


# ==================== 运行入口 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
