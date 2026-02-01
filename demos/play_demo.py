#!/usr/bin/env python3
"""Git Dungeon - Complete play-through demo."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.game_engine import GameState
from src.core.character import get_character


def main():
    """Run the complete game demo."""
    print("=" * 60)
    print("🎮 Git Dungeon - 完整游戏演示")
    print("=" * 60)

    # Load repository
    repo_path = "/tmp/test_git_dungeon"
    print(f"\\n📂 加载仓库: {repo_path}")

    game = GameState()
    if not game.load_repository(repo_path):
        print("❌ 加载失败!")
        return

    print(f"✅ 加载了 {len(game.commits)} 个 commits\\n")

    # Show commits
    print("📦 提交历史 (怪物列表):")
    print("-" * 60)
    for i, c in enumerate(game.commits):
        hp = c.total_changes + 20
        atk = c.additions + 5
        print(f"  [{i:2d}] {c.get_creature_name():20} HP:{hp:3} ATK:{atk:2} | {c.message[:35]}")
    print()

    # Start
    player_char = get_character(game.player)
    total_rounds = 0

    while len(game.defeated_commits) < len(game.commits):
        # Start combat if not in one
        if not game.current_combat:
            game.start_combat()

        if not game.current_combat or not game.current_combat.enemy:
            break

        enemy = game.current_combat.enemy
        enemy_char = get_character(enemy)

        if enemy_char.is_dead:
            print(f"\\n💀 击败了 {enemy_char.name}!")
            game.current_combat = None
            game._advance_to_next_commit()
            continue

        total_rounds += 1

        # Quick combat (auto-battle)
        damage = player_char.stats.attack.value
        game.player_action("attack", damage=damage)

        if not game.current_combat:
            continue

        # Enemy attacks
        game.enemy_turn()

    # End
    print("\\n" + "=" * 60)
    print(f"🎉 游戏完成! 共 {total_rounds} 回合")
    print(f"   击败敌人: {len(game.defeated_commits)}/{len(game.commits)}")
    print(f"   玩家等级: {player_char.level}")
    print(f"   玩家HP: {player_char.current_hp}/{player_char.stats.hp.value}")
    print(f"   经验值: {player_char.experience}")
    print("=" * 60)


if __name__ == "__main__":
    main()
