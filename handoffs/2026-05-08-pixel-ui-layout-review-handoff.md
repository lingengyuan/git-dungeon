# Pixel UI Layout Review Handoff

## 背景

Phase 14A 之后，用户通过截图连续指出多处界面重叠和对齐问题。上一轮已经修正战斗页生命、魔力、敌人块、血条之间的冲突。本轮任务是把这些经验沉淀成文档，并深度复查其他像素界面是否还有同类问题。

## 目标

- 输出像素 UI 布局经验文档。
- 重新审查标题、地牢、战斗、事件、休息、商店、设置、暂停、结算、错误页。
- 修掉发现的同类布局问题。
- 补充回归测试，防止以后再次出现同类问题。

## 当前进度

- [x] 新增 `docs/PIXEL_UI_LAYOUT_LESSONS.md`。
- [x] 生成全屏 contact sheet 做人工复查。
- [x] 修复标题页标题与敌人块重叠。
- [x] 修复商店页底部“跳过”按钮被底栏盖住。
- [x] 为标题页安全间距和商店底栏按钮顺序补测试。
- [x] 重新生成修复后截图。

## 完成情况

实际交付：

- `src/git_dungeon/ui_pixel/screens/title.py`：标题页图块、标题和副标题改为命名常量；标题改用固定宽度绘制，避免碰到右侧敌人块。
- `src/git_dungeon/ui_pixel/screens/shop.py`：商店底栏先绘制，底部“跳过”按钮后绘制，避免按钮被盖住；按钮区域和底栏预留宽度改为常量。
- `tests/unit/test_pixel_phase14a.py`：新增标题页安全间距测试、商店底栏按钮空间和绘制顺序测试。
- `docs/PIXEL_UI_LAYOUT_LESSONS.md`：记录已遇到的问题、根因、规则和检查清单。

偏离原计划：

- 本轮没有重做整体美术风格，也没有生成新素材；范围只限于布局问题和经验沉淀。

## 后续任务

下一轮如果继续 Phase 14B，需要先读：

1. `AGENTS.md`
2. `plans/pixel-stardew-level-repair-plan.md`
3. `docs/PIXEL_UI_LAYOUT_LESSONS.md`
4. `handoffs/2026-05-08-pixel-ui-layout-review-handoff.md`

已知风险：

- 当前截图脚本仍是临时验证脚本，没有沉淀成正式工具。后续 Phase 14B/14C 建议把 contact sheet 生成脚本化。
- 事件、商店、休息页虽然没有明显重叠，但仍是抽象 UI，不是最终的地点化场景。

验证结果：

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase14a.py -q
# 11 passed

.venv/bin/python -m ruff check src/git_dungeon/ui_pixel/screens/title.py src/git_dungeon/ui_pixel/screens/shop.py tests/unit/test_pixel_phase14a.py
# passed

PYTHONPATH=src .venv/bin/python -m mypy src/git_dungeon/ui_pixel --ignore-missing-imports
# passed

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase5.py tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/unit/test_pixel_phase10.py tests/unit/test_pixel_phase11.py tests/unit/test_pixel_phase12.py tests/unit/test_pixel_phase13.py tests/unit/test_pixel_phase14a.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
# 43 passed

SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-ui-layout-review-smoke PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --lang zh_CN --pixel-smoke-frames 8
# passed

PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
# 405 passed, 2 skipped, 153 deselected, 2 warnings
```

截图复查：

- 修复前：`/tmp/git-dungeon-ui-deep-review/contact-2x.png`
- 修复后：`/tmp/git-dungeon-ui-deep-review-fixed/contact-2x.png`
