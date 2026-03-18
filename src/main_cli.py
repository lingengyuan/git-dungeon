#!/usr/bin/env python3
"""
Git Dungeon - CLI Entry Point
简单的命令行入口点，不需要 Textual
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.config import GameConfig
from src.core.game_engine import GameState
from src.core.character import CharacterComponent


def print_banner():
    """Print game banner."""
    banner = """
    ╔════════════════════════════════════╗
    ║         G I T   D U N G E O N       ║
    ║     Battle through your commits!   ║
    ╚════════════════════════════════════╝
    """
    print(banner)


def print_status(state: GameState):
    """Print current game status."""
    player = state.player.get_component(CharacterComponent)
    
    print(f"\n{'─'*40}")
    print(f"📍 Location: {state.current_commit.get_creature_name() if state.current_commit else 'Game Over'}")
    print(f"💀 Enemies defeated: {len(state.defeated_commits)}/{len(state.commits)}")
    print(f"{'─'*40}")
    print(f"👤 {player.name}")
    print(f"   Level: {player.level}")
    print(f"   HP: {player.current_hp}/{player.stats.hp.value}")
    print(f"   EXP: {player.experience}/{player.experience_to_next}")
    print(f"{'─'*40}")


def battle(state: GameState) -> bool:
    """Run a battle with manual input."""
    # 检查是否已经在战斗中
    if state.current_combat and not state.current_combat.ended:
        print("⚠️  战斗进行中!")
        return True
    
    # 开始新战斗
    if not state.start_combat():
        print("⚠️  没有敌人可以战斗!")
        return False
    
    player = state.player.get_component(CharacterComponent)
    enemy = state.current_combat.enemy.get_component(CharacterComponent)
    
    print(f"\n{'─'*40}")
    print(f"⚔️  BATTLE: {player.name} vs {enemy.name}")
    print(f"{'─'*40}")
    print(f"👤 {player.name}: HP {player.current_hp}/{player.stats.hp.value} | MP {player.current_mp}/{player.stats.mp.value}")
    print(f"👾 {enemy.name}: HP {enemy.current_hp}/{enemy.stats.hp.value}")
    print(f"{'─'*40}")
    
    while state.current_combat and not state.current_combat.ended:
        if state.current_combat.is_player_turn:
            # 玩家回合 - 等待输入
            print(f"\n🎯 你的回合! (HP:{player.current_hp} MP:{player.current_mp})")
            print("   [1] ⚔️ 攻击  [2] 🛡️ 防御  [3] ✨ 技能  [4] 🏃 逃跑")
            
            try:
                choice = input("   > ").strip()
            except EOFError:
                choice = '1'  # 默认攻击
            
            if choice == '1':
                # 攻击
                dmg = player.stats.attack.value + 5
                actual = enemy.take_damage(dmg)
                print(f"   ⚔️ 你攻击 {enemy.name}，造成 {actual} 伤害!")
            elif choice == '2':
                # 防御
                print("   🛡️ 你进入防御姿态，减少 50% 伤害!")
                state.current_combat.player_defending = True  # type: ignore[attr-defined]
            elif choice == '3':
                # 技能 (消耗 MP)
                if player.current_mp >= 10:
                    player.current_mp -= 10
                    dmg = (player.stats.attack.value + 5) * 2
                    actual = enemy.take_damage(dmg)
                    print(f"   ✨ 你使出技能，造成 {actual} 暴击伤害! (MP -10)")
                else:
                    print(f"   ⚠️ MP 不足! 需要 10 MP，当前 {player.current_mp}")
                    continue  # 重新选择
            elif choice == '4':
                # 逃跑
                import random
                if random.random() > 0.3:
                    print("   🏃 逃跑成功!")
                    state.current_combat.ended = True
                    state.current_combat = None
                    return False
                else:
                    print("   ❌ 逃跑失败!")
            else:
                print("   ⚠️ 无效选择，默认攻击")
                dmg = player.stats.attack.value + 5
                actual = enemy.take_damage(dmg)
                print(f"   ⚔️ 你攻击 {enemy.name}，造成 {actual} 伤害!")
            
            # 检查敌人是否死亡
            if enemy.current_hp <= 0:
                print(f"\n   🎉 {enemy.name} 被击败了!")
                state.current_combat.ended = True
                break
            
            # 切换到敌人回合
            state.current_combat.turn_phase = "enemy"
            
        else:
            # 敌人回合
            import random
            dmg = enemy.stats.attack.value
            
            # 如果玩家防御，减伤 50%
            if getattr(state.current_combat, 'player_defending', False):
                dmg = dmg // 2
                print(f"   🛡️ 防御生效，{enemy.name} 的伤害减少到 {dmg}")
                state.current_combat.player_defending = False  # type: ignore[attr-defined]
            
            actual = player.take_damage(dmg)
            print(f"   💥 {enemy.name} 攻击你，造成 {actual} 伤害!")
            
            # 检查玩家是否死亡
            if player.current_hp <= 0:
                print(f"\n   💀 你被 {enemy.name} 击败了!")
                state.current_combat.ended = True
                return False
            
            # 切换回玩家回合
            state.current_combat.turn_phase = "player"
    
    # 清理战斗状态
    if state.current_combat:
        state.current_combat.ended = True
        state.current_combat = None
    
    return enemy.current_hp <= 0


def parse_github_url(url: str) -> str:
    """解析 GitHub URL，返回 repo 路径和临时目录"""
    import re
    import tempfile
    
    # GitHub URL 格式检测
    patterns = [
        r'https://github\.com/([^/]+/[^/]+)/?$',
        r'git@github\.com:([^/]+/[^/]+)\.git$',
        r'^([^/]+/[^/]+)$',  # 简短格式: user/repo
    ]
    
    for pattern in patterns:
        match = re.match(pattern, url)
        if match:
            repo_path = match.group(1)
            # 移除 .git 后缀
            if repo_path.endswith(".git"):
                repo_path = repo_path[:-4]
            
            # 创建临时目录
            temp_dir = tempfile.mkdtemp(prefix='git-dungeon-')
            clone_path = os.path.join(temp_dir, repo_path.split('/')[-1])
            
            return repo_path, temp_dir, clone_path
    
    return None, None, None


def clone_github_repo(repo_path: str, clone_path: str) -> bool:
    """Clone GitHub repository"""
    import subprocess
    
    url = f"https://github.com/{repo_path}.git"
    print(f"🔽 Cloning {url}...")
    
    try:
        result = subprocess.run(
            ['git', 'clone', '--depth', '1', url, clone_path],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print("✅ Cloned successfully!")
            return True
        else:
            print(f"❌ Clone failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Clone timeout (network slow?)")
        return False
    except FileNotFoundError:
        print("❌ Git not installed")
        return False


def main():
    """Main CLI entry point."""
    print_banner()
    
    # 检查参数
    repo_input = sys.argv[1] if len(sys.argv) > 1 else None
    
    if not repo_input or repo_input in ['--help', '-h']:
        print("""
