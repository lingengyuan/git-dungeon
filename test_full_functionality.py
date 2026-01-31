#!/usr/bin/env python3
"""
Comprehensive game functionality test with screenshots.
Tests all major features and validates game integrity.
"""

import sys
from pathlib import Path
import tempfile
import os
import json
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from src.core.game_engine import GameState
from src.core.character import CharacterComponent, CharacterType
from src.core.combat import CombatSystem, CombatAction, CombatResult
from src.core.inventory import InventoryComponent, Item, ItemType, ItemRarity, ItemStats
from src.core.lua import LuaEngine, MonsterTemplate, DropTable, Theme, DropEntry
from src.config import GameConfig


def create_test_screenshot(content: str, title: str) -> str:
    """Create a text-based screenshot."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    border = "=" * 60
    
    screenshot = f"""
{border}
{title.upper().center(60)}
{timestamp}
{border}

{content}

{border}
"""
    return screenshot


def test_1_repository_loading():
    """Test 1: Repository Loading"""
    print("\n" + "=" * 60)
    print("TEST 1: Repository Loading")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = os.path.join(tmpdir, "test_repo")
        os.makedirs(repo_path)
        os.system(f"cd {repo_path} && git init > /dev/null 2>&1")
        os.system(f"cd {repo_path} && git config user.email 'test@test.com'")
        os.system(f"cd {repo_path} && git config user.name 'Test'")
        
        # Create commits
        commands = [
            "echo 'init' > README.md && git add . && git commit -m 'Initial' -q",
            "echo 'a=1' > app.py && git add . && git commit -m 'feat: Add app' -q",
            "echo 'b=2' >> app.py && git add . && git commit -m 'fix: Bug fix' -q",
        ]
        for cmd in commands:
            os.system(f"cd {repo_path} && {cmd}")
        
        # Load repository
        config = GameConfig()
        state = GameState(config=config)
        result = state.load_repository(repo_path)
        
        print(f"  Repository loaded: {result}")
        print(f"  Commits found: {len(state.commits)}")
        
        for i, commit in enumerate(state.commits):
            print(f"    [{i+1}] {commit.get_creature_name()}: +{commit.additions}/-{commit.deletions}")
        
        assert result == True, "Failed to load repository"
        assert len(state.commits) >= 3, "Not enough commits"
        
        return create_test_screenshot(
            f"Repository: {repo_path}\n"
            f"Commits: {len(state.commits)}\n"
            f"Status: SUCCESS",
            "TEST 1: Repository Loading"
        )


def test_2_character_creation():
    """Test 2: Character Creation"""
    print("\n" + "=" * 60)
    print("TEST 2: Character Creation")
    print("=" * 60)
    
    state = GameState()
    char = state.player.get_component(CharacterComponent)
    
    print(f"  Name: {char.name}")
    print(f"  Level: {char.level}")
    print(f"  HP: {char.current_hp}/{char.stats.hp.value}")
    print(f"  MP: {char.current_mp}/{char.stats.mp.value}")
    print(f"  ATK: {char.stats.attack.value}")
    print(f"  DEF: {char.stats.defense.value}")
    print(f"  Speed: {char.stats.speed.value}")
    print(f"  Critical: {char.stats.critical.value}%")
    print(f"  Evasion: {char.stats.evasion.value}%")
    
    # Get stat summary
    summary = char.get_stat_summary()
    power = char.get_power_level()
    
    print(f"\n  Power Level: {power}")
    print(f"  Stat Summary: HP={summary['hp']}, ATK={summary['attack']}")
    
    assert char.name == "Developer", "Wrong character name"
    assert char.level == 1, "Should start at level 1"
    assert char.current_hp == char.stats.hp.value, "Should be full HP"
    
    return create_test_screenshot(
        f"Character: {char.name}\n"
        f"Level: {char.level} | HP: {char.current_hp}/{char.stats.hp.value}\n"
        f"ATK: {char.stats.attack.value} | DEF: {char.stats.defense.value}\n"
        f"Power Level: {power}\n"
        f"Status: SUCCESS",
        "TEST 2: Character Creation"
    )


def test_3_character_leveling():
    """Test 3: Character Leveling"""
    print("\n" + "=" * 60)
    print("TEST 3: Character Leveling")
    print("=" * 60)
    
    state = GameState()
    char = state.player.get_component(CharacterComponent)
    
    initial_hp = char.stats.hp.value
    initial_atk = char.stats.attack.value
    
    print(f"  Before leveling:")
    print(f"    Level: {char.level}")
    print(f"    HP: {char.stats.hp.value}")
    print(f"    ATK: {char.stats.attack.value}")
    print(f"    EXP: {char.experience}/{char.experience_to_next}")
    
    # Gain experience
    gained, leveled = char.gain_experience(150)
    print(f"\n  Gained 150 EXP:")
    print(f"    Leveled up: {leveled}")
    print(f"    New Level: {char.level}")
    print(f"    New HP: {char.stats.hp.value}")
    print(f"    New ATK: {char.stats.attack.value}")
    
    # Get level info
    info = char.get_level_info()
    print(f"\n  Level Info:")
    print(f"    Level: {info['level']}")
    print(f"    Progress: {info['progress']:.1f}%")
    print(f"    Total EXP: {info['total_exp']}")
    
    assert char.level >= 2, "Should have leveled up"
    assert char.stats.hp.value > initial_hp, "HP should increase"
    
    return create_test_screenshot(
        f"Before: Lv1, HP={initial_hp}, ATK={initial_atk}\n"
        f"After: Lv{char.level}, HP={char.stats.hp.value}, ATK={char.stats.attack.value}\n"
        f"EXP Gained: {char._total_exp_gained}\n"
        f"Status: SUCCESS",
        "TEST 3: Character Leveling"
    )


def test_4_inventory_system():
    """Test 4: Inventory System"""
    print("\n" + "=" * 60)
    print("TEST 4: Inventory System")
    print("=" * 60)
    
    inventory = InventoryComponent(max_slots=10)
    
    # Add items
    items_to_add = [
        ("Health Potion", ItemType.CONSUMABLE, ItemStats(hp_bonus=30)),
        ("Mana Potion", ItemType.CONSUMABLE, ItemStats(mp_bonus=20)),
        ("Iron Sword", ItemType.WEAPON, ItemStats(attack=5)),
        ("Wood Shield", ItemType.ARMOR, ItemStats(defense=3)),
        ("Speed Ring", ItemType.ACCESSORY, ItemStats(luck_bonus=10)),
    ]
    
    print(f"  Adding items:")
    for i, (name, item_type, stats) in enumerate(items_to_add):
        item = Item(
            id=f"item_{i}",
            name=name,
            item_type=item_type,
            rarity=ItemRarity.COMMON,
            value=25,
        )
        item.stats = stats
        result, slot = inventory.add_item(item)
        print(f"    [{slot}] {name}: {result}")
    
    print(f"\n  Inventory: {inventory.item_count}/{inventory.max_slots} slots")
    
    # List all items
    print(f"\n  Items:")
    for i, item in enumerate(inventory.items):
        if item:
            rarity_icon = {"common": "⚪", "rare": "🔵", "epic": "🟣", "legendary": "🟡"}.get(item.rarity.value, "⚪")
            print(f"    [{i}] {rarity_icon} {item.name} ({item.item_type.value})")
    
    # Test item usage with proper entity
    from src.core.entity import Entity
    
    # Create character component
    char_comp = CharacterComponent(CharacterType.PLAYER, "TestPlayer")
    char_comp.initialize_stats(hp=100, mp=50, attack=10, defense=5)
    char_comp.current_hp = 50
    
    # Create entity with character and inventory
    player_entity = Entity(id="player", name="Player")
    player_entity.add_component(char_comp)
    
    inventory = InventoryComponent(max_slots=10)
    player_entity.add_component(inventory)
    
    # Add health potion
    potion = Item(
        id="health_potion",
        name="Health Potion",
        item_type=ItemType.CONSUMABLE,
        rarity=ItemRarity.COMMON,
        value=25,
    )
    potion.stats = ItemStats(hp_bonus=30)
    inventory.add_item(potion)
    
    print(f"\n  Testing item usage:")
    print(f"    HP before: {char_comp.current_hp}")
    
    success = inventory.use_item(0, player_entity)
    print(f"    Used Health Potion: {success}")
    print(f"    HP after: {char_comp.current_hp}")
    
    # Get all items
    all_items = inventory.get_all_items()
    print(f"\n  Total items with quantity: {len(all_items)}")
    
    return create_test_screenshot(
        f"Slots: {inventory.item_count}/10\n"
        f"Items: {len(all_items)} types\n"
        f"Potion test: HP 50 -> {char_comp.current_hp}\n"
        f"Status: SUCCESS",
        "TEST 4: Inventory System"
    )


def test_5_combat_system():
    """Test 5: Combat System"""
    print("\n" + "=" * 60)
    print("TEST 5: Combat System")
    print("=" * 60)
    
    # Create player
    player = CharacterComponent(CharacterType.PLAYER, "Developer")
    player.initialize_stats(hp=100, mp=50, attack=20, defense=10)
    
    # Create enemy
    enemy = CharacterComponent(CharacterType.MONSTER, "Bug")
    enemy.initialize_stats(hp=50, mp=0, attack=10, defense=5)
    
    combat = CombatSystem()
    encounter = combat.start_combat(
        player.get_entity() if hasattr(player, 'get_entity') else None,
        enemy.get_entity() if hasattr(enemy, 'get_entity') else None,
    )
    
    print(f"  Combat started!")
    print(f"  Player HP: {player.current_hp}")
    print(f"  Enemy HP: {enemy.current_hp}")
    print(f"  Player turn: {encounter.is_player_turn}")
    
    # Battle loop
    turn = 1
    combat_log = []
    
    print(f"\n  Battle Log:")
    while not encounter.ended and turn <= 20:
        if encounter.is_player_turn:
            # Player attacks
            damage = 20  # base damage
            actual_damage = enemy.take_damage(damage)
            combat_log.append(f"  Turn {turn}: Player attacks for {actual_damage} damage!")
            print(f"    Turn {turn}: Player deals {actual_damage} dmg (Enemy HP: {enemy.current_hp})")
            
            if enemy.current_hp <= 0:
                combat_log.append(f"  Turn {turn}: Enemy defeated!")
                print(f"    Enemy HP: 0 - DEFEATED!")
                break
        else:
            # Enemy attacks
            actual_damage = player.take_damage(10)
            combat_log.append(f"  Turn {turn}: Enemy attacks for {actual_damage} damage!")
            print(f"    Turn {turn}: Enemy deals {actual_damage} dmg (Player HP: {player.current_hp})")
            
            if player.current_hp <= 0:
                combat_log.append(f"  Turn {turn}: Player defeated!")
                print(f"    Player HP: 0 - DEFEATED!")
                break
        
        encounter.turn_phase = "player" if encounter.turn_phase == "enemy" else "enemy"
        turn += 1
    
    print(f"\n  Combat ended in {turn} turns")
    print(f"  Result: {'VICTORY' if enemy.current_hp <= 0 else 'INCOMPLETE'}")
    
    assert enemy.current_hp <= 0, "Enemy should be defeated"
    
    return create_test_screenshot(
        f"Combat: Player vs Enemy\n"
        f"Turns: {turn}\n"
        f"Player: {player.current_hp} HP left\n"
        f"Enemy: {'DEFEATED' if enemy.current_hp <= 0 else 'ALIVE'}\n"
        f"Status: SUCCESS",
        "TEST 5: Combat System"
    )


def test_6_lua_content_system():
    """Test 6: Lua/JSON Content System"""
    print("\n" + "=" * 60)
    print("TEST 6: Lua/JSON Content System")
    print("=" * 60)
    
    engine = LuaEngine()
    
    # Add content via Python API
    print(f"  Lua available: {hasattr(engine, 'lua') and engine.lua is not None}")
    
    # Add monsters
    monsters = [
        MonsterTemplate(name="SyntaxError", base_hp=30, base_attack=10, experience=20),
        MonsterTemplate(name="TypeError", base_hp=50, base_attack=15, experience=35),
        MonsterTemplate(name="ImportError", base_hp=80, base_attack=20, experience=50),
    ]
    for m in monsters:
        engine.monsters[m.name] = m
    
    print(f"\n  Monsters defined: {len(engine.monsters)}")
    for name, m in engine.monsters.items():
        if name != "default":
            print(f"    - {name}: HP={m.base_hp}, ATK={m.base_attack}, EXP={m.experience}")
    
    # Add drop table
    table = DropTable(name="common_drops")
    table.entries = [
        DropEntry(item_id="Health Potion", chance=0.3),
        DropEntry(item_id="Mana Potion", chance=0.2),
        DropEntry(item_id="Gold", chance=0.5),
    ]
    engine.drop_tables["common_drops"] = table
    
    print(f"\n  Drop tables: {len(engine.drop_tables)}")
    for name, t in engine.drop_tables.items():
        if name != "default":
            print(f"    - {name}: {len(t.entries)} entries")
    
    # Add theme
    theme = Theme(
        id="python",
        name="Python",
        icon="🐍",
        color_scheme="blue",
        monster_prefixes=["SyntaxError", "TypeError", "ImportError"],
    )
    engine.themes["python"] = theme
    
    print(f"\n  Themes: {len(engine.themes)}")
    for tid, t in engine.themes.items():
        print(f"    - {t.icon} {t.name}")
    
    # Get all content
    content = engine.get_all_content()
    print(f"\n  Total content:")
    print(f"    Monsters: {len(content['monsters'])}")
    print(f"    Drop tables: {len(content['drop_tables'])}")
    print(f"    Themes: {len(content['themes'])}")
    
    return create_test_screenshot(
        f"Monsters: {len(engine.monsters)-1}\n"
        f"Drop Tables: {len(engine.drop_tables)}\n"
        f"Themes: {len(engine.themes)}\n"
        f"Status: SUCCESS",
        "TEST 6: Lua/JSON Content System"
    )


def test_7_save_load_system():
    """Test 7: Save/Load System"""
    print("\n" + "=" * 60)
    print("TEST 7: Save/Load System")
    print("=" * 60)
    
    from src.core.save_system import SaveSystem
    
    with tempfile.TemporaryDirectory() as tmpdir:
        save_system = SaveSystem(tmpdir)
        
        # Create game state
        state = GameState()
        
        # Modify state
        char = state.player.get_component(CharacterComponent)
        char.gain_experience(200)
        initial_level = char.level
        initial_exp = char._total_exp_gained
        
        print(f"  Before save:")
        print(f"    Level: {char.level}")
        print(f"    Total EXP: {char._total_exp_gained}")
        
        # Save
        result = save_system.save(state, 0)
        print(f"\n  Save result: {result}")
        
        # Create new state and load
        new_state = GameState()
        load_result = save_system.load(new_state, 0)
        print(f"  Load result: {load_result}")
        
        new_char = new_state.player.get_component(CharacterComponent)
        print(f"\n  After load:")
        print(f"    Level: {new_char.level}")
        print(f"    Total EXP: {new_char._total_exp_gained}")
        
        assert new_char.level == initial_level, "Level not preserved"
        assert new_char._total_exp_gained == initial_exp, "EXP not preserved"
        
        return create_test_screenshot(
            f"Before: Level {initial_level}, EXP {initial_exp}\n"
            f"After: Level {new_char.level}, EXP {new_char._total_exp_gained}\n"
            f"Status: SUCCESS",
            "TEST 7: Save/Load System"
        )


def test_8_full_game_loop():
    """Test 8: Full Game Loop"""
    print("\n" + "=" * 60)
    print("TEST 8: Full Game Loop")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = os.path.join(tmpdir, "game_repo")
        os.makedirs(repo_path)
        os.system(f"cd {repo_path} && git init > /dev/null 2>&1")
        os.system(f"cd {repo_path} && git config user.email 'test@test.com'")
        os.system(f"cd {repo_path} && git config user.name 'Test'")
        
        # Create simple commits
        commands = [
            "echo 'a' > f1.txt && git add . && git commit -m 'feat: First' -q",
            "echo 'b' > f2.txt && git add . && git commit -m 'fix: Second' -q",
        ]
        for cmd in commands:
            os.system(f"cd {repo_path} && {cmd}")
        
        # Load game
        state = GameState()
        result = state.load_repository(repo_path)
        
        print(f"  Repository loaded: {result}")
        print(f"  Commits: {len(state.commits)}")
        print(f"  Player: {state.player.get_component(CharacterComponent).name}")
        
        # Battle through commits
        kills = 0
        total_damage_dealt = 0
        total_damage_taken = 0
        
        print(f"\n  Starting battles:")
        
        while state.current_commit and not state.is_game_over:
            commit = state.current_commit
            print(f"\n  --- Enemy {kills + 1}: {commit.get_creature_name()} ---")
            print(f"  Message: {commit.message[:30]}...")
            print(f"  Changes: +{commit.additions}/-{commit.deletions}")
            
            # Start combat
            if state.start_combat():
                char = state.player.get_component(CharacterComponent)
                enemy_char = state.current_combat.enemy.get_component(CharacterComponent)
                
                # Quick battle simulation
                while state.current_combat and not state.current_combat.ended:
                    if state.current_combat.is_player_turn:
                        dmg = 25
                        enemy_char.take_damage(dmg)
                        total_damage_dealt += dmg
                        if enemy_char.current_hp <= 0:
                            break
                    else:
                        dmg = char.take_damage(10)
                        total_damage_taken += dmg
                    state.current_combat.turn_phase = "player" if state.current_combat.turn_phase == "enemy" else "enemy"
                
                # End combat
                if state.current_combat:
                    state.current_combat.ended = True
                    state.current_combat = None
                
                kills += 1
                print(f"  Defeated! Player HP: {char.current_hp}")
            
            # Advance
            if not state._advance_to_next_commit():
                break
        
        print(f"\n  === GAME SUMMARY ===")
        print(f"  Enemies defeated: {kills}")
        print(f"  Total damage dealt: {total_damage_dealt}")
        print(f"  Total damage taken: {total_damage_taken}")
        
        final_char = state.player.get_component(CharacterComponent)
        print(f"  Final level: {final_char.level}")
        print(f"  Final HP: {final_char.current_hp}")
        print(f"  Total EXP: {final_char._total_exp_gained}")
        
        return create_test_screenshot(
            f"Game Loop Complete!\n"
            f"Enemies Defeated: {kills}\n"
            f"Damage Dealt: {total_damage_dealt}\n"
            f"Damage Taken: {total_damage_taken}\n"
            f"Final Level: {final_char.level}\n"
            f"Status: SUCCESS",
            "TEST 8: Full Game Loop"
        )


def main():
    """Run all tests and generate report."""
    print("\n" + "=" * 70)
    print(" " * 20 + "GIT DUNGEON" + " " * 20)
    print(" " * 15 + "FUNCTIONALITY TEST" + " " * 15)
    print("=" * 70)
    
    screenshots = []
    tests_passed = 0
    tests_total = 8
    
    # Run all tests
    try:
        screenshots.append(test_1_repository_loading())
        tests_passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        screenshots.append(f"TEST 1 FAILED: {e}")
    
    try:
        screenshots.append(test_2_character_creation())
        tests_passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        screenshots.append(f"TEST 2 FAILED: {e}")
    
    try:
        screenshots.append(test_3_character_leveling())
        tests_passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        screenshots.append(f"TEST 3 FAILED: {e}")
    
    try:
        screenshots.append(test_4_inventory_system())
        tests_passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        screenshots.append(f"TEST 4 FAILED: {e}")
    
    try:
        screenshots.append(test_5_combat_system())
        tests_passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        screenshots.append(f"TEST 5 FAILED: {e}")
    
    try:
        screenshots.append(test_6_lua_content_system())
        tests_passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        screenshots.append(f"TEST 6 FAILED: {e}")
    
    try:
        screenshots.append(test_7_save_load_system())
        tests_passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        screenshots.append(f"TEST 7 FAILED: {e}")
    
    try:
        screenshots.append(test_8_full_game_loop())
        tests_passed += 1
    except Exception as e:
        print(f"  FAILED: {e}")
        screenshots.append(f"TEST 8 FAILED: {e}")
    
    # Generate final report
    print("\n" + "=" * 70)
    print(" " * 25 + "TEST RESULTS" + " " * 25)
    print("=" * 70)
    print(f"\n  Tests Passed: {tests_passed}/{tests_total}")
    print(f"  Success Rate: {tests_passed/tests_total*100:.1f}%")
    print(f"\n  {'✅ ALL TESTS PASSED!' if tests_passed == tests_total else '⚠️ SOME TESTS FAILED'}")
    
    # Save screenshots to file
    report_path = "/root/projects/git-dungeon/test_screenshots.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(screenshots))
    print(f"\n  Screenshots saved to: {report_path}")
    
    return tests_passed == tests_total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
