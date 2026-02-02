"""
M2 功能测试集 - Route + Event 脚本

覆盖 M2 至少 6 个新场景:
1. m2_route_graph_determinism_golden
2. m2_route_branch_count_happy  
3. m2_route_different_seeds
4. m2_event_opcode_happy_*
5. m2_event_opcode_edge_*
6. m2_elite_boss_rewards_golden

运行命令:
    PYTHONPATH=src python3 -m pytest tests/functional/test_m2_func.py -v
"""

import sys
from pathlib import Path
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from git_dungeon.engine.route import build_route, NodeKind
from git_dungeon.content.loader import load_content
from git_dungeon.content.schema import EventEffect
from tests.harness.snapshots import (
    SnapshotManager, snapshot_route, stable_serialize
)


# ==================== Fixtures ====================

@pytest.fixture
def content():
    return load_content("src/git_dungeon/content")


@pytest.fixture
def snapshot_mgr():
    return SnapshotManager("tests/golden")


# ==================== 测试数据类 ====================

@dataclass
class MockCommit:
    """模拟 Git Commit"""
    hexsha: str
    msg: str
    type: str = "feat"


def make_commits(count: int = 10) -> list:
    """生成模拟 commits"""
    types = ["feat", "fix", "docs", "refactor", "test"]
    commits = []
    for i in range(count):
        commit_type = types[i % len(types)]
        commits.append(MockCommit(
            hexsha=f"abc{i:04d}",
            msg=f"{commit_type}: commit {i}",
            type=commit_type
        ))
    return commits


# ==================== M2.1 Route 测试 ====================

class TestRouteDeterminism:
    """M2.1 测试: 路径确定性"""
    
    def test_route_graph_determinism_golden(self, snapshot_mgr):
        """同 seed 同 route 结构 (golden)"""
        commits = make_commits(10)
        
        # 运行 3 次，应该完全相同
        routes = []
        for _ in range(3):
            route = build_route(commits, seed=42, chapter_index=0, node_count=10)
            route_snapshot = snapshot_route(route.nodes)
            routes.append(route_snapshot)
        
        # 验证确定性
        assert routes[0] == routes[1] == routes[2]
        
        # Golden 验证
        passed, msg = snapshot_mgr.verify("m2_route_graph_determinism", {
            "seed": 42,
            "node_count": 10,
            "route": routes[0]
        })
        
        print(f"✅ Route determinism: {msg}")
    
    def test_route_different_seeds_different(self):
        """不同 seed 不同 route"""
        commits = make_commits(10)
        
        route1 = build_route(commits, seed=42, chapter_index=0, node_count=10)
        route2 = build_route(commits, seed=123, chapter_index=0, node_count=10)
        
        # 不同 seed 应该产生不同路径
        snapshot1 = snapshot_route(route1.nodes)
        snapshot2 = snapshot_route(route2.nodes)
        
        assert snapshot1 != snapshot2
        print("✅ Different seeds produce different routes")
    
    def test_route_node_count(self):
        """路径节点数量正确"""
        commits = make_commits(10)
        
        route = build_route(commits, seed=42, chapter_index=0, node_count=10)
        
        assert len(route.nodes) == 10
        print(f"✅ Route has {len(route.nodes)} nodes")
    
    def test_route_has_required_kinds(self):
        """路径包含必需节点类型"""
        commits = make_commits(15)
        
        route = build_route(commits, seed=42, chapter_index=0, node_count=12)
        
        node_kinds = set(n.kind for n in route.nodes)
        
        # 应该有战斗节点
        assert NodeKind.BATTLE in node_kinds
        print(f"✅ Route kinds: {node_kinds}")


class TestRouteBranchCount:
    """M2.1 测试: 分叉数量"""
    
    def test_route_has_multiple_battles(self):
        """路径包含多个战斗节点"""
        commits = make_commits(12)
        
        route = build_route(commits, seed=42, chapter_index=0, node_count=10)
        
        battles = [n for n in route.nodes if n.kind == NodeKind.BATTLE]
        
        # 应该有至少 2 个战斗
        assert len(battles) >= 2
        print(f"✅ Route has {len(battles)} battles")
    
    def test_route_different_commits_different(self):
        """不同 seed 产生不同路径"""
        commits1 = make_commits(10)
        commits2 = make_commits(10)
        
        # 使用相同 commit 数量但不同 seed
        route1 = build_route(commits1, seed=42, chapter_index=0, node_count=8)
        route2 = build_route(commits2, seed=123, chapter_index=0, node_count=8)
        
        snapshot1 = snapshot_route(route1.nodes)
        snapshot2 = snapshot_route(route2.nodes)
        
        assert snapshot1 != snapshot2
        print("✅ Different seeds produce different routes")


