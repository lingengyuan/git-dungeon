# Pixel Phase 15 Handoff

## 背景

Phase 14C 已经把地牢从抽象节点图改成 tile 场景。Phase 15 继续处理真实试玩中最明显的第二个问题：战斗页仍然像按钮面板，普通敌人和首领缺少清晰身份，攻击、防御、胜利掉落主要靠文字表达。

上游约束：

- 战斗视觉可以增强，但不能改变战斗结算、CLI 自动路径和 Pixel/CLI parity。
- 新战斗素材必须走 prompt、raw、processed、contact sheet、asset card、manifest、校验。
- 中文界面不能继续暴露 `Battle started`、`phase_1` 这类内部字段。
- 每个 phase 完成后必须写 handoff、提交并推送 GitHub。

## 目标

原计划交付：

- 战斗画面拆成角色区、敌人区、动作区、日志区。
- 玩家攻击、防御、技能、受击、胜利有短动画或状态变化。
- 6 个 Boss 使用独立 sprite、入场提示、气氛色和战斗音乐。
- 胜利掉落用金币/经验/道具画面反馈，不只是一行文字。

验收：

- 普通战斗和 Boss 战各有截图和输入回放。
- 中文胜利反馈无英文属性混杂。
- Boss 和普通敌人第一眼可区分。

## 当前进度

- [x] 使用 Codex 内置 GPT Image 2 生成 Phase 15 战斗 sprite sheet。
- [x] 原图保存到 `assets/generated/raw/phase15/battle_sheet.png`。
- [x] Prompt 保存到 `assets/source_prompts/phase15/battle_sheet.md`。
- [x] Asset plan 保存到 `assets/generated/phase15/asset_plan.json`。
- [x] 后处理输出 13 个 32x32 battle sprite。
- [x] Contact sheet 保存到 `assets/generated/contact_sheets/phase15_battle.png`。
- [x] `assets/manifest_sprites.json` 新增 Phase 15 source 和 battle sprite id。
- [x] BattleScreen 使用玩家 idle/attack/defend、普通敌人、首领、slash、shield、reward drop sprite。
- [x] 普通战和 Boss 战有不同 sprite、边框和气氛色。
- [x] 攻击、防御、胜利奖励有短时 sprite/状态反馈。
- [x] 中文模式清理战斗开场、敌人名、Boss 阶段显示。
- [x] 新增 Phase 15 单元测试。
- [x] 固定截图完成普通战/Boss 战实景复查。
- [x] 计划索引和活跃 phase 状态已回填。

## 完成情况

实际交付：

- `assets/source_prompts/phase15/battle_sheet.md`：本次生成 prompt。
- `assets/generated/raw/phase15/battle_sheet.png`：Codex 内置 GPT Image 2 原图。
- `assets/generated/processed/phase15/*.png`：13 个战斗素材。
- `assets/generated/contact_sheets/phase15_battle.png`：人工核对用接触表。
- `assets/generated/phase15/asset_plan.json`：本阶段 asset card。
- `assets/generated/README.md`：登记 Phase 15 生成资产批次。
- `assets/manifest_sprites.json`：新增 `gpt_image_2_phase15` source 和 battle sprite id。
- `src/git_dungeon/ui_pixel/screens/battle.py`
  - 战斗中景区域使用墙面/地面 tile。
  - 玩家 idle/attack/defend 三态切换。
  - 普通敌人使用 `enemy_default_git_goblin`。
  - Boss 根据名字映射到不同 sprite。
  - 攻击显示 `fx_slash`，防御显示 `fx_shield`，胜利掉落显示 `fx_reward_drop`。
- `src/git_dungeon/ui_pixel/text.py`
  - 新增敌人名和 Boss 阶段的玩家语言 formatter。
  - 中文模式 `Battle started` 改为 `战斗开始`，`phase_1` 改为 `阶段 1`。
- `tests/unit/test_pixel_phase15.py`
  - 覆盖资产链、manifest、敌人/Boss sprite、攻击姿态、slash fx、中文敌人名和阶段文案。

