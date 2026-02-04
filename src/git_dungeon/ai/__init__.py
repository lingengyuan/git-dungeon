"""
Git Dungeon AI Text Generation Module

Provides flavor text generation for enemies, battles, events, and boss phases.
"""

from .types import TextKind, TextRequest, TextResponse
from .client_base import AIClient
from .client_null import NullAIClient
from .client_mock import MockAIClient
from .cache import TextCache

__all__ = [
    "TextKind",
    "TextRequest", 
    "TextResponse",
    "AIClient",
    "NullAIClient", 
    "MockAIClient",
    "TextCache",
]
