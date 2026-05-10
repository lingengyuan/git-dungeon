# Pixel Phase 24 Handoff

## 背景

Phase 23 已经让地牢页显示近期事件和房间进度。Phase 24 的目标是继续做内容体验打磨：不改底层规则，不新增移动端/手柄，只让 PC 玩家更容易理解每个房间的意义和刚拿到的奖励类型。

上游约束：

- 不引入新玩法规则。
- 不新增生成素材，先复用现有像素素材和 UI。
- 文案要短，适合 320x180 像素画布。
- 中文模式要完整可读。

## 目标

原计划交付：

- 地牢房间有更明确的身份说明。
- 鼠标悬停到房间时，底部提示说明这个房间会发生什么。
- 奖励日志区分补给、钥匙和宝库。
- 自动测试覆盖中文文案和悬停提示。

## 当前进度

- [x] 新增房间标题和房间说明文案。
- [x] 地牢页悬停到路线房间时显示房间说明。
- [x] 奖励日志区分 `Cache opened`、`Key found`、`Vault opened`。
- [x] 新增 Phase 24 单元测试。
- [x] 生成 Phase 24 截图包确认核心页面仍可渲染。

## 完成情况

实际交付：

- `src/git_dungeon/ui_pixel/text.py`
  - 新增 Battle/Event/Rest/Shop/Elite/Boss 房间标题和描述。
  - 新增补给/宝库开启日志文案。
- `src/git_dungeon/ui_pixel/screens/dungeon.py`
  - 悬停路线房间时，底部操作栏显示“房间类型：用途说明”。
- `src/git_dungeon/ui_pixel/game_runner.py`
  - 奖励领取日志按补给、钥匙、宝库区分。
- `tests/unit/test_pixel_phase24.py`
  - 覆盖房间身份中文文案和悬停提示。

关键决策：

- 本 phase 做“解释真实内容”，不做装饰性剧情文本。原因是当前最影响体验的是玩家能否快速理解房间含义。
- 不生成新图。现有 Phase 14B-17 的素材已经覆盖主要房间和奖励类型，本 phase 的收益主要来自反馈和文案。

偏离原计划：

- 没有新增事件池或敌人池。内容数量扩展会影响平衡，应该另开玩法 phase。

## 后续任务

下一 phase：Phase 25 PC 发布前固定。

建议立刻读：

1. `plans/pixel-phases.md`
2. `plans/pixel-phase18-final-playtest.md`
3. `scripts/render_pixel_screens.py`
4. `tests/unit/test_pixel_phase18.py`
5. `tests/integration/test_pixel_smoke.py`

已知风险：

- 当前房间说明是短提示，不是完整教程；后续如果加入新房间类型，需要同步补 `ROOM_TITLES` 和 `ROOM_DESCRIPTIONS`。
- 悬停提示依赖鼠标；键盘玩家仍主要看新手页和底部默认操作提示。

验证结果：

```bash
PYTHONPATH=src .venv/bin/python -m ruff check src/git_dungeon/ui_pixel/game_runner.py src/git_dungeon/ui_pixel/screens/dungeon.py src/git_dungeon/ui_pixel/text.py tests/unit/test_pixel_phase24.py
# All checks passed

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase24.py tests/unit/test_pixel_phase23.py tests/unit/test_pixel_phase22.py -q
# 7 passed

SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=src .venv/bin/python scripts/render_pixel_screens.py --out-dir /tmp/git-dungeon-phase24-screens --scale 2
# rendered 20 screenshots to /tmp/git-dungeon-phase24-screens
```
