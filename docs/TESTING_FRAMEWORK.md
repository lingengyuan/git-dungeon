# Git Dungeon — 自动化功能测试完整方案（强制门禁版 / Post-M3）

> 版本: v1.0 (2026-02-02)  
> 状态: **强制执行** (PR 门禁)

---

## 0. 硬性规则（必须遵守）

### 0.1 Feature DoD（每个功能必备）

每个功能（feature）完成 **必须**：

| 要求 | 说明 |
|------|------|
| 1) 新增/更新功能测试 | ≥2 个场景（happy + edge） |
| 2) 通过 CI 门禁 | `make test-func` + `make test-golden` |
| 3) Golden 更新纪律 | 若输出变化是预期的：允许更新，但必须写明"为何变化" |

### 0.2 PR 门禁

```
必须通过:
├── make test-func    # 功能测试 (27+ scenarios)
├── make test-golden  # 快照回归测试

可选（建议）:
├── make test         # 单元测试
├── make lint         # 代码检查
└── make format       # 代码格式化
```

### 0.3 确定性约束

| 禁止 | 必须 |
|------|------|
| 全局 `random` | 使用 seed 注入的 `RNG` |
| 真实时间依赖 | 时间来源固定或 mock |
| 网络请求 | 所有 I/O 可控或 mock |
| 外部真实仓库 | 统一用 `RepoFactory` 生成最小 git repo |

---

## 1. 测试分层与门禁

### 1.1 测试层级定义

| 层级 | 覆盖范围 | 门禁角色 |
|------|---------|---------|
| **Unit** | 纯函数/边界/轻量校验 | 不做门禁核心（但建议保留） |
| **Integration** | 引擎子系统联动 | 可选门禁 |
| **Functional** ⭐ | 完整玩法链路 | **必须门禁** |
| **Golden** ⭐ | 结构化快照回归 | **必须门禁** |

### 1.2 Functional 测试覆盖链路

```
开局 → 路径选择 → 战斗/事件 → 奖励/倾向 → 结算/存档
```

### 1.3 门禁策略

```makefile
# PR / push main 必跑
make test-func    # 功能测试
make test-golden  # Golden tests

# Nightly（非门禁）
make test-sim     # 大量 seeds / 批量自动跑
```

---

## 2. 目录结构（标准）

```
tests/
├── harness/                  # 测试框架层
│   ├── scenario.py          # Scenario/Runner/RepoFactory
│   ├── assertions.py        # 断言库（27+ 结构化断言）
│   └── snapshots.py         # stable_serialize / golden compare / verify
├── functional/              # 功能测试（每个功能一个文件）
│   ├── test_m3_meta_func.py        # M3 Meta
│   ├── test_m3_characters_func.py  # M3 Characters
│   ├── test_m3_packs_func.py       # M3 Packs
│   └── ...                           # 后续 M4/M5/M6...
├── golden/                  # 快照回归测试
│   ├── m3_meta_profile_default.json
│   ├── m3_character_starters.json
│   ├── m3_packs_info.json
│   └── m3_points_calculation.json
└── ...                      # 其他测试目录
```

---

## 3. Harness 规范（必须实现且保持稳定）

### 3.1 Scenario 结构（必须字段）

```python
@dataclass
class Scenario:
    id: str                      # 全局唯一，作为 golden 文件名
    seed: int                    # 随机种子
    repo_builder: Callable       # 构建最小仓库
    config: Dict                 # difficulty/character/packs/lang
    steps: List[Step]            # 脚本化选择/行为
    expect: List[Expectation]    # 断言与快照规则
```

### 3.2 Step 类型（最少支持）

| Step 类型 | 用途 |
|----------|------|
| `ChoosePath(index)` | 路线分叉选择（M2） |
| `ChooseEvent(option)` | 事件选项选择（M2+） |
| `ShopBuy(item_id\|tag\|rarity)` | 商店购买 |
| `Play(policy, actions)` | 战斗策略 |
| `RunNodes(n)` | 运行 n 个节点/战斗（推荐） |
| `EndRun()` | 结束/结算（触发 meta） |

