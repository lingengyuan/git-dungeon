"""
Null AI Client

Always returns empty responses. Used when AI is disabled (--ai=off).
"""

from typing import List
from .types import TextRequest, TextResponse
from .client_base import AIClient


class NullAIClient(AIClient):
    """
    Null client that always returns empty responses.
    
    Used when AI text generation is disabled via --ai=off.
    """
    
    @property
    def name(self) -> str:
        return "null"
    
    def generate_batch(self, requests: List[TextRequest]) -> List[TextResponse]:
        """Return empty responses for all requests."""
        return [
            TextResponse(
                text="",
                provider="null",
                cached=False,
                meta={"reason": "ai_disabled"}
            )
            for _ in requests
        ]
    
    def health_check(self) -> bool:
        """Null client is always 'healthy' but never generates."""
        return True
