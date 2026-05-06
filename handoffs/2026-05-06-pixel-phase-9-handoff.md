# Phase 9 Handoff — 地牢陷阱消耗

- **Phase**: `pixel-phase-9`
- **收口日期**: 2026-05-06
- **作者会话**: Codex + Hugh Lin
- **所属 plan**: [`plans/pixel-phases.md`](../plans/pixel-phases.md) §Phase 9
- **上一个 handoff**: [`2026-05-06-pixel-phase-8-handoff.md`](2026-05-06-pixel-phase-8-handoff.md)

---

## 1. 背景

Phase 7-8 已经完成房间地牢、键盘移动、节点进入和事件级回放测试。剩下的主要玩法空洞是陷阱只做提示和阻挡，没有真实资源代价。

Phase 9 的目标是把陷阱升级为明确、可预测、可测试的一次性 HP 消耗，同时不改主线节点、奖励、章节和 CLI 自动通关路径。

**上游约束**：
- 不新增第二套战斗、奖励或章节流程。
- 陷阱致死必须复用现有 Game Over 屏。
- 陷阱消耗必须可见，不允许静默扣血。
- 同一陷阱不能重复扣血。
- 每个 phase 完成后必须写 handoff。

---

## 2. 目标

来自 `plans/pixel-phases.md` §Phase 9：

| 交付 | 状态 |
|---|---|
| 陷阱固定伤害值 | ✅ |
| GameRunner 记录每章已触发陷阱 | ✅ |
| DungeonScreen 触发陷阱后显示实际 HP 损失 | ✅ |
| 同一陷阱再次触发不重复扣血 | ✅ |
| 低 HP 时触发陷阱会进入 Game Over | ✅ |
| Phase 9 测试覆盖 | ✅ |