🎮 Git Dungeon - Battle through your commits!

Usage:
    python -m src.main_cli <repository>

Examples:
    # Local repository
    python -m src.main_cli /path/to/your/project
    
    # GitHub repository
    python -m src.main_cli https://github.com/username/repo
    python -m src.main_cli username/repo
    python -m src.main_cli git@github.com:username/repo.git

Or use the TUI version:
    textual run src.main
""")
        return
    
    # 检测是否为 GitHub URL
    import re
    is_github = bool(re.match(r'^(https://github\.com|git@github\.com|:|[^/]+/[^/]+$)', repo_input))
    
    temp_dir = None
    
    if is_github:
        repo_path, temp_dir, clone_path = parse_github_url(repo_input)
        if not repo_path:
            print(f"❌ Invalid GitHub URL: {repo_input}")
            return
        
        if not clone_github_repo(repo_path, clone_path):
            return
        
        repo_path = clone_path
    else:
        # 本地路径
        if not os.path.exists(repo_input):
            print(f"❌ Repository not found: {repo_input}")
            return
    
    # 加载仓库
    print(f"\n📦 Loading repository: {repo_path}")
    config = GameConfig()
    state = GameState(config=config)
    
    if not state.load_repository(repo_path):
        print("❌ Failed to load repository")
        if temp_dir:
            import shutil
            shutil.rmtree(temp_dir)
        return
    
    print(f"✅ Loaded {len(state.commits)} commits!")
    
    # 清理临时目录（可选：保留用于后续游戏）
    if temp_dir:
        print(f"\n📁 Repository cached at: {temp_dir}")
    
    # 游戏循环
    while state.current_commit and not state.is_game_over:
        print_status(state)
        
        # 战斗
        if battle(state):
            print("✅ Victory! Gained experience.")
            state._advance_to_next_commit()
        else:
            print("💀 Defeat!")
            break
    
    # 游戏结束
    print("\n" + "="*40)
    if state.is_game_over:
        print("🎉  VICTORY! All commits defeated!")
    else:
        print("💀  GAME OVER")
    
    player = state.player.get_component(CharacterComponent)
    print(f"   Final Level: {player.level}")
    print(f"   Enemies Defeated: {len(state.defeated_commits)}")
    print("="*40)


if __name__ == "__main__":
    main()
