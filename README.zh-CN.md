# Git Dungeon

[English](README.md) | [简体中文](README.zh-CN.md)

将 Git 提交历史映射为可游玩的命令行 Roguelike。

## 当前版本

- `1.2.0`
- 版本策略：`SemVer`
- 升级说明：见 `CHANGELOG.md`（`1.2.0`）

## 快速开始（3 步）

1. 创建并激活干净虚拟环境。

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. 使用 wheel 安装（发布链路推荐）。

```bash
python -m pip install --upgrade pip build
python -m build --wheel
pip install dist/*.whl
```

3. 运行可复现 demo（自动战斗 + 紧凑输出 + 指标）。

```bash
git-dungeon . --seed 42 --auto --compact --metrics-out ./run_metrics.json
```

## 常用参数

- `--auto`：自动战斗决策。
- `--compact`：战斗紧凑日志。
- `--metrics-out <path>`：输出 JSON 指标。
- `--print-metrics`：终局打印指标摘要。
- `--seed <int>`：固定随机种子，便于复现。
- `--ai=off|on --ai-provider=mock|gemini|openai`：AI 文案开关与提供方。

## 存档目录

默认保存到 `~/.local/share/git-dungeon`，可通过环境变量覆盖：

```bash
export GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-saves
```

## Demo 命令

```bash
# 运行当前仓库
git-dungeon . --auto

# 紧凑自动战斗并打印指标摘要
git-dungeon . --seed 42 --auto --compact --print-metrics

# 中文 UI
git-dungeon . --auto --lang zh_CN
```

## 开发命令

```bash
make lint
make test
make test-func
make test-golden
make build-wheel
make smoke-install
```

## 文档

- `CHANGELOG.md`
- `docs/FAQ.md`
- `docs/perf.md`
- `docs/AI_TEXT.md`
- `docs/TESTING_FRAMEWORK.md`

## License

MIT (`LICENSE`)
