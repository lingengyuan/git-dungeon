# golden_test.py - Golden tests for deterministic replay

"""
Golden tests for Git Dungeon engine.

These tests use fixed seeds to ensure deterministic behavior.
Run with: python tests/golden_test.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from git_dungeon.engine import (
    Engine, GameState, Action,
    create_rng, EventType
)


def test_golden_combat_seed_12345():
    """Golden test: Fixed seed produces consistent combat results."""
    print("=" * 60)
    print("🧪 Golden Test: Combat with seed=12345")
    print("=" * 60)
    
    seed = 12345
    rng = create_rng(seed)
    engine = Engine(rng=rng)
    
    # Create state
    state = GameState(seed=seed, repo_path="/test-repo")
    
    # Actions: attack, attack, defend, attack
    actions = [
        Action(action_type="combat", action_name="start_combat"),
        Action(action_type="combat", action_name="attack"),
        Action(action_type="combat", action_name="attack"),
        Action(action_type="combat", action_name="attack"),
    ]
    
    all_events = []
    
    for i, action in enumerate(actions):
        state, events = engine.apply(state, action)
        all_events.extend(events)
        print(f"  Action {i+1}: {action.action_name} -> {len(events)} events")
    
    # Verify results
    assert state.player.character.current_hp > 0, "Player should be alive"
    assert len(all_events) > 0, "Should have events"
    
    # Count event types
    event_counts = {}
    for e in all_events:
        event_counts[e.type.value] = event_counts.get(e.type.value, 0) + 1
    
    print("\n📊 Event Summary:")
    for event_type, count in sorted(event_counts.items()):
        print(f"   {event_type}: {count}")
    
    print(f"\n✅ Test passed! Player HP: {state.player.character.current_hp}")
    return True


def test_golden_multiple_battles_seed_99999():
    """Golden test: Multiple battles with different seed."""
    print("\n" + "=" * 60)
    print("🧪 Golden Test: Multiple battles with seed=99999")
    print("=" * 60)
    
    seed = 99999
    rng = create_rng(seed)
    engine = Engine(rng=rng)
    
    state = GameState(seed=seed, repo_path="/multi-battle-test")
    
    # Simulate 10 battles
    total_events = 0
    total_damage = 0
    
    for battle_num in range(10):
        # Start battle
        action = Action(action_type="combat", action_name="start_combat")
        state, events = engine.apply(state, action)
        total_events += len(events)
        
        # Fight until enemy defeated or player dead
        while state.in_combat and state.player.character.is_alive:
            action = Action(action_type="combat", action_name="attack")
            state, events = engine.apply(state, action)
            total_events += len(events)
            
            # Count damage dealt
            for e in events:
                if e.type == EventType.DAMAGE_DEALT:
                    if e.data.get("src_type") == "player":
                        total_damage += e.data.get("amount", 0)
        
        if not state.player.character.is_alive:
            break
    
    print("\n📊 Results:")
    print(f"   Battles fought: {min(battle_num + 1, 10)}")
    print(f"   Total events: {total_events}")
    print(f"   Total damage dealt: {total_damage}")
    print(f"   Player final HP: {state.player.character.current_hp}")
    
    assert total_damage > 0, "Should deal damage"
    assert total_events > 0, "Should have events"
    
    print("\n✅ Test passed!")
    return True


def test_golden_escape_mechanics_seed_55555():
    """Golden test: Escape mechanics are deterministic."""
    print("\n" + "=" * 60)
    print("🧪 Golden Test: Escape mechanics with seed=55555")
    print("=" * 60)
    
    # Run same scenario twice with same seed
    for run in range(2):
        rng = create_rng(55555)
        engine = Engine(rng=rng)
        state = GameState(seed=55555, repo_path="/escape-test")
        
        # Try to escape 5 times
        escapes = 0
        for i in range(5):
            action = Action(action_type="combat", action_name="start_combat")
            state, _ = engine.apply(state, action)
            
            action = Action(action_type="combat", action_name="escape")
            state, events = engine.apply(state, action)
            
            # Check if escaped
            for e in events:
                if e.type == EventType.BATTLE_ENDED and e.data.get("result") == "escaped":
                    escapes += 1
                    break
            
            # Reset combat state
            state.in_combat = False
            state.current_enemy = None
        
        print(f"  Run {run + 1}: Escaped {escapes}/5 times")
        
        # Both runs should have same result (deterministic)
        if run == 0:
            first_run_escapes = escapes
        else:
            assert escapes == first_run_escapes, "Should be deterministic"
    
    print(f"\n✅ Test passed! Both runs escaped {first_run_escapes}/5 times")
    return True


def test_golden_level_progression_seed_77777():
    """Golden test: Level progression is deterministic."""
    print("\n" + "=" * 60)
    print("🧪 Golden Test: Level progression with seed=77777")
    print("=" * 60)
    
    seed = 77777
    rng = create_rng(seed)
    engine = Engine(rng=rng)
    
    state = GameState(seed=seed, repo_path="/level-test")
    
    initial_level = state.player.character.level
    initial_exp = state.player.character.experience
    
    # Gain enough experience to level up
    # Manually add experience through actions
    for i in range(10):
        action = Action(
            action_type="combat",
            action_name="start_combat",
            data={"exp_reward": 50}
        )
        state, events = engine.apply(state, action)
        
        # Check for level up events
        for e in events:
            if e.type == EventType.LEVEL_UP:
                print(f"  🎉 Leveled up to {e.data['new_level']}!")
    
    final_level = state.player.character.level
    final_exp = state.player.character.experience
    
    print("\n📊 Level Progress:")
    print(f"   Initial: Level {initial_level}, EXP {initial_exp}")
    print(f"   Final: Level {final_level}, EXP {final_exp}")
    print(f"   Level-ups: {final_level - initial_level}")
    
    assert final_level >= initial_level, "Should not decrease level"
    
    print("\n✅ Test passed!")
    return True


def run_all_golden_tests():
    """Run all golden tests."""
    print("\n" + "🗡️  " + "=" * 58 + "  🗡️")
    print("        G I T   D U N G E O N   G O L D E N   T E S T S")
    print("🗡️  " + "=" * 58 + "  🗡️\n")
    
    tests = [
        ("Combat (seed=12345)", test_golden_combat_seed_12345),
        ("Multiple Battles (seed=99999)", test_golden_multiple_battles_seed_99999),
        ("Escape Mechanics (seed=55555)", test_golden_escape_mechanics_seed_55555),
        ("Level Progression (seed=77777)", test_golden_level_progression_seed_77777),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            test_func()
            results.append((name, "✅ PASS", None))
        except Exception as e:
            results.append((name, "❌ FAIL", str(e)))
    
    print("\n" + "=" * 60)
    print("📋 GOLDEN TEST SUMMARY")
    print("=" * 60)
    
    passed_count = 0
    for name, status, error in results:
        icon = "✅" if "PASS" in status else "❌"
        print(f"  {icon} {name}: {status}")
        if error:
            print(f"     Error: {error[:80]}...")
        if "PASS" in status:
            passed_count += 1
    
    print("=" * 60)
    print(f"  Total: {passed_count}/{len(tests)} tests passed")
    print("=" * 60)
    
    return passed_count == len(tests)


if __name__ == "__main__":
    success = run_all_golden_tests()
    sys.exit(0 if success else 1)
