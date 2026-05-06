# Phase 12 Handoff — 钥匙门支线

- **Phase**: `pixel-phase-12`
- **收口日期**: 2026-05-06
- **作者会话**: Codex + Hugh Lin
- **所属 plan**: [`plans/pixel-phases.md`](../plans/pixel-phases.md) §Phase 12
- **上一个 handoff**: [`2026-05-06-pixel-phase-11-handoff.md`](2026-05-06-pixel-phase-11-handoff.md)

---

## 1. 背景

Phase 10 已有一个可选补给房，但探索仍只是“进去领奖再回来”。Phase 12 增加一个最小钥匙门闭环：玩家先离开主路进入钥匙房，拿到钥匙后才能进入锁住的宝库领奖。这个玩法只发生在手动地牢探索层，不改变主线 route 和 CLI 自动模式。

**上游约束**：
- 不改变 CLI 自动模式结果。
- 不生成随机大地图。
- 钥匙和宝库奖励不能反复刷。
- 每个 phase 完成后必须写 handoff。

---

## 2. 目标

来自 `plans/pixel-phases.md` §Phase 12：

| 交付 | 状态 |
|---|---|
| `DungeonRewardRoom` 支持发钥匙和钥匙要求 | ✅ |
| `GameRunner` 按章节记录已领取钥匙 | ✅ |
| DungeonScreen 未拿钥匙时阻止进入宝库 | ✅ |
| DungeonScreen 支持钥匙领取、宝库领取、重复提示 | ✅ |
| Phase 12 测试覆盖 | ✅ |
| 计划文档同步 | ✅ |

