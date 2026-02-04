# AI Text Generation (M6)

Git Dungeon M6: AI-powered flavor text generation for enhanced immersion.

## Overview

M6 introduces AI-generated narrative text for enemies, battles, events, and boss phases. This feature is **completely optional** and **disabled by default**.

### Key Principles

- **Text Only**: AI generates flavor text only, never numerical values or game rules
- **Deterministic**: Same inputs always produce same outputs (via caching)
- **Offline Capable**: Works without network (mock mode or fallbacks)
- **Graceful Degradation**: Falls back to templates if AI fails

## CLI Parameters

```bash
python -m git_dungeon <repo> --ai=on --ai-provider=openai
```

| Parameter | Values | Default | Description |
|-----------|--------|---------|-------------|
| `--ai` | `on` / `off` | `off` | Enable AI text generation |
| `--ai-provider` | `mock` / `openai` | `mock` | AI provider to use |
| `--ai-cache` | path | `.git_dungeon_cache` | Cache directory |
| `--ai-prefetch` | `chapter` / `run` / `off` | `chapter` | Prefetch strategy |
| `--ai-timeout` | seconds | 5 | API timeout |

## Providers

### Null Provider (`--ai=off`)

Disables AI entirely. No network calls, no caching.

### Mock Provider (Default)

Deterministic pseudo-random text for testing and CI. No network required.

```bash
python -m git_dungeon . --ai=on --ai-provider=mock
```

### OpenAI Provider

Real AI-generated text using OpenAI API.

```bash
export OPENAI_API_KEY="sk-..."
python -m git_dungeon . --ai=on --ai-provider=openai
```

**Requirements:**
- `openai` package installed
- `OPENAI_API_KEY` environment variable
- Network access to OpenAI API

## Text Types

AI generates the following text types:

| Type | Description | Length Limit |
|------|-------------|--------------|
| `ENEMY_INTRO` | Enemy introduction | 60 chars |
| `BATTLE_START` | Battle opening narration | 80 chars |
| `BATTLE_END` | Battle conclusion | 80 chars |
| `EVENT_FLAVOR` | Event atmosphere | 80 chars |
| `BOSS_PHASE` | Boss phase transition | 80 chars |

## Caching

AI-generated text is cached for reproducibility:

```
.git_dungeon_cache/
└── ai_text.sqlite    # SQLite cache (default)
```

### Cache Key Structure

```
{provider}:{repo_id}:{seed}:{lang}:{content_version}:{kind}:{specific_id}
```

The cache ensures:
- Same seed + same repo = same text
- Different runs produce identical results
- CI/CD builds are reproducible

### Clear Cache

```bash
# Manual
rm -rf .git_dungeon_cache/ai_text.sqlite

# Or use helper
python -m git_dungeon.tools.clear_cache
```

## Offline / CI Behavior

### When Network is Unavailable

1. Provider fails → Fallback to template
2. Fallback templates cover all text types
3. Game continues normally

### CI/CD Mode

```bash
# Recommended for CI
python -m git_dungeon . --ai=on --ai-provider=mock
```

Mock provider ensures:
- No network calls
- Deterministic outputs
- Fast test execution

## Configuration

### Environment Variables

```bash
# OpenAI (required for openai provider)
OPENAI_API_KEY=sk-...

# Optional overrides
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT=5
```

### Content Version

Content version is automatically computed from YAML files:

```bash
# Determined from content/defaults/*.yml
content_version = hash(all_yml_files)
```

Changes to content files automatically invalidate cache.

## Safety Features

### Output Sanitization

AI output is sanitized before use:

1. **Markdown Removal**: Code blocks, bold, italic stripped
2. **Length Limits**: Hard limits per text type
3. **Keyword Blocking**: Prevents rule-breaking suggestions
4. **Character Cleaning**: Invalid characters removed

### Blocked Keywords

AI suggestions for actions or numbers are blocked:

```python
BLOCKED = [
    "you should", "you must",  # Action suggestions
    "+10 damage", "50 HP",     # Numbers
    "increase attack",         # Rule changes
]
```

## Fallback Templates

When AI fails or is disabled, template-based fallbacks are used:

| Text Kind | Fallback Source |
|-----------|----------------|
| ENEMY_INTRO | Commit type (feat/fix/docs/etc.) |
| BATTLE_START | Enemy tier (normal/elite/boss) |
| BATTLE_END | Victory/defeat flag |
| EVENT_FLAVOR | Event type (rest/shop/treasure) |
| BOSS_PHASE | Phase transition |

Fallbacks support both English and Chinese.

## Testing

### Run M6 Tests

```bash
# All M6 tests
pytest tests/functional/test_m6_ai_text_func.py -v

# Specific test
pytest tests/functional/test_m6_ai_text_func.py::TestMockAIClient::test_deterministic_same_seed -v
```

### Golden Tests

```bash
# Run golden tests
pytest tests/golden/ -v

# Update golden files
pytest tests/golden/ --update-goldens
```

## Performance

### Prefetch Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `chapter` (default) | Prefetch chapter text | Best for single chapter |
| `run` | Prefetch entire run | Best for full playthrough |
| `off` | Generate on-demand | Low memory, slower |

### Batch Generation

AI provider supports batch generation:

```python
# Generate 10 texts in one API call
requests = [TextRequest(...), ...]
responses = client.generate_batch(requests)  # Single API call
```

## Troubleshooting

### AI generates inappropriate text

1. Check sanitization logs
2. Verify fallback is working
3. Report issue with seed + repo

### Cache not working

1. Check cache directory permissions
2. Clear cache and retry
3. Verify cache backend (sqlite/json)

### OpenAI API errors

```bash
# Check API key
echo $OPENAI_API_KEY

# Test connection
curl https://api.openai.com/v1/models
```

## Migration from v0.8

### Backward Compatibility

- `--ai=off` (default) → identical to v0.8 behavior
- No changes to game logic or rules
- Existing save files work unchanged

### Opt-in Feature

AI text generation is opt-in:

```bash
# v0.8 behavior (default)
python -m git_dungeon .

# M6 with AI
python -m git_dungeon . --ai=on
```

## Future Work

Potential enhancements for future versions:

- [ ] More AI providers (Claude, Gemini)
- [ ] Custom prompt templates
- [ ] Voice synthesis for text-to-speech
- [ ] Multi-language support expansion
- [ ] Per-user text style preferences
