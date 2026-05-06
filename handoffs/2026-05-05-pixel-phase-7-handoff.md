# Phase 7 Handoff — 房间地牢化最小闭环

- **Phase**: `pixel-phase-7`
- **收口日期**: 2026-05-05
- **作者会话**: Codex + Hugh Lin
- **所属 plan**: [`plans/dungeon-rooms-plan.md`](../plans/dungeon-rooms-plan.md)
- **上一个 handoff**: [`2026-05-05-pixel-phase-6-handoff.md`](2026-05-05-pixel-phase-6-handoff.md)

---

## 1. 背景

Phase 7 要把 Pixel 版从静态路线节点推进到真正的房间探索体验。为了不破坏 Phase 6 已建立的 CLI/Pixel parity，本阶段先做“房间探索层”，不改战斗、奖励、章节和结算规则。

**上游约束**：
- 仍然复用现有 `GameRunner` 和 engine 结算。
- 不新增第二套战斗/奖励流程。
- 新增地牢外壳不能改变 CLI 自动模式结果。
- 每个 phase 完成后必须写 handoff。

---

## 2. 目标

来自 `plans/dungeon-rooms-plan.md`：

| 交付 | 状态 |
|---|---|
| 加载后进入房间地牢屏 | ✅ |
| route node 映射为房间，房间之间用门连接 | ✅ |
| 玩家用方向键/WASD 逐格移动 | ✅ |
| 到达当前房间后 Enter 进入现有节点流程 | ✅ |
| 显示可见陷阱格 | ✅ |
| 不改变 HP/Gold/EXP 和 CLI 结算 | ✅ |

**验收命令**（已执行）：

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-phase7-smoke \
PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --pixel-smoke-frames 8

