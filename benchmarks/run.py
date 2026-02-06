"""Benchmark entrypoint for Git Dungeon performance baselines."""

from __future__ import annotations

import argparse
import cProfile
import io
import json
import pstats
import tracemalloc
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from git_dungeon.config import GameConfig
from git_dungeon.core.git_parser import GitParser
from git_dungeon.engine import GameState
from git_dungeon.main_cli import GitDungeonCLI

from .repo_factory import SyntheticRepoSpec, count_commits, ensure_synthetic_repo


@dataclass(frozen=True)
class DatasetSpec:
    """Benchmark dataset descriptor."""

    name: str
    kind: str
    repo_path: Path
    commit_target: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run reproducible Git Dungeon benchmarks.")
    parser.add_argument(
        "--dataset",
        choices=["small", "medium", "large", "all"],
        default="all",
        help="Dataset size to benchmark.",
    )
    parser.add_argument("--seed", type=int, default=2026, help="Deterministic seed for benchmark run.")
    parser.add_argument(
        "--iterations",
        type=int,
        default=3,
        help="Iterations per dataset (median is reported).",
    )
    parser.add_argument(
        "--commit-fetch-samples",
        type=int,
        default=40,
        help="How many _get_current_commit calls to profile in loop metric.",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path(".git_dungeon_cache/bench_repos"),
        help="Cache directory for generated synthetic repositories.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("benchmarks/output/benchmark_results.json"),
        help="Path to write benchmark JSON output.",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Collect cProfile data for the selected dataset.",
    )
    parser.add_argument(
        "--profile-output",
        type=Path,
        default=Path("benchmarks/output/profile_latest.pstats"),
        help="Where to write .pstats (typically gitignored).",
    )
    parser.add_argument(
        "--profile-top",
        type=int,
        default=10,
        help="How many top cProfile entries to include in summary.",
    )
    parser.add_argument(
        "--perf-smoke",
        action="store_true",
        help="Print soft regression warnings for small dataset.",
    )
    parser.add_argument(
        "--fail-on-regression",
        action="store_true",
        help="Exit non-zero when perf-smoke detects a regression.",
    )
    parser.add_argument(
        "--smoke-baseline",
        type=Path,
        default=Path("benchmarks/baselines/small_baseline.json"),
        help="Baseline JSON used by perf-smoke.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset_specs = resolve_datasets(args.dataset, args.cache_dir)
    results: list[dict[str, Any]] = []

    for spec in dataset_specs:
        result = benchmark_dataset(
            spec=spec,
            seed=args.seed,
            iterations=args.iterations,
            commit_fetch_samples=args.commit_fetch_samples,
        )
        results.append(result)

    profile_summary: dict[str, Any] | None = None
    if args.profile:
        profile_summary = run_profile(
            spec=dataset_specs[0],
            seed=args.seed,
            output_path=args.profile_output,
            top_n=args.profile_top,
            commit_fetch_samples=args.commit_fetch_samples,
        )

    payload = {
        "schema_version": "m2_benchmark_v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "python_version": _python_version(),
        "platform": _platform_summary(),
        "iterations": args.iterations,
        "results": results,
    }
    if profile_summary is not None:
        payload["profile"] = profile_summary

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print_human_summary(payload)
    print(f"\nWrote JSON: {args.output_json}")

    if args.perf_smoke:
        ok = run_perf_smoke(payload, args.smoke_baseline)
        if not ok and args.fail_on_regression:
            return 2

    return 0


def resolve_datasets(requested: str, cache_dir: Path) -> list[DatasetSpec]:
    repo_root = Path(__file__).resolve().parent.parent
    cache_dir.mkdir(parents=True, exist_ok=True)

    all_specs = {
        "small": DatasetSpec(
            name="small",
            kind="existing",
            repo_path=repo_root,
            commit_target=0,
        ),
        "medium": DatasetSpec(
            name="medium",
            kind="synthetic",
            repo_path=ensure_synthetic_repo(
                cache_dir, "synthetic_medium", SyntheticRepoSpec(commit_count=1000)
            ),
            commit_target=1000,
        ),
        "large": DatasetSpec(
            name="large",
            kind="synthetic",
            repo_path=ensure_synthetic_repo(
                cache_dir, "synthetic_large", SyntheticRepoSpec(commit_count=5000)
            ),
            commit_target=5000,
        ),
    }

    if requested == "all":
        return [all_specs["small"], all_specs["medium"], all_specs["large"]]
    return [all_specs[requested]]


def benchmark_dataset(
    spec: DatasetSpec, seed: int, iterations: int, commit_fetch_samples: int
) -> dict[str, Any]:
    samples = []
    for _ in range(iterations):
        sample = _benchmark_once(spec.repo_path, seed=seed, commit_fetch_samples=commit_fetch_samples)
        samples.append(sample)

    med = median_sample(samples)
    repo_commit_count = count_commits(spec.repo_path)
    med.update(
        {
            "dataset": spec.name,
            "dataset_kind": spec.kind,
            "repo_path": str(spec.repo_path),
            "commit_count": repo_commit_count,
            "commit_target": spec.commit_target,
        }
    )
    med["samples"] = samples
    return med


def _benchmark_once(repo_path: Path, seed: int, commit_fetch_samples: int) -> dict[str, float]:
    tracemalloc.start()
    start_total = perf_counter()

    cli = GitDungeonCLI(seed=seed, auto_mode=True, compact=True)
    parser = GitParser(GameConfig())

    parse_start = perf_counter()
    parser.load_repository(str(repo_path))
    commits = parser.get_commit_history()
    parse_duration = perf_counter() - parse_start

    chapter_start = perf_counter()
    cli.chapter_system.parse_chapters(commits)
    chapter = cli.chapter_system.get_current_chapter()
    chapter_duration = perf_counter() - chapter_start

    state_start = perf_counter()
    cli.state = GameState(
        seed=seed,
        repo_path=str(repo_path),
        total_commits=len(commits),
        current_commit_index=0,
        difficulty="normal",
    )
    cli._parser = parser
    first_enemy_ready = 0.0
    if commits and chapter:
        enemy_start = perf_counter()
        _ = cli._create_enemy(commits[0])
        first_enemy_ready = perf_counter() - enemy_start
    state_duration = perf_counter() - state_start

    fetch_start = perf_counter()
    max_samples = min(len(commits), commit_fetch_samples)
    for index in range(max_samples):
        cli.state.current_commit_index = index
        _ = cli._get_current_commit()
    commit_fetch_loop_duration = perf_counter() - fetch_start

    startup_total = perf_counter() - start_total
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "startup_total_s": round(startup_total, 6),
        "git_parse_s": round(parse_duration, 6),
        "chapter_build_s": round(chapter_duration, 6),
        "state_init_s": round(state_duration, 6),
        "first_enemy_generation_s": round(first_enemy_ready, 6),
        "commit_fetch_loop_s": round(commit_fetch_loop_duration, 6),
        "peak_memory_mb": round(peak_bytes / (1024 * 1024), 3),
    }


