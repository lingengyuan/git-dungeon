"""
M3 元进度系统测试

测试 Meta 存档、角色系统、解锁功能
"""

import sys
import os
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from git_dungeon.engine.meta import (
    MetaProfile, RunSummary, load_meta, save_meta, award_points,
    get_available_unlocks, can_afford, unlock_item,
    create_default_profile, UNLOCK_DEFINITIONS
)
from git_dungeon.content.loader import load_content


def test_meta_profile_create():
    """测试创建玩家档案"""
    print("=" * 50)
    print("🧪 测试: 创建玩家档案")
    print("=" * 50)
    
    profile = create_default_profile("TestPlayer")
    
    assert profile.player_name == "TestPlayer"
    assert profile.profile_id != ""
    assert "developer" in profile.unlocks["characters"]
    assert profile.total_points == 0
    assert profile.available_points == 0
    
    print(f"✅ 档案创建成功: {profile.player_name}")
    print(f"   ID: {profile.profile_id}")
    print(f"   已解锁角色: {profile.unlocks['characters']}")


def test_meta_serialization():
    """测试存档序列化"""
    print("\n" + "=" * 50)
    print("🧪 测试: 存档序列化")
    print("=" * 50)
    
    profile = create_default_profile("SaveTest")
    profile.total_points = 150
    profile.available_points = 50
    profile.unlocks["achievements"].append("first_blood")
    profile.stats["total_runs"] = 5
    profile.stats["enemies_killed"] = 20
    
    # 序列化
    data = profile.to_dict()
    assert data["player_name"] == "SaveTest"
    assert data["total_points"] == 150
    assert "first_blood" in data["unlocks"]["achievements"]
    
    # 反序列化
    restored = MetaProfile.from_dict(data)
    assert restored.player_name == "SaveTest"
    assert restored.total_points == 150
    assert restored.stats["total_runs"] == 5
    
    print(f"✅ 序列化/反序列化成功")
    print(f"   原始点数: {profile.total_points}")
    print(f"   恢复点数: {restored.total_points}")


def test_meta_save_load():
    """测试存档保存/加载"""
    print("\n" + "=" * 50)
    print("🧪 测试: 存档保存/加载")
    print("=" * 50)
    
    profile = create_default_profile("FileTest")
    profile.total_points = 300
    
    # 使用临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        # 保存
        success = save_meta(profile, temp_path)
        assert success, "保存失败"
        print(f"✅ 保存成功: {temp_path}")
        
        # 加载
        loaded = load_meta(temp_path)
        assert loaded is not None, "加载返回 None"
        assert loaded.player_name == "FileTest"
        assert loaded.total_points == 300
        print(f"✅ 加载成功")
        print(f"   玩家: {loaded.player_name}")
        print(f"   点数: {loaded.total_points}")
    finally:
        os.unlink(temp_path)


def test_award_points():
    """测试点数奖励"""
    print("\n" + "=" * 50)
    print("🧪 测试: 点数奖励")
    print("=" * 50)
    
    profile = create_default_profile("PointsTest")
    initial_points = profile.total_points
    
    # 创建单局总结
    run = RunSummary(
        character_id="developer",
        archetype="debug_beatdown",
        chapter_reached=2,
        enemies_killed=10,
        elites_killed=2,
        bosses_killed=0,
        gold_earned=100,
        death_reason="damage",
        is_victory=False,
        final_archetype_bias={"debug_beatdown": 0.8}
    )
    
    # 奖励点数
    points = award_points(profile, run)
    
    # 期望: 10(敌) + 4(精英) + 20(章节) = 34
    expected = 10 + 2*2 + 2*10  # 基础 + 精英加成 + 章节
    assert points == expected, f"期望 {expected}, 实际 {points}"
    
    assert profile.total_points == initial_points + points
    assert profile.available_points == initial_points + points
    assert profile.stats["total_runs"] == 1
    assert profile.stats["enemies_killed"] == 10
    assert profile.stats["elites_killed"] == 2
    assert profile.stats["max_chapter_reached"] == 2
    
    print(f"✅ 点数奖励计算正确: +{points}")
    print(f"   总点数: {profile.total_points}")
    print(f"   可用点数: {profile.available_points}")
    print(f"   击杀敌人: {profile.stats['enemies_killed']}")


def test_award_points_victory():
    """测试胜利额外奖励"""
    print("\n" + "=" * 50)
    print("🧪 测试: 胜利奖励")
    print("=" * 50)
    
    profile = create_default_profile("VictoryTest")
    
    # 胜利局
    victory_run = RunSummary(
        character_id="developer",
        is_victory=True,
        chapter_reached=3,
        enemies_killed=15,
        elites_killed=3,
        bosses_killed=1,
        death_reason=""
    )
    
    points = award_points(profile, victory_run)
    
    # 胜利额外 +50
    assert points > 50, f"胜利应有额外奖励, 实际 {points}"
    assert profile.stats["victories"] == 1
    
    print(f"✅ 胜利奖励: +{points} (含胜利加成)")
    print(f"   胜利次数: {profile.stats['victories']}")


