# Pixel Phase 13 Handoff

## 背景

Phase 0-12 已经完成 Pixel mode 最小闭环，但真实窗口试玩后发现它仍更像“像素 UI 原型”，不是稳定可读的像素游戏体验。`plans/pixel-game-issues.md` 记录了 44 个问题，其中最高优先级集中在窗口安全、中文混杂、地牢状态不清、运行中退出危险、音频调试标签外露和设置页开发信息外露。

## 目标

本 phase 的目标是先修玩家第一分钟会遇到的问题：

- 默认窗口不再过大。
- 普通界面不显示正常音频槽位。
- 中文模式使用玩家语言表达属性、奖励、钥匙和动作。
- 地牢底部显示当前可执行动作。
- 地牢奖励、钥匙、宝库、陷阱、已领取、当前房间有更清楚的视觉状态。
- 鼠标点击相邻房间可以移动。
- 运行中 `Esc/Q` 打开暂停确认，不直接退出。
- 设置页不默认展示配置文件路径。

## 当前进度

- [x] 修复计划已写入 `plans/pixel-game-fix-plan.md`。
- [x] `plans/pixel-phases.md` 已新增 Phase 13-18 路线。
- [x] Phase 13 代码和测试已完成。
- [x] 真实渲染截图已检查：标题页和地牢页均能正常显示。
- [x] 验证命令已通过。

## 完成情况

实际交付：

- 默认窗口从 1280x720 改为 960x540，仍保持 320x180 逻辑画布的整数缩放。
- 新增运行中暂停确认页，地牢、战斗、事件、休息、商店按 `Esc` 会进入暂停，不再直接退出。
- 新增玩家文案工具，中文模式显示“生命、魔力、攻击、金币、铁钥匙”等，不再在地牢和战斗 HUD 暴露 `HP/MP/ATK/Gold`。
- 普通音频状态不再显示 `Audio: chapter`；只有静音或错误状态仍会显示。
- 地牢页新增更清楚的房间表现：地砖、粗通道、陷阱形状、钥匙形状、锁形状、补给箱状态、当前房间双框、已访问标记、HUD 钥匙位。
- 地牢底部动作提示会随状态变化，例如进入当前房间、领取奖励、需要钥匙。
- 鼠标点击相邻格会移动；点击远处格会给出可理解提示。
- 设置页隐藏配置文件路径。
- 新增 `tests/unit/test_pixel_phase13.py`，覆盖窗口尺寸、音频标签隐藏、中文玩家文案、暂停确认、鼠标移动。

偏离原计划：

- 本 phase 没有接入真正的新 tile art、标题大背景、Boss 独立资产或完整暂停设置页。这些需要资产和更大布局调整，已经放入 Phase 14-17。
- `make lint` 没有作为最终通过项使用，因为 Makefile 固定调用全局 `python3`，当前全局环境没有 ruff。已用项目 `.venv` 运行同等 ruff 和 mypy 检查。

## 后续任务

下一阶段建议直接进入 **Phase 14：真正的 tile 房间表现**。

Phase 14 需要优先读：

- `plans/pixel-game-fix-plan.md`
- `plans/pixel-game-issues.md`
- `src/git_dungeon/ui_pixel/screens/dungeon.py`
- `src/git_dungeon/ui_pixel/dungeon.py`
- `tests/unit/test_pixel_phase13.py`

已知风险：

- 当前地牢还是用代码绘制基础形状，不是真正完整 tile 场景。Phase 14 要把房间、墙、门、走廊进一步游戏化。
- 暂停页目前只做继续和退出确认，还没有接入运行中设置页。Phase 16 需要补。
- 中文文案已覆盖第一批高频 HUD 和奖励反馈，但事件、商店和战斗日志仍需要后续继续清理玩家文案。

验证命令：

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase13.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase5.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase10.py tests/unit/test_pixel_phase12.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/unit/test_pixel_phase10.py tests/unit/test_pixel_phase11.py tests/unit/test_pixel_phase12.py tests/unit/test_pixel_phase13.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-phase13-smoke PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --lang zh_CN --pixel-smoke-frames 8
.venv/bin/python -m ruff check src/ tests/
PYTHONPATH=src .venv/bin/python -m mypy src/ --ignore-missing-imports
```
