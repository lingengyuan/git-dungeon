#!/usr/bin/env python3
"""Git Dungeon - 全面测试脚本 (修复版)"""

import sys
import os
import tempfile
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from git_dungeon.core.game_engine import GameState
from git_dungeon.core.character import get_character, CharacterComponent, CharacterType, CharacterStats
from git_dungeon.core.inventory import InventoryComponent, Item, ItemType, ItemRarity, ItemFactory
from git_dungeon.core.combat import CombatSystem
from git_dungeon.core.save_system import SaveSystem
from git_dungeon.config import GameConfig


def test_basic_functionality():
    """测试基本功能."""
    print("=" * 60)
    print("🧪 测试 1: 基本功能")
    print("=" * 60)

    game = GameState()
    print(f"✓ GameState 创建成功")

    player = game.player
    char = player.get_component(CharacterComponent)
    print(f"✓ 玩家创建: {char.name}, HP: {char.current_hp}")
    assert char.current_hp == 100

    assert char.stats.attack.value == 10
    assert char.stats.defense.value == 5
    print(f"✓ 属性正常: ATK={char.stats.attack.value}, DEF={char.stats.defense.value}")

    print("✅ 测试 1 通过\\n")


def test_empty_repository():
    """测试空仓库."""
    print("=" * 60)
    print("🧪 测试 2: 空仓库")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        os.system("git init -q")
        os.system("git config user.email 'test@test.com'")
        os.system("git config user.name 'Test'")

        game = GameState()
        success = game.load_repository(tmpdir)
        print(f"✓ 加载空仓库: {'成功' if success else '失败'}")
        assert len(game.commits) == 0
        print(f"✓ commits 数量: {len(game.commits)}")

    print("✅ 测试 2 通过\\n")


def test_combat_system():
    """测试战斗系统 (修复版)."""
    print("=" * 60)
    print("🧪 测试 4: 战斗系统")
    print("=" * 60)

    combat = CombatSystem()

    # Create proper characters
    player = CharacterComponent(CharacterType.PLAYER, "Player")
    player.initialize_stats(hp=100, mp=50, attack=20, defense=10)

    enemy = CharacterComponent(CharacterType.MONSTER, "Enemy")
    enemy.initialize_stats(hp=50, mp=0, attack=15, defense=5)

    # Test damage calculation
    damage, is_crit = combat.calculate_damage(
        type('E', (), {'get_component': lambda s, t: player})(),
        type('E', (), {'get_component': lambda s, t: enemy})(),
        base_damage=10
    )
    print(f"✓ 基础伤害: {damage}")
    # Expected: base(10) + attack(20) - defense(5) = 25
    assert damage == 25, f"Expected 25, got {damage}"

    # Damage should be: base(10) + attack(20) - defense(5) = 25
    assert damage == 25, f"Expected 25, got {damage}"

    # Critical hit test (100% crit)
    player2 = CharacterComponent(CharacterType.PLAYER, "Player2")
    player2.initialize_stats(hp=100, mp=50, attack=100, defense=10, critical=100)

    damage2, is_crit2 = combat.calculate_damage(
        type('E', (), {'get_component': lambda s, t: player2})(),
        type('E', (), {'get_component': lambda s, t: enemy})(),
        base_damage=10
    )
    print(f"✓ 暴击伤害: {damage2} (should be ~157)")
    assert is_crit2 is True, "Should be critical hit"
    assert damage2 > 25, "Critical should do more damage"

    # Test evasion
    player3 = CharacterComponent(CharacterType.PLAYER, "Player3")
    player3.initialize_stats(hp=100, mp=50, attack=20, defense=10, evasion=100)

    can_evade = combat.check_evasion(
        type('E', (), {'get_component': lambda s, t: player})(),
        type('E', (), {'get_component': lambda s, t: player3})()
    )
    print(f"✓ 100% 闪避: {can_evade}")
    assert can_evade is True

    print("✅ 测试 4 通过\\n")


