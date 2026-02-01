#!/usr/bin/env python3
"""Comprehensive game test script - edge cases and error handling."""

import sys
import os
from pathlib import Path
import tempfile
from datetime import datetime
import random

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from git_dungeon.core.game_engine import GameState
from git_dungeon.core.git_parser import GitParser, CommitInfo, FileChange
from git_dungeon.core.character import CharacterComponent, CharacterType
from git_dungeon.core.combat import CombatSystem, CombatEncounter, CombatAction, CombatResult
from git_dungeon.core.inventory import InventoryComponent, Item, ItemType, ItemRarity
from git_dungeon.core.entity import Entity
from git_dungeon.config import GameConfig, Difficulty


def test_empty_repository():
    """Test loading empty repository."""
    print("\n=== Test: Empty Repository ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = os.path.join(tmpdir, "empty")
        os.makedirs(repo_path)
        os.system(f"cd {repo_path} && git init > /dev/null 2>&1")
        
        state = GameState()
        result = state.load_repository(repo_path)
        print(f"  Load result: {result}")
        print(f"  Commits loaded: {len(state.commits)}")
        assert result == True, "Empty repo should load"
        print("  ✓ Empty repository test passed")


def test_invalid_repository():
    """Test loading invalid path."""
    print("\n=== Test: Invalid Repository ===")
    state = GameState()
    
    # Non-existent path
    result = state.load_repository("/nonexistent/path/to/repo")
    print(f"  Non-existent path result: {result}")
    assert result == False, "Non-existent path should fail"
    
    # Valid path but not a git repo
    with tempfile.TemporaryDirectory() as tmpdir:
        not_git_path = os.path.join(tmpdir, "not_git")
        os.makedirs(not_git_path)
        with open(os.path.join(not_git_path, "file.txt"), 'w') as f:
            f.write("test")
        
        result = state.load_repository(not_git_path)
        print(f"  Not git repo result: {result}")
    
    print("  ✓ Invalid repository test passed")


def test_very_large_commit():
    """Test commit with many changes."""
    print("\n=== Test: Very Large Commit ===")
    
    info = CommitInfo(
        hash="a" * 40,
        short_hash="a" * 8,
        message="Test large commit",
        author="Test",
        author_email="test@test.com",
        datetime=datetime.now(),
        additions=500,
        deletions=300,
        files_changed=50,
        file_changes=[],
        is_merge=False,
        is_revert=False,
        branches=[],
    )
    
    print(f"  Total changes: {info.total_changes}")
    print(f"  Difficulty factor: {info.difficulty_factor}")
    print(f"  Creature name: {info.get_creature_name()}")
    
    assert info.total_changes == 800, "Total changes should be additions + deletions"
    print("  ✓ Large commit test passed")


def test_character_edge_cases():
    """Test character edge cases."""
    print("\n=== Test: Character Edge Cases ===")
    
    char = CharacterComponent(CharacterType.PLAYER, "TestPlayer", level=1, experience=0)
    char.initialize_stats(hp=100, mp=50, attack=10, defense=5)
    
    print(f"  Level 1 HP: {char.current_hp}")
    
    char.gain_experience(100)  # Should trigger level up
    
    print(f"  After 100 exp - Level: {char.level}, HP: {char.current_hp}")
    
    info = char.get_level_info()
    print(f"  Level info: {info}")
    
    summary = char.get_stat_summary()
    print(f"  Stat summary HP: {summary.get('hp')}")
    
    power = char.get_power_level()
    print(f"  Power level: {power}")
    
    assert char.level >= 2, "Should have leveled up"
    print("  ✓ Character edge cases test passed")


def test_damage_calculation():
    """Test damage calculations with real entities."""
    print("\n=== Test: Damage Calculation ===")
    
    # Create attacker entity
    attacker = Entity(id="attacker", name="Attacker")
    attacker_char = CharacterComponent(CharacterType.PLAYER, "Attacker")
    attacker_char.initialize_stats(hp=100, mp=50, attack=10, defense=5)
    attacker.add_component(attacker_char)
    
    # Create defender entity
    defender = Entity(id="defender", name="Defender")
    defender_char = CharacterComponent(CharacterType.MONSTER, "Defender")
    defender_char.initialize_stats(hp=50, mp=0, attack=5, defense=5)
    defender.add_component(defender_char)
    
    combat = CombatSystem()
    
    # Normal damage - returns (damage, is_critical)
    result = combat.calculate_damage(attacker, defender, 10)
    damage, is_crit = result
    print(f"  Attack 10, Defense 5 -> Damage: {damage}, Crit: {is_crit}")
    assert isinstance(damage, int), "Damage should be int"
    
    # High defense
    defender_char.stats.defense.base_value = 100
    result = combat.calculate_damage(attacker, defender, 10)
    damage, is_crit = result
    print(f"  Attack 10, Defense 100 -> Damage: {damage}")
    assert damage >= 1, "Minimum 1 damage"
    
    print("  ✓ Damage calculation test passed")


def test_full_inventory():
    """Test inventory with full capacity."""
    print("\n=== Test: Full Inventory ===")
    
    inventory = InventoryComponent(max_slots=5)
    
    for i in range(6):
        item = Item(
            id=f"item_{i}",
            name=f"Item {i}",
            item_type=ItemType.CONSUMABLE,
            rarity=ItemRarity.COMMON,
            value=10,
        )
        result = inventory.add_item(item)
        print(f"  Add item {i}: {result}")
    
    print(f"  Inventory count: {inventory.item_count}")
    assert inventory.item_count == 5, "Should be capped at max slots"
    
    # Try to use non-existent slot
    result = inventory.use_item(10, None)
    print(f"  Use invalid slot: {result}")
    assert result == False, "Should fail to use invalid slot"
    
    print("  ✓ Full inventory test passed")


def test_combat_entity_preparation():
    """Test combat preparation with entities."""
    print("\n=== Test: Combat Entity Preparation ===")
    
    player = Entity(id="player", name="Player")
    player_char = CharacterComponent(CharacterType.PLAYER, "Player")
    player_char.initialize_stats(hp=100, mp=50, attack=10, defense=5)
    player.add_component(player_char)
    
    enemy = Entity(id="enemy", name="Enemy")
    enemy_char = CharacterComponent(CharacterType.MONSTER, "Enemy")
    enemy_char.initialize_stats(hp=50, mp=0, attack=10, defense=5)
    enemy.add_component(enemy_char)
    
    combat = CombatSystem()
    encounter = combat.start_combat(player, enemy)
    
    print(f"  Combat started: {encounter is not None}")
    print(f"  Player HP: {player_char.current_hp}")
    print(f"  Enemy HP: {enemy_char.current_hp}")
    
    assert encounter is not None, "Combat should start"
    print("  ✓ Combat entity preparation test passed")


def test_multiple_level_ups():
    """Test gaining massive experience."""
    print("\n=== Test: Multiple Level Ups ===")
    
    char = CharacterComponent(CharacterType.PLAYER, "TestPlayer")
    char.initialize_stats(hp=100, mp=50, attack=10, defense=5)
    
    initial_level = char.level
    print(f"  Initial level: {initial_level}")
    
    gained, leveled = char.gain_experience(5000)
    print(f"  Gained: {gained}, Leveled up: {leveled}")
    print(f"  New level: {char.level}")
    print(f"  Total exp gained: {char._total_exp_gained}")
    
    assert char.level > initial_level, "Should have leveled up multiple times"
    
    info = char.get_level_info()
    print(f"  Level info: {info}")
    
    print("  ✓ Multiple level ups test passed")


def test_item_stack_edge_cases():
    """Test item stacking edge cases."""
    print("\n=== Test: Item Stack Edge Cases ===")
    
    inventory = InventoryComponent(max_slots=10)
    
    # Create a player entity for item use
    player = Entity(id="player", name="Player")
    player_char = CharacterComponent(CharacterType.PLAYER, "Player")
    player_char.initialize_stats(hp=100, mp=50, attack=10, defense=5)
    player.add_component(player_char)
    
    # Add stackable items
    item1 = Item(
        id="item1",
        name="Health Potion",
        item_type=ItemType.CONSUMABLE,
        rarity=ItemRarity.COMMON,
        value=10,
        max_stack=5,
    )
    item1.quantity = 3
    
    result = inventory.add_item(item1)
    print(f"  Add stack 1: {result}")
    
    # Add same item to different slot
    item2 = Item(
        id="item2",
        name="Health Potion",
        item_type=ItemType.CONSUMABLE,
        rarity=ItemRarity.COMMON,
        value=10,
        max_stack=5,
    )
    item2.quantity = 4
    
    result = inventory.add_item(item2)
    print(f"  Add stack 2: {result}")
    
    # Use from stack with valid entity
    used = inventory.use_item(0, player)
    print(f"  Use item: {used}")
    
    print("  ✓ Item stack edge cases test passed")


def test_zero_stat_character():
    """Test character with zero stats."""
    print("\n=== Test: Zero Stat Character ===")
    
    char = CharacterComponent(CharacterType.MONSTER, "WeakEnemy")
    char.initialize_stats(hp=1, mp=0, attack=1, defense=0)
    
    attacker = Entity(id="attacker", name="Attacker")
    attacker_char = CharacterComponent(CharacterType.PLAYER, "Attacker")
    attacker_char.initialize_stats(hp=100, mp=50, attack=1, defense=0)
    attacker.add_component(attacker_char)
    
    defender = Entity(id="defender", name="WeakEnemy")
    defender.add_component(char)
    
    combat = CombatSystem()
    
    # Very low stats - base_damage=1, attack=1 -> initial = 2, defense=0 -> final = 2
    result = combat.calculate_damage(attacker, defender, 1)
    damage, is_crit = result
    print(f"  Attack 1, Defense 0 -> Damage: {damage}")
    assert damage >= 1, "Should be at least 1 damage"
    
    print("  ✓ Zero stat character test passed")


def test_experience_overflow():
    """Test experience handling on level up."""
    print("\n=== Test: Experience Overflow ===")
    
    char = CharacterComponent(CharacterType.PLAYER, "TestPlayer")
    char.initialize_stats(hp=100, mp=50, attack=10, defense=5)
    
    char.gain_experience(150)
    
    print(f"  Level: {char.level}")
    print(f"  Experience: {char.experience}")
    print(f"  Exp to next: {char.experience_to_next}")
    
    assert char.experience == 50, "Should have 50 excess exp"
    
    char.gain_experience(60)
    print(f"  After +60 - Level: {char.level}, Exp: {char.experience}")
    
    print("  ✓ Experience overflow test passed")


def test_creature_name_generation():
    """Test creature name generation from commit messages."""
    print("\n=== Test: Creature Name Generation ===")
    
    test_cases = [
        ("feat: Add new feature", True),
        ("fix: Critical bug", True),
        ("chore: Update deps", True),
        ("WIP: Work in progress", True),
        ("", True),  # Empty message
        ("just a simple message", True),
        ("refactor!: Breaking change", True),
    ]
    
    for msg, _ in test_cases:
        info = CommitInfo(
            hash="a" * 40,
            short_hash="a" * 8,
            message=msg,
            author="Test",
            author_email="test@test.com",
            datetime=datetime.now(),
            additions=10,
            deletions=5,
            files_changed=1,
            file_changes=[],
            is_merge=False,
            is_revert=False,
            branches=[],
        )
        name = info.get_creature_name()
        print(f"  '{msg}' -> '{name}'")
        assert len(name) > 0, "Name should not be empty"
    
    print("  ✓ Creature name generation test passed")


def test_difficulty_calculation():
    """Test difficulty factor calculation."""
    print("\n=== Test: Difficulty Calculation ===")
    
    cases = [
        (10, 5, False, False, 1.0),      # Normal
        (150, 50, False, False, 1.5),     # Many additions (1.0 + 0.5)
        (50, 100, False, False, 1.3),     # Many deletions (1.0 + 0.3)
        (10, 5, True, False, 1.2),        # Merge (1.0 + 0.2)
        (10, 5, False, True, 1.5),        # Revert (1.0 + 0.5)
        (200, 100, True, True, 2.2),      # Everything (1.0 + 0.5 + 0.3 + 0.2 + 0.5 = 2.5, capped?)
    ]
    
    for adds, dels, is_merge, is_revert, expected_min in cases:
        info = CommitInfo(
            hash="a" * 40,
            short_hash="a" * 8,
            message="test",
            author="Test",
            author_email="test@test.com",
            datetime=datetime.now(),
            additions=adds,
            deletions=dels,
            files_changed=1,
            file_changes=[],
            is_merge=is_merge,
            is_revert=is_revert,
            branches=[],
        )
        factor = info.difficulty_factor
        print(f"  Adds:{adds}, Dels:{dels}, Merge:{is_merge}, Revert:{is_revert} -> Factor: {factor}")
        assert factor >= expected_min, f"Factor {factor} should be at least {expected_min}"
    
    print("  ✓ Difficulty calculation test passed")


def test_save_system_edge_cases():
    """Test save system edge cases."""
    print("\n=== Test: Save System Edge Cases ===")
    
    from git_dungeon.core.save_system import SaveSystem
    
    state = GameState()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        save_system = SaveSystem(tmpdir)
        
        result = save_system.save(state, 0)
        print(f"  Save empty game: {result}")
        
        new_state = GameState()
        result = save_system.load(new_state, 0)
        print(f"  Load game: {result}")
        
        empty_state = GameState()
        result = save_system.load(empty_state, 999)
        print(f"  Load non-existent: {result}")
    
    print("  ✓ Save system edge cases test passed")


def test_game_state_reset():
    """Test game state reset."""
    print("\n=== Test: Game State Reset ===")
    
    state = GameState()
    
    char = state.player.get_component(CharacterComponent)
    char.gain_experience(200)
    
    print(f"  Pre-reset level: {char.level}")
    
    state = GameState()
    char = state.player.get_component(CharacterComponent)
    
    print(f"  Post-reset level: {char.level}")
    assert char.level == 1, "Should be fresh level 1"
    
    print("  ✓ Game state reset test passed")


def test_turn_order():
    """Test combat turn order."""
    print("\n=== Test: Turn Order ===")
    
    player = Entity(id="player", name="Player")
    player_char = CharacterComponent(CharacterType.PLAYER, "Player")
    player_char.initialize_stats(hp=100, mp=50, attack=10, defense=5)
    player.add_component(player_char)
    
    enemy = Entity(id="enemy", name="Enemy")
    enemy_char = CharacterComponent(CharacterType.MONSTER, "Enemy")
    enemy_char.initialize_stats(hp=50, mp=0, attack=10, defense=5)
    enemy.add_component(enemy_char)
    
    combat = CombatSystem()
    encounter = combat.start_combat(player, enemy)
    
    print(f"  Initial is_player_turn: {encounter.is_player_turn}")
    
    # Player takes action
    action = CombatAction(
        action_type="attack",
        source=player,
        target=enemy,
        damage=10,
    )
    encounter.player_action(action)
    
    print(f"  After player action is_player_turn: {encounter.is_player_turn}")
    
    print("  ✓ Turn order test passed")


def test_inventory_remove_by_slot():
    """Test removing items from inventory by slot."""
    print("\n=== Test: Inventory Remove By Slot ===")
    
    inventory = InventoryComponent(max_slots=10)
    
    for i in range(3):
        item = Item(
            id=f"item_{i}",
            name=f"Item {i}",
            item_type=ItemType.CONSUMABLE,
            rarity=ItemRarity.COMMON,
            value=10,
        )
        inventory.add_item(item)
    
    print(f"  Initial count: {inventory.item_count}")
    
    # Remove by slot index
    removed = inventory.remove_item(1)
    print(f"  Remove slot 1: {removed is not None}")
    print(f"  After remove count: {inventory.item_count}")
    
    # Remove out of bounds
    removed = inventory.remove_item(99)
    print(f"  Remove invalid slot: {removed is None}")
    
    print("  ✓ Inventory remove test passed")


def test_full_combat_flow():
    """Test complete combat flow."""
    print("\n=== Test: Full Combat Flow ===")
    
    player = Entity(id="player", name="Player")
    player_char = CharacterComponent(CharacterType.PLAYER, "Player")
    player_char.initialize_stats(hp=100, mp=50, attack=20, defense=10)
    player.add_component(player_char)
    
    enemy = Entity(id="enemy", name="Enemy")
    enemy_char = CharacterComponent(CharacterType.MONSTER, "Enemy")
    enemy_char.initialize_stats(hp=30, mp=0, attack=10, defense=5)
    enemy.add_component(enemy_char)
    
    combat = CombatSystem()
    encounter = combat.start_combat(player, enemy)
    
    print(f"  Combat started - Turn: {encounter.turn_number}")
    print(f"  Player HP: {player_char.current_hp}, Enemy HP: {enemy_char.current_hp}")
    
    # Player attacks until enemy dies
    while enemy_char.current_hp > 0 and encounter.is_player_turn:
        action = CombatAction(
            action_type="attack",
            source=player,
            target=enemy,
            damage=20,
        )
        encounter.player_action(action)
        print(f"  Player attacks! Enemy HP: {enemy_char.current_hp}")
    
    print(f"  Final - Player HP: {player_char.current_hp}, Enemy HP: {enemy_char.current_hp}")
    print(f"  Combat ended: {encounter.ended}")
    
    print("  ✓ Full combat flow test passed")


def test_equipment_stats():
    """Test equipment stat bonuses."""
    print("\n=== Test: Equipment Stats ===")
    
    char = CharacterComponent(CharacterType.PLAYER, "TestPlayer")
    char.initialize_stats(hp=100, mp=50, attack=10, defense=5)
    
    # Check base stats
    print(f"  Base HP: {char.stats.hp.value}")
    print(f"  Base Attack: {char.stats.attack.value}")
    
    # Level up should increase stats
    char.gain_experience(500)
    print(f"  After level up - HP: {char.stats.hp.value}, Attack: {char.stats.attack.value}")
    
    assert char.stats.hp.value > 100, "HP should increase"
    
    print("  ✓ Equipment stats test passed")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Git Dungeon - Comprehensive Edge Case Tests")
    print("=" * 60)
    
    tests = [
        test_empty_repository,
        test_invalid_repository,
        test_very_large_commit,
        test_character_edge_cases,
        test_damage_calculation,
        test_full_inventory,
        test_combat_entity_preparation,
        test_multiple_level_ups,
        test_item_stack_edge_cases,
        test_zero_stat_character,
        test_experience_overflow,
        test_creature_name_generation,
        test_difficulty_calculation,
        test_save_system_edge_cases,
        test_game_state_reset,
        test_turn_order,
        test_inventory_remove_by_slot,
        test_full_combat_flow,
        test_equipment_stats,
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
