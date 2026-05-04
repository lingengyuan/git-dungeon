# Phase 5 Handoff — 设置 & 中文 & 布局

- **Phase**: `pixel-phase-5`
- **收口日期**: 2026-05-04
- **作者会话**: Codex + Hugh Lin
- **所属 plan**: [`plans/pixel-phases.md`](../plans/pixel-phases.md) §Phase 5
- **上一个 handoff**: [`2026-05-04-pixel-phase-4-handoff.md`](2026-05-04-pixel-phase-4-handoff.md)

---

## 1. 背景

Phase 5 要让 Pixel 模式不再只有固定英文界面和固定音量。目标是把设置做成可保存、可恢复、错误可见的最小闭环，并让 `--lang zh_CN` 进入 Pixel 后能稳定显示中文。

**上游约束**：
- 设置必须写到 `GIT_DUNGEON_SAVE_DIR` 对应目录，不能写硬编码绝对路径。
- 配置不存在要创建默认配置。
- 配置损坏要显示错误，并用默认值启动。
- 写入失败要明确提示。
- 中文界面不能靠系统字体碰运气，不能让按钮文字溢出。

---

## 2. 目标

来自 `plans/pixel-phases.md` §Phase 5：

| 交付 | 状态 |
|---|---|
| `SettingsScreen`：BGM / SFX / 语言 / 窗口模式 | ✅ |
| `settings.toml` 写入 `GIT_DUNGEON_SAVE_DIR` | ✅ |
| 配置不存在 → 创建默认 | ✅ |
| 配置损坏 → 显示错误并用默认值启动 | ✅ |
| 写入失败 → 明确提示 | ✅ |
| 中文模式：按钮/事件描述不溢出，自动裁切/换行 | ✅ 基础完成 |

**验收命令**（已执行）：

```bash
GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-phase5-settings \
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --lang zh_CN --pixel-smoke-frames 8

GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-phase5-settings \
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --pixel-smoke-frames 2

GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-phase5-bad \
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --pixel-smoke-frames 2

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase1.py tests/unit/test_pixel_phase2.py tests/unit/test_pixel_phase3.py tests/unit/test_pixel_phase4.py tests/unit/test_pixel_phase5.py tests/test_cli.py tests/unit/test_main.py tests/test_i18n.py -q
PYTHONPATH=src .venv/bin/python -m ruff check src/git_dungeon/main.py src/git_dungeon/ui_pixel tests/unit/test_pixel_phase5.py
PYTHONPATH=src .venv/bin/python -m mypy src/git_dungeon/main.py src/git_dungeon/ui_pixel tests/unit/test_pixel_phase5.py --ignore-missing-imports
PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
PYTHONPATH=src .venv/bin/python -m pytest tests/functional/ -q
PYTHONPATH=src .venv/bin/python -m pytest tests/golden_test.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_assets.py --strict
PYTHONPATH=src .venv/bin/python scripts/verify_audio.py
PYTHONPATH=src .venv/bin/python -m git_dungeon . --seed 42 --auto --compact --print-metrics
```

**结果**：
- Pixel zh_CN smoke：通过，并创建 `settings.toml`。
- Pixel 重启读取设置：通过，保留 `lang = "zh_CN"`。
- 损坏配置 smoke：通过，使用默认配置继续启动。
- Pixel Phase 1-5 + CLI/i18n 重点测试：`41 passed`。
- 快速测试：`361 passed, 2 skipped, 153 deselected`。
- Functional：`133 passed`。
- Golden：`4 passed`。
- Asset / Audio 校验：通过。
- Ruff / mypy：通过。
- CLI 自动模式：能完整运行到游戏内失败结局；退出码为失败结局对应的 `1`，不是崩溃。

---

## 3. 当前进度

- [x] **设置存储** — 新增 `src/git_dungeon/ui_pixel/settings.py`，读写 `settings.toml`。
- [x] **标题页入口** — TitleScreen 支持进入 SettingsScreen。
- [x] **音量设置** — BGM/SFX 音量可调，立即应用，保存后重启保留。
- [x] **语言设置** — 支持 `en` / `zh_CN`，`--lang zh_CN` 可初始化 Pixel 设置；无 CLI 覆盖时读取已保存语言。
- [x] **窗口模式设置** — 支持 windowed / fullscreen，保存后下次启动应用。
- [x] **中文字体** — PixelFont 接入 VT323 和 Ark Pixel，中文走 Ark Pixel。
- [x] **布局防溢出** — Button 和关键文本使用宽度裁切，动态内容不再靠硬切字符。
- [x] **错误可见** — 设置损坏和写入失败都有显式状态。
- [x] **测试覆盖** — `tests/unit/test_pixel_phase5.py` 覆盖设置文件、损坏配置、归一化、中文标签、设置页入口。

---

## 4. 完成情况

### 4.1 实际交付物

