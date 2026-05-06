# Phase 11 Handoff — 旧地图清理

- **Phase**: `pixel-phase-11`
- **收口日期**: 2026-05-06
- **作者会话**: Codex + Hugh Lin
- **所属 plan**: [`plans/pixel-phases.md`](../plans/pixel-phases.md) §Phase 11
- **上一个 handoff**: [`2026-05-06-pixel-phase-10-handoff.md`](2026-05-06-pixel-phase-10-handoff.md)

---

## 1. 背景

Phase 7 已把 Pixel 默认入口切到房间地牢屏，但 Phase 2 的旧 `MapScreen` 仍留在代码里。它不再是正式玩法路径，却继续保留一套路线展示、打开节点和旧文案，容易让后续维护误以为 Pixel 有两套地图入口。

**上游约束**：
- 不改变 CLI 自动模式结果。
- 不新增钥匙门或资源规则。
- 正式 Pixel 流程只保留 DungeonScreen。
- 每个 phase 完成后必须写 handoff。

---

## 2. 目标

来自 `plans/pixel-phases.md` §Phase 11：

| 交付 | 状态 |
|---|---|
| 删除旧 `MapScreen` 模块 | ✅ |
| 清理只服务旧路线图的文案和注释 | ✅ |
| 构建前清理旧产物，避免已删文件混入 wheel | ✅ |
| 加载后仍进入 DungeonScreen | ✅ |
| Phase 11 测试覆盖 | ✅ |
| 计划文档同步 | ✅ |

