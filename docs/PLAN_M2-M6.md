# Git Dungeon — Project Plan (Post-M1)

> **当前状态**: M1 已完成（Deck/Energy/Status、Combat 状态机、奖励与 3 流派倾向、54 卡/27 敌/16 遗物/9 状态/6 事件、确定性与测试齐全）

> **下一步目标**: 在不做 UI 的前提下，显著提升"重开动力 + 叙事感 + 选择重量 + 内容扩展性"

---

## 0. 现状回顾（用于约束后续设计）

### 现有关键资产
- `src/git_dungeon/content/`：schema + loader + defaults（cards/enemies/relics/statuses/archetypes/events）
- `src/git_dungeon/engine/model.py`：Deck/Energy/Status 等运行态
- `src/git_dungeon/engine/engine.py`：战斗状态机
- `src/git_dungeon/engine/events.py`：事件类型
- `src/git_dungeon/engine/rules/`：rewards.py + archetype.py（奖励与倾向）
- `tests/`: 47 passed（含 golden、determinism、auto-play demo）

### 后续里程碑必须遵守
1. **确定性优先**: 任何随机均由 seed 驱动；新增系统必须可 Golden。
2. **数据驱动优先**: 内容尽量落在 `content/defaults/*.yml`，引擎只做"规则解释器"。
3. **10 分钟乐趣**: 每 1~3 战必须出现一次改变 build 的选择；失败后愿意立刻重开。

---

# M2 — 路径系统（章节地图） + 事件扩展

## M2 目标/验收
- 每章至少出现 2 次"路径分叉选择"，选择会影响未来 3~5 个节点的奖励/敌人/事件权重。
- 事件数量从 6 提升到 >= 15，并做到"有代价、有偏好、有 build 影响"。
- auto-play 可跑 2 章；Golden 覆盖：路径序列 + 关键事件效果。

---

## M2.1 新增 Chapter Route（节点图）

### 新增：src/git_dungeon/engine/route.py
- [ ] 定义 RouteNode / RouteGraph
  - node.kind: battle | event | shop | rest | elite | boss | treasure
  - node.meta: tags（risk/safe/greed/refactor-heavy/test-heavy 等）
- [ ] build_route(commits, seed, chapter_index, difficulty) -> RouteGraph
  - 固定 seed 下图稳定
  - 图的规模：每章 10~14 个节点（CLI 可读）
- [ ] next_nodes(current)：提供 2~3 个可选分支

### 修改：src/git_dungeon/engine/model.py
- [ ] RunState 增加：
  - chapter_index
  - route_state：当前 node_id、已访问节点列表
  - route_flags：最近选择（risk/safe）用于 bias

### 修改：src/git_dungeon/engine/engine.py
- [ ] 把"战斗串行"升级为"节点驱动"：
  - run_next_node()：battle/event/shop/rest/elite/boss
- [ ] CLI 输出分支选择（纯文本即可）：
  - 1) Safe path (heal/remove)
  - 2) Risk path (elite/relic odds)

### tests 新增/修改
- [ ] tests/test_m2_route_graph.py
  - seed 固定 -> 节点序列稳定
  - 分叉点数量满足最低要求
- [ ] Golden：保存 route 的 node kind 序列快照

---

## M2.2 事件系统升级：从"类型"到"事件脚本（effects）"

### 修改：src/git_dungeon/engine/events.py
- [ ] 统一事件效果执行入口：
  - apply_event_choice(run_state, choice_effects, rng)
- [ ] effects 设计（尽量通用、可组合）：
  - gain_gold(x) / lose_gold(x)
  - heal(x) / take_damage(x)
  - add_card(card_id) / remove_card(criteria) / upgrade_card(criteria)
  - add_relic(relic_id|rarity) / remove_relic(...)
  - apply_status(target, status_id, stacks)
  - trigger_battle(kind=elite|normal)
  - modify_bias(archetype_id, delta)
  - set_flag(key, value)（用于后续连锁事件）

### 修改：src/git_dungeon/content/schema.py
- [ ] EventDef 扩展字段：
  - choices[]: { text_key, effects[], conditions[] }
  - conditions 支持对 run_state / route_flags / archetype_bias 做判断
- [ ] loader 校验：
  - effects 的 opcode 必须在白名单中
  - 引用 card_id / relic_id / status_id 必须存在

### 修改：src/git_dungeon/content/defaults/events.yml
- [ ] 事件数量 >= 15（先把质量做高）
- [ ] 每个事件至少 2 个 choice，且至少 1 个 choice 有明确代价
- [ ] 增加"build 倾向事件"（针对 Debug/Test/Refactor）：
  - Debug：爆发换 TechDebt
  - Test：稳健换节奏变慢
  - Refactor：高收益但加债/扣血

