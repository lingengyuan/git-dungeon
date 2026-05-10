# Pixel Phase 18 Final Playtest

> 日期：2026-05-08
> 范围：Phase 13-18 修复线最终验收。
> 目标：确认 Pixel mode 第一视口体验、核心页面截图、玩家语言、窗口缩放和可访问性基础选项不再回退。

## 截图包

固定截图脚本：

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=src .venv/bin/python scripts/render_pixel_screens.py --out-dir /tmp/git-dungeon-phase18-screens --scale 4
```

输出：

- `/tmp/git-dungeon-phase18-screens/contact.png`
- `/tmp/git-dungeon-phase18-screens/manifest.json`
- 英文：title、dungeon、battle、event、shop、rest、settings
- 中文：title、dungeon、battle、event、shop、rest、settings

截图复查结果：

- 标题页：标题、入口、角色、设置按钮没有重叠；中文副标题为“像素模式”。
- 地牢页：生命/魔力/攻击/金币与面板线条不重叠；门、冲突陷阱、commit shard、CI sentinel、release gate 可见。
- 战斗页：双方生命和攻击信息对齐，按钮和底部日志不重叠。
- 事件页：事件标题、描述、选择、风险/奖励图标可读；不显示 `event_id` / `choice_id`。
- 商店页：商品标题、价格、效果和买不起原因可读；中文不显示 raw offer label。
- 休息页：营火/神龛场景和治疗/专注选择可读。
- 设置页：高对比、文字大小、减少动画选项可见；按钮文字不再截断；底部提示不贴边。

本轮截图复查中发现并修复：

- 设置页新增可访问性按钮文字过长，被截成 `Reduce ...`。
- 设置页底部提示贴近面板下边缘。

## 视觉回归保护

新增脚本：

- `scripts/render_pixel_screens.py`
  - 生成中英文 7 个核心屏幕截图。
  - 生成 `manifest.json`，记录语言、屏幕名、路径和尺寸。

新增测试：

- `tests/unit/test_pixel_phase18.py`
  - 验证截图脚本能生成所有核心屏幕。
  - 验证 960x540、1280x720、1440x900 使用整数倍缩放或安全留边。
  - 验证高对比、文字大小、减少动画可以保存、加载和在设置页切换。

窗口缩放修复：

- `scale_rect` / `window_to_logical` 优先使用整数倍缩放。
- 960x540 = 3x，1280x720 = 4x。
- 1440x900 使用 4x 画布居中，避免 4.5x 导致像素发糊。

## 可访问性基础选项

新增设置项：

- `text_size = "normal" | "large"`
- `high_contrast = true | false`
- `reduce_motion = true | false`

实际效果：

- 文字大小会影响 `PixelFont` 的渲染字号。
- 高对比会影响标题页、地牢页、设置页的关键边框/强调色。
- 减少动画会停止标题页和地牢页的轻量 idle/pulse 时间推进。

## 问题关闭清单

P0：

| ID | 状态 | 说明 |
|---|---|---|
| PX-001 | 已关闭 | 默认窗口为 960x540；常见尺寸缩放已测试。 |
| PX-002 | 已关闭 | Phase 14A-18 持续修复标题、地牢、战斗、设置布局。 |
| PX-003 | 已关闭 | 中文玩家语言层覆盖属性、奖励、商店、事件、音频状态。 |
| PX-004 | 已关闭 | 地牢已改为 tile world。 |
| PX-005 | 已关闭 | 补给、钥匙、宝库、陷阱、精英、Boss 使用独立视觉身份。 |
| PX-006 | 已关闭 | 玩家位置、当前房间、奖励、锁定、陷阱状态已分离。 |
| PX-007 | 已关闭 | 当前动作条和按钮给出下一步动作。 |
| PX-008 | 已关闭 | 奖励、陷阱、战斗胜利加入状态 sprite / 反馈。 |
| PX-009 | 已关闭 | 运行中 Esc/Q 进入暂停确认，不再直接退出。 |
| PX-010 | 已关闭 | 已加入截图脚本和 Phase 18 回归测试。 |

P1：

| ID | 状态 | 说明 |
|---|---|---|
| PX-011 | 已关闭 | 标题页加入专属 banner、地牢入口、角色、火把和 CI sentinel。 |
| PX-012 | 已关闭 | gpt-image-2 生成地牢、战斗、非战斗、主题四批项目专属素材。 |
| PX-013 | 已关闭 | Boss sprite 和 Boss 战区别已接入。 |
| PX-014 | 已关闭 | 战斗加入角色/敌人 sprite、攻击、防御、奖励反馈。 |
| PX-015 | 已关闭 | 玩家文案层清理 event/shop/battle 原始字段。 |
| PX-016 | 已关闭 | 统一按钮、卡片、action bar、dialog、toast/tooltip 基础 UI。 |
| PX-017 | 已关闭 | 地牢支持点击相邻房间移动、查看陷阱/奖励/锁门提示。 |
| PX-018 | 已关闭 | action bar 根据当前房间、奖励、陷阱、锁门变化。 |
| PX-019 | 已关闭 | 普通音频槽位不再显示，静音/错误才显示。 |
| PX-020 | 延期 | 大仓库后台加载仍未做；当前 Phase 18 只保证加载错误可见和小/中仓库 smoke。 |
| PX-021 | 已关闭 | 陷阱 hover/选中显示预计生命损失。 |
| PX-022 | 已关闭 | HUD 有钥匙状态，宝库显示锁定需求。 |
| PX-023 | 已关闭 | 标题、地牢、战斗已有基础 idle/pulse/反馈动效。 |
| PX-024 | 已关闭 | Phase 20 已完成暂停页进入设置、退出本局回标题页和暂停页截图覆盖。 |
| PX-025 | 已关闭 | 地牢有 tile、门、走廊、分支、奖励、宝库和 Boss 门推进。 |

P2：

| ID | 状态 | 说明 |
|---|---|---|
| PX-026 | 已关闭 | Phase 17 加入章节 accent palette。 |
| PX-027 | 已关闭 | 主世界、战斗、非战斗场景的视觉占比已提升。 |
| PX-028 | 已关闭 | 细线已由 corridor / branch door 表现替代。 |
| PX-029 | 已关闭 | 奖励领取后保留打开/领取状态。 |
| PX-030 | 已关闭 | 战斗角色区、敌人区、按钮区、日志区已拆分。 |
| PX-031 | 已关闭 | 商店有店主、柜台、商品标题、价格、效果和买不起反馈。 |
| PX-032 | 已关闭 | 事件有地点、标题、描述、选择和后果预览。 |
| PX-033 | 已关闭 | 休息点有营火/神龛地点感。 |
| PX-034 | 已关闭 | 设置页不显示配置文件路径。 |
| PX-035 | 已关闭 | Phase 21 已完成设置页窗口/全屏即时切换，继续保留整数倍缩放。 |
| PX-036 | 延期 | 手柄支持未进入 Phase 13-18 范围。 |
| PX-037 | 已关闭 | 已支持文字大小、高对比、减少动画基础选项。 |
| PX-038 | 已关闭 | BGM 完成响度统一、循环策略和用途记录。 |
| PX-039 | 延期 | 近期事件日志/章节总结未做，属于后续内容体验。 |
| PX-040 | 延期 | 首次游玩教学未做，Phase 18 先确保第一分钟界面自解释。 |

## 最终验证命令

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase18.py -q
# 4 passed

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_assets.py tests/unit/test_pixel_audio.py tests/unit/test_pixel_phase1.py tests/unit/test_pixel_phase2.py tests/unit/test_pixel_phase3.py tests/unit/test_pixel_phase4.py tests/unit/test_pixel_phase5.py tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/unit/test_pixel_phase10.py tests/unit/test_pixel_phase11.py tests/unit/test_pixel_phase12.py tests/unit/test_pixel_phase13.py tests/unit/test_pixel_phase14a.py tests/unit/test_pixel_phase14b.py tests/unit/test_pixel_phase14c.py tests/unit/test_pixel_phase15.py tests/unit/test_pixel_phase16.py tests/unit/test_pixel_phase17.py tests/unit/test_pixel_phase18.py tests/unit/test_pixel_settings.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
# 91 passed

PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
# 434 passed, 2 skipped, 153 deselected, 2 warnings
```