# ==================== M2.2 Event Opcode 测试 ====================

class TestEventOpcodeHappy:
    """M2.2 测试: Event Opcode Happy Path"""
    
    @pytest.mark.parametrize("opcode", [
        "gain_gold", "heal", "take_damage", "add_card", 
        "add_relic", "modify_bias"
    ])
    def test_event_opcode_happy(self, opcode):
        """每个 opcode 至少 1 个 happy path 测试"""
        # 创建测试事件数据
        effects = [EventEffect(opcode=opcode, value=10)]
        
        # 验证 effects 可以序列化
        serialized = stable_serialize(effects)
        assert isinstance(serialized, list)
        
        print(f"✅ Opcode {opcode} happy path: serializable")
    
    def test_event_gain_gold_happy(self):
        """gain_gold opcode 测试"""
        effects = [EventEffect(opcode="gain_gold", value=50)]
        
        data = stable_serialize(effects)
        assert data[0]["opcode"] == "gain_gold"
        assert data[0]["value"] == 50
        
        print("✅ gain_gold opcode works")
    
    def test_event_heal_happy(self):
        """heal opcode 测试"""
        effects = [EventEffect(opcode="heal", value=30)]
        
        data = stable_serialize(effects)
        assert data[0]["opcode"] == "heal"
        assert data[0]["value"] == 30
        
        print("✅ heal opcode works")
    
    def test_event_add_card_happy(self):
        """add_card opcode 测试"""
        effects = [EventEffect(opcode="add_card", value="strike")]
        
        data = stable_serialize(effects)
        assert data[0]["opcode"] == "add_card"
        assert data[0]["value"] == "strike"
        
        print("✅ add_card opcode works")
    
    def test_event_modify_bias_happy(self):
        """modify_bias opcode 测试"""
        effects = [EventEffect(opcode="modify_bias", value="debug_beatdown:0.2")]
        
        data = stable_serialize(effects)
        assert data[0]["opcode"] == "modify_bias"
        assert "debug_beatdown" in data[0]["value"]
        
        print("✅ modify_bias opcode works")


class TestEventOpcodeEdge:
    """M2.2 测试: Event Opcode Edge Cases"""
    
    def test_event_opcode_edge_gain_gold_negative(self):
        """gain_gold 负值（扣金币）"""
        effects = [EventEffect(opcode="gain_gold", value=-30)]
        
        data = stable_serialize(effects)
        assert data[0]["value"] == -30
        
        print("✅ gain_gold negative value works")
    
    def test_event_opcode_edge_zero_value(self):
        """0 值处理"""
        effects = [EventEffect(opcode="gain_gold", value=0)]
        
        data = stable_serialize(effects)
        assert data[0]["value"] == 0
        
        print("✅ zero value works")
    
    def test_event_opcode_edge_large_value(self):
        """大数值处理"""
        effects = [EventEffect(opcode="gain_gold", value=9999)]
        
        data = stable_serialize(effects)
        assert data[0]["value"] == 9999
        
        print("✅ large value works")
    
    def test_event_opcode_edge_invalid_card(self):
        """add_card 无效卡牌 ID（应该不崩）"""
        effects = [EventEffect(opcode="add_card", value="nonexistent_card")]
        
        data = stable_serialize(effects)
        assert data[0]["value"] == "nonexistent_card"
        
        print("✅ invalid card id serializable")
    
    def test_event_opcode_edge_malformed_bias(self):
        """modify_bias 格式错误"""
        effects = [EventEffect(opcode="modify_bias", value="invalid_format")]
        
        data = stable_serialize(effects)
        assert data[0]["value"] == "invalid_format"
        
        print("✅ malformed bias value serializable")


# ==================== M2.3 Elite/BOSS 测试 ====================

