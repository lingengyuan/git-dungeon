# Git Dungeon

一个将 Git 提交历史转化为 roguelike 卡牌游戏的创新工具。

> 🎮 在提交历史中战斗，让理解项目演进变得有趣！

[![CI](https://img.shields.io/github/actions/workflow/status/lingengyuan/git-dungeon/ci.yml?branch=main)](https://github.com/lingengyuan/git-dungeon/actions)
[![Tests](https://img.shields.io/badge/tests-47%2F47-blue)](https://github.com/lingengyuan/git-dungeon/actions)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org)

## 🎯 M1 更新：完整卡牌战斗系统

M1 版本完成了核心游戏机制，包含完整的 Deck/Energy/Status 系统、Combat 状态机、奖励与流派系统。

### M1 功能特性

| 模块 | 功能 | 描述 |
|------|------|------|
| **Deck 系统** | 抽牌/出牌/洗牌 | 手牌、抽牌堆、弃牌堆、消耗堆 |
| **Energy 系统** | 3 能量/回合 | 能量消耗与回合重置 |
| **Status 系统** | 9 种状态 | Block/Vulnerable/Burn/TechDebt 等 |
| **Combat 状态机** | 回合制战斗 | 回合开始→抽牌→出牌→敌人行动→回合结束 |
| **奖励系统** | 金币/卡牌/遗物 | 战斗奖励、精英加成、BOSS 奖励 |
| **流派系统** | 3 大流派 | Debug 爆发流/测试护盾流/重构代价流 |

### M1 内容统计

| 内容类型 | 数量 | 说明 |
|---------|------|------|
| 卡牌 | 54 张 | Debug 15, Test 17, Refactor 20, Basic 2 |
| 敌人 | 27 个 | 10 commit 类型，每种 2+ 模板 |
| 遗物 | 16 个 | Starter/BOSS/Rare/Uncommon/Common |
| 状态 | 9 个 | Block/Vulnerable/Burn/TechDebt 等 |
| 流派 | 3 个 | Debug 爆发流/测试护盾流/重构代价流 |
| 事件 | 6 个 | 休息点/商店/宝藏/流派事件 |

### M1 测试结果

```
47 passed, 1 skipped

测试套件:
├── i18n tests              6/6  ✅
├── CLI tests               3/3  ✅
├── golden tests            4/4  ✅
├── content loader tests    6/6  ✅
├── M1 feature tests       12/12 ✅
└── M1 rewards tests       16/16 ✅
```

## 快速开始

```bash
# 克隆项目
git clone https://github.com/lingengyuan/git-dungeon.git
cd git-dungeon

# 安装依赖
pip install -r requirements.txt

# 运行游戏 (当前仓库)
python -m git_dungeon .

# 运行游戏 (任意 GitHub 仓库)
python -m git_dungeon username/repo

# 使用中文界面
python -m git_dungeon . --lang zh_CN

# 自动战斗模式 (适合演示)
python -m git_dungeon . --auto
```

## 命令行参数

| 参数 | 描述 |
|------|------|
| `repository` | 仓库路径或 GitHub 用户名/仓库名 |
| `--seed, -s` | 随机种子 (用于复现) |
| `--lang, -l` | 语言 (en/zh_CN)，默认英文 |
| `--auto, -a` | 自动战斗模式 |
| `--verbose, -v` | 详细输出 |
| `--json-log` | JSON 格式日志 |

## 游戏界面

```
⚔️  Chapter 1: Chaos Begins
👤 DEVELOPER (Lv.1)          👾 Bug: fix issue
🟢 HP:100/100 |████████      🟢 HP:30/30 |███

Your Hand:
  [1] ⚔️  Strike      [2] 🛡️  Defend
  [3] ⚔️  Debug Strike [4] 🛡️  Test Guard

Choose your action (1-4) or enter card number:
>
```

### 流派系统

| 流派 | 风格 | 核心机制 |
|------|------|---------|
| 🔥 **Debug 爆发流** | 高伤害输出 | 快速击杀避免 TechDebt 累积 |
| 🛡️ **Test 护盾流** | 防御持久 | 高护甲/净化，稳扎稳打 |
| ⚖️ **Refactor 代价流** | 高风险高回报 | 用血量/状态换强大效果 |

## 敌人类型

| Commit 类型 | 敌人 | 难度 | 描述 |
|------------|------|------|------|
| `feat` | ✨ 功能 | ⭐⭐ | 新功能 |
| `fix` | 🐛 Bug | ⭐⭐⭐ | 修复问题 |
| `docs` | 📖 文档 | ⭐ | 文档更新 |
| `merge` | 🔀 合并 | ⭐⭐⭐⭐⭐ | BOSS 级 |
| `refactor` | 🔨 重构 | ⭐⭐⭐ | 代码重构 |
| `chore` | 🔧 维护 | ⭐ | 杂项任务 |
| `perf` | ⚡ 性能 | ⭐⭐⭐ | 性能优化 |
| `style` | 💅 格式 | ⭐ | 代码格式 |
| `test` | ✅ 测试 | ⭐⭐ | 测试相关 |
| `ci` | 🔄 流水线 | ⭐⭐ | CI/CD |

## 运行测试

```bash
# 运行所有测试
PYTHONPATH=src python3 -m pytest tests/ -v

# 运行 Golden Tests (确定性测试)
PYTHONPATH=src python3 -m pytest tests/golden_test.py -v

# 运行 i18n 测试
PYTHONPATH=src python3 -m pytest tests/test_i18n.py -v

# 运行 CLI 测试
PYTHONPATH=src python3 -m pytest tests/test_cli.py -v
```

## 项目结构

```
git-dungeon/
├── src/git_dungeon/
│   ├── content/              # 内容系统 (M1)
│   │   ├── schema.py         # 数据模型定义
│   │   ├── loader.py         # YAML 加载器
│   │   └── defaults/         # 默认内容
│   │       ├── cards.yml     # 54 张卡牌
│   │       ├── enemies.yml   # 27 个敌人
│   │       ├── relics.yml    # 16 个遗物
│   │       ├── statuses.yml  # 9 个状态
│   │       ├── archetypes.yml # 3 个流派
│   │       └── events.yml    # 6 个事件
│   ├── engine/
│   │   ├── model.py          # 数据模型 (M1 扩展)
│   │   ├── engine.py         # 游戏引擎 (M1 扩展)
│   │   ├── events.py         # 事件系统 (M1 扩展)
│   │   ├── rng.py            # 随机数生成
│   │   └── rules/
│   │       ├── rewards.py    # 奖励系统 (M1.3)
│   │       └── archetype.py  # 流派系统 (M1.3)
│   ├── core/
│   │   └── git_parser.py     # Git 数据提取
│   ├── i18n/                 # 国际化
│   ├── main.py               # CLI 入口
│   └── main_cli.py           # CLI 游戏逻辑
├── tests/
│   ├── golden_test.py        # 确定性测试
│   ├── test_i18n.py          # i18n 测试
│   ├── test_cli.py           # CLI 测试
│   ├── test_content_loader.py # 内容加载测试
│   ├── test_m1_features.py   # M1 功能测试
│   └── test_m1_rewards.py    # M1 奖励/流派测试
├── docs/                     # 文档
└── pyproject.toml            # 项目配置
```

## 技术栈

- **Python 3.11** - 开发语言
- **GitPython** - Git 仓库操作
- **Rich** - 终端美化输出
- **Typer** - CLI 框架
- **PyInstaller** - 打包成可执行文件
- **PyYAML** - 内容配置

## M1 技术细节

### 确定性保证
- 所有随机数由 `seed` 驱动
- 固定 seed 下游戏结果完全可复现
- Golden Tests 覆盖核心功能

### 数据驱动设计
- 所有游戏内容通过 YAML 文件定义
- 新增卡牌/敌人/遗物只需修改 YAML
- Content Loader 自动校验引用完整性

## 路线图

| 版本 | 里程碑 | 目标 |
|------|--------|------|
| v0.5 | M2 | 路径系统 + 事件扩展 |
| v0.6 | M3 | Meta 进度 + 角色系统 |
| v0.7 | M4 | 难度曲线 + 平衡工具 |
| v0.8 | M5 | 成就挑战系统 |
| v0.9 | M6 | AI 文案（可选） |

详见 [docs/PLAN_M2-M6.md](docs/PLAN_M2-M6.md)

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License - see [LICENSE](LICENSE) for details.

## 作者

- GitHub: [@lingengyuan](https://github.com/lingengyuan)
- 项目: https://github.com/lingengyuan/git-dungeon
