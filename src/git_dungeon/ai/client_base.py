"""
AI Client Base Protocol

Defines the interface for AI text generation providers.
"""

from typing import Protocol, List
from .types import TextRequest, TextResponse


class AIClient(Protocol):
    """
    Protocol for AI text generation clients.
    
    All AI providers (OpenAI, mock, fallback) must implement this interface.
    """
    
    def generate_batch(self, requests: List[TextRequest]) -> List[TextResponse]:
        """
        Generate text for a batch of requests.
        
        Args:
            requests: List of text generation requests
            
        Returns:
            List of text responses (order matches input)
        """
        ...
    
    @property
    def name(self) -> str:
        """Provider name identifier."""
        ...
    
    def health_check(self) -> bool:
        """
        Check if the provider is available.
        
        Returns:
            True if provider can generate text
        """
        ...
