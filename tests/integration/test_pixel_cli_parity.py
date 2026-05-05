"""Pixel headless metrics parity with CLI auto mode."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


PARITY_FIELDS = (
    "run_victory",
    "chapters_completed",
    "battles_total",
    "boss_battles_total",
    "battles_won",
    "total_exp_gained",
    "total_gold_gained",
    "node_type_counts",
)


def test_pixel_headless_auto_metrics_match_cli(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    cli_json = tmp_path / "cli.json"
    pixel_json = tmp_path / "pixel.json"
    env = {**os.environ, "PYTHONPATH": "src", "GIT_DUNGEON_SAVE_DIR": str(tmp_path / "save")}

    cli_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "git_dungeon",
            ".",
            "--seed",
            "42",
            "--auto",
            "--metrics-out",
            str(cli_json),
        ],
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
    )
    pixel_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "git_dungeon",
            ".",
            "--pixel",
            "--auto",
            "--headless",
            "--seed",
            "42",
            "--metrics-out",
            str(pixel_json),
        ],
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
    )

    assert cli_json.exists(), cli_result.stderr + cli_result.stdout
    assert pixel_json.exists(), pixel_result.stderr + pixel_result.stdout
    cli_metrics = json.loads(cli_json.read_text(encoding="utf-8"))
    pixel_metrics = json.loads(pixel_json.read_text(encoding="utf-8"))
    for field in PARITY_FIELDS:
        assert pixel_metrics[field] == cli_metrics[field], field

    compare = subprocess.run(
        [
            sys.executable,
            "scripts/compare_run_metrics.py",
            str(cli_json),
            str(pixel_json),
        ],
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
    )
    assert compare.returncode == 0, compare.stdout + compare.stderr