**验收命令**（已执行）：

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py -q
PYTHONPATH=src .venv/bin/python -m ruff check src/git_dungeon/ui_pixel tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py
PYTHONPATH=src .venv/bin/python -m mypy src/git_dungeon/ui_pixel tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py --ignore-missing-imports
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-phase9-smoke PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --pixel-smoke-frames 8
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase1.py tests/unit/test_pixel_phase2.py tests/unit/test_pixel_phase3.py tests/unit/test_pixel_phase4.py tests/unit/test_pixel_phase5.py tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
PYTHONPATH=src .venv/bin/python -m pytest tests/functional/ -q
PYTHONPATH=src .venv/bin/python -m pytest tests/golden_test.py -q
make smoke-install
.venv/bin/python -m PyInstaller --clean --noconfirm GitDungeon.spec
set +e
PYTHONPATH=src .venv/bin/python -m git_dungeon . --seed 42 --auto --metrics-out /tmp/git-dungeon-phase9-cli.json --compact
cli_exit=$?
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy ./dist/GitDungeon . --pixel --auto --headless --seed 42 --metrics-out /tmp/git-dungeon-phase9-pyi.json
pyi_exit=$?
set -e
PYTHONPATH=src .venv/bin/python scripts/compare_run_metrics.py /tmp/git-dungeon-phase9-cli.json /tmp/git-dungeon-phase9-pyi.json
printf 'cli_exit=%s pyi_exit=%s\n' "$cli_exit" "$pyi_exit"
```

**阶段内结果**：
- Ruff / mypy：通过。
- Phase 8-9 重点测试：`6 passed`。
- Phase 7-9 + smoke/parity 重点测试：`12 passed`。
- Pixel dummy smoke：通过。
- Pixel Phase 1-9 重点测试：`30 passed`。
- 快速测试：`380 passed, 2 skipped, 153 deselected`。
- Functional：`133 passed`。
- Golden：`4 passed`。
- wheel 安装 smoke：通过。
- PyInstaller 构建：通过。
- CLI vs PyInstaller metrics：匹配（该 seed 自动通关结果为失败，CLI 和 PyInstaller 都返回 1，指标一致）。

---

## 3. 当前进度

- [x] **陷阱伤害** — `DungeonTrap` 现在带固定 `damage`。
- [x] **一次性触发** — `GameRunner` 记录每章已触发陷阱。
- [x] **真实 HP 消耗** — 触发陷阱会扣除玩家 HP，并显示实际损失。
- [x] **低血量边界** — 陷阱可以把玩家 HP 降到 0，并进入现有 Game Over 屏。
- [x] **交互测试** — 新增 Phase 9 测试，覆盖一次扣血和重复触发。
- [x] **计划更新** — `plans/pixel-phases.md` 和 `plans/dungeon-rooms-plan.md` 已补 Phase 9 状态。

---

## 4. 完成情况

### 4.1 实际交付物

| 路径 | 内容 |
|---|---|
| `src/git_dungeon/ui_pixel/dungeon.py` | 陷阱固定伤害值。 |
| `src/git_dungeon/ui_pixel/game_runner.py` | 陷阱触发记录和 HP 消耗接口。 |
| `src/git_dungeon/ui_pixel/screens/dungeon.py` | 陷阱触发反馈、已触发状态显示。 |
| `src/git_dungeon/ui_pixel/screens/game_over.py` | 陷阱致死时显示失败原因。 |
| `src/git_dungeon/ui_pixel/text.py` | 新增陷阱触发文案翻译。 |
| `tests/unit/test_pixel_phase8.py` | 更新陷阱反馈期望。 |
| `tests/unit/test_pixel_phase9.py` | 新增陷阱一次性消耗测试。 |
| `plans/pixel-phases.md` | Phase 9 行、范围、验收命令和变更记录。 |
| `plans/dungeon-rooms-plan.md` | 房间地牢计划补充 Phase 9 陷阱消耗完成状态。 |
| `handoffs/2026-05-06-pixel-phase-9-handoff.md` | Phase 9 交接文档。 |

### 4.2 关键决策

#### 1. 陷阱扣 HP，并复用现有失败页

陷阱会按真实伤害扣 HP。HP 归零时不新增第二套失败流程，直接进入现有 Game Over 屏。

#### 2. 同一陷阱只触发一次

这样玩家不会因为误按方向键被同一陷阱反复扣血。已触发陷阱仍保留在地图上，但会变成已消耗状态。

#### 3. 自动通关路径不改

Phase 9 的陷阱是玩家主动撞到支线格触发，不改变 route node 的主线推进，也不改 CLI 自动通关结果。

### 4.3 偏离原计划

| 原计划项 | 实际情况 | 原因 |
|---|---|---|
| “同步 CLI/Pixel parity” | 未新增 parity 字段；保留现有 CLI/Pixel 自动指标 | 陷阱是手动支线动作，不在当前自动主线路径中。现有 parity 测试仍覆盖自动通关不变。 |
| “地牢玩法扩展” | 只做陷阱消耗，不做分支/钥匙门 | 保持单 phase 小闭环，避免同时改地图结构和资源结算。 |

### 4.4 触发的项目原则

- **第一性原理**：先让陷阱有真实代价，再扩展更复杂地图。
- **DRY**：HP 消耗由 `GameRunner` 统一记录，Screen 不直接改角色状态。
- **正交性**：地牢层只触发消耗；战斗、奖励、章节仍走原流程。
- **禁止掩盖性质 fallback**：陷阱触发显示真实 HP 损失，致死时进入失败页，重复触发显示已触发。
- **Phase handoff**：本文件即 Phase 9 交接文档。

---

## 5. 后续任务

### 5.1 Phase 10 入口

建议下一个 phase 做 **`pixel-phase-10` — 分支房间或旧地图清理**，二选一：

1. 加入分支房间和可选奖励房间，但仍复用现有节点结算。
2. 清理旧 MapScreen，或把它改成明确的调试视图。

### 5.2 已知风险与未决问题

| 风险 / 未决项 | 影响 | 处理建议 |
|---|---|---|
| 地牢路径仍是线性 route 映射 | 探索感有限 | 下一阶段优先做小分支，不要直接上随机大地图。 |
| 旧 MapScreen 仍保留 | 维护面稍大 | 明确删除或改为 debug view。 |
| 陷阱伤害值固定为 8 | 后续平衡空间有限 | 等分支和奖励房间稳定后，再按章节或难度调参。 |

### 5.3 新会话立刻要读哪些文件

1. `AGENTS.md`
2. `plans/pixel-phases.md`
3. `plans/dungeon-rooms-plan.md`
4. `handoffs/2026-05-06-pixel-phase-9-handoff.md`
5. `src/git_dungeon/ui_pixel/dungeon.py`
6. `src/git_dungeon/ui_pixel/game_runner.py`
7. `src/git_dungeon/ui_pixel/screens/dungeon.py`
8. `tests/unit/test_pixel_phase9.py`

### 5.4 推荐的第一条验证命令

```bash
cd /Users/hughlin/Projects/git-dungeon && \
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
```

命令 exit 0，说明 Phase 7-9 的地牢入口、交互回放、陷阱消耗和 CLI/Pixel parity 仍完好。