### tests
- [ ] tests/test_m2_event_effects.py
  - 每个 opcode 的边界条件（不会负金币、不会无卡可删导致崩溃）
- [ ] Golden：固定 seed + 固定选择路径 -> run_state 快照一致

---

## M2.3 精英与 Boss 节点（把紧张点打出来）

### 修改：src/git_dungeon/content/defaults/enemies.yml
- [ ] 增加 tier: normal|elite|boss
- [ ] 至少新增：
  - elite >= 6
  - boss >= 3（每个有阶段机制）

### 修改：src/git_dungeon/engine/engine.py
- [ ] 节点 kind=elite/boss 时：
  - 调用 enemies tier 池
  - elite 掉落强化（见 M2.4）

### 修改：src/git_dungeon/engine/rules/rewards.py
- [ ] elite：遗物必掉 or 高概率掉；卡牌稀有度权重提升
- [ ] boss：提供"强遗物 + 大改 build 的选择"（例如 2 选 1 boss relic）

### tests
- [ ] tests/test_m2_elite_boss_rewards.py
- [ ] Golden：固定 seed 的 boss 战前 3 回合快照

---

# M3 — Meta 进度（失败也有推进：解锁/角色/内容包）

## M3 目标/验收
- 失败后玩家愿意立刻再开一局：有明确"我解锁了什么/离什么更近"。
- 只做 3 类解锁：角色、起手、内容包（避免变肝）。

---

## M3.1 元进度存档

### 新增：src/git_dungeon/engine/meta.py
- [ ] MetaProfile（本地 json 存档）
  - points
  - unlocks: {characters, starter_bundles, packs}
- [ ] load_meta(path) / save_meta(path)
- [ ] award_points(run_summary)：
  - 章节通关、精英击杀、无伤节点、首次击杀 boss 等

### 修改：src/git_dungeon/engine/model.py
- [ ] RunSummary 输出：
  - 死亡原因（damage/techdebt/burn 等）
  - archetype 倾向、关键卡牌、关键遗物
  - 用于 meta 结算

### 修改：CLI（若已有入口）
- [ ] --profile <path> 指定 meta 存档
- [ ] 每局结束打印：
  - 获得 points、可解锁项提示

### tests
- [ ] tests/test_m3_meta_profile.py（读写与兼容）
- [ ] tests/test_m3_award_points.py

---

## M3.2 角色（3 个足够）

### 新增：src/git_dungeon/content/defaults/characters.yml
- [ ] 3 角色定义（差异大）：
  - Developer（均衡）
  - Reviewer（净化 TechDebt/防御）
  - DevOps（回合触发"管道"：生成资源/抽牌/护甲）
- [ ] schema + loader 校验

### 修改：src/git_dungeon/engine/model.py
- [ ] RunState 增加 character_id
- [ ] 开局初始化根据角色配置生成起手牌组/起手遗物

### tests
- [ ] tests/test_m3_characters.py（起手差异与确定性）

---

## M3.3 内容包（让扩展变"加 YAML"）

### 新增：src/git_dungeon/content/packs/
- [ ] packs/<pack_id>/{cards.yml,enemies.yml,relics.yml,events.yml,...}
- [ ] loader 支持 pack 合并：
  - 默认 content + packs（按 meta unlock 过滤）
  - pack 优先级/冲突策略（id 冲突 -> fail）

### tests
- [ ] tests/test_m3_packs_loader.py

---

# M4 — 难度曲线与平衡（让 2~3 章能反复玩）

## M4 目标/验收
- Normal 难度 2 章可稳定通；Hard 难度需要 build 才能通。
- 至少 3 种 build 都能通关（避免唯一解）。
- 出现"有紧张点"的节奏：普通→精英→休整→boss。

---

## M4.1 难度参数表

### 新增：src/git_dungeon/engine/rules/difficulty.py
- [ ] 参数按 chapter 递增：
  - enemy hp/dmg scale
  - elite 概率
  - reward 质量
  - event 风险/收益倍率
- [ ] difficulty level：normal/hard（先两档）

### 修改：src/git_dungeon/engine/engine.py
- [ ] 章节开始设置 chapter_scale
- [ ] route 构建时引用 difficulty 参数（risk/safe 影响也可叠加）

### tests
- [ ] tests/test_m4_difficulty_scaling.py（不会爆炸/不会负数/不会无限战斗）

---

## M4.2 平衡工具（本地批量模拟）

### 新增：src/git_dungeon/tools/simulate.py
- [ ] 批量跑 auto-play：
  - 多 seed、不同 repo（可选）、不同角色、不同难度
