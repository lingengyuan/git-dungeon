# Pixel Phase 25 Handoff

## 背景

Phase 24 已完成内容体验打磨。Phase 25 是 PC-only 打磨线的收口，不再继续加功能，重点是把当前状态固定成可交接、可验证、可试玩的 PC 版本。

上游约束：

- 用户明确不考虑手柄支持。
- 用户明确不考虑移动端，只支持 PC。
- 每个 phase 完成后必须验证、写 handoff、提交并推送。
- 文档状态必须和仓库现实一致，不能继续写 Phase 18 后延期项。

## 目标

原计划交付：

- PC-only 发布前检查清单。
- 更新 AGENTS、plans 索引和延期项状态。
- 明确手柄/移动端移出范围。
- 加文档状态测试，防止后续计划状态过期。
- 跑完整 pixel 回归、资源检查、音频检查、截图生成和 smoke。

## 当前进度

- [x] 新增 `plans/pixel-pc-release-checklist.md`。
- [x] `AGENTS.md` 当前活跃 plan 更新为 Phase 0-25 已完成。
- [x] `plans/pixel-phases.md` 标记 Phase 25 完成。
- [x] `plans/README.md` 标记 pixel phase 索引和 PC release checklist 已完成。
- [x] `plans/pixel-phase18-final-playtest.md` 更新手柄、首次教学等剩余状态。
- [x] `plans/pixel-game-issues.md` 标注 PX-036 移出范围、PX-040 已关闭。
- [x] 新增 Phase 25 文档状态测试。

## 完成情况

实际交付：

- `plans/pixel-pc-release-checklist.md`
  - 写明 PC-only 范围、试玩入口、发布前检查命令、人工截图复查项和已知限制。
- `AGENTS.md`
  - 新会话入口指向 PC release checklist。
  - 明确当前不做手柄、不做移动端。
- `tests/unit/test_pixel_phase25.py`
  - 验证 Phase 0-25 完成状态、PC-only 范围和下一会话入口。

关键决策：

- Phase 25 不新增运行时代码。原因是本 phase 是发布前固定，继续加功能会扩大风险。
- 手柄不是延期项，而是明确移出范围。原因是用户已经指定当前只做 PC。

偏离原计划：

- 无。

## 后续任务

当前 Phase 0-25 已完成。

如果后续继续，建议不要直接开 Phase 26 写功能，先做一次真实 PC 手动试玩并记录问题，再决定是否进入：

1. 打包分发。
2. 更多内容池和平衡。
3. 更严格的像素级截图 golden。
4. 独立章节结算页。

新会话立刻读取：

1. `AGENTS.md`
2. `plans/pixel-pc-release-checklist.md`
3. `plans/pixel-phases.md`
4. `handoffs/2026-05-10-pixel-phase-25-handoff.md`

已知风险：

- 当前仍是源码本地试玩，不是完整安装包。
- 加载进度是阶段提示，不是百分比。
- 日志和章节总结是地牢页内摘要，不是独立结算页。

验证结果：

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase25.py -q
# 3 passed

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_*.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
# 108 passed

PYTHONPATH=src .venv/bin/python scripts/verify_assets.py --strict
# OK: 57/57 sprites mapped, all valid

PYTHONPATH=src .venv/bin/python scripts/verify_audio.py
# OK

SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=src .venv/bin/python scripts/render_pixel_screens.py --out-dir /tmp/git-dungeon-pixel-pc-release-screens --scale 2
# rendered 20 screenshots to /tmp/git-dungeon-pixel-pc-release-screens

SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-pixel-pc-release-smoke PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --lang zh_CN --pixel-smoke-frames 12
# passed
```
