"""CLI regression tests against real module entrypoints."""

import os
import subprocess
import sys
from pathlib import Path


def _run_module(module: str, *args: str) -> subprocess.CompletedProcess:
    repo_root = Path(__file__).resolve().parent.parent
    src_dir = repo_root / "src"
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{src_dir}{os.pathsep}{env.get('PYTHONPATH', '')}"

    return subprocess.run(
        [sys.executable, "-m", module, *args],
        capture_output=True,
        text=True,
        env=env,
    )


def test_package_module_entrypoint_help():
    """`python -m git_dungeon` should be executable."""
    result = _run_module("git_dungeon", "--help")
    assert result.returncode == 0, result.stderr
    assert "Git Dungeon" in result.stdout


def test_help_includes_ai_arguments():
    """Main parser should expose AI flags."""
    result = _run_module("git_dungeon.main", "--help")
    assert result.returncode == 0, result.stderr
    assert "--ai-provider" in result.stdout
    assert "--ai-model" in result.stdout
    assert "copilot" in result.stdout
    assert "--ai-cache" in result.stdout
    assert "--compact" in result.stdout
    assert "--metrics-out" in result.stdout
    assert "--content-pack" in result.stdout
    assert "--daily" in result.stdout
    assert "--mutator" in result.stdout


def test_invalid_lang_is_rejected():
    """Invalid language must fail in the real parser."""
    result = _run_module("git_dungeon.main", "--lang", "invalid")
    assert result.returncode != 0
    assert "invalid choice" in result.stderr


def test_ai_args_are_parsed_by_real_cli():
    """AI flags should not trigger argparse unknown-argument errors."""
    result = _run_module(
        "git_dungeon.main",
        "/definitely/missing/repo",
        "--ai=on",
        "--ai-provider=mock",
        "--ai-model=gemini-2.0-flash",
    )
    assert result.returncode == 1
    combined = f"{result.stdout}\n{result.stderr}"
    assert "unrecognized arguments" not in combined


def test_content_pack_daily_and_mutator_args_are_parsed() -> None:
    result = _run_module(
        "git_dungeon.main",
        "/definitely/missing/repo",
        "--content-pack",
        "content_packs/example_pack",
        "--daily",
        "--daily-date",
        "2026-02-06",
        "--mutator",
        "hard",
    )
    assert result.returncode == 1
    combined = f"{result.stdout}\n{result.stderr}"
    assert "unrecognized arguments" not in combined
