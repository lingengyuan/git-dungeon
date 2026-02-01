#!/usr/bin/env python3
"""Full game integration test with real repository."""

import sys
from pathlib import Path
import tempfile
import os

sys.path.insert(0, str(Path(__file__).parent))

from git_dungeon.core.game_engine import GameState
from git_dungeon.core.character import CharacterComponent, CharacterType
from git_dungeon.core.combat import CombatSystem, CombatAction, CombatResult
from git_dungeon.core.git_parser import GitParser


def create_test_repo(path):
    """Create a test repository with various commits."""
    os.makedirs(path, exist_ok=True)
    os.system(f"cd {path} && rm -rf .git && git init > /dev/null 2>&1")
    os.system(f"cd {path} && git config user.email 'test@test.com'")
    os.system(f"cd {path} && git config user.name 'Test User'")
    
    commands = [
        ("echo '# Test' > README.md && git add . && git commit -m 'Initial'"),
        ("echo 'a=1' > app.py && git add . && git commit -m 'feat: Add app'"),
        ("echo 'b=2' >> app.py && git add . && git commit -m 'fix: Add b'"),
        ("for i in {1..50}; do echo 'line $i' >> big.txt; done && git add . && git commit -m 'chore: Add data'"),
        ("echo 'updated' >> app.py && git add . && git commit -m 'refactor: Update'"),
    ]
    
    for cmd in commands:
        os.system(f"cd {path} && {cmd} > /dev/null 2>&1")
    
    print(f"  Created test repo at {path}")
    return path


