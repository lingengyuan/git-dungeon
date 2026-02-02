#!/usr/bin/env python3
"""
Balance simulation tool for Git Dungeon.

Batch run auto-play simulations to collect statistics for balance tuning.
Only runs locally (not on CI), provides JSON output summary.
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from git_dungeon.engine.rules.difficulty import DifficultyLevel, get_difficulty
from git_dungeon.content.loader import load_content


class SimulationResult:
    """Result of a single simulation run."""
    
    def __init__(self, seed: int, character_id: str):
        self.seed = seed
        self.character_id = character_id
        self.success = False
        self.chapters_completed = 0
        self.enemies_killed = 0
        self.elites_killed = 0
        self.bosses_killed = 0
        self.turns_total = 0
        self.death_reason: Optional[str] = None
        self.final_hp = 0
        self.gold_earned = 0
        self.cards_obtained: List[str] = []
        self.relics_obtained: List[str] = []
        self.difficulty: str = "normal"


class BalanceSimulator:
    """Simulator for balance testing."""
    
    def __init__(self, content_path: str = "src/git_dungeon/content"):
        self.content = load_content(content_path)
        self.results: List[SimulationResult] = []
    
    def simulate_run(
        self,
        seed: int,
        character_id: str = "developer",
        difficulty: str = "normal",
        max_chapters: int = 3,
        auto_play: bool = True
    ) -> SimulationResult:
        """Run a single simulation.
        
        Args:
            seed: Random seed for reproducibility
            character_id: Character to use
            difficulty: Difficulty level (normal/hard)
            max_chapters: Maximum chapters to simulate
            auto_play: Whether to use auto-play mode
            
        Returns:
            SimulationResult with run statistics
        """
        result = SimulationResult(seed, character_id)
        result.difficulty = difficulty
        
        # Load content to get character stats
        from git_dungeon.content.loader import load_content
        content = load_content("src/git_dungeon/content")
        
        # Create game state
        from git_dungeon.engine.model import GameState
        from git_dungeon.engine.route import build_route, NodeKind
        
        state = GameState(seed=seed)
        state.difficulty = difficulty
        state.character_id = character_id
        
        # Initialize character stats
        char = content.characters[character_id]
        state.player.current_hp = char.stats.hp
        state.player.max_hp = char.stats.hp
        state.player.energy.max_energy = char.stats.energy
        state.player.energy.current_energy = char.stats.energy
        state.player.gold = 0
        
        # Initialize deck with starting cards
        for card_id in char.starter_cards:
            if card_id in content.cards:
                state.player.deck.draw_pile.append(content.cards[card_id])
        
        # Create mock commits
        class MockCommit:
            def __init__(self, i):
                self.hexsha = f"abc{i}"
        
        commits = [MockCommit(i) for i in range(50)]
        
        for chapter_idx in range(max_chapters):
            diff_params = get_difficulty(chapter_idx, DifficultyLevel(difficulty))
            
            # Build route
            route = build_route(commits, seed=seed + chapter_idx, chapter_index=chapter_idx, node_count=diff_params.node_count)
            state.chapter_route = route
            
            # Process nodes
            for node in route.nodes:
                if state.player.current_hp <= 0:
                    result.death_reason = "damage"
                    result.final_hp = 0
                    return result
                
                if node.kind == NodeKind.BATTLE:
                    result.enemies_killed += 1
                    
                    # Simplified combat - deal damage to enemy and receive damage
                    enemy_hp = 20 * diff_params.enemy_scaling.hp_multiplier
                    enemy_damage = 5 * diff_params.enemy_scaling.damage_multiplier
                    
                    # Auto combat simulation
                    turns = 0
                    max_combat_turns = 30
                    
                    while enemy_hp > 0 and turns < max_combat_turns and state.player.current_hp > 0:
                        turns += 1
                        result.turns_total += 1
                        
                        # Player deals damage
                        player_damage = 10  # Simplified
                        enemy_hp -= player_damage
                        
                        # Enemy attacks
                        if enemy_hp > 0:
                            damage_taken = max(0, int(enemy_damage))
                            state.player.current_hp -= damage_taken
                    
                    if turns >= max_combat_turns:
                        result.death_reason = "timeout"
                        return result
                
                elif node.kind == NodeKind.ELITE:
                    result.elites_killed += 1
                    # Elite combat (stronger)
                    elite_hp = 40 * diff_params.enemy_scaling.hp_multiplier
                    elite_damage = 8 * diff_params.enemy_scaling.damage_multiplier
                    
                    turns = 0
                    while elite_hp > 0 and turns < 40 and state.player.current_hp > 0:
                        turns += 1
                        player_damage = 10
                        elite_hp -= player_damage
                        if elite_hp > 0:
                            state.player.current_hp -= max(0, int(elite_damage))
                
                elif node.kind == NodeKind.BOSS:
                    result.bosses_killed += 1
                    # Boss combat (strongest)
                    boss_hp = 80 * diff_params.enemy_scaling.hp_multiplier
                    boss_damage = 12 * diff_params.enemy_scaling.damage_multiplier
                    
                    turns = 0
                    while boss_hp > 0 and turns < 50 and state.player.current_hp > 0:
                        turns += 1
                        player_damage = 12
                        boss_hp -= player_damage
                        if boss_hp > 0:
                            state.player.current_hp -= max(0, int(boss_damage))
            
            # Check if player survived chapter
            if state.player.current_hp <= 0:
                result.death_reason = f"chapter_{chapter_idx}"
                result.final_hp = 0
                return result
            
            result.chapters_completed = chapter_idx + 1
            result.final_hp = state.player.current_hp
        
        result.success = True
        result.final_hp = state.player.current_hp
        return result
    
    def batch_simulate(
        self,
        num_runs: int = 100,
        seeds_start: int = 42,
        characters: List[str] = None,
        difficulties: List[str] = None,
        max_chapters: int = 3
    ) -> List[SimulationResult]:
        """Run batch simulations.
        
        Args:
            num_runs: Number of runs per configuration
            seeds_start: Starting seed
            characters: Characters to test
            difficulties: Difficulties to test
            max_chapters: Maximum chapters per run
            
        Returns:
            List of SimulationResult
        """
        if characters is None:
            characters = ["developer", "reviewer", "devops"]
        if difficulties is None:
            difficulties = ["normal", "hard"]
        
        results = []
        
        for difficulty in difficulties:
            for char in characters:
                for i in range(num_runs):
                    seed = seeds_start + i
                    result = self.simulate_run(
                        seed=seed,
                        character_id=char,
                        difficulty=difficulty,
                        max_chapters=max_chapters
                    )
                    results.append(result)
        
        self.results = results
        return results
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics.
        
        Returns:
            Dictionary with summary statistics
        """
        if not self.results:
            return {"error": "No simulation results"}
        
        # Group by difficulty
        by_difficulty: Dict[str, List[SimulationResult]] = defaultdict(list)
        for r in self.results:
            by_difficulty[r.difficulty].append(r)
        
        summary = {
            "total_runs": len(self.results),
            "by_difficulty": {}
        }
        
        for difficulty, results in by_difficulty.items():
            diff_summary = {
                "runs": len(results),
                "successes": sum(1 for r in results if r.success),
                "success_rate": sum(1 for r in results if r.success) / len(results),
                "avg_chapters": sum(r.chapters_completed for r in results) / len(results),
                "avg_enemies_killed": sum(r.enemies_killed for r in results) / len(results),
                "death_reasons": Counter(r.death_reason for r in results if r.death_reason),
            }
            summary["by_difficulty"][difficulty] = diff_summary
        
        return summary


