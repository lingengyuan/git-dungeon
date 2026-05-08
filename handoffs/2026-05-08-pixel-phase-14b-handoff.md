# Pixel Phase 14B Handoff

## 背景

Phase 14A 已经统一了 UI kit 和玩家语言层，但地牢仍在使用 Kenney 旧素材和抽象节点图。Phase 14B 的目标不是马上重做地图，而是先建立一条可追溯、可验证的 gpt-image-2 素材流水线，确保后续 Phase 14C 接入 tile 场景时不会把未经核对的图片直接塞进游戏。

上游约束：

- 使用 Codex 内置 GPT Image 2 生成，不依赖 OpenAI API 或 `OPENAI_API_KEY`。
- 生成图不等于运行时资产，必须经过 prompt、raw、processed、contact sheet、asset card、manifest、校验。
- 素材接入不得改变 CLI 自动路径和主线结算。
- 每个 phase 完成后必须写 handoff、提交并推送 GitHub。

## 目标

原计划交付：

- `scripts/postprocess_pixel_assets.py`
- `scripts/verify_pixel_assets.py`
- 使用 Codex GPT Image 2 生成 Phase 14 第一批地牢素材。
- Phase 14 第一批地牢素材完成 prompt/raw/processed/contact sheet/asset card。
- 通过人工核对后写入 manifest。

验收：

- Codex 生成失败时必须保持素材 pending，不得写入假文件或空白图。
- 所有 processed 素材尺寸、透明/满格 tile 语义、manifest 路径、asset card 完整。
- contact sheet 小尺寸可读。

## 当前进度

- [x] AGENTS/CLAUDE 增加强制原则：Phase 14B-18 每个 phase 完成后验证、handoff、提交并推送。
- [x] GPT Image 2 生成地牢基础素材 sheet。
- [x] 原图保存到 `assets/generated/raw/phase14b/dungeon_sheet.png`。
- [x] Prompt 保存到 `assets/source_prompts/phase14b/dungeon_sheet.md`。
- [x] Asset plan/card 保存到 `assets/generated/phase14b/asset_plan.json`。
- [x] 后处理脚本把 sheet 切分为 15 个 16x16 processed sprite。
- [x] Contact sheet 保存到 `assets/generated/contact_sheets/phase14b_dungeon.png`。
- [x] `assets/manifest_sprites.json` 新增 generated source 和 15 个 sprite id。
- [x] `scripts/verify_pixel_assets.py` 校验 asset card、processed sprite、contact sheet 和 manifest。
- [x] Phase 14B 单元测试覆盖资产链、尺寸和 manifest 映射。

## 完成情况

实际交付：

- `assets/source_prompts/phase14b/dungeon_sheet.md`：本次生成 prompt。
- `assets/generated/raw/phase14b/dungeon_sheet.png`：Codex 内置 GPT Image 2 原图。
- `assets/generated/processed/phase14b/*.png`：15 个 16x16 地牢基础素材。
- `assets/generated/contact_sheets/phase14b_dungeon.png`：人工核对用接触表。
- `assets/generated/phase14b/asset_plan.json`：本阶段 asset card 和处理配置。
- `scripts/postprocess_pixel_assets.py`：按配置切分、去背景、裁切、nearest 缩放。
- `scripts/verify_pixel_assets.py`：校验生成素材链和 runtime manifest。
- `tests/unit/test_pixel_phase14b.py`：Phase 14B 回归测试。
- `assets/manifest_sprites.json`：新增 `gpt_image_2_phase14b` source 和 `tile_floor_stone` 等 15 个 sprite id。

本批 sprite id：

- `tile_floor_stone`
- `tile_wall_stone`
- `tile_corridor`
- `door_open`
- `door_locked`
- `chest_closed`
- `chest_open`
- `trap_spikes_armed`
- `trap_spikes_spent`
- `key_iron`
- `vault_locked`
- `vault_open`
- `room_marker_current`
- `room_marker_available`
- `boss_gate`

关键决策：

- 先用单张 sheet 生成，避免 15 次生成带来风格漂移。
- 后处理使用格子切分和边缘 flood-fill 去背景。地砖、墙、陷阱这类满格 tile 允许不透明四角；图标类素材保留透明背景。
- Phase 14B 只建立素材流水线和 manifest，不改变 DungeonScreen 的渲染逻辑。实际接入 tile 场景放到 Phase 14C。

偏离原计划：

- `scripts/build_contact_sheet.py` 已在 Phase 0 存在，本阶段复用它生成 Phase 14B contact sheet，没有重写。
- Asset card 使用 JSON：`assets/generated/phase14b/asset_plan.json`。原因是校验脚本可以只依赖标准库，不引入 YAML 解析依赖。

## 后续任务

下一阶段进入 **Phase 14C：地牢 tile 场景重做**。

新会话立刻读取：

1. `AGENTS.md`
2. `plans/pixel-phases.md`
3. `plans/pixel-stardew-level-repair-plan.md`
4. `docs/PIXEL_UI_LAYOUT_LESSONS.md`
5. `handoffs/2026-05-08-pixel-phase-14b-handoff.md`
6. `assets/generated/phase14b/asset_plan.json`
7. `src/git_dungeon/ui_pixel/screens/dungeon.py`

Phase 14C 重点：

- DungeonScreen 使用 Phase 14B 的 tile、门、箱子、陷阱、钥匙、宝库、boss gate 素材。
- 地牢从抽象节点连线改成 tile 场景。
- 陷阱靠近/选中时显示预计损失。
- 奖励领取后保留打开后的宝箱或空补给箱。
- 保持 CLI/Pixel 自动结果不变。

已知风险：

- Phase 14B contact sheet 小尺寸可读，但部分素材来自同张 sheet 的缩放，最终美术仍需在 Phase 14C 实景里复查。
- 当前生成资产只有静态单帧，没有动画帧。

验证结果：

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_pixel_assets.py --asset-cards assets/generated/phase14b/asset_plan.json
# OK: generated pixel assets verified

PYTHONPATH=src .venv/bin/python scripts/verify_assets.py --strict
# OK: 28/28 sprites mapped, all valid

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase14b.py -q
# 4 passed

.venv/bin/python -m ruff check AGENTS.md CLAUDE.md scripts/postprocess_pixel_assets.py scripts/verify_pixel_assets.py tests/unit/test_pixel_phase14b.py
# passed

PYTHONPATH=src .venv/bin/python -m mypy scripts/postprocess_pixel_assets.py scripts/verify_pixel_assets.py --ignore-missing-imports
# passed

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase5.py tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/unit/test_pixel_phase10.py tests/unit/test_pixel_phase11.py tests/unit/test_pixel_phase12.py tests/unit/test_pixel_phase13.py tests/unit/test_pixel_phase14a.py tests/unit/test_pixel_phase14b.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
# 47 passed

SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-phase14b-smoke PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --lang zh_CN --pixel-smoke-frames 8
# passed

PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
# 409 passed, 2 skipped, 153 deselected, 2 warnings
```

截图复查：

- `assets/generated/contact_sheets/phase14b_dungeon.png`
