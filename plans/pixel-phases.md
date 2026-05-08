# Pixel 化改造 Phase 拆解

> **源 plan**：`/Users/hughlin/MyNotes/HughLin/Notes/plans/git-dungeon/pixel-game-plan.md`（审阅修订版）
> **状态**：Phase 0-16 已完成最小闭环、首批体验修复、统一 UI/玩家语言层、gpt-image-2 地牢/战斗/非战斗素材流水线、tile 场景重做、战斗表现补强和非战斗地点重做（截至 2026-05-08）；后续按 `plans/pixel-stardew-level-repair-plan.md` 进入 Phase 17 主题统一
> **作用**：Phase 0-18 的范围/交付/验收索引；每个 phase 完成后回填 handoff 链接。
>
> 阅读路径：`AGENTS.md`（或 `CLAUDE.md`）→ 本文件 → `handoffs/` 下最新一份。

## 0. 总览

像素化分两段：

- **Phase 0-6**：Pixel 版完整一局（保留现有章节/节点/战斗，外层换 Pygame-CE 像素界面）。源 plan 称为 "Phase 1"。
- **Phase 7-12**：真正的像素地牢化与交互打磨（房间地图、逐格移动、陷阱、事件级回放测试、陷阱消耗、支线奖励房间、旧地图清理、钥匙门）。源 plan 称为 "Phase 2"，已拆成独立递进计划。

工期估算：8-12 个工作日（源 plan §10）。

## 1. Phase 表

