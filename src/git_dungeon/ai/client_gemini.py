"""
Gemini Client

Google Gemini-powered text generation for M6.
"""

import os
import time
from collections import deque
from typing import Deque, List, Optional, Dict, Any
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
        # Free-tier safe defaults: keep below common 10 req/min limit.
        self.max_requests_per_minute = max(1, int(os.environ.get("GEMINI_MAX_RPM", "8")))
        self.rate_limit_cooldown_seconds = max(5, int(os.environ.get("GEMINI_RATE_LIMIT_COOLDOWN", "60")))
        self._request_timestamps: Deque[float] = deque()
        self._rate_limited_until = 0.0
        self._rate_limit_notice_until = 0.0
        
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
            return self._fallback_to_mock(requests, reason="missing_api_key")
        
        requests = requests[:self.batch_size]
        results = []
        for idx, req in enumerate(requests):
            if self._is_in_cooldown():
                results.extend(
                    self._fallback_to_mock(
                        requests[idx:],
                        reason="rate_limited_cooldown",
                    )
                )
                break
            if not self._reserve_request_slot():
                self._mark_rate_limited("local_rpm_budget")
                results.extend(
                    self._fallback_to_mock(
                        requests[idx:],
                        reason="local_rpm_budget",
                    )
                )
                break
            try:
                results.append(self._generate_one(req))
            except Exception as e:
                if self._is_rate_limit_error(e):
                    self._mark_rate_limited(str(e))
                    results.extend(
                        self._fallback_to_mock(
                            requests[idx:],
                            reason="http_429",
                            error=str(e),
                        )
                    )
                    break
                print(f"[AI] Gemini generation error: {e}")
                results.append(
                    TextResponse(
                        text="",
                        provider=self.name,
                        cached=False,
                        meta={"error": str(e), "fallback": True},
                    )
                )
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
            except Exception:
                if attempt < self.max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))
                else:
                    raise

        return TextResponse(
            text="",
            provider=self.name,
            cached=False,
            meta={"reason": "retry_exhausted"},
        )
    
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
    
    def _is_rate_limit_error(self, err: Exception) -> bool:
        text = str(err).lower()
        return "429" in text or "too many requests" in text or "rate limit" in text

    def _is_in_cooldown(self) -> bool:
        return time.time() < self._rate_limited_until

    def _mark_rate_limited(self, reason: str) -> None:
        now = time.time()
        self._rate_limited_until = max(
            self._rate_limited_until,
            now + self.rate_limit_cooldown_seconds,
        )
        if now >= self._rate_limit_notice_until:
            wait_s = int(max(1, self._rate_limited_until - now))
            print(f"[AI] Gemini rate limit: {reason}. Falling back to mock for ~{wait_s}s")
            self._rate_limit_notice_until = self._rate_limited_until

    def _reserve_request_slot(self) -> bool:
        """Local RPM guard to avoid hammering free-tier quotas."""
        now = time.time()
        window_start = now - 60
        while self._request_timestamps and self._request_timestamps[0] < window_start:
            self._request_timestamps.popleft()
        if len(self._request_timestamps) >= self.max_requests_per_minute:
            return False
        self._request_timestamps.append(now)
        return True

    def _fallback_to_mock(
        self,
        requests: List[TextRequest],
        reason: str = "fallback",
        error: Optional[str] = None,
    ) -> List[TextResponse]:
        """Fallback to mock responses while preserving request kind/context."""
        from .client_mock import MockAIClient

        mock = MockAIClient()
        responses = mock.generate_batch(requests)
        for r in responses:
            r.provider = "gemini/fallback"
            r.meta["fallback"] = True
            r.meta["reason"] = reason
            if error:
                r.meta["error"] = error
        return responses
