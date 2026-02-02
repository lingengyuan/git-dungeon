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

**维护者**: Git Dungeon Team  
**最后更新**: 2026-02-02  
**版本**: v1.0