| Phase | 主题 | 对应源 plan | 状态 | Handoff |
|---|---|---|---|---|
| Phase 0 | 基线 & 资源准备 | Day 0 | ✅ 完成 (2026-05-04) | [2026-05-04](../handoffs/2026-05-04-pixel-phase-0-handoff.md) |
| Phase 1 | GameRunner & `--pixel` 入口 | Day 1-2 | ✅ 完成 (2026-05-04) | [2026-05-04](../handoffs/2026-05-04-pixel-phase-1-handoff.md) |
| Phase 2 | 非战斗屏幕（Map/Rest/Event/Shop） | Day 3 | ✅ 完成 (2026-05-04) | [2026-05-04](../handoffs/2026-05-04-pixel-phase-2-handoff.md) |
| Phase 3 | 战斗 & Boss | Day 4-5 | ✅ 完成 (2026-05-04) | [2026-05-04](../handoffs/2026-05-04-pixel-phase-3-handoff.md) |
| Phase 4 | 美术 & 音频接入 | Day 6 | ✅ 完成 (2026-05-04) | [2026-05-04](../handoffs/2026-05-04-pixel-phase-4-handoff.md) |
| Phase 5 | 设置 & 中文 & 布局 | Day 7 | ✅ 完成 (2026-05-04) | [2026-05-04](../handoffs/2026-05-04-pixel-phase-5-handoff.md) |
| Phase 6 | 自动化测试 & 打磨 & 打包 | Day 8-10 | ✅ 完成 (2026-05-05) | [2026-05-05](../handoffs/2026-05-05-pixel-phase-6-handoff.md) |
| Phase 7 | 真正的像素地牢化 | 源 plan §15 | ✅ 完成最小闭环 (2026-05-05) | [2026-05-05](../handoffs/2026-05-05-pixel-phase-7-handoff.md) |
| Phase 8 | 地牢交互打磨 & 回放测试 | Phase 7 后续 | ✅ 完成 (2026-05-06) | [2026-05-06](../handoffs/2026-05-06-pixel-phase-8-handoff.md) |
| Phase 9 | 地牢陷阱消耗 | Phase 8 后续 | ✅ 完成 (2026-05-06) | [2026-05-06](../handoffs/2026-05-06-pixel-phase-9-handoff.md) |
| Phase 10 | 支线奖励房间 | Phase 9 后续 | ✅ 完成 (2026-05-06) | [2026-05-06](../handoffs/2026-05-06-pixel-phase-10-handoff.md) |
| Phase 11 | 旧地图清理 | Phase 10 后续 | ✅ 完成 (2026-05-06) | [2026-05-06](../handoffs/2026-05-06-pixel-phase-11-handoff.md) |
| Phase 12 | 钥匙门支线 | Phase 11 后续 | ✅ 完成 (2026-05-06) | [2026-05-06](../handoffs/2026-05-06-pixel-phase-12-handoff.md) |
| Phase 13 | 可读性和安全交互 | `pixel-game-issues.md` P0/P1 首批 | ✅ 完成 (2026-05-07) | [2026-05-07](../handoffs/2026-05-07-pixel-phase-13-handoff.md) |
| Phase 13R | Phase 13 review finding 补丁 | `pixel-stardew-level-repair-plan.md` | ✅ 完成 (2026-05-07) | [2026-05-07](../handoffs/2026-05-07-pixel-phase-13r-handoff.md) |
| Phase 14A | 统一 UI kit 和玩家语言层 | `pixel-stardew-level-repair-plan.md` | ✅ 完成 (2026-05-07) | [2026-05-07](../handoffs/2026-05-07-pixel-phase-14a-handoff.md) |
| Phase 14B | gpt-image-2 地牢素材流水线 | `pixel-stardew-level-repair-plan.md` | ✅ 完成 (2026-05-08) | [2026-05-08](../handoffs/2026-05-08-pixel-phase-14b-handoff.md) |
| Phase 14C | 地牢 tile 场景重做 | `pixel-stardew-level-repair-plan.md` | ✅ 完成 (2026-05-08) | [2026-05-08](../handoffs/2026-05-08-pixel-phase-14c-handoff.md) |
| Phase 15 | 战斗表现补强 | `pixel-game-issues.md` 战斗体验 | ✅ 完成 (2026-05-08) | [2026-05-08](../handoffs/2026-05-08-pixel-phase-15-handoff.md) |
| Phase 16 | 非战斗场景和玩家文案 | `pixel-game-issues.md` 商店/事件/休息/标题流程 | ✅ 完成 (2026-05-08) | [2026-05-08](../handoffs/2026-05-08-pixel-phase-16-handoff.md) |
| Phase 17 | 美术、动画和音乐方向统一 | `pixel-game-issues.md` 美术/音频/主题 | 未开始 | 待回填 |
| Phase 18 | 视觉回归保护 | `pixel-game-issues.md` 测试/可访问性/输入 | 未开始 | 待回填 |

---

## Phase 0 — 基线 & 资源准备

**范围**：建立环境基线，收齐 CC0 素材，确定字体与音乐授权。素材未齐**不开始**写 Screen。

**交付**：
- Kenney Tiny Dungeon / UI Pack / RPG Audio / UI Audio 入库
- `assets/manifest_sprites.json` + `assets/contact_sheet.png`（人工核对每个 ID 对应正确图像）
- 4 首 CC0 BGM：`title.ogg` / `chapter.ogg` / `boss.ogg` / `gameover.ogg`，作者/链接/license 写入 `assets/CREDITS.md`
- 字体：m5x7（英，CC0）+ Ark Pixel 或 Fusion Pixel（中，OFL）
- `scripts/verify_assets.py`、`scripts/verify_audio.py`

**验收命令**：
```bash
python scripts/verify_assets.py
python scripts/verify_audio.py
PYTHONPATH=src python3 -m git_dungeon . --seed 42 --auto --compact --print-metrics
make test && make test-func && make test-golden
```

**关键约束**：
- manifest 不允许含猜测文件名（源 plan §7.1 反例：`tile_0084.png`）
- **禁止**把 Zpix 当 OFL（实际是个人/教育免费）
- BGM 必须逐首确认 CC0；CC-BY/CC-BY-SA/GPL/非商用一律不收

**MiMo 参与**：不参与（授权判定需人工）。