PYTHONPATH=src .venv/bin/python -m ruff check src/git_dungeon/ui_pixel tests/unit/test_pixel_phase7.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py
PYTHONPATH=src .venv/bin/python -m mypy src/git_dungeon/ui_pixel tests/unit/test_pixel_phase7.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py --ignore-missing-imports
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase1.py tests/unit/test_pixel_phase2.py tests/unit/test_pixel_phase3.py tests/unit/test_pixel_phase4.py tests/unit/test_pixel_phase5.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
PYTHONPATH=src .venv/bin/python -m pytest tests/functional/ -q
PYTHONPATH=src .venv/bin/python -m pytest tests/golden_test.py -q
make smoke-install
.venv/bin/python -m PyInstaller --clean --noconfirm GitDungeon.spec
```

**阶段内结果**：
- Pixel dummy smoke：通过。
- Ruff / mypy：通过。
- Pixel Phase 1-7 重点测试：`24 passed`。
- 快速测试：`374 passed, 2 skipped, 153 deselected`。
- Functional：`133 passed`。
- Golden：`4 passed`。
- wheel 安装 smoke：通过。
- PyInstaller 构建和 headless smoke：通过。
- CLI vs Pixel headless metrics：匹配。
- CLI vs PyInstaller metrics：匹配。

---

## 3. 当前进度

- [x] **地牢数据模型** — `build_dungeon_floor()` 把 route nodes 转成房间、门和陷阱。
- [x] **房间探索屏** — 新增 `DungeonScreen`，支持键盘移动、进入当前房间、陷阱阻挡提示。
- [x] **入口切换** — LoadingScreen 加载完成后进入 DungeonScreen。
- [x] **节点回流** — Battle/Event/Rest/Shop 结束后回到 DungeonScreen。
- [x] **测试覆盖** — 新增 Phase 7 单元测试。
- [x] **打包声明** — PyInstaller spec 显式包含 dungeon 模块。

---

## 4. 完成情况

### 4.1 实际交付物

| 路径 | 内容 |
|---|---|
| `plans/dungeon-rooms-plan.md` | Phase 7 独立计划。 |
| `src/git_dungeon/ui_pixel/dungeon.py` | 地牢房间、门、陷阱的纯数据模型。 |
| `src/git_dungeon/ui_pixel/screens/dungeon.py` | 房间探索屏。 |
| `src/git_dungeon/ui_pixel/screens/title.py` | 加载后进入 DungeonScreen。 |
| `src/git_dungeon/ui_pixel/screens/{battle,event,rest,shop}.py` | 节点完成后回到 DungeonScreen。 |
| `src/git_dungeon/ui_pixel/text.py` | Phase 7 新 UI 文案。 |
| `tests/unit/test_pixel_phase7.py` | 房间顺序、当前房间、门、陷阱测试。 |
| `GitDungeon.spec` | 打包显式包含 dungeon 模块。 |

### 4.2 关键决策

#### 1. 陷阱先阻挡，不扣血

本阶段陷阱是可见障碍，不改变角色 HP。这样能先建立地牢空间感，又不破坏 Phase 6 已验证的 CLI/Pixel 指标一致性。后续如果要让陷阱扣血，需要同步更新 parity 规则和测试。

#### 2. route node 是房间的唯一权威来源

房间不是新生成一套玩法节点，而是从 `GameRunner.route_nodes()` 映射而来。这样当前节点、已访问节点、可进入节点仍由原流程决定。

#### 3. 保留旧 MapScreen

旧 MapScreen 暂时保留，避免一次性删除带来无关风险。默认入口已经切到 DungeonScreen，后续确认稳定后可清理旧屏幕。

### 4.3 偏离原计划

| 原计划项 | 实际情况 | 原因 |
|---|---|---|
| “真正的像素地牢化” | 完成最小房间探索闭环，不做大地图和自由分支 | 先保证移动、房间、门、陷阱、节点进入都成立。 |
| “陷阱” | 陷阱阻挡移动，不扣 HP | 避免改变核心结算和 Phase 6 parity。 |

### 4.4 触发的项目原则

- **第一性原理**：先做“房间移动到节点”的最小闭环，再考虑复杂地图。
- **DRY**：route node 仍是房间节点的唯一来源。
- **正交性**：地牢层只负责空间移动；战斗和结算仍交给原节点屏幕与 engine。
- **禁止掩盖性质 fallback**：无门、陷阱、未到当前房间都有明确提示。
- **Phase handoff**：本文件即 Phase 7 交接文档。

---

## 5. 后续任务

### 5.1 下一阶段入口

Phase 7 之后的交互打磨已作为 `pixel-phase-8` 收口。当前下一阶段建议进入 **Phase 9 — 地牢玩法扩展**：

1. 让陷阱变成可预测消耗，并同步 CLI/Pixel 指标规则。
2. 增加分支房间、钥匙门或可选奖励房间。
3. 清理旧 MapScreen 或把它改成调试视图。

### 5.2 已知风险与未决问题

| 风险 / 未决项 | 影响 | 处理建议 |
|---|---|---|
| 旧 MapScreen 还在代码中 | 维护面稍大 | Phase 9 删除或改为调试屏。 |
| 键盘移动事件级测试 | 已由 Phase 8 补齐 | 继续保留 `tests/unit/test_pixel_phase8.py` 作为回归保护。 |
| 陷阱只阻挡不扣血 | 玩法深度有限 | 下一步引入可预测消耗并同步 parity。 |

### 5.3 新会话立刻要读哪些文件

1. `AGENTS.md`
2. `plans/dungeon-rooms-plan.md`
3. `handoffs/2026-05-05-pixel-phase-7-handoff.md`
4. `src/git_dungeon/ui_pixel/dungeon.py`
5. `src/git_dungeon/ui_pixel/screens/dungeon.py`
6. `tests/unit/test_pixel_phase7.py`

### 5.4 推荐的第一条验证命令

```bash
cd /Users/hughlin/Projects/git-dungeon && \
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --pixel-smoke-frames 8 && \
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase7.py -q
```

两条都 exit 0，说明 Phase 7 的房间地牢入口和基础布局仍完好。

---

## 补遗（2026-05-06）

原「Phase 7.1 — 地牢交互打磨」已作为 `pixel-phase-8` 收口，详见 [`2026-05-06-pixel-phase-8-handoff.md`](2026-05-06-pixel-phase-8-handoff.md)。

已完成：
- UI 事件回放测试，覆盖移动到当前房间并进入节点。
- 陷阱提示的事件级测试。
- 节点回流后玩家位置保持测试。

仍留给后续 phase：
- 陷阱从阻挡升级为可预测消耗。
- 分支房间、钥匙门或可选奖励房间。
- 清理旧 MapScreen 或改为调试视图。
