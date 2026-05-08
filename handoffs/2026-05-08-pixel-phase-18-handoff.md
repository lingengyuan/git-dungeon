# Pixel Phase 18 Handoff

## 背景

Phase 17 已经完成标题、Git 主题物件、基础动效和 BGM 统一。Phase 18 是本轮 Phase 13-18 修复线的收口：防止后续改动再次造成文字溢出、内部字段暴露、非整数缩放、可访问性缺项和截图无法复查。

上游约束：

- 视觉回归要能重复执行，不能只依赖一次人工截图命令。
- 中英文标题、地牢、战斗、事件、商店、休息、设置都要覆盖。
- 常见窗口尺寸要保持像素清晰。
- 高对比、文字大小、减少动画要成为实际设置项。
- 每个 phase 完成后必须写 handoff、提交并推送 GitHub。

## 目标

原计划交付：

- 中英文标题、地牢、战斗、事件、商店、休息、设置截图检查。
- 常见窗口尺寸检查：960x540、1280x720、全屏整数倍。
- 禁止内部 ID/英文属性混杂的界面文本测试。
- 高对比、文字大小、减少动画的基础选项。
- 完整手动试玩记录和最终问题清单。

验收：

- 新玩家从标题进入一局，能在不看代码/文档的情况下理解移动、奖励、陷阱、钥匙、商店、事件、战斗和暂停。
- 所有本计划 P1/P2 项关闭或有明确延期理由。
- 每个完成 phase 都有 handoff 文档。

## 当前进度

- [x] 新增可重复截图脚本 `scripts/render_pixel_screens.py`。
- [x] 截图脚本覆盖中英文 7 个核心屏幕。
- [x] 截图输出 `manifest.json`。
- [x] 实际生成并复查 `/tmp/git-dungeon-phase18-screens/contact.png`。
- [x] 修复设置页新增选项按钮截断和底部提示贴边。
- [x] `scale_rect` / `window_to_logical` 改为优先整数倍缩放。
- [x] `PixelSettings` 新增 `text_size`、`high_contrast`、`reduce_motion`。
- [x] 设置页支持切换高对比、文字大小、减少动画。
- [x] `PixelFont` 的文字大小设置会影响实际渲染。
- [x] 标题页和地牢页遵守减少动画设置。
- [x] 标题页、地牢页、设置页使用高对比设置强化边框/强调色。
- [x] 新增 Phase 18 单元测试。
- [x] 写入 `plans/pixel-phase18-final-playtest.md`。
- [x] 回填 `plans/pixel-game-issues.md`、`plans/pixel-phases.md`、`plans/README.md`、`plans/pixel-stardew-level-repair-plan.md`。

## 完成情况

实际交付：

- `scripts/render_pixel_screens.py`
  - 生成 `en/zh_CN` 下 title、dungeon、battle、event、shop、rest、settings 截图。
  - 输出截图 manifest。
- `src/git_dungeon/ui_pixel/layout.py`
  - 常见大窗口优先使用整数倍缩放，避免像素发糊。
- `src/git_dungeon/ui_pixel/settings.py`
  - 新增 `text_size`、`high_contrast`、`reduce_motion`。
  - 保存和加载 TOML 时保留这些设置。
- `src/git_dungeon/ui_pixel/app.py`
  - `PixelFont` 接入文字大小设置。
- `src/git_dungeon/ui_pixel/screens/settings.py`
  - 设置页新增高对比、文字大小、减少动画。
  - 修复新增按钮文字截断。
- `src/git_dungeon/ui_pixel/screens/title.py`
  - 高对比和减少动画实际生效。
- `src/git_dungeon/ui_pixel/screens/dungeon.py`
  - 高对比和减少动画实际生效。
- `src/git_dungeon/ui_pixel/text.py`
  - 增加可访问性设置的中文文案。
- `tests/unit/test_pixel_phase18.py`
  - 覆盖截图脚本、窗口缩放和可访问性设置。
- `plans/pixel-phase18-final-playtest.md`
  - 记录截图包、截图复查结论、P0/P1/P2 关闭与延期清单。

关键决策：

- 视觉回归先落成可重复截图脚本和文件存在/尺寸测试，不在本阶段做像素级 golden 对比。原因是 UI 仍处于快速打磨期，像素级快照会造成大量非行为性维护成本。
- 常见大窗口使用整数倍缩放，1440x900 这类非 16:9 整数尺寸使用 4x 居中留边，而不是 4.5x 拉伸。
- 文字大小只提供 `normal/large`，减少动画先作用在标题和地牢两个有 idle/pulse 的主屏幕。

