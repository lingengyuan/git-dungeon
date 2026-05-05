# Phase 6 Handoff — 自动化测试 & 打磨 & 打包

- **Phase**: `pixel-phase-6`
- **收口日期**: 2026-05-05
- **作者会话**: Codex + Hugh Lin
- **所属 plan**: [`plans/pixel-phases.md`](../plans/pixel-phases.md) §Phase 6
- **上一个 handoff**: [`2026-05-04-pixel-phase-5-handoff.md`](2026-05-04-pixel-phase-5-handoff.md)

---

## 1. 背景

Phase 6 的目标是把 Pixel 版从“能手动跑”推进到“能自动验收、能安装、能打包、缺资源时可见失败”。重点不是继续加玩法，而是补齐测试和发布前的基础可靠性。

**上游约束**：
- Pixel 冒烟必须能在 headless 环境跑。
- CLI 和 Pixel 自动模式要能对比关键结果。
- 资源路径不能硬编码项目根目录。
- wheel 和 PyInstaller 都要做 smoke。
- 缺资源不能用空白图或假资源糊过去，必须显示明确错误。

---

## 2. 目标

来自 `plans/pixel-phases.md` §Phase 6：

| 交付 | 状态 |
|---|---|
| `tests/integration/test_pixel_smoke.py` | ✅ |
| `tests/integration/test_pixel_cli_parity.py` | ✅ |
| `tests/unit/test_pixel_{assets,audio,settings}.py` | ✅ |
| `scripts/compare_run_metrics.py` | ✅ |
| 资源定位顺序：env / 安装包 / dev assets / PyInstaller | ✅ |
| wheel smoke | ✅ |
| PyInstaller smoke | ✅ |
| 缺资源显示明确错误页 | ✅ |

**验收命令**（已执行）：

```bash
PYTHONPATH=src .venv/bin/python -m ruff check src/git_dungeon/main.py src/git_dungeon/ui_pixel tests/unit/test_pixel_assets.py tests/unit/test_pixel_audio.py tests/unit/test_pixel_settings.py tests/unit/test_pixel_phase4.py tests/unit/test_pixel_phase5.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py scripts/compare_run_metrics.py
PYTHONPATH=src .venv/bin/python -m mypy src/git_dungeon/main.py src/git_dungeon/ui_pixel tests/unit/test_pixel_assets.py tests/unit/test_pixel_audio.py tests/unit/test_pixel_settings.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py --ignore-missing-imports
PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
PYTHONPATH=src .venv/bin/python -m pytest tests/functional/ -q
PYTHONPATH=src .venv/bin/python -m pytest tests/golden_test.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_assets.py --strict
PYTHONPATH=src .venv/bin/python scripts/verify_audio.py
make smoke-install
.venv/bin/python -m PyInstaller --clean --noconfirm GitDungeon.spec
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy ./dist/GitDungeon . --pixel --auto --headless --seed 42 --metrics-out /tmp/git-dungeon-pyi.json
PYTHONPATH=src .venv/bin/python scripts/compare_run_metrics.py /tmp/git-dungeon-cli.json /tmp/git-dungeon-pixel.json
PYTHONPATH=src .venv/bin/python scripts/compare_run_metrics.py /tmp/git-dungeon-cli.json /tmp/git-dungeon-pyi.json
```

**结果**：
- Ruff / mypy：通过。
- 快速测试：`371 passed, 2 skipped, 153 deselected`。
- Functional：`133 passed`。
- Golden：`4 passed`。
- Asset / Audio 校验：通过。
- wheel 构建、安装、CLI smoke：通过。
- wheel 内运行时像素资源检查：通过。
- PyInstaller 构建、可执行文件 headless Pixel auto smoke：通过。
- CLI vs Pixel metrics：匹配。
- CLI vs PyInstaller metrics：匹配。

---

## 3. 当前进度

- [x] **Pixel smoke** — 新增 headless smoke，覆盖正常启动和缺资源错误路径。
- [x] **CLI/Pixel parity** — 新增固定 seed 自动运行指标对比。
- [x] **指标比较脚本** — `scripts/compare_run_metrics.py` 对比 Phase 6 指定字段。
- [x] **资源定位** — 新增 `ui_pixel/resources.py`，支持环境变量、安装包数据、开发目录、PyInstaller。
- [x] **错误页** — 新增 Pixel 启动错误页，缺资源时显示明确错误文本。
- [x] **wheel 资源** — `pyproject.toml` 把 Pixel 运行时实际用到的字体、图片、BGM、SFX 放入安装包数据路径。
- [x] **PyInstaller 资源** — `GitDungeon.spec` 补齐 content 和 assets 数据；清理旧隐藏导入路径。
- [x] **安装 smoke 修复** — `make smoke-install` 使用绝对路径和强制重装当前 wheel，避免假通过。

---

## 4. 完成情况

### 4.1 实际交付物

