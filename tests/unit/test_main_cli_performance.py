"""Regression tests for CLI performance-sensitive paths."""

from __future__ import annotations

from types import SimpleNamespace

from git_dungeon.engine import GameState
from git_dungeon.main_cli import GitDungeonCLI


def test_get_current_commit_uses_cached_history() -> None:
    """`_get_current_commit` should load commit history once and then reuse cache."""
    cli = GitDungeonCLI(seed=5, auto_mode=True, compact=True)
    cli.state = GameState(seed=5, repo_path=".", total_commits=3, current_commit_index=0, difficulty="normal")

    commits = [
        SimpleNamespace(hexsha="a" * 40, message="feat: 1"),
        SimpleNamespace(hexsha="b" * 40, message="fix: 2"),
        SimpleNamespace(hexsha="c" * 40, message="docs: 3"),
    ]

    class DummyParser:
        def __init__(self) -> None:
            self.calls = 0

        def get_commit_history(self):
            self.calls += 1
            return commits

    dummy_parser = DummyParser()
    cli._parser = dummy_parser

    for idx in range(3):
        cli.state.current_commit_index = idx
        assert cli._get_current_commit() is commits[idx]

    assert dummy_parser.calls == 1

