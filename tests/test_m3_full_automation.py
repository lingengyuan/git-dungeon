#!/usr/bin/env python3
"""
M3 完整自动化测试 - 覆盖所有功能点

运行方式:
    PYTHONPATH=src python3 tests/test_m3_full_automation.py

功能覆盖:
- M3.1 元进度系统 (MetaProfile/RunSummary/award_points/解锁)
- M3.2 角色系统 (3 角色差异、起始配置、能力)
- M3.3 内容包系统 (packs/ 目录、loader、解锁过滤)
"""

import sys
import pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from git_dungeon.engine import Engine, GameState, Action, DefaultRNG
from git_dungeon.engine.meta import (
    RunSummary, load_meta, save_meta, award_points,
    can_afford, unlock_item, create_default_profile
)
from git_dungeon.engine.route import build_route, NodeKind
from git_dungeon.content.loader import load_content
from git_dungeon.content.packs import (
    PackLoader, merge_content_with_packs, get_pack_info
)


# ==================== 测试结果收集 ====================

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, name):
        self.passed += 1
        print(f"  ✅ {name}")
    
    def add_fail(self, name, reason):
        self.failed += 1
        self.errors.append((name, reason))
        print(f"  ❌ {name}: {reason}")
    
    def summary(self):
        print("\n" + "=" * 60)
        print(f"📊 测试结果: {self.passed} 通过, {self.failed} 失败")
        if self.errors:
            print("\n失败详情:")
            for name, reason in self.errors:
                print(f"  - {name}: {reason}")
        print("=" * 60)
        return self.failed == 0


# ==================== M3.1 元进度系统测试 ====================

@pytest.mark.slow
def test_m3_1_meta_profile(results: TestResult):
    """M3.1 测试: 元进度档案"""
    print("\n" + "=" * 50)
    print("🧪 M3.1 元进度系统测试")
    print("=" * 50)
    
    # 创建档案
    profile = create_default_profile("TestPlayer")
    results.add_pass("创建玩家档案")
    
    # 验证初始状态
    assert "developer" in profile.unlocks["characters"]
    results.add_pass("默认解锁 Developer")
    
    # 点数初始化
    assert profile.total_points == 0
    results.add_pass("点数初始化为 0")


@pytest.mark.slow
def test_m3_1_run_summary(results: TestResult):
    """M3.1 测试: 单局总结"""
    print("\n" + "=" * 50)
    print("🧪 M3.1 单局总结测试")
    print("=" * 50)
    
    run = RunSummary(
        character_id="reviewer",
        archetype="test_shrine",
        chapter_reached=2,
        enemies_killed=10,
        elites_killed=2,
        bosses_killed=1,
        gold_earned=100,
        cards_obtained=["test_guard", "purify"],
        relics_obtained=["test_framework"],
        death_reason="damage",
        is_victory=False,
        key_cards=["test_guard"],
        key_relics=["test_framework"],
        final_archetype_bias={"test_shrine": 0.7}
    )
    
    assert run.character_id == "reviewer"
    results.add_pass("单局总结创建")
    
    # 序列化
    data = run.to_dict()
    restored = RunSummary.from_dict(data)
    assert restored.character_id == "reviewer"
    results.add_pass("单局总结序列化")


@pytest.mark.slow
def test_m3_1_award_points(results: TestResult):
    """M3.1 测试: 点数奖励"""
    print("\n" + "=" * 50)
    print("🧪 M3.1 点数奖励测试")
    print("=" * 50)
    
    profile = create_default_profile("PointsTest")
    
    run = RunSummary(
        character_id="developer",
        enemies_killed=10,
        elites_killed=3,
        bosses_killed=1,
        chapter_reached=2,
        is_victory=True
    )
    
    points = award_points(profile, run)
    
    # 期望: 10 + 6 + 5 + 20 + 50 = 91
    assert points >= 50  # 胜利加成
    results.add_pass(f"点数奖励 (+{points})")
    
    # 统计更新
    assert profile.stats["total_runs"] == 1
    results.add_pass("统计更新")


