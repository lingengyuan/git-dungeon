# Git Dungeon

[English](README.md) | [简体中文](README.zh-CN.md)

Turn Git commit history into a playable command-line roguelike.

## What This Project Is

`Git Dungeon` maps repository history into a battle run:

- Each commit becomes an enemy encounter.
- Commit types (`feat`, `fix`, `docs`, `merge`) shape chapter flavor and pacing.
- You gain EXP and gold, level up, and progress chapter by chapter.
- Optional AI text adds narrative flavor while keeping deterministic fallback behavior.

This project is useful for:

- Exploring repository history in a game-like way.
- Demoing deterministic game systems in Python CLI.
- Serving as a reference for test-first roguelike architecture.

## Gameplay Loop

1. Parse repository commits.
2. Build chapters and enemies.
3. Fight battles (manual or `--auto` policy).
4. Collect rewards and advance until clear or defeat.

## Example Output (No AI)

```text
Loading repository...
Loaded 248 commits!
Divided into 20 chapters:
  🔄 Chapter 0: Genesis of Chaos (initial)
  ⏳ Chapter 1: Fixing Era (fix)

⚔️  Genesis of Chaos: fix bug [compact]
T01 action=attack dealt=14 taken=3 hp=97/100 enemy=6/20
T02 action=skill dealt=9 taken=0 hp=97/100 enemy=0/20 [KILL]
   ✨[KILL] fix bug defeated
📊 Metrics written: ./run_metrics.json
```

If you run with `--lang zh_CN`, chapter names and UI text are shown in Chinese.

## Example Output (AI On)

```text
[AI] enabled provider=mock
🧠 A fix-typed enemy appears, carrying unstable energy.
🧠 Battle starts. Prepare your next action.
⚔️  Genesis of Chaos: fix parser bug
T01 action=skill dealt=16 taken=0 hp=100/100 enemy=4/20 [CRIT]
...
```

## Current Version

- `1.2.0`
- Versioning strategy: [SemVer](https://semver.org/)
- Upgrade notes: `CHANGELOG.md`

## Quickstart (3 Steps)

1. Create and activate a clean virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install from wheel.

```bash
python -m pip install --upgrade pip build
python -m build --wheel
pip install dist/*.whl
```

3. Run a reproducible demo.

```bash
git-dungeon . --seed 42 --auto --compact --metrics-out ./run_metrics.json
```

Start here for a 1-minute first run:

```bash
git-dungeon . --seed 42 --auto --compact --print-metrics
```

## Common Options

- `--auto`: automatic combat decisions.
- `--compact`: concise per-turn battle summary.
- `--metrics-out <path>`: write metrics JSON.
- `--print-metrics`: print run summary.
- `--seed <int>`: deterministic run seed.
- `--ai=off|on --ai-provider=mock|gemini|openai`: AI flavor text control.

## AI Flavor Text (Optional)

Enable AI text with deterministic mock provider:

```bash
git-dungeon . --ai=on --ai-provider=mock --auto --compact
```

Enable Gemini:

```bash
export GEMINI_API_KEY="your-key"
git-dungeon . --ai=on --ai-provider=gemini --lang zh_CN
```

Enable OpenAI:

```bash
export OPENAI_API_KEY="your-key"
git-dungeon . --ai=on --ai-provider=openai --lang zh_CN
```

Example AI lines:

```text
[AI] enabled provider=mock
🧠 A fix-typed enemy appears, carrying unstable energy.
🧠 Battle starts. Prepare your next action.
⚔️  Genesis of Chaos: fix parser bug
...
```

`mock` is CI-safe and reproducible. If remote providers hit rate limits, runtime falls back safely.
Details: `docs/AI_TEXT.md`.

## Save Directory

Default:

- `~/.local/share/git-dungeon`

Override:

```bash
export GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-saves
```

## Demo Commands

```bash
git-dungeon . --auto
git-dungeon . --seed 42 --auto --compact --print-metrics
git-dungeon . --auto --lang zh_CN
```

## Development

```bash
make lint
make test
make test-func
make test-golden
make build-wheel
make smoke-install
```

## Docs

- `CHANGELOG.md`
- `docs/FAQ.md`
- `docs/perf.md`
- `docs/AI_TEXT.md`
- `docs/TESTING_FRAMEWORK.md`

## License

MIT (`LICENSE`)
