# Pixel Phase 16 Handoff

## 背景

Phase 15 已经补齐战斗场景、敌人身份和攻击/防御/奖励反馈。Phase 16 继续处理试玩和对标审查里暴露的问题：事件、商店、休息仍然偏数据面板，缺少地点感；部分玩家可见文案仍来自内部字段或英文商品标题。

上游约束：

- 非战斗页面可以换表现，但不能改变事件、商店、休息的结算规则。
- 新素材必须走 prompt、raw、processed、contact sheet、asset card、manifest、校验。
- 中文界面不能继续暴露 `event_id`、`choice_id`、opcode 或英文原始商品标题。
- 每个 phase 完成后必须写 handoff、提交并推送 GitHub。

## 目标

原计划交付：

- 事件页从数据面板变成神龛/终端遗迹这类地点。
- 事件选择显示风险/奖励图标，而不是暴露原始 choice id。
- 商店页加入店主、柜台、商品标题清理和买不起反馈。
- 休息页加入营火/神龛等安全地点元素。
- 事件、商店、休息完成后回到地牢的提示继续使用玩家语言。

验收：

- 三个非战斗页面都有固定截图或接触表复查。
- 中文模式不出现原始字段、内部 id、英文商品标题。
- Pixel smoke 和非功能测试切片通过。

## 当前进度

- [x] 使用 Codex 内置 GPT Image 2 生成 Phase 16 非战斗 sprite sheet。
- [x] 原图保存到 `assets/generated/raw/phase16/noncombat_sheet.png`。
- [x] Prompt 保存到 `assets/source_prompts/phase16/noncombat_sheet.md`。
- [x] Asset plan 保存到 `assets/generated/phase16/asset_plan.json`。
- [x] 后处理输出 8 个非战斗 sprite。
- [x] Contact sheet 保存到 `assets/generated/contact_sheets/phase16_noncombat.png`。
- [x] `assets/manifest_sprites.json` 新增 Phase 16 source 和非战斗 sprite id。
- [x] 新增共享地点舞台绘制工具，战斗、事件、商店、休息复用同一地点底座。
- [x] EventScreen 使用事件地点 sprite 和风险/奖励选择图标。
- [x] ShopScreen 使用店主、柜台和玩家语言商品标题。
- [x] RestScreen 使用营火、神龛和安全地点布局。
- [x] 新增 Phase 16 单元测试。
- [x] 计划索引和活跃 phase 状态已回填。

## 完成情况

实际交付：

- `assets/source_prompts/phase16/noncombat_sheet.md`：本次生成 prompt。
- `assets/generated/raw/phase16/noncombat_sheet.png`：Codex 内置 GPT Image 2 原图。
- `assets/generated/processed/phase16/*.png`：8 个非战斗素材。
- `assets/generated/contact_sheets/phase16_noncombat.png`：人工核对用接触表。
- `assets/generated/phase16/asset_plan.json`：本阶段 asset card。
- `assets/generated/README.md`：登记 Phase 16 生成资产批次。
- `assets/manifest_sprites.json`：新增 `gpt_image_2_phase16` source 和非战斗 sprite id。
- `src/git_dungeon/ui_pixel/widgets.py`
  - 新增 `draw_location_stage`，统一墙面/地面/边线舞台。
- `src/git_dungeon/ui_pixel/screens/event.py`
  - 事件页改为地点场景。
  - 使用 `event_shrine` / `event_terminal_ruin`。
  - 选择项增加 `choice_icon_risk` / `choice_icon_reward`。
- `src/git_dungeon/ui_pixel/screens/shop.py`
  - 商店页加入 `shopkeeper` 和 `shop_counter`。
  - 商品标题通过玩家语言 formatter 清理。
- `src/git_dungeon/ui_pixel/screens/rest.py`
  - 休息页加入 `rest_campfire` 和 `rest_shrine`。
- `src/git_dungeon/ui_pixel/text.py`
  - 新增 `shop_offer_title`。
  - 调整事件选择标签优先级，风险事件优先显示为冒险选择。
- `tests/unit/test_pixel_phase16.py`
  - 覆盖资产链、manifest、事件图标、风险标签、商店标题、休息地点素材。

本批 sprite id：

- `event_shrine`
- `event_terminal_ruin`
- `shopkeeper`
- `shop_counter`
- `rest_campfire`
- `rest_shrine`
- `choice_icon_risk`
- `choice_icon_reward`

关键决策：