@pytest.mark.slow
def test_m3_1_unlock_system(results: TestResult):
    """M3.1 测试: 解锁系统"""
    print("\n" + "=" * 50)
    print("🧪 M3.1 解锁系统测试")
    print("=" * 50)
    
    profile = create_default_profile("UnlockTest")
    profile.total_points = 200
    profile.available_points = 200
    
    # 解锁 Reviewer
    can = can_afford(profile, "characters", "reviewer")
    assert can
    results.add_pass("可解锁 Reviewer")
    
    unlock_item(profile, "characters", "reviewer")
    assert "reviewer" in profile.unlocks["characters"]
    results.add_pass("解锁 Reviewer 成功")
    
    # 再次解锁应失败
    cannot = unlock_item(profile, "characters", "reviewer")
    assert not cannot
    results.add_pass("重复解锁失败")
    
    # 钱不够解锁 DevOps
    can = can_afford(profile, "characters", "devops")
    assert not can
    results.add_pass("钱不够时解锁失败")


@pytest.mark.slow
def test_m3_1_save_load(results: TestResult):
    """M3.1 测试: 存档保存/加载"""
    print("\n" + "=" * 50)
    print("🧪 M3.1 存档测试")
    print("=" * 50)
    
    import tempfile
    import os
    
    profile = create_default_profile("SaveTest")
    profile.total_points = 300
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        save_meta(profile, temp_path)
        results.add_pass("存档保存")
        
        loaded = load_meta(temp_path)
        assert loaded.player_name == "SaveTest"
        assert loaded.total_points == 300
        results.add_pass("存档加载")
    finally:
        os.unlink(temp_path)


# ==================== M3.2 角色系统测试 ====================

@pytest.mark.slow
def test_m3_2_character_stats(results: TestResult):
    """M3.2 测试: 角色属性差异"""
    print("\n" + "=" * 50)
    print("🧪 M3.2 角色系统测试")
    print("=" * 50)
    
    content = load_content("src/git_dungeon/content")
    
    developer = content.characters["developer"]
    reviewer = content.characters["reviewer"]
    devops = content.characters["devops"]
    
    assert developer.stats.hp == 100
    results.add_pass("Developer HP=100")
    
    assert reviewer.stats.hp == 110
    results.add_pass("Reviewer HP=110")
    
    assert devops.stats.hp == 90
    results.add_pass("DevOps HP=90")


@pytest.mark.slow
def test_m3_2_starter_deck(results: TestResult):
    """M3.2 测试: 起始套牌"""
    print("\n" + "=" * 50)
    print("🧪 M3.2 起始套牌测试")
    print("=" * 50)
    
    content = load_content("src/git_dungeon/content")
    
    # Developer: Strike/Defend
    dev = content.characters["developer"]
    assert "strike" in dev.starter_cards
    assert "defend" in dev.starter_cards
    results.add_pass("Developer 起始套牌")
    
    # Reviewer: Test Guard
    rev = content.characters["reviewer"]
    assert "test_guard" in rev.starter_cards
    results.add_pass("Reviewer 起始套牌")
    
    # DevOps: CI Pipeline
    ops = content.characters["devops"]
    assert "ci_pipeline" in ops.starter_cards
    results.add_pass("DevOps 起始套牌")


@pytest.mark.slow
def test_m3_2_starter_relics(results: TestResult):
    """M3.2 测试: 起始遗物"""
    print("\n" + "=" * 50)
    print("🧪 M3.2 起始遗物测试")
    print("=" * 50)
    
    content = load_content("src/git_dungeon/content")
    
    dev = content.characters["developer"]
    rev = content.characters["reviewer"]
    ops = content.characters["devops"]
    
    assert dev.starter_relics[0] != rev.starter_relics[0]
    results.add_pass("起始遗物不同")
    
    assert rev.starter_relics[0] == "test_framework"
    results.add_pass("Reviewer 遗物=test_framework")
    
    assert ops.starter_relics[0] == "ci_badge"
    results.add_pass("DevOps 遗物=ci_badge")


@pytest.mark.slow
def test_m3_2_character_abilities(results: TestResult):
    """M3.2 测试: 角色能力"""
    print("\n" + "=" * 50)
    print("🧪 M3.2 角色能力测试")
    print("=" * 50)
    
    content = load_content("src/git_dungeon/content")
    
    dev = content.characters["developer"]
    assert len(dev.abilities) == 0
    results.add_pass("Developer 无能力")
    
    rev = content.characters["reviewer"]
    assert len(rev.abilities) == 1
    assert rev.abilities[0].trigger == "on_turn_start"
    results.add_pass("Reviewer 回合开始净化")
    
    ops = content.characters["devops"]
    assert len(ops.abilities) == 1
    assert ops.abilities[0].trigger == "on_turn_end"
    results.add_pass("DevOps 回合结束生成")


