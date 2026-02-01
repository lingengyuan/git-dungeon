# Git Dungeon - Story & Chapter System

> 基于 plan.md 设计：merge commit → 商店/休息点，revert commit → BOSS 战

## 1. 章节划分 (基于 plan.md 3.1)

```
根据 commit 类型自动划分章节：

┌─────────────────────────────────────────────────────────────────────┐
│  第一章：初始之地 (Initial Era)                                       │
│  ├─ 定义: 最初的 commits (Initial, README, config)                   │
│  ├─ 敌人: Initial commit, README.md, .gitignore                       │
│  ├─ 难度: ⭐                                                          │
│  └─ 描述: "在代码的虚无中，第一个 commit 诞生了..."                   │
├─────────────────────────────────────────────────────────────────────┤
│  第二章：功能涌现 (Feature Age)                                       │
│  ├─ 定义: feat: 类型 commits                                          │
│  ├─ 敌人: Feature x N                                                │
│  ├─ 难度: ⭐⭐                                                         │
│  └─ 描述: "新功能如雨后春笋般涌现，代码库日益膨胀..."                  │
├─────────────────────────────────────────────────────────────────────┤
│  第三章：修复时代 (Fix Age)                                           │
│  ├─ 定义: fix: 类型 commits                                           │
│  ├─ 敌人: Bug x N                                                    │
│  ├─ 难度: ⭐⭐⭐                                                        │
│  └─ 描述: "随着功能增加，Bug 也开始蔓延..."                           │
├─────────────────────────────────────────────────────────────────────┤
│  第四章：整合之路 (Integration Road) [基于 plan.md]                   │
│  ├─ 定义: merge: 类型 commits                                         │
│  ├─ 敌人: **Merge Conflict (BOSS!)**                                  │
│  ├─ 特性: 战斗后进入 **商店/休息点**                                  │
│  ├─ 难度: ⭐⭐⭐⭐⭐                                                      │
│  └─ 描述: "当多条分支汇聚之时，最强大的敌人出现了..."                  │
├─────────────────────────────────────────────────────────────────────┤
│  终章：版本传承 (Legacy)                                              │
│  ├─ 定义: release:, version:, tag: commits                            │
│  ├─ 敌人: Release, Version Bump                                       │
│  ├─ 难度: ⭐⭐⭐                                                        │
│  └─ 描述: "一切归于平静，但代码的传说将永存..."                       │
└─────────────────────────────────────────────────────────────────────┘
```

## 2. Git → 游戏元素映射 (来自 plan.md 3.1)

| Git 元素 | 游戏元素 | 实现 |
|----------|----------|------|
| commit message | 怪物名称 + 描述 | ✅ 已实现 |
| +lines (添加行数) | 攻击力 / 经验值 | ✅ 已实现 |
| -lines (删除行数) | 防御力 / 难度 | ✅ 已实现 |
| merge commit | **商店/休息点** | ⏳ 待实现 |
| branch commit | 隐藏关卡/支线任务 | ⏳ 暂不实现 |
| revert commit | **BOSS 战** | ⏳ 待实现 |

## 3. 故事系统实现

