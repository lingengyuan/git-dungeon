# Pixel Phase 21 Handoff

## 背景

Phase 20 已经完成暂停页设置入口和退出本局回标题页。Phase 18 的延期项里，窗口/全屏切换仍需要重启。本 phase 只处理 PC 桌面窗口体验，不考虑移动端和手柄。

上游约束：

- 保持 320x180 逻辑画布和整数倍缩放策略。
- 设置页切换窗口模式要即时生效。
- 标题页设置和暂停页设置都要走同一条即时切换路径。
- 中文提示不能截断或贴边。

## 目标

原计划交付：

- 设置页窗口/全屏即时切换。
- 保存设置后下次启动仍使用上次窗口模式。
- 标题页和暂停页设置入口都能触发即时切换。
- 自动测试覆盖窗口模式标志和设置页即时回调。
- 截图复查设置页提示。

## 当前进度

- [x] `app.py` 增加统一窗口模式应用函数。
- [x] `SettingsScreen` 切换窗口模式后立即调用设置回调。
- [x] Title/Loading/Tutorial/Dungeon/Battle/Event/Rest/Shop/Pause 传递窗口模式回调。
- [x] 设置页提示从“重启后生效”改成“立即切换”。
- [x] 新增 Phase 21 单元测试。
- [x] 复查中英文设置页截图，缩短中文底部提示。
- [x] 更新 PX-035 状态。

## 完成情况

实际交付：

- `src/git_dungeon/ui_pixel/app.py`
  - 新增 `display_flags_for_window_mode()`。
  - 设置变更时调用 `pygame.display.set_mode()` 立即切换窗口/全屏。
- `src/git_dungeon/ui_pixel/screens/settings.py`
  - 窗口模式切换后提示“Window applied / 窗口已切换”。
  - 默认提示改成“Window applies now / 窗口立即切换”。
- `src/git_dungeon/ui_pixel/screens/title.py`、`pause.py` 和运行中屏幕
  - 串起窗口模式回调，保证两个设置入口一致。
- `tests/unit/test_pixel_phase21.py`
  - 覆盖窗口模式 flags 和设置页即时应用。

关键决策：

- 继续使用固定 `WINDOW_SIZE = 960x540` 作为窗口模式尺寸；全屏只改变 display flags，不改变逻辑画布。原因是 Phase 18 已经验证整数倍缩放，不能为了即时切换破坏像素清晰度。
- 没有新增分辨率列表。当前目标是“窗口/全屏即时切换”，不是完整显示设置面板。

偏离原计划：

- 无。

## 后续任务

下一 phase：Phase 22 大仓库加载体验。

建议立刻读：

1. `src/git_dungeon/ui_pixel/screens/title.py`
2. `src/git_dungeon/ui_pixel/game_runner.py`
3. `src/git_dungeon/core/git_parser.py`
4. `tests/integration/test_pixel_smoke.py`

已知风险：

- 在 headless/dummy driver 下只能验证调用路径，不能验证真实全屏视觉；本轮通过截图确认设置页文本，真实桌面切换可在最终 PC 试玩里复核。
- 目前不提供多分辨率选项，后续如果要做显示设置，仍应保持整数倍缩放。

验证结果：

```bash
PYTHONPATH=src .venv/bin/python -m ruff check src/git_dungeon/ui_pixel/app.py src/git_dungeon/ui_pixel/screens/title.py src/git_dungeon/ui_pixel/screens/tutorial.py src/git_dungeon/ui_pixel/screens/dungeon.py src/git_dungeon/ui_pixel/screens/pause.py src/git_dungeon/ui_pixel/screens/event.py src/git_dungeon/ui_pixel/screens/rest.py src/git_dungeon/ui_pixel/screens/shop.py src/git_dungeon/ui_pixel/screens/battle.py src/git_dungeon/ui_pixel/screens/settings.py src/git_dungeon/ui_pixel/text.py tests/unit/test_pixel_phase21.py
# All checks passed

PYTHONPATH=src .venv/bin/python -m mypy src/git_dungeon/ui_pixel/app.py src/git_dungeon/ui_pixel/screens/title.py src/git_dungeon/ui_pixel/screens/tutorial.py src/git_dungeon/ui_pixel/screens/dungeon.py src/git_dungeon/ui_pixel/screens/pause.py src/git_dungeon/ui_pixel/screens/event.py src/git_dungeon/ui_pixel/screens/rest.py src/git_dungeon/ui_pixel/screens/shop.py src/git_dungeon/ui_pixel/screens/battle.py src/git_dungeon/ui_pixel/screens/settings.py
# Success: no issues found in 10 source files

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase21.py tests/unit/test_pixel_phase20.py tests/unit/test_pixel_phase19.py tests/unit/test_pixel_phase18.py -q
# 11 passed

SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=src .venv/bin/python scripts/render_pixel_screens.py --out-dir /tmp/git-dungeon-phase21-screens --scale 2
# rendered 18 screenshots to /tmp/git-dungeon-phase21-screens

SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-phase21-smoke PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --lang zh_CN --pixel-smoke-frames 8
# passed
```

截图复查：

- `/tmp/git-dungeon-phase21-screens/zh_CN-settings.png`
- `/tmp/git-dungeon-phase21-screens/en-settings.png`
