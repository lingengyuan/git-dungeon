# Phase 10 Handoff — 支线奖励房间

- **Phase**: `pixel-phase-10`
- **收口日期**: 2026-05-06
- **作者会话**: Codex + Hugh Lin
- **所属 plan**: [`plans/pixel-phases.md`](../plans/pixel-phases.md) §Phase 10
- **上一个 handoff**: [`2026-05-06-pixel-phase-9-handoff.md`](2026-05-06-pixel-phase-9-handoff.md)

---

## 1. 背景

Phase 7-9 已完成房间地牢、键盘移动、陷阱消耗和陷阱致死。当前地牢仍以线性 route 为核心，探索感有限。Phase 10 先做一个最小支线：在主路旁放一个可选奖励房间，让玩家可以离开主线领取一次补给，再返回当前节点。

**上游约束**：
- 不改变 CLI 自动主线路径。
- 不把奖励房间混入 route node。
- 奖励只能领取一次，不能反复刷 HP/Gold。
- 每个 phase 完成后必须写 handoff。

---

## 2. 目标

来自 `plans/pixel-phases.md` §Phase 10：

| 交付 | 状态 |
|---|---|
| `DungeonRewardRoom` 支线奖励房间 | ✅ |
| `DungeonFloor.reward_rooms` 不混入 route room | ✅ |
| 奖励房间参与门、移动、陷阱避让 | ✅ |
| `GameRunner` 记录每章已领取奖励 | ✅ |
| DungeonScreen 支持进入、领取、重复提示、回主线 | ✅ |
| Phase 10 测试覆盖 | ✅ |