### 3.3 Runner 输出（必须字段）

```python
@dataclass
class ScenarioResult:
    run_state: Dict              # 可 stable serialize
    meta_profile: Optional[Dict] # 若使用 profile
    snapshots: Dict              # battle/route/rewards/meta
    logs: List[str]              # stdout/stderr（仅辅助定位）
```

### 3.4 RepoFactory（必须能力）

```python
class RepoFactory:
    @staticmethod
    def basic() -> Dict:
        """feat/fix/docs/refactor 混合"""
    
    @staticmethod
    def with_merge() -> Dict:
        """含分支与 merge commit"""
    
    @staticmethod
    def with_revert() -> Dict:
        """含 revert"""
    
    @staticmethod
    def test_heavy() -> Dict:
        """tests/ 路径占比高"""
    
    @staticmethod
    def large_diff() -> Dict:
        """大量 diff lines"""
```

**所有 repo 必须满足**：
- commit message 与文件路径可控
- commit time 固定（避免时间漂移）
- 构建耗时 < 1s

---

## 4. Assertions 规范（必须采用"结构化断言"）

### 4.1 强约束断言（必须稳定）

| 断言类型 | 说明 |
|---------|------|
| 解锁过滤 | 锁定内容绝不出现 |
| points 计算 | 规则正确 |
| pack 冲突 | 必须 fail |
| pack 缺引用 | 必须 fail |
| seed 确定性 | 同输入同输出 |

### 4.2 弱约束断言（避免脆弱）

```python
# ✅ 正确：断言范围/类型
assert 50 <= points <= 200
assert len(cards) >= 5
assert any(card.tags.contains("debug") for card in cards)

# ❌ 错误：断言具体 id（脆弱）
assert "debug_strike" in cards  # 禁止
assert cards[0].id == "strike"  # 禁止
```

---

## 5. Golden 快照规则（必须遵守）

### 5.1 允许写入快照的内容

| 类型 | 内容 |
|------|------|
| route | 节点 kind 序列、分叉点位置 |
| battle | 前 N 回合（建议 N=3~5）手牌 id、能量、状态 stacks、敌人 intent |
| rewards | 候选卡 ids、遗物 ids、金币变化 |
| meta | points 增量、unlocks 增量、profile 默认结构 |

### 5.2 禁止写入快照的内容

| 类型 | 原因 |
|------|------|
| stdout 大段文本 | 易变、AI 生成 |
| AI 文案 | 易变、测试目的不相关 |
| 非确定性字段 | 时间戳、路径临时目录 |

### 5.3 更新快照纪律（强制）

**Golden 更新必须在 PR 描述写明**：

```markdown
## Golden 快照更新

### 变更原因
[为什么预期变化]

### 影响的 scenario ids
- m3_meta_points_happy
- m3_character_starters
```

**不允许**：顺手更新 golden 让 CI 过但无说明

---

## 6. Feature → Functional 的强制映射（Definition of Done）

### 6.1 DoD 检查清单

| 要求 | 完成标准 |
|------|---------|
| Happy scenario | 1 个成功路径测试 |
| Edge scenario | 1 个失败/边界测试 |
| 断言覆盖 | 强约束 + 结构化 |
| CI 通过 | `make test-func` + `make test-golden` |

### 6.2 Edge case 最小集合

每个功能至少覆盖一种：

- [ ] 资源不足（金币/能量/卡池空）
- [ ] 条件不满足（事件/解锁）
- [ ] 存档缺字段/迁移
- [ ] pack 冲突/缺引用
- [ ] 非法参数（character_id/pack_id）
- [ ] 失败路径（死亡/退出）

---

## 7. Post-M3 必须具备的功能测试清单（最低要求）

> 已完成 M3，必须确保至少以下 10 个场景存在并通过

### 7.1 Meta（至少 3）

| # | Scenario ID | 输入 | 断言 | Golden |
|---|------------|------|------|--------|
| 1 | `m3_meta_points_happy` | 完整流程 | points 增量正确；存档一致 | points 计算快照 |
| 2 | `m3_meta_profile_migration_edge` | 缺字段/旧字段 | 加载不崩；默认补齐 | 默认 profile 结构 |
| 3 | `m3_meta_award_bonus_edge` | 精英/无伤 | bonus 规则正确 | - |

