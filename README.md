# Git Dungeon

[English](README.md) | [简体中文](README.zh-CN.md)

Turn Git commit history into a playable command-line roguelike.

## Current Version

- `1.2.0`
- Versioning strategy: [SemVer](https://semver.org/)
- Upgrade notes: see `CHANGELOG.md` (`1.2.0`)

## Quickstart (3 Steps)

1. Create and activate a clean virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install from wheel (recommended for release validation).

```bash
python -m pip install --upgrade pip build
python -m build --wheel
pip install dist/*.whl
```

3. Run a reproducible auto demo (compact output + metrics).

```bash
git-dungeon . --seed 42 --auto --compact --metrics-out ./run_metrics.json
```

## Common Options

- `--auto`: automatic combat decisions.
- `--compact`: concise battle logs.
- `--metrics-out <path>`: write run metrics JSON.
- `--print-metrics`: print metrics summary to stdout.
- `--seed <int>`: deterministic run seed.
- `--ai=off|on --ai-provider=mock|gemini|openai`: AI flavor text control.

## Save Directory

By default saves are written under `~/.local/share/git-dungeon`.
Override with:

```bash
export GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-saves
```

## Demo Commands

```bash
# Run current repository
git-dungeon . --auto

# Compact auto run with metrics summary
git-dungeon . --seed 42 --auto --compact --print-metrics

# Chinese UI
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
