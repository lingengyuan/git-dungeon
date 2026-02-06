# Git Dungeon

[English](README.md) | [简体中文](README.zh-CN.md)

Turn Git commit history into a playable command-line roguelike.

## What This Project Does

`Git Dungeon` maps repository commits into chapters and enemies:

- Each commit becomes one battle enemy.
- Commit types (`feat`, `fix`, `merge`) affect enemy flavor and chapter pacing.
- You gain EXP and gold from battles, then progress chapter by chapter.
- Optional M6 AI flavor text adds dynamic narration for intros, battle lines, events, and boss phases.

Use cases:

- Explore project history in a game-like way.
- Experiment with CLI architecture, rules engines, and YAML-driven content.
- Reference a tested Python CLI game project structure.

## Current Status

- Core gameplay is complete: parse repo, chapter progression, combat, rewards.
- Content system is active: built-in YAML + extension packs.
- Test layers are stable: unit, functional, golden.
- M6 AI text is integrated and production-safe (fallback + caching + rate-limit guard).

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Quick Start

```bash
# Play current repository
python -m git_dungeon.main .

# Auto battle + Chinese UI (supports zh alias)
python -m git_dungeon.main . --auto --lang zh_CN
# or
python -m git_dungeon.main . --auto --lang zh

# Auto battle with compact logs + metrics
python -m git_dungeon.main . --auto --compact --metrics-out ./run_metrics.json
python -m git_dungeon.main . --auto --compact --print-metrics

# Installed command
git-dungeon . --auto
```

## Gameplay Output Example (No AI)

```text
Loading repository...
Loaded 248 commits!
Divided into 20 chapters:
  🔄 Chapter 0: 混沌初开 (initial)
  ⏳ Chapter 1: 修复时代 (fix)

📖 第 1 章：混沌初开
⚔️  混沌初开: fix bug
👤 DEVELOPER (Lv.1)          👾 fix bug
⚔️  You attack fix bug for 14 damage!
💀 fix bug defeated!
⭐ +19 EXP  |  💰 +9 Gold
```

## AI Flavor Text (Optional)

```bash
# Deterministic CI-friendly mode
python -m git_dungeon.main . --ai=on --ai-provider=mock

# Gemini
export GEMINI_API_KEY="your-key"
python -m git_dungeon.main . --ai=on --ai-provider=gemini --lang zh_CN

# OpenAI
export OPENAI_API_KEY="your-key"
python -m git_dungeon.main . --ai=on --ai-provider=openai --lang zh_CN
```

AI output example:

```text
[AI] enabled provider=gemini
[AI] prefetch auto-adjusted: chapter -> off (gemini free-tier safety)
🧠 A fix approaches, its aura pulsing with mysterious energy.
🧠 The battle begins! fix prepares its power surge...
⚔️  修复时代: fix unit test bug
...
[AI] Gemini rate limit: HTTP Error 429: Too Many Requests. Falling back to mock for ~60s
🧠 You enter a quantum realm, pulsating.
```

If `🧠` lines do not appear:

- Confirm `--ai=on` is present.
- For Chinese output, pass `--lang zh_CN` (or `--lang zh`).
- Clear old cache first with `make ai-cache-clear`.

Gemini behavior:

- Prefetch auto-adjusts to `off` for free-tier safety.
- On HTTP 429, client enters cooldown and falls back to mock text temporarily.
- Tunable by env vars: `GEMINI_MAX_RPM` (default `8`), `GEMINI_RATE_LIMIT_COOLDOWN` (default `60`).

## Development and Tests

```bash
make lint
make test
make test-func
make test-golden
```

## Project Layout

```text
src/git_dungeon/     # application code
tests/               # unit / functional / golden / integration
docs/                # active docs
Makefile             # common commands
```

## Docs

- `docs/AI_TEXT.md`
- `docs/TESTING_FRAMEWORK.md`

## License

MIT (`LICENSE`)
