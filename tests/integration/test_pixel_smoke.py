"""Headless smoke tests for pixel mode."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_pixel_ui_smoke_creates_settings(tmp_path: Path) -> None:
    save_dir = tmp_path / "save"
    env = {
        **os.environ,
        "PYTHONPATH": "src",
        "SDL_VIDEODRIVER": "dummy",
        "SDL_AUDIODRIVER": "dummy",
        "GIT_DUNGEON_SAVE_DIR": str(save_dir),
    }

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "git_dungeon",
            ".",
            "--pixel",
            "--seed",
            "42",
            "--lang",
            "zh_CN",
            "--pixel-smoke-frames",
            "8",
        ],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    settings = save_dir / "settings.toml"
    assert settings.exists()
    assert 'lang = "zh_CN"' in settings.read_text(encoding="utf-8")


def test_pixel_missing_assets_show_startup_error(tmp_path: Path) -> None:
    env = {
        **os.environ,
        "PYTHONPATH": "src",
        "SDL_VIDEODRIVER": "dummy",
        "SDL_AUDIODRIVER": "dummy",
        "GIT_DUNGEON_ASSET_DIR": str(tmp_path / "missing-assets"),
        "GIT_DUNGEON_SAVE_DIR": str(tmp_path / "save"),
    }

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "git_dungeon",
            ".",
            "--pixel",
            "--seed",
            "42",
            "--pixel-smoke-frames",
            "2",
        ],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr + result.stdout