---

## Phase 1 — GameRunner & `--pixel` 入口

**范围**：把 CLI 中散落的一局推进流程抽到无 print/input 的 `GameRunner`，建立 Pygame-CE 入口骨架。**这是整个项目最关键的一步**（源 plan §1 已点名 GameRunner 抽离比想象的难）。

**交付**：
- `pyproject.toml` 增 `[pixel]` optional dep
- `main.py` 接 `--pixel` 分支（不带仍走原 CLI）
- `src/git_dungeon/ui_pixel/{app,game_runner,assets,audio,fonts,widgets}.py` 骨架
- `screens/{base,title}.py` + 加载页（不让窗口假死）
- `window_to_logical(pos, window_size, logical_size)` 坐标转换函数（**禁止 `// 4` 硬编码**，源 plan §4）
- `GameRunner` 接口至少包含源 plan §5 列出的 12 个方法

**验收命令**：
```bash
pip install -e ".[pixel,dev]"
PYTHONPATH=src python3 -m git_dungeon . --pixel --seed 42
PYTHONPATH=src python3 -m git_dungeon . --seed 42 --auto --compact --print-metrics  # CLI 路径行为不变
```

**关键约束**：
- Screen 只能调用 `GameRunner`，**不允许**直接 import `engine.*` / `rules.*` / `main_cli.*` 私有流程（源 plan §5）
- 如果 CLI 抽离卡住：把共享流程**下沉到 engine 共享层**，让 CLI 保持原输出，**禁止**让 Screen 反向调 main_cli 私有方法
- 触发 CLAUDE.md 第 3 条（正交性）：依赖单向 Screen → GameRunner → engine

**MiMo 参与**：不参与（核心抽离）。

---

## Phase 2 — 非战斗屏幕（Map / Rest / Event / Shop）

**范围**：四个非战斗屏幕，全部走 `GameRunner` 接口。

**交付**：
- `screens/{map,rest,event,shop}.py`
- 节点图标用 sprite，**禁止 emoji**（不同系统字体回退不稳定，破坏像素风）
- EventScreen / ShopScreen：买不起或 MP 不够时按钮**灰显或明确提示**，禁止静默无效（CLAUDE.md 第 5 条：禁止掩盖性 fallback）
- RestScreen：选项文案与实际效果一致，选择后展示真实变化

**验收**：固定 seed 跑到这四类节点，各自的状态变化与 CLI `--auto` 完全一致。

**MiMo 参与**：
- 可：`RestScreen`、widgets（Button/HPBar/TextBox/FloatingText）
- 不可：MapScreen 节点推进逻辑

---

## Phase 3 — 战斗 & Boss

**范围**：BattleScreen 接入普通战斗与 Boss，加视觉/音效反馈。

**交付**：
- 普通战斗：Attack / Defend / Skill / Escape
- Boss 战：Attack / Defend / Skill；Escape **灰显或不显示**
- 视觉：伤害飞字、暴击红字 + 抖动、玩家闪红、盾牌闪、敌人淡出、奖励飞字
- 音效：命中 / 暴击 / 防御 / 受伤 / 击杀 / 升级
- MP 不够时按钮灰显或明确提示（同 Phase 2 反 fallback 规则）

**验收**：固定 seed 下普通战斗与 Boss 战均能结束 → 转 GameOverScreen；胜负与 CLI 一致。

**关键约束**：
- 不做 Item action（源 plan §6.3 修正：Item 进 Phase 1 必须同步做物品系统，本次不做）
- Boss 战 Escape 不可用，与现有 boss_rules.py 的逻辑保持一致

**MiMo 参与**：不参与（战斗核心交互）。

---

## Phase 4 — 美术 & 音频接入

**范围**：把 Phase 0 收齐的素材正式接到所有屏幕。

