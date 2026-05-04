# Phase 2 Handoff — 非战斗屏幕（Map / Rest / Event / Shop）

- **Phase**: `pixel-phase-2`
- **收口日期**: 2026-05-04
- **作者会话**: Codex + Hugh Lin
- **所属 plan**: [`plans/pixel-phases.md`](../plans/pixel-phases.md) §Phase 2
- **上一个 handoff**: [`2026-05-04-pixel-phase-1-handoff.md`](2026-05-04-pixel-phase-1-handoff.md)

---

## 1. 背景

Phase 2 要把 pixel 模式从“能启动和加载仓库”推进到“能显示路线，并处理非战斗节点”。本阶段只做 Map / Rest / Event / Shop，不做普通战斗、精英战、Boss 战，也不做完整一局。

**上游约束**：
- Screen 只能调用 `GameRunner`，不能直接 import `main_cli` 私有流程。
- Rest / Event / Shop 的状态变化必须和 CLI 使用同一套规则，不能在 UI 里重写一套看起来相同的逻辑。
- 节点图标必须走 sprite，禁止用 emoji 当图标。
- 买不起、不可用、错误状态必须可见，不能静默无效。
- Phase 完成后必须写 handoff，并回填 `plans/pixel-phases.md`。

---

## 2. 目标

来自 `plans/pixel-phases.md` §Phase 2：

| 交付 | 状态 |
|---|---|
| `screens/{map,rest,event,shop}.py` | ✅ |
| 节点图标用 sprite，禁止 emoji | ✅ |
| EventScreen / ShopScreen：买不起或 MP 不够时按钮灰显或明确提示 | ✅（Shop 已处理；Event 当前无 MP 消耗选项） |
| RestScreen：选项文案与实际效果一致，选择后展示真实变化 | ✅ |

**补齐 Phase 1 遗留项**：

| 遗留项 | 状态 |
|---|---|
| `window_to_logical(pos, window_size, logical_size)` | ✅ |
| `assets.py` / `widgets.py` 基础模块 | ✅ |
| Title / Loading 从 `app.py` 拆出 | ✅ |

**验收命令**（已执行）：
```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
  PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --pixel-smoke-frames 8

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase1.py tests/unit/test_pixel_phase2.py -q
PYTHONPATH=src .venv/bin/python -m ruff check src/git_dungeon/engine/node_actions.py src/git_dungeon/main_cli.py src/git_dungeon/ui_pixel tests/unit/test_pixel_phase1.py tests/unit/test_pixel_phase2.py
PYTHONPATH=src .venv/bin/python -m mypy src/git_dungeon/engine/node_actions.py src/git_dungeon/main_cli.py src/git_dungeon/ui_pixel tests/unit/test_pixel_phase1.py tests/unit/test_pixel_phase2.py --ignore-missing-imports

PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
PYTHONPATH=src .venv/bin/python -m pytest tests/functional/ -q
PYTHONPATH=src .venv/bin/python -m pytest tests/golden_test.py -q

.venv/bin/python scripts/verify_assets.py --strict
.venv/bin/python scripts/verify_audio.py
git diff --check
```

**结果**：
- Pixel smoke：通过，并且已真实加载仓库、进入 MapScreen。
- Pixel Phase 1/2 单测：`6 passed`。
- 快速测试：`349 passed, 2 skipped, 153 deselected`。
- Functional：`133 passed`。
- Golden：`4 passed`。
- Ruff / mypy / diff check：通过。
- 资源 / 音频严格校验：通过。

---

## 3. 当前进度