### 7.2 Unlock Filtering（至少 2）

| # | Scenario ID | 输入 | 断言 | Golden |
|---|------------|------|------|--------|
| 4 | `m3_unlock_filter_locked_never_drawn_happy` | 未解锁内容 | 绝不出现（强约束） | - |
| 5 | `m3_unlock_after_purchase_changes_pool_happy` | 解锁后重跑 | 候选池变化；deterministic | - |

### 7.3 Characters（至少 2）

| # | Scenario ID | 输入 | 断言 | Golden |
|---|------------|------|------|--------|
| 6 | `m3_character_starters_happy` | 3 角色 | 起始配置生效 | character starters |
| 7 | `m3_character_invalid_edge` | 非法 character_id | fail + 稳定错误 | - |

### 7.4 Packs（至少 3）

| # | Scenario ID | 输入 | 断言 | Golden |
|---|------------|------|------|--------|
| 8 | `m3_packs_merge_happy` | 默认 + pack | registry 合并正确；内容可抽到 | pack info |
| 9 | `m3_pack_conflict_edge` | id 冲突 pack | loader 必须 fail（强约束） | - |
| 10 | `m3_pack_missing_reference_edge` | 引用不存在 | loader 必须 fail（强约束） | - |

---

## 8. 命令速查表

```bash
# 运行游戏
make run

# 测试（按优先级）
make test-func    # ⭐ 功能测试（PR 门禁）
make test-golden  # ⭐ Golden 快照（PR 门禁）
make test         # 单元测试（本地快速检查）
make test-all     # 全部测试

# 代码质量
make lint         # 代码检查
make format       # 代码格式化

# 清理
make clean        # 清理缓存

# 开发
make dev-install  # 安装开发依赖
make pre-commit-install  # 安装预提交 hook
```

---

## 9. 违反规则的后果

| 违规类型 | 处理方式 |
|---------|---------|
| PR 缺少功能测试 | ❌ 拒绝合并 |
| 功能测试不通过 | ❌ 拒绝合并 |
| Golden 更新无说明 | ❌ 拒绝合并 |
| 使用全局 random/time | ❌ 拒绝合并 |
| 依赖外部真实仓库 | ❌ 拒绝合并 |

---

## 10. 演进与例外

- **Minor 更新**：修改 harness 代码 → 同步更新相关 golden 快照
- **Major 更新**：框架结构变更 → 更新本文档 + 所有相关 golden
- **例外申请**：在 PR 中说明为什么必须违反某条规则

---

## 11. 附录：当前测试覆盖率

### 11.1 M3 功能测试覆盖

| 模块 | Scenarios | 状态 | Golden |
|------|----------|------|--------|
| Meta | 8 | ✅ | 2 |
| Characters | 9 | ✅ | 1 |
| Packs | 10 | ✅ | 1 |
| **总计** | **27** | **✅** | **4** |

### 11.2 运行结果

```bash
$ make test-func
PYTHONPATH=src python3 -m pytest tests/functional/ -v
============================== 27 passed in 2.31s ==============================

$ make test-golden
PYTHONPATH=src python3 -m pytest tests/golden_test.py -v
============================== 4 passed in 0.5s ==============================
```

---

## 8. 命令与脚本（必须提供）

### 8.1 Makefile（必须）

`Makefile` 至少包含：

| 命令 | 说明 |
|------|------|
| `make run` | 运行游戏 |
| `make test` | unit/integration 测试（快速本地检查） |
| `make test-func` | **functional 测试（PR 门禁）** |
| `make test-golden` | **golden 快照测试（PR 门禁）** |
| `make test-all` | 全部测试 |
| `make lint` | 代码检查（ruff/mypy） |
| `make format` | 代码格式化（ruff/black） |

**建议新增**：