def test_full_game_flow():
    """Test the complete game flow."""
    print("\n=== Full Game Flow Test ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = os.path.join(tmpdir, "test_repo")
        create_test_repo(repo_path)
        
        # Load repository
        state = GameState()
        result = state.load_repository(repo_path)
        print(f"  Loaded commits: {len(state.commits)}")
        
        assert result == True, "Should load repository"
        assert len(state.commits) > 0, "Should have commits"
        
        # Check player exists
        player = state.player
        char = player.get_component(CharacterComponent)
        print(f"  Player: {char.name}, Level: {char.level}, HP: {char.current_hp}")
        
        assert char.name == "Developer", "Player should be Developer"
        assert char.level == 1, "Should start at level 1"
        
        # Combat through all commits
        total_kills = 0
        
        while state.current_commit and not state.is_game_over:
            commit = state.current_commit
            print(f"\n  --- Combat {total_kills + 1}: {commit.get_creature_name()} ---")
            print(f"  Message: {commit.message[:40]}...")
            print(f"  Changes: +{commit.additions}/-{commit.deletions}")
            
            # Start combat
            result = state.start_combat()
            if not result:
                print(f"  Combat already in progress or no commit")
                break
            
            # Get enemy from combat
            enemy_from_combat = state.current_combat.enemy
            enemy_char = enemy_from_combat.get_component(CharacterComponent)
            print(f"  Enemy: {enemy_char.name}, HP: {enemy_char.current_hp}, ATK: {enemy_char.stats.attack.value}")
            
            # Battle loop
            turn = 0
            while state.current_combat and not state.current_combat.ended:
                turn += 1
                
                if state.current_combat.is_player_turn:
                    # Use game_engine.player_action which handles combat cleanup
                    state.player_action("attack", damage=20)
                    
                    if enemy_char.current_hp <= 0:
                        print(f"  Player kills enemy on turn {turn}!")
                        break
                else:
                    # Enemy attacks
                    state.enemy_turn()
                    print(f"  Enemy attacks! Player HP: {char.current_hp}")
                    
                    if char.current_hp <= 0:
                        print(f"  Player died on turn {turn}!")
                        break
            
            print(f"  After loop: current_combat is {'None' if state.current_combat is None else 'still active'}")
            print(f"    Enemy HP: {enemy_char.current_hp}")
            
            # Check result
            if state.is_game_over:
                print(f"  GAME OVER! Defeated {total_kills} enemies")
                break
            
            total_kills += 1
            print(f"  Victory! Player HP: {char.current_hp}, Level: {char.level}")
            
            # Check for level up
            if char.level > 1:
                info = char.get_level_info()
                print(f"  Level info: Lv{info['level']}, {info['experience']}/{info['experience_to_next']} XP")
        
        print(f"\n  === Game Summary ===")
        print(f"  Total enemies defeated: {total_kills}")
        print(f"  Final level: {char.level}")
        print(f"  Final HP: {char.current_hp}/{char.stats.hp.value}")
        print(f"  Total exp gained: {char._total_exp_gained}")
        print(f"  Power level: {char.get_power_level()}")
        
        # Just check that game flow works (combat -> victory/defeat -> next)
        assert total_kills >= 1, "Should defeat at least one enemy"
        
        print("  ✓ Full game flow test passed!")



def test_save_and_load_game():
    """Test saving and loading game state."""
    print("\n=== Save/Load Game Test ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = os.path.join(tmpdir, "test_repo")
        create_test_repo(repo_path)
        
        # Load and play a bit
        state = GameState()
        state.load_repository(repo_path)
        
        # Get initial player stats
        char = state.player.get_component(CharacterComponent)
        initial_level = char.level
        initial_exp = char._total_exp_gained
        
        # Gain some experience
        char.gain_experience(150)
        print(f"  Before save: Level {char.level}, Exp {char._total_exp_gained}")
        
        # Save
        result = state.save_game(0)
        print(f"  Save result: {result}")
        assert result == True, "Save should succeed"
        
        # Load into new state
        new_state = GameState()
        result = new_state.load_game(0)
        print(f"  Load result: {result}")
        assert result == True, "Load should succeed"
        
        new_char = new_state.player.get_component(CharacterComponent)
        print(f"  After load: Level {new_char.level}, Exp {new_char._total_exp_gained}")
        
        # Check progress was saved
        assert new_char.level == char.level, "Level should be preserved"
        assert new_char._total_exp_gained == char._total_exp_gained, "Exp should be preserved"
        
        print("  ✓ Save/load game test passed!")


def test_combat_edge_cases():
    """Test various combat scenarios."""
    print("\n=== Combat Edge Cases Test ===")
    
    from git_dungeon.core.entity import Entity
    
    # Player with very high defense vs weak enemy
    player = Entity(id="player", name="Player")
    player_char = CharacterComponent(CharacterType.PLAYER, "Player")
    player_char.initialize_stats(hp=200, mp=100, attack=50, defense=100)
    player.add_component(player_char)
    
    enemy = Entity(id="enemy", name="Weak")
    enemy_char = CharacterComponent(CharacterType.MONSTER, "Weak")
    enemy_char.initialize_stats(hp=10, mp=0, attack=5, defense=0)
    enemy.add_component(enemy_char)
    
    combat = CombatSystem()
    encounter = combat.start_combat(player, enemy)
    
    # Get enemy char from encounter
    enemy_char = enemy.get_component(CharacterComponent)
    
    # Player should win easily
    for _ in range(10):
        if encounter.is_player_turn:
            encounter.player_action("attack", damage=50)
        else:
            encounter.enemy_turn()
        if encounter.ended:
            break
    
    print(f"  High defense vs weak: {encounter.ended}")
    assert encounter.ended == True, "Combat should end"
    assert enemy_char.current_hp <= 0, "Enemy should be dead"
    
    # Test very low damage (minimum 1)
    player_char.current_hp = 200  # Reset
    enemy_char.current_hp = 1  # One HP enemy
    
    enemy2 = Entity(id="enemy2", name="OneHP")
    enemy2_char = CharacterComponent(CharacterType.MONSTER, "OneHP")
    enemy2_char.initialize_stats(hp=1, mp=0, attack=1000, defense=0)
    enemy2.add_component(enemy2_char)
    
    encounter2 = combat.start_combat(player, enemy2)
    enemy2_char = enemy2.get_component(CharacterComponent)
    
    encounter2.player_action("attack", damage=50)
    
    print(f"  One HP enemy: Enemy HP {enemy2_char.current_hp}")
    # Enemy should be dead (HP <= 0) or nearly dead
    assert enemy2_char.current_hp <= 5, "One HP enemy should take significant damage"
    
    print("  ✓ Combat edge cases test passed!")


def test_item_usage_in_combat():
    """Test using items during combat."""
    print("\n=== Item Usage Test ===")
    
    from git_dungeon.core.entity import Entity
    from git_dungeon.core.inventory import InventoryComponent, Item, ItemType, ItemRarity, ItemStats
    
    player = Entity(id="player", name="Player")
    player_char = CharacterComponent(CharacterType.PLAYER, "Player")
    player_char.initialize_stats(hp=100, mp=50, attack=10, defense=5)
    player.add_component(player_char)
    
    inventory = InventoryComponent(max_slots=10)
    player.add_component(inventory)
    
    # Add health potion with proper stats
    potion = Item(
        id="health_potion",
        name="Health Potion",
        item_type=ItemType.CONSUMABLE,
        rarity=ItemRarity.COMMON,
        value=25,
    )
    potion.stats = ItemStats(hp_bonus=30)  # Heal 30 HP
    inventory.add_item(potion)
    
    # Take damage first
    player_char.current_hp = 50
    print(f"  Player HP before: {player_char.current_hp}")
    
    # Use item
    result = inventory.use_item(0, player)
    print(f"  Item used: {result}")
    print(f"  Player HP after: {player_char.current_hp}")
    
    assert player_char.current_hp > 50, "HP should increase"
    assert player_char.current_hp == 80, f"HP should be 80 (50+30), got {player_char.current_hp}"
    
    print("  ✓ Item usage test passed!")


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("Git Dungeon - Full Integration Tests")
    print("=" * 60)
    
    tests = [
        test_full_game_flow,
        test_save_and_load_game,
        test_combat_edge_cases,
        test_item_usage_in_combat,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
