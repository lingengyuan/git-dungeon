# Git Dungeon

将 Git 提交历史映射为可游玩的命令行 Roguelike 卡牌战斗项目。

## 当前状态（以代码为准）

- 核心玩法可运行：仓库解析、章节推进、战斗、奖励与基础结算。
- 内容系统可用：`YAML` 配置 + `packs` 扩展内容。
- 测试体系完整：`unit` / `integration` / `functional` / `golden`。
- M6（AI）为可选能力：已具备 provider、缓存、清洗、fallback 与测试；默认关闭，不影响主流程。

> 说明：历史里程碑/统计信息已移除，避免与当前实现偏差。

## 快速开始

```bash
git clone https://github.com/lingengyuan/git-dungeon.git
cd git-dungeon

python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 运行游戏

```bash
# 当前目录仓库
python -m git_dungeon .

# 指定 GitHub 仓库（user/repo）
python -m git_dungeon username/repo

# 中文界面
python -m git_dungeon . --lang zh_CN

# 自动战斗
python -m git_dungeon . --auto
```

### AI 参数（可选）

```bash
# 本地可复现（无外网依赖）
python -m git_dungeon . --ai=on --ai-provider=mock

# Gemini
export GEMINI_API_KEY="your-key"
python -m git_dungeon . --ai=on --ai-provider=gemini

# OpenAI
export OPENAI_API_KEY="your-key"
python -m git_dungeon . --ai=on --ai-provider=openai
```

支持参数：

- `--ai`：`on/off`（默认 `off`）
- `--ai-provider`：`mock/gemini/openai`（默认 `mock`）
- `--ai-cache`：缓存目录（默认 `.git_dungeon_cache`）
- `--ai-timeout`：API 超时秒数（默认 `5`）
- `--ai-prefetch`：`chapter/run/off`（默认 `chapter`）

## 开发命令

```bash
# 快速单测/集成（排除 functional、golden、slow）
make test

# 功能测试（CI 门禁）
make test-func

# Golden 回归测试（CI 门禁）
make test-golden

# 代码检查
make lint

# 格式化
make format
```

## 项目结构

```text
git-dungeon/
├── src/git_dungeon/
│   ├── main.py              # CLI 入口
│   ├── main_cli.py          # 主游戏流程
│   ├── main_cli_ai.py       # AI 参数与包装层
│   ├── engine/              # 核心规则与状态
│   ├── content/             # YAML 内容与 packs
│   ├── ai/                  # AI 客户端/缓存/清洗/fallback
│   └── core/                # Git 解析与基础系统
├── tests/                   # unit/integration/functional/golden
├── docs/                    # 设计与阶段文档
└── Makefile                 # 常用开发命令
```

## 相关文档

- `docs/AI_TEXT.md`：M6 AI 模块说明（部分内容可能超前，建议结合代码与测试阅读）
- `docs/TESTING_FRAMEWORK.md`：测试分层与门禁策略
- `AGENTS.md`：仓库协作约定

## 贡献

欢迎提交 Issue / PR。提交前建议至少运行：

```bash
make test
make test-func
make test-golden
```

## License

MIT，详见 `LICENSE`。