**交付**：
- 全量 sprite 走 `assets/manifest_sprites.json`（禁止屏幕内硬编码路径）
- gpt-image-2 title banner / 玩家 / 6 个 Boss 建立 prompt 与 asset card；只有完成生成、后处理、contact sheet 核对并写入 manifest 后，才允许接入运行时：
  ```yaml
  id: boss_fix
  source: gpt-image-2
  prompt_file: assets/source_prompts/boss_fix.md
  generated_at: <date>
  postprocess: [remove background, crop, nearest downscale to 32x32, palette cleanup]
  license_note: generated project asset, keep source prompt and output
  ```
- BGM 切换（title / chapter / boss / gameover）
- SFX 库接入（UI / 战斗 / 经济 / 进度）
- 音频设备不可用时**降级为静音**，日志/设置页显式提示静音状态（合法 fallback：已知场景、可声明、不改变语义）

**验收**：所有屏幕无缺图崩溃；`SDL_AUDIODRIVER=dummy` 仍能启动；AI 图未生成时必须明确标记 pending，禁止写入 sprite manifest。

**MiMo 参与**：可参与 `audio.py` 壳子与静音降级。

---

## Phase 5 — 设置 & 中文 & 布局

**范围**：设置页持久化、`--lang zh_CN` 全流程、文字换行。

**交付**：
- `SettingsScreen`：BGM 音量 / SFX 音量 / 语言 / 窗口模式
- `settings.toml` 写入 `GIT_DUNGEON_SAVE_DIR`（**禁止硬编码绝对路径**，源 plan §4）
- 配置不存在 → 创建默认；配置损坏 → **显示错误并用默认值启动**（CLAUDE.md 第 5 条：错误必须可见，禁止静默吞）
- 写入失败 → 明确提示
- 中文模式：所有按钮/事件描述不溢出；自动换行；小字号看不清的位置允许更大文本框

**验收命令**：
```bash
PYTHONPATH=src python3 -m git_dungeon . --pixel --seed 42 --lang zh_CN
# 重启后 settings 保留
```

**实际收口说明**：窗口模式保存后下次启动生效；动态长文本以宽度裁切保证不溢出，完整 TextBox/wrap 打磨进入 Phase 6。

**MiMo 参与**：可参与 `settings.py`。

---

## Phase 6 — 自动化测试 & 打磨 & 打包

**范围**：补齐自动化、CLI/Pixel parity、资源打包、错误页。

**交付**：
- `tests/integration/test_pixel_smoke.py`（headless）
- `tests/integration/test_pixel_cli_parity.py`：对比字段
  - `run_victory`、`chapters_completed`、`battles_total`、`boss_battles_total`、`battles_won`
  - `total_exp_gained`、`total_gold_gained`、`node_type_counts`
  - 允许 UI 动画 / BGM / SFX 不一致
- `tests/unit/test_pixel_{assets,audio,settings}.py`
- `scripts/compare_run_metrics.py`
- 资源定位顺序（**禁止硬编码项目根目录**）：
  1. 环境变量 `GIT_DUNGEON_ASSET_DIR`
  2. 安装包内资源目录
  3. 开发模式仓库根 `assets/`
  4. PyInstaller `_MEIPASS`
- wheel + PyInstaller 都做 smoke
- 缺资源时显示**明确错误页并退出**，禁止用空白图假装正常（CLAUDE.md 第 5 条）

**验收命令**：
```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
  PYTHONPATH=src python3 -m pytest tests/integration/test_pixel_smoke.py

PYTHONPATH=src python3 -m git_dungeon . --seed 42 --auto --metrics-out /tmp/cli.json
PYTHONPATH=src python3 -m git_dungeon . --pixel --auto --headless --seed 42 --metrics-out /tmp/pixel.json
python scripts/compare_run_metrics.py /tmp/cli.json /tmp/pixel.json

make test && make test-func && make test-golden
```

**最终验收**：源 plan §14「最终验收清单」全勾。

**MiMo 参与**：可参与单元测试编写。