| 路径 | 内容 |
|---|---|
| `src/git_dungeon/ui_pixel/settings.py` | Pixel 设置模型、读写、默认路径、损坏配置处理。 |
| `src/git_dungeon/ui_pixel/screens/settings.py` | 设置页，支持音量、语言、窗口模式、保存、返回。 |
| `src/git_dungeon/ui_pixel/text.py` | Pixel UI 文案翻译和音频状态本地化。 |
| `src/git_dungeon/ui_pixel/app.py` | 启动时读取设置、应用窗口模式、字体语言和音量。 |
| `src/git_dungeon/main.py` | Pixel 模式下 `--lang` 可作为显式覆盖；未传时读取保存设置。 |
| `src/git_dungeon/ui_pixel/widgets.py` | Button 文本按宽度裁切，避免溢出。 |
| `src/git_dungeon/ui_pixel/screens/*.py` | 主要屏幕接入 settings/lang，关键文案中文化。 |
| `tests/unit/test_pixel_phase5.py` | Phase 5 设置与中文测试。 |

### 4.2 关键决策

#### 1. CLI 的 `--lang` 只在显式传入时覆盖 Pixel 设置

原本 argparse 默认是 `en`，会导致用户保存中文后，下次不传 `--lang` 又被强制改回英文。现在普通 CLI 仍默认英文，Pixel 模式未传 `--lang` 时读取保存值。

#### 2. 窗口模式保存后下次启动应用

设置页可以切 windowed / fullscreen，但窗口模式不在当前屏幕中热切换。这样避免在 Screen 层直接管理 display 对象，保持 App 负责窗口生命周期。

#### 3. 中文字体不依赖系统回退

英文使用 VT323，中文使用 Ark Pixel。按钮和动态文本用字体测量后的裁切，而不是按固定字符数猜测宽度。

### 4.3 偏离原计划

| 原计划项 | 实际情况 | 原因 |
|---|---|---|
| 窗口模式设置 | 已保存并在下次启动生效，不做运行时热切换 | 避免让 Screen 接管窗口对象，保持职责清晰。 |
| 所有文本自动换行 | 关键动态文本做宽度裁切，设置/标题/加载等短文本不换行 | 当前 320x180 画布很小，裁切比多行挤压更稳定；长文本换行可放到 Phase 6 打磨。 |

这些偏离不影响 Phase 5 核心目标：设置能保存/恢复，中文能进入主流程，错误状态可见。

### 4.4 触发的项目原则

- **第一性原理**：先保证设置真实保存、真实恢复，再做更复杂的 UI 偏好。
- **DRY**：设置路径、归一化、读写集中在 `settings.py`。
- **正交性**：App 管启动设置，Screen 管交互，Audio 只吃音量值。
- **禁止掩盖性质 fallback**：配置损坏和写入失败都保留错误状态并显示。
- **Phase handoff**：本文件即 Phase 5 交接文档。

---

## 5. 后续任务

### 5.1 Phase 6 入口

下一个 phase：**`pixel-phase-6` — 自动化测试 & 打磨 & 打包**。

建议入口顺序：
1. 增加 Pixel integration smoke，不只跑手写命令。
2. 做 Pixel headless/auto 路径和 CLI metrics 对比。
3. 把资源定位顺序从开发目录扩展到安装包 / PyInstaller。
4. 把缺资源错误改成明确错误页。

### 5.2 已知风险与未决问题

| 风险 / 未决项 | 影响 | 处理建议 |
|---|---|---|
| Pixel 仍没有完整 headless auto 一局 | 还不能自动证明 Pixel/CLI 完整指标一致 | Phase 6 做 `--pixel --auto --headless`。 |
| 窗口模式不热切换 | 设置后需重启才能应用 | 如要热切换，Phase 6 让 App 层处理 display reset。 |
| 中文内容仍有部分 ID 型文本 | Event/shop 的内部 id 仍会显示英文 key | Phase 6 或内容层补 display name。 |
| 长文本是裁切，不是完整换行 | 信息完整性有限 | Phase 6 做统一 TextBox/wrap。 |

### 5.3 新会话立刻要读哪些文件

1. `AGENTS.md`
2. `plans/pixel-phases.md`
3. `handoffs/2026-05-04-pixel-phase-5-handoff.md`
4. `src/git_dungeon/ui_pixel/settings.py`
5. `src/git_dungeon/ui_pixel/screens/settings.py`
6. `src/git_dungeon/ui_pixel/app.py`
7. `src/git_dungeon/ui_pixel/text.py`
8. `tests/unit/test_pixel_phase5.py`

### 5.4 推荐的第一条验证命令

```bash
cd /Users/hughlin/Projects/git-dungeon && \
GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-phase5-check \
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --lang zh_CN --pixel-smoke-frames 8 && \
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase5.py -q
```

两条都 exit 0，说明设置、中文、字体、Pixel 启动仍完好。
