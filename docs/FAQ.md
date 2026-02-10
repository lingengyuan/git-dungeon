# FAQ

## Where are save files stored?

Default save path:

- `~/.local/share/git-dungeon`

Override with environment variable:

```bash
export GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-saves
```

For tests/CI, always point it to a temporary writable directory.

## How do I make runs reproducible?

Use a fixed seed:

```bash
git-dungeon . --seed 42 --auto --compact
```

With the same repository state and seed, auto decisions and generated content stay deterministic.

## How do I enable or disable AI flavor text?

Disable AI (default-safe mode):

```bash
git-dungeon . --ai=off
```

Enable deterministic mock provider:

```bash
git-dungeon . --ai=on --ai-provider=mock
```

Enable remote providers:

```bash
git-dungeon . --ai=on --ai-provider=gemini
git-dungeon . --ai=on --ai-provider=openai
git-dungeon . --ai=on --ai-provider=copilot
# optional: override provider model id
git-dungeon . --ai=on --ai-provider=copilot --ai-model=openai/o4-mini
```

If rate limit is hit (for example HTTP 429), the system degrades to safe fallback text temporarily.

## Where can I find performance benchmarks?

See:

- `docs/perf.md`

It includes benchmark datasets, metric definitions, profiler commands, hotspot summary, and before/after optimization data.

## How do I enable content packs?

Use a pack path or built-in pack id:

```bash
git-dungeon . --content-pack content_packs/example_pack --seed 42 --auto --compact
git-dungeon . --content-pack debug_pack --seed 42 --auto --compact
```

You can also point `GIT_DUNGEON_CONTENT_DIR` to a folder of packs.
