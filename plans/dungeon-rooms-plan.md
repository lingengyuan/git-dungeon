# Pixel Phase 7-9 — 房间地牢化计划

> **状态**：Phase 7 最小闭环已完成（2026-05-05）；Phase 8 交互回放已完成（2026-05-06）；Phase 9 陷阱消耗已完成（2026-05-06）
> **上游**：[`plans/pixel-phases.md`](pixel-phases.md) Phase 7-9
> **目标**：在不破坏现有 CLI/Pixel 结算的前提下，把 Pixel 路线图推进为可移动的房间探索层。

## 1. 范围

Phase 7 先做最小可玩闭环：

- 加载仓库后进入房间地牢屏，而不是静态路线图。
- 每个现有 route node 映射为一个房间，房间之间用门连接。
- 玩家用方向键/WASD 逐格移动。
- 玩家到达当前房间后，按 Enter 进入现有战斗/事件/休息/商店流程。
- 显示可见陷阱格；Phase 9 起，玩家主动撞到陷阱会触发一次固定 HP 消耗。

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
- ✅ `tests/unit/test_pixel_phase8.py` 覆盖键盘移动、进入当前房间、陷阱提示、节点回流后位置保持。
- ✅ `tests/unit/test_pixel_phase9.py` 覆盖陷阱一次性 HP 消耗和低血量边界。

## 4. 验收

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
  PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --pixel-smoke-frames 8

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase7.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase8.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase9.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
```

## 5. Phase 8 交互打磨

Phase 8 不扩大玩法规则，只把 Phase 7 的真实操作链路纳入自动验证：

- 未站在当前房间时，Enter 不进入节点，并提示先移动。
- 方向键/WASD 能把玩家移动到当前房间，位置写回 runner。
- 到达当前房间后，Enter 会进入原有节点屏幕。
- 走向陷阱时优先显示陷阱提示，不被普通无门提示覆盖。
- 节点完成后回到 DungeonScreen 时复用上一房间位置，不跳回起点。

## 6. Phase 9 陷阱消耗

Phase 9 给陷阱增加明确资源代价，但不改主线节点和自动通关路径：

- 每个陷阱有固定伤害值。
- 玩家第一次撞到陷阱时扣除真实 HP，并显示实际损失。
- 同一个陷阱触发后变为已触发状态，再撞不会重复扣血。
- 陷阱不会把 HP 降到 0，避免在地牢层新增第二套失败流程。

## 7. 后续扩展

- 地牢房间加入分支和钥匙门。
- 清理旧 MapScreen，或把它改成明确的调试视图。