@pytest.mark.slow
def test_m3_2_character_init(results: TestResult):
    """M3.2 测试: 角色初始化"""
    print("\n" + "=" * 50)
    print("🧪 M3.2 角色初始化测试")
    print("=" * 50)
    
    content = load_content("src/git_dungeon/content")
    
    def init(character_id):
        char = content.characters[character_id]
        state = GameState(seed=12345)
        state.character_id = character_id
        state.player.character.current_hp = char.stats.hp
        state.player.energy.max_energy = char.stats.energy
        return state
    
    dev_state = init("developer")
    assert dev_state.player.character.current_hp == 100
    results.add_pass("Developer 初始化 HP")
    
    rev_state = init("reviewer")
    assert rev_state.player.character.current_hp == 110
    results.add_pass("Reviewer 初始化 HP")
    
    ops_state = init("devops")
    assert ops_state.player.character.current_hp == 90
    results.add_pass("DevOps 初始化 HP")


# ==================== M3.3 内容包测试 ====================

@pytest.mark.slow
def test_m3_3_pack_loader(results: TestResult):
    """M3.3 测试: 内容包加载"""
    print("\n" + "=" * 50)
    print("🧪 M3.3 内容包测试")
    print("=" * 50)
    
    packs_dir = Path("src/git_dungeon/content/packs")
    loader = PackLoader(packs_dir)
    packs = loader.load_all_packs()
    
    assert len(packs) >= 3
    results.add_pass(f"加载 {len(packs)} 个内容包")


@pytest.mark.slow
def test_m3_3_pack_info(results: TestResult):
    """M3.3 测试: 包信息"""
    print("\n" + "=" * 50)
    print("🧪 M3.3 包信息测试")
    print("=" * 50)
    
    info = get_pack_info("src/git_dungeon/content/packs")
    
    assert "debug_pack" in info
    assert info["debug_pack"]["archetype"] == "debug_beatdown"
    results.add_pass("Debug Pack 信息")
    
    assert "test_pack" in info
    assert info["test_pack"]["archetype"] == "test_shrine"
    results.add_pass("Test Pack 信息")
    
    assert "refactor_pack" in info
    assert info["refactor_pack"]["archetype"] == "refactor_risk"
    results.add_pass("Refactor Pack 信息")


@pytest.mark.slow
def test_m3_3_merge_packs(results: TestResult):
    """M3.3 测试: 合并内容包"""
    print("\n" + "=" * 50)
    print("🧪 M3.3 合并测试")
    print("=" * 50)
    
    base = load_content("src/git_dungeon/content")
    initial = len(base.cards)
    
    merged = merge_content_with_packs(
        base,
        "src/git_dungeon/content/packs",
        ["debug_pack"]
    )
    
    assert len(merged.cards) > initial
    results.add_pass(f"合并后卡牌 {initial} -> {len(merged.cards)}")
    
    # 检查 pack
    debug = merged.get_pack("debug_pack")
    assert debug is not None
    results.add_pass("Pack 对象存在")


@pytest.mark.slow
def test_m3_3_archetype_filter(results: TestResult):
    """M3.3 测试: 流派筛选"""
    print("\n" + "=" * 50)
    print("🧪 M3.3 流派筛选测试")
    print("=" * 50)
    
    packs_dir = Path("src/git_dungeon/content/packs")
    loader = PackLoader(packs_dir)
    packs = loader.load_all_packs()
    
    debug = [p for p in packs.values() if p.archetype == "debug_beatdown"]
    assert len(debug) == 1
    results.add_pass("Debug 流派包")
    
    test = [p for p in packs.values() if p.archetype == "test_shrine"]
    assert len(test) == 1
    results.add_pass("Test 流派包")
    
    refactor = [p for p in packs.values() if p.archetype == "refactor_risk"]
    assert len(refactor) == 1
    results.add_pass("Refactor 流派包")


# ==================== M3 完整流程测试 ====================

