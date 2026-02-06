"""Tests for compact combat output mode."""

from __future__ import annotations

from types import SimpleNamespace

from git_dungeon.engine import EnemyState, GameState
from git_dungeon.main_cli import GitDungeonCLI


def test_compact_output_has_stable_turn_summary_and_key_events(capsys) -> None:
    """Compact mode should emit deterministic one-line turn summaries."""
    cli = GitDungeonCLI(seed=7, auto_mode=True, compact=True)
    cli.state = GameState(seed=7, repo_path=".", total_commits=1, current_commit_index=0, difficulty="normal")

    enemy = EnemyState(
        entity_id="enemy_0",
        name="Smoke Bug",
        enemy_type="bug",
        commit_hash="abc1234",
        commit_message="fix: smoke test",
        current_hp=20,
        max_hp=20,
        attack=6,
        defense=0,
        exp_reward=8,
        gold_reward=4,
        is_boss=False,
    )
    chapter = SimpleNamespace(
        name="Test Chapter",
        is_boss_chapter=False,
        config=SimpleNamespace(shop_enabled=False),
    )

    cli.combat_rules.roll_critical = lambda _chance, multiplier: (True, multiplier)

    result = cli._combat(enemy, chapter)
    out = capsys.readouterr().out
    summary_lines = [line.strip() for line in out.splitlines() if line.strip().startswith("T")]

    assert result is True
    assert "✨[KILL] Smoke Bug defeated" in out
    assert summary_lines == ["T01 action=skill dealt=60 taken=0 hp=100/100 enemy=0/20 [CRIT] [KILL]"]

