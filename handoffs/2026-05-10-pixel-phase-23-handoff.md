# Pixel Phase 23 Handoff

## 背景

Phase 22 已经解决加载页阻塞问题。Phase 18 的延期项里，近期事件日志/章节总结仍未完成。玩家在战斗、事件、商店、休息、陷阱和奖励之间切换后，容易忘记刚刚发生了什么。本 phase 只做 PC 地牢页内的过程记录，不新增独立结算大屏。

上游约束：

- 不改变底层结算规则。
- 日志必须来自真实运行结果，不能写装饰性假消息。
- 中文模式不能暴露英文属性缩写。
- 不占用底部操作栏，不遮挡地图。

## 目标

原计划交付：

- 记录近期运行事件。
- 地牢页展示最近事件和房间进度摘要。
- 战斗、事件、休息、商店、陷阱、奖励都写入日志。
- 截图脚本覆盖带日志的地牢页。
- 单元测试覆盖日志截断和地牢页显示。

## 当前进度

- [x] `GameRunner` 新增 `RunLogEntry` 和 `ChapterSummarySnapshot`。
- [x] `GameRunner` 记录战斗胜利、事件解决、休息、商店、陷阱、奖励。
- [x] 地牢页右侧新增日志面板。
- [x] 日志面板显示最近 4 条事件和房间进度。
- [x] 中文文案加入日志相关翻译。
- [x] 截图脚本示例地牢加入日志数据。
- [x] 新增 Phase 23 单元测试。
- [x] 更新 PX-039 状态。

## 完成情况

实际交付：

- `src/git_dungeon/ui_pixel/game_runner.py`
  - 新增日志和章节摘要数据结构。
  - 记录真实运行事件。
  - 最近日志限制为 12 条，页面显示最近 4 条。
- `src/git_dungeon/ui_pixel/screens/dungeon.py`
  - 右侧新增日志面板。
  - 展示“记录”、房间进度、近期事件。
- `src/git_dungeon/ui_pixel/text.py`
  - 新增日志、房间、事件结果等中文文案。
- `scripts/render_pixel_screens.py`
  - 示例地牢截图带日志，便于人工复查。
- `tests/unit/test_pixel_phase23.py`
  - 覆盖日志保留最新记录和地牢页绘制。

关键决策：

- 不做单独章节总结页，先把信息放在地牢页。原因是玩家最需要回忆上下文的时刻就是回到地牢后做下一步选择。
- 日志用短句，不写完整叙事。原因是右侧面板空间有限，短句更适合像素 UI。

偏离原计划：

- 章节总结先落为房间进度摘要，不做章节完成弹窗。完整章节结算可以后续再扩展。

## 后续任务

下一 phase：Phase 24 内容体验打磨。

建议立刻读：

1. `src/git_dungeon/ui_pixel/game_runner.py`
2. `src/git_dungeon/ui_pixel/screens/dungeon.py`
3. `src/git_dungeon/ui_pixel/text.py`
4. `scripts/render_pixel_screens.py`

已知风险：

- 日志短句目前覆盖关键事件，不是完整战报。
- 右侧日志面板依赖当前地图宽度；如果后续扩大地牢网格，需要重新检查布局。

验证结果：

```bash
PYTHONPATH=src .venv/bin/python -m ruff check src/git_dungeon/ui_pixel/game_runner.py src/git_dungeon/ui_pixel/screens/dungeon.py src/git_dungeon/ui_pixel/text.py tests/unit/test_pixel_phase23.py
# All checks passed

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase23.py tests/unit/test_pixel_phase22.py tests/unit/test_pixel_phase21.py tests/unit/test_pixel_phase20.py -q
# 9 passed

SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=src .venv/bin/python scripts/render_pixel_screens.py --out-dir /tmp/git-dungeon-phase23-screens --scale 2
# rendered 20 screenshots to /tmp/git-dungeon-phase23-screens
```

截图复查：

- `/tmp/git-dungeon-phase23-screens/zh_CN-dungeon.png`
