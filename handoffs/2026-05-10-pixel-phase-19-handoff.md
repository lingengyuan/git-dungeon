# Pixel Phase 19 Handoff

## 背景

Phase 18 已经完成核心界面的视觉回归保护，但“首次游玩教学”仍是延期项。用户明确后续只支持 PC，不考虑手柄和移动端，所以本 phase 只处理桌面键盘、鼠标下的新玩家第一分钟理解问题。

上游约束：

- 不新增移动端、触控、手柄相关范围。
- 教学不能遮盖真实流程，仓库加载完成后进入，读完后进入地牢。
- 文案必须中英文可读，不再出现溢出和重叠。
- 每个 phase 完成后必须验证、写 handoff、提交并推送。

## 目标

原计划交付：

- 首次启动 Pixel mode 时，在进入地牢前展示 PC 键鼠教学。
- 教学说明移动、确认进入房间、陷阱/补给和暂停入口。
- 看过后写入设置，后续启动不重复弹出。
- 截图脚本覆盖教学页，便于人工复查。

## 当前进度

- [x] 新增 `TutorialScreen`。
- [x] `LoadingScreen` 在仓库加载完成后按 `tutorial_seen` 决定是否显示教学。
- [x] `PixelSettings` 新增 `tutorial_seen` 并持久化。
- [x] 教学文案加入中文翻译。
- [x] 截图脚本加入 tutorial 页面。
- [x] 新增 Phase 19 单元测试。
- [x] 实际复查中英文教学截图，修正中文文字重叠和英文按钮截断。

## 完成情况

实际交付：

- `src/git_dungeon/ui_pixel/screens/tutorial.py`
  - 展示 PC 键鼠教学页。
  - Enter/Space、Esc/Q 或点击按钮可进入地牢。
  - 保存 `tutorial_seen = true`，保存失败会显示错误，不静默吞掉。
- `src/git_dungeon/ui_pixel/screens/title.py`
  - 加载完成后首次进入教学页，之后直接进入地牢。
- `src/git_dungeon/ui_pixel/settings.py`
  - 设置文件新增 `tutorial_seen`。
- `scripts/render_pixel_screens.py`
  - 截图覆盖 title、tutorial、dungeon、battle、event、shop、rest、settings。
- `tests/unit/test_pixel_phase19.py`
  - 覆盖首次显示、已看过跳过、确认后写入设置。

关键决策：

- 教学只做一页，不做多页向导。原因是当前目标是降低首次进入门槛，不打断地牢主流程。
- 教学文案改成三条短句。原因是中文像素字体实际渲染比预估更高，长文案会重叠。

偏离原计划：

- 没有做手柄提示、移动端提示或触控说明。用户已明确 PC-only。

## 后续任务

下一 phase：Phase 20 暂停、设置和退出本局闭环。

建议立刻读：

1. `AGENTS.md`
2. `plans/pixel-phases.md`
3. `src/git_dungeon/ui_pixel/screens/pause.py`
4. `src/git_dungeon/ui_pixel/screens/settings.py`
5. `src/git_dungeon/ui_pixel/screens/title.py`

已知风险：

- 教学状态写入失败时会停留在教学页并显示错误；如果用户配置目录不可写，需要手动修复保存路径。
- 教学截图仍需要人工视觉复查，自动测试只保证页面存在和流程正确。

验证结果：

```bash
PYTHONPATH=src .venv/bin/python -m ruff check src/git_dungeon/ui_pixel/settings.py src/git_dungeon/ui_pixel/screens/tutorial.py src/git_dungeon/ui_pixel/screens/title.py src/git_dungeon/ui_pixel/text.py scripts/render_pixel_screens.py tests/unit/test_pixel_phase19.py
# All checks passed

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase19.py tests/unit/test_pixel_phase18.py -q
# 7 passed

SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=src .venv/bin/python scripts/render_pixel_screens.py --out-dir /tmp/git-dungeon-phase19-screens --scale 2
# rendered 16 screenshots to /tmp/git-dungeon-phase19-screens

SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-phase19-smoke PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --lang zh_CN --pixel-smoke-frames 8
# passed

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase19.py tests/unit/test_pixel_phase18.py tests/integration/test_pixel_smoke.py -q
# 9 passed
```

截图复查：

- `/tmp/git-dungeon-phase19-screens/zh_CN-tutorial.png`
- `/tmp/git-dungeon-phase19-screens/en-tutorial.png`
