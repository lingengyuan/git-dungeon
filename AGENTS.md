# AGENTS.md

This file provides guidance to coding agents when working with code in this repository.

## Project Principles (强制)

任何代码改动、设计决策、PR 都必须满足以下 7 条；冲突时以本节为准。

1. **第一性原理** — 遇到问题先回到本质：「这件事到底是什么？必须经过哪些环节？」再决定方案。不照搬既有抽象、不沿用「之前都是这么做的」。结论先标注「未验证」，再用实验/测试确认。
2. **DRY (Don't Repeat Yourself)** — 每个知识点（规则、配置、数据结构、文案）在系统中只能有一个权威来源。发现重复立即抽取，不允许「再写一个类似的」。
3. **正交性 (Orthogonality)** — 模块边界清晰、职责单一；依赖单向（高层 → 低层），不出现反向依赖；副作用显式化；避免全局状态。改一个模块不应连带改另一个。
4. **ETC (Easier to Change)** — 所有设计的终极判据：「明天需求变了，要改几处？」答案 > 2 处时，先重构再写功能。优先接口而非实现，避免为假想需求预留代码。
5. **禁止掩盖性质的 fallback** — fallback 只能用于「已知、可声明、不改变语义」的降级场景（如 AI provider 失败 → 模板文案、缓存命中 → 跳过远程调用）。**严禁**用 try/except 吞错误、用默认值掩盖配置缺失、用「兜底分支」掩盖未实现路径。错误必须可见、可定位、可追溯；不确定就抛出，不要静默。
6. **Phase 交接文档（强制）** — 每完成一个 phase（里程碑、独立 feature、重构阶段）必须在 `./handoffs/<YYYY-MM-DD>-<phase-id>-handoff.md` 写交接文档，包含：
   - **背景**：这个 phase 要解决什么问题、上游约束。
   - **目标**：原计划交付什么。
   - **当前进度**：已完成 / 进行中 / 未开始（按 checklist）。
   - **完成情况**：实际交付物、关键决策、偏离原计划的地方及原因。
   - **后续任务**：下一个 phase 需要做什么、已知风险、未决问题、需要新会话立刻读哪些文件。
   - 文档要让一个**没有当前会话上下文**的新 Claude 实例读完即可接手，不依赖口头说明。
7. **Phase 完成后必须提交并推送（强制）** — Phase 14B 到 Phase 18 必须按顺序完成；每完成一个 phase，先验证，再写 handoff，再提交，再推送到 GitHub，最后再进入下一个 phase。禁止把多个 phase 的交接、提交、推送混在一起。

## Session Bootstrap（新会话入口）

接手任务时按顺序读：

1. **本文件** — 项目原则与架构。
2. **`plans/README.md`** + **`plans/<topic>-phases.md`** — 找到当前所在 phase 与拆解索引。
3. **`handoffs/`** 下最新一份 — 拿到精确进度、未决问题、推荐验证命令。
4. 仅在以上三步无法回答问题时再读源代码。

当前活跃 plan：`plans/pixel-phases.md`（像素化改造，Phase 0-17 已完成；后续按 `plans/pixel-stardew-level-repair-plan.md` 从 Phase 18 接手）。

## Project Snapshot

`git-dungeon` is a Python ≥3.11 CLI roguelike that turns a repository's commit history into a deterministic battle run. The same `git-dungeon` console script ships two front-ends — plain CLI and AI-flavored CLI — that drive a shared pure-logic engine.

- Console entry: `git-dungeon` → `git_dungeon.main:main` (also `python -m git_dungeon`).
- `src/`-layout package: code lives in `src/git_dungeon/`; tests and benchmarks expect `PYTHONPATH=src`.

## Common Commands

The `Makefile` is the canonical interface. Use it instead of raw `pytest` so `PYTHONPATH=src` is set correctly.

```bash
make test          # unit/integration only: pytest -m "not functional and not golden and not slow"
make test-func     # ⭐ PR gate: tests/functional/
make test-golden   # ⭐ PR gate: tests/golden_test.py (snapshot regression)
make test-all      # everything
make test-m6       # AI-text functional suite

make lint          # ruff check + mypy (mypy is heavily relaxed in pyproject.toml)
make format        # ruff format

make build-wheel   # python -m build --wheel
make smoke-install # build wheel, install into .venv-smoke, run scripts/ci_smoke_demo.sh

make bench         # benchmarks/run.py against small+medium+large datasets
make perf-smoke    # small dataset, --perf-smoke (non-fatal regression check)
make ai-cache-clear  # delete .git_dungeon_cache/ai_text.sqlite
```

Single-test invocation (mind the path):

```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_combat.py::TestX::test_y -v
```

Update golden snapshots only when the change is intentional and explained in the PR:

```bash
make test-golden-update   # = pytest tests/golden_test.py --update-golden
```

## Pre-commit / Pre-push

`.pre-commit-config.yaml` runs ruff (+ format), `mypy --strict`, basic file hygiene, and a custom `tests/harness/check_test_structure.py`. The pre-push hook runs the unit-test slice via `.venv/bin/python` — keep a project venv at `.venv/` or push will fail.

```bash
make pre-commit-install   # installs both pre-commit and pre-push hooks
```

## Run the Game

```bash
git-dungeon . --seed 42 --auto --compact --print-metrics
git-dungeon . --content-pack content_packs/example_pack --seed 42 --auto
git-dungeon . --daily --daily-date 2026-02-06 --auto
git-dungeon . --ai=on --ai-provider=mock --auto       # CI-safe mock provider
```

Relevant env vars:

- `GIT_DUNGEON_SAVE_DIR` — overrides the default `~/.local/share/git-dungeon` save dir (use `/tmp/...` for CI).
- `GIT_DUNGEON_CONTENT_DIR` — directory whose subfolders are auto-discovered as packs and merged after CLI `--content-pack` entries (alphabetical order; later entries override earlier IDs).
- `GEMINI_API_KEY` / `OPENAI_API_KEY` / `GITHUB_TOKEN` (`GITHUB_MODELS_MODEL`) — only when `--ai-provider=gemini|openai|copilot`.

## Architecture

The codebase splits cleanly into a deterministic core engine, two thin CLI front-ends, an optional AI flavor layer, and a runtime content-pack loader.

### Front-end layer (`src/git_dungeon/`)

- `main.py` — argument parsing, logging setup, version resolution. Selects `main_cli.GitDungeonCLI` or `main_cli_ai.GitDungeonAICLI` based on `--ai`.
- `main_cli.py` / `main_cli_ai.py` — orchestrate a run: load repo → build chapters → drive `node_flow` → render via `engine/ui/cli_renderer.py` → emit `run_metrics.json`.
- `main_tui.py` + `ui/` — Textual TUI screens (combat / inventory). Optional path, not on the default `git-dungeon` invocation.

### Engine layer (`src/git_dungeon/engine/`) — pure logic, no I/O

- `engine.py` + `model.py` + `events.py` — action-in / `(state, events)`-out state machine. All randomness is injected via `rng.RNG` (`DefaultRNG(seed=…)`); never call `random.*` or `time.time()` directly — see "Determinism" below.
- `rules/` — composable rule modules: `combat_rules`, `progression_rules`, `economy_rules`, `equipment_rules`, `boss_rules`, `chapter_rules`, `difficulty`, `archetype`, `skill_rules`, `rewards`.
- `node_flow.py` + `route.py` — chapter graph (`battle/event/rest/shop/elite/boss`) and traversal.
- `auto_policy.py` — decision policy used by `--auto`.
- `daily.py` + `mutators.py` — `--daily`/`--daily-date`/`--mutator` seed and rule modifiers.
- `meta.py` + `achievements.py` — meta-progression (points, unlocks, profile) persisted to the save dir.
- `run_metrics.py`, `replay.py` — telemetry emitted to `--metrics-out` and replay scaffolding.

### Core domain (`src/git_dungeon/core/`)

- `git_parser.py` (+ `optimized_git_parser.py`, `ultrafast_git_parser.py`) — commit ingestion. The default parser path is the production one; alternates exist for benchmarking.
- `character.py`, `combat.py`, `inventory.py`, `skills.py`, `save_system.py`, `game_engine.py` — domain entities used by the engine and front-ends.
- `entity.py` + `component.py` + `system.py` + `optimized_components.py` — lightweight ECS scaffolding.
- `lua/` — Lua scripting hooks (via `lupa`).

### Content packs (`src/git_dungeon/content/` and `content_packs/`)

- `runtime_loader.py` + `loader.py` + `schema.py` + `packs.py` — strict YAML validation and deterministic merge (cards / relics / events / chapter_overrides).
- Defaults live in `src/git_dungeon/content/defaults/` (e.g. `chapters.yml`); shipped packs in `src/git_dungeon/content/packs/`; external example in `content_packs/example_pack/pack.yml`.
- Merge order: CLI `--content-pack` entries first (in argv order), then `GIT_DUNGEON_CONTENT_DIR` discoveries (alphabetical). Later wins on conflicting IDs. Conflicts and missing references are hard failures — see `tests/functional/test_m3_packs_func.py`.
- See `docs/CONTENT_PACKS.md` for the schema reference.

### AI text layer (`src/git_dungeon/ai/`) — fully optional

- `client_{mock,null,openai,gemini,copilot}.py` behind `client_base.py`. `mock` is deterministic and CI-safe; `null` disables generation.
- `cache.py` — sqlite cache at `.git_dungeon_cache/ai_text.sqlite`, keyed by provider/repo/seed/lang/kind plus a `content_version` hash of `prompts.py`/`fallbacks.py`/`sanitize.py` so template changes auto-invalidate.
- `sanitize.py` enforces length limits and Markdown stripping; `fallbacks.py` provides deterministic templates used on API failure or rate-limit cooldown.
- `integration.py` is the seam used by `main_cli_ai.py` to inject flavor at chapter intros, battle start/end, shop, and boss phases.
- Background and provider quirks (Gemini RPM budget, copilot model env): `docs/AI_TEXT.md`.

### i18n

`i18n/translations.py` and `i18n/zh_CN.py` back `--lang en|zh|zh_CN`. New user-facing strings should go through the translation layer rather than being hard-coded.

## Testing Architecture

The testing framework is a hard-enforced contract — see `docs/TESTING_FRAMEWORK.md` for the full version. Key invariants when writing or modifying tests:

- **Layers**: `tests/unit/`, `tests/integration/`, `tests/functional/`, `tests/golden/`. Functional + golden are PR gates; unit/integration are local fast-feedback.
- **Markers**: `functional`, `golden`, `slow`, `m3` are auto-applied by `tests/conftest.py` based on file path. `make test` excludes all three to stay fast.
- **Harness** (`tests/harness/`) is the only sanctioned way to compose scenarios:
  - `scenario.py` — `Scenario` (id/seed/repo_builder/config/steps/expect), `Runner`, `RepoFactory` (build minimal git repos in <1s).
  - `assertions.py` — structured assertions (range/tag/shape) instead of brittle ID equality.
  - `snapshots.py` — `stable_serialize` (sorts keys, sorts lists by id, strips temp paths/timestamps) plus golden compare/update.
- **Golden snapshots** live in `tests/golden/*.json`. Allowed: route kind sequences, first ~5 turns of battle (hand ids, energy, status stacks, intent), reward candidate ids, meta deltas. Forbidden: stdout dumps, AI prose, timestamps. Updates require a justification in the PR description.
- **Determinism rules (PR-blocking)**: never use global `random` or `time.time()`; route randomness through `git_dungeon.engine.rng.DefaultRNG(seed=…)`. Never hit network or external real repos — use `RepoFactory`.

## Conventions Worth Knowing

- The package uses an `src/`-layout. Prefer the Makefile or `python -m git_dungeon` over ad-hoc imports; if you must run pytest directly, prefix with `PYTHONPATH=src`.
- `pyproject.toml` ships a deliberately permissive mypy config (many error codes disabled, `disallow_untyped_defs = false`). Pre-commit, however, runs mypy in `--strict` mode on staged files — code added there must satisfy the stricter check.
- Commit messages follow Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`) per `CONTRIBUTING.md`. CI release flows in `.github/workflows/release.yml` consume version tags.
- Performance baselines and the `benchmarks/` harness are documented in `docs/perf.md`; treat regressions visible via `make perf-smoke` as worth investigating.