- [x] **共享非战斗规则** — 新增 `src/git_dungeon/engine/node_actions.py`，CLI 与 Pixel 共用 Event / Rest / Shop 规则。
- [x] **CLI 规则去重** — `main_cli.py` 的事件选择、休息、商店购买改为调用共享规则，输出保持原行为。
- [x] **GameRunner Phase 2 接口** — 支持 route nodes、当前节点、玩家快照、event/rest/shop resolve。
- [x] **坐标转换** — `window_to_logical()` 支持任意窗口比例和 letterbox，不写死 `// 4`。
- [x] **sprite catalog** — `assets.py` 读取 `assets/manifest_sprites.json`，缺映射或缺文件直接报错。
- [x] **widgets** — Button、panel、stat bar、文本 wrap 基础件。
- [x] **Title / Loading 拆分** — `screens/title.py`；headless smoke 直接进入 loading，能验证真实 repo 加载。
- [x] **MapScreen** — 显示路线、玩家 HP/MP/ATK/Gold、当前节点状态；只允许打开当前非战斗节点。
- [x] **RestScreen** — Heal / Focus 两个选项，文案展示真实效果，执行后回地图显示结果。
- [x] **EventScreen** — 显示 deterministic event 与 choices，选择后应用真实 effect 并回地图显示 HP/Gold 变化。
- [x] **ShopScreen** — 显示 deterministic offers；买不起的 Buy 按钮灰显，键盘选择买不起项只提示，不推进节点。
- [x] **测试覆盖** — `tests/unit/test_pixel_phase2.py` 覆盖坐标转换、Rest/Event/Shop 真实状态变化和买不起提示路径。
- [ ] **战斗 / 精英 / Boss 屏幕** — 未做，属于 Phase 3。

---

## 4. 完成情况

### 4.1 实际交付物

| 路径 | 内容 |
|---|---|
| `src/git_dungeon/engine/node_actions.py` | 非战斗节点共享规则：事件选择/应用、休息、商店 offer 和购买。 |
| `src/git_dungeon/main_cli.py` | Rest / Event / Shop 改为调用共享规则，避免 CLI 与 Pixel 分叉。 |
| `src/git_dungeon/ui_pixel/game_runner.py` | 增 route、player snapshot、event/rest/shop 操作接口。 |
| `src/git_dungeon/ui_pixel/layout.py` | `window_to_logical()` 与 letterbox scale rect。 |
| `src/git_dungeon/ui_pixel/assets.py` | sprite manifest 加载与绘制。 |
| `src/git_dungeon/ui_pixel/widgets.py` | Button、panel、stat bar、基础文本工具。 |
| `src/git_dungeon/ui_pixel/screens/title.py` | Title / Loading 屏幕。 |
| `src/git_dungeon/ui_pixel/screens/map.py` | 路线地图和当前非战斗节点入口。 |
| `src/git_dungeon/ui_pixel/screens/rest.py` | Rest 节点交互。 |
| `src/git_dungeon/ui_pixel/screens/event.py` | Event 节点交互。 |
| `src/git_dungeon/ui_pixel/screens/shop.py` | Shop 节点交互，含 disabled/提示状态。 |
| `tests/unit/test_pixel_phase2.py` | Phase 2 单测。 |

### 4.2 关键决策

#### 1. 抽 `engine/node_actions.py`，不让 Pixel 复制 CLI 私有逻辑

Phase 2 最容易出问题的是 CLI 与 Pixel 各自实现一套 Rest/Event/Shop，短期看起来一样，后续一定漂移。因此把非战斗规则下沉到共享模块，CLI 和 Pixel 都调用它。这样后续 parity 测试才有可靠基础。

#### 2. Map 只开放“当前非战斗节点”

路线生成仍然保持当前引擎顺序。MapScreen 会显示整条路线，但只允许打开当前未解决且属于 Event/Rest/Shop 的节点。当前节点如果是 Battle/Elite/Boss，会明确显示“Battle screens arrive in Phase 3”。这样不伪造战斗，也不允许玩家跳过路线乱改状态。

#### 3. Smoke 改为真实加载

Phase 1 的 smoke 只证明窗口能启动。Phase 2 后，`--pixel-smoke-frames` 会直接进入 LoadingScreen，加载真实 repo，再渲染 MapScreen。这个检查更接近实际启动路径。

#### 4. Shop 买不起不推进节点

CLI 自动模式遇到买不起会记录并继续；Pixel 交互里如果按钮灰显，用户不应该因为误按键盘就离开商店。因此 ShopScreen 对买不起项只提示，不调用 `GameRunner.resolve_current_shop()`，不会推进节点。

### 4.3 偏离原计划

| 原计划项 | 实际情况 | 原因 |
|---|---|---|
| “固定 seed 跑到四类节点，各自状态变化与 CLI auto 完全一致” | 非战斗规则已共享；单测用同一规则验证状态变化。Pixel UI 还不能通过战斗节点自然跑到后续节点。 | 战斗渲染和战斗推进属于 Phase 3。本阶段不伪造战斗，不跳过战斗节点。 |
| EventScreen / ShopScreen “MP 不够” | Shop 无 MP 消耗；Event 默认内容没有需要 MP 的 choice。 | 当前内容 schema 的 EventEffect 没有 MP cost 条件，本阶段无可测路径。保留“不可用必须可见”的 UI 规则。 |
| RestScreen “选择后展示真实变化” | 执行后回到 MapScreen，并在地图顶部显示结果，同时玩家 HP/ATK/Gold 真实刷新。 | 比停留在 RestScreen 更贴合当前路线推进。 |

