"""
M2.3 精英/BOSS 奖励测试

测试 elite/boss 节点奖励逻辑
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from git_dungeon.engine.rules.rewards import (
    RewardsEngine, EliteRewardsEngine, RewardBundle
)
from git_dungeon.engine.model import GameState, EnemyState
from git_dungeon.engine.rng import DefaultRNG
from git_dungeon.content.schema import EnemyTier


def test_elite_rewards():
    """测试精英敌人奖励"""
    print("=" * 50)
    print("🧪 测试: 精英敌人奖励")
    print("=" * 50)
    
    rng = DefaultRNG(seed=12345)
    state = GameState(seed=12345)
    
    # 创建精英敌人
    elite = EnemyState(
        entity_id="legacy_monolith",
        name="Legacy Monolith",
        enemy_type="feat",
        commit_hash="abc123",
        commit_message="Big legacy code",
        current_hp=80,
        max_hp=80,
        attack=10,
        defense=5,
        exp_reward=50,
        gold_reward=20,
        is_alive=True,
        is_boss=False
    )
    # 添加 tier 属性
    elite.tier = EnemyTier.ELITE
    
    engine = RewardsEngine(rng, content_registry=None)
    rewards = engine.generate_post_battle_rewards(state, elite)
    
    assert isinstance(rewards, RewardBundle), "返回类型错误"
    assert rewards.gold_delta >= 10, f"金币应 >= 10, 实际 {rewards.gold_delta}"
    print("✅ 精英奖励:")
    print(f"   金币: {rewards.gold_delta}")
    print(f"   卡牌: {rewards.card_choices}")
    print(f"   遗物: {rewards.relic_drop}")
    print(f"   治疗: {rewards.heal}")


def test_boss_rewards():
    """测试 BOSS 敌人奖励"""
    print("\n" + "=" * 50)
    print("🧪 测试: BOSS 敌人奖励")
    print("=" * 50)
    
    rng = DefaultRNG(seed=12345)
    state = GameState(seed=12345)
    
    # 创建 BOSS 敌人
    boss = EnemyState(
        entity_id="merge_chaos",
        name="Merge Chaos",
        enemy_type="merge",
        commit_hash="def456",
        commit_message="Massive merge conflict",
        current_hp=200,
        max_hp=200,
        attack=15,
        defense=20,
        exp_reward=200,
        gold_reward=100,
        is_alive=True,
        is_boss=True
    )
    
    engine = RewardsEngine(rng, content_registry=None)
    rewards = engine.generate_post_battle_rewards(state, boss)
    
    assert isinstance(rewards, RewardBundle), "返回类型错误"
    assert rewards.gold_delta >= 20, f"金币应 >= 20, 实际 {rewards.gold_delta}"
    assert rewards.relic_drop is not None, "BOSS 应掉落遗物"
    assert len(rewards.card_choices) == 3, f"BOSS 应 3 选 1, 实际 {len(rewards.card_choices)}"
    assert rewards.remove_card, "BOSS 应可移除卡牌"
    assert rewards.upgrade_card, "BOSS 应可升级卡牌"
    
    print("✅ BOSS 奖励:")
    print(f"   金币: {rewards.gold_delta}")
    print(f"   卡牌 (3选1): {rewards.card_choices}")
    print(f"   遗物: {rewards.relic_drop}")
    print(f"   可移除卡: {rewards.remove_card}")
    print(f"   可升级卡: {rewards.upgrade_card}")
    print(f"   治疗: {rewards.heal}")


def test_elite_multipliers():
    """测试精英/BOSS 倍率计算"""
    print("\n" + "=" * 50)
    print("🧪 测试: 奖励倍率")
    print("=" * 50)
    
    engine = EliteRewardsEngine(DefaultRNG(seed=1))
    
    # 普通敌人
    normal = EnemyState(
        entity_id="bug",
        name="Bug",
        enemy_type="fix",
        commit_hash="abc",
        commit_message="fix",
        current_hp=20,
        max_hp=20,
        attack=6,
        defense=0,
        exp_reward=10,
        gold_reward=10,
        is_alive=True,
        is_boss=False
    )
    normal.tier = EnemyTier.NORMAL
    
    # 精英敌人
    elite = EnemyState(
        entity_id="elite",
        name="Elite",
        enemy_type="fix",
        commit_hash="def",
        commit_message="fix",
        current_hp=60,
        max_hp=60,
        attack=12,
        defense=5,
        exp_reward=30,
        gold_reward=30,
        is_alive=True,
        is_boss=False
    )
    elite.tier = EnemyTier.ELITE
    
    # BOSS
    boss = EnemyState(
        entity_id="boss",
        name="BOSS",
        enemy_type="merge",
        commit_hash="ghi",
        commit_message="merge",
        current_hp=200,
        max_hp=200,
        attack=15,
        defense=20,
        exp_reward=200,
        gold_reward=100,
        is_alive=True,
        is_boss=True
    )
    
    normal_mult = engine.calculate_elite_boss_multipliers(normal)
    elite_mult = engine.calculate_elite_boss_multipliers(elite)
    boss_mult = engine.calculate_elite_boss_multipliers(boss)
    
    print("✅ 倍率计算:")
    print(f"   普通: gold={normal_mult['gold']}, exp={normal_mult['exp']}")
    print(f"   精英: gold={elite_mult['gold']}, exp={elite_mult['exp']}, relic={elite_mult['relic_chance']}")
    print(f"   BOSS: gold={boss_mult['gold']}, exp={boss_mult['exp']}, relic={boss_mult['relic_chance']}")
    
    assert normal_mult['gold'] == 1.0
    assert elite_mult['gold'] == 2.0
    assert boss_mult['gold'] == 3.0
    print("✅ 倍率正确")


def test_enemy_tier_parsing():
    """测试敌人 tier 解析"""
    print("\n" + "=" * 50)
    print("🧪 测试: 敌人 tier 解析")
    print("=" * 50)
    
    from git_dungeon.content.loader import load_content
    from pathlib import Path
    
    content_dir = Path("src/git_dungeon/content")
    content = load_content(str(content_dir))
    
    # 统计各 tier 敌人数量
    normal_count = 0
    elite_count = 0
    boss_count = 0
    
    for enemy in content.enemies.values():
        if enemy.tier == EnemyTier.NORMAL:
            normal_count += 1
        elif enemy.tier == EnemyTier.ELITE:
            elite_count += 1
        elif enemy.tier == EnemyTier.BOSS:
            boss_count += 1
    
    print("✅ 敌人 tier 分布:")
    print(f"   Normal: {normal_count}")
    print(f"   Elite: {elite_count}")
    print(f"   BOSS: {boss_count}")
    
    assert normal_count >= 20, f"Normal 敌人应 >= 20, 实际 {normal_count}"
    assert elite_count >= 6, f"Elite 敌人应 >= 6, 实际 {elite_count}"
    assert boss_count >= 3, f"BOSS 敌人应 >= 3, 实际 {boss_count}"
    print("✅ 分布符合要求")


def test_elite_relic_drops():
    """测试精英遗物掉落"""
    print("\n" + "=" * 50)
    print("🧪 测试: 精英遗物掉落")
    print("=" * 50)
    
    engine = EliteRewardsEngine(DefaultRNG(seed=54321))
    
    # 获取精英/BOSS 专属遗物
    elite_relics = engine.get_elite_boss_relics("elite")
    boss_relics = engine.get_elite_boss_relics("boss")
    
    print(f"   精英遗物: {elite_relics}")
    print(f"   BOSS 遗物: {boss_relics}")
    
    assert len(elite_relics) >= 2, f"精英遗物应 >= 2, 实际 {len(elite_relics)}"
    assert len(boss_relics) >= 2, f"BOSS 遗物应 >= 2, 实际 {len(boss_relics)}"
    print("✅ 遗物池有内容")
    
    # 测试随机获取
    relic = engine._get_random_relic("uncommon")
    print(f"   随机遗物 (uncommon+): {relic}")
    assert relic is not None


def test_is_elite_detection():
    """测试精英敌人检测"""
    print("\n" + "=" * 50)
    print("🧪 测试: 精英敌人检测")
    print("=" * 50)
    
    engine = EliteRewardsEngine()
    
    normal = EnemyState(
        entity_id="normal",
        name="Normal",
        enemy_type="feat",
        commit_hash="abc",
        commit_message="feat",
        current_hp=25,
        max_hp=25,
        attack=6,
        defense=0,
        exp_reward=10,
        gold_reward=10,
        is_alive=True,
        is_boss=False
    )
    normal.tier = EnemyTier.NORMAL
    
    elite = EnemyState(
        entity_id="elite",
        name="Elite",
        enemy_type="feat",
        commit_hash="def",
        commit_message="feat",
        current_hp=80,
        max_hp=80,
        attack=10,
        defense=5,
        exp_reward=50,
        gold_reward=30,
        is_alive=True,
        is_boss=False
    )
    elite.tier = EnemyTier.ELITE
    
    assert not engine._is_elite(normal), "普通敌人不应被检测为精英"
    assert engine._is_elite(elite), "精英敌人应被检测为精英"
    print("✅ 精英检测正确")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🧪 Git Dungeon M2.3 精英/BOSS 奖励测试")
    print("=" * 60 + "\n")
    
    test_elite_rewards()
    test_boss_rewards()
    test_elite_multipliers()
    test_enemy_tier_parsing()
    test_elite_relic_drops()
    test_is_elite_detection()
    
    print("\n" + "=" * 60)
    print("✅ M2.3 精英/BOSS 奖励测试全部通过!")
    print("=" * 60)


if __name__ == "__main__":
    main()