| 命令 | 说明 |
|------|------|
| `make golden-update` | 显式更新 golden（仅预期变化时用） |
| `make test-sim` | nightly 批量跑（多 seed 组合） |
| `make clean` | 清理缓存 |
| `make dev-install` | 安装开发依赖 |

### 8.2 pytest 组织建议（可选）

```bash
# 功能测试（全量）
pytest tests/functional/ -v

# Golden 测试
pytest tests/golden_test.py -v

# 单元测试
pytest tests/ -m "not functional and not golden" -v

# 带标记运行
pytest -m "functional" -v    # 只跑 functional
pytest -m "golden" -v        # 只跑 golden
pytest -m "slow" -v          # 慢速测试（nightly）
```

---

## 9. CI 门禁（GitHub Actions 必须配置）

### 9.1 PR 门禁工作流（必须）

```yaml
# .github/workflows/ci.yml
name: CI

on:
  pull_request:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      
      - name: Run Functional Tests ⭐
        run: make test-func
      
      - name: Run Golden Tests ⭐
        run: make test-golden
      
      - name: Lint (optional)
        run: make lint
      
      - name: Unit Tests (optional)
        run: make test
```

### 9.2 Nightly 工作流（可选）

```yaml
# .github/workflows/nightly.yml
name: Nightly

on:
  schedule:
    - cron: '0 2 * * *'  # 每天 02:00 UTC
  workflow_dispatch:

jobs:
  simulation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -e ".[dev]"
      - run: make test-sim
        env:
          SEEDS: '42,123,456,789,9999'
          CHARACTERS: 'developer,reviewer,devops'
```

**Nightly 输出示例**：

```
Nightly Test Results
====================
Seeds tested: 5
Characters: 3
Packs: 3
Total runs: 45
Success rate: 42/45 (93.3%)
Avg run time: 2.3s
Failed seeds: [456, 789]
```

---

## 10. 反脆弱要求（必须执行）

### 10.1 确定性控制

| 禁止 | 必须 |
|------|------|
| `import random` | 使用 `from git_dungeon.engine.rng import DefaultRNG` |
| `time.time()` | 使用 `seed` 注入时间或 mock |
| 网络请求 | 所有 I/O 可控或 mock |

**正确示例**：

```python
# ✅ 正确：从 seed 创建 RNG
rng = DefaultRNG(seed=42)
value = rng.randint(1, 100)

# ❌ 错误：使用全局 random
import random
value = random.randint(1, 100)
```

### 10.2 性能预算

| 测试类型 | 目标耗时 | 当前状态 |
|---------|---------|---------|
| PR 门禁（test-func + test-golden） | < 30s | ✅ ~5s |
| functional 单次 | < 10s | ✅ ~0.1s/scenario |
| unit 单次 | < 1s | ✅ ~0.01s/test |
| nightly (test-sim) | < 5min | 批量运行 |

### 10.3 输出稳定化

所有快照通过 `stable_serialize` 处理：

```python
from tests.harness.snapshots import stable_serialize

# 处理前
data = {
    "temp_path": "/tmp/abc123",  # 不稳定
    "timestamp": 1699999999,     # 每次不同
    "cards": [{"id": "strike"}, {"id": "defend"}]
}

# 处理后（stable_serialize 自动过滤/排序）
{
    "cards": [{"id": "defend"}, {"id": "strike"}]  # 按 id 排序
}
```

**stable_serialize 规则**：
- dict key 排序
- list 按 id 排序
- 过滤临时路径/时间戳等非确定性字段
- dataclass 转 dict 递归处理

---

## 11. 扩展到后续里程碑时的测试要求（提前写死）

### 11.1 M2（Route + Event 脚本）新增最低场景（至少 6）

| Scenario ID | 说明 |
|------------|------|
| `m2_route_graph_determinism_golden` | 同 seed 同 route 结构 |
| `m2_route_branch_count_happy` | 分叉数量符合预期 |
| `m2_route_branch_influence_happy` | risk vs safe 影响后续节点 |
| `m2_event_opcode_happy_<opcode>` | 每个 opcode 至少 1 |
| `m2_event_opcode_edge_<opcode>` | 每个 opcode 至少 1 边界 |
| `m2_elite_boss_rewards_golden` | 精英/BOSS 奖励快照 |

