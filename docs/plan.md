# Git Dungeon Roguelike - 项目方案 (Production-Grade vNext)

> 版本: 2.0
> 更新日期: 2026-02-01
> 作者: OpenClaw (claw)
> 状态: 待开发 (M0 进行中)

---

## 目录

1. [项目概述](#1-项目概述)
2. [架构设计](#2-架构设计)
3. [里程碑路线](#3-里程碑路线)
4. [目录结构](#4-目录结构)
5. [核心机制](#5-核心机制)
6. [质量保证](#6-质量保证)
7. [安装与运行](#7-安装与运行)
8. [附录](#8-附录)

---

## 1. 项目概述

### 1.1 愿景

将 Git 提交历史转化为一个有趣的肉鸽类地牢爬行游戏，让开发者通过游戏的方式回顾自己的代码历史。

**生产级目标**：
- **确定性**：相同仓库 + 相同 seed + 相同选择 → 结果一致
- **可测试**：核心规则 100% 可单测
- **可演进**：存档/内容版本化，规则可插拔
- **可观测**：结构化事件流，支持战斗回放

### 1.2 核心创意

```
真实 Git 仓库 → 游戏关卡

commit hash         → 关卡ID
commit message      → 怪物名称 + 挑战描述
代码变更 (+/- 行数) → 怪物属性（攻击力/防御力）
commit 作者         → BOSS 信息
改动的文件          → 掉落物品
merge commit        → 商店/休息点
revert commit       → BOSS 战
```

### 1.3 非功能需求

| 需求 | 说明 |
|------|------|
| 确定性 | 相同输入 → 相同输出（用于回归、平衡、debug） |
| 可测试 | 核心规则 100% 单测；大仓库有性能测试 |
| 可演进 | 存档版本化 + 迁移；内容可配置 |
| 可观测 | 结构化日志；战斗回放支持 |

### 1.4 可玩性需求

| 需求 | 说明 |
|------|------|
| 节奏 | 章节 → 精英 → BOSS → 结算 → 商店 → 下一章 |
| 反馈 | 每次战斗产出 EXP/金币/掉落/剧情碎片 |
| 差异 | 不同仓库玩起来像不同地牢 |

---

## 2. 架构设计

### 2.1 三层架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Git Dungeon Roguelike                     │
├─────────────────────────────────────────────────────────────────┤
│  UI Layer (表现层)                                               │
│  ├── CLI Renderer (CLI 输出)                                     │
│  └── TUI Renderer (Textual 界面)                                 │
│      └── 只订阅 GameEvent 渲染，不直接读写状态                   │
├─────────────────────────────────────────────────────────────────┤
│  Core Engine (纯逻辑层)                                          │
│  ├── model.py       - State, Enemy, Chapter (Pydantic/Dataclass)│
│  ├── events.py      - GameEvent 定义 (JSON 可序列化)             │
│  ├── rng.py         - 可注入 RNG (seed 支持)                     │
│  ├── engine.py      - apply(action, state) -> (new_state, events)│
│  └── rules/                                                    │
│       ├── combat_rules.py    - 战斗规则                          │
│       ├── loot_rules.py      - 掉落规则                          │
│       ├── chapter_rules.py   - 章节规则                          │
│       ├── economy_rules.py   - 经济规则                          │
│       └── progression_rules.py - 成长规则                        │
├─────────────────────────────────────────────────────────────────┤
│  Adapters (I/O 适配层)                                           │
│  ├── git_repo.py      - Git clone/open/parse                    │
│  ├── save_store.py    - 存档 + 版本迁移                          │
│  ├── content_loader.py - JSON/YAML/Lua 内容加载                  │
│  └── plugin_loader.py  - 插件加载                                │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 核心原则

1. **引擎纯逻辑**：不依赖 Rich/Textual，不打印，不读 stdin
2. **输入**：玩家指令 + 随机源 + 当前状态
3. **输出**：新状态 + 一串 `GameEvent[]`
4. **UI 只渲染事件**：CLI/TUI 订阅事件渲染

### 2.3 事件模型

所有玩法扩展（BOSS、商店、掉落、剧情）只要产出事件，就能被任何 UI 展示。

```python
# events.py - GameEvent 定义

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from datetime import datetime


class EventType(Enum):
    """事件类型"""
    BATTLE_STARTED = "battle_started"
    DAMAGE_DEALT = "damage_dealt"
    STATUS_APPLIED = "status_applied"
    EXP_GAINED = "exp_gained"
    LEVEL_UP = "level_up"
    ITEM_DROPPED = "item_dropped"
    GOLD_GAINED = "gold_gained"
    CHAPTER_CLEARED = "chapter_cleared"
    SHOP_ENTERED = "shop_entered"
    GAME_SAVED = "game_saved"
    GAME_LOADED = "game_loaded"
    ERROR = "error"


@dataclass
class GameEvent:
    """游戏事件基类（JSON 可序列化）"""
    type: EventType
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    data: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "timestamp": self.timestamp,
            "data": self.data
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "GameEvent":
        return cls(
            type=EventType(data["type"]),
            timestamp=data["timestamp"],
            data=data["data"]
        )


# 具体事件定义
@dataclass
class DamageDealt(GameEvent):
    """伤害事件"""
    src: str  # 攻击者 ID
    dst: str  # 目标 ID
    amount: int
    is_critical: bool = False
    is_evaded: bool = False
    
    def __post_init__(self):
        self.type = EventType.DAMAGE_DEALT


@dataclass
class ExpGained(GameEvent):
    """经验获取事件"""
    amount: int
    reason: str  # "enemy_defeated", "chapter_complete"
    
    def __post_init__(self):
        self.type = EventType.EXP_GAINED


@dataclass
class LevelUp(GameEvent):
    """升级事件"""
    new_level: int
    delta_stats: dict
    
    def __post_init__(self):
        self.type = EventType.LEVEL_UP


@dataclass
class ItemDropped(GameEvent):
    """物品掉落事件"""
    item_id: str
    item_name: str
    rarity: str  # common, rare, epic, legendary
    reason: str
    
    def __post_init__(self):
        self.type = EventType.ITEM_DROPPED


@dataclass
class ChapterCleared(GameEvent):
    """章节完成事件"""
    chapter_id: str
    chapter_name: str
    enemies_defeated: int
    gold_reward: int
    exp_reward: int
    
    def __post_init__(self):
        self.type = EventType.CHAPTER_CLEARED
```

### 2.4 RNG 系统

```python
# rng.py - 可注入 RNG

import random
from typing import Protocol, Any


class RNG(Protocol):
    """随机数生成器接口"""
    
    def random(self) -> float:
        """返回 [0, 1) 的随机浮点数"""
        ...
    
    def randint(self, low: int, high: int) -> int:
        """返回 [low, high] 的随机整数"""
        ...
    
    def choice(self, seq: list) -> Any:
        """从序列中随机选择一个元素"""
        ...
    
    def shuffle(self, seq: list) -> None:
        """打乱序列"""
        ...
    
    def seed(self, seed: int) -> None:
        """设置随机种子"""
        ...
    
    def get_state(self) -> dict:
        """获取随机状态（用于回放）"""
        ...
    
    @classmethod
    def from_state(cls, state: dict) -> "RNG":
        """从状态恢复随机数生成器"""
        ...


class DefaultRNG:
    """默认随机数生成器"""
    
    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)
    
    def random(self) -> float:
        return self._rng.random()
    
    def randint(self, low: int, high: int) -> int:
        return self._rng.randint(low, high)
    
    def choice(self, seq: list) -> Any:
        return self._rng.choice(seq)
    
    def shuffle(self, seq: list) -> None:
        self._rng.shuffle(seq)
    
    def seed(self, seed: int) -> None:
        self._rng.seed(seed)
    
    def get_state(self) -> dict:
        return {
            "state": self._rng.getstate()
        }
    
    @classmethod
    def from_state(cls, state: dict) -> "DefaultRNG":
        rng = cls()
        rng._rng.setstate(state["state"])
        return rng
```

### 2.5 引擎核心

```python
# engine.py - 核心引擎

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from dataclasses import dataclass, field

from .model import GameState, Action
from .events import GameEvent
from .rng import RNG


@dataclass
class Engine:
    """游戏引擎 - 纯逻辑层
    
    输入：玩家指令、随机源、当前状态
    输出：新状态 + 一串 GameEvent[]
    """
    
    rng: RNG
    save_version: int = 1
    
    def apply(
        self,
        state: GameState,
        action: Action
    ) -> Tuple[GameState, List[GameEvent]]:
        """应用动作，返回新状态和事件"""
        events = []
        
        # 分发到对应的规则处理器
        if action.type == "battle_action":
            new_state, battle_events = self._apply_battle_action(state, action)
            events.extend(battle_events)
        elif action.type == "shop_action":
            new_state, shop_events = self._apply_shop_action(state, action)
            events.extend(shop_events)
        elif action.type == "chapter_action":
            new_state, chapter_events = self._apply_chapter_action(state, action)
            events.extend(chapter_events)
        else:
            events.append(GameEvent(
                type=EventType.ERROR,
                data={"message": f"Unknown action type: {action.type}"}
            ))
            return state, events
        
        return new_state, events
    
    def _apply_battle_action(
        self,
        state: GameState,
        action: Action
    ) -> Tuple[GameState, List[GameEvent]]:
        """应用战斗动作"""
        # ... 调用 combat_rules.py
        pass
    
    def _apply_shop_action(
        self,
        state: GameState,
        action: Action
    ) -> Tuple[GameState, List[GameEvent]]:
        """应用商店动作"""
        # ... 调用 economy_rules.py
        pass
    
    def _apply_chapter_action(
        self,
        state: GameState,
        action: Action
    ) -> Tuple[GameState, List[GameEvent]]:
        """应用章节动作"""
        # ... 调用 chapter_rules.py
        pass
```

---

## 3. 里程碑路线

### M0 — 根治现有 bug + 引擎事件化 (P0，必须先做)

**目标**：EXP/升级必然生效；HP 显示问题消失；能够"回放一场战斗"。

**交付**：
- [ ] 引擎改为：`apply(action, state) -> (new_state, events[])`
- [ ] EXP/升级从"显示层修补"改为"规则层产出 ExpGained/LevelUp 事件"
- [ ] UI 渲染只读事件（CLI/TUI 同一套事件渲染接口）
- [ ] 引入 `--seed`，所有随机都来自注入的 RNG
- [ ] 存档版本化（`save_version` + migration pipeline）

**DoD**：
- [ ] 单测全绿（现有 5 个失败边界全部修掉）
- [ ] 添加 "golden replay test"：固定仓库 + 固定 seed + 固定选择序列 → 事件摘要一致
- [ ] 存档可跨版本加载（至少支持 v1->v2 一次迁移）

---

### M1 — 章节系统 (P0：可玩性闭环的节拍器)

**目标**：从"commit 列表刷怪"升级为"章节推进"，每章有开始/结算/奖励。

**章节切分策略**：
- Rule A：按 conventional commits（feat/fix/refactor/docs/test/chore…）聚合
- Rule B：若 message 不规范，按时间窗（例如每 N 天一章）
- Rule C：若 commit 极少，强制生成 1 章（避免空章节）

**章内结构**：
- 小怪（普通 commits）
- 精英（大 diff / 修改核心目录）
- 章 BOSS（先留接口，M2 补全）

**DoD**：
- [ ] 章节切分有明确单测：输入 commit 列表 → 输出章节结构稳定
- [ ] 每章结算必产出：金币/EXP/掉落至少一种（强反馈）

---

### M2 — BOSS (P1：高潮 + 仪式感)

**目标**：让 merge/revert 变成"记忆点"，不是一个标签。

**BOSS 类型**：
- Merge BOSS：两阶段（冲突阶段 / 合并完成阶段）
- Revert BOSS：会"反噬"（例如清除一个 buff、或降低金币收益）
- Mega-commit 精英：diff 超阈值触发 mini-boss

**DoD**：
- [ ] 至少 2 种 BOSS 行为脚本（不只是血厚）
- [ ] BOSS 必掉落稀有奖励（保证高潮反馈）

---

### M3 — 商店 + 经济系统 (P1：循环闭合)

**目标**：打怪的收益可消费，形成 build（构筑）空间。

**经济模型**：
- `gold`：章结算 + 掉落
- `shop`：章结算进入
- `price curve`：随章节递增，避免后期金币溢出

**DoD**：
- [ ] 至少 10 个商品（消耗品/永久提升/技能书）
- [ ] 购买行为产出事件（可回放、可测试）

---

### M4 — 掉落与物品 (P1：项目特色)

**目标**：文件变化→掉落，构成"这个仓库玩起来像什么"的差异。

**掉落映射**：
- docs 变更多：知识类道具（MP/经验增益）
- tests 变更多：防御类道具（DEF/抗性）
- src 核心模块变更：技能类道具（新技能/技能强化）
- 大 diff：高品质概率上升

**DoD**：
- [ ] rarity（common/rare/epic）与概率可控、可 seed 复现
- [ ] 道具可装备/可消耗，并影响战斗规则（不是摆设）

---

### M5 — Textual TUI (P1：体验升级)

**目标**：把信息呈现做"像游戏"，并保持 engine 纯净。

**实现原则**：
- Textual 是 event-driven + message pump，UI 更新基于事件/状态变化
- 引擎跑在后台任务里，UI 只消费事件队列

**DoD**：
- [ ] TUI 可完整通关（章节→战斗→商店→下一章）
- [ ] CLI 仍是稳定 fallback（回归测试走 CLI 更稳）

---

### M6 — 内容系统 (P2：Mod/可扩展生态)

**目标**：把"内容"从代码里拔出来。

**路线**：
- v1：章节定义、掉落表、商店表、剧情文本（JSON/YAML）
- v2：Lua（只用于行为脚本：BOSS AI/特殊事件）

---

## 4. 目录结构

```
git-dungeon/
├── src/
│   ├── git_dungeon/
│   │   ├── engine/                  # 纯逻辑：可单测、无 IO
│   │   │   ├── __init__.py
│   │   │   ├── model.py             # Pydantic/Dataclass: State, Enemy, Chapter...
│   │   │   ├── events.py            # GameEvent 定义
│   │   │   ├── rng.py               # 可注入 RNG（seed）
│   │   │   ├── engine.py            # apply(action, state) -> (state, events)
│   │   │   ├── replay.py            # events -> replay / assert helpers
│   │   │   └── rules/               # 规则
│   │   │       ├── __init__.py
│   │   │       ├── combat_rules.py  # 战斗规则
│   │   │       ├── loot_rules.py    # 掉落规则
│   │   │       ├── chapter_rules.py # 章节规则
│   │   │       ├── economy_rules.py # 经济规则
│   │   │       └── progression_rules.py  # 成长规则
│   │   │
│   │   ├── adapters/                # I/O 适配层
│   │   │   ├── __init__.py
│   │   │   ├── git_repo.py          # clone/open/parse
│   │   │   ├── save_store.py        # 存档 + 版本迁移
│   │   │   ├── content_loader.py    # json/yaml/lua 内容加载
│   │   │   └── plugin_loader.py     # entry points / lua hooks
│   │   │
│   │   ├── ui/                      # 表现层
│   │   │   ├── __init__.py
│   │   │   ├── cli_app.py           # CLI 应用
│   │   │   ├── tui_app.py           # Textual TUI 应用
│   │   │   └── renderers/           # 渲染器
│   │   │       ├── __init__.py
│   │   │       ├── cli_renderer.py  # CLI 渲染
│   │   │       └── tui_renderer.py  # TUI 渲染
│   │   │
│   │   └── main.py                  # 稳定入口（选择 CLI/TUI）
│   │
│   └── ...
│
├── content/                         # 游戏内容（JSON/YAML）
│   ├── chapters/
│   │   └── default.yaml
│   ├── items/
│   │   └── weapons.yaml
│   ├── loot_tables/
│   │   └── common.yaml
│   └── shops/
│       └── default.yaml
│
├── migrations/                      # 存档迁移脚本
│   ├── __init__.py
│   └── v1_to_v2.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── golden/                      # 回放测试
│   └── fuzz/
│
├── scripts/
│   ├── build.sh
│   └── test.sh
│
├── docs/
│   ├── plan.md
│   ├── ARCHITECTURE.md
│   └── API.md
│
├── pyproject.toml
├── pyinstaller.spec
└── requirements.txt
```

---

## 5. 核心机制

### 5.1 Git → 游戏元素映射

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

### 5.2 Git 命令 → 战斗技能

| Git 命令 | 游戏技能 | 效果 |
|----------|----------|------|
| git add <file> | 普通攻击 | 伤害 = 文件行数 |
| git commit -m "msg" | 必杀技 | 消耗MP，大伤害 |
| git push origin HEAD | 远程攻击 | 高伤害，可暴击 |
| git pull origin | 恢复 HP | 恢复一定生命值 |
| git stash | 护盾 | 抵挡一次攻击 |
| git reset --hard | 时间回溯 | 回到上一步状态 |
| git merge | 组合技 | 多个敌人同时攻击 |

### 5.3 存档结构

```python
@dataclass
class SaveData:
    """存档数据结构"""
    save_version: int = 2  # 当前版本
    game_version: str = "2.0.0"
    repo_fingerprint: str  # 仓库标识
    seed: int  # 随机种子
    created_at: str
    updated_at: str
    
    # 游戏状态
    state: GameState
    
    # 事件日志（用于回放）
    events: List[dict]
    
    # 校验
    checksum: str
    
    def validate(self) -> bool:
        """验证存档完整性"""
        return self.checksum == self._compute_checksum()
```

---

## 6. 质量保证

### 6.1 测试覆盖目标

| 模块 | 覆盖率要求 |
|------|------------|
| engine/ | >= 95% |
| rules/*.py | >= 90% |
| adapters/ | >= 80% |
| 整体 | >= 85% |

### 6.2 测试类型

1. **单元测试**：规则层逻辑
2. **集成测试**：完整流程
3. **Golden 测试**：固定 seed → 固定事件序列
4. **模糊测试**：随机操作序列

### 6.3 性能要求

| 场景 | 指标 |
|------|------|
| 大仓库解析 | 5k commits < 5s |
| 战斗响应 | < 100ms |
| 存档加载 | < 500ms |

### 6.4 兼容底线

- Git 解析失败必须给出可读错误（网络/权限/空仓库/无 HEAD）
- 大仓库解析必须有上限与缓存策略

---

## 7. 安装与运行

### 7.1 环境要求

- Python 3.11+
- Git
- uv (推荐) 或 pip

### 7.2 安装

```bash
# 使用 uv（推荐）
uv venv
source .venv/bin/activate
uv pip install -e .

# 或使用 pip
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 7.3 运行

```bash
# CLI 模式
python -m git_dungeon username/repo

# 带 seed（可复现）
python -m git_dungeon username/repo --seed 12345

# TUI 模式
textual run git_dungeon.main
```

### 7.4 测试

```bash
# 全部测试
pytest tests/ -v

# Golden 测试
pytest tests/golden/ -v

# 模糊测试
pytest tests/fuzz/ -v
```

---

## 8. 附录

### 8.1 技术栈

| 层级 | 技术选择 | 理由 |
|------|----------|------|
| 语言 | Python 3.11+ | 开发效率高、类型系统完善 |
| UI | Textual | 现代终端UI、GPU加速、事件驱动 |
| Git解析 | GitPython | 轻量、稳定 |
| 测试 | pytest | 成熟、插件丰富 |
| 打包 | PyInstaller | 跨平台支持 |

### 8.2 参考项目

| 项目 | GitHub | 亮点 |
|------|--------|------|
| End of Eden | gridbugs/end_of_eden | 模糊测试、内容测试、Lua脚本、CI集成 |
| Oh My Git! | ohmygit/oh-my-git | Git 游戏化、卡片系统 |
| Pokete | lxgr-linux/pokete | 完整的类型系统、mod支持 |

### 8.3 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0 | 2026-01-31 | 初始版本 |
| 2.0 | 2026-02-01 | 生产级重构：事件流、seed、存档迁移、章节系统 |

---

> **注意**：本项目采用渐进式开发，M0 为必须先完成的基础设施。M0 完成后，后续功能可独立迭代。

**文档版本**: 2.0
