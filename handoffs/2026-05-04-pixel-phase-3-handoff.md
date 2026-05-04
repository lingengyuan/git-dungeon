# Phase 3 Handoff — 战斗 & Boss

- **Phase**: `pixel-phase-3`
- **收口日期**: 2026-05-04
- **作者会话**: Codex + Hugh Lin
- **所属 plan**: [`plans/pixel-phases.md`](../plans/pixel-phases.md) §Phase 3
- **上一个 handoff**: [`2026-05-04-pixel-phase-2-handoff.md`](2026-05-04-pixel-phase-2-handoff.md)

---

## 1. 背景

Phase 3 要让 Pixel 路线能穿过 Battle / Elite / Boss 节点，不再卡在第一场战斗。目标是把战斗状态推进接到 `GameRunner`，让 `BattleScreen` 只负责显示和发动作。

**上游约束**：
- Screen 只能调用 `GameRunner`，不能直接调用 CLI 私有方法。
- 普通战斗必须有 Attack / Defend / Skill / Escape。
- Boss 战必须禁用 Escape。
- MP 不够必须灰显或明确提示。
- Item action 不做。
- 音效按计划属于 Phase 4，本阶段不提前接入音频。

---

## 2. 目标

来自 `plans/pixel-phases.md` §Phase 3：

| 交付 | 状态 |
|---|---|
| 普通战斗：Attack / Defend / Skill / Escape | ✅ |
| Boss 战：Attack / Defend / Skill；Escape 灰显或不显示 | ✅ |
| 视觉：伤害飞字、暴击红字 + 抖动、玩家闪红、盾牌闪、敌人淡出、奖励飞字 | 部分完成 |
| 音效：命中 / 暴击 / 防御 / 受伤 / 击杀 / 升级 | 未做，留 Phase 4 |
| MP 不够时按钮灰显或明确提示 | ✅ |

**验收命令**（已执行）：
```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
  PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --pixel-smoke-frames 8

PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase1.py tests/unit/test_pixel_phase2.py tests/unit/test_pixel_phase3.py -q
PYTHONPATH=src .venv/bin/python -m ruff check src/git_dungeon/engine/combat_actions.py src/git_dungeon/ui_pixel tests/unit/test_pixel_phase1.py tests/unit/test_pixel_phase2.py tests/unit/test_pixel_phase3.py
PYTHONPATH=src .venv/bin/python -m mypy src/git_dungeon/engine/combat_actions.py src/git_dungeon/ui_pixel tests/unit/test_pixel_phase1.py tests/unit/test_pixel_phase2.py tests/unit/test_pixel_phase3.py --ignore-missing-imports

PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
PYTHONPATH=src .venv/bin/python -m pytest tests/functional/ -q
PYTHONPATH=src .venv/bin/python -m pytest tests/golden_test.py -q
```

**结果**：
- Pixel smoke：通过，能真实加载仓库并渲染路线。
- Pixel Phase 1/2/3 单测：`9 passed`。
- 快速测试：`352 passed, 2 skipped, 153 deselected`。
- Functional：`133 passed`。
- Golden：`4 passed`。
- Ruff / mypy：通过。

---

## 3. 当前进度

- [x] **共享战斗 step** — 新增 `src/git_dungeon/engine/combat_actions.py`，统一处理 attack / defend / skill / escape 单回合结果。
- [x] **GameRunner 战斗接口** — 支持 start current battle、resolve battle action、battle snapshot、reward snapshot。
- [x] **普通战斗** — Battle 节点可进入 BattleScreen，胜利后推进路线并发奖励。
- [x] **Elite 战斗** — Elite 节点复用 BattleScreen，敌人 HP/ATK 按 CLI 规则放大并显示 Elite。
- [x] **Boss 战** — Boss 节点复用 BattleScreen，Escape 灰显并被规则拒绝。
- [x] **MP 不够** — Skill 按钮灰显；键盘触发也只提示，不执行敌人回合。
- [x] **GameOverScreen** — 玩家死亡后进入结束页。
- [x] **地图衔接** — MapScreen 现在可打开 battle / elite / boss / event / rest / shop 当前节点。
- [x] **测试覆盖** — `tests/unit/test_pixel_phase3.py` 覆盖普通战斗胜利推进、MP 不够拒绝、Boss 禁逃。
- [~] **视觉反馈** — 已有 HP bar、敌人闪框、战斗结果文本、奖励文本；未做完整动画系统。
- [ ] **音效** — 未做，按计划进入 Phase 4。

---

## 4. 完成情况

### 4.1 实际交付物

| 路径 | 内容 |
|---|---|
| `src/git_dungeon/engine/combat_actions.py` | 单回合战斗共享规则，含攻击、防御、技能、逃跑、Boss 禁逃、MP 检查。 |
| `src/git_dungeon/ui_pixel/game_runner.py` | 战斗开始、动作推进、胜利奖励、Boss/Elite 状态快照。 |
| `src/git_dungeon/ui_pixel/screens/battle.py` | 普通 / Elite / Boss 共用战斗屏。 |
| `src/git_dungeon/ui_pixel/screens/game_over.py` | 玩家失败后的结束页。 |
| `src/git_dungeon/ui_pixel/screens/map.py` | 当前 combat 节点可进入 BattleScreen。 |
| `tests/unit/test_pixel_phase3.py` | Phase 3 战斗回归测试。 |

### 4.2 关键决策