```python
# src/core/story.py

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

from ..config import GameConfig
from .git_parser import CommitInfo


class ChapterType(Enum):
    """章节类型"""
    INITIAL = "initial"       # 初始之地
    FEATURE = "feature"       # 功能涌现
    FIX = "fix"               # 修复时代
    INTEGRATION = "integration"  # 整合之路 (BOSS)
    LEGACY = "legacy"         # 版本传承


@dataclass
class Chapter:
    """章节定义"""
    type: ChapterType
    name: str
    description: str
    min_index: int
    max_index: int
    is_boss: bool = False
    has_shop: bool = False  # 基于 plan.md: merge commit → 商店
    boss_name: Optional[str] = None
    boss_hp_multiplier: float = 1.0


class StorySystem:
    """故事系统 - 管理章节和剧情"""
    
    # 章节配置 (基于 plan.md)
    CHAPTER_CONFIG = {
        ChapterType.INITIAL: {
            "name": "初始之地",
            "description": "在代码的虚无中，第一个 commit 诞生了...",
            "is_boss": False,
            "has_shop": False,
        },
        ChapterType.FEATURE: {
            "name": "功能涌现",
            "description": "新功能如雨后春笋般涌现，代码库日益膨胀...",
            "is_boss": False,
            "has_shop": False,
        },
        ChapterType.FIX: {
            "name": "修复时代",
            "description": "随着功能增加，Bug 也开始蔓延...",
            "is_boss": False,
            "has_shop": False,
        },
        ChapterType.INTEGRATION: {
            "name": "整合之路",
            "description": "当多条分支汇聚之时，最强大的敌人出现了...",
            "is_boss": True,
            "has_shop": True,  # merge commit 后进入商店
            "boss_name": "混沌融合体",
        },
        ChapterType.LEGACY: {
            "name": "版本传承",
            "description": "一切归于平静，但代码的传说将永存...",
            "is_boss": False,
            "has_shop": False,
        },
    }
    
    def __init__(self, commits: List[CommitInfo], config: GameConfig):
        self.commits = commits
        self.config = config
        self.chapters = self._parse_chapters()
        self.current_chapter_index = 0
        self.story_events: List[str] = []
    
    def _parse_chapters(self) -> List[Chapter]:
        """解析章节划分"""
        chapters = []
        
        # 根据 commit 类型自动划分
        current_type = None
        start_index = 0
        
        for i, commit in enumerate(self.commits):
            commit_type = self._get_chapter_type(commit)
            
            # 检测章节变化
            if current_type is None:
                current_type = commit_type
                start_index = i
            elif current_type != commit_type:
                # 结束当前章节，开始新章节
                config = self.CHAPTER_CONFIG[current_type]
                chapters.append(Chapter(
                    type=current_type,
                    name=config["name"],
                    description=config["description"],
                    min_index=start_index,
                    max_index=i - 1,
                    is_boss=config["is_boss"],
                    has_shop=config["has_shop"],
                ))
                current_type = commit_type
                start_index = i
        
        # 添加最后一个章节
        if current_type:
            config = self.CHAPTER_CONFIG[current_type]
            chapters.append(Chapter(
                type=current_type,
                name=config["name"],
                description=config["description"],
                min_index=start_index,
                max_index=len(self.commits) - 1,
                is_boss=config["is_boss"],
                has_shop=config["has_shop"],
            ))
        
        return chapters
    
    def _get_chapter_type(self, commit: CommitInfo) -> ChapterType:
        """根据 commit 判断章节类型 (基于 plan.md 3.1)"""
        msg = commit.message.lower()
        
        if commit.index == 0:
            return ChapterType.INITIAL
        elif "merge" in msg or "integration" in msg:
            return ChapterType.INTEGRATION
        elif "release" in msg or "version" in msg or "tag" in msg:
            return ChapterType.LEGACY
        elif msg.startswith("fix") or "bug" in msg or "hotfix" in msg:
            return ChapterType.FIX
        elif msg.startswith("feat") or "feature" in msg:
            return ChapterType.FEATURE
        else:
            # 默认按顺序分配
            return ChapterType.FEATURE
    
    def get_current_chapter(self) -> Chapter:
        """获取当前章节"""
        return self.chapters[self.current_chapter_index]
    
    def check_chapter_transition(self, commit_index: int) -> Optional[Chapter]:
        """检查是否进入新章节"""
        for i, chapter in enumerate(self.chapters):
            if chapter.min_index <= commit_index <= chapter.max_index:
                if i != self.current_chapter_index:
                    self.current_chapter_index = i
                    return chapter
        return None
    
    def display_chapter_intro(self, chapter: Chapter):
        """显示章节介绍"""
        chapter_num = self.current_chapter_index + 1
        
        print(f"""
{'='*60}
║               第 {chapter_num} 章：{chapter.name}
{'='*60}
📖 {chapter.description}
{'='*60}
""")
        
        if chapter.is_boss:
            print(f"⚠️  警告：{chapter.boss_name} 在前方等待！")
        
        if chapter.has_shop:
            print(f"🏪 击败本章 BOSS 后将进入商店")
        
        print()
    
    def display_chapter_complete(self, chapter: Chapter):
        """显示章节完成"""
        print(f"""
{'='*60}
✨ 章节完成：{chapter.name}
{'='*60}
""")
        
        if chapter.has_shop:
            self._display_shop()
    
    def _display_shop(self):
        """显示商店 (基于 plan.md: merge commit → 商店)"""
        player = self.player_state
        print(f"""
{'─'*40}
🏪        商店 / 休息点
{'─'*40}
💰 当前金币: {player.get("coins", 0)}

可用商品：
  [1] 🧪 生命药水     - 50金币 - 恢复 50 HP
  [2] 💧 法力药水     - 30金币 - 恢复 30 MP
  [3] ⚔️ 攻击卷轴     - 100金币 - 下次攻击 +10 伤害
  [4] 🛡️ 防御卷轴     - 100金币 - 下次受伤 -10 伤害
  [5] 💤 休息         - 免费 - 恢复 50% HP 和 MP
  [0] 🚪 离开商店

请选择 (0-5):
{'─'*40}
""")
    
    def display_ending(self):
        """显示结局 (基于 plan.md)"""
        print(f"""
{'█'*60}
{'█'}                                                            {'█'}
{'█'}            🎉 恭喜！你已经完成了 Git Dungeon！              {'█'}
{'█'}                                                            {'█'}
{'█'*60}

📖 故事结局：

   经过漫长的战斗，你终于击败了所有的 commit 怪物。
   
   你的代码之旅已经结束，但你创造的代码将永远留在这个仓库中。
   
   每一个 commit 都是一段历史，每一行代码都是一个故事。
   
   而你，就是这段历史的见证者和创造者。

{'─'*60}
📊 最终统计：
   总击败敌人: {len(self.story_events)}
   最终等级: {self.player_state.get("level", 1)}
   获得成就: 3/5

{'─'*60}
感谢游玩 Git Dungeon！
{"="*60}
""")
```

