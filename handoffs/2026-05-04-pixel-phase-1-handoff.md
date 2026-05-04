# Phase 1 Handoff — GameRunner & `--pixel` 入口

- **Phase**: `pixel-phase-1`
- **收口日期**: 2026-05-04
- **作者会话**: Codex + Hugh Lin
- **所属 plan**: [`plans/pixel-phases.md`](../plans/pixel-phases.md) §Phase 1
- **上一个 handoff**: [`2026-05-04-pixel-phase-0-handoff.md`](2026-05-04-pixel-phase-0-handoff.md)

---

## 1. 背景

Phase 1 要把像素模式从计划推进到可启动状态：保留现有 CLI 路径不变，同时新增 `--pixel` 入口，让后续屏幕都能围绕一个无 `print/input` 的 `GameRunner` 接入现有仓库加载和章节生成流程。

**上游约束**：
- CLI 仍是主路径，`--pixel` 只能新增分支，不能破坏原 `--auto` / `--ai` / `--lang` 行为。
- Screen 只能依赖 `GameRunner`，不允许反向调用 `main_cli` 私有流程。
- 本阶段优先打通可启动骨架和仓库加载闭环；不能用假数据掩盖真实加载失败。
- 每个 phase 完成后必须写 handoff，并回填 `plans/pixel-phases.md`。

---

## 2. 目标

来自 `plans/pixel-phases.md` §Phase 1：

| 交付 | 状态 |
|---|---|
| `pyproject.toml` 增 `[pixel]` optional dep | ✅ |
| `main.py` 接 `--pixel` 分支（不带仍走原 CLI） | ✅ |
| `src/git_dungeon/ui_pixel/{app,game_runner,assets,audio,fonts,widgets}.py` 骨架 | 部分完成 |
| `screens/{base,title}.py` + 加载页（不让窗口假死） | 部分完成 |
| `window_to_logical(pos, window_size, logical_size)` 坐标转换函数 | 未做 |
| `GameRunner` 接口至少包含源 plan §5 列出的 12 个方法 | 部分完成 |

**验收命令**（已执行）：
```bash
.venv/bin/python -m pip install -e ".[pixel,dev]"

SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
  PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --pixel-smoke-frames 5

PYTHONPATH=src .venv/bin/python -m git_dungeon --help | rg -- '--pixel|--auto|--lang'

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase1.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
PYTHONPATH=src .venv/bin/python -m pytest tests/functional/ -v --tb=short
PYTHONPATH=src .venv/bin/python -m pytest tests/golden_test.py -v --tb=short
PYTHONPATH=src .venv/bin/python -m ruff check pyproject.toml src/git_dungeon/main.py src/git_dungeon/ui_pixel tests/unit/test_pixel_phase1.py
PYTHONPATH=src .venv/bin/python -m mypy src/git_dungeon/main.py src/git_dungeon/ui_pixel tests/unit/test_pixel_phase1.py --ignore-missing-imports

.venv/bin/python scripts/verify_assets.py --strict
.venv/bin/python scripts/verify_audio.py
```

**结果**：
- Pixel smoke：通过，可在 headless dummy SDL 下自动启动并退出。
- Pixel Phase 1 单测：`2 passed`。
- 快速测试：`345 passed, 2 skipped, 153 deselected`。
- Functional：`133 passed`。
- Golden：`4 passed`。
- Ruff / mypy：通过。
- 资源 / 音频严格校验：通过。

---

## 3. 当前进度