偏离原计划：

- “完整手动试玩”本阶段落为截图复查 + headless smoke + issue closure 文档，没有通过真实桌面逐键游玩录屏。原因是 Phase 18 的关键目标是把可重复检查固化到项目里；真实桌面试玩可在下一轮 UI polish 继续做。
- 暂停页进入设置、即时窗口模式切换、手柄支持、近期事件日志、首次游玩教学明确延期，见 `plans/pixel-phase18-final-playtest.md`。

## 后续任务

本轮 **Phase 0-18 已完成**。

后续若继续打磨，建议从 `plans/pixel-phase18-final-playtest.md` 的延期项开始：

1. 暂停页进入设置。
2. 窗口/全屏即时切换。
3. 大仓库后台加载。
4. 首次游玩教学。
5. 近期事件日志/章节总结。
6. 手柄基础映射。
7. 若 UI 稳定，再考虑像素级 golden 截图对比。

新会话立刻读取：

1. `AGENTS.md`
2. `plans/README.md`
3. `plans/pixel-phases.md`
4. `plans/pixel-phase18-final-playtest.md`
5. `handoffs/2026-05-08-pixel-phase-18-handoff.md`
6. `scripts/render_pixel_screens.py`
7. `tests/unit/test_pixel_phase18.py`

已知风险：

- 截图脚本能生成复查素材，但不会自动判断“好不好看”；仍需要人工打开 contact sheet。
- 高对比目前只覆盖标题、地牢、设置的关键强调色，不是完整全局主题系统。
- 文字大小设为 large 后会全局增大字体，后续新增紧凑控件时仍要补布局测试。
- `make test` 在当前 shell 仍可能调用系统 Python；本轮使用 `.venv/bin/python` 跑等价检查。

验证结果：

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=src .venv/bin/python scripts/render_pixel_screens.py --out-dir /tmp/git-dungeon-phase18-screens --scale 4
# rendered 14 screenshots to /tmp/git-dungeon-phase18-screens

PYTHONPATH=src .venv/bin/python -m ruff check src/git_dungeon/ui_pixel/settings.py src/git_dungeon/ui_pixel/app.py src/git_dungeon/ui_pixel/layout.py src/git_dungeon/ui_pixel/screens/settings.py src/git_dungeon/ui_pixel/screens/title.py src/git_dungeon/ui_pixel/screens/dungeon.py src/git_dungeon/ui_pixel/text.py scripts/render_pixel_screens.py tests/unit/test_pixel_phase18.py
# All checks passed

PYTHONPATH=src .venv/bin/python -m mypy src/git_dungeon/ui_pixel/settings.py src/git_dungeon/ui_pixel/app.py src/git_dungeon/ui_pixel/layout.py src/git_dungeon/ui_pixel/screens/settings.py src/git_dungeon/ui_pixel/screens/title.py src/git_dungeon/ui_pixel/screens/dungeon.py
# Success: no issues found in 6 source files

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase18.py tests/unit/test_pixel_phase5.py tests/unit/test_pixel_phase17.py -q
# 17 passed

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_assets.py tests/unit/test_pixel_audio.py tests/unit/test_pixel_phase1.py tests/unit/test_pixel_phase2.py tests/unit/test_pixel_phase3.py tests/unit/test_pixel_phase4.py tests/unit/test_pixel_phase5.py tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/unit/test_pixel_phase10.py tests/unit/test_pixel_phase11.py tests/unit/test_pixel_phase12.py tests/unit/test_pixel_phase13.py tests/unit/test_pixel_phase14a.py tests/unit/test_pixel_phase14b.py tests/unit/test_pixel_phase14c.py tests/unit/test_pixel_phase15.py tests/unit/test_pixel_phase16.py tests/unit/test_pixel_phase17.py tests/unit/test_pixel_phase18.py tests/unit/test_pixel_settings.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
# 91 passed

SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-phase18-smoke PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --lang zh_CN --pixel-smoke-frames 8
# passed

PYTHONPATH=src .venv/bin/python scripts/verify_pixel_assets.py --asset-cards assets/generated/phase17/asset_plan.json
# OK: generated pixel assets verified

PYTHONPATH=src .venv/bin/python scripts/verify_assets.py --strict
# OK: 57/57 sprites mapped, all valid

PYTHONPATH=src .venv/bin/python scripts/verify_audio.py
# OK

PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
# 434 passed, 2 skipped, 153 deselected, 2 warnings
```

截图复查：

- `/tmp/git-dungeon-phase18-screens/contact.png`
- `/tmp/git-dungeon-phase18-screens/manifest.json`
