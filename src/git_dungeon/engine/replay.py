# replay.py - Replay system for testing and debugging

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .events import GameEvent, EventType
from .model import GameState, Action
from .engine import Engine
from .rng import RNG, DefaultRNG


@dataclass
class Replay:
    """Replay data for deterministic replay"""
    version: str = "1.0"
    seed: int
    initial_state_hash: str
    actions: List[Dict[str, Any]]
    final_events_summary: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "seed": self.seed,
            "initial_state_hash": self.initial_state_hash,
            "actions": self.actions,
            "final_events_summary": self.final_events_summary,
        }
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Replay":
        return cls(
            version=data.get("version", "1.0"),
            seed=data.get("seed", 0),
            initial_state_hash=data.get("initial_state_hash", ""),
            actions=data.get("actions", []),
            final_events_summary=data.get("final_events_summary", []),
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "Replay":
        return cls.from_dict(json.loads(json_str))


class ReplaySystem:
    """System for recording and replaying games"""
    
    def __init__(self, engine: Engine):
        self.engine = engine
        self.actions: List[Action] = []
        self.events: List[GameEvent] = []
    
    def record_action(self, action: Action) -> None:
        """Record an action"""
        self.actions.append(action)
    
    def record_events(self, events: List[GameEvent]) -> None:
        """Record events"""
        self.events.extend(events)
    
    def create_replay(
        self,
        initial_state: GameState,
        seed: int
    ) -> Replay:
        """Create a replay from current recording"""
        # Generate summary of final events
        final_summary = []
        for event in self.events[-50:]:  # Last 50 events
            final_summary.append({
                "type": event.type.value,
                "summary": event.summary(),
            })
        
        return Replay(
            seed=seed,
            initial_state_hash=self._hash_state(initial_state),
            actions=[a.to_dict() for a in self.actions],
            final_events_summary=final_summary,
        )
    
    def replay(
        self,
        replay_data: Replay,
        initial_state: GameState
    ) -> tuple:
        """
        Replay a game from replay data.
        
        Returns:
            (final_state, replayed_events)
        """
        state = initial_state
        all_events = []
        
        rng = DefaultRNG(seed=replay_data.seed)
        engine = Engine(rng=rng)
        
        for action_dict in replay_data.actions:
            action = Action.from_dict(action_dict)
            state, events = engine.apply(state, action)
            all_events.extend(events)
        
        return state, all_events
    
    def verify_replay(
        self,
        replay_data: Replay,
        initial_state: GameState,
        expected_events_summary: List[Dict[str, Any]]
    ) -> bool:
        """
        Verify a replay produces expected results.
        
        Used for golden testing.
        """
        _, events = self.replay(replay_data, initial_state)
        
        # Compare summaries
        actual_summary = []
        for event in events[-50:]:
            actual_summary.append({
                "type": event.type.value,
                "summary": event.summary(),
            })
        
        return actual_summary == expected_events_summary
    
    def _hash_state(self, state: GameState) -> str:
        """Generate a simple hash of the state"""
        state_str = f"{state.player.character.level}_{len(state.enemies_defeated)}_{state.current_commit_index}"
        return str(hash(state_str))


def run_golden_test(
    seed: int,
    actions: List[Action],
    initial_state: GameState,
    expected_event_count: int = None,
    expected_wins: bool = None
) -> Dict[str, Any]:
    """
    Run a golden test with fixed seed.
    
    Args:
        seed: Random seed for determinism
        actions: List of actions to execute
        initial_state: Starting game state
        expected_event_count: Optional expected event count
        expected_wins: Optional expected win/loss result
        
    Returns:
        Test result dictionary
    """
    rng = DefaultRNG(seed=seed)
    engine = Engine(rng=rng)
    
    state = initial_state
    all_events = []
    
    for action in actions:
        state, events = engine.apply(state, action)
        all_events.extend(events)
    
    result = {
        "seed": seed,
        "actions_count": len(actions),
        "events_count": len(all_events),
        "final_player_hp": state.player.character.current_hp,
        "enemies_defeated": len(state.enemies_defeated),
        "is_game_over": state.is_game_over,
        "is_victory": state.is_victory,
        "passed": True,
        "errors": [],
    }
    
    # Verify constraints
    if expected_event_count is not None:
        if len(all_events) != expected_event_count:
            result["passed"] = False
            result["errors"].append(
                f"Expected {expected_event_count} events, got {len(all_events)}"
            )
    
    if expected_wins is not None:
        if state.is_victory != expected_wins:
            result["passed"] = False
            result["errors"].append(
                f"Expected victory={expected_wins}, got {state.is_victory}"
            )
    
    return result


def generate_test_replay(
    repo_path: str,
    seed: int,
    actions: List[str]
) -> Dict[str, Any]:
    """
    Generate a test replay for a repository.
    
    Args:
        repo_path: Path to Git repository
        seed: Random seed
        actions: List of action names ("attack", "defend", etc.)
        
    Returns:
        Replay data dictionary
    """
    rng = DefaultRNG(seed=seed)
    engine = Engine(rng=rng)
    
    # Create initial state
    state = GameState(
        seed=seed,
        repo_path=repo_path,
    )
    
    all_events = []
    
    # Generate actions
    for action_name in actions:
        action = Action(
            action_type="combat",
            action_name=action_name,
        )
        state, events = engine.apply(state, action)
        all_events.extend(events)
    
    # Create replay
    replay = Replay(
        seed=seed,
        initial_state_hash="test_hash",
        actions=[a.to_dict() for a in []],
        final_events_summary=[
            {"type": e.type.value, "summary": e.summary()}
            for e in all_events[-20:]
        ],
    )
    
    return replay.to_dict()
