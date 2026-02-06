# Git Dungeon

将 Git 提交历史映射为可游玩的命令行 Roguelike 战斗游戏。

## 这个项目是做什么的

`Git Dungeon` 会把一个 Git 仓库的提交历史转换为“章节 + 敌人”战斗流程：

- 每个 commit 会映射为一场战斗敌人。
- commit 类型会影响敌人类型和章节分布（如 `feat`、`fix`、`merge`）。
- 你通过战斗获得经验与金币，推进章节，最终通关整局。
- 可选开启 M6 AI 文案，让章节/战斗/Boss 有动态旁白。

它适合用于：

- 用游戏化方式浏览仓库历史。
- 做 CLI/规则引擎/内容系统（YAML）实验。
- 作为测试驱动的 Python 项目模板参考。

## 当前能力

- 主流程已可用：仓库解析、章节推进、战斗、奖励结算。
- 内容系统可用：`YAML` 默认内容 + `packs` 扩展。
- 测试分层完整：`unit` / `functional` / `golden`。
- M6 AI 文案已接入章节、战斗、商店、Boss 输出；默认关闭。

## 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## 运行方式

```bash
# 当前目录仓库
python -m git_dungeon.main .

# 自动战斗 + 中文
python -m git_dungeon.main . --auto --lang zh_CN

# 安装后可直接使用命令
git-dungeon . --auto
```

## 实际输出示例（无 AI）

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

## AI 文案（可选）

```bash
# 可复现（推荐 CI）
python -m git_dungeon.main . --ai=on --ai-provider=mock

# Gemini
export GEMINI_API_KEY="your-key"
python -m git_dungeon.main . --ai=on --ai-provider=gemini --lang zh_CN

# OpenAI
export OPENAI_API_KEY="your-key"
python -m git_dungeon.main . --ai=on --ai-provider=openai --lang zh_CN
```

## AI 模式输出示例（Gemini + 自动保护）

```text
[AI] enabled provider=gemini
[AI] prefetch auto-adjusted: chapter -> off (gemini free-tier safety)
[AI] Gemini rate limit: HTTP Error 429: Too Many Requests. Falling back to mock for ~60s
🧠 A fix approaches, its aura pulsing with mysterious energy.
🧠 The battle begins! fix prepares its power surge...
```

- `--ai`: `on/off`（默认 `off`）
- `--ai-provider`: `mock/gemini/openai`（默认 `mock`）
- `--ai-cache`: 缓存目录（默认 `.git_dungeon_cache`）
- `--ai-timeout`: 超时秒数（默认 `5`）
- `--ai-prefetch`: `chapter/run/off`（默认 `chapter`）

Gemini 说明：
- 当 `--ai-provider=gemini` 且 prefetch 非 `off`，运行时会自动降级为 `off`。
- 命中 429 后会进入冷却并回退 `gemini/fallback`，避免持续限流。
- 可通过 `GEMINI_MAX_RPM`（默认 `8`）和 `GEMINI_RATE_LIMIT_COOLDOWN`（默认 `60`）调节。

## 开发与测试

```bash
# 代码检查
make lint

# 单元/集成（不含 functional/golden/slow）
make test

# 功能测试
make test-func

# Golden 回归
make test-golden
```

## 目录结构

```text
src/git_dungeon/     # 主代码
tests/               # unit / functional / golden / integration
docs/                # 当前有效文档
Makefile             # 常用命令
```

## 文档

- `docs/AI_TEXT.md`
- `docs/TESTING_FRAMEWORK.md`

## License

MIT (`LICENSE`)