- [ ] 输出 JSON 汇总：
  - 通关率、平均回合数、死亡原因 TopN、最强遗物/卡牌出现频率
- [ ] 仅本地工具，不上 CI（或做轻量 smoke）

### tests
- [ ] tests/test_m4_simulate_smoke.py（小样本可跑）

---

# M5 — 成就/挑战（轻量，不做 UI 也能很好玩）

## M5 目标/验收
- 增加"目标感"，让玩家愿意用不同 build/角色去尝试。
- 不做复杂系统：只做本地记录 + 结算展示。

### 新增：src/git_dungeon/engine/achievements.py
- [ ] 成就定义（YAML 或代码都可，建议 YAML）：
  - 无伤过精英
  - 只用 Test 卡通关一章
  - TechDebt 达到 X 但仍击杀 boss
  - 10 回合内击杀 boss
- [ ] 记录到 MetaProfile

### tests
- [ ] tests/test_m5_achievements.py

---

# M6 — AI 风味文本（可选，严格降级，不影响可玩）

## M6 目标/验收
- AI 只负责"文案润色/旁白/敌人一句话描述"，不碰数值与规则。
- 预生成 + 缓存，失败降级到模板文本仍可玩。

### 新增：src/git_dungeon/ai/
- [ ] client.py（抽象接口 + mock）
- [ ] cache.py（cache key: repo@sha + seed + lang + content_version + prompt_hash）
- [ ] prompts.py（短文本、长度限制）
- [ ] fallbacks.py（模板文案）

### 修改：src/git_dungeon/engine/engine.py
- [ ] --ai-text=off|on
- [ ] 章节开始批量生成本章文本包

### tests
- [ ] tests/test_m6_ai_cache.py
- [ ] tests/test_m6_ai_fallback.py

---

# 版本建议

| 版本 | 里程碑 | 核心功能 |
|------|--------|---------|
| v0.5 | M2 | route+events+elite/boss |
| v0.6 | M3 | meta+角色+内容包 |
| v0.7 | M4 | 难度曲线+模拟工具 |
| v0.8 | M5 | 成就挑战 |
| v0.9 | M6 | AI 文案（可选开关） |

---

# 每个里程碑统一 Done 定义（必须满足）

- [ ] `--seed` 确定性：同参数重复运行输出一致
- [ ] 新增系统都有单测 + 至少 1 个 Golden
- [ ] `--auto` 可跑通目标章数（M2:2章，M3+:至少2章）
- [ ] content loader 校验覆盖新增字段与引用完整性

---

# 附录 A：测试覆盖要求

| 类型 | 要求 |
|------|------|
| Unit | 每个新增类/函数有单元测试 |
| Golden | 固定 seed -> 确定快照 |
| Auto-play | 完整跑通 2 章无报错 |
| Coverage | 核心逻辑 > 80% |

---

# 附录 B：待办清单（用于日常跟踪）

## M2 待办
- [ ] route.py RouteNode/RouteGraph
- [ ] build_route() 函数
- [ ] model.py RunState 扩展
- [ ] engine.py 节点驱动
- [ ] events.py apply_event_choice()
- [ ] events.yml >= 15 事件
- [ ] enemies.yml elite/boss tier
- [ ] rewards.py elite/boss 奖励
- [ ] test_m2_route_graph.py
- [ ] test_m2_event_effects.py
- [ ] test_m2_elite_boss_rewards.py

## M3 待办
- [ ] meta.py MetaProfile
- [ ] RunSummary 输出
- [ ] --profile CLI 参数
- [ ] unlocks.yml
- [ ] characters.yml
- [ ] engine.py meta_unlocks
- [ ] run_failed_summary()
- [ ] CLI 进度显示
- [ ] packs/ 目录
- [ ] test_m3_meta_profile.py
- [ ] test_m3_award_points.py
- [ ] test_m3_characters.py
- [ ] test_m3_packs_loader.py

## M4 待办
- [x] difficulty.py 参数表 ✅
- [x] engine.py difficulty 集成 ✅
- [x] simulate.py 批量模拟 ✅
- [x] test_m4_difficulty_scaling.py ✅

## M5 待办
- [x] achievements.py 成就系统 ✅
- [x] test_m5_achievements.py ✅

## M6 待办
- [ ] ai/ 目录结构
- [ ] client.py + cache.py + prompts.py + fallbacks.py
- [ ] --ai-text CLI 参数
- [ ] test_m6_ai_cache.py
- [ ] test_m6_ai_fallback.py

---

> **最后更新**: 2026-02-03
> **版本**: M1 完成, M2-M6 规划完成