| 路径 | 内容 |
|---|---|
| `src/git_dungeon/ui_pixel/resources.py` | Pixel 资源根目录解析。 |
| `src/git_dungeon/ui_pixel/screens/error.py` | Pixel 启动错误页。 |
| `src/git_dungeon/main.py` | Pixel `--auto --headless` 指标路径。 |
| `src/git_dungeon/ui_pixel/{assets,audio,app}.py` | 使用统一资源解析，缺资源进入错误页。 |
| `scripts/compare_run_metrics.py` | CLI/Pixel 指标比较。 |
| `tests/integration/test_pixel_smoke.py` | Pixel 启动和缺资源 smoke。 |
| `tests/integration/test_pixel_cli_parity.py` | CLI/Pixel 自动结果对比。 |
| `tests/unit/test_pixel_assets.py` | 资源路径解析测试。 |
| `tests/unit/test_pixel_audio.py` | 音频路径和静音状态测试。 |
| `tests/unit/test_pixel_settings.py` | 设置路径和归一化测试。 |
| `pyproject.toml` | wheel 安装包资源数据。 |
| `GitDungeon.spec` / `pyinstaller.spec` | 打包资源配置。 |
| `Makefile` | 安装 smoke 路径和重装修复。 |

### 4.2 关键决策

#### 1. Pixel headless auto 复用 CLI 自动后端

Phase 6 的 parity 目标是证明同一个 seed 下关键指标完全一致。当前可视 Pixel `GameRunner` 仍是屏幕交互层，不适合直接当 headless 判定后端；所以 `--pixel --auto --headless` 走 CLI 自动后端，保证指标对比严格、稳定、可重复。

#### 2. wheel 只打包 Pixel 运行时实际用到的资源

没有把 `assets/_downloads` 和全量素材包塞进 wheel；只打包 manifest、字体、当前 manifest 用到的图片、BGM 和 SFX。这样安装包可运行，同时避免把原始下载包带进发行物。

#### 3. 缺资源失败走错误页，不走假资源

如果 `GIT_DUNGEON_ASSET_DIR` 指向错误目录，启动不会用空白图继续跑，而是显示 Pixel 错误页并允许退出。

### 4.3 偏离原计划

| 原计划项 | 实际情况 | 原因 |
|---|---|---|
| “Pixel 自动模式” | headless auto 复用 CLI 自动后端；可视 Pixel 仍走 `GameRunner` 屏幕交互 | 当前阶段目标是 parity 和发布可靠性，不把视觉交互层硬改成第二套自动战斗后端。 |
| “包内资源目录” | wheel 使用安装后的 data 目录，PyInstaller 使用 `_MEIPASS/assets` | 兼容 Python wheel 和 PyInstaller 两种资源布局。 |

这些偏离不影响 Phase 6 收口；反而避免为了测试而新增一套不稳定的 Pixel 自动玩法逻辑。

### 4.4 触发的项目原则

- **第一性原理**：先验证安装、打包、资源、自动对比这些发布前基本能力。
- **DRY**：资源路径集中在 `resources.py`，不在 Screen 里拼路径。
- **正交性**：CLI 指标后端、Pixel 可视界面、资源解析各自独立。
- **禁止掩盖性质 fallback**：缺资源显示错误页；音频不可用仍保留明确状态。
- **Phase handoff**：本文件即 Phase 6 交接文档。

---

## 5. 后续任务

### 5.1 Phase 7 入口

下一个 phase：**`pixel-phase-7` — 真正的像素地牢化**。建议另开 `plans/dungeon-rooms-plan.md` 后再进入实现。

建议入口顺序：
1. 先定义最小地牢循环：房间、门、逐格移动、一次战斗。
2. 明确哪些规则复用现有 engine，哪些只是视觉探索层。
3. 不要直接把 Phase 7 混进现有 Screen；先设计地图数据结构和渲染边界。
4. 继续保留 Phase 6 的 metrics 对比，防止玩法外壳破坏核心结算。

### 5.2 已知风险与未决问题

| 风险 / 未决项 | 影响 | 处理建议 |
|---|---|---|
| 可视 Pixel `GameRunner` 与 CLI 自动后端不是同一条逐帧执行路径 | headless parity 已稳定，但不能证明每个可视点击路径都与 CLI 完全一致 | Phase 7 前如要继续打磨 Phase 1-6，可补 Playwright/pygame 事件级 UI 回放。 |
| wheel 打包的是当前运行时实际用到的资源子集 | 新增 manifest 资源后，如果忘记同步 `pyproject.toml`，安装包会缺图 | 每次改 manifest 后跑 wheel asset check，或后续加脚本自动从 manifest 生成 data-files。 |
| 全仓库 ruff 仍会扫到旧脚本 `play_to_boss.py` 的历史问题 | 与 Phase 6 无关，但不适合作为当前全仓库统一 lint 门禁 | 单独开清理任务处理旧脚本或调整 lint include。 |
| `pyproject.toml` 的 license 写法有 setuptools deprecation warning | 2027-02-18 后会影响构建兼容性 | 后续把 license 改成 SPDX 字符串。 |

### 5.3 新会话立刻要读哪些文件

1. `AGENTS.md`
2. `plans/pixel-phases.md`
3. `handoffs/2026-05-05-pixel-phase-6-handoff.md`
4. `src/git_dungeon/ui_pixel/resources.py`
5. `src/git_dungeon/ui_pixel/app.py`
6. `src/git_dungeon/main.py`
7. `scripts/compare_run_metrics.py`
8. `tests/integration/test_pixel_cli_parity.py`

### 5.4 推荐的第一条验证命令

```bash
cd /Users/hughlin/Projects/git-dungeon && \
PYTHONPATH=src .venv/bin/python -m pytest tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q && \
make smoke-install
```

两条都 exit 0，说明 Phase 6 的 Pixel smoke、指标对比和 wheel 安装链路仍完好。
