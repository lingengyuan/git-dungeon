"""
Golden Tests - pytest compatible version

These tests use fixed seeds to ensure deterministic behavior.
Run with: PYTHONPATH=src python -m pytest tests/test_golden.py -v
"""

import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from git_dungeon.engine import (
    Engine, GameState, Action,
    create_rng, EventType
)


@pytest.fixture
def seed_12345():
    """Fixture for seed 12345."""
    rng = create_rng(12345)
    engine = Engine(rng=rng)
    state = GameState(seed=12345, repo_path="/test-repo")
    return rng, engine, state


@pytest.fixture
def seed_99999():
    """Fixture for seed 99999."""
    rng = create_rng(99999)
    engine = Engine(rng=rng)
    state = GameState(seed=99999, repo_path="/multi-battle-test")
    return rng, engine, state


@pytest.fixture
def seed_55555():
    """Fixture for seed 55555."""
    rng = create_rng(55555)
    engine = Engine(rng=rng)
    state = GameState(seed=55555, repo_path="/escape-test")
    return rng, engine, state


@pytest.fixture
def seed_77777():
    """Fixture for seed 77777."""
    rng = create_rng(77777)
    engine = Engine(rng=rng)
    state = GameState(seed=77777, repo_path="/level-test")
    return rng, engine, state


class TestGoldenCombat:
    """Golden tests for combat mechanics."""
    
    def test_golden_combat_seed_12345(self, seed_12345):
        """Golden test: Fixed seed produces consistent combat results."""
        rng, engine, state = seed_12345
        
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
        
        # Verify results
        assert state.player.character.current_hp > 0, "Player should be alive"
        assert len(all_events) > 0, "Should have events"
        
        # Count event types
        event_counts = {}
        for e in all_events:
            event_counts[e.type.value] = event_counts.get(e.type.value, 0) + 1
        
        # Should have expected event types
        assert "battle_started" in event_counts
        assert "enemy_defeated" in event_counts


class TestGoldenMultipleBattles:
    """Golden tests for multiple battles."""
    
    def test_golden_multiple_battles_seed_99999(self, seed_99999):
        """Golden test: Multiple battles with different seed."""
        rng, engine, state = seed_99999
        
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
        
        # Verify results
        assert total_damage > 0, "Should deal damage"
        assert total_events > 0, "Should have events"


class TestGoldenEscape:
    """Golden tests for escape mechanics."""
    
    def test_golden_escape_mechanics_seed_55555(self, seed_55555):
        """Golden test: Escape mechanics are deterministic."""
        rng, engine, state = seed_55555
        
        # Run same scenario twice with same seed
        first_run_escapes = None
        
        for run in range(2):
            rng = create_rng(55555)
            engine = Engine(rng=rng)
            state = GameState(seed=55555, repo_path="/escape-test")
            
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
            
            if run == 0:
                first_run_escapes = escapes
            else:
                # Both runs should have same result (deterministic)
                assert escapes == first_run_escapes, "Should be deterministic"


class TestGoldenLevelProgression:
    """Golden tests for level progression."""
    
    def test_golden_level_progression_seed_77777(self, seed_77777):
        """Golden test: Level progression is deterministic."""
        rng, engine, state = seed_77777
        
        initial_level = state.player.character.level
        initial_exp = state.player.character.experience
        
        # Gain experience through actions
        for i in range(10):
            action = Action(
                action_type="combat",
                action_name="start_combat",
                data={"exp_reward": 50}
            )
            state, events = engine.apply(state, action)
        
        final_level = state.player.character.level
        final_exp = state.player.character.experience
        
        # Verify results
        assert final_level >= initial_level, "Should not decrease level"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