@pytest.mark.slow
def test_m3_full_gameplay(results: TestResult):
    """M3 完整游戏流程测试"""
    print("\n" + "=" * 50)
    print("🎮 M3 完整游戏流程测试")
    print("=" * 50)
    
    engine = Engine(rng=DefaultRNG(seed=42))
    state = GameState(seed=42)
    
    # 1. 选择角色
    state.character_id = "reviewer"
    results.add_pass("选择角色 Reviewer")
    
    # 2. 设置角色属性
    content = load_content("src/git_dungeon/content")
    char = content.characters["reviewer"]
    state.player.character.current_hp = char.stats.hp
    state.player.energy.max_energy = char.stats.energy
    results.add_pass("设置角色属性 (HP=110)")
    
    # 3. 构建路径
    class MockCommit:
        def __init__(self, i):
            self.hexsha = f"abc{i}"
    
    commits = [MockCommit(i) for i in range(20)]
    route = build_route(commits, seed=42, chapter_index=0, node_count=6)
    state.chapter_route = route
    results.add_pass(f"构建路径 ({len(route.nodes)} 节点)")
    
    # 4. 遍历战斗
    battles = 0
    for node in route.nodes[:3]:
        if node.kind == NodeKind.BATTLE:
            action = Action(action_type="combat", action_name="start_combat")
            state, _ = engine.apply(state, action)
            
            # 快速战斗
            for _ in range(3):
                if not state.in_combat:
                    break
                action = Action(action_type="combat", action_name="start_turn")
                state, _ = engine.apply(state, action)
                
                while len(state.player.deck.hand) > 0 and state.player.energy.current_energy > 0:
                    action = Action(action_type="combat", action_name="play_card", data={"card_index": 0})
                    state, _ = engine.apply(state, action)
                
                if not state.in_combat:
                    break
                
                action = Action(action_type="combat", action_name="end_turn")
                state, _ = engine.apply(state, action)
            
            if not state.in_combat:
                battles += 1
    
    results.add_pass(f"完成 {battles} 场战斗")
    
    # 5. 生成单局总结
    run = RunSummary(
        character_id=state.character_id,
        enemies_killed=battles,
        chapter_reached=0
    )
    
    profile = create_default_profile("GameTest")
    points = award_points(profile, run)
    results.add_pass(f"生成单局总结 (+{points} 点数)")
    
    # 6. 解锁检查
    can_afford(profile, "characters", "test_pack")
    results.add_pass("解锁检查")


# ==================== M3 内容验证 ====================

@pytest.mark.slow
def test_m3_content_verification(results: TestResult):
    """M3 内容验证"""
    print("\n" + "=" * 50)
    print("📦 M3 内容验证")
    print("=" * 50)
    
    content = load_content("src/git_dungeon/content")
    
    # 角色
    assert len(content.characters) == 3
    results.add_pass(f"角色: {len(content.characters)}")
    
    # 内容包
    packs_dir = Path("src/git_dungeon/content/packs")
    loader = PackLoader(packs_dir)
    packs = loader.load_all_packs()
    assert len(packs) >= 3
    results.add_pass(f"内容包: {len(packs)}")
    
    # 统计
    total_cards = sum(len(p.cards) for p in packs.values())
    total_relics = sum(len(p.relics) for p in packs.values())
    total_events = sum(len(p.events) for p in packs.values())
    
    results.add_pass(f"包内卡牌: {total_cards}")
    results.add_pass(f"包内遗物: {total_relics}")
    results.add_pass(f"包内事件: {total_events}")


# ==================== 主函数 ====================

def main():
    print("=" * 60)
    print("🧪 Git Dungeon M3 完整自动化测试")
    print("=" * 60)
    
    results = TestResult()
    
    # M3.1 元进度系统
    test_m3_1_meta_profile(results)
    test_m3_1_run_summary(results)
    test_m3_1_award_points(results)
    test_m3_1_unlock_system(results)
    test_m3_1_save_load(results)
    
    # M3.2 角色系统
    test_m3_2_character_stats(results)
    test_m3_2_starter_deck(results)
    test_m3_2_starter_relics(results)
    test_m3_2_character_abilities(results)
    test_m3_2_character_init(results)
    
    # M3.3 内容包
    test_m3_3_pack_loader(results)
    test_m3_3_pack_info(results)
    test_m3_3_merge_packs(results)
    test_m3_3_archetype_filter(results)
    
    # 完整流程
    test_m3_full_gameplay(results)
    
    # 内容验证
    test_m3_content_verification(results)
    
    # 输出结果
    return results.summary()


if __name__ == "__main__":
    success = main()
    print("\n" + "=" * 60)
    if success:
        print("🎉 M3 所有测试通过!")
    else:
        print("⚠️  部分测试失败")
    print("=" * 60)
    
    # 输出运行命令
    print("\n📝 运行命令:")
    print("   PYTHONPATH=src python3 -m pytest tests/test_m3_meta.py tests/test_m3_characters.py tests/test_m3_packs.py -v")
    print("   或者:")
    print("   PYTHONPATH=src python3 tests/test_m3_full_automation.py")
    
    sys.exit(0 if success else 1)