def test_unlocks_system():
    """测试解锁系统"""
    print("\n" + "=" * 50)
    print("🧪 测试: 解锁系统")
    print("=" * 50)
    
    profile = create_default_profile("UnlockTest")
    profile.total_points = 200
    profile.available_points = 200
    
    # 检查可解锁内容
    available = get_available_unlocks(profile)
    
    assert "reviewer" in [c["id"] for c in available["characters"]]
    assert "devops" in [c["id"] for c in available["characters"]]
    
    # 解锁 Reviewer (需要 100 点)
    can_unlock = can_afford(profile, "characters", "reviewer")
    assert can_unlock, "应该可以解锁 Reviewer"
    
    success = unlock_item(profile, "characters", "reviewer")
    assert success, "解锁应该成功"
    assert "reviewer" in profile.unlocks["characters"]
    assert profile.available_points == 100  # 200 - 100
    
    # 尝试再次解锁 (应该失败，因为已解锁)
    success2 = unlock_item(profile, "characters", "reviewer")
    assert not success2, "已解锁不应再解锁"
    
    # 钱不够解锁 DevOps (需要 200 点，只有 100)
    cannot_unlock = can_afford(profile, "characters", "devops")
    assert not cannot_unlock, "不应该可以解锁 DevOps"
    
    print(f"✅ 解锁系统工作正常")
    print(f"   已解锁: {profile.unlocks['characters']}")
    print(f"   剩余点数: {profile.available_points}")


def test_character_loading():
    """测试角色加载"""
    print("\n" + "=" * 50)
    print("🧪 测试: 角色加载")
    print("=" * 50)
    
    content_dir = Path("src/git_dungeon/content")
    content = load_content(str(content_dir))
    
    # 检查角色
    assert "developer" in content.characters
    assert "reviewer" in content.characters
    assert "devops" in content.characters
    
    developer = content.characters["developer"]
    assert len(developer.starter_cards) >= 5
    assert len(developer.starter_relics) >= 1
    
    reviewer = content.characters["reviewer"]
    assert len(reviewer.starter_cards) >= 5, f"Reviewer 起始卡应 >= 5, 实际 {len(reviewer.starter_cards)}"
    assert "test_framework" in reviewer.starter_relics, "Reviewer 有 test_framework 遗物"
    
    devops = content.characters["devops"]
    assert "ci_pipeline" in devops.starter_cards, "DevOps 有 ci_pipeline 卡"
    assert "staging_deploy" in devops.starter_cards, "DevOps 有 staging_deploy 卡"
    
    print(f"✅ 角色加载成功:")
    print(f"   Developer: {len(developer.starter_cards)} 起始卡")
    print(f"   Reviewer: {len(reviewer.starter_cards)} 起始卡, {len(reviewer.abilities)} 能力")
    print(f"   DevOps: {len(devops.starter_cards)} 起始卡")


def test_run_summary():
    """测试单局总结"""
    print("\n" + "=" * 50)
    print("🧪 测试: 单局总结")
    print("=" * 50)
    
    run = RunSummary(
        character_id="reviewer",
        archetype="test_shrine",
        chapter_reached=2,
        enemies_killed=8,
        elites_killed=1,
        bosses_killed=0,
        gold_earned=80,
        cards_obtained=["test_guard", "purify"],
        relics_obtained=["clean_code"],
        death_reason="tech_debt",
        key_cards=["test_guard"],
        key_relics=["clean_code"],
        final_archetype_bias={"test_shrine": 0.7, "debug_beatdown": 0.3}
    )
    
    data = run.to_dict()
    assert data["character_id"] == "reviewer"
    assert data["death_reason"] == "tech_debt"
    assert len(data["cards_obtained"]) == 2
    
    restored = RunSummary.from_dict(data)
    assert restored.character_id == "reviewer"
    assert restored.archetype == "test_shrine"
    
    print(f"✅ 单局总结序列化成功")
    print(f"   角色: {run.character_id}")
    print(f"   流派: {run.archetype}")
    print(f"   章节: {run.chapter_reached}")
    print(f"   死亡: {run.death_reason}")


def test_achievement_unlocked():
    """测试成就解锁"""
    print("\n" + "=" * 50)
    print("🧪 测试: 成就解锁")
    print("=" * 50)
    
    profile = create_default_profile("AchievementTest")
    
    # 首次击杀 BOSS 应该解锁成就
    run = RunSummary(
        character_id="developer",
        bosses_killed=1,
        enemies_killed=5,
        is_victory=True
    )
    
    award_points(profile, run)
    
    assert "boss_slayer" in profile.unlocks["achievements"]
    print(f"✅ 成就解锁: boss_slayer")
    print(f"   已解锁成就: {profile.unlocks['achievements']}")


def test_content_verification():
    """测试 M3 内容验证"""
    print("\n" + "=" * 50)
    print("📦 M3 内容验证")
    print("=" * 50)
    
    content_dir = Path("src/git_dungeon/content")
    content = load_content(str(content_dir))
    
    # 验证角色数量
    assert len(content.characters) == 3, f"期望 3 角色, 实际 {len(content.characters)}"
    
    # 验证角色属性
    for char_id, char in content.characters.items():
        assert len(char.starter_cards) >= 5, f"{char_id} 起始卡不足"
        assert len(char.starter_relics) >= 1, f"{char_id} 起始遗物不足"
    
    print(f"✅ 内容验证通过:")
    print(f"   角色: {len(content.characters)}")
    for char_id, char in content.characters.items():
        print(f"      {char_id}: {len(char.starter_cards)} 卡, {len(char.starter_relics)} 遗物")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🧪 Git Dungeon M3 元进度系统测试")
    print("=" * 60 + "\n")
    
    test_meta_profile_create()
    test_meta_serialization()
    test_meta_save_load()
    test_award_points()
    test_award_points_victory()
    test_unlocks_system()
    test_character_loading()
    test_run_summary()
    test_achievement_unlocked()
    test_content_verification()
    
    print("\n" + "=" * 60)
    print("✅ M3 元进度系统测试全部通过!")
    print("=" * 60)


if __name__ == "__main__":
    main()