本批 sprite id：

- `player_idle`
- `player_attack`
- `player_defend`
- `enemy_default_git_goblin`
- `boss_fix`
- `boss_refactor`
- `boss_merge_conflict`
- `boss_ci_sentinel`
- `boss_secret_leak`
- `boss_release_gate`
- `fx_slash`
- `fx_shield`
- `fx_reward_drop`

关键决策：

- 战斗 sprite 使用 32x32 processed 输出。原因是战斗角色比 16x16 地牢物件更需要轮廓和动作可读性，运行时仍由 SpriteCatalog 统一缩放。
- Boss 映射优先按名称关键词，未知 Boss 使用稳定的名称哈希分配到 6 个 Boss sprite 之一，不影响战斗规则。
- 普通战和 Boss 战先共享同一个战斗空间结构，Boss 用红色边框、独立 sprite 和不可逃跑按钮状态强化身份。

偏离原计划：

- 本阶段没有新增真正逐帧动画，只做短时姿态和效果 sprite。原因是 Phase 17/18 还会统一处理动画和视觉回归，Phase 15 先完成可见身份和反馈闭环。

## 后续任务

下一阶段进入 **Phase 16：事件、商店、休息重做**。

新会话立刻读取：

1. `AGENTS.md`
2. `plans/pixel-phases.md`
3. `plans/pixel-stardew-level-repair-plan.md`
4. `docs/PIXEL_UI_LAYOUT_LESSONS.md`
5. `handoffs/2026-05-08-pixel-phase-15-handoff.md`
6. `src/git_dungeon/ui_pixel/screens/event.py`
7. `src/git_dungeon/ui_pixel/screens/shop.py`
8. `src/git_dungeon/ui_pixel/screens/rest.py`
9. `assets/generated/phase15/asset_plan.json`

Phase 16 重点：

- 事件页要像地点，不再像数据面板。
- 商店需要店主、柜台、商品图标和买不起原因。
- 休息点需要营火/神龛/安全屋场景。
- 事件完成后回地牢的提示不能出现 ID、opcode 或原始字段。

已知风险：

- Boss sprite 已明显区分，但具体 Boss 类型和现有引擎只有 4 个模板完全对应；其余 sprite 作为未来扩展和未知 Boss 稳定映射使用。
- 战斗中景仍是静态 tile，后续 Phase 17 可统一加动效和整体主题 polish。
- 当前截图脚本仍是临时验证命令，Phase 18 应沉淀成正式视觉回归工具。

验证结果：

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_pixel_assets.py --asset-cards assets/generated/phase15/asset_plan.json
# OK: generated pixel assets verified

PYTHONPATH=src .venv/bin/python scripts/verify_assets.py --strict
# OK: 41/41 sprites mapped, all valid

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase15.py -q
# 6 passed

.venv/bin/python -m ruff check src/git_dungeon/ui_pixel/screens/battle.py src/git_dungeon/ui_pixel/text.py tests/unit/test_pixel_phase15.py scripts/postprocess_pixel_assets.py scripts/verify_pixel_assets.py
# All checks passed

PYTHONPATH=src .venv/bin/python -m mypy src/git_dungeon/ui_pixel/screens/battle.py src/git_dungeon/ui_pixel/text.py --ignore-missing-imports
# Success: no issues found in 2 source files

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase5.py tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/unit/test_pixel_phase10.py tests/unit/test_pixel_phase11.py tests/unit/test_pixel_phase12.py tests/unit/test_pixel_phase13.py tests/unit/test_pixel_phase14a.py tests/unit/test_pixel_phase14b.py tests/unit/test_pixel_phase14c.py tests/unit/test_pixel_phase15.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
# 56 passed

SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-phase15-smoke PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --lang zh_CN --pixel-smoke-frames 8
# passed

PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
# 418 passed, 2 skipped, 153 deselected, 2 warnings
```

截图复查：

- `assets/generated/contact_sheets/phase15_battle.png`
- `/tmp/git-dungeon-phase15-battle-contact-4x.png`
