# Pixel Phase 7 — 房间地牢化计划

> **状态**：已完成最小闭环（2026-05-05）
> **上游**：[`plans/pixel-phases.md`](pixel-phases.md) Phase 7
> **目标**：在不破坏现有 CLI/Pixel 结算的前提下，把 Pixel 路线图推进为可移动的房间探索层。

## 1. 范围

Phase 7 先做最小可玩闭环：

- 加载仓库后进入房间地牢屏，而不是静态路线图。
- 每个现有 route node 映射为一个房间，房间之间用门连接。
- 玩家用方向键/WASD 逐格移动。
- 玩家到达当前房间后，按 Enter 进入现有战斗/事件/休息/商店流程。
- 显示可见陷阱格；本阶段陷阱只阻挡移动，不改 HP/Gold/EXP，避免破坏 Phase 6 parity。

## 2. 非目标

- 不做自由探索掉落。
- 不新增第二套战斗、奖励或章节规则。
- 不改变 CLI 自动模式结果。
- 不做随机生成大地图；先用当前 chapter route 生成紧凑房间路径。

## 3. 交付

- ✅ `src/git_dungeon/ui_pixel/dungeon.py`：纯数据房间布局。
- ✅ `src/git_dungeon/ui_pixel/screens/dungeon.py`：房间探索屏。
- ✅ 加载后默认进入 DungeonScreen。
- ✅ 战斗/事件/休息/商店结束后回到 DungeonScreen。
- ✅ `tests/unit/test_pixel_phase7.py` 覆盖房间顺序、当前房间、门、陷阱。

## 4. 验收

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
  PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --pixel-smoke-frames 8

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase7.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
```

## 5. 后续扩展

- 陷阱从“阻挡”升级为明确的、可预测的消耗，并同步 CLI/Pixel parity。
- 地牢房间加入分支和钥匙门。
- 增加 UI 事件回放测试，验证键盘移动和进入房间流程。
