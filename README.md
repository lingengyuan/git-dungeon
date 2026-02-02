# Git Dungeon

一个将 Git 提交历史转化为roguelike游戏的创新工具。

> 🎮 在提交历史中战斗，让理解项目演进变得有趣！

[![CI](https://img.shields.io/github/actions/workflow/status/lingengyuan/git-dungeon/ci.yml?branch=main)](https://github.com/lingengyuan/git-dungeon/actions)
[![Tests](https://img.shields.io/badge/tests-13%2F13-blue)](https://github.com/lingengyuan/git-dungeon/actions)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org)

## 特性

| 功能 | 描述 |
|------|------|
| 🎮 **回合制战斗** | 每个 commit 都是一个敌人 |
| 📊 **章节系统** | 根据 commit 自动划分游戏章节 |
| 🏪 **商店系统** | 战斗获取金币，购买装备和药水 |
| 👹 **BOSS 战** | 合并提交(merge)变成强大敌人 |
| 🌐 **中文支持** | 支持英文/中文界面切换 |
| 📦 **任意仓库** | 支持任意 GitHub 仓库 |

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

## 安装可执行文件

```bash
# Linux/macOS
./dist/GitDungeon .

# Windows
./dist/GitDungeon.exe .
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

### 英文版 (默认)
```
⚔️  Chapter 1: Chaos Begins
👤 DEVELOPER (Lv.1)          👾 Bug: fix issue
🟢 HP:100/100 |████████      🟢 HP:30/30 |███

Choose your action:
  [1] Attack  [2] Defend  [3] Skill  [4] Run/Shop
>
```

### 中文版
```
⚔️  第一章：混沌初开
👤 开发者 (Lv.1)          👾 Bug: 修复问题
🟢 HP:100/100 |████████    🟢 HP:30/30 |███

选择你的行动:
  [1] ⚔️ 攻击  [2] 🛡️ 防御  [3] ✨ 技能  [4] 🏃 逃跑/商店
>
```

## 敌人类型

| Commit 类型 | 敌人 | 难度 | 描述 |
|------------|------|------|------|
| `feat` | ✨ 功能 | ⭐⭐ | 新功能 |
| `fix` | 🐛 Bug | ⭐⭐⭐ | 修复问题 |
| `docs` | 📖 文档 | ⭐ | 文档更新 |
| `merge` | 🔀 合并 | ⭐⭐⭐⭐⭐ | BOSS 级 |
| `refactor` | 🔨 重构 | ⭐⭐⭐ | 代码重构 |

## 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行 Golden Tests (确定性测试)
PYTHONPATH=src python3 tests/golden_test.py

# 运行 i18n 测试
PYTHONPATH=src python3 tests/test_i18n.py

# 运行 CLI 测试
PYTHONPATH=src python3 tests/test_cli.py
```

## 测试结果

```
🧪 Golden Test Results
  ✅ Combat (seed=12345): PASS
  ✅ Multiple Battles (seed=99999): PASS
  ✅ Escape Mechanics (seed=55555): PASS
  ✅ Level Progression (seed=77777): PASS

🧪 i18n Test Results
  ✅ Translation structure valid
  ✅ English translations valid
  ✅ Chinese translations valid

Total: 13/13 tests passed
```

## 项目结构

```
git-dungeon/
├── src/git_dungeon/
│   ├── core/           # 核心逻辑
│   │   └── git_parser.py    # Git 数据提取
│   ├── engine/         # 游戏引擎
│   │   ├── model.py         # 数据模型
│   │   ├── combat.py        # 战斗系统
│   │   └── rules/           # 规则系统
│   ├── i18n/           # 国际化
│   │   └── translations.py  # 翻译表
│   ├── main.py         # CLI 入口
│   └── main_cli.py     # CLI 游戏逻辑
├── tests/              # 测试用例
│   ├── golden_test.py  # 确定性测试
│   ├── test_i18n.py    # i18n 测试
│   └── test_cli.py     # CLI 测试
├── docs/               # 文档
├── dist/               # 可执行文件
└── pyproject.toml      # 项目配置
```

## 技术栈

- **Python 3.11** - 开发语言
- **GitPython** - Git 仓库操作
- **Rich** - 终端美化输出
- **Typer** - CLI 框架
- **PyInstaller** - 打包成可执行文件

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License - see [LICENSE](LICENSE) for details.

## 作者

- GitHub: [@lingengyuan](https://github.com/lingengyuan)
- 项目: https://github.com/lingengyuan/git-dungeon
