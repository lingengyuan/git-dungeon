# Pixel Phase 17 Handoff

## 背景

Phase 16 已经把事件、商店、休息改成有地点感的非战斗场景。Phase 17 继续解决“像通用地牢模板”的问题：标题页缺少正式入口，Git 主题物件还没有进入世界，美术、基础动效和音乐记录没有统一。

上游约束：

- 标题和主题表现可以增强，但不能改变输入、结算、CLI 自动路径或 Pixel/CLI parity。
- 新主题素材必须走 prompt、raw、processed、contact sheet、asset card、manifest、校验。
- BGM 必须保留来源、license、用途、循环和响度处理记录。
- 每个 phase 完成后必须写 handoff、提交并推送 GitHub。

## 目标

原计划交付：

- 标题页有正式背景、banner、角色或地牢入口。
- Git 主题物件进入世界：commit shard、branch door、merge conflict trap、CI sentinel、release gate。
- 每章有轻量 palette 和地砖变化。
- BGM 完成试听、响度统一、循环处理和用途记录。
- 基础待机动画：火把、陷阱、奖励、按钮、角色 idle。

验收：

- 标题页第一眼能看出这是 Git Dungeon，不是通用地牢模板。
- 音乐切换不突兀，普通界面不显示音频调试文字。
- 资产 manifest、CREDITS、asset cards 完整。

## 当前进度

- [x] 使用 Codex 内置 GPT Image 2 生成 Phase 17 theme sprite sheet。
- [x] 原图保存到 `assets/generated/raw/phase17/theme_sheet.png`。
- [x] Prompt 保存到 `assets/source_prompts/phase17/theme_sheet.md`。
- [x] Asset plan 保存到 `assets/generated/phase17/asset_plan.json`。
- [x] 后处理输出 8 个主题 sprite。
- [x] Contact sheet 保存到 `assets/generated/contact_sheets/phase17_theme.png`。
- [x] `assets/manifest_sprites.json` 新增 Phase 17 source 和 theme sprite id。
- [x] 标题页接入 banner、地牢入口、火把、玩家和 CI sentinel。
- [x] 地牢页接入 branch door、commit shard、merge conflict trap、CI sentinel、release gate。
- [x] 地牢页增加章节 accent palette 和轻量地砖变化。
- [x] 标题页、地牢页增加基础 idle/pulse 动效。
- [x] BGM 完成响度复查和重编码，记录到 `assets/audio/bgm/USAGE.md`。
- [x] 新增 Phase 17 单元测试。
- [x] 计划索引和活跃 phase 状态已回填。

## 完成情况

实际交付：

- `assets/source_prompts/phase17/theme_sheet.md`：本次生成 prompt。
- `assets/generated/raw/phase17/theme_sheet.png`：Codex 内置 GPT Image 2 原图。
- `assets/generated/processed/phase17/*.png`：8 个主题素材。
- `assets/generated/contact_sheets/phase17_theme.png`：人工核对用接触表。
- `assets/generated/phase17/asset_plan.json`：本阶段 asset card。
- `assets/generated/README.md`：登记 Phase 17 生成资产批次。
- `assets/manifest_sprites.json`：新增 `gpt_image_2_phase17` source 和 theme sprite id。
- `src/git_dungeon/ui_pixel/screens/title.py`
  - 标题页加入 tile 背景、正式 banner、地牢入口、火把、玩家和 CI sentinel。
  - 中文模式副标题改为“像素模式”。
  - 火把有轻量 idle 位移。
- `src/git_dungeon/ui_pixel/screens/dungeon.py`
  - 门改为 `branch_door`。
  - 普通奖励改为 `commit_shard`。
  - 陷阱改为 `merge_conflict_trap`。
  - elite 使用 `ci_sentinel`，boss 使用 `release_gate`。
  - 章节 accent palette 影响标题、面板边框、地砖点缀和当前房间 pulse。
  - 玩家 idle 有轻量上下浮动。
- `src/git_dungeon/ui_pixel/audio.py`
  - 新增 `BGM_LOOPS`，明确 title/chapter/boss 循环，gameover 不循环。
- `assets/audio/bgm/USAGE.md`
  - 记录每个 BGM 槽位用途、循环和 Phase 17 后的响度。
- `assets/CREDITS.md`
  - 更新 BGM 处理记录。
  - 更新已接入 AI 生成资源批次。
- `scripts/postprocess_pixel_assets.py`
  - 支持洋红 chroma-key。
  - 对生成图网格线做边缘内收和背景清理，避免抠图残留。
- `tests/unit/test_pixel_phase17.py`
  - 覆盖资产链、manifest、标题主题素材、地牢主题物件、章节 palette、BGM loop policy。

本批 sprite id：

- `title_banner`
- `dungeon_entrance`
- `commit_shard`
- `branch_door`
- `merge_conflict_trap`
- `ci_sentinel`
- `release_gate`
- `torch_lit`

关键决策：