- 非战斗页面与战斗页面复用同一地点舞台绘制函数，避免每个页面单独复制墙面/地面逻辑。
- 事件地点先用事件 id 的稳定值在神龛和终端遗迹间切换，不改变事件规则，也避免新增内容配置。
- 商店商品标题只清理玩家可见标题，价格和属性仍由已有 `shop_offer_detail` 统一生成。

偏离原计划：

- 本阶段没有给每个商品生成独立图标。原因是现有商品是规则生成的属性组合，Phase 16 先清理地点感和文案；商品图标可以在 Phase 17 的主题资产里统一补。
- 本阶段没有新增背景音乐，只保留已有音频调用。原因是 Phase 17 专门处理主题、美术、动画和音乐方向统一。

## 后续任务

下一阶段进入 **Phase 17：美术、动画和音乐方向统一**。

新会话立刻读取：

1. `AGENTS.md`
2. `plans/pixel-phases.md`
3. `plans/pixel-stardew-level-repair-plan.md`
4. `docs/PIXEL_UI_LAYOUT_LESSONS.md`
5. `handoffs/2026-05-08-pixel-phase-16-handoff.md`
6. `src/git_dungeon/ui_pixel/screens/title.py`
7. `src/git_dungeon/ui_pixel/screens/dungeon.py`
8. `src/git_dungeon/ui_pixel/screens/battle.py`
9. `assets/generated/phase16/asset_plan.json`

Phase 17 重点：

- 标题页要有明确的游戏入口和统一主题资产。
- 地牢、战斗、事件、商店、休息要共享同一套像素主题语言。
- 增加基础 idle/hover/反馈动效，但不要影响结算和输入。
- 明确音乐资源来源、循环与响度规则，补齐 credits。

已知风险：

- 事件地点目前只有两类视觉变化，长期看还需要更多地点类型匹配内容包。
- 商店商品没有独立图标，商品可读性主要依赖标题和详情。
- Phase 18 仍需要把临时截图复查沉淀成稳定视觉回归流程。

验证结果：

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_pixel_assets.py --asset-cards assets/generated/phase16/asset_plan.json
# OK: generated pixel assets verified

PYTHONPATH=src .venv/bin/python scripts/verify_assets.py --strict
# OK: 49/49 sprites mapped, all valid

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase14a.py tests/unit/test_pixel_phase16.py -q
# 16 passed

PYTHONPATH=src .venv/bin/python -m ruff check src/git_dungeon/ui_pixel/screens/event.py src/git_dungeon/ui_pixel/screens/shop.py src/git_dungeon/ui_pixel/screens/rest.py src/git_dungeon/ui_pixel/screens/battle.py src/git_dungeon/ui_pixel/widgets.py src/git_dungeon/ui_pixel/text.py tests/unit/test_pixel_phase14a.py tests/unit/test_pixel_phase16.py
# All checks passed

PYTHONPATH=src .venv/bin/python -m mypy src/git_dungeon/ui_pixel/screens/event.py src/git_dungeon/ui_pixel/screens/shop.py src/git_dungeon/ui_pixel/screens/rest.py src/git_dungeon/ui_pixel/screens/battle.py src/git_dungeon/ui_pixel/widgets.py src/git_dungeon/ui_pixel/text.py
# Success: no issues found in 6 source files

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_assets.py tests/unit/test_pixel_audio.py tests/unit/test_pixel_phase1.py tests/unit/test_pixel_phase2.py tests/unit/test_pixel_phase3.py tests/unit/test_pixel_phase4.py tests/unit/test_pixel_phase5.py tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/unit/test_pixel_phase10.py tests/unit/test_pixel_phase11.py tests/unit/test_pixel_phase12.py tests/unit/test_pixel_phase13.py tests/unit/test_pixel_phase14a.py tests/unit/test_pixel_phase14b.py tests/unit/test_pixel_phase14c.py tests/unit/test_pixel_phase15.py tests/unit/test_pixel_phase16.py tests/unit/test_pixel_settings.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
# 80 passed

SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-phase16-smoke PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --lang zh_CN --pixel-smoke-frames 8
# passed

PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
# 423 passed, 2 skipped, 153 deselected, 2 warnings
```

截图复查：

- `assets/generated/contact_sheets/phase16_noncombat.png`
- `/tmp/git-dungeon-phase16-noncombat-contact-4x.png`

备注：

- `make test` 在当前 shell 会调用系统 Python，缺少项目依赖，出现 `git` / `textual` 导入错误；本阶段使用 `.venv/bin/python` 跑了等价测试切片并通过。
