# Phase 4 Handoff — 美术 & 音频接入

- **Phase**: `pixel-phase-4`
- **收口日期**: 2026-05-04
- **作者会话**: Codex + Hugh Lin
- **所属 plan**: [`plans/pixel-phases.md`](../plans/pixel-phases.md) §Phase 4
- **上一个 handoff**: [`2026-05-04-pixel-phase-3-handoff.md`](2026-05-04-pixel-phase-3-handoff.md)

---

## 1. 背景

Phase 4 要把 Phase 0 收齐的像素素材、BGM、SFX 真正接到 Pixel 模式里，并补上 Phase 3 留下的基础战斗反馈。

**上游约束**：
- 所有运行时 sprite 必须继续通过 `assets/manifest_sprites.json` 读取，屏幕内不能写素材路径。
- BGM/SFX 必须来自已登记、可验证 license 的资源。
- 音频设备不可用可以静音，但必须在界面中明确显示静音状态。
- `gpt-image-2` 图片未生成、未后处理、未写入 manifest 前，不能算作已接入运行时素材。

---

## 2. 目标

来自 `plans/pixel-phases.md` §Phase 4：

| 交付 | 状态 |
|---|---|
| 全量 sprite 走 `assets/manifest_sprites.json` | ✅ |
| `gpt-image-2` title banner / 玩家 / 6 个 Boss asset card | ✅ 清单完成，图片待生成 |
| BGM 切换：title / chapter / boss / gameover | ✅ |
| SFX 库接入：UI / 战斗 / 经济 / 进度 | ✅ |
| 音频设备不可用时静音并显式提示 | ✅ |
| 战斗视觉反馈补齐 | ✅ 基础动效完成 |

**验收命令**（已执行）：

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
  PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --pixel-smoke-frames 8

