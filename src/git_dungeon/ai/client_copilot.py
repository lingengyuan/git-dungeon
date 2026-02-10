"""
Copilot/GitHub Models Client

Uses GitHub Models chat completions endpoint for AI text generation.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from .client_base import AIClient
from .prompts import get_prompt, get_system_prompt
from .sanitize import sanitize_text
from .types import TextKind, TextRequest, TextResponse


class CopilotAIClient(AIClient):
    """
    GitHub Copilot/GitHub Models powered text generation client.

    Auth:
    - `GITHUB_TOKEN` (recommended)
    - `GH_TOKEN` or `GITHUB_MODELS_TOKEN` (fallback)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "openai/gpt-4.1-mini",
        timeout: int = 8,
        max_retries: int = 2,
        batch_size: int = 10,
    ) -> None:
        self.api_key = (
            api_key
            or os.environ.get("GITHUB_TOKEN")
            or os.environ.get("GH_TOKEN")
            or os.environ.get("GITHUB_MODELS_TOKEN")
        )
        self.model = os.environ.get("GITHUB_MODELS_MODEL", model)
        self.timeout = timeout
        self.max_retries = max_retries
        self.batch_size = batch_size
        self.base_url = os.environ.get(
            "GITHUB_MODELS_ENDPOINT",
            "https://models.github.ai/inference/chat/completions",
        )

    @property
    def name(self) -> str:
        return f"copilot/{self.model}"

    def generate_batch(self, requests: List[TextRequest]) -> List[TextResponse]:
        """Generate text for a batch of requests."""
        if not self.api_key:
            return self._fallback_to_mock(requests, reason="missing_token")

        requests = requests[: self.batch_size]
        results: List[TextResponse] = []
        for req in requests:
            try:
                results.append(self._generate_one(req))
            except Exception as err:
                if self._is_rate_limit_error(err):
                    results.append(
                        TextResponse(
                            text="",
                            provider=self.name,
                            cached=False,
                            meta={"fallback": True, "reason": "http_429", "error": str(err)},
                        )
                    )
                    continue
                results.append(
                    TextResponse(
                        text="",
                        provider=self.name,
                        cached=False,
                        meta={"fallback": True, "error": str(err)},
                    )
                )
        return results

    def health_check(self) -> bool:
        """A lightweight local check to avoid network dependency."""
        return bool(self.api_key)

    def _generate_one(self, request: TextRequest) -> TextResponse:
        prompt_vars = self._build_prompt_vars(request)
        prompt = get_prompt(request.kind, request.lang, **prompt_vars)
        system_prompt = get_system_prompt(request.lang)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        for attempt in range(self.max_retries):
            try:
                text = self._call_api(messages)
                text, meta = sanitize_text(text, request.kind)
                if text:
                    return TextResponse(text=text, provider=self.name, cached=False, meta=meta)
                return TextResponse(
                    text="",
                    provider=self.name,
                    cached=False,
                    meta={"reason": "sanitization_failed"},
                )
            except Exception:
                if attempt < self.max_retries - 1:
                    time.sleep(0.4 * (attempt + 1))
                else:
                    raise

        return TextResponse(
            text="",
            provider=self.name,
            cached=False,
            meta={"reason": "retry_exhausted"},
        )

    def _call_api(self, messages: List[Dict[str, str]]) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 100,
            "temperature": 0.7,
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.base_url,
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status}")
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            detail = ""
            try:
                detail = err.read().decode("utf-8")
            except Exception:
                pass
            raise RuntimeError(f"HTTP {err.code}: {detail}") from err

        return self._extract_content(body)

    def _extract_content(self, body: Dict[str, Any]) -> str:
        choices = body.get("choices", [])
        if not choices:
            return ""
        message = choices[0].get("message", {})
        content = message.get("content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: List[str] = []
            for item in content:
                if isinstance(item, dict):
                    txt = item.get("text")
                    if isinstance(txt, str):
                        parts.append(txt)
            return " ".join(parts).strip()
        return ""

    def _is_rate_limit_error(self, err: Exception) -> bool:
        text = str(err).lower()
        return "429" in text or "too many requests" in text or "rate limit" in text

    def _build_prompt_vars(self, request: TextRequest) -> Dict[str, Any]:
        vars: Dict[str, Any] = {"repo_id": request.repo_id, "seed": request.seed}

        if request.kind == TextKind.ENEMY_INTRO:
            vars.update(
                {
                    "commit_type": request.extra_context.get("commit_type", "commit"),
                    "commit_sha": request.commit_sha or "unknown",
                    "enemy_id": request.enemy_id or "unknown",
                    "tone": "neutral",
                }
            )
        elif request.kind == TextKind.BATTLE_START:
            vars.update(
                {
                    "player_class": request.extra_context.get("player_class", "Developer"),
                    "commit_type": request.extra_context.get("commit_type", "enemy"),
                    "tier": request.extra_context.get("tier", "normal"),
                    "player_hp": "unknown",
                    "enemy_hp": "unknown",
                    "tone": "neutral",
                }
            )
        elif request.kind == TextKind.BATTLE_END:
            vars.update(
                {
                    "result": "victory" if request.extra_context.get("victory") else "defeat",
                    "victory": "yes" if request.extra_context.get("victory") else "no",
                    "commit_type": request.extra_context.get("commit_type", "enemy"),
                    "loot": request.extra_context.get("loot", "nothing"),
                    "tone": "neutral",
                }
            )
        elif request.kind == TextKind.EVENT_FLAVOR:
            vars.update(
                {
                    "event_location": request.extra_context.get("event_type", "unknown"),
                    "event_type": request.extra_context.get("event_type", "mystery"),
                    "event_tags": ", ".join(request.extra_context.get("event_tags", [])),
                    "tone": "neutral",
                }
            )
        elif request.kind == TextKind.BOSS_PHASE:
            vars.update(
                {
                    "boss_name": request.extra_context.get("boss_name", "Boss"),
                    "phase": str(request.extra_context.get("phase", "2")),
                    "prev_ability": request.extra_context.get("prev_ability", "unknown"),
                    "tone": "neutral",
                }
            )

        return vars

    def _fallback_to_mock(
        self,
        requests: List[TextRequest],
        reason: str = "fallback",
    ) -> List[TextResponse]:
        from .client_mock import MockAIClient

        mock = MockAIClient()
        responses = mock.generate_batch(requests)
        for response in responses:
            response.provider = "copilot/fallback"
            response.meta["fallback"] = True
            response.meta["reason"] = reason
        return responses
