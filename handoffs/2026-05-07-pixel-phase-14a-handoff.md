# Pixel Phase 14A Handoff

## 背景

Phase 13R 修掉了最明显的 review findings，但界面层仍有两个结构性问题：各个 screen 继续自己拼属性和结果文案，休息、商店、事件、战斗、地牢页的底部提示和选择卡片没有统一规则。Phase 14A 的任务是在进入 gpt-image-2 素材生成和 tile 场景重做前，先统一 UI kit 和玩家语言层。

上游约束：

- 不改变 CLI 自动路径、主线节点、奖励结算和战斗规则。
- 不接入未验证的新美术资源。
- 所有玩家可见属性、奖励、损失、商店价格、休息结果都必须从统一 formatter 输出。
- 每个 phase 完成后必须写 handoff。

## 目标

原计划交付：

- Pixel UI kit：按钮、面板、对话框、toast、tooltip、action bar、choice card、item card。
- 玩家语言 formatter：属性、奖励、损失、钥匙、锁门、陷阱、控制提示统一输出。
- 运行中页面共用 pause/action/log 布局。
- 中英文文本不压边，不靠 screen 自己拼字段。

验收：

- 标题、地牢、战斗、事件、商店、休息、设置在中英文下可读。
- `rg` 检查 screen 中不再直接拼接玩家可见 `HP/MP/EXP/Gold`。
- 视觉 smoke 截图无明显重叠。

## 当前进度

- [x] UI kit 增加对话框、toast、tooltip、action bar、choice card、item card。
- [x] 属性、奖励、陷阱、休息、商店文案统一移到 `ui_pixel/text.py`。
- [x] 地牢页、战斗页、事件页、休息页、商店页接入统一底部 action bar。
- [x] 事件、休息、商店选择项改用统一卡片。
- [x] 暂停页改用统一对话框。
- [x] 中文小卡片文案压缩，避免休息/商店效果说明被截断。
- [x] 测试覆盖 formatter、UI kit 暴露和 screen 源码中 raw 字段禁用。
- [x] 渲染 smoke 生成 8 个主要页面截图并人工检查。

## 完成情况

实际交付：

- `src/git_dungeon/ui_pixel/widgets.py`：新增 `draw_dialog`、`draw_action_bar`、`draw_toast`、`draw_tooltip`、`draw_choice_card`、`draw_item_card`，并统一运行页 action bar 区域。
- `src/git_dungeon/ui_pixel/text.py`：新增 `stat_value`、`stat_delta`、`trap_feedback`、`skill_cost_text`、`rest_detail`、`rest_result_feedback`、`shop_offer_detail`、`shop_result_feedback` 等玩家文案 formatter。
- `src/git_dungeon/ui_pixel/screens/dungeon.py`、`battle.py`、`event.py`、`rest.py`、`shop.py`、`pause.py`、`game_over.py`：改为调用统一 formatter 和 UI kit。
- `tests/unit/test_pixel_phase14a.py`：新增 Phase 14A 回归测试。
- `tests/unit/test_pixel_phase8.py`、`test_pixel_phase9.py`、`test_pixel_phase10.py`、`test_pixel_phase12.py`：更新英文 UI 期望，避免继续断言 `HP` 这类旧显示。
- `AGENTS.md`、`CLAUDE.md`、`plans/README.md`、`plans/pixel-phases.md`、`plans/pixel-stardew-level-repair-plan.md`：当前进度同步到 Phase 14B。

关键决策：

- 本阶段只统一 UI 和玩家语言，不把商店/事件/休息重做成完整地点场景。完整地点感留给 Phase 16，避免和 Phase 14B/14C 的素材与 tile 场景范围混在一起。
- 英文模式保留自然英文属性词如 `Health`、`Energy`、`Gold`，但 screen 不再自己拼 `HP/MP/EXP` 或 `cost hp atk maxhp` 这类调试文案。
- 渲染 smoke 使用临时假素材验证 UI 结构，不写入运行时资产；真实美术从 Phase 14B 开始按 asset card 和 manifest 流程处理。

偏离原计划：

- Phase 14A 没有开始生成 gpt-image-2 图片。这符合修订后的拆分：14A 只做 UI/语言层，14B 才开始素材流水线。
- 标题页和设置页只做可读性渲染检查，没有进入视觉重做；标题主题、美术统一放在 Phase 17。

## 后续任务

下一阶段进入 **Phase 14B：gpt-image-2 地牢素材流水线**。

新会话立刻读取：

1. `AGENTS.md`
2. `plans/README.md`
3. `plans/pixel-phases.md`
4. `plans/pixel-stardew-level-repair-plan.md`
5. `handoffs/2026-05-07-pixel-phase-14a-handoff.md`
6. `src/git_dungeon/ui_pixel/widgets.py`
7. `src/git_dungeon/ui_pixel/text.py`

Phase 14B 重点：

- 使用 Codex GPT Image 2 生成第一批地牢基础素材。
- 建立 prompt/raw/processed/contact sheet/asset card/manifest 的闭环。
- 新素材未通过人工核对前不得接入运行时。
- 不用 API 脚本强行生成；Codex 内置 GPT Image 2 可作为当前生成入口。

已知风险：

- 商店商品名称仍来自当前内容数据，部分英文名在中文模式下仍会显示英文；这不是 raw ID，但 Phase 16 需要做完整地点化和商品自然语言化。
- 当前地牢仍是抽象节点图；Phase 14C 才会改成 tile 场景。
- 本阶段的截图 smoke 用假素材检查 UI 布局，不能代表最终美术质量。

验证结果：

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase13.py tests/unit/test_pixel_phase14a.py -q
# 12 passed

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/unit/test_pixel_phase10.py tests/unit/test_pixel_phase11.py tests/unit/test_pixel_phase12.py tests/unit/test_pixel_phase13.py tests/unit/test_pixel_phase14a.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
# 30 passed

SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-phase14a-smoke PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --lang zh_CN --pixel-smoke-frames 8
# passed

PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
# 398 passed, 2 skipped, 153 deselected, 2 warnings

.venv/bin/python -m ruff check src/git_dungeon/ui_pixel tests/unit/test_pixel_phase14a.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/unit/test_pixel_phase10.py tests/unit/test_pixel_phase12.py
# passed

PYTHONPATH=src .venv/bin/python -m mypy src/git_dungeon/ui_pixel --ignore-missing-imports
# passed
```

渲染 smoke：

- 8 个页面截图生成到 `/tmp/git-dungeon-phase14a-screens/`
- 接触表：`/tmp/git-dungeon-phase14a-screens/contact.png`
- 已检查：标题、地牢、战斗、事件、休息、商店、设置、暂停均非空白，主要 UI 没有明显遮挡。
