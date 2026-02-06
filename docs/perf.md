# Performance Baseline (M2)

## Scope

This document defines reproducible performance measurement for `git-dungeon` and records:

1. Baseline benchmark numbers (small/medium/large datasets)
2. Profiler evidence (`cProfile`)
3. One data-driven hotspot optimization with before/after comparison

All commands below are local/offline and do not require network access.

## Environment

- Date: 2026-02-06
- OS: Linux 6.8.0-71-generic (`x86_64`)
- Python: 3.12.3

## Benchmark Entry

Primary entrypoint:

```bash
PYTHONPATH=src python -m benchmarks.run --dataset all --iterations 2 \
  --output-json benchmarks/output/benchmark_results.json
```

Convenience targets:

```bash
make bench
make perf-smoke
```

## Datasets

- `small`: current repository (`/root/projects/git-dungeon`)
- `medium`: synthetic local repo, 1,000 commits
- `large`: synthetic local repo, 5,000 commits

Synthetic repos are generated deterministically in `.git_dungeon_cache/bench_repos/` by `benchmarks/repo_factory.py` (git fast-import).

## Metrics Definition

- `startup_total_s`: from CLI object setup + git load + commit parse + chapter parse + state init + first enemy generation
- `git_parse_s`: `GitParser.load_repository` + `GitParser.get_commit_history`
- `chapter_build_s`: `ChapterSystem.parse_chapters`
- `first_enemy_generation_s`: first `_create_enemy(...)` call
- `commit_fetch_loop_s`: repeated `_get_current_commit` fetch loop (`--commit-fetch-samples`)
- `peak_memory_mb`: peak memory during benchmark section (`tracemalloc`)

## Baseline (After M2 Optimization)

| dataset | commits | startup_total_s | git_parse_s | chapter_build_s | commit_fetch_loop_s | peak_memory_mb |
|---|---:|---:|---:|---:|---:|---:|
| small | 266 | 0.1443 | 0.0679 | 0.0014 | 0.0741 | 0.670 |
| medium | 1000 | 0.4797 | 0.2259 | 0.0073 | 0.2460 | 2.280 |
| large | 5000 | 2.4065 | 1.1326 | 0.0455 | 1.2071 | 10.918 |

Raw JSON example: `benchmarks/output/benchmark_results.json` (ignored by git).

## Profiler Evidence

### Command

```bash
PYTHONPATH=src python -m benchmarks.run --dataset medium --iterations 1 \
  --profile --profile-output benchmarks/output/profile_after_medium.pstats \
  --output-json benchmarks/output/profile_after_medium.json
```

Inspect with:

```bash
python -m pstats benchmarks/output/profile_after_medium.pstats
# then inside pstats shell:
# sort cumtime
# stats 20
```

### Top10 Hotspots (before optimization)

Captured with:

```bash
PYTHONPATH=src python -m benchmarks.run --dataset medium --iterations 1 \
  --profile --profile-output benchmarks/output/profile_before_medium.pstats \
  --output-json benchmarks/output/profile_before_medium.json
```

Top10 (by cumulative time):

1. `benchmarks/run.py:_benchmark_once` (18.898s)
2. `src/git_dungeon/core/git_parser.py:get_commit_history` (18.541s)
3. `src/git_dungeon/main_cli.py:_get_current_commit` (18.287s)
4. `src/git_dungeon/core/git_parser.py:_parse_commit_fast` (16.746s)
5. `gitdb/util.py:__getattr__` (14.014s)
6. `git/objects/commit.py:_set_cache_` (13.878s)
7. `git/objects/commit.py:_deserialize` (8.252s)
8. `git/db.py:stream` (4.872s)
9. `git/cmd.py:stream_object_data` (4.317s)
10. `git/cmd.py:__get_object_header` (3.608s)

Observation:

- The main hotspot was repeated `get_commit_history()` calls from `GitDungeonCLI._get_current_commit`.
- This caused repeated parsing of the same commit list inside combat progression.

After optimization (`profile_after_medium.pstats`), cumulative time dropped from ~18.9s to ~0.94s for the same profiler scenario, and `_get_current_commit` cumulative time dropped to ~0.45s.

## Optimization Implemented (Data-driven)

### Optimized hotspot

- File: `src/git_dungeon/main_cli.py`
- Change:
  - Cache commit history once at startup (`self._commits_cache = commits`)
  - Reuse cache in `_get_current_commit` instead of calling `self._parser.get_commit_history()` every fetch

### Before/After Comparison (same benchmark command)

Command:

```bash
PYTHONPATH=src python -m benchmarks.run --dataset all --iterations 2 \
  --commit-fetch-samples 40 --output-json <file>.json
```

| dataset | metric | before | after | speedup |
|---|---|---:|---:|---:|
| small | startup_total_s | 3.0202 | 0.1443 | 20.93x |
| small | commit_fetch_loop_s | 2.9305 | 0.0741 | 39.53x |
| medium | startup_total_s | 9.9943 | 0.4797 | 20.83x |
| medium | commit_fetch_loop_s | 9.7312 | 0.2460 | 39.55x |
| large | startup_total_s | 50.7262 | 2.4065 | 21.08x |
| large | commit_fetch_loop_s | 49.5183 | 1.2071 | 41.02x |

### Correctness guard

Added regression test:

- `tests/unit/test_main_cli_performance.py::test_get_current_commit_uses_cached_history`

This ensures repeated `_get_current_commit` calls only trigger one history load.

## Perf Smoke for CI

Small dataset smoke check:

```bash
PYTHONPATH=src python -m benchmarks.run --dataset small --iterations 2 \
  --output-json benchmarks/output/perf_smoke.json --perf-smoke
```

- Baseline file: `benchmarks/baselines/small_baseline.json`
- Behavior:
  - prints warning when key metrics exceed soft regression ratio
  - default does not fail hard (CI-friendly)
  - supports `--fail-on-regression` for strict mode
