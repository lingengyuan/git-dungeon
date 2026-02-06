# Git Dungeon

[English](README.md) | [简体中文](README.zh-CN.md)

将 Git 提交历史映射为可游玩的命令行 Roguelike 战斗游戏。

## 这个项目是做什么的

`Git Dungeon` 会把一个 Git 仓库的提交历史转换为“章节 + 敌人”战斗流程：

- 每个 commit 会映射为一场战斗敌人。
- commit 类型（`feat`、`fix`、`merge`）会影响敌人风格和章节节奏。
- 你通过战斗获得经验与金币，推进章节，最终通关整局。
- 可选开启 M6 AI 文案，让章节/战斗/Boss 有动态旁白。

适合场景：

- 用游戏化方式浏览仓库历史。
- 做 CLI / 规则引擎 / YAML 内容系统实验。
- 作为测试驱动的 Python CLI 项目参考。

## 当前能力

- 主流程已可用：仓库解析、章节推进、战斗、奖励结算。
- 内容系统可用：`YAML` 默认内容 + `packs` 扩展。
- 测试分层完整：`unit` / `functional` / `golden`。
- M6 AI 文案已接入章节、战斗、商店、Boss 输出，具备缓存与回退策略。

## 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## 快速开始

```bash
# 运行当前目录仓库
python -m git_dungeon.main .

# 自动战斗 + 中文（支持 zh 别名）
python -m git_dungeon.main . --auto --lang zh_CN
# 或
python -m git_dungeon.main . --auto --lang zh

# 安装后直接运行
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

Gemini 说明：

- 免费层保护：prefetch 会自动降级为 `off`。
- 遇到 HTTP 429：会进入冷却窗口并临时回退到 mock 文案。
- 可调环境变量：`GEMINI_MAX_RPM`（默认 `8`）、`GEMINI_RATE_LIMIT_COOLDOWN`（默认 `60`）。

## 开发与测试

```bash
make lint
make test
make test-func
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
