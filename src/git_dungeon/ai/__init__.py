"""
Git Dungeon AI Text Generation Module

Provides flavor text generation for enemies, battles, events, and boss phases.
Supports: null, mock, gemini (free tier), openai, copilot (GitHub Models)
"""

from .types import TextKind, TextRequest, TextResponse
from .client_base import AIClient
from .client_null import NullAIClient
from .client_mock import MockAIClient
from .client_gemini import GeminiAIClient
from .client_copilot import CopilotAIClient
from .cache import TextCache

__all__ = [
    "TextKind",
    "TextRequest", 
    "TextResponse",
    "AIClient",
    "NullAIClient", 
    "MockAIClient",
    "GeminiAIClient",
    "CopilotAIClient",
    "TextCache",
]
