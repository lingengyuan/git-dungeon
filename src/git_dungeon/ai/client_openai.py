"""
OpenAI Client

OpenAI-powered text generation (skeleton for future implementation).
"""

import os
import time
from typing import List, Optional, Dict, Any
from .types import TextRequest, TextResponse, TextKind
from .client_base import AIClient
from .prompts import get_prompt, get_system_prompt
from .sanitize import sanitize_text


class OpenAIClient(AIClient):
    """
    OpenAI-powered text generation client.
    
    Requires OPENAI_API_KEY environment variable.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        timeout: int = 5,
        max_retries: int = 2,
        batch_size: int = 10
    ):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            batch_size: Maximum batch size for generate_batch
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.batch_size = batch_size
        
        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key) if self.api_key else None
        except ImportError:
            self.client = None
            print("[AI] Warning: openai package not installed")
    
    @property
    def name(self) -> str:
        return f"openai/{self.model}"
    
    def generate_batch(self, requests: List[TextRequest]) -> List[TextResponse]:
        """Generate text for a batch of requests."""
        if not self.client:
            return self._fallback_to_mock(len(requests))
        
        requests = requests[:self.batch_size]
        results = []
        for req in requests:
            try:
                results.append(self._generate_one(req))
            except Exception as e:
                print(f"[AI] OpenAI generation error: {e}")
                results.append(TextResponse(text="", provider="openai", cached=False, meta={"error": str(e), "fallback": True}))
        return results
    
    def health_check(self) -> bool:
        """Check if OpenAI is available."""
        if not self.client or not self.api_key:
            return False
        try:
            self.client.models.list()
            return True
        except Exception:
            return False
    
    def _generate_one(self, request: TextRequest) -> TextResponse:
        """Generate text for a single request."""
        prompt_vars = self._build_prompt_vars(request)
        prompt = get_prompt(request.kind, request.lang, **prompt_vars)
        system_prompt = get_system_prompt(request.lang)
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=100,
                    temperature=0.7,
                    timeout=self.timeout,
                )
                text = response.choices[0].message.content
                text, meta = sanitize_text(text, request.kind)
                
                if text:
                    return TextResponse(text=text, provider=self.name, cached=False, meta=meta)
                return TextResponse(text="", provider=self.name, cached=False, meta={"reason": "sanitization_failed"})
            except Exception:
                if attempt < self.max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))

        return TextResponse(
            text="",
            provider=self.name,
            cached=False,
            meta={"reason": "retry_exhausted"},
        )
    
    def _build_prompt_vars(self, request: TextRequest) -> Dict[str, Any]:
        """Build prompt variables from request."""
        vars = {"repo_id": request.repo_id, "seed": request.seed}
        
        if request.kind == TextKind.ENEMY_INTRO:
            vars.update({"commit_type": request.extra_context.get("commit_type", "commit"), "commit_sha": request.commit_sha or "unknown", "enemy_id": request.enemy_id or "unknown", "tone": "neutral"})
        elif request.kind == TextKind.BATTLE_START:
            vars.update({"player_class": request.extra_context.get("player_class", "Developer"), "commit_type": request.extra_context.get("commit_type", "enemy"), "tier": request.extra_context.get("tier", "normal"), "player_hp": "unknown", "enemy_hp": "unknown", "tone": "neutral"})
        elif request.kind == TextKind.BATTLE_END:
            vars.update({"result": "victory" if request.extra_context.get("victory") else "defeat", "victory": "yes" if request.extra_context.get("victory") else "no", "commit_type": request.extra_context.get("commit_type", "enemy"), "loot": request.extra_context.get("loot", "nothing"), "tone": "neutral"})
        elif request.kind == TextKind.EVENT_FLAVOR:
            vars.update({"event_location": request.extra_context.get("event_type", "unknown"), "event_type": request.extra_context.get("event_type", "mystery"), "event_tags": ", ".join(request.extra_context.get("event_tags", [])), "tone": "neutral"})
        elif request.kind == TextKind.BOSS_PHASE:
            vars.update({"boss_name": request.extra_context.get("boss_name", "Boss"), "phase": str(request.extra_context.get("phase", "2")), "prev_ability": request.extra_context.get("prev_ability", "unknown"), "tone": "neutral"})
        
        return vars
    
    def _fallback_to_mock(self, count: int) -> List[TextResponse]:
        """Fallback to mock responses when OpenAI is unavailable."""
        from .client_mock import MockAIClient
        mock = MockAIClient()
        responses = mock.generate_batch([
            TextRequest(kind=TextKind.ENEMY_INTRO, lang="en", seed=0, repo_id="fallback")
        ] * count)
        for r in responses:
            r.provider = "openai/fallback"
            r.meta["fallback"] = True
        return responses
