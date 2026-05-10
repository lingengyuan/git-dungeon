# Pixel Phase 22 Handoff

## 背景

Phase 21 已完成 PC 窗口/全屏即时切换。Phase 18 的延期项里，大仓库加载仍可能阻塞窗口，玩家会以为游戏卡死。本 phase 只处理 Pixel mode 的仓库加载体验。

上游约束：

- 不改变 CLI 行为。
- 加载失败必须显示错误，不能静默退回。
- 加载中窗口要继续刷新。
- 用户按 Esc/Q 可以取消回标题页。

## 目标

原计划交付：

- 仓库读取放到后台，加载页不阻塞主循环。
- 加载页显示阶段提示和活动状态。
- Esc/Q 可取消加载并回标题页。
- 取消后使用干净 runner，避免旧后台加载污染下一局。
- 截图脚本覆盖 loading 页面。

## 当前进度

- [x] `LoadingScreen` 改为后台线程加载仓库。
- [x] 加载页显示阶段状态：准备本局、读取提交历史、生成路线、大仓库仍在处理。
- [x] Esc/Q 取消加载回标题页。
- [x] `GameRunner.fresh_copy()` 支持用同配置创建干净 runner。
- [x] 截图脚本加入 loading 页面。
- [x] 新增 Phase 22 单元测试。
- [x] 更新 PX-020 状态。

## 完成情况

实际交付：

- `src/git_dungeon/ui_pixel/screens/title.py`
  - `LoadingScreen` 使用后台线程执行 `load_repository()`。
  - 主循环继续刷新，并显示阶段提示和动态点。
  - 加载失败后 Enter/Esc 返回标题页。
  - Esc/Q 取消加载后回标题页。
- `src/git_dungeon/ui_pixel/game_runner.py`
  - 记录启动配置。
  - 新增 `fresh_copy()`，取消加载时生成干净 runner。
- `scripts/render_pixel_screens.py`
  - 截图覆盖 loading。
- `tests/unit/test_pixel_phase22.py`
  - 覆盖非阻塞启动、取消回标题页、阶段提示推进。

关键决策：

- 后台线程只负责仓库读取和运行初始化，不触碰 pygame 对象。原因是 pygame 渲染和事件处理必须留在主线程。
- 取消加载不强杀线程，而是忽略结果并回到使用新 runner 的标题页。原因是 Python 线程无法安全中断 Git 读取；忽略结果比强行终止更可靠。

偏离原计划：

- 没有做真实百分比进度。当前底层 Git 读取没有暴露可追踪进度，本 phase 用阶段提示替代。

## 后续任务

下一 phase：Phase 23 近期事件日志和章节总结。

建议立刻读：

1. `src/git_dungeon/ui_pixel/game_runner.py`
2. `src/git_dungeon/ui_pixel/screens/dungeon.py`
3. `src/git_dungeon/ui_pixel/screens/battle.py`
4. `src/git_dungeon/ui_pixel/screens/event.py`
5. `src/git_dungeon/ui_pixel/screens/rest.py`
6. `src/git_dungeon/ui_pixel/screens/shop.py`

已知风险：

- 后台线程取消后会自然结束，期间不会再被 UI 使用；如果底层 Git 读取本身长期阻塞，线程仍会等系统调用结束。
- 阶段提示是时间驱动，不是精确进度百分比。

验证结果：

```bash
PYTHONPATH=src .venv/bin/python -m ruff check src/git_dungeon/ui_pixel/game_runner.py src/git_dungeon/ui_pixel/screens/title.py src/git_dungeon/ui_pixel/text.py tests/unit/test_pixel_phase22.py
# All checks passed

PYTHONPATH=src .venv/bin/python -m mypy src/git_dungeon/ui_pixel/game_runner.py src/git_dungeon/ui_pixel/screens/title.py
# Success: no issues found in 2 source files

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase22.py tests/unit/test_pixel_phase21.py tests/unit/test_pixel_phase20.py tests/unit/test_pixel_phase19.py tests/integration/test_pixel_smoke.py -q
# 12 passed

SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=src .venv/bin/python scripts/render_pixel_screens.py --out-dir /tmp/git-dungeon-phase22-screens --scale 2
# rendered 20 screenshots to /tmp/git-dungeon-phase22-screens
```

截图复查：

- `/tmp/git-dungeon-phase22-screens/zh_CN-loading.png`
