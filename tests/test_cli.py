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
    assert "--ai-cache" in result.stdout


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
    )
    assert result.returncode == 1
    combined = f"{result.stdout}\n{result.stderr}"
    assert "unrecognized arguments" not in combined