- Phase 17 改用洋红色 chroma-key 重新生成主题素材。原因是 Git 主题需要绿色/青色，绿色背景会和主体颜色冲突，导致抠图损伤或残留。
- 标题页保留英文游戏名 `GIT DUNGEON`，但中文模式下把副标题改为“像素模式”。
- 地牢主题替换只改视觉 sprite 和轻量 pulse，不碰路线、陷阱、奖励、钥匙、战斗入口等规则。
- BGM 只做温和音量归一，不更换来源，不引入新授权风险。

偏离原计划：

- “每章地砖变化”没有新增完整 tile set，而是先用章节 accent palette 和地砖点缀完成轻量变化。原因是 Phase 18 还要做最终视觉回归，本阶段优先保证主题统一和风险可控。
- 基础动画采用时间驱动的轻量位置/边框变化，没有新增逐帧动画 sheet。原因是当前 sprite sheet 已满足第一分钟体验，逐帧动画会显著增加素材和回归成本。

## 后续任务

下一阶段进入 **Phase 18：视觉回归和最终试玩验收**。

新会话立刻读取：

1. `AGENTS.md`
2. `plans/pixel-phases.md`
3. `plans/pixel-stardew-level-repair-plan.md`
4. `docs/PIXEL_UI_LAYOUT_LESSONS.md`
5. `handoffs/2026-05-08-pixel-phase-17-handoff.md`
6. `tests/unit/test_pixel_phase17.py`
7. `src/git_dungeon/ui_pixel/screens/title.py`
8. `src/git_dungeon/ui_pixel/screens/dungeon.py`
9. `assets/audio/bgm/USAGE.md`

Phase 18 重点：

- 把标题、地牢、战斗、事件、商店、休息、设置截图检查沉淀成稳定视觉回归。
- 覆盖中英文和多个窗口尺寸。
- 做一次完整试玩记录，关闭或明确延期剩余 P1/P2 问题。
- 检查所有玩家界面是否还有内部 ID、英文属性词、调试状态或文字溢出。

已知风险：

- Phase 17 的主题素材是 8 个核心物件，章节级 tile set 仍是轻量变化，不是完整多主题地图。
- GPT 生成图仍有少量非主体边缘像素，已通过后处理和截图复查压到运行画面不可见的程度；Phase 18 需要继续用截图守住。
- 当前截图生成命令仍是临时命令，Phase 18 应转为正式脚本或测试工具。

验证结果：

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_pixel_assets.py --asset-cards assets/generated/phase17/asset_plan.json
# OK: generated pixel assets verified

PYTHONPATH=src .venv/bin/python scripts/verify_assets.py --strict
# OK: 57/57 sprites mapped, all valid

PYTHONPATH=src .venv/bin/python scripts/verify_audio.py
# BGM: 4/4 slots filled, all vorbis OGG, all credited.
# SFX: 2 packs present with License.txt.
# OK

PYTHONPATH=src .venv/bin/python -m ruff check src/git_dungeon/ui_pixel/screens/title.py src/git_dungeon/ui_pixel/screens/dungeon.py src/git_dungeon/ui_pixel/audio.py scripts/postprocess_pixel_assets.py tests/unit/test_pixel_phase14a.py tests/unit/test_pixel_phase14c.py tests/unit/test_pixel_phase17.py
# All checks passed

PYTHONPATH=src .venv/bin/python -m mypy src/git_dungeon/ui_pixel/screens/title.py src/git_dungeon/ui_pixel/screens/dungeon.py src/git_dungeon/ui_pixel/audio.py
# Success: no issues found in 3 source files

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase14a.py tests/unit/test_pixel_phase14c.py tests/unit/test_pixel_phase17.py tests/unit/test_pixel_audio.py tests/unit/test_pixel_phase4.py -q
# 26 passed

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_assets.py tests/unit/test_pixel_audio.py tests/unit/test_pixel_phase1.py tests/unit/test_pixel_phase2.py tests/unit/test_pixel_phase3.py tests/unit/test_pixel_phase4.py tests/unit/test_pixel_phase5.py tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/unit/test_pixel_phase10.py tests/unit/test_pixel_phase11.py tests/unit/test_pixel_phase12.py tests/unit/test_pixel_phase13.py tests/unit/test_pixel_phase14a.py tests/unit/test_pixel_phase14b.py tests/unit/test_pixel_phase14c.py tests/unit/test_pixel_phase15.py tests/unit/test_pixel_phase16.py tests/unit/test_pixel_phase17.py tests/unit/test_pixel_settings.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
# 87 passed

SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-phase17-smoke PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --lang zh_CN --pixel-smoke-frames 8
# passed

PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
# 430 passed, 2 skipped, 153 deselected, 2 warnings
```

截图复查：

- `assets/generated/contact_sheets/phase17_theme.png`
- `/tmp/git-dungeon-phase17-title-4x.png`
- `/tmp/git-dungeon-phase17-dungeon-4x.png`

备注：

- BGM 初次归一时尝试 `libvorbis` 失败；本机 ffmpeg 无该编码器。已恢复原文件后，使用 `vorbis -strict -2` 重新生成并通过 `verify_audio.py`。
