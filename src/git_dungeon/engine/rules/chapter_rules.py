# chapter_rules.py - Chapter system rules

"""
Chapter system for Git Dungeon.

Divides commits into chapters based on commit types:
- Initial (first commits)
- Features (feat: type)
- Fixes (fix: type)
- Integration (merge: type)
- Legacy (release/version: type)

Each chapter has:
- Name and description
- Enemy types
- Difficulty scaling
- Boss (for integration chapter)
- Shop (after chapter completion)
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional, Dict, Any
from enum import Enum

from git_dungeon.engine.rng import RNG
from git_dungeon.engine.events import GameEvent, EventType

if TYPE_CHECKING:
    from git_dungeon.engine.rules.boss_rules import BossSystem, BossState


class ChapterType(Enum):
    """Types of chapters"""
    INITIAL = "initial"
    FEATURE = "feature"
    FIX = "fix"
    INTEGRATION = "integration"
    LEGACY = "legacy"


@dataclass
class ChapterConfig:
    """Configuration for a chapter type"""
    chapter_type: ChapterType
    name: str
    description: str
    min_commits: int = 1
    max_commits: int = 50
    boss_chance: float = 0.0
    shop_enabled: bool = False
    gold_bonus: float = 1.0
    exp_bonus: float = 1.0
    enemy_hp_multiplier: float = 1.0
    enemy_atk_multiplier: float = 1.0


# Default chapter configurations
CHAPTER_CONFIGS = {
    ChapterType.INITIAL: ChapterConfig(
        chapter_type=ChapterType.INITIAL,
        name="混沌初开",
        description="在代码的虚无中，第一个 commit 诞生了...",
        min_commits=1,
        max_commits=3,
        boss_chance=0.0,
        shop_enabled=False,
        gold_bonus=0.8,
        exp_bonus=0.8,
        enemy_hp_multiplier=0.6,
        enemy_atk_multiplier=0.6,
    ),
    ChapterType.FEATURE: ChapterConfig(
        chapter_type=ChapterType.FEATURE,
        name="功能涌现",
        description="新功能如雨后春笋般涌现，代码库日益膨胀...",
        min_commits=5,
        max_commits=30,
        boss_chance=0.3,  # 30% chance for feature chapters
        shop_enabled=True,
        gold_bonus=1.0,
        exp_bonus=1.0,
        enemy_hp_multiplier=1.0,
        enemy_atk_multiplier=1.0,
    ),
    ChapterType.FIX: ChapterConfig(
        chapter_type=ChapterType.FIX,
        name="修复时代",
        description="随着功能增加，Bug 也开始蔓延...",
        min_commits=3,
        max_commits=25,
        boss_chance=0.4,  # 40% chance for fix chapters
        shop_enabled=True,
        gold_bonus=1.2,
        exp_bonus=1.3,
        enemy_hp_multiplier=1.1,
        enemy_atk_multiplier=1.4,
    ),
    ChapterType.INTEGRATION: ChapterConfig(
        chapter_type=ChapterType.INTEGRATION,
        name="整合之路",
        description="当多条分支汇聚之时，最强大的敌人出现了...",
        min_commits=1,
        max_commits=10,
        boss_chance=1.0,  # Always has boss
        shop_enabled=True,  # Shop after boss
        gold_bonus=2.0,
        exp_bonus=2.0,
        enemy_hp_multiplier=2.0,
        enemy_atk_multiplier=1.5,
    ),
    ChapterType.LEGACY: ChapterConfig(
        chapter_type=ChapterType.LEGACY,
        name="版本传承",
        description="一切归于平静，但代码的传说将永存...",
        min_commits=1,
        max_commits=15,
        boss_chance=0.3,
        shop_enabled=True,
        gold_bonus=1.5,
        exp_bonus=1.5,
        enemy_hp_multiplier=1.3,
        enemy_atk_multiplier=1.2,
    ),
}


@dataclass
class Chapter:
    """A single chapter in the game"""
    chapter_id: str  # e.g., "chapter_0", "chapter_1"
    chapter_index: int
    chapter_type: ChapterType
    config: ChapterConfig
    commits: List  # CommitInfo objects
    start_index: int
    end_index: int
    is_completed: bool = False
    enemies_defeated: int = 0
    gold_earned: int = 0
    exp_earned: int = 0
    _rng: any = None  # RNG for boss probability
    
    @property
    def name(self) -> str:
        return self.config.name
    
    @property
    def description(self) -> str:
        return self.config.description
    
    @property
    def enemy_count(self) -> int:
        return len(self.commits)
    
    @property
    def progress(self) -> float:
        if self.enemy_count == 0:
            return 1.0
        return self.enemies_defeated / self.enemy_count
    
    @property
    def is_boss_chapter(self) -> bool:
        """Check if this chapter has a boss."""
        if self.config.boss_chance <= 0:
            return False
        # Roll for boss (only if we have an RNG)
        if hasattr(self, '_rng') and self._rng:
            from git_dungeon.engine.rng import roll_chance
            return roll_chance(self._rng, self.config.boss_chance)
        # Default: use boss_chance as threshold
        return self.config.boss_chance > 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chapter_id": self.chapter_id,
            "chapter_index": self.chapter_index,
            "chapter_type": self.chapter_type.value,
            "name": self.name,
            "is_completed": self.is_completed,
            "enemies_defeated": self.enemies_defeated,
            "total_enemies": self.enemy_count,
            "progress": f"{self.progress * 100:.1f}%",
        }


class ChapterSystem:
    """
    Manages chapter division and progression.
    
    Flow:
    1. Parse commits into chapters based on type
    2. Track chapter progress
    3. Generate chapter events
    4. Handle chapter transitions
    5. Award chapter rewards
    """
    
    def __init__(self, rng: RNG):
        self.rng = rng
        self.chapters: List[Chapter] = []
        self.current_chapter_index: int = 0
    
    def parse_chapters(
        self,
        commits: List,
        chapter_index_offset: int = 0
    ) -> List[Chapter]:
        """
        Parse commits into chapters.
        
        Args:
            commits: List of CommitInfo objects
            chapter_index_offset: Starting index for chapter IDs
            
        Returns:
            List of Chapter objects
        """
        if not commits:
            return []
        
        self.chapters = []
        total_commits = len(commits)
        
        # Prepare indexed commits
        indexed_commits = []
        for i, commit in enumerate(commits):
            indexed_commits.append((i, total_commits, commit))
        
        current_chapter_type = self._get_chapter_type(0, total_commits, commits[0].message.lower() if hasattr(commits[0], 'message') else "")
        current_chapter_commits = []
        current_start_index = 0
        
        for i, total, commit in indexed_commits:
            commit_type = self._get_chapter_type(i, total, commit.message.lower() if hasattr(commit, 'message') else "")
            
            # Check if we should start a new chapter
            should_switch = self._should_switch_chapter(
                current_chapter_type,
                commit_type,
                len(current_chapter_commits),
                current_chapter_commits
            )
            
            if should_switch and current_chapter_commits:
                # Finalize current chapter
                chapter = self._create_chapter(
                    current_chapter_commits,
                    current_chapter_type,
                    current_start_index,
                    i - 1,
                    len(self.chapters) + chapter_index_offset
                )
                self.chapters.append(chapter)
                
                # Start new chapter
                current_chapter_type = commit_type
                current_chapter_commits = [commit]
                current_start_index = i
            else:
                current_chapter_commits.append(commit)
        
        # Don't forget the last chapter
        if current_chapter_commits:
            chapter = self._create_chapter(
                current_chapter_commits,
                current_chapter_type,
                current_start_index,
                len(commits) - 1,
                len(self.chapters) + chapter_index_offset
            )
            self.chapters.append(chapter)
        
        return self.chapters
    
    def _get_chapter_type(self, index: int, total: int, msg: str) -> ChapterType:
        """Determine chapter type from commit."""
        
        # First 2 commits are initial
        if index < 2:
            return ChapterType.INITIAL
        
        # Check commit message patterns (highest priority)
        if "merge" in msg or "integration" in msg:
            return ChapterType.INTEGRATION
        elif "release" in msg or "version" in msg or "tag" in msg:
            return ChapterType.LEGACY
        elif msg.startswith("fix") or " bug" in msg or "hotfix" in msg:
            return ChapterType.FIX
        elif msg.startswith("feat"):
            return ChapterType.FEATURE
        else:
            # Position-based for unclassified commits
            ratio = index / total
            if ratio < 0.4:
                return ChapterType.FEATURE
            elif ratio < 0.7:
                return ChapterType.FIX
            else:
                return ChapterType.LEGACY
    
    def _should_switch_chapter(
        self,
        current_type: ChapterType,
        new_type: ChapterType,
        current_count: int,
        commits: List
    ) -> bool:
        """
        Determine if we should switch chapters.
        
        Rules:
        - Switch on type change
        - Create new chapter every N commits for same type
        - Minimum commits per chapter
        """
        config = CHAPTER_CONFIGS[current_type]
        
        # Different type - check minimum
        if current_type != new_type:
            if current_type in [ChapterType.INTEGRATION, ChapterType.LEGACY]:
                if current_count >= 1:
                    return True
            else:
                if current_count >= config.min_commits:
                    return True
        
        # Same type - switch every max_commits
        if current_count >= config.max_commits:
            return True
        
        return False
    
    def _create_chapter(
        self,
        commits: List,
        chapter_type: ChapterType,
        start_index: int,
        end_index: int,
        chapter_num: int
    ) -> Chapter:
        """Create a chapter from commits."""
        config = CHAPTER_CONFIGS[chapter_type]
        
        return Chapter(
            chapter_id=f"chapter_{chapter_num}",
            chapter_index=chapter_num,
            chapter_type=chapter_type,
            config=config,
            commits=commits,
            start_index=start_index,
            end_index=end_index,
            _rng=self.rng,
        )
    
    def get_current_chapter(self) -> Optional[Chapter]:
        """Get current chapter."""
        if 0 <= self.current_chapter_index < len(self.chapters):
            return self.chapters[self.current_chapter_index]
        return None
    
    def advance_chapter(self) -> bool:
        """Advance to next chapter. Returns True if successful."""
        if self.current_chapter_index < len(self.chapters) - 1:
            self.current_chapter_index += 1
            return True
        return False
    
    def complete_current_chapter(self) -> Chapter:
        """Mark current chapter as complete and return it."""
        chapter = self.get_current_chapter()
        if chapter:
            chapter.is_completed = True
        return chapter
    
    def get_chapter_events(self, chapter: Chapter, previous_chapter: Optional[Chapter] = None) -> List[GameEvent]:
        """Generate events for chapter start/completion."""
        events = []
        
        # Chapter started event
        events.append(GameEvent(
            type=EventType.CHAPTER_STARTED,
            data={
                "chapter_id": chapter.chapter_id,
                "chapter_index": chapter.chapter_index,
                "chapter_name": chapter.name,
                "chapter_type": chapter.chapter_type.value,
                "description": chapter.description,
                "enemy_count": chapter.enemy_count,
                "is_boss_chapter": chapter.is_boss_chapter,
                "previous_chapter": previous_chapter.name if previous_chapter else None,
            }
        ))
        
        # If this is a boss chapter, add boss spawned event
        if chapter.is_boss_chapter:
            boss_name = self._get_boss_name(chapter)
            events.append(GameEvent(
                type=EventType.BOSS_SPAWNED,
                data={
                    "boss_name": boss_name,
                    "chapter_name": chapter.name,
                    "hp_multiplier": chapter.config.enemy_hp_multiplier,
                    "atk_multiplier": chapter.config.enemy_atk_multiplier,
                }
            ))
        
        return events
    
    def get_chapter_completion_events(
        self,
        chapter: Chapter,
        next_chapter: Optional[Chapter] = None
    ) -> List[GameEvent]:
        """Generate events for chapter completion."""
        events = []
        
        # Calculate rewards
        gold_reward = int(50 * chapter.config.gold_bonus * (1 + chapter.chapter_index * 0.2))
        exp_reward = int(100 * chapter.config.exp_bonus * (1 + chapter.chapter_index * 0.2))
        
        # Chapter completed event
        events.append(GameEvent(
            type=EventType.CHAPTER_COMPLETED,
            data={
                "chapter_id": chapter.chapter_id,
                "chapter_name": chapter.name,
                "chapter_type": chapter.chapter_type.value,
                "enemies_defeated": chapter.enemies_defeated,
                "total_enemies": chapter.enemy_count,
                "gold_reward": gold_reward,
                "exp_reward": exp_reward,
                "next_chapter_id": next_chapter.chapter_id if next_chapter else None,
                "next_chapter_name": next_chapter.name if next_chapter else None,
                "shop_enabled": chapter.config.shop_enabled,
            }
        ))
        
        # Shop event if enabled
        if chapter.config.shop_enabled:
            events.append(GameEvent(
                type=EventType.SHOP_ENTERED,
                data={
                    "shop_id": f"shop_{chapter.chapter_id}",
                    "chapter_name": chapter.name,
                    "gold": gold_reward,
                }
            ))
        
        return events
    
    def _get_boss_name(self, chapter: Chapter) -> str:
        """Get boss name for chapter."""
        boss_names = {
            ChapterType.INTEGRATION: ["混沌融合体", "分支吞噬者", "合并巨兽"],
            ChapterType.LEGACY: ["版本守护者", "发布巨龙", "Tag 守卫者"],
        }
        
        names = boss_names.get(chapter.chapter_type, ["古老存在"])
        
        # Use RNG to pick a name
        return self.rng.choice(names) if names else "Unknown Boss"
    
    def get_chapter_summary(self) -> str:
        """Get a summary of all chapters."""
        if not self.chapters:
            return "No chapters created yet."
        
        lines = []
        for i, chapter in enumerate(self.chapters):
            status = "✅" if chapter.is_completed else "🔄" if i == self.current_chapter_index else "⏳"
            progress = f"{chapter.progress * 100:.1f}%"
            
            lines.append(f"  {status} Chapter {i}: {chapter.name} ({chapter.chapter_type.value})")
            lines.append(f"      Enemies: {chapter.enemies_defeated}/{chapter.enemy_count} | Progress: {progress}")
        
        return "\n".join(lines)
    
    def get_chapter_boss(
        self,
        chapter: Chapter,
        boss_system: 'BossSystem' = None
    ) -> Optional['BossState']:
        """
        Get the boss for a chapter.
        
        Args:
            chapter: The chapter
            boss_system: BossSystem instance (creates one if not provided)
            
        Returns:
            BossState or None if no boss
        """
        if not chapter.is_boss_chapter:
            return None
        
        # Import here to avoid circular imports
        if boss_system is None:
            from git_dungeon.engine.rng import create_rng
            from .boss_rules import BossSystem
            boss_system = BossSystem(create_rng())
        
        # Get boss based on chapter type
        boss = boss_system.get_boss_for_chapter_type(
            chapter.chapter_type.value,
            chapter.chapter_index
        )
        
        return boss
    
    def is_chapter_complete(self, chapter: Chapter) -> bool:
        """Check if a chapter is complete."""
        return chapter.enemies_defeated >= chapter.enemy_count


# Helper function to get chapter config
def get_chapter_config(chapter_type: ChapterType) -> ChapterConfig:
    """Get configuration for a chapter type."""
    return CHAPTER_CONFIGS.get(chapter_type, CHAPTER_CONFIGS[ChapterType.FEATURE])


# Export
__all__ = [
    "ChapterType",
    "ChapterConfig",
    "CHAPTER_CONFIGS",
    "Chapter",
    "ChapterSystem",
    "get_chapter_config",
]