- [x] **依赖入口** — `[pixel]` optional dependency 加入 `pygame-ce>=2.5.0`。
- [x] **CLI 参数** — `main.py` 增 `--pixel`；默认 CLI 路径保持不变。
- [x] **Smoke 参数** — 增隐藏参数 `--pixel-smoke-frames`，仅用于自动化启动验证。
- [x] **Pixel package** — 新增 `src/git_dungeon/ui_pixel/` 包。
- [x] **Pygame App 骨架** — `app.py` 支持 320x180 logical surface、1280x720 窗口、TitleScreen、LoadingScreen、ScreenStack、退出事件。
- [x] **Pygame lazy import** — `pygame` 只在 pixel 路径导入，避免没装 `[pixel]` 时影响 CLI。
- [x] **GameRunner 最小闭环** — `GameRunner.load_repository()` 能加载当前 repo、生成章节、返回 `RunSummary`。
- [x] **测试覆盖** — 新增 `tests/unit/test_pixel_phase1.py`，覆盖仓库加载和 pixel app smoke。
- [x] **AGENTS.md** — 按 `CLAUDE.md` 同步为项目代理规则；`.gitignore` 不再忽略 `AGENTS.md`。
- [~] **GameRunner 完整接口** — 只完成 Phase 1 启动闭环所需的加载、摘要、当前章节接口；12 方法完整契约留给 Phase 2/3 随屏幕落地补齐。
- [ ] **资产 / 音频 / 字体 / widgets 独立模块** — 未拆出，原因见偏离说明。
- [ ] **窗口坐标转换函数** — 未做，当前还没有鼠标交互屏幕，留到 Phase 2 第一批按钮前完成。

---

## 4. 完成情况

### 4.1 实际交付物

| 路径 | 内容 |
|---|---|
| `pyproject.toml` | 新增 `[pixel]` optional dependency，安装 `pygame-ce`。 |
| `src/git_dungeon/main.py` | 新增 `--pixel` 入口和隐藏 smoke 参数；pixel 路径调用 `git_dungeon.ui_pixel.run()`。 |
| `src/git_dungeon/ui_pixel/__init__.py` | 暴露 pixel mode `run()`。 |
| `src/git_dungeon/ui_pixel/app.py` | Pygame 初始化、窗口循环、Title/Loading 基础屏幕、headless smoke 支持。 |
| `src/git_dungeon/ui_pixel/game_runner.py` | 最小 `GameRunner`，加载 repo 并建立章节摘要。 |
| `src/git_dungeon/ui_pixel/screens/base.py` | Screen 协议与 `ScreenStack`。 |
| `src/git_dungeon/ui_pixel/screens/__init__.py` | Pixel screens package。 |
| `tests/unit/test_pixel_phase1.py` | 覆盖 `GameRunner` 和 pixel app smoke。 |
| `AGENTS.md` | 从 `CLAUDE.md` 同步来的项目规则，供 Codex/代理读取。 |
| `.gitignore` | 移除 `AGENTS.md` 忽略规则，让项目规则可被跟踪。 |

### 4.2 关键决策

#### 1. 先做真实加载闭环，不先堆屏幕模块

Phase 1 的真正风险是入口和 `GameRunner` 能不能接上现有 repo → chapters 流程。因此本阶段先交付可启动窗口 + 真实 repo 加载 + 测试，而不是先拆 `assets.py/audio.py/fonts.py/widgets.py` 空壳。这样不会制造“模块齐了但跑不起来”的假完成。

#### 2. `pygame` 走 lazy import

`pygame-ce` 是可选依赖。默认 CLI 用户不安装 `[pixel]` 也应该继续正常使用，所以 `pygame` 只在 `--pixel` 路径导入。缺依赖时会显示明确安装提示，不影响 CLI。

#### 3. 加隐藏 smoke 参数

图形窗口天然需要人工关闭，不适合自动化验证。`--pixel-smoke-frames` 只服务测试，让 CI/headless 环境能确认窗口循环可启动、可渲染几帧、可退出。

#### 4. AGENTS.md 与 CLAUDE.md 保持同源

用户要求“按照项目的 CLAUDE.md，作为项目的 AGENTS.md”。实际处理是复制规则内容，仅把第一句从 Claude 专用描述改成 coding agents 通用描述。后续如 `CLAUDE.md` 变更，应同步检查 `AGENTS.md`。

### 4.3 偏离原计划

