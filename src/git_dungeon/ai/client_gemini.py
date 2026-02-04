"""
Gemini Client

Google Gemini-powered text generation for M6.
"""

import os
import time
from typing import List, Optional, Dict, Any
from .types import TextRequest, TextResponse, TextKind
from .client_base import AIClient
from .prompts import get_prompt, get_system_prompt
from .sanitize import sanitize_text


class GeminiAIClient(AIClient):
    """
    Gemini-powered text generation client.
    
    Requires GEMINI_API_KEY environment variable.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash",
        timeout: int = 10,
        max_retries: int = 2,
        batch_size: int = 10
    ):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            model: Model to use
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            batch_size: Maximum batch size
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.batch_size = batch_size
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        
        # Available models for Gemini Free tier
        self.available_models = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-flash",
        ]
    
    @property
    def name(self) -> str:
        return f"gemini/{self.model}"
    
    def generate_batch(self, requests: List[TextRequest]) -> List[TextResponse]:
        """Generate text for a batch of requests."""
        if not self.api_key:
            return self._fallback_to_mock(len(requests))
        
        requests = requests[:self.batch_size]
        results = []
        for req in requests:
            try:
                results.append(self._generate_one(req))
            except Exception as e:
                print(f"[AI] Gemini generation error: {e}")
                results.append(TextResponse(
                    text="",
                    provider=self.name,
                    cached=False,
                    meta={"error": str(e), "fallback": True}
                ))
        return results
    
    def health_check(self) -> bool:
        """Check if Gemini API is available."""
        if not self.api_key:
            return False
        
        try:
            url = f"{self.base_url}/models?key={self.api_key}"
            import urllib.request
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False
    
    def _generate_one(self, request: TextRequest) -> TextResponse:
        """Generate text for a single request."""
        prompt_vars = self._build_prompt_vars(request)
        prompt = get_prompt(request.kind, request.lang, **prompt_vars)
        system_prompt = get_system_prompt(request.lang)
        
        # Combine system + user prompt
        full_prompt = f"{system_prompt}\n\n{prompt}"
        
        for attempt in range(self.max_retries):
            try:
                response = self._call_api(full_prompt)
                if response:
                    text, meta = sanitize_text(response, request.kind)
                    if text:
                        return TextResponse(
                            text=text,
                            provider=self.name,
                            cached=False,
                            meta=meta
                        )
                return TextResponse(
                    text="",
                    provider=self.name,
                    cached=False,
                    meta={"reason": "sanitization_failed"}
                )
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))
                else:
                    raise
    
    def _call_api(self, prompt: str) -> Optional[str]:
        """Call Gemini API."""
        import urllib.request
        import json
        
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}],
                "role": "user"
            }],
            "generationConfig": {
                "maxOutputTokens": 100,
                "temperature": 0.7,
            }
        }
        
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            if resp.status == 200:
                result = json.loads(resp.read().decode("utf-8"))
                if "candidates" in result:
                    return result["candidates"][0]["content"]["parts"][0]["text"]
        
        return None
    
    def _build_prompt_vars(self, request: TextRequest) -> Dict[str, Any]:
        """Build prompt variables from request."""
        vars = {
            "repo_id": request.repo_id,
            "seed": request.seed,
            "lang": request.lang,
        }
        
        if request.kind == TextKind.ENEMY_INTRO:
            vars.update({
                "commit_type": request.extra_context.get("commit_type", "commit"),
                "commit_sha": request.commit_sha or "unknown",
                "enemy_id": request.enemy_id or "unknown",
                "tone": "neutral",
            })
        elif request.kind == TextKind.BATTLE_START:
            vars.update({
                "player_class": request.extra_context.get("player_class", "Developer"),
                "commit_type": request.extra_context.get("commit_type", "enemy"),
                "tier": request.extra_context.get("tier", "normal"),
                "player_hp": "unknown",
                "enemy_hp": "unknown",
                "tone": "neutral",
            })
        elif request.kind == TextKind.BATTLE_END:
            vars.update({
                "result": "victory" if request.extra_context.get("victory") else "defeat",
                "victory": "yes" if request.extra_context.get("victory") else "no",
                "commit_type": request.extra_context.get("commit_type", "enemy"),
                "loot": request.extra_context.get("loot", "nothing"),
                "tone": "neutral",
            })
        elif request.kind == TextKind.EVENT_FLAVOR:
            vars.update({
                "event_location": request.extra_context.get("event_type", "unknown"),
                "event_type": request.extra_context.get("event_type", "mystery"),
                "event_tags": ", ".join(request.extra_context.get("event_tags", [])),
                "tone": "neutral",
            })
        elif request.kind == TextKind.BOSS_PHASE:
            vars.update({
                "boss_name": request.extra_context.get("boss_name", "Boss"),
                "phase": str(request.extra_context.get("phase", "2")),
                "prev_ability": request.extra_context.get("prev_ability", "unknown"),
                "tone": "neutral",
            })
        
        return vars
    
    def _fallback_to_mock(self, count: int) -> List[TextResponse]:
        """Fallback to mock responses when Gemini is unavailable."""
        from .client_mock import MockAIClient
        mock = MockAIClient()
        responses = mock.generate_batch([
            TextRequest(kind=TextKind.ENEMY_INTRO, lang="en", seed=0, repo_id="fallback")
        ] * count)
        for r in responses:
            r.provider = "gemini/fallback"
            r.meta["fallback"] = True
        return responses
