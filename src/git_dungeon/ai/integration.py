"""
M6 AI Integration - CLI Parameters and Engine Integration

Adds --ai parameters to CLI and integrates AI text generation into game flow.
"""

import argparse
from typing import Optional
from git_dungeon.ai import (
    TextKind, TextRequest, TextResponse,
    NullAIClient, MockAIClient, GeminiAIClient,
    TextCache
)
from git_dungeon.i18n import normalize_lang


def add_ai_args(parser: argparse.ArgumentParser) -> None:
    """Add AI-related CLI arguments."""
    ai_group = parser.add_argument_group("AI Text Generation (M6)")
    
    ai_group.add_argument(
        "--ai", "-a",
        choices=["on", "off"],
        default="off",
        help="Enable AI text generation (default: off)"
    )
    ai_group.add_argument(
        "--ai-provider",
        choices=["mock", "gemini", "openai"],
        default="mock",
        help="AI provider (default: mock)"
    )
    ai_group.add_argument(
        "--ai-cache",
        type=str,
        default=".git_dungeon_cache",
        help="AI cache directory (default: .git_dungeon_cache)"
    )
    ai_group.add_argument(
        "--ai-timeout",
        type=int,
        default=5,
        help="AI API timeout in seconds (default: 5)"
    )
    ai_group.add_argument(
        "--ai-prefetch",
        choices=["chapter", "run", "off"],
        default="chapter",
        help="AI text prefetch strategy (default: chapter)"
    )


def create_ai_client(
    provider: str,
    api_key: Optional[str] = None,
    timeout: int = 5
):
    """
    Create AI client based on provider.
    
    Args:
        provider: Provider name (mock/gemini/openai)
        api_key: API key (reads from env if not provided)
        timeout: Request timeout
        
    Returns:
        AIClient instance
    """
    if provider == "null" or provider == "off":
        return NullAIClient()
    
    elif provider == "mock":
        return MockAIClient()
    
    elif provider == "gemini":
        # API key from environment variable
        actual_key = None
        
        # Try environment variable
        import os
        env_key = os.environ.get("GEMINI_API_KEY")
        if env_key:
            actual_key = env_key
        elif api_key:
            actual_key = api_key
        
        return GeminiAIClient(api_key=actual_key, timeout=timeout)
    
    elif provider == "openai":
        import os
        openai_key = api_key or os.environ.get("OPENAI_API_KEY")
        
        try:
            from git_dungeon.ai.client_openai import OpenAIClient
            return OpenAIClient(api_key=openai_key, timeout=timeout)
        except ImportError:
            print("[AI] Warning: openai package not installed, falling back to mock")
            return MockAIClient()
    
    else:
        print(f"[AI] Unknown provider: {provider}, using mock")
        return MockAIClient()


def get_ai_text(
    client,
    cache: TextCache,
    kind: TextKind,
    lang: str,
    seed: int,
    repo_id: str,
    extra_context: dict = None,
    content_version: str = "1.0"
) -> str:
    """
    Get AI-generated text with caching and fallback.
    
    Args:
        client: AIClient instance
        cache: TextCache instance
        kind: Type of text to generate
        lang: Language code
        seed: Random seed
        repo_id: Repository identifier
        extra_context: Additional context for prompt
        content_version: Content version for cache key
        
    Returns:
        Generated text (or empty string if AI disabled)
    """
    from git_dungeon.ai.fallbacks import get_fallback_text
    lang = normalize_lang(lang)
    
    # Check if AI is disabled
    if isinstance(client, NullAIClient):
        return ""
    
    # Build request
    request = TextRequest(
        kind=kind,
        lang=lang,
        seed=seed,
        repo_id=repo_id,
        extra_context=extra_context or {}
    )
    
    # Check cache first
    cache_key = cache.build_cache_key(
        provider=client.name,
        request=request,
        content_version=content_version
    )
    cached = cache.get(cache_key)
    
    if cached and cached.text:
        return cached.text
    
    # Generate new text
    responses = client.generate_batch([request])
    
    if responses and responses[0].text:
        text = responses[0].text
        # Cache the result
        cache.set(cache_key, responses[0])
        return text
    
    # Fallback to template
    fallback_text = get_fallback_text(request)
    cache.set(
        cache_key,
        TextResponse(
            text=fallback_text,
            provider=f"{client.name}/fallback",
            cached=False,
            meta={"fallback": True, "reason": "provider_empty"},
        ),
    )
    return fallback_text


class AIAggregator:
    """
    Aggregates AI text generation requests for batch processing.
    Useful for prefetch strategies.
    """
    
    def __init__(self, client, cache, lang, seed, repo_id, content_version="1.0"):
        self.client = client
        self.cache = cache
        self.lang = normalize_lang(lang)
        self.seed = seed
        self.repo_id = repo_id
        self.content_version = content_version
        self.requests = []
        self.results = {}
    
    def add_request(self, kind: TextKind, key: str, extra_context: dict = None):
        """Add a text generation request."""
        request = TextRequest(
            kind=kind,
            lang=self.lang,
            seed=self.seed,
            repo_id=self.repo_id,
            extra_context=extra_context or {}
        )
        self.requests.append((key, request))
    
    def prefetch(self) -> dict:
        """
        Prefetch all pending requests.
        
        Returns:
            Dict mapping keys to generated text
        """
        if not self.requests or isinstance(self.client, NullAIClient):
            return {}
        
        # Build batch request
        text_requests = [req for _, req in self.requests]
        
        # Generate batch
        responses = self.client.generate_batch(text_requests)
        
        # Process results
        results = {}
        for (key, request), response in zip(self.requests, responses):
            text = response.text
            
            # Fallback if empty
            if not text:
                from git_dungeon.ai.fallbacks import get_fallback_text
                text = get_fallback_text(request)
                response = TextResponse(
                    text=text,
                    provider=f"{self.client.name}/fallback",
                    cached=False,
                    meta={"fallback": True, "reason": "provider_empty"},
                )
            
            # Cache both provider and fallback responses to reduce repeated calls.
            cache_key = self.cache.build_cache_key(
                provider=self.client.name,
                request=request,
                content_version=self.content_version
            )
            self.cache.set(cache_key, response)
            
            results[key] = text
        
        self.requests = []  # Clear after prefetch
        return results
    
    def get(self, kind: TextKind, key: str, extra_context: dict = None) -> str:
        """
        Get text for a single request (on-demand).
        
        Returns:
            Generated text
        """
        # Check cache first
        request = TextRequest(
            kind=kind,
            lang=self.lang,
            seed=self.seed,
            repo_id=self.repo_id,
            extra_context=extra_context or {}
        )
        
        cache_key = self.cache.build_cache_key(
            provider=self.client.name,
            request=request,
            content_version=self.content_version
        )
        
        cached = self.cache.get(cache_key)
        if cached and cached.text:
            return cached.text
        
        # Generate on-demand
        responses = self.client.generate_batch([request])
        
        if responses and responses[0].text:
            text = responses[0].text
            self.cache.set(cache_key, responses[0])
            return text
        
        # Fallback
        from git_dungeon.ai.fallbacks import get_fallback_text
        fallback_text = get_fallback_text(request)
        self.cache.set(
            cache_key,
            TextResponse(
                text=fallback_text,
                provider=f"{self.client.name}/fallback",
                cached=False,
                meta={"fallback": True, "reason": "provider_empty"},
            ),
        )
        return fallback_text