| 原计划项 | 实际情况 | 原因 |
|---|---|---|
| `assets.py/audio.py/fonts.py/widgets.py` 骨架 | 未创建 | 当前没有资产加载、音量设置、字体排版、按钮交互需求。先创建空壳会增加维护面。 |
| `screens/{base,title}.py` + 加载页 | `base.py` 独立，Title/Loading 暂在 `app.py` | 两个屏幕目前很小，先保留在入口文件里；Phase 2 开始增屏幕时再拆。 |
| `window_to_logical(...)` | 未实现 | 当前没有鼠标点击命中逻辑；Phase 2 做按钮前必须补。 |
| `GameRunner` 12 方法 | 未全量完成 | Phase 1 只需要加载和当前章节摘要。节点推进、休息、事件、商店、战斗分别属于 Phase 2/3，应随真实屏幕需求补齐。 |

这些偏离不影响 Phase 1 “pixel 入口可启动、CLI 不破坏、GameRunner 能加载真实 repo”的完成标准，但会影响 Phase 2/3，已列入后续任务。

### 4.4 触发的项目原则

- **第一性原理**：先验证最小真实闭环，确认 pixel 入口不是假窗口。
- **DRY**：没有复制 CLI 主流程；GameRunner 从现有 `GitParser` / `ChapterSystem` / `GameState` 建立状态。
- **正交性**：`main.py` 只分发入口；pixel UI 放在独立 `ui_pixel` 包；默认 CLI 不依赖 pygame。
- **禁止掩盖性质 fallback**：缺 `pygame-ce` 时明确报错；`GameRunner` 加载失败不吞掉。
- **Phase handoff**：本文件即 Phase 1 交接文档。

---

## 5. 后续任务

### 5.1 Phase 2 入口

下一个 phase：**`pixel-phase-2` — 非战斗屏幕（Map / Rest / Event / Shop）**。

第一步建议先补三个基础件：
1. `window_to_logical(pos, window_size, logical_size)`，用测试覆盖不同窗口比例和 letterbox。
2. `widgets.py`，至少 Button / TextBox / HPBar，按钮必须支持 disabled 状态和提示文本。
3. 将 `TitleScreen` / `LoadingScreen` 从 `app.py` 拆到 `screens/title.py`，再新增 `MapScreen`。

### 5.2 已知风险与未决问题

| 风险 / 未决项 | 影响 | 处理建议 |
|---|---|---|
| `GameRunner` 接口还不完整 | Phase 2/3 不能直接实现所有屏幕 | 按 Map/Rest/Event/Shop/Battle 的顺序补方法，补一个屏幕就补对应测试。 |
| Title/Loading 还在 `app.py` | 屏幕增多后文件会变大 | Phase 2 第一步拆出。 |
| 坐标转换还没写 | 鼠标点击在非 4x 缩放或窗口变化时可能错位 | Phase 2 写第一个 Button 前必须实现并测试。 |
| Pixel UI 暂无资产/音频接入 | 仍是纯色像素壳，不是最终视觉效果 | Phase 4 再统一接 manifest、BGM、SFX，避免提前硬编码资源路径。 |
| `AGENTS.md` 与 `CLAUDE.md` 未来可能分叉 | 规则冲突会误导代理 | 修改任何一个时同步核对另一个。 |

### 5.3 新会话立刻要读哪些文件

1. `AGENTS.md`
2. `plans/pixel-phases.md`
3. `handoffs/2026-05-04-pixel-phase-1-handoff.md`
4. `src/git_dungeon/ui_pixel/app.py`
5. `src/git_dungeon/ui_pixel/game_runner.py`
6. `src/git_dungeon/ui_pixel/screens/base.py`
7. `src/git_dungeon/main.py`
8. `src/git_dungeon/main_cli.py`
9. `src/git_dungeon/engine/node_flow.py`

### 5.4 推荐的第一条验证命令

```bash
cd /Users/hughlin/Projects/git-dungeon && \
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --pixel-smoke-frames 5 && \
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase1.py -q
```

两条都 exit 0，就说明 Phase 1 入口仍完好。之后再跑：

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
PYTHONPATH=src .venv/bin/python -m pytest tests/functional/ -v --tb=short
PYTHONPATH=src .venv/bin/python -m pytest tests/golden_test.py -v --tb=short
```

这三条用来确认默认 CLI 路径没有被 pixel 入口破坏。
