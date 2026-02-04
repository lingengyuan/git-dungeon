"""
AI Text Generation Types

Defines the request/response types for AI text generation.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


class TextKind(Enum):
    """Categories of AI-generated flavor text."""
    ENEMY_INTRO = "enemy_intro"  # 敌人一句话描述
    BATTLE_START = "battle_start"  # 战斗开场旁白
    BATTLE_END = "battle_end"  # 战斗胜利/失败旁白
    EVENT_FLAVOR = "event_flavor"  # 事件场景氛围文案
    BOSS_PHASE = "boss_phase"  # Boss 过场台词


@dataclass
class TextRequest:
    """
    Request for AI text generation.
    
    Attributes:
        kind: Type of text to generate
        lang: Language code (e.g., 'en', 'zh_CN')
        seed: Random seed for reproducibility
        repo_id: Repository identifier (path or URL hash)
        commit_sha: Optional commit SHA for enemy context
        enemy_id: Optional enemy ID for enemy_intro
        event_id: Optional event ID for event_flavor
        extra_context: Additional context for prompt
    """
    kind: TextKind
    lang: str
    seed: int
    repo_id: str
    commit_sha: Optional[str] = None
    enemy_id: Optional[str] = None
    event_id: Optional[str] = None
    extra_context: Dict[str, Any] = field(default_factory=dict)
    
    def cache_key_parts(self) -> Dict[str, Any]:
        """Return dict parts relevant for cache key."""
        return {
            "kind": self.kind.value,
            "lang": self.lang,
            "seed": self.seed,
            "repo_id": self.repo_id,
            "commit_sha": self.commit_sha,
            "enemy_id": self.enemy_id,
            "event_id": self.event_id,
        }


@dataclass
class TextResponse:
    """
    Response from AI text generation.
    
    Attributes:
        text: Generated text content
        provider: Provider identifier (e.g., 'openai', 'mock', 'fallback')
        cached: Whether this was from cache
        meta: Additional metadata (e.g., trimmed, fallback_reason)
    """
    text: str
    provider: str
    cached: bool = False
    meta: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def trimmed(self) -> bool:
        """Check if text was trimmed due to length limits."""
        return self.meta.get("trimmed", False)
    
    @property 
    def fallback_used(self) -> bool:
        """Check if fallback was used."""
        return self.provider == "fallback"
