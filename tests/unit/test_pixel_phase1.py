"""Phase 1 smoke tests for the pixel UI shell."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from git_dungeon.ui_pixel.game_runner import GameRunner


def _make_git_repo(path: Path) -> Path:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "pixel@example.com"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Pixel Tester"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    for idx, message in enumerate(["feat: initial pixel shell", "fix: loading state"], start=1):
        (path / f"file_{idx}.txt").write_text(f"{message}\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", message], cwd=path, check=True, capture_output=True)
    return path


def test_game_runner_loads_repository_without_cli_io(tmp_path: Path) -> None:
    repo = _make_git_repo(tmp_path)
    runner = GameRunner(str(repo), seed=42, lang="en")

    summary = runner.load_repository()

    assert summary.total_commits == 2
    assert summary.chapter_count >= 1
    assert summary.seed == 42
    assert runner.loaded is True


def test_pixel_app_smoke_exits_under_dummy_video(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("pygame")
    repo = _make_git_repo(tmp_path)
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")

    from git_dungeon.ui_pixel.app import run

    assert run(str(repo), seed=42, smoke_frames=3) == 0
