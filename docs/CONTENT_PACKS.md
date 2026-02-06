# Content Packs

`Git Dungeon` supports runtime content packs for extending cards, relics, events, and chapter tuning.

## Quick Usage

Load one pack directory:

```bash
git-dungeon . --content-pack content_packs/example_pack --seed 42 --auto --compact
```

Load by built-in pack id:

```bash
git-dungeon . --content-pack debug_pack --seed 42 --auto --compact
```

Load packs from environment directory:

```bash
export GIT_DUNGEON_CONTENT_DIR=./content_packs
git-dungeon . --content-pack example_pack --seed 42 --auto --compact
```

## Directory Layout

Each pack is one directory containing `pack.yml` (preferred) or `cards.yml` (legacy-compatible):

```text
content_packs/
  example_pack/
    pack.yml
```

## Minimal Schema

```yaml
pack_info:
  id: example_pack
  name_key: pack.example_pack.name
  desc_key: pack.example_pack.desc
  archetype: community
  rarity: uncommon
  points_cost: 120

chapter_overrides:
  feature:
    name: "Plugin Bazaar"
    gold_bonus: 1.15

cards: []
relics: []
events: []
```

## Event Schema For Node Flow

`event` nodes in chapter flow select from merged `events` definitions. Recommended fields:

```yaml
events:
  - id: contributor_wave
    name_key: event.contributor_wave.name
    desc_key: event.contributor_wave.desc
    route_tags: [safe]   # optional: safe/risk/shop/greed/debug_heavy/...
    weights:
      default: 10
      fix: 12            # optional chapter-type override
    choices:
      - id: mentor
        text_key: event.contributor_wave.choice.mentor
        effects:
          - opcode: gain_gold
            value: 30
      - id: review
        text_key: event.contributor_wave.choice.review
        effects:
          - opcode: heal
            value: 15
```

Notes:

- Use at least `2` choices per event for meaningful node decisions.
- Keep effects deterministic (avoid hidden runtime randomness in pack content).
- With fixed `--seed`, node sequence and event selection remain reproducible.

Supported `chapter_overrides` fields:

- `name`
- `description`
- `min_commits`
- `max_commits`
- `boss_chance`
- `shop_enabled`
- `gold_bonus`
- `exp_bonus`
- `enemy_hp_multiplier`
- `enemy_atk_multiplier`

## Merge and Priority

Merge target:

- `cards`, `relics`, `events`, `chapter_overrides`

Rules:

1. CLI `--content-pack` entries are merged in input order.
2. Packs discovered from `GIT_DUNGEON_CONTENT_DIR` are merged after CLI entries, sorted by folder name.
3. Later definitions override earlier IDs.

## Determinism

- With fixed `--seed`, chapter flow and boss rolls remain deterministic even with packs.
- Use `--daily --daily-date YYYY-MM-DD` to share reproducible daily runs.

## Debugging

Common validation failures are raised as explicit errors:

- Missing `pack_info`
- Missing `pack_info.id`
- Invalid YAML root type
- Non-list `cards/relics/events`
- Invalid item payload shape

Use:

```bash
git-dungeon . --content-pack <path> --verbose --seed 42 --auto --compact
```

to inspect load details and runtime behavior.

## Example Pack

Reference implementation:

- `content_packs/example_pack/pack.yml`