---

## Phase 7 — 真正的像素地牢化

最小闭环详见 `plans/dungeon-rooms-plan.md`：当前 route node 映射为房间，玩家用方向键/WASD 逐格移动，到当前房间后进入原战斗/事件/休息/商店流程；陷阱本阶段只阻挡移动，不改变核心结算。

---

## Phase 8 — 地牢交互打磨 & 回放测试

**范围**：收紧 Phase 7 的交互可靠性，补齐事件级自动测试，先验证“走到当前房间并进入节点”这个真实操作闭环。

**交付**：
- `tests/unit/test_pixel_phase8.py`：模拟键盘输入，覆盖不能原地进入、移动到当前房间、Enter 进入节点。
- 测试陷阱优先提示，确保走向陷阱时不会被普通“无门”提示掩盖。
- 测试节点完成后的玩家位置复用，避免每次回到 DungeonScreen 都跳回起点。
- 保持陷阱仍为阻挡，不改 HP/Gold/EXP，继续保护 CLI/Pixel parity。

**验收命令**：
```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase8.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
```

**关键约束**：
- Phase 8 只打磨房间交互，不引入新结算规则。
- 陷阱扣血、钥匙门、分支奖励房间进入后续玩法 phase。
- UI 回放测试必须走 Screen 输入事件，不只调用底层数据函数。

**MiMo 参与**：可参与测试夹具与文档，不碰 engine / CLI parity。

---

## Phase 9 — 地牢陷阱消耗

**范围**：把陷阱从“只挡路”升级为“第一次触发会造成固定、可见、可测试的 HP 消耗”，同时保持主线节点和 CLI 自动结果不变。

**交付**：
- `DungeonTrap.damage` 明确固定伤害值。
- `GameRunner` 记录每章已触发陷阱，并提供一次性触发接口。
- DungeonScreen 触发陷阱后显示真实 HP 损失，再次触发同一陷阱不重复扣血。
- 陷阱可以把玩家 HP 降到 0，并直接进入现有 Game Over 屏。
- `tests/unit/test_pixel_phase9.py` 覆盖一次性扣血和低血量边界。

**验收命令**：
```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
```

**关键约束**：
- 陷阱是玩家主动撞上的支线消耗，不改自动模式主线路径。
- 不新增随机陷阱伤害；伤害值写在地牢数据模型里，便于测试和调参。
- 不在地牢层新增 Game Over；死亡仍由现有战斗/结算流程处理。

**MiMo 参与**：可参与测试，不碰 CLI 自动流程。

---

## Phase 10 — 支线奖励房间

**范围**：在不改变 route 主线和 CLI 自动结果的前提下，给地牢增加一个可选支线奖励房间。玩家可以离开主线领取一次补给，再回到主线继续进入当前节点。

**交付**：
- `DungeonRewardRoom`：固定支线补给房间，包含位置、锚点、治疗量和金币。
- `DungeonFloor.reward_rooms`：奖励房间不混入 route room，但参与门、移动、陷阱避让。
- `GameRunner` 记录每章已领取奖励，并提供一次性领取接口。
- DungeonScreen 支持走进补给房间、Enter 领取、重复领取提示、返回主线。
- `tests/unit/test_pixel_phase10.py` 覆盖奖励房间生成、领取一次、重复不再给、回主线。

**验收命令**：
```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase10.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/unit/test_pixel_phase10.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
```

**关键约束**：
- 奖励房间是手动支线，不进入 CLI 自动主线路径。
- 奖励只能领取一次，不能反复刷 HP/Gold。
- 不生成随机大地图；只做一个固定、可验证的小分支。

**MiMo 参与**：可参与测试，不碰 CLI 自动流程。

---

## Phase 11 — 旧地图清理

**范围**：删除 Phase 2 遗留的静态 `MapScreen`，让 Pixel 正式入口只保留房间地牢屏，降低后续维护面。不要引入钥匙门或新资源规则。

