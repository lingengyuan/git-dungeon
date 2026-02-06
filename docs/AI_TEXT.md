# AI Text Generation (M6) - Current Status

本文档描述当前代码中 M6 的真实实现状态。

## Scope

M6 提供“可选 AI 文案层”，默认关闭，不影响核心战斗逻辑。

## Current Implementation

### 1) CLI 参数

```bash
python -m git_dungeon . --ai=on --ai-provider=mock
```

可用参数：

- `--ai`: `on/off`（默认 `off`）
- `--ai-provider`: `mock/gemini/openai`（默认 `mock`）
- `--ai-cache`: 缓存目录（默认 `.git_dungeon_cache`）
- `--ai-timeout`: API 超时（默认 `5`）
- `--ai-prefetch`: `chapter/run/off`（文案预取策略）

### 2) Providers

- `off/null`: 不生成文案
- `mock`: 确定性伪随机文本（CI 推荐）
- `gemini`: 读取 `GEMINI_API_KEY`
- `openai`: 读取 `OPENAI_API_KEY`（依赖 `openai` 包）

### 3) Runtime Integration（已接入主流程）

AI 文案已接入以下 CLI 输出点：

- 章节介绍（`EVENT_FLAVOR`）
- 普通战斗开场（`ENEMY_INTRO` + `BATTLE_START`）
- 普通战斗结算（`BATTLE_END`）
- 商店进入提示（`EVENT_FLAVOR`）
- Boss 战开场/结算（`BOSS_PHASE` + `BATTLE_END`）

### 4) Cache / Sanitize / Fallback

- 缓存默认文件：`.git_dungeon_cache/ai_text.sqlite`
- 缓存键包含 provider/repo_id/seed/lang/kind 等信息
- `content_version` 由 `prompts/fallbacks/sanitize` 内容哈希生成（模板变更自动失效）
- 文本会经过长度限制、Markdown 清理、规则关键词过滤
- AI 失败时使用 fallback 模板文案

清理缓存：

```bash
rm -f .git_dungeon_cache/ai_text.sqlite
# 或
make ai-cache-clear
```

### Prefetch 行为

- `chapter`: 章节开始时预取该章节常用文案
- `run`: 首章开始时预取整局文案
- `off`: 不预取，按需生成/读缓存
- `gemini` provider 下，若用户传入 `chapter/run`，运行时会自动降级为 `off`（避免免费额度快速触发 429）

Gemini 限流保护：

- 客户端内置本地 RPM 预算（默认 `GEMINI_MAX_RPM=8`，低于常见免费额度 10/min）
- 命中 429 后进入冷却窗口（默认 `GEMINI_RATE_LIMIT_COOLDOWN=60` 秒）
- 冷却期间自动回退 `gemini/fallback` 并写入缓存，避免重复打 API

## Testing

```bash
# M6 文本模块测试
PYTHONPATH=src python3 -m pytest tests/functional/test_m6_ai_text_func.py -v

# M6 集成测试
PYTHONPATH=src python3 -m pytest tests/functional/test_m6_ai_integration.py -v
```

CI 推荐使用 mock provider，避免外网依赖：

```bash
python -m git_dungeon . --ai=on --ai-provider=mock
```