### 11.2 M4（难度 + 精英/BOSS）新增最低场景（至少 5）

| Scenario ID | 说明 |
|------------|------|
| `m4_difficulty_scaling_bounds` | 难度在合理范围内 |
| `m4_elite_drop_rules_strict` | 精英掉落规则严格 |
| `m4_boss_phase_snapshot_golden` | BOSS 阶段快照 |
| `m4_multi_build_can_win_smoke` | 3 build 至少可通 |
| `m4_hard_mode_requires_build_smoke` | 困难模式需要构建 |

### 11.3 M5（成就）新增最低场景（至少 3）

| Scenario ID | 说明 |
|------------|------|
| `m5_achievement_trigger_happy` | 成就触发正确 |
| `m5_achievement_not_trigger_edge` | 条件不满足不触发 |
| `m5_achievement_persist_profile_happy` | 成就持久化到 profile |

### 11.4 M6（AI 文案）新增最低场景（至少 3）

| Scenario ID | 说明 |
|------------|------|
| `m6_ai_off_no_calls_happy` | AI 关闭时不调用 API |
| `m6_ai_on_cache_hit_happy` | 缓存命中返回正确结果 |
| `m6_ai_failure_fallback_edge` | API 失败时 fallback 到默认值 |

---

## 12. PR 模板（必须执行）

PR 描述必须包含以下模板：

```markdown
## 实现的功能（Feature List）

- [ ] 功能 1
- [ ] 功能 2
- [ ] ...

## 新增/更新的 Scenario IDs

### 新增
- `m3_meta_points_happy`
- `m3_pack_conflict_edge`

### 更新
- （无）

## Golden 快照更新

- [ ] 无变更
- [ ] 有变更，更新了以下快照：

| Snapshot | 变更原因 |
|----------|----------|
| `m3_character_starters.json` | 角色 HP 调整 |

## CI 测试结果

### make test-func
```
27 passed in 2.31s
```

### make test-golden
```
4 passed in 0.5s
```

### make test（可选）
```
87 passed, 8 warnings
```

## 注意事项
（其他需要 reviewer 注意的事项）
```

---

## 13. 违反规则的后果

| 违规类型 | 处理方式 |
|---------|---------|
| PR 缺少功能测试 | ❌ 拒绝合并 |
| 功能测试不通过 | ❌ 拒绝合并 |
| Golden 更新无说明 | ❌ 拒绝合并 |
| 使用全局 random/time | ❌ 拒绝合并 |
| 依赖外部真实仓库 | ❌ 拒绝合并 |
| PR 模板不完整 | ❌ 拒绝合并 |

---

## 14. 演进与例外

- **Minor 更新**：修改 harness 代码 → 同步更新相关 golden 快照
- **Major 更新**：框架结构变更 → 更新本文档 + 所有相关 golden
- **例外申请**：在 PR 中说明为什么必须违反某条规则

---

## 15. Golden 更新纪律（强制）

**任何 PR 更新 golden 必须在 PR 描述中写明**：

| 字段 | 内容 |
|------|------|
| **为什么输出变化是预期的** | 功能变更/规则调整/内容扩充说明 |
| **影响的 scenario ids** | 具体哪些场景的快照需要更新 |
| **快照文件名** | `tests/golden/<id>.json` |

**禁止**：
- 无理由"刷新 golden 让 CI 过"
- "顺手更新 golden" 但无说明

**正确示例**：

```markdown
## Golden 快照更新

### 变更原因
新增 debug_pack 内容包，扩展了卡池。

### 影响的 snapshot ids
- `m3_packs_info`（增加了 debug_pack 信息）

### 验证
- make test-func: 56 passed
- make test-golden: 5 passed
```

---

## 16. 断言分层（强断言 vs 弱断言）

### 16.1 强断言（门禁级约束，必须稳定）

