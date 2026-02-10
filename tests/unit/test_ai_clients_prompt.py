"""Regression tests for AI prompt variable wiring."""

from types import SimpleNamespace

from git_dungeon.ai import TextKind, TextRequest, TextResponse
from git_dungeon.ai.client_copilot import CopilotAIClient
from git_dungeon.ai.client_gemini import GeminiAIClient
from git_dungeon.ai.client_openai import OpenAIClient


def _battle_start_request() -> TextRequest:
    return TextRequest(
        kind=TextKind.BATTLE_START,
        lang="en",
        seed=123,
        repo_id="repo-test",
        extra_context={"commit_type": "feat", "tier": "normal"},
    )


def test_gemini_prompt_vars_exclude_lang():
    client = GeminiAIClient(api_key="dummy-key")
    vars = client._build_prompt_vars(_battle_start_request())
    assert "lang" not in vars


def test_openai_prompt_vars_exclude_lang():
    client = OpenAIClient(api_key="dummy-key")
    vars = client._build_prompt_vars(_battle_start_request())
    assert "lang" not in vars


def test_copilot_prompt_vars_exclude_lang():
    client = CopilotAIClient(api_key="dummy-key")
    vars = client._build_prompt_vars(_battle_start_request())
    assert "lang" not in vars


def test_gemini_generate_one_no_lang_conflict(monkeypatch):
    client = GeminiAIClient(api_key="dummy-key")
    monkeypatch.setattr(client, "_call_api", lambda _prompt: "The battle begins.")

    response = client._generate_one(_battle_start_request())

    assert response.text != ""
    assert response.provider.startswith("gemini/")


def test_openai_generate_one_no_lang_conflict():
    client = OpenAIClient(api_key="dummy-key")
    client.client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **_kwargs: SimpleNamespace(
                    choices=[SimpleNamespace(message=SimpleNamespace(content="The battle begins."))]
                )
            )
        )
    )

    response = client._generate_one(_battle_start_request())

    assert response.text != ""
    assert response.provider.startswith("openai/")


def test_copilot_generate_one_no_lang_conflict(monkeypatch):
    client = CopilotAIClient(api_key="dummy-key")
    monkeypatch.setattr(client, "_call_api", lambda _messages: "The battle begins.")

    response = client._generate_one(_battle_start_request())

    assert response.text != ""
    assert response.provider.startswith("copilot/")


def test_gemini_429_enters_cooldown_and_fallbacks(monkeypatch):
    client = GeminiAIClient(api_key="dummy-key")
    request = _battle_start_request()

    # First call hits 429 and should switch to fallback for the whole batch.
    monkeypatch.setattr(
        client,
        "_generate_one",
        lambda _req: (_ for _ in ()).throw(Exception("HTTP Error 429: Too Many Requests")),
    )
    responses = client.generate_batch([request])
    assert len(responses) == 1
    assert responses[0].provider == "gemini/fallback"
    assert responses[0].meta.get("reason") == "http_429"
    assert responses[0].text != ""

    # During cooldown, client should not call _generate_one again.
    call_count = {"n": 0}

    def _should_not_call(_req):
        call_count["n"] += 1
        return TextResponse(text="unexpected", provider=client.name)

    monkeypatch.setattr(client, "_generate_one", _should_not_call)
    cooldown_responses = client.generate_batch([request])
    assert cooldown_responses[0].provider == "gemini/fallback"
    assert cooldown_responses[0].meta.get("reason") == "rate_limited_cooldown"
    assert call_count["n"] == 0


def test_gemini_local_rpm_budget_fallback(monkeypatch):
    client = GeminiAIClient(api_key="dummy-key")
    client.max_requests_per_minute = 1
    request = _battle_start_request()

    monkeypatch.setattr(
        client,
        "_generate_one",
        lambda _req: TextResponse(text="ok", provider=client.name),
    )
    responses = client.generate_batch([request, request])
    assert len(responses) == 2
    assert responses[0].text == "ok"
    assert responses[1].provider == "gemini/fallback"
    assert responses[1].meta.get("reason") in {"local_rpm_budget", "rate_limited_cooldown"}
