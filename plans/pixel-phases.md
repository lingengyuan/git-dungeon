# Pixel 化改造 Phase 拆解

> **源 plan**：`/Users/hughlin/MyNotes/HughLin/Notes/plans/git-dungeon/pixel-game-plan.md`（审阅修订版）
> **状态**：进行中（截至 2026-05-04 完成 Phase 0-3，准备进入 Phase 4）
> **作用**：Phase 0-7 的范围/交付/验收索引；每个 phase 完成后回填 handoff 链接。
>
> 阅读路径：`AGENTS.md`（或 `CLAUDE.md`）→ 本文件 → `handoffs/` 下最新一份。

## 0. 总览

像素化分两段：

- **Phase 0-6**：Pixel 版完整一局（保留现有章节/节点/战斗，外层换 Pygame-CE 像素界面）。源 plan 称为 "Phase 1"。
- **Phase 7**：真正的像素地牢化（房间地图、逐格移动、陷阱）。源 plan 称为 "Phase 2"，**不在本次范围**，留独立 plan。

工期估算：8-12 个工作日（源 plan §10）。

## 1. Phase 表

| Phase | 主题 | 对应源 plan | 状态 | Handoff |
|---|---|---|---|---|
| Phase 0 | 基线 & 资源准备 | Day 0 | ✅ 完成 (2026-05-04) | [2026-05-04](../handoffs/2026-05-04-pixel-phase-0-handoff.md) |
| Phase 1 | GameRunner & `--pixel` 入口 | Day 1-2 | ✅ 完成 (2026-05-04) | [2026-05-04](../handoffs/2026-05-04-pixel-phase-1-handoff.md) |
| Phase 2 | 非战斗屏幕（Map/Rest/Event/Shop） | Day 3 | ✅ 完成 (2026-05-04) | [2026-05-04](../handoffs/2026-05-04-pixel-phase-2-handoff.md) |
| Phase 3 | 战斗 & Boss | Day 4-5 | ✅ 完成 (2026-05-04) | [2026-05-04](../handoffs/2026-05-04-pixel-phase-3-handoff.md) |
| Phase 4 | 美术 & 音频接入 | Day 6 | 待开始 | — |
| Phase 5 | 设置 & 中文 & 布局 | Day 7 | 待开始 | — |
| Phase 6 | 自动化测试 & 打磨 & 打包 | Day 8-10 | 待开始 | — |
| Phase 7 | 真正的像素地牢化 | 源 plan §15 | 暂缓 | — |

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
- gpt-image-2 处理后的 title banner / 玩家 / 6 个 Boss 接入；每个素材有 asset card：
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

**验收**：所有屏幕无缺图崩溃；`SDL_AUDIODRIVER=dummy` 仍能启动并跑完一局。

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

## Phase 7 — 真正的像素地牢化（暂缓）

不在本次范围。Phase 6 收口后另开 `plans/dungeon-rooms-plan.md`。最小目标见源 plan §15。

---

## 跨 Phase 强制约束（每个 phase 都要满足）

引自 CLAUDE.md「Project Principles」与源 plan：

1. **CLI 路径不破坏**：所有 phase 验收都必须包含「同 seed 下 CLI `--auto` 行为不变」检查。
2. **确定性**：禁止全局 `random` / `time.time()`；走 `engine.rng.DefaultRNG(seed=…)`。
3. **禁止掩盖性 fallback**：缺资源、配置损坏、音频设备缺失等必须显式可见。
4. **Phase 完成 → 写 handoff**：路径 `handoffs/<YYYY-MM-DD>-<phase-id>-handoff.md`，5 节必填（见 `handoffs/README.md`）。回填本文件「Phase 表」对应行的 Handoff 列。
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