## 4. BOSS 战检测 (基于 plan.md: revert → BOSS)

```python
# src/core/boss.py

class BossSystem:
    """BOSS 战系统"""
    
    @staticmethod
    def is_boss_commit(commit) -> bool:
        """判断是否是 BOSS commit (基于 plan.md 3.1)"""
        msg = commit.message.lower()
        
        # revert commit → BOSS 战
        if "revert" in msg:
            return True
        
        # merge conflict → BOSS 战
        if "merge" in msg and ("conflict" in msg or "resolve" in msg):
            return True
        
        # 大型 merge commit
        if msg.startswith("merge") and len(msg) > 100:
            return True
        
        return False
    
    @staticmethod
    def get_boss_name(commit) -> str:
        """获取 BOSS 名称"""
        msg = commit.message
        
        if "revert" in msg.lower():
            return "时光回溯者"
        elif "merge" in msg.lower():
            return "混沌融合体"
        else:
            return "神秘存在"
    
    @staticmethod
    def get_boss_hp(commit) -> int:
        """计算 BOSS HP (基于 commit 规模)"""
        # BOSS HP = 总变更行数 × 2
        total_changes = commit.total_changes
        return max(100, total_changes * 2)
    
    def display_boss_intro(self, boss_name: str, hp: int):
        """显示 BOSS 登场"""
        print(f"""
{'█'*60}
{'█'}                                                            {'█'}
{'█'}               ⚔️  B O S S  降 临  ⚔️                       {'█'}
{'█'}                                                            {'█'}
{'█'*60}

👹 名称: {boss_name}
❤️  HP: {hp}
💀 描述: "这是你遇到过的最强大的敌人！"

准备战斗！
""")
```

## 5. 游戏循环更新

```python
def main():
    # ... 加载仓库 ...
    
    # 初始化故事系统
    story = StorySystem(state.commits, config)
    boss_system = BossSystem()
    
    # 显示第一章介绍
    chapter = story.get_current_chapter()
    story.display_chapter_intro(chapter)
    
    while state.current_commit and not state.is_game_over:
        print_status(state)
        
        commit = state.current_commit
        
        # 检查是否是 BOSS (基于 plan.md)
        if boss_system.is_boss_commit(commit):
            boss_name = boss_system.get_boss_name(commit)
            boss_hp = boss_system.get_boss_hp(commit)
            boss_system.display_boss_intro(boss_name, boss_hp)
        
        # 战斗
        if battle(state):
            print(f"✅ Victory! Gained experience.")
            
            # 击败 BOSS
            if boss_system.is_boss_commit(commit):
                print(f"\n🎉 BOSS {boss_name} 被击败了!")
                print(f"🏪 商店已开启！击败本章后可以休息...")
            
            state._advance_to_next_commit()
            
            # 检查章节切换
            new_chapter = story.check_chapter_transition(state.current_commit_index)
            if new_chapter:
                story.display_chapter_complete(story.get_current_chapter())
                story.display_chapter_intro(new_chapter)
        else:
            print(f"💀 Defeat!")
            break
    
    # 游戏结束 - 显示故事结局
    story.display_ending()
```

## 6. 实现优先级

| 功能 | 优先级 | 来源 |
|------|--------|------|
| 章节检测 | P0 | plan.md 3.1 |
| 章节介绍显示 | P0 | plan.md |
| BOSS 检测 (revert/merge) | P1 | plan.md 3.1 |
| BOSS 战特殊界面 | P1 | plan.md |
| 商店系统 (merge 后) | P2 | plan.md 3.1 |
| 结局展示 | P2 | plan.md |

## 7. 下一步

基于 plan.md 实现：
1. ✅ StorySystem 类 (章节管理)
2. ✅ BossSystem 类 (BOSS 检测)
3. ⏳ 集成到主循环
4. ⏳ 商店系统 (merge 后)

需要我开始实现吗？
