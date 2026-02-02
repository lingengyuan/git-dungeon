"""
Scenario Harness - Functional test scenarios for Git Dungeon

Provides standardized scenario definition, execution, and result collection.
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from git_dungeon.engine import Engine, GameState, DefaultRNG
from git_dungeon.engine.route import build_route, NodeKind
from git_dungeon.content.loader import load_content


class StepResult(Enum):
    CONTINUE = "continue"
    COMPLETE = "complete"
    FAIL = "fail"


@dataclass
class ScenarioStep:
    """Scenario step definition"""
    name: str
    action: Callable[[Engine, GameState], tuple[GameState, StepResult]]
    assert_fn: Optional[Callable[[GameState, Dict], bool]] = None
    description: str = ""


@dataclass
class ScenarioExpect:
    """Expected result for scenario"""
    min_enemies_killed: int = 0
    expected_character: Optional[str] = None
    expected_chapters: int = 0
    expected_victory: Optional[bool] = None
    expected_points_range: Optional[tuple[int, int]] = None
    expected_unlocks_added: int = 0
    snapshot_keys: List[str] = field(default_factory=list)


@dataclass
class Scenario:
    """Functional test scenario definition
    
    Attributes:
        id: Unique identifier (e.g., "m3_meta_points_happy")
        seed: Random seed
        repo_builder: Repository builder function
        steps: List of scenario steps
        expect: Expected result
        description: Scenario description
    """
    id: str
    seed: int
    repo_builder: Callable
    steps: List[ScenarioStep]
    expect: ScenarioExpect
    description: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class ScenarioResult:
    """Scenario execution result"""
    scenario_id: str
    success: bool
    run_state: Optional[Dict] = None
    meta_profile: Optional[Dict] = None
    route_sequence: List[Dict] = None
    battle_count: int = 0
    event_count: int = 0
    points_earned: int = 0
    error: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    snapshots: Dict[str, Any] = field(default_factory=dict)


class ScenarioRunner:
    """Scenario executor"""
    
    def __init__(self, content_dir: str = "src/git_dungeon/content", packs_dir: str = "src/git_dungeon/content/packs"):
        self.content_dir = content_dir
        self.packs_dir = packs_dir
        self.content = load_content(content_dir)
    
    def run(self, scenario: Scenario) -> ScenarioResult:
        """Execute scenario"""
        result = ScenarioResult(scenario_id=scenario.id, success=False)
        
        try:
            # 1. Build repository
            repo_info = scenario.repo_builder()
            
            # 2. Initialize engine and state
            engine = Engine(rng=DefaultRNG(seed=scenario.seed))
            state = GameState(seed=scenario.seed)
            
            # 3. Setup character
            content = load_content(self.content_dir)
            if scenario.expect.expected_character:
                state.character_id = scenario.expect.expected_character
                char = content.characters.get(state.character_id)
                if char:
                    state.player.character.current_hp = char.stats.hp
                    state.player.energy.max_energy = char.stats.energy
            
            # 4. Build route
            commits = repo_info.get("commits", [])
            route = build_route(commits, seed=scenario.seed, chapter_index=0, node_count=10)
            state.chapter_route = route
            
            result.route_sequence = [self._serialize_node(n) for n in route.nodes]
            
            # 5. Execute scenario steps
            for step in scenario.steps:
                try:
                    state, step_result = step.action(engine, state)
                    
                    # Assertion check
                    if step.assert_fn:
                        step_assert_result = step.assert_fn(state, result.__dict__)
                        if not step_assert_result:
                            result.error = f"Step '{step.name}' assertion failed"
                            return result
                    
                    if step_result == StepResult.FAIL:
                        result.error = f"Step '{step.name}' failed"
                        return result
                    
                    if step_result == StepResult.COMPLETE:
                        break
                        
                except Exception as e:
                    result.error = f"Step '{step.name}' error: {str(e)}"
                    return result
            
            # 6. Collect results
            result.success = True
            result.run_state = self._serialize_state(state)
            result.battle_count = len([n for n in route.nodes if n.kind == NodeKind.BATTLE])
            result.event_count = len([n for n in route.nodes if n.kind == NodeKind.EVENT])
            
            # 7. Generate snapshots
            result.snapshots = self._generate_snapshots(scenario, state, route, result)
            
        except Exception as e:
            result.error = f"Scenario error: {str(e)}"
        
        return result
    
    def _serialize_node(self, node) -> Dict:
        """Serialize node"""
        return {
            "id": node.id,
            "kind": node.kind.value if hasattr(node.kind, 'value') else str(node.kind),
            "enemy_id": getattr(node, 'enemy_id', None),
            "event_id": getattr(node, 'event_id', None),
        }
    
    def _serialize_state(self, state: GameState) -> Dict:
        """Serialize game state"""
        return {
            "character_id": state.character_id,
            "current_hp": state.player.character.current_hp,
            "max_hp": state.player.character.max_hp,
            "energy": state.player.energy.current_energy,
            "max_energy": state.player.energy.max_energy,
            "gold": state.player.gold,
            "in_combat": state.in_combat,
            "route_progress": state.route_progress,
            "deck_size": len(state.player.deck.draw_pile) + len(state.player.deck.hand) + len(state.player.deck.discard_pile),
        }
    
    def _generate_snapshots(self, scenario: Scenario, state: GameState, route, result: ScenarioResult) -> Dict:
        """Generate snapshots for the scenario"""
        return {
            "route": result.route_sequence,
            "final_state": result.run_state,
            "battle_count": result.battle_count,
            "event_count": result.event_count,
        }


class RepoFactory:
    """Test repository factory - generates controlled minimal Git repos"""
    
    @staticmethod
    def make_repo_basic() -> Dict:
        """Generate basic test repo (feat/fix/docs/refactor mix)"""
        return {
            "commits": [
                {"type": "feat", "msg": "feat: add login feature"},
                {"type": "fix", "msg": "fix: resolve login bug"},
                {"type": "docs", "msg": "docs: update README"},
                {"type": "refactor", "msg": "refactor: login module"},
                {"type": "feat", "msg": "feat: add logout feature"},
                {"type": "fix", "msg": "fix: logout crash"},
                {"type": "test", "msg": "test: add login tests"},
                {"type": "chore", "msg": "chore: update deps"},
            ],
            "expected_enemies": 8,
        }
    
    @staticmethod
    def make_repo_with_merge() -> Dict:
        """Generate repo with merge commits"""
        return {
            "commits": [
                {"type": "feat", "msg": "feat: add feature A"},
                {"type": "feat", "msg": "feat: add feature B"},
                {"type": "merge", "msg": "merge: merge feature B into main"},
                {"type": "fix", "msg": "fix: merge conflict"},
                {"type": "feat", "msg": "feat: add feature C"},
            ],
            "expected_enemies": 5,
        }
    
    @staticmethod
    def make_repo_test_heavy() -> Dict:
        """Generate test-heavy repo"""
        commits = []
        for i in range(12):
            if i % 3 == 0:
                commits.append({"type": "test", "msg": f"test: test case {i}"})
            elif i % 3 == 1:
                commits.append({"type": "feat", "msg": f"feat: feature {i}"})
            else:
                commits.append({"type": "fix", "msg": f"fix: bug {i}"})
        
        return {
            "commits": commits,
            "expected_enemies": 12,
        }
    
    @staticmethod
    def make_repo_large_diff() -> Dict:
        """Generate large diff repo"""
        commits = []
        for i in range(6):
            commits.append({
                "type": "refactor" if i % 2 == 0 else "feat",
                "msg": f"feat: large change {i}",
                "diff_lines": 100 + i * 50
            })
        
        return {
            "commits": commits,
            "expected_enemies": 6,
        }
    
    @staticmethod
    def make_repo_elite_heavy() -> Dict:
        """Generate elite-heavy repo (merge/fix heavy)"""
        commits = [
            {"type": "merge", "msg": "merge: feature branch"},
            {"type": "merge", "msg": "merge: hotfix"},
            {"type": "fix", "msg": "fix: critical bug"},
            {"type": "merge", "msg": "merge: release"},
            {"type": "fix", "msg": "fix: another bug"},
            {"type": "merge", "msg": "merge: final"},
        ]
        
        return {
            "commits": commits,
            "expected_enemies": 6,
            "expected_elites": 4,
        }
    
    @staticmethod
    def make_repo_single() -> Dict:
        """Single commit repo"""
        return {
            "commits": [
                {"type": "feat", "msg": "feat: single feature"},
            ],
            "expected_enemies": 1,
        }
