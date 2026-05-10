# Pixel Phase 20 Handoff

## 背景

Phase 19 已经补上首次游玩教学。Phase 18 的延期项里，暂停页仍不能进入设置，“退出本局”也容易被误解为关闭整个游戏。本 phase 只处理 PC 键鼠下的运行中菜单闭环。

上游约束：

- 不做手柄和移动端。
- 运行中页面按 Esc/Q 仍进入暂停，不直接关闭游戏。
- 暂停页的“退出本局”必须回标题页，而不是关闭窗口。
- 设置页可以从暂停页打开，且音量、语言、文字大小等即时影响当前暂停菜单。

## 目标

原计划交付：

- 暂停页新增“设置”入口。
- 暂停页“退出本局”回标题页。
- 所有运行中屏幕打开暂停时携带当前运行上下文。
- 截图脚本覆盖暂停页。
- 行为测试覆盖设置入口和退出本局。

## 当前进度

- [x] `ScreenAction` 新增 reset 行为，支持清空窗口栈并回标题页。
- [x] `PauseScreen` 增加继续、设置、退出本局三按钮。
- [x] Q 二次确认从“关闭游戏”改为“回到标题页”。
- [x] Dungeon/Battle/Event/Rest/Shop 传递运行上下文给暂停页。
- [x] 暂停页可以打开设置页。
- [x] 截图脚本加入 pause 页面。
- [x] 新增 Phase 20 单元测试。
- [x] 更新 PX-024 状态。

## 完成情况

实际交付：

- `src/git_dungeon/ui_pixel/screens/pause.py`
  - 新增设置入口。
  - “退出本局”二次确认后回标题页。
  - 设置变更会更新暂停页字体和音量。
- `src/git_dungeon/ui_pixel/screens/base.py`
  - 新增 `ScreenAction.reset()`。
- `src/git_dungeon/ui_pixel/app.py`
  - 支持 reset 清空当前窗口栈并进入指定屏幕。
- `src/git_dungeon/ui_pixel/screens/{dungeon,battle,event,rest,shop}.py`
  - 打开暂停页时传递 runner、assets、settings store。
- `scripts/render_pixel_screens.py`
  - 截图覆盖 pause。
- `tests/unit/test_pixel_phase20.py`
  - 覆盖暂停页打开设置和退出本局回标题页。

关键决策：

- “退出本局”回标题页，不保留旧运行栈。原因是玩家选择退出本局时，下一步最自然的是重新开始或改设置，而不是留在旧房间下面。
- 没有新增“关闭游戏”按钮。玩家回标题页后仍可 Esc/Q 关闭游戏，暂停页只处理本局行为。

偏离原计划：

- 暂停页打开设置后，底层运行屏幕已经存在的局部设置引用不会全部被重写；但字体和音量通过共享对象即时生效，回到后续屏幕会继续使用更新设置。完整全局设置广播不是本 phase 范围。

## 后续任务

下一 phase：Phase 21 PC 窗口/全屏即时切换。

建议立刻读：

1. `src/git_dungeon/ui_pixel/app.py`
2. `src/git_dungeon/ui_pixel/layout.py`
3. `src/git_dungeon/ui_pixel/settings.py`
4. `src/git_dungeon/ui_pixel/screens/settings.py`
5. `tests/unit/test_pixel_phase20.py`

已知风险：

- 设置页的窗口模式仍是“保存后重启生效”，Phase 21 需要改为即时切换。
- 暂停页截图已覆盖，但自动测试不判断视觉美观，仍需人工复查截图。

验证结果：

```bash
PYTHONPATH=src .venv/bin/python -m ruff check src/git_dungeon/ui_pixel/app.py src/git_dungeon/ui_pixel/screens/base.py src/git_dungeon/ui_pixel/screens/pause.py src/git_dungeon/ui_pixel/screens/dungeon.py src/git_dungeon/ui_pixel/screens/event.py src/git_dungeon/ui_pixel/screens/rest.py src/git_dungeon/ui_pixel/screens/shop.py src/git_dungeon/ui_pixel/screens/battle.py src/git_dungeon/ui_pixel/text.py tests/unit/test_pixel_phase13.py tests/unit/test_pixel_phase20.py
# All checks passed

PYTHONPATH=src .venv/bin/python -m mypy src/git_dungeon/ui_pixel/app.py src/git_dungeon/ui_pixel/screens/base.py src/git_dungeon/ui_pixel/screens/pause.py src/git_dungeon/ui_pixel/screens/dungeon.py src/git_dungeon/ui_pixel/screens/event.py src/git_dungeon/ui_pixel/screens/rest.py src/git_dungeon/ui_pixel/screens/shop.py src/git_dungeon/ui_pixel/screens/battle.py
# Success: no issues found in 8 source files

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase20.py tests/unit/test_pixel_phase13.py tests/unit/test_pixel_phase19.py tests/unit/test_pixel_phase18.py -q
# 17 passed

SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=src .venv/bin/python scripts/render_pixel_screens.py --out-dir /tmp/git-dungeon-phase20-screens --scale 2
# rendered 18 screenshots to /tmp/git-dungeon-phase20-screens
```

截图复查：

- `/tmp/git-dungeon-phase20-screens/zh_CN-pause.png`
- `/tmp/git-dungeon-phase20-screens/en-pause.png`