**验收命令**（已执行）：

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase10.py -q
PYTHONPATH=src .venv/bin/python -m ruff check src/git_dungeon/ui_pixel tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/unit/test_pixel_phase10.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py
PYTHONPATH=src .venv/bin/python -m mypy src/git_dungeon/ui_pixel tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/unit/test_pixel_phase10.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py --ignore-missing-imports
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/unit/test_pixel_phase10.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-phase10-smoke PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --pixel-smoke-frames 8
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase1.py tests/unit/test_pixel_phase2.py tests/unit/test_pixel_phase3.py tests/unit/test_pixel_phase4.py tests/unit/test_pixel_phase5.py tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/unit/test_pixel_phase10.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
PYTHONPATH=src .venv/bin/python -m pytest tests/functional/ -q
PYTHONPATH=src .venv/bin/python -m pytest tests/golden_test.py -q
make smoke-install
.venv/bin/python -m PyInstaller --clean --noconfirm GitDungeon.spec
PYTHONPATH=src .venv/bin/python scripts/compare_run_metrics.py /tmp/git-dungeon-phase10-cli.json /tmp/git-dungeon-phase10-pyi.json
```

**验证结果**：

| 检查 | 结果 |
|---|---|
| Phase 10 单测 | `2 passed` |
| ruff | `All checks passed` |
| mypy | `Success: no issues found in 29 source files` |
| Phase 7-10 + smoke/parity | `14 passed` |
| Pixel Phase 1-10 + smoke/parity | `32 passed` |
| 快速全量回归 | `382 passed, 2 skipped, 153 deselected` |
| Functional | `133 passed` |
| Golden | `4 passed` |
| smoke-install | `Smoke demo passed` |
| PyInstaller | 构建成功，产物在 `dist/GitDungeon` |
| CLI vs PyInstaller metrics | `METRICS MATCH` |

---

## 3. 当前进度

- [x] **支线房间模型** — 新增 `DungeonRewardRoom`，包含 reward id、坐标、锚点、治疗量和金币。
- [x] **地牢布局** — `build_dungeon_floor()` 在主路第二个房间旁生成一个补给房间。
- [x] **门与陷阱避让** — 奖励房间通过门接入主路，陷阱不会生成在奖励房间上。
- [x] **一次性奖励** — `GameRunner` 记录每章已领取奖励，重复领取不给资源。
- [x] **交互闭环** — DungeonScreen 支持进入补给房间、Enter 领取、重复提示、回主线。
- [x] **计划更新** — `plans/pixel-phases.md` 和 `plans/dungeon-rooms-plan.md` 已补 Phase 10 状态。

---

## 4. 完成情况

### 4.1 实际交付物

| 路径 | 内容 |
|---|---|
| `src/git_dungeon/ui_pixel/dungeon.py` | 支线奖励房间模型和布局。 |
| `src/git_dungeon/ui_pixel/game_runner.py` | 一次性奖励领取接口和领取记录。 |
| `src/git_dungeon/ui_pixel/screens/dungeon.py` | 奖励房间绘制、进入、领取、重复提示和回主线。 |
| `src/git_dungeon/ui_pixel/text.py` | 奖励房间文案翻译。 |
| `tests/unit/test_pixel_phase10.py` | 支线奖励房间单元测试。 |
| `plans/pixel-phases.md` | Phase 10 行、范围、验收命令和变更记录。 |
| `plans/dungeon-rooms-plan.md` | 房间地牢计划补充 Phase 10 状态。 |
| `handoffs/2026-05-06-pixel-phase-10-handoff.md` | Phase 10 交接文档。 |

### 4.2 关键决策

#### 1. 奖励房间不混入 route node

route node 仍然是战斗、事件、休息、商店和 Boss 的唯一权威来源。奖励房间是地牢空间层的可选支线，不推进章节节点。

#### 2. 奖励只能领取一次

领取记录放在 `GameRunner`，并按章节隔离。这样 Screen 不直接改玩家资源，也避免重复刷 HP/Gold。

#### 3. 固定小分支，不做随机大地图

本阶段只做一个固定补给房间，便于测试和验证。更多分支、钥匙门和地图生成留后续 phase。

### 4.3 偏离原计划

| 原计划项 | 实际情况 | 原因 |
|---|---|---|
| “分支房间或旧地图清理” | 选择支线奖励房间 | 比清理旧 MapScreen 更能增加玩法价值，范围仍可控。 |
| “钥匙门” | 未做 | 钥匙门需要额外资源状态和门禁规则，留后续小闭环。 |

### 4.4 触发的项目原则

- **第一性原理**：先用一个可领取、可返回的小分支验证探索玩法。
- **DRY**：奖励领取由 `GameRunner` 统一记录，Screen 不直接改资源。
- **正交性**：奖励房间是地牢空间层，不改变 route 主线和自动通关。
- **禁止掩盖性质 fallback**：重复领取有明确提示，不静默失败。
- **Phase handoff**：本文件即 Phase 10 交接文档。

---

## 5. 后续任务

### 5.1 Phase 11 入口

建议下一个 phase 做 **`pixel-phase-11` — 旧地图清理或钥匙门**，二选一：

1. 清理旧 MapScreen，或把它改成明确的调试视图。
2. 加入钥匙门和更多可选分支，但仍复用现有节点结算。

### 5.2 已知风险与未决问题

| 风险 / 未决项 | 影响 | 处理建议 |
|---|---|---|
| 当前只有一个固定奖励房间 | 探索感仍有限 | 后续可加钥匙门或更多支线，但不要一次上随机大地图。 |
| 旧 MapScreen 仍保留 | 维护面稍大 | 明确删除或改为 debug view。 |
| 奖励数值固定为 12 HP / 15 Gold | 后续平衡空间有限 | 等分支稳定后，再按章节或难度调参。 |

### 5.3 新会话立刻要读哪些文件

1. `AGENTS.md`
2. `plans/pixel-phases.md`
3. `plans/dungeon-rooms-plan.md`
4. `handoffs/2026-05-06-pixel-phase-10-handoff.md`
5. `src/git_dungeon/ui_pixel/dungeon.py`
6. `src/git_dungeon/ui_pixel/game_runner.py`
7. `src/git_dungeon/ui_pixel/screens/dungeon.py`
8. `tests/unit/test_pixel_phase10.py`

### 5.4 推荐的第一条验证命令

```bash
cd /Users/hughlin/Projects/git-dungeon && \
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/unit/test_pixel_phase10.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
```

命令 exit 0，说明 Phase 7-10 的地牢入口、交互回放、陷阱、支线奖励和 CLI/Pixel parity 仍完好。