PYTHONPATH=src .venv/bin/python scripts/verify_assets.py --strict
PYTHONPATH=src .venv/bin/python scripts/verify_audio.py
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase1.py tests/unit/test_pixel_phase2.py tests/unit/test_pixel_phase3.py tests/unit/test_pixel_phase4.py -q
PYTHONPATH=src .venv/bin/python -m ruff check src/git_dungeon/ui_pixel tests/unit/test_pixel_phase4.py
PYTHONPATH=src .venv/bin/python -m mypy src/git_dungeon/ui_pixel tests/unit/test_pixel_phase4.py --ignore-missing-imports
PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
PYTHONPATH=src .venv/bin/python -m pytest tests/functional/ -q
PYTHONPATH=src .venv/bin/python -m pytest tests/golden_test.py -q
PYTHONPATH=src .venv/bin/python -m git_dungeon . --seed 42 --auto --compact --print-metrics
```

**结果**：
- Pixel headless smoke：通过。
- Asset 校验：`13/13` sprite 有效。
- Audio 校验：4 个 BGM 槽位和 2 个 SFX 包有效。
- Pixel Phase 1-4 单测：`12 passed`。
- 快速测试：`355 passed, 2 skipped, 153 deselected`。
- Functional：`133 passed`。
- Golden：`4 passed`。
- Ruff / mypy：通过。
- CLI 自动模式：能完整运行到游戏内失败结局；退出码为失败结局对应的 `1`，不是崩溃。

---

## 3. 当前进度

- [x] **统一音频入口** — 新增 `src/git_dungeon/ui_pixel/audio.py`，管理 BGM、SFX、静音状态。
- [x] **BGM 切换** — Title、Map、Boss Battle、GameOver 分别播放对应 BGM。
- [x] **SFX 接入** — UI 确认/取消/拒绝、战斗命中/暴击/受伤/防御/击杀、商店金币、事件和休息都有音效槽位。
- [x] **音频不可用可见** — Title、Loading、Map、Battle、GameOver 显示 `Audio muted: ...`。
- [x] **战斗反馈** — 伤害飞字、暴击红字、敌人/玩家闪框、防御盾框、胜利奖励飞字、敌人淡出。
- [x] **运行时 sprite 路径约束** — 屏幕继续只用 sprite id，不直接读素材路径。
- [x] **AI 图 asset card** — `assets/generated/asset_cards.yml` 和 8 个 prompt 文件已建。
- [~] **AI 图运行时接入** — 暂不接入；当前没有可验证的 `gpt-image-2` 生成路径，不能伪造产物。
- [x] **测试覆盖** — 新增 `tests/unit/test_pixel_phase4.py`，覆盖音频可用/不可用和 AI 图待生成状态。

---

## 4. 完成情况

### 4.1 实际交付物

| 路径 | 内容 |
|---|---|
| `src/git_dungeon/ui_pixel/audio.py` | Pixel 音频管理，含 BGM/SFX 槽位、加载、播放、静音状态。 |
| `src/git_dungeon/ui_pixel/app.py` | 启动时加载 AudioManager，并传给首屏。 |
| `src/git_dungeon/ui_pixel/screens/*.py` | 屏幕接入 BGM/SFX 和音频状态显示。 |
| `src/git_dungeon/ui_pixel/screens/battle.py` | 补战斗飞字、闪框、暴击、淡出、奖励反馈。 |
| `assets/generated/asset_cards.yml` | `gpt-image-2` 资源卡，状态明确为待生成。 |
| `assets/source_prompts/*.md` | title、玩家、6 个 Boss 的生成 prompt。 |
| `assets/generated/README.md` | AI 生成素材进入 manifest 前的验收规则。 |
| `assets/CREDITS.md` | 登记 AI 生成资源当前状态和接入规则。 |
| `tests/unit/test_pixel_phase4.py` | Phase 4 音频与 asset card 单测。 |

### 4.2 关键决策

#### 1. 音频失败不崩，但状态必须显示

Pygame 在无音频设备或 dummy 环境下可能没有 mixer。这里把它收敛到 `AudioManager.status()`，所有相关屏幕都能显示静音原因。这样符合“可声明 fallback”，不会让玩家误以为音效已经正常播放。

#### 2. SFX 用语义槽位，不在屏幕里绑定文件

屏幕只说 `combat_hit`、`economy`、`ui_denied` 这类动作含义。具体文件集中在 `audio.py`，以后换素材包不需要改每个屏幕。

#### 3. `gpt-image-2` 不生成就不接入

当前环境没有 `OPENAI_API_KEY`，本地 imagegen skill 也没有验证到 `gpt-image-2` 可用路径。因此只建立 prompt 和 asset card，状态写 `pending_generation`。这避免把未生成素材写进 manifest 后造成缺图或虚假完成。

### 4.3 偏离原计划

| 原计划项 | 实际情况 | 原因 |
|---|---|---|
| `gpt-image-2` 处理后的 title banner / 玩家 / 6 个 Boss 接入运行时 | 只完成 prompt + asset card，未写入 manifest | 没有可验证生成路径；未生成图片不能算运行时素材。 |
| 完整奖励飞字后再转场 | 做了短延迟奖励飞字和敌人淡出 | 当前仍是简洁战斗屏，不引入复杂动画队列，避免影响战斗推进。 |

这些偏离不影响 Phase 4 的可运行目标：现有 CC0 美术、BGM、SFX 已经接入，音频不可用时也能启动并明确显示状态。

### 4.4 触发的项目原则

- **第一性原理**：先接入真实存在且 license 清楚的资源，不把未生成图当资产。
- **DRY**：音频路径集中在 `audio.py`，屏幕只发语义事件。
- **正交性**：Screen → AudioManager / GameRunner；音频不混进战斗规则。
- **禁止掩盖性质 fallback**：音频不可用显示原因；AI 图待生成写入 card，不写入 manifest。
- **Phase handoff**：本文件即 Phase 4 交接文档。

---

## 5. 后续任务

### 5.1 Phase 5 入口

下一个 phase：**`pixel-phase-5` — 设置 & 中文 & 布局**。

建议入口顺序：
1. 做 `SettingsScreen` 和 `settings.toml`，先支持 BGM/SFX 音量。
2. 把 `AudioManager` 接入设置值，重启后仍保留。
3. 接 `--lang zh_CN` 到 Pixel 文案层，避免屏幕内硬编码英文。
4. 使用 Ark Pixel 中文字体，检查中文按钮、事件、商店描述是否溢出。

### 5.2 已知风险与未决问题

| 风险 / 未决项 | 影响 | 处理建议 |
|---|---|---|
| `gpt-image-2` 图片未生成 | 运行时仍用 Kenney sprite，缺少定制角色/Boss | 配好 API 后按 `assets/generated/asset_cards.yml` 生成、后处理、做 contact sheet，再写 manifest。 |
| 还没有设置页 | 音量当前固定，不能手动静音或保存偏好 | Phase 5 第一项处理。 |
| 中文文案未统一 | `--lang zh_CN` 下 Pixel UI 仍以英文为主 | Phase 5 建文案表和字体 fallback。 |
| 完整一局 parity 还没做 | Pixel/CLI 的完整指标一致性未自动证明 | Phase 6 做 headless auto 和 metrics 对比。 |

### 5.3 新会话立刻要读哪些文件

1. `AGENTS.md`
2. `plans/pixel-phases.md`
3. `handoffs/2026-05-04-pixel-phase-4-handoff.md`
4. `src/git_dungeon/ui_pixel/audio.py`
5. `src/git_dungeon/ui_pixel/app.py`
6. `src/git_dungeon/ui_pixel/screens/battle.py`
7. `assets/generated/asset_cards.yml`
8. `assets/CREDITS.md`

### 5.4 推荐的第一条验证命令

```bash
cd /Users/hughlin/Projects/git-dungeon && \
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --pixel-smoke-frames 8 && \
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase1.py tests/unit/test_pixel_phase2.py tests/unit/test_pixel_phase3.py tests/unit/test_pixel_phase4.py -q
```

两条都 exit 0，说明 Pixel 启动、路线、非战斗、战斗、素材和音频入口仍完好。