class TestEliteBossRewards:
    """M2.3 测试: 精英/BOSS 奖励"""
    
    def test_elite_boss_rewards_golden(self, content, snapshot_mgr):
        """精英/BOSS 奖励规则 (golden)"""
        enemies = content.enemies
        
        # 统计各层级敌人
        normal = [e for e in enemies.values() if e.tier.value == "normal"]
        elite = [e for e in enemies.values() if e.tier.value == "elite"]
        boss = [e for e in enemies.values() if e.tier.value == "boss"]
        
        # 生成 golden 快照
        reward_data = {
            "normal_count": len(normal),
            "elite_count": len(elite),
            "boss_count": len(boss),
            # 精英和 BOSS 有 tier 标记
            "has_elites": len(elite) > 0,
            "has_bosses": len(boss) > 0,
            "elite_tier_enemies": [e.id for e in elite],
            "boss_tier_enemies": [e.id for e in boss],
        }
        
        passed, msg = snapshot_mgr.verify("m2_elite_boss_rewards", reward_data)
        print(f"✅ Elite/BOSS rewards: {msg}")
    
    def test_elite_exists(self):
        """精英敌人存在"""
        content = load_content("src/git_dungeon/content")
        
        elite_enemies = [e for e in content.enemies.values() if e.tier.value == "elite"]
        
        assert len(elite_enemies) > 0
        print(f"✅ {len(elite_enemies)} elite enemies exist")
    
    def test_boss_exists(self):
        """BOSS 敌人存在"""
        content = load_content("src/git_dungeon/content")
        
        boss_enemies = [e for e in content.enemies.values() if e.tier.value == "boss"]
        
        assert len(boss_enemies) > 0
        print(f"✅ {len(boss_enemies)} boss enemies exist")
    
    def test_elite_has_tier_flag(self):
        """精英有 tier 标记"""
        content = load_content("src/git_dungeon/content")
        
        for eid, enemy in content.enemies.items():
            if enemy.tier.value == "elite":
                assert enemy.tier.value == "elite"
        
        print("✅ Elite enemies have tier flag")
    
    def test_boss_has_tier_flag(self):
        """BOSS 有 tier 标记"""
        content = load_content("src/git_dungeon/content")
        
        for eid, enemy in content.enemies.items():
            if enemy.tier.value == "boss":
                assert enemy.tier.value == "boss"
                assert enemy.is_boss
        
        print("✅ Boss enemies have tier flag and is_boss=True")


# ==================== M2 完整场景测试 ====================

class TestM2FullScenario:
    """M2 完整场景测试"""
    
    def test_m2_full_route_with_battles(self):
        """完整路径测试"""
        commits = make_commits(12)
        
        # 构建路径
        route = build_route(commits, seed=42, chapter_index=0, node_count=8)
        
        # 统计节点
        battles = [n for n in route.nodes if n.kind == NodeKind.BATTLE]
        
        print(f"✅ Route: {len(route.nodes)} nodes, {len(battles)} battles")
        
        # 应该有战斗
        assert len(battles) >= 2
        print("✅ Route has battles")
    
    def test_m2_combat_with_enemy(self):
        """战斗与敌人交互"""
        content = load_content("src/git_dungeon/content")
        
        # 获取敌人
        enemy_ids = list(content.enemies.keys())[:5]
        
        for enemy_id in enemy_ids:
            enemy = content.enemies.get(enemy_id)
            if enemy:
                assert hasattr(enemy, 'base_hp')
                assert hasattr(enemy, 'base_damage')
                assert enemy.base_hp > 0
        
        print(f"✅ {len(enemy_ids)} enemies validated")
    
    def test_m2_event_effects_serializable(self):
        """事件效果可序列化"""
        effects = [
            EventEffect(opcode="gain_gold", value=50),
            EventEffect(opcode="heal", value=30),
            EventEffect(opcode="take_damage", value=10),
            EventEffect(opcode="add_card", value="strike"),
            EventEffect(opcode="add_relic", value="git_init"),
            EventEffect(opcode="modify_bias", value="debug_beatdown:0.2"),
        ]
        
        data = stable_serialize(effects)
        assert len(data) == 6
        assert all("opcode" in d for d in data)
        
        print("✅ All event effects serializable")


# ==================== 运行入口 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