**交付**：
- 删除 `src/git_dungeon/ui_pixel/screens/map.py`。
- 清理只服务旧路线图的中文文案和注释。
- `tests/unit/test_pixel_phase11.py` 覆盖旧模块不存在、加载后仍进入 DungeonScreen。
- 更新 `plans/dungeon-rooms-plan.md` 和 Phase handoff。

**验收命令**：
```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase11.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/unit/test_pixel_phase10.py tests/unit/test_pixel_phase11.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
```

**关键约束**：
- 旧 MapScreen 删除后，战斗/事件/休息/商店结束仍必须回 DungeonScreen。
- 不改变 CLI 自动模式结果。
- 不把旧屏幕改成隐藏 fallback；正式路径只保留一个地牢入口。

**MiMo 参与**：可参与测试和文档，不碰 GameRunner 节点推进规则。

---

## Phase 12 — 钥匙门支线

**范围**：在现有房间地牢里增加一个钥匙房和一个锁住的宝库。玩家必须先进入钥匙房领取钥匙，才能打开宝库领取一次奖励；不改变 route 主线和 CLI 自动结果。

**交付**：
- `DungeonRewardRoom` 支持 `grants_key` 和 `requires_key`。
- `GameRunner` 按章节记录已领取钥匙，奖励领取接口可一次性发钥匙。
- DungeonScreen 阻止未拿钥匙时进入锁住房间，并显示明确提示。
- DungeonScreen 支持钥匙领取、宝库领取、重复领取提示。
- `tests/unit/test_pixel_phase12.py` 覆盖钥匙房、锁住房间、未拿钥匙阻挡、领取后进入、宝库奖励只领一次。

**验收命令**：
```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase12.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase7.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase9.py tests/unit/test_pixel_phase10.py tests/unit/test_pixel_phase11.py tests/unit/test_pixel_phase12.py tests/integration/test_pixel_smoke.py tests/integration/test_pixel_cli_parity.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
```

**关键约束**：
- 钥匙、宝库奖励都按章节隔离，不能跨章误用。
- 未拿钥匙不能进入宝库，不能用静默失败或“假进入”掩盖。
- 不生成随机大地图；仍使用固定、可验证的小分支。
- CLI 自动模式不走支线，结果对齐必须保持。

**MiMo 参与**：可参与测试和文档，不碰 CLI 自动流程。

---

## Phase 13 — 可读性和安全交互

详见 `plans/pixel-game-fix-plan.md`。本阶段先修真实试玩暴露的第一批高优先级问题：窗口尺寸、中文玩家文案、普通界面隐藏音频调试标签、地牢动作提示、房间状态表达、鼠标点击地图、运行中暂停确认、设置页隐藏路径。

**验收命令**：
```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase13.py -q
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase5.py tests/unit/test_pixel_phase8.py tests/unit/test_pixel_phase10.py tests/unit/test_pixel_phase12.py tests/unit/test_pixel_phase13.py -q
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy GIT_DUNGEON_SAVE_DIR=/tmp/git-dungeon-phase13-smoke PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --lang zh_CN --pixel-smoke-frames 8
```

**关键约束**：
- 不改变 CLI 自动路径和主线结算。
- 地牢视觉修正只改 Pixel 层表现和输入，不引入随机地图。
- `Esc/Q` 不能直接退出运行，必须出现暂停确认。
- 中文模式不再在普通玩家界面显示英文属性名或音频槽位。

**MiMo 参与**：可参与截图检查和文案清单，不碰 GameRunner / engine / CLI 自动流程。

---

## Phase 13R — Phase 13 review finding 补丁

详见 `plans/pixel-stardew-level-repair-plan.md`。本阶段先修暂停语义、战斗胜利中文奖励文案、事件/休息/商店 `Q` 暂停、事件页内部 ID 暴露，以及计划索引一致性。

