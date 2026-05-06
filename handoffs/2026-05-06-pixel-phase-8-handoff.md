# Phase 8 Handoff — 地牢交互打磨 & 回放测试

- **Phase**: `pixel-phase-8`
- **收口日期**: 2026-05-06
- **作者会话**: Codex + Hugh Lin
- **所属 plan**: [`plans/pixel-phases.md`](../plans/pixel-phases.md) §Phase 8
- **上一个 handoff**: [`2026-05-05-pixel-phase-7-handoff.md`](2026-05-05-pixel-phase-7-handoff.md)

---

## 1. 背景

Phase 7 已经把 Pixel 版入口切到房间地牢屏，完成了房间、门、逐格移动、陷阱阻挡和节点进入的最小闭环。但 Phase 7 的自动测试主要覆盖地牢数据模型，真实 Screen 输入链路仍缺少回放测试。

Phase 8 的目标是先把“玩家通过键盘走到当前房间，再进入原节点流程”这条核心操作链路固定住，不急着扩大玩法规则。

**上游约束**：
- 不改变 CLI 自动模式结果。
- 不新增第二套战斗、奖励、章节或结算规则。
- 陷阱仍只阻挡移动，不扣 HP。
- 每个 phase 完成后必须写 handoff。

---

## 2. 目标

来自 `plans/pixel-phases.md` §Phase 8：

| 交付 | 状态 |
|---|---|
| 事件级键盘回放测试 | ✅ |
| 覆盖“未到当前房间不能进入” | ✅ |
| 覆盖“移动到当前房间后 Enter 进入节点” | ✅ |
| 覆盖陷阱优先提示 | ✅ |
| 覆盖节点回流后玩家位置保持 | ✅ |
| 不改变 HP/Gold/EXP 和 CLI/Pixel parity | ✅ |

**验收命令**（已执行）：

```bash
PYTHONPATH=src .venv/bin/python -m ruff check src/git_dungeon/ui_pixel tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py
PYTHONPATH=src .venv/bin/python -m mypy src/git_dungeon/ui_pixel tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py --ignore-missing-imports
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-phase8-smoke PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --pixel-smoke-frames 8
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase1.py tests/unit/test_pixel_phase2.py tests/unit/test_pixel_phase3.py tests/unit/test_pixel_phase4.py tests/unit/test_pixel_phase5.py tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
PYTHONPATH=src .venv/bin/python -m pytest tests/functional/ -q
PYTHONPATH=src .venv/bin/python -m pytest tests/golden_test.py -q
make smoke-install
```

**阶段内结果**：
- Ruff / mypy：通过。
- Pixel dummy smoke：通过。
- Phase 7-8 + smoke/parity 重点测试：`9 passed`。
- Pixel Phase 1-8 重点测试：`27 passed`。
- 快速测试：`377 passed, 2 skipped, 153 deselected`。
- Functional：`133 passed`。
- Golden：`4 passed`。
- wheel 安装 smoke：通过。

---

## 3. 当前进度

- [x] **键盘移动回放** — 新增测试模拟方向键输入，验证玩家从起点走到当前房间。
- [x] **进入节点回放** — 未到当前房间按 Enter 不进入；到达后按 Enter 进入原节点屏幕。
- [x] **陷阱反馈** — 走向陷阱时保留明确陷阱提示，不退化成普通无门提示。
- [x] **位置保持** — DungeonScreen 重新创建时复用上一房间位置。
- [x] **计划更新** — `plans/pixel-phases.md` 和 `plans/dungeon-rooms-plan.md` 已补 Phase 8 状态。
- [x] **交接文档** — 本文件即 Phase 8 handoff。

---

## 4. 完成情况

### 4.1 实际交付物

| 路径 | 内容 |
|---|---|
| `tests/unit/test_pixel_phase8.py` | 地牢 Screen 事件回放测试。 |
| `plans/pixel-phases.md` | Phase 8 行、范围、验收命令和变更记录。 |
| `plans/dungeon-rooms-plan.md` | 房间地牢计划补充 Phase 8 交互打磨完成状态。 |
| `handoffs/2026-05-06-pixel-phase-8-handoff.md` | Phase 8 交接文档。 |

### 4.2 关键决策

#### 1. Phase 8 只补交互可靠性，不扩玩法

Phase 7 handoff 提到了陷阱扣血、钥匙门、分支奖励房间等方向。但这些都会影响核心结算或扩大地图规则。Phase 8 先把当前真实操作链路测稳，避免在未锁住基础交互时继续加玩法。

#### 2. UI 回放测试直接驱动 Screen 输入

新增测试不是只调用地牢数据模型，而是构造键盘事件交给 `DungeonScreen.handle()`。这样能覆盖玩家实际操作路径：不能进入、移动、进入节点、陷阱提示、位置保持。

#### 3. 陷阱继续阻挡，不扣血

这与 Phase 7 一致。陷阱扣血会改变 HP 和结算指标，必须在未来 phase 同步 CLI/Pixel parity 后再做。

### 4.3 偏离原计划

| 原计划项 | 实际情况 | 原因 |
|---|---|---|
| “Phase 7.1 地牢交互打磨” | 收口为 `pixel-phase-8` | 项目当前按 phase 编号递进，避免 handoff 和计划索引出现半号。 |
| “让陷阱变成可预测消耗” | 未做 | 会改变 HP/parity，留给后续玩法 phase。 |
| “清理旧 MapScreen” | 未做 | 默认入口已是 DungeonScreen；清理旧屏幕不是 Phase 8 交互验证的必要条件。 |

### 4.4 触发的项目原则

- **第一性原理**：先验证最核心的玩家动作闭环，再扩展地图玩法。
- **正交性**：Phase 8 只碰 Pixel UI 测试和计划文档，不改 engine / CLI 流程。
- **禁止掩盖性质 fallback**：陷阱、无门、未到当前房间仍有明确提示。
- **Phase handoff**：本文件即 Phase 8 交接文档。

---

## 5. 后续任务

### 5.1 Phase 9 入口

建议下一个 phase 做 **`pixel-phase-9` — 地牢玩法扩展**，从以下三项里选一个小闭环：

1. 陷阱变成明确的可预测消耗，并同步 CLI/Pixel 指标规则。
2. 加入分支房间和可选奖励房间，但仍复用现有节点结算。
3. 清理旧 MapScreen，或把它改成明确的调试视图。

### 5.2 已知风险与未决问题

| 风险 / 未决项 | 影响 | 处理建议 |
|---|---|---|
| 陷阱还没有资源消耗 | 玩法深度有限 | Phase 9 如果做陷阱扣血，必须同步更新 parity 和指标测试。 |
| 地牢路径仍是线性 route 映射 | 探索感有限 | 先做可选分支，不要直接上随机大地图。 |
| 旧 MapScreen 仍保留 | 维护面稍大 | 下一阶段确认是删除，还是改为 debug view。 |

### 5.3 新会话立刻要读哪些文件

1. `AGENTS.md`
2. `plans/pixel-phases.md`
3. `plans/dungeon-rooms-plan.md`
4. `handoffs/2026-05-06-pixel-phase-8-handoff.md`
5. `src/git_dungeon/ui_pixel/dungeon.py`
6. `src/git_dungeon/ui_pixel/screens/dungeon.py`
7. `tests/unit/test_pixel_phase8.py`

### 5.4 推荐的第一条验证命令

```bash
cd /Users/hughlin/Projects/git-dungeon && \
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
```

命令 exit 0，说明 Phase 7-8 的地牢入口、交互回放和 CLI/Pixel parity 仍完好。
