# Pixel Phase 14C Handoff

## 背景

Phase 14B 已经用 Codex 内置 GPT Image 2 生成并接入了第一批地牢基础素材，但地牢界面仍然是抽象节点图。Phase 14C 的目标是把这些素材真正放进 DungeonScreen，让玩家看到地面、墙、门、走廊、陷阱、宝箱、钥匙和宝库，而不是只看到线框节点。

上游约束：

- 只能使用已经通过 Phase 14B asset card、contact sheet 和 manifest 校验的素材。
- 地牢视觉改造不得改变 CLI 自动路径、节点结算和主线流程。
- 玩家可见属性和损失提示必须走统一 formatter，不能重新拼 `HP/Gold` 这类内部词。
- 每个 phase 完成后必须写 handoff、提交并推送 GitHub。

## 目标

原计划交付：

- 地面、墙、门、走廊替换抽象连线。
- 当前房间、可进入房间、锁门、陷阱、已领取奖励、宝库状态用物件表达。
- 陷阱靠近/选中时显示预计损失。
- 奖励领取后保留打开宝箱或空补给箱。
- 首次进入地牢有短引导。

验收：

- 固定 seed 截图能看出入口、道路、当前房间、可互动对象和危险。
- 鼠标点击房间、锁门、陷阱、奖励都有正确行为或说明。
- CLI/Pixel 自动结果不被 tile 表现改动破坏。

## 当前进度

- [x] `DungeonScreen` 接入 Phase 14B tile、门、走廊、陷阱、宝箱、钥匙、宝库、当前房间和 boss gate 素材。
- [x] 地牢背景由抽象节点图改为 10x5 tile 场景。
- [x] 奖励领取状态映射为关闭/打开宝箱、钥匙、锁住/打开宝库。
- [x] 陷阱已触发状态映射为 armed/spent 两种 sprite。
- [x] 鼠标停在陷阱上时，action bar 显示预计生命损失。
- [x] 门和走廊绘制顺序已调整，避免被地板遮盖。
- [x] 新增 Phase 14C 单元测试。
- [x] 固定截图完成实景复查。
- [x] 计划索引和活跃 phase 状态已回填。

## 完成情况

实际交付：

- `src/git_dungeon/ui_pixel/screens/dungeon.py`
  - 使用 `tile_wall_stone` 和 `tile_floor_stone` 绘制地牢空间。
  - 使用 `tile_corridor` 和 `door_open` 绘制连接。
  - 使用 `trap_spikes_armed` / `trap_spikes_spent` 表达陷阱状态。
  - 使用 `chest_closed` / `chest_open`、`key_iron`、`vault_locked` / `vault_open` 表达奖励、钥匙和宝库。
  - 使用 `room_marker_current` / `room_marker_available` 表达当前房间和可进入房间。
  - boss 房间使用 `boss_gate` 强化身份。
  - 陷阱 hover 提示统一输出，例如中文为 `陷阱: 生命 -8`。
- `tests/unit/test_pixel_phase14c.py`
  - 覆盖地牢 tile 场景 sprite 是否实际绘制。
  - 覆盖已领取奖励是否切到打开状态。
  - 覆盖陷阱 hover 预计损失提示。
- `AGENTS.md` / `CLAUDE.md`
  - 当前活跃 plan 更新为 Phase 0-14C 已完成，下一步 Phase 15。
- `plans/README.md`
- `plans/pixel-phases.md`
- `plans/pixel-stardew-level-repair-plan.md`
  - 回填 Phase 14C 完成状态和 handoff 链接。

关键决策：

- Phase 14C 只改 DungeonScreen 视觉层，不改 `git_dungeon.ui_pixel.dungeon` 的确定性房间布局和奖励/陷阱规则。
- 门和走廊必须在地板之后绘制，否则细小连接会被地板 tile 遮住。
- 陷阱 hover 直接复用 `stat_delta`，避免在 screen 里再次发明属性文案。

偏离原计划：

- “首次进入地牢短引导”沿用当前已有顶部消息和 action bar，没有新增独立弹窗。原因是 Phase 14A 已经建立统一 action bar，新增弹窗会增加遮挡风险，且 14C 的核心是 tile 场景接入。

## 后续任务

下一阶段进入 **Phase 15：战斗场景和 Boss 身份**。

新会话立刻读取：

1. `AGENTS.md`
2. `plans/pixel-phases.md`
3. `plans/pixel-stardew-level-repair-plan.md`
4. `docs/PIXEL_UI_LAYOUT_LESSONS.md`
5. `handoffs/2026-05-08-pixel-phase-14c-handoff.md`
6. `src/git_dungeon/ui_pixel/screens/battle.py`
7. `src/git_dungeon/ui_pixel/screens/dungeon.py`
8. `assets/generated/phase14b/asset_plan.json`

Phase 15 重点：

- 战斗画面拆成角色区、敌人区、动作区、日志区。
- 玩家攻击、防御、技能、受击、胜利要有更明确的画面反馈。
- Boss 和普通敌人第一眼要能区分。
- Boss 入场、气氛色和战斗音乐需要统一。
- 胜利掉落不能只是一行文字，要用金币/经验/道具反馈。

已知风险：

- Phase 14B 生成的素材风格已经能进入游戏，但墙面和地面仍偏暗，后续 Phase 17 需要统一做美术 polish。
- 地牢仍然是静态 tile，没有逐帧动画。动画统一放到 Phase 17/18 前后处理更合适。
- 当前截图脚本仍是临时验证命令，Phase 18 应沉淀成正式视觉回归工具。

验证结果：

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase14c.py -q
# 3 passed

.venv/bin/python -m ruff check src/git_dungeon/ui_pixel/screens/dungeon.py tests/unit/test_pixel_phase14c.py
# All checks passed

PYTHONPATH=src .venv/bin/python -m mypy src/git_dungeon/ui_pixel/screens/dungeon.py --ignore-missing-imports
# Success: no issues found in 1 source file

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase5.py tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/unit/test_pixel_phase10.py tests/unit/test_pixel_phase11.py tests/unit/test_pixel_phase12.py tests/unit/test_pixel_phase13.py tests/unit/test_pixel_phase14a.py tests/unit/test_pixel_phase14b.py tests/unit/test_pixel_phase14c.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
# 50 passed

SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-phase14c-smoke PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --lang zh_CN --pixel-smoke-frames 8
# passed

PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
# 412 passed, 2 skipped, 153 deselected, 2 warnings
```

截图复查：

- `/tmp/git-dungeon-phase14c-dungeon-4x.png`
