#!/usr/bin/env python3
"""
Git Dungeon Performance Profiler
分析游戏各组件的性能，找出瓶颈
"""

import sys
import cProfile
import pstats
import io
import tempfile
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.game_engine import GameState
from src.core.character import CharacterComponent, CharacterType
from src.core.combat import CombatSystem
from src.core.lua import LuaEngine, MonsterTemplate


def profile_repository_loading():
    """分析仓库加载性能"""
    print("\n" + "=" * 60)
    print("PROFILING: Repository Loading")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = os.path.join(tmpdir, "test_repo")
        os.makedirs(repo_path)
        os.system(f"cd {repo_path} && git init > /dev/null 2>&1")
        os.system(f"cd {repo_path} && git config user.email 'test@test.com'")
        os.system(f"cd {repo_path} && git config user.name 'Test'")
        
        # 创建大量 commits
        for i in range(100):
            os.system(f"echo 'file{i}' > f{i}.txt && git add . && git commit -m 'feat: {i}' -q 2>/dev/null")
        
        pr = cProfile.Profile()
        pr.enable()
        
        # 测试加载
        for _ in range(10):
            state = GameState()
            state.load_repository(repo_path)
        
        pr.disable()
        
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(20)
        print(s.getvalue())
        
        return pr


def profile_character_creation():
    """分析角色创建性能"""
    print("\n" + "=" * 60)
    print("PROFILING: Character Creation")
    print("=" * 60)
    
    pr = cProfile.Profile()
    pr.enable()
    
    # 批量创建角色
    for _ in range(1000):
        char = CharacterComponent(CharacterType.PLAYER, "Test")
        char.initialize_stats(hp=100, mp=50, attack=20, defense=10)
        char.gain_experience(100)
    
    pr.disable()
    
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(15)
    print(s.getvalue())


def profile_combat():
    """分析战斗性能"""
    print("\n" + "=" * 60)
    print("PROFILING: Combat System")
    print("=" * 60)
    
    pr = cProfile.Profile()
    pr.enable()
    
    combat = CombatSystem()
    
    for _ in range(100):
        player = CharacterComponent(CharacterType.PLAYER, "Dev")
        player.initialize_stats(hp=100, mp=50, attack=20, defense=10)
        
        enemy = CharacterComponent(CharacterType.MONSTER, "Bug")
        enemy.initialize_stats(hp=50, mp=0, attack=10, defense=5)
        
        # 快速战斗
        while player.current_hp > 0 and enemy.current_hp > 0:
            dmg = 20
            enemy.take_damage(dmg)
            if enemy.current_hp <= 0:
                break
            player.take_damage(10)
    
    pr.disable()
    
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(15)
    print(s.getvalue())


def profile_lua_content():
    """分析 Lua 内容系统性能"""
    print("\n" + "=" * 60)
    print("PROFILING: Lua Content System")
    print("=" * 60)
    
    pr = cProfile.Profile()
    pr.enable()
    
    engine = LuaEngine()
    
    # 批量添加怪物
    for i in range(100):
        engine.monsters[f"Monster{i}"] = MonsterTemplate(
            name=f"Monster{i}",
            base_hp=100 + i,
            base_attack=20 + i,
        )
    
    # 批量获取
    for i in range(100):
        _ = engine.get_monster(f"Monster{i}")
    
    pr.disable()
    
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(15)
    print(s.getvalue())


def profile_full_game_loop():
    """分析完整游戏循环"""
    print("\n" + "=" * 60)
    print("PROFILING: Full Game Loop")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = os.path.join(tmpdir, "test_repo")
        os.makedirs(repo_path)
        os.system(f"cd {repo_path} && git init > /dev/null 2>&1")
        os.system(f"cd {repo_path} && git config user.email 'test@test.com'")
        os.system(f"cd {repo_path} && git config user.name 'Test'")
        
        # 创建 commits
        for i in range(20):
            os.system(f"echo 'f{i}' > f{i}.txt && git add . && git commit -m 'feat: {i}' -q 2>/dev/null")
        
        pr = cProfile.Profile()
        pr.enable()
        
        # 完整游戏循环
        for _ in range(5):
            state = GameState()
            state.load_repository(repo_path)
            
            while state.current_commit:
                if state.start_combat():
                    player = state.player.get_component(CharacterComponent)
                    enemy = state.current_combat.enemy.get_component(CharacterType.MONSTER)
                    
                    while state.current_combat and not state.current_combat.ended:
                        if state.current_combat.is_player_turn:
                            enemy.take_damage(25)
                        else:
                            player.take_damage(10)
                        state.current_combat.turn_phase = "player" if state.current_combat.turn_phase == "enemy" else "enemy"
                    
                    state._advance_to_next_commit()
        
        pr.disable()
        
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(25)
        print(s.getvalue())


def main():
    """运行所有性能分析"""
    print("\n" + "=" * 60)
    print("  Git Dungeon Performance Profiler")
    print("=" * 60)
    
    try:
        # 分析各组件
        profile_repository_loading()
        profile_character_creation()
        profile_combat()
        profile_lua_content()
        profile_full_game_loop()
        
    except KeyboardInterrupt:
        print("\n分析中断")


if __name__ == "__main__":
    main()