#### 1. 战斗规则先抽小步，不整块搬 CLI

CLI 的 `_combat()` / `_boss_combat()` 很大，直接搬会把 print/input 和 UI 绑死。这里先抽“一个玩家动作 + 敌人响应”的共享 step，`GameRunner` 负责节点、敌人、奖励和路线推进。这样 Phase 3 能落地，后续仍可继续把奖励、章节完成等流程下沉。

#### 2. 普通 Boss 节点按 CLI guardian 规则处理

当前 route 的 Boss 节点多数不是 `chapter.is_boss_chapter` 的特殊 Boss，而是章节 guardian。Pixel 按 CLI 同样做 HP/ATK 放大、禁止逃跑。真正的 `BossState` 也已支持，但本阶段测试重点覆盖 route boss 禁逃。

#### 3. 胜利回地图，失败进 GameOver

普通战斗胜利后需要继续路线，所以回 MapScreen 并显示奖励；玩家死亡进入 GameOverScreen。这样比“每场战斗结束都 GameOver”更符合当前游戏循环。

### 4.3 偏离原计划

| 原计划项 | 实际情况 | 原因 |
|---|---|---|
| 完整视觉动画：伤害飞字、暴击红字 + 抖动、玩家闪红、盾牌闪、敌人淡出、奖励飞字 | 只做了基础 HP bar、敌人闪框、结果/奖励文本 | 先保证真实战斗闭环；完整动效和素材表现更适合 Phase 4 美术/音频一起做。 |
| 音效接入 | 未做 | Phase 4 明确负责 BGM/SFX 接入；本阶段避免提前做半套音频。 |
| 固定 seed 下普通战斗与 Boss 战均结束并与 CLI 完全一致 | 单回合规则、禁逃、奖励推进已测；完整一局 parity 还没做 | Pixel 还没有自动完整一局和章节完成界面，完整 parity 属于 Phase 6。 |

这些偏离不影响 Phase 3 的核心目标：Pixel 已能进入并解决 combat 节点，不再卡在路线第一场战斗。

### 4.4 触发的项目原则

- **第一性原理**：先解决“战斗节点如何真实推进”这个核心闭环，再做动画和音效。
- **DRY**：战斗 step 放入 `engine/combat_actions.py`，不给 BattleScreen 写规则。
- **正交性**：Screen → GameRunner → engine/combat_actions；Screen 不接触 CLI。
- **禁止掩盖性质 fallback**：MP 不够、Boss 禁逃都明确提示，动作不被静默吞掉。
- **Phase handoff**：本文件即 Phase 3 交接文档。

---

## 5. 后续任务

### 5.1 Phase 4 入口

下一个 phase：**`pixel-phase-4` — 美术 & 音频接入**。

建议入口顺序：
1. 建 `audio.py`，接 title / chapter / boss / gameover BGM 和基础 SFX，音频不可用时显示静音状态。
2. 统一扩展 `assets.py`，所有屏幕继续通过 manifest 取 sprite。
3. 为 BattleScreen 增完整视觉反馈：伤害飞字、暴击红字、盾牌闪、敌人淡出、奖励飞字。
4. 接入 gpt-image-2 生成/后处理后的 title banner、玩家、Boss 资产，并写 asset card。

### 5.2 已知风险与未决问题

| 风险 / 未决项 | 影响 | 处理建议 |
|---|---|---|
| Pixel 还没有章节完成处理 | Boss 胜利后路线可推进，但章节结束奖励/进入下一章还未完整 UI 化 | Phase 4/5 前最好补一个 ChapterCompleteScreen 或在 MapScreen 处理 cursor 到尾部。 |
| 完整 parity 还没做 | 不能证明 Pixel 一整局指标等于 CLI | Phase 6 按 plan 做 `--pixel --auto --headless` 和 metrics 对比。 |
| `combat_actions.py` 只抽单回合，不含完整 CLI 战斗循环 | CLI 与 Pixel 仍有少量 orchestration 差异 | 后续做 parity 前继续下沉奖励、章节完成、战斗统计。 |
| 音效和完整动画缺失 | 体验仍偏工具壳 | Phase 4 统一做，不要在 Phase 3 补零散音效。 |

### 5.3 新会话立刻要读哪些文件

1. `AGENTS.md`
2. `plans/pixel-phases.md`
3. `handoffs/2026-05-04-pixel-phase-3-handoff.md`
4. `src/git_dungeon/ui_pixel/screens/battle.py`
5. `src/git_dungeon/ui_pixel/game_runner.py`
6. `src/git_dungeon/engine/combat_actions.py`
7. `src/git_dungeon/ui_pixel/assets.py`
8. `assets/manifest_sprites.json`
9. `assets/CREDITS.md`

### 5.4 推荐的第一条验证命令

```bash
cd /Users/hughlin/Projects/git-dungeon && \
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
PYTHONPATH=src .venv/bin/python -m git_dungeon . --pixel --seed 42 --pixel-smoke-frames 8 && \
PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_pixel_phase1.py tests/unit/test_pixel_phase2.py tests/unit/test_pixel_phase3.py -q
```

两条都 exit 0，说明 Pixel 启动、路线、非战斗和战斗核心仍完好。改音频/美术后继续跑：

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/ -m "not functional and not golden and not slow" -q
PYTHONPATH=src .venv/bin/python -m pytest tests/functional/ -q
PYTHONPATH=src .venv/bin/python -m pytest tests/golden_test.py -q
```