**验收命令**（已执行）：

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase11.py -q
PYTHONPATH=src .venv/bin/python -m ruff check src/git_dungeon/ui_pixel tests/unit/test_pixel_phase11.py
PYTHONPATH=src .venv/bin/python -m mypy src/git_dungeon/ui_pixel tests/unit/test_pixel_phase11.py --ignore-missing-imports
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/unit/test_pixel_phase10.py tests/unit/test_pixel_phase11.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-phase11-smoke PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --pixel-smoke-frames 8
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase1.py tests/unit/test_pixel_phase2.py tests/unit/test_pixel_phase3.py tests/unit/test_pixel_phase4.py tests/unit/test_pixel_phase5.py tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/unit/test_pixel_phase10.py tests/unit/test_pixel_phase11.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
PYTHONPATH=src .venv/bin/python -m pytest tests/functional/ -q
PYTHONPATH=src .venv/bin/python -m pytest tests/golden_test.py -q
make smoke-install
.venv-smoke/bin/python -c "import importlib.util; raise SystemExit(0 if importlib.util.find_spec('git_dungeon.ui_pixel.screens.map') is None else 1)"
.venv/bin/python -m PyInstaller --clean --noconfirm GitDungeon.spec
PYTHONPATH=src .venv/bin/python scripts/compare_run_metrics.py /tmp/git-dungeon-phase11-cli.json /tmp/git-dungeon-phase11-pyi.json
```

**验证结果**：

| 检查 | 结果 |
|---|---|
| Phase 11 单测 | `2 passed` |
| ruff | `All checks passed` |
| mypy | `Success: no issues found in 23 source files` |
| Phase 7-11 + smoke/parity | `16 passed` |
| Pixel Phase 1-11 + smoke/parity | `34 passed` |
| Pixel smoke 启动 | exit 0 |
| 快速全量回归 | `384 passed, 2 skipped, 153 deselected` |
| Functional | `133 passed` |
| Golden | `4 passed` |
| smoke-install | `Smoke demo passed` |
| 安装包旧模块检查 | `git_dungeon.ui_pixel.screens.map` 不存在 |
| PyInstaller | 构建成功，产物在 `dist/GitDungeon` |
| CLI vs PyInstaller metrics | `METRICS MATCH` |

---

## 3. 当前进度

- [x] **旧屏幕删除** — 删除 `src/git_dungeon/ui_pixel/screens/map.py`。
- [x] **入口确认** — LoadingScreen 仍直接进入 DungeonScreen。
- [x] **文案清理** — 删除只服务旧路线图的翻译项。
- [x] **注释清理** — `route_nodes()` 注释改为地牢屏用途。
- [x] **构建清理** — `build-wheel` 先删除旧 `build/` 和 `dist/`，避免已删除模块被旧构建目录带回 wheel。
- [x] **测试覆盖** — 新增 Phase 11 测试，覆盖旧模块不存在和加载入口。
- [x] **计划更新** — `plans/pixel-phases.md` 和 `plans/dungeon-rooms-plan.md` 已补 Phase 11 状态。

---

## 4. 完成情况

### 4.1 实际交付物

| 路径 | 内容 |
|---|---|
| `src/git_dungeon/ui_pixel/screens/map.py` | 已删除旧路线图屏幕。 |
| `src/git_dungeon/ui_pixel/text.py` | 清理旧路线图专用文案。 |
| `src/git_dungeon/ui_pixel/game_runner.py` | 更新 `route_nodes()` 注释。 |
| `Makefile` | 构建 wheel 前清理旧构建产物。 |
| `tests/unit/test_pixel_phase11.py` | 覆盖旧模块删除和加载后进入 DungeonScreen。 |
| `plans/pixel-phases.md` | Phase 11 行、范围、验收命令和变更记录。 |
| `plans/dungeon-rooms-plan.md` | 房间地牢计划补充 Phase 11 状态。 |
| `handoffs/2026-05-06-pixel-phase-11-handoff.md` | Phase 11 交接文档。 |

### 4.2 关键决策

#### 1. 删除旧屏幕，不保留调试入口

旧 MapScreen 已没有正式路径。继续保留调试入口会留下第二套节点打开逻辑，不符合单一入口和 DRY。

#### 2. 不做钥匙门

钥匙门会新增资源状态、门禁规则和更多支线，适合单独作为 Phase 12，不和清理工作混在一起。

#### 3. 用测试锁定入口

Phase 11 测试明确要求旧模块不存在，同时确认加载仓库后仍进入 DungeonScreen，防止以后误恢复旧入口。

#### 4. 构建前清理旧产物

首次安装验证发现旧 `build/` 目录会把已删除的 `map.py` 带回 wheel。`build-wheel` 现在先清理 `build/` 和 `dist/`，并用安装后的 Python 明确检查旧模块不存在。

### 4.3 偏离原计划

| 原计划项 | 实际情况 | 原因 |
|---|---|---|
| “旧地图清理或钥匙门” | 只做旧地图清理 | 清理维护面更小，也为后续钥匙门留出干净入口。 |
| “改成调试视图” | 未保留 | 调试视图会继续维护第二套地图展示，当前没有真实需求。 |

### 4.4 触发的项目原则

- **第一性原理**：正式 Pixel 地图已经是房间地牢，旧路线图不是必要环节。
- **DRY**：删除第二套路线展示和打开节点逻辑。
- **正交性**：只清理 UI 层遗留，不改 engine 和 CLI。
- **ETC**：后续地图玩法只需要改 DungeonScreen 一条路径。
- **Phase handoff**：本文件即 Phase 11 交接文档。

---

## 5. 后续任务

### 5.1 Phase 12 入口

建议下一个 phase 做 **`pixel-phase-12` — 钥匙门或更多支线**：

1. 在现有 `DungeonFloor` 上增加钥匙门或第二个可选分支。
2. 继续保持 route 主线和 CLI 自动结果不变。
3. 奖励、钥匙、陷阱都必须一次性结算，不能反复刷资源。

### 5.2 已知风险与未决问题

| 风险 / 未决项 | 影响 | 处理建议 |
|---|---|---|
| 当前只有一个固定奖励房间 | 探索感仍有限 | Phase 12 可加钥匙门或更多支线。 |
| 奖励和陷阱数值固定 | 后续平衡空间有限 | 等更多分支稳定后统一调参。 |
| 老 handoff 仍会提到历史 MapScreen | 只作为历史记录 | 新会话以最新 handoff 和 plan 为准。 |

### 5.3 新会话立刻要读哪些文件

1. `AGENTS.md`
2. `plans/pixel-phases.md`
3. `plans/dungeon-rooms-plan.md`
4. `handoffs/2026-05-06-pixel-phase-11-handoff.md`
5. `src/git_dungeon/ui_pixel/dungeon.py`
6. `src/git_dungeon/ui_pixel/screens/dungeon.py`
7. `tests/unit/test_pixel_phase11.py`

### 5.4 推荐的第一条验证命令

```bash
cd /Users/hughlin/Projects/git-dungeon && \
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/unit/test_pixel_phase10.py tests/unit/test_pixel_phase11.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
```

命令 exit 0，说明 Phase 7-11 的地牢入口、交互回放、陷阱、支线奖励、旧地图清理和 CLI/Pixel parity 仍完好。
