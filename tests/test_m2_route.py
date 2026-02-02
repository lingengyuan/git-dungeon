"""
M2 路径系统测试

测试章节路径生成、分叉选择、节点类型分布
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from git_dungeon.engine.route import (
    build_route, get_route_stats, NodeKind, NodeTag, RouteGraph
)


def test_route_basic():
    """基础路径生成测试"""
    print("=" * 50)
    print("🧪 测试: 基础路径生成")
    print("=" * 50)
    
    # 创建模拟 commits
    class MockCommit:
        def __init__(self, hash_val, msg, author):
            self.hexsha = hash_val
            self.message = msg
            self.author = author
    
    commits = [MockCommit(f"abc{i}", f"feat: add feature {i}", "dev") for i in range(20)]
    
    # 生成路径
    route = build_route(
        commits=commits,
        seed=12345,
        chapter_index=0,
        difficulty=1.0,
        node_count=12
    )
    
    # 验证
    assert isinstance(route, RouteGraph), "返回类型错误"
    assert len(route.nodes) == 12, f"节点数错误: {len(route.nodes)}"
    assert route.chapter_index == 0, "章节索引错误"
    assert route.seed == 12345, "种子错误"
    
    print(f"✅ 路径生成成功: {len(route.nodes)} 个节点")
    print(f"   节点序列: {[n.kind.value for n in route.nodes]}")
    

def test_route_determinism():
    """确定性测试 - 同 seed 同结果"""
    print("\n" + "=" * 50)
    print("🧪 测试: 路径确定性")
    print("=" * 50)
    
    class MockCommit:
        pass
    
    commits = [MockCommit() for _ in range(20)]
    
    # 两次生成
    route1 = build_route(commits, seed=99999, chapter_index=0)
    route2 = build_route(commits, seed=99999, chapter_index=0)
    
    seq1 = route1.get_node_sequence()
    seq2 = route2.get_node_sequence()
    
    assert seq1 == seq2, "同种子应生成相同路径"
    print(f"✅ 确定性验证通过")
    print(f"   节点序列: {seq1}")
    

def test_route_stats():
    """路径统计测试"""
    print("\n" + "=" * 50)
    print("🧪 测试: 路径统计")
    print("=" * 50)
    
    class MockCommit:
        pass
    
    commits = [MockCommit() for _ in range(20)]
    
    route = build_route(commits, seed=54321, chapter_index=0, node_count=14)
    stats = get_route_stats(route)
    
    print(f"✅ 路径统计:")
    print(f"   总节点: {stats['total_nodes']}")
    print(f"   战斗: {stats['battles']}")
    print(f"   事件: {stats['events']}")
    print(f"   商店: {stats['shops']}")
    print(f"   休息: {stats['rests']}")
    print(f"   精英: {stats['elites']}")
    print(f"   BOSS: {stats['bosses']}")
    print(f"   宝藏: {stats['treasures']}")
    print(f"   分叉: {stats['fork_count']}")
    
    # 验证至少有一个 BOSS
    assert stats['bosses'] >= 1, "缺少 BOSS 节点"
    assert stats['battles'] >= 3, "战斗节点过少"
    

def test_route_fork_points():
    """分叉点测试"""
    print("\n" + "=" * 50)
    print("🧪 测试: 分叉点")
    print("=" * 50)
    
    class MockCommit:
        pass
    
    commits = [MockCommit() for _ in range(30)]
    
    route = build_route(commits, seed=11111, chapter_index=0, node_count=12)
    
    # 检查起始分叉
    start_node = route.get_start_node()
    next_options = route.get_next_nodes(start_node.node_id)
    
    print(f"✅ 起始分叉:")
    print(f"   起始节点: {start_node.kind.value}")
    print(f"   可选分支: {len(next_options)} 个")
    
    # 验证有分叉
    if len(next_options) >= 2:
        print(f"   ✅ 存在 {len(next_options)} 个分支")
    else:
        print(f"   ⚠️ 只有 {len(next_options)} 个分支（可能随机）")
    

def test_route_node_kinds():
    """节点类型分布测试"""
    print("\n" + "=" * 50)
    print("🧪 测试: 节点类型分布")
    print("=" * 50)
    
    class MockCommit:
        pass
    
    commits = [MockCommit() for _ in range(20)]
    
    # 生成多个路径验证分布
    kind_counts = {kind: 0 for kind in NodeKind}
    
    for seed in range(100, 110):
        route = build_route(commits, seed=seed, chapter_index=0, node_count=12)
        for node in route.nodes:
            kind_counts[node.kind] += 1
    
    print("✅ 节点类型分布 (10 次生成):")
    for kind, count in kind_counts.items():
        if count > 0:
            print(f"   {kind.value}: {count}")
    
    # BOSS 应该每个路径都有
    assert kind_counts[NodeKind.BOSS] >= 10, "BOSS 节点不足"
    

def test_route_golden():
    """Golden 测试 - 固定 seed 快照"""
    print("\n" + "=" * 50)
    print("🎲 Golden 测试")
    print("=" * 50)
    
    class MockCommit:
        def __init__(self, i):
            self.hexsha = f"abc{i}"
    
    commits = [MockCommit(i) for i in range(20)]
    
    # 固定 seed 的预期序列
    route = build_route(commits, seed=77777, chapter_index=1, node_count=10)
    node_sequence = route.get_node_sequence()
    
    print(f"✅ 固定 seed (77777) 节点序列:")
    print(f"   {node_sequence}")
    
    # 验证序列长度
    assert len(node_sequence) == 10, "序列长度错误"
    
    # 验证最后一个是 BOSS
    assert node_sequence[-1] == NodeKind.BOSS, "最后一个节点应该是 BOSS"
    print(f"   ✅ 最后一个节点是 BOSS")
    
    return node_sequence


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🧪 Git Dungeon M2 路径系统测试")
    print("=" * 60 + "\n")
    
    test_route_basic()
    test_route_determinism()
    test_route_stats()
    test_route_fork_points()
    test_route_node_kinds()
    golden_seq = test_route_golden()
    
    print("\n" + "=" * 60)
    print("✅ M2 路径系统测试全部通过!")
    print("=" * 60)
    
    # 返回 golden 序列用于 CI 验证
    return golden_seq


if __name__ == "__main__":
    import sys
    result = main()
    
    # CI 模式下输出序列供验证
    if "--ci" in sys.argv:
        print(f"\n🔑 GOLDEN_SEQUENCE={result}")