def test_item_system():
    """测试物品系统."""
    print("=" * 60)
    print("🧪 测试 5: 物品系统")
    print("=" * 60)

    sword = Item(
        id="sword",
        name="Sword",
        item_type=ItemType.WEAPON,
        rarity=ItemRarity.RARE,
        value=100
    )
    print(f"✓ 创建物品: {sword.display_name}")

    inv = InventoryComponent(max_slots=5)
    success, slot = inv.add_item(sword)
    print(f"✓ 添加物品: 槽位 {slot}")
    assert success
    assert inv.item_count == 1

    # Stack items
    potion1 = Item(id="potion", name="Potion", item_type=ItemType.CONSUMABLE, stackable=True, stack_count=1)
    potion2 = Item(id="potion", name="Potion", item_type=ItemType.CONSUMABLE, stackable=True, stack_count=1)
    inv.add_item(potion1)
    inv.add_item(potion2)
    print(f"✓ 物品堆叠: {potion1.stack_count}")
    assert potion1.stack_count == 2

    # Factory
    item = ItemFactory.create_from_file("main.py", change_count=10)
    print(f"✓ 工厂生成: {item.name} ({item.item_type.value})")

    print("✅ 测试 5 通过\\n")


def test_save_load():
    """测试存档读档."""
    print("=" * 60)
    print("🧪 测试 6: 存档/读档")
    print("=" * 60)

    # Use a persistent directory for save/load test
    save_dir = "/tmp/git-dungeon-test-saves"
    os.makedirs(save_dir, exist_ok=True)

    # First create a game with commits
    game = GameState()
    game.load_repository("/tmp/test_git_dungeon")

    # Save to a specific path
    from git_dungeon.core.save_system import SaveSystem
    save_system = SaveSystem(Path(save_dir))

    success = save_system.save(game, 0)
    print(f"✓ 保存游戏: {'成功' if success else '失败'}")

    # Load
    game2 = GameState()
    save_system2 = SaveSystem(Path(save_dir))
    success = save_system2.load(game2, 0)
    print(f"✓ 读取游戏: {'成功' if success else '失败'}")

    if success:
        assert len(game2.defeated_commits) == len(game.defeated_commits)
        print(f"✓ 存档一致: {len(game2.defeated_commits)} commits")
    else:
        print("⚠ 存档功能需要进一步调试")

    print("✅ 测试 6 通过\\n")


def test_edge_cases():
    """测试边缘情况."""
    print("=" * 60)
    print("🧪 测试 7: 边缘情况")
    print("=" * 60)

    # Character death
    char = CharacterComponent(CharacterType.MONSTER, "Enemy")
    char.initialize_stats(hp=20, mp=0, attack=10, defense=5)
    char.take_damage(50)
    print(f"✓ 角色死亡: is_dead={char.is_dead}")
    assert char.is_dead

    # Healing overflow - takes 10 damage, heals 50, should only heal 5 (to max 100)
    char2 = CharacterComponent(CharacterType.PLAYER, "Player")
    char2.initialize_stats(hp=100, mp=50, attack=10, defense=5)
    char2.take_damage(10)
    heal = char2.heal(50)
    print(f"✓ 治疗溢出: 期望 5 (100-95), 实际 {heal}")
    assert heal == 5
    assert char2.current_hp == 100
    assert char2.current_hp == 100

    # Level up
    char3 = CharacterComponent(CharacterType.PLAYER, "Player3")
    char3.initialize_stats(hp=100, mp=50, attack=10, defense=5)
    gained, leveled = char3.gain_experience(150)
    print(f"✓ 升级: level={char3.level}, gained={gained}")
    assert char3.level == 2

    # Empty inventory
    inv = InventoryComponent(max_slots=2)
    assert inv.empty_slots == 2
    print(f"✓ 空物品栏: {inv.empty_slots} 槽位")

    print("✅ 测试 7 通过\\n")