| 断言类型 | 示例 |
|---------|------|
| 解锁过滤 | 锁定内容绝不出现 |
| pack 冲突 | loader 必须 fail |
| pack 缺引用 | loader 必须 fail |
| points 计算 | 规则正确 |
| seed 确定性 | 同输入同输出 |

**示例**：

```python
# ✅ 强断言：永不出现锁定内容
assert locked_content_id not in reward_pool

# ✅ 强断言：冲突必须 fail
with pytest.raises(LoaderError):
    loader.load_pack("conflict_pack")
```

### 16.2 弱断言（内容扩充时避免脆弱）

| 类型 | 推荐方式 | 禁止方式 |
|------|---------|---------|
| 卡牌 | `any(c.tags.contains("debug") for c in cards)` | `c.id == "debug_strike"` |
| 遗物 | `len(relics) >= 3` | `relics[0].id == "git_init"` |
| 敌人 | `any(e.tier == "elite" for e in enemies)` | `e.id == "legacy_monolith"` |
| 数量 | `5 <= count <= 20` | `count == 10` |

**示例**：

```python
# ✅ 弱断言：断言范围
assert 5 <= len(cards) <= 20
assert any("debug" in c.tags for c in cards)

# ❌ 禁止：锁死具体 id
assert "debug_strike" in cards
```

---

## 17. PR 门禁耗时预算

| 类型 | 目标耗时 | 当前状态 | 违规处理 |
|------|---------|---------|---------|
| **PR 门禁总计** | < 30s | ~5s | 需优化或解释 |
| **functional 单 scenario** | < 300ms | ~50ms | 需拆/减断言 |
| **golden 单 snapshot** | < 100ms | ~10ms | 需优化快照 |

**优化策略**：
- 功能测试禁止大规模 simulate（放 nightly）
- 单个 scenario 超时：拆分场景 / 减少断言 / 缩场景
- golden 过大：只保留关键结构，移除冗余数据

---

## 18. 补强测试 v1.1（建议补充）

### 18.1 失败路径/错误信息稳定性（2 个）

| # | Scenario ID | 输入 | 断言 | Golden |
|---|------------|------|------|--------|
| 11 | `m2_invalid_route_choice_edge` | 非法分叉选择（index 越界） | 稳定失败类型 + 稳定错误信息 | - |
| 12 | `m3_profile_corruption_edge` | meta 存档 JSON 损坏/字段类型错 | 明确报错或自动修复策略一致 | - |

### 18.2 内容包合并强约束回归（2 个）

| # | Scenario ID | 输入 | 断言 | Golden |
|---|------------|------|------|--------|
| 13 | `m3_pack_override_forbidden_edge` | 同 id 重复但内容不同 | fail + 指出冲突 id | - |
| 14 | `m3_pack_unlock_filter_strict_golden` | 未解锁时跑 N 次抽取（固定 seed） | 永不出现锁定内容 | 序列结构 |

### 18.3 Route / Elite-BOSS 关键结构快照（2 个）

| # | Scenario ID | 输入 | 断言 | Golden |
|---|------------|------|------|--------|
| 15 | `m2_route_branch_influence_golden` | 同 seed 分叉点选 safe/risk | 后续 5 节点 kind 序列不同 | 结构快照 |
| 16 | `m2_elite_boss_phase_snapshot_golden` | boss 战前 3 回合 | intent + 状态 stacks + 能量 | 阶段快照 |

---

## 19. M4/M5/M6 强制新增测试配额

### 19.1 M4（难度/平衡/精英 BOSS 扩展）

**必须新增**：≥5 functional + ≥2 golden

| Scenario ID | 说明 |
|------------|------|
| `m4_difficulty_scaling_bounds` | 难度在合理范围内 |
| `m4_elite_drop_rules_strict` | 精英掉落规则严格 |
| `m4_boss_phase_snapshot_golden` | BOSS 阶段快照 |
| `m4_multi_build_can_win_smoke` | 3 build 至少可通 |
| `m4_hard_mode_requires_build_smoke` | 困难模式需要构建 |

### 19.2 M5（成就）

**必须新增**：≥3 functional

