"""Unit tests for benchmark tooling."""

from pathlib import Path

from benchmarks.repo_factory import SyntheticRepoSpec, count_commits, ensure_synthetic_repo
from benchmarks.run import _benchmark_once


def test_ensure_synthetic_repo_creates_expected_commit_count(tmp_path) -> None:
    repo = ensure_synthetic_repo(
        base_dir=tmp_path,
        name="synthetic_tiny",
        spec=SyntheticRepoSpec(commit_count=25, file_count=8, seed=99),
    )
    assert repo.exists()
    assert (repo / ".git").exists()
    assert count_commits(repo) == 25


def test_benchmark_once_returns_required_metrics(tmp_path) -> None:
    repo = ensure_synthetic_repo(
        base_dir=tmp_path,
        name="synthetic_bench",
        spec=SyntheticRepoSpec(commit_count=30, file_count=10, seed=7),
    )
    result = _benchmark_once(Path(repo), seed=7, commit_fetch_samples=8)
    required = {
        "startup_total_s",
        "git_parse_s",
        "chapter_build_s",
        "state_init_s",
        "first_enemy_generation_s",
        "commit_fetch_loop_s",
        "peak_memory_mb",
    }
    assert required.issubset(result.keys())
    assert result["startup_total_s"] >= 0.0
    assert result["peak_memory_mb"] > 0.0