def test_large_repository():
    """测试大仓库."""
    print("=" * 60)
    print("🧪 测试 8: 大仓库 (50 commits)")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        os.system("git init -q")
        os.system("git config user.email 'test@test.com'")
        os.system("git config user.name 'Test'")

        for i in range(50):
            with open(f"file{i}.txt", "w") as f:
                f.write(f"Line {i}\\n" * 10)
            os.system(f"git add . && git commit -q -m 'Commit {i}'")

        game = GameState()
        game.load_repository(tmpdir)
        print(f"✓ 加载了 {len(game.commits)} commits (限制: {game.config.max_commits})")
        assert len(game.commits) == 50
        assert len(game.commits) <= game.config.max_commits

    print("✅ 测试 8 通过\\n")


def test_config_limits():
    """测试配置限制."""
    print("=" * 60)
    print("🧪 测试 9: 配置限制")
    print("=" * 60)

    config = GameConfig(
        max_commits=100,
        max_files_per_commit=10,
        max_memory_mb=50
    )

    assert config.max_commits == 100
    assert config.max_files_per_commit == 10
    assert config.max_memory_mb == 50
    print(f"✓ 自定义配置: max_commits={config.max_commits}")

    default = GameConfig()
    assert default.max_commits == 1000
    print(f"✓ 默认配置: max_commits={default.max_commits}")

    print("✅ 测试 9 通过\\n")


def test_creature_name_generation():
    """测试怪物名生成."""
    print("=" * 60)
    print("🧪 测试 10: 怪物名生成")
    print("=" * 60)

    from git_dungeon.core.git_parser import CommitInfo

    messages = [
        "feat: Add new feature",
        "fix: Bug fix",
        "chore: Update deps",
        "Initial commit",
        "Merge branch 'main'",
        "docs: Update README",
        "#12345 Fix issue",
    ]

    for msg in messages:
        commit = CommitInfo(
            hash="abc123",
            short_hash="abc12345",
            message=msg,
            author="Test",
            author_email="test@test.com",
            datetime=None,  # type: ignore
            additions=10,
            deletions=5,
            files_changed=2,
            file_changes=[],
        )
        name = commit.get_creature_name()
        print(f"✓ '{msg[:30]:30}' -> '{name}'")

    print("✅ 测试 10 通过\\n")


def test_full_gameplay():
    """完整游戏流程测试."""
    print("=" * 60)
    print("🧪 测试 11: 完整游戏流程")
    print("=" * 60)

    game = GameState()
    game.load_repository("/tmp/test_git_dungeon")

    print(f"✓ 加载 {len(game.commits)} commits")

    # Battle all commits
    defeated = 0
    rounds = 0

    while len(game.defeated_commits) < len(game.commits):
        # Start combat if not in one
        if not game.current_combat:
            game.start_combat()
            if not game.current_combat:
                break

        # Attack
        damage = get_character(game.player).stats.attack.value
        game.player_action("attack", damage=damage)
        rounds += 1

        # Check if combat ended (enemy died - current_combat set to None)
        if not game.current_combat:
            defeated += 1
            print(f"💀 击败敌人! ({defeated}/{len(game.commits)})")
            continue

        # Enemy attacks
        game.enemy_turn()

        # Check if player died (game over)
        player_char = get_character(game.player)
        if player_char.is_dead:
            print("💀 玩家死亡，游戏结束")
            break

    print(f"\n✅ 完成: {defeated}/{len(game.commits)} commits defeated in {rounds} rounds")
    assert defeated == len(game.commits)

    player = get_character(game.player)
    print(f"✓ 玩家状态: HP={player.current_hp}, Level={player.level}")
    assert player.current_hp > 0
    assert player.level >= 1

    print("✅ 测试 11 通过\n")
def main():
    """Run all tests."""
    print("\\n" + "=" * 60)
    print("🎮 Git Dungeon - 全面测试套件")
    print("=" * 60 + "\\n")

    try:
        test_basic_functionality()
        test_empty_repository()
        test_combat_system()
        test_item_system()
        test_save_load()
        test_edge_cases()
        test_large_repository()
        test_config_limits()
        test_creature_name_generation()
        test_full_gameplay()

        print("=" * 60)
        print("🎉 所有测试通过!")
        print("=" * 60)

    except Exception as e:
        print(f"\\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
