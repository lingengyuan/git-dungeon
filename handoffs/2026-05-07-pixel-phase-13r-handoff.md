# Pixel Phase 13R Handoff

## 背景

Phase 13 修完了第一批可读性和安全交互问题，但后续 review 又指出几处会继续破坏玩家信任的问题：暂停页“退出本局”实际关闭游戏、战斗胜利仍混 `EXP/Gold`、事件/休息/商店没有统一支持 `Q` 暂停、事件页暴露 event/choice 原始 ID 和 `HP/Gold` 结果文案。

本 phase 依据 `plans/pixel-stardew-level-repair-plan.md` 先做止血修复，不进入 Phase 14A 的大 UI kit 重构。

## 目标

原计划交付：

- “退出本局”不再关闭程序，或明确改成“关闭游戏”。
- 战斗胜利奖励不再显示 `EXP/Gold`。
- 事件、休息、商店统一支持 `Esc/Q` 暂停。
- 事件页短期止血：不显示 event/choice 原始 ID，结果反馈用玩家语言。
- `plans/README.md` 和 phase 索引保持最新。

验收：

- 单元测试覆盖上述行为。
- 中文 smoke 不出现 `EXP`、`Gold`、`HP`、`choice_id`、`event_id`。
- 手动试玩确认暂停语义正确。

## 当前进度

- [x] 暂停页按钮从“退出本局”改为“关闭游戏”，确认文案同步。
- [x] 战斗胜利和浮字使用玩家文案，中文显示“经验/金币”。
- [x] 事件、休息、商店支持 `Esc/Q` 进入暂停。
- [x] 事件页不再绘制 event/choice 原始 ID。
- [x] 事件结果不再拼 `choice_id HP Gold`。
- [x] 陷阱中文结果不再保留 `HP`。
- [x] Phase 索引、主修复计划和 handoff 已更新。
- [x] 相关测试已通过。

## 完成情况

实际交付：

- `src/git_dungeon/ui_pixel/screens/pause.py`：暂停页现在明确是“关闭游戏”，不再把关闭程序伪装成退出本局。
- `src/git_dungeon/ui_pixel/screens/battle.py`：战斗胜利奖励和技能不足提示改用统一属性文案。
- `src/git_dungeon/ui_pixel/screens/event.py`：事件标题、选项、效果预览和结果反馈改为玩家语言；`Q` 进入暂停。
- `src/git_dungeon/ui_pixel/screens/rest.py`、`src/git_dungeon/ui_pixel/screens/shop.py`：`Q` 与 `Esc` 一致进入暂停。
- `src/git_dungeon/ui_pixel/text.py`：新增战斗奖励、事件标题/选项/效果/结果、陷阱结果的玩家文案工具。
- `tests/unit/test_pixel_phase13.py`：覆盖本次 review findings。
- `plans/pixel-phases.md`、`plans/pixel-stardew-level-repair-plan.md`、`plans/pixel-game-fix-plan.md`、`AGENTS.md`、`CLAUDE.md`：当前 phase 状态已同步到 Phase 14A。

关键决策：

- 暂停页本阶段选择把按钮改成“关闭游戏”，而不是立刻实现“返回标题”。原因是返回标题需要更完整的 screen stack 重置和运行状态清理，属于 Phase 14A/16 的统一暂停菜单范围；本 phase 先保证文案和真实行为一致。
- 事件页本阶段没有重做事件数据结构，只基于已有 effects 生成可理解的标题、选项和后果预览。完整事件标题、描述、角色和地点会进入 Phase 16。

偏离原计划：

- “返回标题”没有在 Phase 13R 实现，改为“明确关闭游戏”。这是计划允许的止血路径。
- 本阶段没有做手动窗口截图，因为改动集中在输入语义和文案；最终仍保留 headless smoke 作为验证。

## 后续任务

下一阶段进入 **Phase 14A：统一 UI kit 和玩家语言层**。

新会话立刻读取：

1. `AGENTS.md`
2. `plans/README.md`
3. `plans/pixel-phases.md`
4. `plans/pixel-stardew-level-repair-plan.md`
5. `handoffs/2026-05-07-pixel-phase-13r-handoff.md`
6. `src/git_dungeon/ui_pixel/text.py`
7. `src/git_dungeon/ui_pixel/widgets.py`

已知风险：

- 事件页现在只是“隐藏 ID + 玩家化效果预览”，还不是成熟像素游戏事件。Phase 16 需要补地点背景、事件描述、自然语言选择和角色感。
- 暂停页仍只有继续和关闭游戏，没有运行中设置、返回标题、退出本局确认。Phase 14A/16 需要统一暂停菜单。
- `ShopScreen` 英文商品详情仍是数据式文案，Phase 14A 的玩家语言层需要统一处理英文和中文。

推荐第一条命令：

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase13.py -q
```