**验收命令**（已执行）：

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase10.py tests/unit/test_pixel_phase12.py -q
PYTHONPATH=src .venv/bin/python -m ruff check src/git_dungeon/ui_pixel tests/unit/test_pixel_phase10.py tests/unit/test_pixel_phase12.py
PYTHONPATH=src .venv/bin/python -m mypy src/git_dungeon/ui_pixel tests/unit/test_pixel_phase10.py tests/unit/test_pixel_phase12.py --ignore-missing-imports
PYTHONPATH=src .venv/bin/python -m ruff check src/git_dungeon/ui_pixel tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/unit/test_pixel_phase10.py tests/unit/test_pixel_phase11.py tests/unit/test_pixel_phase12.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py
PYTHONPATH=src .venv/bin/python -m mypy src/git_dungeon/ui_pixel tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/unit/test_pixel_phase10.py tests/unit/test_pixel_phase11.py tests/unit/test_pixel_phase12.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py --ignore-missing-imports
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/unit/test_pixel_phase10.py tests/unit/test_pixel_phase11.py tests/unit/test_pixel_phase12.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-phase12-smoke PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --pixel-smoke-frames 8
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase1.py tests/unit/test_pixel_phase2.py tests/unit/test_pixel_phase3.py tests/unit/test_pixel_phase4.py tests/unit/test_pixel_phase5.py tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/unit/test_pixel_phase10.py tests/unit/test_pixel_phase11.py tests/unit/test_pixel_phase12.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
PYTHONPATH=src .venv/bin/python -m pytest tests/functional/ -q
PYTHONPATH=src .venv/bin/python -m pytest tests/golden_test.py -q
make smoke-install
.venv/bin/python -m PyInstaller --clean --noconfirm GitDungeon.spec
PYTHONPATH=src .venv/bin/python scripts/compare_run_metrics.py /tmp/git-dungeon-phase12-cli.json /tmp/git-dungeon-phase12-pyi.json
```

**验证结果**：

| 检查 | 结果 |
|---|---|
| Phase 10 + Phase 12 单测 | `4 passed` |
| ruff | `All checks passed` |
| mypy | `Success: no issues found in 24 source files` |
| Phase 7-12 + smoke/parity | `18 passed` |
| Pixel Phase 1-12 + smoke/parity | `36 passed` |
| Pixel smoke 启动 | exit 0 |
| 快速全量回归 | `386 passed, 2 skipped, 153 deselected` |
| Functional | `133 passed` |
| Golden | `4 passed` |
| smoke-install | `Smoke demo passed` |
| PyInstaller | 构建成功，产物在 `dist/GitDungeon` |
| CLI vs PyInstaller metrics | `METRICS MATCH` |

---

## 3. 当前进度

- [x] **钥匙房模型** — `DungeonRewardRoom.grants_key` 支持领取钥匙。
- [x] **宝库模型** — `DungeonRewardRoom.requires_key` 支持锁住房间。
- [x] **地牢布局** — 主路旁新增钥匙房和宝库，仍避开 route room 和陷阱。
- [x] **一次性钥匙** — `GameRunner` 按章节记录已领取钥匙。
- [x] **门禁交互** — 未拿钥匙时无法进入宝库，并显示明确提示。
- [x] **宝库奖励** — 拿到钥匙后可进入宝库并领取一次 HP/Gold。
- [x] **测试覆盖** — `tests/unit/test_pixel_phase12.py` 覆盖完整闭环。
- [x] **计划更新** — `plans/pixel-phases.md` 和 `plans/dungeon-rooms-plan.md` 已补 Phase 12 状态。

---

## 4. 完成情况

### 4.1 实际交付物

| 路径 | 内容 |
|---|---|
| `src/git_dungeon/ui_pixel/dungeon.py` | 奖励房间支持钥匙/锁，新增钥匙房和宝库布局。 |
| `src/git_dungeon/ui_pixel/game_runner.py` | 记录已领取钥匙，奖励领取接口可发钥匙。 |
| `src/git_dungeon/ui_pixel/screens/dungeon.py` | 未拿钥匙阻挡、钥匙领取、宝库领取和重复提示。 |
| `src/git_dungeon/ui_pixel/text.py` | 钥匙、宝库、锁门提示的中文文案。 |
| `tests/unit/test_pixel_phase10.py` | 适配奖励领取接口新增钥匙参数。 |
| `tests/unit/test_pixel_phase12.py` | 钥匙门支线单元测试。 |
| `plans/pixel-phases.md` | Phase 12 行、范围、验收命令和变更记录。 |
| `plans/dungeon-rooms-plan.md` | 房间地牢计划补充 Phase 12 状态。 |
| `handoffs/2026-05-06-pixel-phase-12-handoff.md` | Phase 12 交接文档。 |

### 4.2 关键决策

#### 1. 复用奖励房间模型

钥匙房和宝库本质都是“可选支线房间”。直接扩展 `DungeonRewardRoom` 比新增第二套房间模型更简单，也避免重复门、移动和领取逻辑。

#### 2. 钥匙按章节隔离

钥匙记录放在 `GameRunner`，并和陷阱/奖励一样按当前章节生成 key。这样不会出现上一章钥匙打开下一章宝库的问题。

#### 3. 未拿钥匙不能进入宝库

门禁发生在移动前。玩家不会被移动到锁住房间后再失败，提示也不会被“无门”信息掩盖。

### 4.3 偏离原计划

| 原计划项 | 实际情况 | 原因 |
|---|---|---|
| “钥匙门或更多支线” | 只做一个钥匙房 + 一个锁住宝库 | 保持 Phase 小闭环，避免一次引入随机地图或多分支生成。 |
| “更多支线形状” | 未做 | 需要更多布局规则，留到钥匙门稳定后再扩展。 |

### 4.4 触发的项目原则

- **第一性原理**：钥匙门闭环只需要钥匙来源、门禁检查、锁后奖励三个环节。
- **DRY**：钥匙房和宝库复用奖励房间、门、移动和领取机制。
- **正交性**：钥匙门只影响手动地牢探索，不影响 route 主线和 CLI。
- **禁止掩盖性质 fallback**：未拿钥匙时明确提示锁门，不静默失败。
- **Phase handoff**：本文件即 Phase 12 交接文档。

---

## 5. 后续任务

### 5.1 Phase 13 入口

建议下一个 phase 做 **`pixel-phase-13` — 支线打磨或章节化数值**：

1. 钥匙门/宝库增加更清楚的视觉区分。
2. 按章节或难度调整补给、宝库和陷阱数值。
3. 继续保持 CLI 自动结果不变。

### 5.2 已知风险与未决问题

| 风险 / 未决项 | 影响 | 处理建议 |
|---|---|---|
| 钥匙房和宝库位置固定 | 长局可预测 | 后续可做有限布局变体，但先保持 deterministic。 |
| 钥匙和宝库共用商店图标 | 视觉区分不强 | 后续可补专门 sprite 或图标映射。 |
| 奖励/陷阱数值固定 | 平衡空间有限 | Phase 13 可章节化调参。 |

### 5.3 新会话立刻要读哪些文件

1. `AGENTS.md`
2. `plans/pixel-phases.md`
3. `plans/dungeon-rooms-plan.md`
4. `handoffs/2026-05-06-pixel-phase-12-handoff.md`
5. `src/git_dungeon/ui_pixel/dungeon.py`
6. `src/git_dungeon/ui_pixel/game_runner.py`
7. `src/git_dungeon/ui_pixel/screens/dungeon.py`
8. `tests/unit/test_pixel_phase12.py`

### 5.4 推荐的第一条验证命令

```bash
cd /Users/hughlin/Projects/git-dungeon && \
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/unit/test_pixel_phase10.py tests/unit/test_pixel_phase11.py tests/unit/test_pixel_phase12.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
```

命令 exit 0，说明 Phase 7-12 的地牢入口、交互回放、陷阱、支线奖励、旧地图清理、钥匙门和 CLI/Pixel parity 仍完好。
