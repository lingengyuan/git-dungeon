#!/usr/bin/env python3
"""Git Dungeon - 完整游戏流程测试 (修复版)"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from git_dungeon.core.game_engine import GameState
from git_dungeon.core.character import get_character


def test_full_gameplay():
    """完整游戏流程测试 (正确战斗流程)."""
    print("=" * 60)
    print("🧪 测试 11: 完整游戏流程")
    print("=" * 60)

    game = GameState()
    game.load_repository("/tmp/test_git_dungeon")
    print(f"✓ 加载 {len(game.commits)} commits")

    defeated = 0
    rounds = 0

    while len(game.defeated_commits) < len(game.commits):
        # Start combat if not in one
        if not game.current_combat:
            game.start_combat()
            if not game.current_combat:
                break

        enemy = game.current_combat.enemy
        enemy_char = get_character(enemy)
        player_char = get_character(game.player)

        # Check if enemy is already dead
        if enemy_char.is_dead:
            defeated += 1
            game.current_combat = None
            game._advance_to_next_commit()
            print(f"💀 击败 {enemy_char.name}! ({defeated}/{len(game.commits)})")
            continue

        rounds += 1
        if rounds > 100:
            print("⚠ 超过100回合，停止")
            break

        # Player attacks
        damage = player_char.stats.attack.value
        game.player_action("attack", damage=damage)

        # Check if enemy died from player attack
        enemy_char = get_character(enemy)
        if enemy_char.is_dead:
            defeated += 1
            game.current_combat = None
            game._advance_to_next_commit()
            print(f"💀 击败 {enemy_char.name}! ({defeated}/{len(game.commits)})")
            continue

        # Enemy attacks (if still in combat)
        if game.current_combat:
            game.enemy_turn()

    print(f"\\n✅ 完成: {defeated}/{len(game.commits)} commits defeated in {rounds} rounds")
    assert defeated == len(game.commits)

    player = get_character(game.player)
    print(f"✓ 玩家状态: HP={player.current_hp}, Level={player.level}")
    assert player.current_hp > 0
    assert player.level >= 1

    print("✅ 测试 11 通过\\n")


if __name__ == "__main__":
    test_full_gameplay()