def run_profile(
    spec: DatasetSpec, seed: int, output_path: Path, top_n: int, commit_fetch_samples: int
) -> dict[str, Any]:
    profiler = cProfile.Profile()
    profiler.enable()
    _benchmark_once(spec.repo_path, seed=seed, commit_fetch_samples=commit_fetch_samples)
    profiler.disable()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    profiler.dump_stats(str(output_path))

    stats_stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stats_stream).sort_stats("cumtime")
    stats.print_stats(top_n)

    top_entries = []
    for (filename, line, func_name), stat in list(stats.stats.items()):
        cc, nc, tt, ct, _callers = stat
        top_entries.append(
            {
                "file": filename,
                "line": line,
                "function": func_name,
                "primitive_calls": cc,
                "total_calls": nc,
                "total_time_s": round(tt, 6),
                "cumulative_time_s": round(ct, 6),
            }
        )
    top_entries.sort(key=lambda item: item["cumulative_time_s"], reverse=True)
    return {
        "dataset": spec.name,
        "pstats_path": str(output_path),
        "top_entries": top_entries[:top_n],
        "text_top": stats_stream.getvalue(),
    }


def run_perf_smoke(payload: dict[str, Any], baseline_path: Path) -> bool:
    result_by_dataset = {item["dataset"]: item for item in payload["results"]}
    small = result_by_dataset.get("small")
    if small is None:
        print("perf-smoke: skipped (small dataset not present)")
        return True

    if not baseline_path.exists():
        print(f"perf-smoke: no baseline file at {baseline_path}, skipping comparison")
        return True

    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    checks = [
        ("startup_total_s", 3.0),
        ("git_parse_s", 3.0),
        ("chapter_build_s", 3.0),
        ("commit_fetch_loop_s", 2.5),
        ("peak_memory_mb", 2.0),
    ]
    ok = True
    for metric, threshold in checks:
        current = float(small.get(metric, 0.0))
        reference = float(baseline.get(metric, 0.0))
        if reference <= 0:
            continue
        ratio = current / reference
        if ratio > threshold:
            ok = False
            print(
                f"perf-smoke warning: {metric} regressed {ratio:.2f}x "
                f"(current={current:.4f}, baseline={reference:.4f})"
            )
    if ok:
        print("perf-smoke: OK (no major regression detected)")
    return ok


def print_human_summary(payload: dict[str, Any]) -> None:
    print("\nGit Dungeon Benchmark Summary")
    print("=" * 72)
    print(f"Platform: {payload['platform']}")
    print(f"Python:   {payload['python_version']}")
    print()
    print(
        "dataset   commits  startup(s)  parse(s)  chapter(s)  fetch-loop(s)  peak-mem(MB)"
    )
    print("-" * 72)
    for result in payload["results"]:
        print(
            f"{result['dataset']:<8} {result['commit_count']:>7}  "
            f"{result['startup_total_s']:>9.4f}  {result['git_parse_s']:>7.4f}  "
            f"{result['chapter_build_s']:>10.4f}  {result['commit_fetch_loop_s']:>13.4f}  "
            f"{result['peak_memory_mb']:>12.3f}"
        )


def median_sample(samples: list[dict[str, float]]) -> dict[str, float]:
    if len(samples) == 1:
        return dict(samples[0])
    sorted_samples = sorted(samples, key=lambda item: item["startup_total_s"])
    return dict(sorted_samples[len(sorted_samples) // 2])


def _python_version() -> str:
    import platform

    return platform.python_version()


def _platform_summary() -> str:
    import platform

    return f"{platform.system()} {platform.release()} ({platform.machine()})"


if __name__ == "__main__":
    raise SystemExit(main())
