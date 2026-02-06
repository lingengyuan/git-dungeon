# AI Text Generation (M6) - Current Status

本文档描述 **当前代码已实现** 的 M6 能力，避免与历史计划混淆。

## Scope

M6 目前提供的是 AI 文案基础设施：

- CLI 参数（`--ai*`）
- Provider 抽象（null/mock/gemini/openai）
- 缓存（SQLite/JSON）
- 文本清洗（sanitize）
- 模板降级（fallback）
- 功能测试（M6 相关）

## Current Implementation

### 1) CLI 参数（已完成）

```bash
python -m git_dungeon . --ai=on --ai-provider=mock
```

可用参数：

- `--ai`: `on/off`（默认 `off`）
- `--ai-provider`: `mock/gemini/openai`（默认 `mock`）
- `--ai-cache`: 缓存目录（默认 `.git_dungeon_cache`）
- `--ai-timeout`: API 超时（默认 `5`）
- `--ai-prefetch`: `chapter/run/off`（参数存在）

### 2) Providers（已完成）

- `off/null`: 不生成文案
- `mock`: 确定性伪随机文本（CI 推荐）
- `gemini`: 读取 `GEMINI_API_KEY`
- `openai`: 读取 `OPENAI_API_KEY`（依赖 `openai` 包）

### 3) Cache / Sanitize / Fallback（已完成）

- 缓存默认文件：`.git_dungeon_cache/ai_text.sqlite`
- 缓存键包含 provider/repo_id/seed/lang/kind 等信息
- 文本会经过长度限制、Markdown 清理、规则关键词过滤
- AI 失败时使用 fallback 模板文案

清理缓存：

```bash
rm -f .git_dungeon_cache/ai_text.sqlite
# 或
make ai-cache-clear
```

## Important Gaps (Not Finished Yet)

以下能力在当前主流程中 **尚未完整接入**：

1. AI 文案并未系统性注入到战斗/事件/BOSS 的实时输出流程。  
2. `--ai-prefetch` 参数已提供，但尚未形成稳定可观测的预取收益路径。  
3. `content_version` 目前使用固定值，尚未自动按 YAML 内容哈希失效缓存。  

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