**状态**：已完成，交接文档见 `handoffs/2026-05-07-pixel-phase-13r-handoff.md`。

**关键约束**：
- 本阶段只修 review finding，不重做 UI 大结构。
- “退出本局”和“关闭游戏”不能混用。
- 中文玩家界面不得出现 `EXP/Gold/HP` 等混杂字段。

---

## Phase 14 — 统一 UI、gpt-image-2 素材流水线与 tile 房间表现

详见 `plans/pixel-stardew-level-repair-plan.md`。Phase 14 不再只做 tile 表现，而是拆成 14A/14B/14C：先统一 UI kit 和玩家语言层，再生成并验证地牢基础素材，最后把地牢从节点图重做成 tile 场景。

**状态**：Phase 14A、Phase 14B 和 Phase 14C 已完成，交接文档见 `handoffs/2026-05-07-pixel-phase-14a-handoff.md`、`handoffs/2026-05-08-pixel-phase-14b-handoff.md` 与 `handoffs/2026-05-08-pixel-phase-14c-handoff.md`。

**关键约束**：
- 未通过 asset card、contact sheet 和 manifest 校验的 AI 图不得接入运行时。
- 所有玩家可见文案必须走统一 formatter，禁止 screen 自己拼内部字段。
- tile 表现不得改变 CLI 自动路径和主线结算。

---

## Phase 15 — 战斗表现补强

详见 `plans/pixel-stardew-level-repair-plan.md`。本阶段补齐战斗 sprite sheet，把普通战和首领战改成有角色、敌人、Boss 身份、动作反馈和掉落反馈的战斗场景。

**状态**：已完成，交接文档见 `handoffs/2026-05-08-pixel-phase-15-handoff.md`。

**关键约束**：
- 战斗表现不得改变战斗结算、CLI 自动路径或 Pixel/CLI parity。
- 新战斗素材必须通过 prompt、raw、processed、contact sheet、asset card 和 manifest 校验。
- 中文模式不得显示 `Battle started`、`phase_1` 等内部字段。

---

## Phase 16 — 非战斗场景和玩家文案

详见 `plans/pixel-stardew-level-repair-plan.md`。本阶段把事件、商店、休息从数据面板改成有地点感的场景，并补齐非战斗地点素材。

**状态**：已完成，交接文档见 `handoffs/2026-05-08-pixel-phase-16-handoff.md`。下一步进入 Phase 17。

**关键约束**：
- 事件、商店、休息页面不得暴露 `event_id`、`choice_id`、opcode 或英文原始商品标题。
- 非战斗页面要使用地点素材，而不是继续只画节点图标和数据卡片。
- 不改变事件、商店、休息的结算规则。

---

## 跨 Phase 强制约束（每个 phase 都要满足）

引自 CLAUDE.md「Project Principles」与源 plan：

1. **CLI 路径不破坏**：所有 phase 验收都必须包含「同 seed 下 CLI `--auto` 行为不变」检查。
2. **确定性**：禁止全局 `random` / `time.time()`；走 `engine.rng.DefaultRNG(seed=…)`。
3. **禁止掩盖性 fallback**：缺资源、配置损坏、音频设备缺失等必须显式可见。
4. **Phase 完成 → 写 handoff、提交并推送**：路径 `handoffs/<YYYY-MM-DD>-<phase-id>-handoff.md`，5 节必填（见 `handoffs/README.md`）。回填本文件「Phase 表」对应行的 Handoff 列，并按 AGENTS.md 第 7 条提交、推送到 GitHub。
5. **MiMo 边界**：MiMo 不碰 GameRunner、engine、CLI 入口、奖励/章节/Boss 流程；超过 3 个无关模块的改动一律不让 MiMo 做。

---

## 变更记录

