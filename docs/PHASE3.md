# Phase 3: Lua 内容系统

> 开始日期: 2026-01-31  
> **状态: ✅ 已完成**

---

## 目标 ✅
实现可配置的 Lua/JSON 内容系统，支持多主题和自定义怪物/掉落。

---

## 1. Lua 内容系统 ✅ 已完成

### 核心文件

```
src/core/lua/
├── lua_engine.py      # Lua 引擎 (可降级为纯 JSON)
├── __init__.py        # 包导出
```

### 数据模型

| 类 | 说明 |
|------|------|
| `MonsterTemplate` | 怪物模板 (HP/ATK/DEF/技能/掉落) |
| `DropTable` | 掉落表 (概率/保底) |
| `Theme` | 主题配置 (怪物前缀/颜色) |

### 测试: 26/26 ✅

---

## 2. 内容定义示例

### JSON 格式 (无需 Lua)

```json
// monsters.json
{
  "SyntaxError": {
    "hp": 50,
    "attack": 15,
    "defense": 5,
    "experience": 30,
    "skills": ["TypeError"],
    "drop_table": "common_bugs"
  },
  "ImportError": {
    "hp": 80,
    "attack": 20,
    "experience": 50
  }
}

// themes.json
{
  "python": {
    "name": "Python",
    "icon": "🐍",
    "color_scheme": "blue",
    "monster_prefixes": ["SyntaxError", "ImportError"]
  }
}
```

### Lua 格式 (需要 lupa 库)

```lua
Monster.define {
    name = "BossMonster",
    hp = 500,
    attack = 50,
    experience = 500,
    skills = {"power_strike", "heal"},
    drop_table = "boss_loot"
}

DropTable.define("boss_loot", {
    {item = "Legendary Sword", chance = 0.05},
    {item = "Health Potion", chance = 0.3}
})
```

---

## 3. 内置主题

| 主题 | ID | 怪物示例 |
|------|-----|---------|
| Default | `default` | Bug, Feature, Crash |
| Python | `python` | SyntaxError, ImportError |
| JavaScript | `javascript` | TypeError, undefined |
| Git | `git` | MergeConflict, RebaseFail |

---

## 📊 测试统计

| 模块 | 测试数 | 通过 |
|------|--------|------|
| Phase 2 原有测试 | 167 | 167 ✅ |
| Lua 内容系统 | 26 | 26 ✅ |
| **总计** | **193** | **193** ✅ |

---

## 文件清单

```
src/core/lua/
├── __init__.py              # 导出 LuaEngine, MonsterTemplate 等
├── lua_engine.py            # 核心引擎 (500+ 行)

tests/unit/
└── test_lua_engine.py       # 26 个测试

docs/
└── PHASE3.md               # 本文档
```

---

## 使用方法

```python
from src.core.lua import LuaEngine

# 创建引擎
engine = LuaEngine()

# 直接添加怪物
from src.core.lua import MonsterTemplate
engine.monsters["MyMonster"] = MonsterTemplate(
    name="MyMonster",
    base_hp=100,
    base_attack=20,
)

# 加载 JSON 文件
engine.load_directory("content/")

# 导出到 JSON
engine.export_content("exported/")
```

---

## 下一步

- [ ] 集成到游戏引擎 (根据 commit 自动生成怪物)
- [ ] Phase 4: 性能优化与打包