| Scenario ID | 说明 |
|------------|------|
| `m5_achievement_trigger_happy` | 成就触发正确 |
| `m5_achievement_not_trigger_edge` | 条件不满足不触发 |
| `m5_achievement_persist_profile_happy` | 成就持久化到 profile |

### 19.3 M6（AI 文案）

**必须新增**：≥3 functional

| Scenario ID | 说明 |
|------------|------|
| `m6_ai_off_no_calls_happy` | AI 关闭时不调用 API |
| `m6_ai_on_cache_hit_happy` | 缓存命中返回正确结果 |
| `m6_ai_failure_fallback_edge` | API 失败时 fallback 到默认值 |

**注意**：AI 文案不进入普通 golden（仅专门的 fallback golden）

---

## 20. PR 门禁标准（复制到 PR 模板）

```markdown
## 门禁检查

- [ ] `make test-func` 通过（56+ scenarios）
- [ ] `make test-golden` 通过（4+ snapshots）

## Golden 快照更新

- [ ] 无变更
- [ ] 有变更，更新了以下快照：

| Snapshot | 变更原因 |
|----------|----------|
| `<id>.json` | <原因> |

## 功能测试覆盖

- [ ] 新功能至少新增 2 个 functional scenarios（happy+edge）
- [ ] 影响的 scenario ids: `<列出>`

## 性能检查

- [ ] PR 门禁耗时未显著上升（>30s 需解释）
```

---

## 21. 附录：当前测试覆盖率

### 21.1 功能测试统计

| 模块 | Scenarios | 状态 | Golden |
|------|----------|------|--------|
| M2 Route + Event + Elite-BOSS | 29 | ✅ | 2 |
| M3 Meta | 8 | ✅ | 2 |
| M3 Characters | 9 | ✅ | 1 |
| M3 Packs | 10 | ✅ | 1 |
| **总计** | **56** | **✅** | **6** |

### 21.2 运行结果

```bash
$ make test-func
PYTHONPATH=src python3 -m pytest tests/functional/ -v
============================== 56 passed in 3.25s ==============================

$ make test-golden
PYTHONPATH=src python3 -m pytest tests/golden_test.py -v
============================== 4 passed in 0.05s ==============================
```

---

## 22. 命令速查表

```bash
# ===== 核心命令（PR 门禁） =====
make test-func    # 功能测试（56 scenarios）⭐
make test-golden  # 快照回归测试 ⭐

# ===== 本地开发 =====
make run          # 运行游戏
make test         # 单元测试（快速）
make test-all     # 全部测试
make lint         # 代码检查
make format       # 代码格式化
make clean        # 清理缓存

# ===== 高级 =====
make golden-update  # 更新 golden（谨慎使用）
make test-sim       # Nightly 批量模拟
make dev-install    # 安装开发依赖
make pre-commit-install  # 安装预提交 hook

# ===== 手动 pytest =====
pytest tests/functional/ -v           # 功能测试
pytest tests/golden_test.py -v        # Golden 测试
pytest tests/ -v --tb=short           # 全部测试
pytest tests/ -m "slow" -v            # 慢速测试
```

---

## 23. 违反规则的后果

| 违规类型 | 处理方式 |
|---------|---------|
| PR 缺少功能测试 | ❌ 拒绝合并 |
| 功能测试不通过 | ❌ 拒绝合并 |
| Golden 更新无说明 | ❌ 拒绝合并 |
| 使用全局 random/time | ❌ 拒绝合并 |
| 依赖外部真实仓库 | ❌ 拒绝合并 |
| PR 模板不完整 | ❌ 拒绝合并 |
| 单 scenario 超时（>300ms） | ⚠️ 需优化 |
| PR 门禁总耗时 > 30s | ⚠️ 需解释 |

---

**维护者**: Git Dungeon Team  
**最后更新**: 2026-02-02  
**版本**: v1.1

---

## 历史版本

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.1 | 2026-02-02 | 补强测试规则、M4/M5/M6 配额、Golden 更新纪律、断言分层、耗时预算 |
| v1.0 | 2026-02-02 | 初始版本（M3 功能测试框架） |