这些偏离不影响 Phase 2 的交付目标，但 Phase 3 必须补战斗屏幕，否则 Pixel 仍不能完整跑一局。

### 4.4 触发的项目原则

- **DRY**：非战斗规则下沉到 `engine/node_actions.py`，CLI 和 Pixel 共用。
- **正交性**：Screen → GameRunner → engine/node_actions，Screen 不直接调 CLI。
- **ETC**：后续调整 Rest/Event/Shop 规则只改共享模块。
- **禁止掩盖性质 fallback**：sprite 缺失直接报错；商店买不起灰显并提示；错误不静默吞。
- **Phase handoff**：本文件即 Phase 2 交接文档。

### 4.5 审查结果

本阶段 diff 超过 10 个文件，按本地检查流程做了深度审查。发现并修正了一个交互问题：灰显 Shop Buy 按钮曾经仍可能被点击触发购买尝试，且操作结果直接回地图不够明确。现在灰显按钮不会触发，键盘选择买不起项只显示提示，Rest/Event/Shop 操作结果会回填到 MapScreen 顶部。

---

## 5. 后续任务

### 5.1 Phase 3 入口

下一个 phase：**`pixel-phase-3` — 战斗 & Boss**。

建议入口顺序：
1. 在 `GameRunner` 补当前 Battle/Elite/Boss 节点的战斗开始、玩家 action、敌人行动、战斗结束接口。
2. 新增 `screens/battle.py`，先做普通 Battle，再处理 Elite/Boss 差异。
3. BattleScreen 完成后，让 MapScreen 能自然推进 Battle → 后续 Event/Rest/Shop。
4. 补 CLI/Pixel parity 的战斗字段测试雏形，为 Phase 6 提前铺路。

### 5.2 已知风险与未决问题

| 风险 / 未决项 | 影响 | 处理建议 |
|---|---|---|
| Pixel 不能自然穿过战斗节点 | 当前路线经常第一节点就是 battle，用户还不能完整体验到后续非战斗节点 | Phase 3 必须优先做 BattleScreen 和战斗节点推进。 |
| `GameRunner` 仍缺完整一局循环 | Phase 6 parity 还无法跑完整 Pixel 自动一局 | Phase 3/4/5 后统一补 `--pixel --auto --headless`。 |
| `assets.py` 当前只支持开发模式项目根 | wheel / PyInstaller 资源定位还没做 | Phase 6 按 plan 补资源定位顺序。 |
| 中文像素字体还没接入 | zh_CN 下可能仍走 pygame 默认字体，中文不可读 | Phase 5 做字体和中文布局。 |

### 5.3 新会话立刻要读哪些文件

1. `AGENTS.md`
2. `plans/pixel-phases.md`
3. `handoffs/2026-05-04-pixel-phase-2-handoff.md`
4. `src/git_dungeon/ui_pixel/game_runner.py`
5. `src/git_dungeon/engine/node_actions.py`
6. `src/git_dungeon/ui_pixel/screens/map.py`
7. `src/git_dungeon/ui_pixel/screens/event.py`
8. `src/git_dungeon/ui_pixel/screens/rest.py`
9. `src/git_dungeon/ui_pixel/screens/shop.py`
10. `src/git_dungeon/main_cli.py` 的 `_resolve_combat_node()` / `_combat()` / `_resolve_boss_node()` 链路

### 5.4 推荐的第一条验证命令

```bash
cd /Users/hughlin/Projects/git-dungeon && \
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --pixel-smoke-frames 8 && \
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase1.py tests/unit/test_pixel_phase2.py -q
```

两条都 exit 0，说明 Pixel 加载、Map 渲染、非战斗节点规则仍完好。Phase 3 改完战斗后，再跑完整回归：

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
PYTHONPATH=src .venv/bin/python -m pytest tests/functional/ -q
PYTHONPATH=src .venv/bin/python -m pytest tests/golden_test.py -q
```
