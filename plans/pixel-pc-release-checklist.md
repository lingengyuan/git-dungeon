# Pixel PC Release Checklist

> 日期：2026-05-10
> 范围：Pixel mode PC-only 试玩固定。
> 状态：Phase 19-25 收口清单。

## 范围

本轮发布只承诺 PC 桌面键鼠体验：

- 支持窗口模式和全屏模式。
- 支持键盘方向键 / WASD、Enter / Space、鼠标点击相邻房间和按钮。
- 支持标题页设置、运行中暂停设置、退出本局回标题页。
- 不支持手柄。
- 不支持移动端、触控布局、小屏响应式适配。

## 玩家入口

推荐本地试玩命令：

```bash
PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --lang zh_CN
```

英文模式：

```bash
PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --lang en
```

## 发布前检查

必须通过：

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_*.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_assets.py --strict
PYTHONPATH=src .venv/bin/python scripts/verify_audio.py
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=src .venv/bin/python scripts/render_pixel_screens.py --out-dir /tmp/git-dungeon-pixel-pc-release-screens --scale 2
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-pixel-pc-release-smoke PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --lang zh_CN --pixel-smoke-frames 12
```

人工截图复查：

- `/tmp/git-dungeon-pixel-pc-release-screens/zh_CN-title.png`
- `/tmp/git-dungeon-pixel-pc-release-screens/zh_CN-loading.png`
- `/tmp/git-dungeon-pixel-pc-release-screens/zh_CN-tutorial.png`
- `/tmp/git-dungeon-pixel-pc-release-screens/zh_CN-dungeon.png`
- `/tmp/git-dungeon-pixel-pc-release-screens/zh_CN-battle.png`
- `/tmp/git-dungeon-pixel-pc-release-screens/zh_CN-event.png`
- `/tmp/git-dungeon-pixel-pc-release-screens/zh_CN-shop.png`
- `/tmp/git-dungeon-pixel-pc-release-screens/zh_CN-rest.png`
- `/tmp/git-dungeon-pixel-pc-release-screens/zh_CN-pause.png`
- `/tmp/git-dungeon-pixel-pc-release-screens/zh_CN-settings.png`

## 完成标准

- 标题页、加载页、教学页、地牢、战斗、事件、商店、休息、暂停、设置都能渲染。
- 中文文本不溢出、不覆盖边框、不暴露 raw id。
- 地牢页能解释移动、当前房间、陷阱、奖励、钥匙、宝库、日志。
- 暂停页能继续、进设置、退出本局回标题。
- 窗口/全屏切换即时生效。
- 加载页不会阻塞主循环，并可取消回标题。

## 已知限制

- 没有真实打包产物；当前仍是源码本地试玩。
- 没有手柄和移动端支持，这是明确范围外。
- 加载进度是阶段提示，不是百分比。
- 章节总结先落在地牢页房间进度和近期日志，不是独立结算页。
