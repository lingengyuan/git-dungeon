# Git Dungeon Roguelike - 项目方案

> 版本: 1.0
> 创建日期: 2026-01-31
> 作者: OpenClaw (claw)
> 状态: 已批准，待开发

---

## 目录

1. [项目概述](#1-项目概述)
2. [技术架构](#2-技术架构)
3. [核心游戏机制](#3-核心游戏机制)
4. [物品系统](#4-物品系统)
5. [资源限制策略](#5-资源限制策略)
6. [测试架构](#6-测试架构)
7. [项目结构](#7-项目结构)
8. [安装与运行](#8-安装与运行)
9. [CI/CD 流程](#9-cicd-流程)
10. [MVP 里程碑](#10-mvp-里程碑)
11. [参考项目](#11-参考项目)

---

## 1. 项目概述

### 1.1 愿景

将 Git 提交历史转化为一个有趣的肉鸽类地牢爬行游戏，让开发者通过游戏的方式回顾自己的代码历史。

### 1.2 核心创意

```
真实 Git 仓库 → 游戏关卡

commit hash         → 关卡ID
commit message      → 怪物名称 + 挑战描述
代码变更 (+/- 行数) → 怪物属性（攻击力/防御力）
commit 作者         → BOSS 信息
改动的文件          → 掉落物品
merge commit        → 商店/休息点
```

### 1.3 目标用户

- 开发者群体
- Git 用户
- Roguelike 游戏爱好者

### 1.4 核心价值

- 有趣：游戏化代码历史
- 安全：资源受限，不爆服务器
- 可测试：完整的单元测试覆盖
- 可扩展：Lua 脚本系统

---

## 2. 技术架构

### 2.1 技术栈

| 层级 | 技术选择 | 理由 |
|------|----------|------|
| 语言 | Python 3.11+ | 开发效率高、资源友好、类型系统完善 |
| UI | Textual | 现代终端UI、GPU加速、活跃维护 |
| Git解析 | GitPython | 轻量、稳定、文档完善 |
| 测试 | pytest + pytest-asyncio | 成熟、插件丰富 |
| 内容脚本 | Lua 5.4 | 嵌入式、易扩展、安全 |
| 打包 | PyInstaller | 跨平台支持 |

### 2.2 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                      Git Dungeon Roguelike                      │
├─────────────────────────────────────────────────────────────────┤
│  Core Engine (Python 3.11+)                                     │
│  ├── Git Parser (gitpython) - 读取commit历史                    │
│  ├── Game Engine (ECS架构) - 实体-组件-系统                     │
│  ├── Combat System - 回合制战斗                                 │
│  ├── Save System - 增量存档                                     │
│  └── Resource Manager - 资源限制                                │
├─────────────────────────────────────────────────────────────────┤
│  UI Layer (Textual)                                             │
│  ├── Main Screen - 游戏主界面                                   │
│  ├── Combat Screen - 战斗界面                                   │
│  ├── Map Screen - 地图/进度                                     │
│  ├── Inventory Screen - 物品栏                                  │
│  └── Settings Screen - 设置                                     │
├─────────────────────────────────────────────────────────────────┤
│  Content Layer (Lua 5.4)                                        │
│  ├── items.lua - 物品定义                                       │
│  ├── monsters.lua - 怪物模板                                    │
│  ├── skills.lua - 技能定义                                      │
│  └── events.lua - 事件定义                                      │
├─────────────────────────────────────────────────────────────────┤
│  Testing Layer (pytest)                                         │
│  ├── Unit Tests - 单元测试                                      │
│  ├── Integration Tests - 集成测试                               │
│  ├── Fuzzy Tests - 模糊测试                                     │
│  └── Content Tests - 内容测试                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 设计原则

1. **ECS架构**: 实体-组件-系统分离，便于扩展
2. **内容与逻辑分离**: 使用 Lua 定义游戏内容
3. **资源受限**: 所有操作都有资源限制
4. **测试驱动**: 先写测试再开发
5. **渐进式加载**: 分块读取大仓库

---

## 3. 核心游戏机制

### 3.1 Git → 游戏元素映射

| Git 元素 | 游戏元素 | 说明 |
|----------|----------|------|
| commit message (英文) | 怪物名称 + 描述 | 提取 message 作为怪物名 |
| commit message (中文) | 怪物名称 + 描述 | 支持中文 message |
| +lines (添加行数) | 攻击力 / 经验值 | 添加越多越强 |
| -lines (删除行数) | 防御力 / 难度 | 删除越多防御越高 |
| 文件类型 (*.py, *.go, *.js) | 掉落物品类型 | 根据文件类型掉落 |
| merge commit | 商店 / 休息点 | 可以购买/恢复 |
| branch commit | 隐藏关卡 / 支线任务 | 发现隐藏内容 |
| revert commit | BOSS 战 | 特殊挑战 |

### 3.2 Git 命令 → 战斗技能

| Git 命令 | 游戏技能 | 效果 |
|----------|----------|------|
| git add <file> | 普通攻击 | 伤害 = 文件行数 |
| git commit -m "msg" | 必杀技 | 消耗MP，大伤害 |
| git push origin HEAD | 远程攻击 | 高伤害，可暴击 |
| git pull origin | 恢复 HP | 恢复一定生命值 |
| git stash | 护盾 | 抵挡一次攻击 |
| git reset --hard | 时间回溯 | 回到上一步状态 |
| git merge | 组合技 | 多个敌人同时攻击 |

### 3.3 游戏流程

```
1. 选择 Git 仓库
   ↓
2. 解析 commit 历史 (受资源限制)
   ↓
3. 生成怪物列表
   ↓
4. 回合制战斗
   - 玩家行动 (使用 Git 命令)
   - 敌人行动
   ↓
5. 击败怪物获得物品
   ↓
6. 到达最新 commit 胜利
   ↓
7. 结算与存档
```

### 3.4 角色属性

```
玩家 (Developer):
  HP     - 代码行数 (最大)
  MP     - commit 数量 (技能点)
  ATK    - 平均每 commit 添加行数
  DEF    - 平均每 commit 删除行数
  LEVEL  - 战斗次数
  EXP    - 累计获得经验
```

### 3.5 怪物属性

```
怪物 (Commit):
  NAME   - commit message (截取前30字符)
  HP     - 总变更行数 (+/-)
  ATK    - 添加行数
  DEF    - 删除行数
  EXP    - 变更行数 / 10
  DROP   - 改动文件对应的物品
```

---

## 4. 物品系统

### 4.1 文件类型 → 物品映射

| 文件类型 | 物品 | 效果 |
|----------|------|------|
| *.py | 魔法书 | 学习新技能 |
| *.go | 武器 | 攻击力+ |
| *.js | 药水 | 恢复HP |
| *.rs | 装备 | 防御+ |
| *.md | 地图碎片 | 显示隐藏关卡 |
| *.sql | 护符 | 幸运+ |
| *.json | 符文 | 技能冷却- |
| *.yaml | 卷轴 | 一次性技能 |
| *.java | 圣杯 | 全属性+ |
| *.cpp | 剑 | 高攻击 |

### 4.2 物品稀有度

| 稀有度 | 颜色 | 概率 | 效果加成 |
|--------|------|------|----------|
| 普通(Common) | 白色 | 60% | 基础效果 |
| 稀有(Rare) | 蓝色 | 25% | +50% 效果 |
| 史诗(Epic) | 紫色 | 10% | +100% 效果 |
| 传说(Legendary) | 金色 | 4% | +200% 效果 |
| 代码腐败(Corrupted) | 红色 | 1% | 高风险高回报 |

### 4.3 物品属性

```
BaseItem:
  - name: 物品名称
  - type: 物品类型
  - rarity: 稀有度
  - value: 基础值
  - description: 描述

Weapon (继承BaseItem):
  - attack: 攻击力加成

Armor (继承BaseItem):
  - defense: 防御力加成

Consumable (继承BaseItem):
  - effect: 效果类型 (HP恢复, MP恢复, Buff)
  - amount: 效果量
```

---

## 5. 资源限制策略

### 5.1 配置类定义

```python
class Difficulty(Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    HARDCORE = "harcore"

class GameConfig(BaseModel):
    """游戏配置"""
    # 基础设置
    repo_path: str = "./"
    difficulty: Difficulty = Difficulty.NORMAL
    
    # 资源限制
    max_commits: int = 1000
    max_files_per_commit: int = 50
    max_commit_message_len: int = 500
    max_memory_mb: int = 100
    cache_size: int = 100
    chunk_size: int = 100
    
    # 游戏设置
    auto_save: bool = True
    auto_save_interval: int = 10
    show_combat_log: bool = True
    enable_sound: bool = True
    
    # 主题
    theme: str = "default"
    
    class Config:
        env_prefix = "GIT_DUNGEON_"
```

### 5.2 资源限制详情

| 限制项 | 默认值 | 说明 | 超出处理 |
|--------|--------|------|----------|
| max_commits | 1000 | 最多读取1000个commit | 只读最近的1000个 |
| max_files_per_commit | 50 | 每个commit最多50个文件 | 忽略超出的文件 |
| max_commit_message_len | 500 | commit message最大长度 | 截断处理 |
| max_memory_mb | 100 | 最大100MB内存 | 强制GC |
| cache_size | 100 | commit缓存数量 | LRU淘汰 |
| chunk_size | 100 | 分块处理大小 | 渐进式加载 |
| render_fps | 30 | 渲染帧率上限 | 降帧处理 |
| combat_timeout_sec | 300 | 战斗超时5分钟 | 强制跳过 |
| auto_save_interval | 10 | 自动保存间隔 | 回合计数 |

### 5.3 性能监控

```python
class ResourceMonitor:
    """资源监控器"""
    
    def __init__(self):
        self.memory_usage = 0
        self.cpu_usage = 0
        self.active_operations = []
    
    def check_memory(self) -> bool:
        """检查内存是否超限"""
        return self.memory_usage < settings.max_memory_mb
    
    def check_operations(self) -> bool:
        """检查是否有阻塞操作"""
        return len(self.active_operations) < 10
    
    def record_operation(self, op: str):
        """记录操作开始"""
        self.active_operations.append(op)
    
    def finish_operation(self, op: str):
        """记录操作结束"""
        self.active_operations.remove(op)
```

---

## 6. 测试架构

### 6.1 测试类型

```
┌────────────────────────────────────────────────────────────────┐
│                     Testing Framework                           │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Unit Tests (pytest)                                           │
│  ├── test_git_parser.py                                        │
│  │   ├── test_parse_single_commit()                            │
│  │   ├── test_parse_large_repo()                               │
│  │   ├── test_parse_empty_repo()                               │
│  │   └── test_handle_corrupt_data()                            │
│  ├── test_combat_system.py                                     │
│  │   ├── test_damage_calculation()                             │
│  │   ├── test_critical_hit()                                   │
│  │   ├── test_dodge_mechanic()                                 │
│  │   └── test_skill_execution()                                │
│  ├── test_character.py                                         │
│  │   ├── test_level_up()                                       │
│  │   ├── test_stat_calculation()                               │
│  │   └── test_skill_unlocks()                                  │
│  └── test_item_system.py                                       │
│      ├── test_item_generation()                                │
│      ├── test_item_rarity()                                    │
│      └── test_item_combination()                               │
│                                                                 │
│  Integration Tests                                             │
│  ├── test_full_gameplay.py                                     │
│  ├── test_save_load_cycle()                                    │
│  └── test_resource_limits()                                    │
│                                                                 │
│  Fuzzy Tests (随机测试)                                         │
│  ├── test_random_commits()                                     │
│  ├── test_random_player_actions()                              │
│  └── test_edge_cases()                                         │
│                                                                 │
│  Content Tests (Lua内容验证)                                    │
│  ├── test_item_definitions.lua                                 │
│  ├── test_monster_templates.lua                                │
│  └── test_skill_balances.lua                                   │
│                                                                 │
│  Performance Tests                                             │
│  ├── test_memory_usage()                                       │
│  ├── test_load_time()                                          │
│  └── test_render_performance()                                 │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 6.2 测试覆盖率要求

| 模块 | 覆盖率要求 |
|------|------------|
| core/git_parser.py | >= 95% |
| core/combat.py | >= 90% |
| core/character.py | >= 90% |
| core/inventory.py | >= 85% |
| core/save_system.py | >= 95% |
| lua/interpreter.py | >= 80% |
| 整体 | >= 85% |

### 6.3 测试示例

```python
# tests/unit/test_combat.py
import pytest
from src.core.combat import CombatSystem, DamageType

class TestCombatSystem:
    """战斗系统单元测试"""
    
    def setup_method(self):
        """每个测试前初始化"""
        self.combat = CombatSystem()
        self.player = Character("Player", hp=100, attack=10, defense=5)
        self.enemy = Character("Enemy", hp=50, attack=8, defense=3)
    
    def test_damage_calculation(self):
        """测试伤害计算"""
        damage = self.combat.calculate_damage(
            attacker=self.player,
            defender=self.enemy,
            skill_multiplier=1.0
        )
        # 基础伤害 = 攻击 - 防御 = 10 - 3 = 7
        assert damage == 7
    
    def test_critical_hit(self):
        """测试暴击"""
        # 暴击时伤害翻倍
        damage = self.combat.calculate_damage(
            attacker=self.player,
            defender=self.enemy,
            skill_multiplier=2.0
        )
        assert damage == 14
    
    def test_dodge_mechanic(self):
        """测试闪避"""
        # 设置高闪避率
        self.enemy.dodge_chance = 1.0
        
        # 多次测试应该全部闪避
        dodges = 0
        for _ in range(100):
            if self.combat.check_dodge(self.enemy):
                dodges += 1
        
        assert dodges == 100
```

### 6.4 模糊测试示例

```python
# tests/fuzzy/test_random_actions.py
import pytest
from src.core.game_engine import GameEngine
from src.utils.resource_manager import ResourceManager

class TestFuzzy:
    """模糊测试 - 随机操作"""
    
    def test_random_commits(self, tmp_path):
        """测试随机 commit 数据"""
        # 创建临时仓库
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        
        # 生成随机 commit 历史
        engine = GameEngine()
        resource_manager = ResourceManager()
        
        # 执行随机操作序列
        for i in range(100):
            # 随机选择仓库操作
            action = random.choice([
                "parse_commit",
                "get_file_changes",
                "get_author"
            ])
            
            try:
                if action == "parse_commit":
                    engine.parse_commit(repo_path)
                elif action == "get_file_changes":
                    engine.get_file_changes(repo_path)
                else:
                    engine.get_author(repo_path)
            except Exception as e:
                # 任何异常都应该被捕获和处理
                assert isinstance(e, (ValueError, IOError, GitError))
    
    def test_random_player_actions(self, game_state):
        """测试随机玩家操作"""
        engine = GameEngine(game_state)
        
        for _ in range(50):
            action = random.choice([
                "attack",
                "use_skill",
                "use_item",
                "defend"
            ])
            
            result = engine.execute_action(action)
            # 确保不会崩溃
            assert result is not None
```

---

## 7. 项目结构

```
git-dungeon/
├── src/
│   ├── __init__.py
│   ├── main.py                    # 入口点
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py            # 配置管理
│   │   └── themes.py              # 主题系统
│   ├── core/
│   │   ├── __init__.py
│   │   ├── git_parser.py          # Git解析器
│   │   ├── game_engine.py         # 游戏引擎(ECS)
│   │   ├── entity.py              # 实体基类
│   │   ├── component.py           # 组件基类
│   │   ├── system.py              # 系统基类
│   │   ├── combat.py              # 战斗系统
│   │   ├── character.py           # 角色系统
│   │   ├── inventory.py           # 物品栏系统
│   │   ├── save_system.py         # 存档系统
│   │   └── resource_manager.py    # 资源管理
│   ├── content/
│   │   ├── __init__.py
│   │   ├── item_factory.py        # 物品工厂
│   │   ├── monster_factory.py     # 怪物工厂
│  _factory.py       # │   └── skill 技能工厂
│   ├── lua/
│   │   ├── __init__.py
│   │   ├── interpreter.py         # Lua解释器
│   │   └── content_loader.py      # 内容加载器
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── app.py                 # Textual主应用
│   │   ├── screens/
│   │   │   ├── __init__.py
│   │   │   ├── main_screen.py     # 主界面
│   │   │   ├── combat_screen.py   # 战斗界面
│   │   │   ├── map_screen.py      # 地图界面
│   │   │   ├── inventory_screen.py # 物品界面
│   │   │   ├── settings_screen.py # 设置界面
│   │   │   └── game_over_screen.py # 结束界面
│   │   └── components/
│   │       ├── __init__.py
│   │       ├── character_panel.py  # 角色面板
│   │       ├── combat_log.py       # 战斗日志
│   │       ├── minimap.py          # 小地图
│   │       └── dialog.py           # 对话框
│   └── utils/
│       ├── __init__.py
│       ├── logger.py              # 日志系统
│       ├── exceptions.py          # 自定义异常
│       └── helpers.py             # 工具函数
│
├── assets/
│   ├── lua/
│   │   ├── items.lua             # 物品定义
│   │   ├── monsters.lua          # 怪物模板
│   │   ├── skills.lua            # 技能定义
│   │   └── events.lua            # 事件定义
│   ├── themes/
│   │   ├── default.toml          # 默认主题
│   │   ├── dark.toml             # 暗色主题
│   │   └── retro.toml            # 复古主题
│   ├── sounds/                   # 音效文件
│   └── fonts/                    # 字体文件
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # pytest配置
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_git_parser.py
│   │   ├── test_combat.py
│   │   ├── test_character.py
│   │   ├── test_inventory.py
│   │   └── test_save_system.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_full_gameplay.py
│   │   └── test_save_load.py
│   ├── fuzzy/
│   │   ├── __init__.py
│   │   ├── test_random_actions.py
│   │   └── test_edge_cases.py
│   ├── content/
│   │   ├── __init__.py
│   │   └── test_lua_content.py
│   └── performance/
│       ├── __init__.py
│       ├── test_memory.py
│       └── test_performance.py
│
├── scripts/
│   ├── build.sh                 # 构建脚本
│   ├── test.sh                  # 测试脚本
│   ├── lint.sh                  # 代码检查
│   └── package.sh               # 打包脚本
│
├── docs/
│   ├── README.md
│   ├── ARCHITECTURE.md
│   ├── CONTENT_CREATION.md
│   ├── TESTING.md
│   └── API.md
│
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── Dockerfile
├── .gitignore
├── .pre-commit-config.yaml
└── LICENSE
```

---

## 8. 安装与运行

### 8.1 环境要求

- Python 3.11+
- Git
- 终端支持 (256色, 鼠标)

### 8.2 安装步骤

```bash
# 克隆项目
git clone https://github.com/yourusername/git-dungeon.git
cd git-dungeon

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
.\venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 运行游戏
python -m git_dungeon

# 运行测试
pytest tests/ -v
pytest tests/ --fuzzy  # 模糊测试
pytest tests/ -k "performance"  # 性能测试

# 代码检查
pre-commit run --all-files

# 构建
./scripts/build.sh
```

### 8.3 Docker 运行

```bash
# 构建镜像
docker build -t git-dungeon .

# 运行
docker run -it git-dungeon
```

---

## 9. CI/CD 流程

### 9.1 GitHub Actions 配置

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run unit tests
        run: pytest tests/unit/ -v
      - name: Run integration tests
        run: pytest tests/integration/ -v
      - name: Run fuzzy tests (30 seconds)
        run: timeout 35 pytest tests/fuzzy/ -v
      - name: Run performance tests
        run: pytest tests/performance/ -v
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run pre-commit
        uses: pre-commit/action@v3.0.1

  build:
    runs-on: ubuntu-latest
    needs: [test, lint]
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: ./scripts/build.sh
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: git-dungeon
          path: bin/
```

### 9.2 代码质量检查

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies:
          - types-all
```

---

## 10. MVP 里程碑

### Phase 1: 基础框架 (Week 1)

- [ ] Git 解析器
  - [ ] 解析单个 commit
  - [ ] 解析完整仓库历史
  - [ ] 支持资源限制
  - [ ] 单元测试 > 80%

- [ ] 基础游戏循环
  - [ ] 游戏状态管理
  - [ ] 输入处理
  - [ ] 渲染框架

- [ ] 终端UI框架
  - [ ] Textual 集成
  - [ ] 主界面布局
  - [ ] 导航系统

**交付物**: 可运行的原型，支持解析 Git 仓库并在终端显示

### Phase 2: 核心玩法 (Week 2)

- [ ] 战斗系统
  - [ ] 回合制战斗逻辑
  - [ ] 伤害计算
  - [ ] 技能系统
  - [ ] 战斗UI

- [ ] 角色系统
  - [ ] 玩家属性
  - [ ] 升级系统
  - [ ] 状态效果

- [ ] 物品系统
  - [ ] 物品生成
  - [ ] 物品栏管理
  - [ ] 物品使用

- [ ] 集成测试 > 90%

**交付物**: 完整的战斗系统，可玩的核心玩法

### Phase 3: 内容与扩展 (Week 3)

- [ ] Lua 内容系统
  - [ ] Lua 解释器集成
  - [ ] 内容加载器
  - [ ] 热重载支持

- [ ] 物品/怪物模板
  - [ ] 物品定义
  - [ ] 怪物模板
  - [ ] 技能定义

- [ ] 多主题支持
  - [ ] 主题系统
  - [ ] 默认主题
  - [ ] 暗色主题

- [ ] 内容测试 100%

**交付物**: 可扩展的内容系统，支持 Lua 脚本

### Phase 4: 完善与优化 (Week 4)

- [ ] 性能优化
  - [ ] 内存优化
  - [ ] 渲染优化
  - [ ] 加载优化

- [ ] 模糊测试
  - [ ] 随机操作测试
  - [ ] 边界情况测试
  - [ ] CI 集成

- [ ] 文档完善
  - [ ] API 文档
  - [ ] 用户文档
  - [ ] 开发者文档

- [ ] 打包发布
  - [ ] PyInstaller 打包
  - [ ] Docker 镜像
  - [ ] 发布流程

**交付物**: 可发布的完整版本

---

## 11. 参考项目

### 11.1 主要参考

| 项目 | GitHub | 亮点 |
|------|--------|------|
| **End of Eden** | BigJk/end_of_eden | Fuzzy测试、内容测试、Lua脚本、CI集成 |
| **GitType** | unhappychoice/gittype | 多语言支持、主题系统、产品化完善 |
| **Pokete** | lxgr-linux/pokete | 完整的类型系统、mod支持、文档完善 |

### 11.2 学习点

从 **End of Eden** 学习:
- 模糊测试实现
- Lua 内容分离
- CI/CD 集成

从 **GitType** 学习:
- 产品化流程
- 安装方式
- 配置系统

从 **Pokete** 学习:
- Python 架构设计
- 扩展性设计
- 文档结构

---

## 附录

### A. 配置默认值

```python
DEFAULT_CONFIG = GameConfig(
    repo_path="./",
    difficulty=Difficulty.NORMAL,
    max_commits=1000,
    max_files_per_commit=50,
    max_commit_message_len=500,
    max_memory_mb=100,
    cache_size=100,
    chunk_size=100,
    auto_save=True,
    auto_save_interval=10,
    show_combat_log=True,
    enable_sound=True,
    theme="default"
)
```

### B. 常见问题

Q: 为什么选择 Python 而不是 Go/Rust?
A: 开发效率优先，Python 有丰富的游戏开发库，且团队熟悉程度高。

Q: 为什么选择 Textual 而不是 ncurses?
A: Textual 更现代、GPU 加速、维护活跃、API 友好。

Q: 为什么用 Lua 而不是 JSON/YAML?
A: Lua 更灵活，支持逻辑判断，便于扩展。

### C. 后续规划

- Web 版本 (React + WebSocket)
- 移动端版本
- 多人模式
- 排行榜系统

---

> **注意**: 本文档为项目方案，后续开发请严格遵循。如需修改，请先讨论并更新文档。

**文档版本控制**:
- v1.0 (2026-01-31): 初始版本
