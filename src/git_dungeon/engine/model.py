# model.py - Core data models for the game state

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class EntityType(Enum):
    """Entity types in the game"""
    PLAYER = "player"
    ENEMY = "enemy"
    ITEM = "item"
    NPC = "npc"


class CombatActionType(Enum):
    """Player combat actions"""
    ATTACK = "attack"
    DEFEND = "defend"
    SKILL = "skill"
    ITEM = "item"
    ESCAPE = "escape"


class ItemRarity(Enum):
    """Item rarity levels"""
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    CORRUPTED = "corrupted"


@dataclass
class Stat:
    """A single stat value"""
    base: int
    modifier: int = 0
    
    @property
    def value(self) -> int:
        return self.base + self.modifier
    
    def add_modifier(self, amount: int) -> None:
        self.modifier += amount
    
    def remove_modifier(self, amount: int) -> None:
        self.modifier = max(0, self.modifier - amount)
    
    def reset_modifiers(self) -> None:
        self.modifier = 0


@dataclass
class Stats:
    """All character stats"""
    hp: Stat = field(default_factory=lambda: Stat(100))
    mp: Stat = field(default_factory=lambda: Stat(50))
    attack: Stat = field(default_factory=lambda: Stat(10))
    defense: Stat = field(default_factory=lambda: Stat(5))
    speed: Stat = field(default_factory=lambda: Stat(10))
    critical: Stat = field(default_factory=lambda: Stat(10))  # 0-100
    evasion: Stat = field(default_factory=lambda: Stat(5))   # 0-100
    luck: Stat = field(default_factory=lambda: Stat(5))      # 0-100


@dataclass
class CharacterState:
    """Base state for any character (player or enemy)"""
    entity_id: str
    entity_type: EntityType
    name: str
    level: int = 1
    current_hp: int = 100
    current_mp: int = 50
    stats: Stats = field(default_factory=Stats)
    experience: int = 0
    experience_to_next: int = 100
    is_alive: bool = True
    
    def take_damage(self, amount: int) -> int:
        """Take damage, return actual damage taken"""
        actual = max(1, amount - self.stats.defense.value)
        self.current_hp = max(0, self.current_hp - actual)
        if self.current_hp <= 0:
            self.is_alive = False
        return actual
    
    def heal(self, amount: int) -> int:
        """Heal HP, return actual healed amount"""
        actual = min(amount, self.stats.hp.value - self.current_hp)
        self.current_hp += actual
        return actual
    
    def consume_mp(self, amount: int) -> bool:
        """Consume MP, return True if successful"""
        if self.current_mp >= amount:
            self.current_mp -= amount
            return True
        return False
    
    def gain_experience(self, amount: int) -> tuple:
        """Gain experience, return (did_level_up, new_level)"""
        self.experience += amount
        leveled_up = False
        
        while self.experience >= self.experience_to_next:
            self.experience -= self.experience_to_next
            self.experience_to_next = int(self.experience_to_next * 1.5)
            self.level += 1
            leveled_up = True
        
        return leveled_up, self.level


@dataclass
class PlayerState:
    """Player game state"""
    character: CharacterState = field(default_factory=lambda: CharacterState(
        entity_id="player",
        entity_type=EntityType.PLAYER,
        name="Developer"
    ))
    gold: int = 0
    inventory: List[Dict[str, Any]] = field(default_factory=list)
    equipped_weapon: Optional[Dict[str, Any]] = None
    equipped_armor: Optional[Dict[str, Any]] = None
    skills: List[str] = field(default_factory=list)  # Skill IDs
    achievements: List[str] = field(default_factory=list)


@dataclass
class EnemyState:
    """Enemy game state"""
    entity_id: str
    name: str
    enemy_type: str  # "feature", "bug", "merge", etc.
    commit_hash: str
    commit_message: str
    current_hp: int
    max_hp: int
    attack: int
    defense: int
    exp_reward: int
    gold_reward: int = 0
    drops: List[Dict[str, Any]] = field(default_factory=list)
    is_alive: bool = True
    is_boss: bool = False
    
    def take_damage(self, amount: int) -> int:
        """Take damage, return actual damage taken"""
        actual = max(1, amount - self.defense)
        self.current_hp = max(0, self.current_hp - actual)
        if self.current_hp <= 0:
            self.is_alive = False
        return actual


@dataclass
class ChapterState:
    """Chapter/game mode state"""
    chapter_id: str
    chapter_name: str
    chapter_index: int  # 0-based index
    enemies_in_chapter: int
    enemies_defeated: int = 0
    is_completed: bool = False
    gold_reward: int = 0
    exp_reward: int = 0


@dataclass
class GameState:
    """Complete game state"""
    # Metadata
    game_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    save_version: int = 2  # Current save format version
    game_version: str = "2.0.0"
    seed: Optional[int] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Repository info
    repo_path: str = ""
    repo_fingerprint: str = ""  # Hash of repo for identification
    
    # Player
    player: PlayerState = field(default_factory=PlayerState)
    
    # Chapter
    current_chapter: Optional[ChapterState] = None
    current_commit_index: int = 0
    total_commits: int = 0
    
    # Combat
    current_enemy: Optional[EnemyState] = None
    in_combat: bool = False
    
    # Progress
    enemies_defeated: List[str] = field(default_factory=list)  # List of commit hashes
    chapters_completed: List[str] = field(default_factory=list)
    is_game_over: bool = False
    is_victory: bool = False
    
    # Settings
    difficulty: str = "normal"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            "game_id": self.game_id,
            "save_version": self.save_version,
            "game_version": self.game_version,
            "seed": self.seed,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "repo_path": self.repo_path,
            "repo_fingerprint": self.repo_fingerprint,
            "player": {
                "character": {
                    "entity_id": self.player.character.entity_id,
                    "name": self.player.character.name,
                    "level": self.player.character.level,
                    "current_hp": self.player.character.current_hp,
                    "current_mp": self.player.character.current_mp,
                    "experience": self.player.character.experience,
                },
                "gold": self.player.gold,
                "inventory": self.player.inventory,
                "skills": self.player.skills,
            },
            "current_chapter": {
                "chapter_id": self.current_chapter.chapter_id if self.current_chapter else None,
                "chapter_name": self.current_chapter.chapter_name if self.current_chapter else None,
                "chapter_index": self.current_chapter.chapter_index if self.current_chapter else 0,
                "enemies_defeated": self.current_chapter.enemies_defeated if self.current_chapter else 0,
            } if self.current_chapter else None,
            "current_commit_index": self.current_commit_index,
            "total_commits": self.total_commits,
            "in_combat": self.in_combat,
            "enemies_defeated": len(self.enemies_defeated),
            "chapters_completed": self.chapters_completed,
            "is_game_over": self.is_game_over,
            "is_victory": self.is_victory,
            "difficulty": self.difficulty,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameState":
        """Deserialize from dict"""
        state = cls()
        state.game_id = data.get("game_id", state.game_id)
        state.save_version = data.get("save_version", state.save_version)
        state.repo_path = data.get("repo_path", "")
        return state


@dataclass
class Action:
    """Player action to be processed by the engine"""
    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action_type: str = ""  # "combat", "shop", "chapter", "ui"
    action_name: str = ""  # "attack", "defend", "buy", "continue"
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "action_name": self.action_name,
            "data": self.data,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Action":
        return cls(
            action_id=data.get("action_id", ""),
            action_type=data.get("action_type", ""),
            action_name=data.get("action_name", ""),
            data=data.get("data", {}),
            timestamp=data.get("timestamp", "")
        )
