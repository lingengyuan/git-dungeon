# Git Dungeon

将 Git 提交历史映射为可游玩的命令行 Roguelike 战斗游戏。

## 当前实现

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

## 运行

```bash
# 当前目录仓库
python -m git_dungeon.main .

# 自动战斗 + 中文
python -m git_dungeon.main . --auto --lang zh_CN
```

## AI 文案（可选）

```bash
# 可复现（推荐 CI）
python -m git_dungeon.main . --ai=on --ai-provider=mock

# Gemini
export GEMINI_API_KEY="your-key"
python -m git_dungeon.main . --ai=on --ai-provider=gemini

# OpenAI
export OPENAI_API_KEY="your-key"
python -m git_dungeon.main . --ai=on --ai-provider=openai
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
make lint
make test
make test-func
make test-golden
```

## 目录结构

```text
src/git_dungeon/     # 主代码
tests/               # 单测/功能/Golden
docs/                # 当前有效文档
Makefile             # 常用命令
```

## 文档

- `docs/AI_TEXT.md`
- `docs/TESTING_FRAMEWORK.md`

## License

MIT (`LICENSE`)