def main():
    """Main entry point for the simulation tool."""
    parser = argparse.ArgumentParser(
        description="Git Dungeon balance simulation tool"
    )
    parser.add_argument(
        "--runs", type=int, default=50,
        help="Number of runs per configuration (default: 50)"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Starting seed (default: 42)"
    )
    parser.add_argument(
        "--chapters", type=int, default=3,
        help="Maximum chapters per run (default: 3)"
    )
    parser.add_argument(
        "--output", type=str, default="simulation_results.json",
        help="Output JSON file (default: simulation_results.json)"
    )
    parser.add_argument(
        "--difficulty", type=str, default="normal",
        help="Difficulty level: normal, hard, or all (default: normal)"
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress console output"
    )
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("=" * 60)
        print("🎮 Git Dungeon Balance Simulator")
        print("=" * 60)
        print(f"  Runs per config: {args.runs}")
        print(f"  Max chapters: {args.chapters}")
        print(f"  Output: {args.output}")
        print("=" * 60)
    
    simulator = BalanceSimulator()
    
    # Determine difficulties to run
    if args.difficulty == "all":
        difficulties = ["normal", "hard"]
    else:
        difficulties = [args.difficulty]
    
    all_results = []
    for difficulty in difficulties:
        if not args.quiet:
            print(f"\n📊 Running {difficulty} difficulty...")
        
        results = simulator.batch_simulate(
            num_runs=args.runs,
            seeds_start=args.seed,
            difficulties=[difficulty],
            max_chapters=args.chapters
        )
        all_results.extend(results)
    
    # Generate and save summary
    summary = simulator.generate_summary()
    
    # Add individual results for detailed analysis
    summary["individual_results"] = [
        {
            "seed": r.seed,
            "character": r.character_id,
            "difficulty": r.difficulty,
            "success": r.success,
            "chapters": r.chapters_completed,
            "enemies": r.enemies_killed,
            "death_reason": r.death_reason,
        }
        for r in all_results
    ]
    
    # Save to JSON
    with open(args.output, "w") as f:
        json.dump(summary, f, indent=2)
    
    if not args.quiet:
        print("\n" + "=" * 60)
        print("📈 Summary")
        print("=" * 60)
        
        for diff, data in summary.get("by_difficulty", {}).items():
            print(f"\n{diff.upper()}:")
            print(f"  Success rate: {data['success_rate']*100:.1f}%")
            print(f"  Avg chapters: {data['avg_chapters']:.2f}")
            print(f"  Avg enemies: {data['avg_enemies_killed']:.1f}")
            
            if data['death_reasons']:
                print("  Top death reasons:")
                for reason, count in data['death_reasons'].most_common(3):
                    print(f"    - {reason}: {count}")
        
        print(f"\n💾 Results saved to: {args.output}")
        print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