| 日期 | 变更 | 原因 |
|---|---|---|
| 2026-05-03 | 初始创建，从源 plan 拆出 Phase 0-7 | 与 CLAUDE.md 第 6 条对齐，建立 phase → handoff 索引 |
| 2026-05-04 | Phase 0 收口，回填 handoff 链接 | Phase 0 验收命令全绿，详见 handoff |
| 2026-05-04 | Phase 1 收口，回填 handoff 链接 | Pixel 入口、GameRunner 最小闭环、headless smoke 与 CLI 回归验证完成 |
| 2026-05-04 | Phase 2 收口，回填 handoff 链接 | Map/Rest/Event/Shop 屏幕完成，非战斗规则与 CLI 共享，回归验证完成 |
| 2026-05-04 | Phase 3 收口，回填 handoff 链接 | Battle/Elite/Boss 战斗屏完成，Boss 禁逃和 MP 禁用状态验证完成 |
| 2026-05-04 | Phase 4 收口，回填 handoff 链接 | BGM/SFX、音频状态、战斗反馈接入；gpt-image-2 建 prompt/card 并明确 pending |
| 2026-05-04 | Phase 5 收口，回填 handoff 链接 | 设置页、settings.toml、中文字体/文案、布局防溢出和错误可见状态完成 |
| 2026-05-05 | Phase 6 收口，回填 handoff 链接 | Pixel smoke、CLI/Pixel parity、wheel/PyInstaller smoke、资源定位和错误页完成 |
| 2026-05-05 | Phase 7 收口，回填 handoff 链接 | 房间地牢屏、逐格移动、门、陷阱阻挡、节点进入闭环完成 |
| 2026-05-06 | Phase 8 收口，回填 handoff 链接 | 地牢键盘移动、陷阱阻挡、节点进入和位置保持的事件级回放测试完成 |
| 2026-05-06 | Phase 9 收口，回填 handoff 链接 | 陷阱一次性 HP 消耗、已触发状态和陷阱致死边界完成 |
| 2026-05-06 | Phase 10 收口，回填 handoff 链接 | 支线奖励房间、一次性领取和回主线闭环完成 |
| 2026-05-06 | Phase 11 收口，回填 handoff 链接 | 旧 MapScreen 删除，Pixel 正式入口只保留 DungeonScreen |
| 2026-05-06 | Phase 12 收口，回填 handoff 链接 | 钥匙房、锁住宝库、一次性钥匙和宝库奖励闭环完成 |
| 2026-05-07 | 新增 Phase 13-18 修复路线，Phase 13 开始 | 根据真实试玩问题清单拆出后续修复计划 |
| 2026-05-07 | Phase 13 收口，回填 handoff 链接 | 窗口、文案、地牢提示、暂停确认、音频标签隐藏和鼠标移动完成 |
| 2026-05-07 | 新增 Stardew-Level 修复计划并调整 Phase 14 入口 | 用户要求统一 UI、gpt-image-2 标准像素素材和成熟像素 RPG 级验收 |
| 2026-05-07 | Phase 13R 收口，回填 handoff 链接 | 修复 Phase 13 review findings，下一步进入 Phase 14A 统一 UI |
| 2026-05-07 | Phase 14A 收口，回填 handoff 链接 | 统一 UI kit、玩家语言 formatter、运行页 action bar 和可读性回归 |
| 2026-05-08 | Phase 14B 收口，回填 handoff 链接 | Codex GPT Image 2 地牢素材、后处理、contact sheet、manifest 和校验脚本完成 |
| 2026-05-08 | Phase 14C 收口，回填 handoff 链接 | 地牢界面接入 tile、门、走廊、陷阱、宝箱、钥匙、宝库和截图验证 |
| 2026-05-08 | Phase 15 收口，回填 handoff 链接 | Codex GPT Image 2 战斗素材、普通战/首领战场景、动作反馈和中文字段清理完成 |
| 2026-05-08 | Phase 16 收口，回填 handoff 链接 | 非战斗地点素材、事件/商店/休息场景、商品标题和风险标签清理完成 |
