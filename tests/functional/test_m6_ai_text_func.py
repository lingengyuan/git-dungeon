"""
M6 AI Text Generation - Functional Tests

Tests for AI text generation module (M6).
Covers: null client, mock client, cache, sanitization, fallbacks.
"""

import pytest
import tempfile

from git_dungeon.ai import (
    TextKind, TextRequest, TextResponse,
    NullAIClient, MockAIClient, TextCache
)
from git_dungeon.ai.fallbacks import get_fallback_text
from git_dungeon.ai.sanitize import sanitize_text


class TestNullAIClient:
    """Test null AI client (--ai=off)."""
    
    def test_generate_batch_returns_empty(self):
        """Null client should return empty responses."""
        client = NullAIClient()
        requests = [
            TextRequest(kind=TextKind.ENEMY_INTRO, lang="en", seed=123, repo_id="test"),
            TextRequest(kind=TextKind.BATTLE_START, lang="zh_CN", seed=456, repo_id="test"),
        ]
        responses = client.generate_batch(requests)
        
        assert len(responses) == 2
        assert all(r.text == "" for r in responses)
        assert all(r.provider == "null" for r in responses)
        assert all(r.meta.get("reason") == "ai_disabled" for r in responses)
    
    def test_health_check_always_true(self):
        """Null client should always report healthy."""
        client = NullAIClient()
        assert client.health_check() is True


class TestMockAIClient:
    """Test mock AI client for deterministic testing."""
    
    def test_generate_batch_returns_text(self):
        """Mock client should generate pseudo-text."""
        client = MockAIClient()
        requests = [
            TextRequest(kind=TextKind.ENEMY_INTRO, lang="en", seed=123, repo_id="test"),
        ]
        responses = client.generate_batch(requests)
        
        assert len(responses) == 1
        assert responses[0].text != ""
        assert responses[0].provider == "mock"
        assert responses[0].cached is False
    
    def test_deterministic_same_seed(self):
        """Same seed should produce same text."""
        client = MockAIClient()
        
        requests = [
            TextRequest(kind=TextKind.ENEMY_INTRO, lang="en", seed=999, repo_id="test"),
        ]
        
        responses1 = client.generate_batch(requests)
        responses2 = client.generate_batch(requests)
        
        assert responses1[0].text == responses2[0].text
    
    def test_different_seed_different_text(self):
        """Different seeds should produce different text."""
        client = MockAIClient()
        
        req1 = TextRequest(kind=TextKind.ENEMY_INTRO, lang="en", seed=100, repo_id="test")
        req2 = TextRequest(kind=TextKind.ENEMY_INTRO, lang="en", seed=200, repo_id="test")
        
        responses = client.generate_batch([req1, req2])
        
        assert responses[0].text != responses[1].text

    def test_different_context_different_text(self):
        """Different extra_context should produce different text."""
        client = MockAIClient()

        req1 = TextRequest(
            kind=TextKind.BATTLE_START,
            lang="en",
            seed=100,
            repo_id="test",
            extra_context={"commit_type": "fix", "tier": "normal"},
        )
        req2 = TextRequest(
            kind=TextKind.BATTLE_START,
            lang="en",
            seed=100,
            repo_id="test",
            extra_context={"commit_type": "feat", "tier": "normal"},
        )

        responses = client.generate_batch([req1, req2])

        assert responses[0].text != responses[1].text
    
    def test_all_text_kinds(self):
        """Mock client should support all text kinds."""
        client = MockAIClient()
        
        requests = [
            TextRequest(kind=TextKind.ENEMY_INTRO, lang="en", seed=1, repo_id="test"),
            TextRequest(kind=TextKind.BATTLE_START, lang="en", seed=1, repo_id="test"),
            TextRequest(kind=TextKind.BATTLE_END, lang="en", seed=1, repo_id="test", extra_context={"victory": True}),
            TextRequest(kind=TextKind.EVENT_FLAVOR, lang="en", seed=1, repo_id="test"),
            TextRequest(kind=TextKind.BOSS_PHASE, lang="en", seed=1, repo_id="test"),
        ]
        
        responses = client.generate_batch(requests)
        
        assert len(responses) == 5
        for r in responses:
            assert r.text != ""
            assert len(r.text) <= 80  # Length limit
    
    def test_bilingual_support(self):
        """Mock client should support both English and Chinese."""
        client = MockAIClient()
        
        req_en = TextRequest(kind=TextKind.ENEMY_INTRO, lang="en", seed=123, repo_id="test")
        req_zh = TextRequest(kind=TextKind.ENEMY_INTRO, lang="zh_CN", seed=123, repo_id="test")
        
        responses = client.generate_batch([req_en, req_zh])
        
        assert len(responses) == 2
        # Both should have text (different languages)
        assert responses[0].text != ""
        assert responses[1].text != ""
        assert responses[0].text != responses[1].text
        assert any("\u4e00" <= ch <= "\u9fff" for ch in responses[1].text)


class TestTextCache:
    """Test text caching system."""
    
    def test_cache_set_and_get(self):
        """Test basic cache set/get."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = TextCache(cache_dir=tmpdir, backend="json")
            
            # Create a request and response
            request = TextRequest(
                kind=TextKind.ENEMY_INTRO,
                lang="en",
                seed=123,
                repo_id="test-repo"
            )
            
            response = TextResponse(
                text="Test enemy intro",
                provider="mock",
                cached=False
            )
            
            # Build cache key
            key = cache.build_cache_key("mock", request, content_version="1.0")
            
            # Set and get
            cache.set(key, response)
            cached = cache.get(key)
            
            assert cached is not None
            assert cached.text == "Test enemy intro"
            assert cached.provider == "mock"
            assert cached.cached is True
    
    def test_cache_miss(self):
        """Test cache miss returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = TextCache(cache_dir=tmpdir, backend="json")
            
            result = cache.get("nonexistent_key")
            
            assert result is None
    
    def test_sqlite_backend(self):
        """Test SQLite backend."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = TextCache(cache_dir=tmpdir, backend="sqlite")
            
            request = TextRequest(
                kind=TextKind.BATTLE_START,
                lang="zh_CN",
                seed=456,
                repo_id="test"
            )
            response = TextResponse(text="战斗开始！", provider="mock")
            
            key = cache.build_cache_key("mock", request, content_version="1.0")
            cache.set(key, response)
            cached = cache.get(key)
            
            assert cached is not None
            assert cached.text == "战斗开始！"
    
    def test_cache_stats(self):
        """Test cache statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = TextCache(cache_dir=tmpdir, backend="json")
            
            request = TextRequest(
                kind=TextKind.EVENT_FLAVOR,
                lang="en",
                seed=789,
                repo_id="test"
            )
            response = TextResponse(text="Test", provider="mock")
            
            key = cache.build_cache_key("mock", request, content_version="1.0")
            cache.set(key, response)
            
            stats = cache.get_stats()
            
            assert stats["backend"] == "json"
            assert stats["entries"] >= 1


class TestSanitization:
    """Test text sanitization."""
    
    def test_remove_markdown(self):
        """Test markdown removal."""
        text = "```python\nprint('hello')\n```"
        result, _ = sanitize_text(text, TextKind.ENEMY_INTRO)
        
        assert "```" not in result
        assert "python" not in result
    
    def test_single_line(self):
        """Test multi-line to single-line conversion."""
        text = "Line 1\nLine 2\nLine 3"
        result, _ = sanitize_text(text, TextKind.BATTLE_START)
        
        assert "\n" not in result
        assert "Line 1 Line 2 Line 3" in result
    
    def test_length_limit(self):
        """Test length limits by text kind."""
        long_text = "A" * 200
        
        # Enemy intro: 60 chars max
        result, meta = sanitize_text(long_text, TextKind.ENEMY_INTRO)
        assert len(result) <= 60
        assert meta["trimmed"] is True
        
        # Battle start: 80 chars max
        result, meta = sanitize_text(long_text, TextKind.BATTLE_START)
        assert len(result) <= 80
    
    def test_blocked_keywords(self):
        """Test blocked keyword filtering."""
        blocked_text = "You should attack now! This deals 50 damage."
        result, meta = sanitize_text(blocked_text, TextKind.BATTLE_START)
        
        # Should either be empty or have blocked content removed
        assert "you should" not in result.lower()
    
    def test_empty_input(self):
        """Test empty input handling."""
        result, meta = sanitize_text("", TextKind.ENEMY_INTRO)
        assert result == ""
        assert meta["reason"] == "empty_input"


class TestFallbacks:
    """Test fallback template system."""
    
    def test_enemy_intro_fallbacks(self):
        """Test enemy intro fallbacks by commit type."""
        request = TextRequest(
            kind=TextKind.ENEMY_INTRO,
            lang="en",
            seed=123,
            repo_id="test",
            extra_context={"commit_type": "feat"}
        )
        
        result = get_fallback_text(request)
        
        assert result != ""
        assert "feature" in result.lower() or "new" in result.lower()
    
    def test_zh_cn_fallbacks(self):
        """Test Chinese fallbacks."""
        request = TextRequest(
            kind=TextKind.ENEMY_INTRO,
            lang="zh_CN",
            seed=123,
            repo_id="test",
            extra_context={"commit_type": "fix"}
        )
        
        result = get_fallback_text(request)
        
        assert result != ""
        # Should contain Chinese text
        assert any(ord(c) > 127 for c in result)
    
    def test_battle_start_fallbacks(self):
        """Test battle start fallbacks by tier."""
        # Normal enemy
        request = TextRequest(
            kind=TextKind.BATTLE_START,
            lang="en",
            seed=123,
            repo_id="test",
            extra_context={"tier": "normal"}
        )
        result = get_fallback_text(request)
        assert "battle" in result.lower() or "begins" in result.lower()
        
        # Elite enemy
        request.extra_context["tier"] = "elite"
        result = get_fallback_text(request)
        assert "elite" in result.lower() or "enemy" in result.lower()
    
    def test_battle_end_fallbacks(self):
        """Test battle end fallbacks by victory/defeat."""
        # Victory
        request = TextRequest(
            kind=TextKind.BATTLE_END,
            lang="en",
            seed=123,
            repo_id="test",
            extra_context={"victory": True}
        )
        result = get_fallback_text(request)
        assert "victory" in result.lower() or "triumph" in result.lower()
        
        # Defeat
        request.extra_context["victory"] = False
        result = get_fallback_text(request)
        assert "defeat" in result.lower() or "retreat" in result.lower()
    
    def test_event_fallbacks(self):
        """Test event fallbacks by type."""
        request = TextRequest(
            kind=TextKind.EVENT_FLAVOR,
            lang="en",
            seed=123,
            repo_id="test",
            extra_context={"event_type": "rest"}
        )
        result = get_fallback_text(request)
        assert "peaceful" in result.lower() or "haven" in result.lower()
    
    def test_ultimate_fallback(self):
        """Test ultimate fallback for unknown cases."""
        # Unknown commit type
        request = TextRequest(
            kind=TextKind.ENEMY_INTRO,
            lang="en",
            seed=123,
            repo_id="test",
            extra_context={"commit_type": "unknown_type_xyz"}
        )
        
        result = get_fallback_text(request)
        assert result != ""
        # Should use default fallback
        assert "mysterious" in result.lower() or "enemy" in result.lower()


class TestTextKinds:
    """Test text kind enum and request/response types."""
    
    def test_all_kinds_exist(self):
        """Verify all required text kinds exist."""
        kinds = list(TextKind)
        
        assert TextKind.ENEMY_INTRO in kinds
        assert TextKind.BATTLE_START in kinds
        assert TextKind.BATTLE_END in kinds
        assert TextKind.EVENT_FLAVOR in kinds
        assert TextKind.BOSS_PHASE in kinds
    
    def test_text_request_defaults(self):
        """Test TextRequest default values."""
        request = TextRequest(
            kind=TextKind.ENEMY_INTRO,
            lang="en",
            seed=123,
            repo_id="test"
        )
        
        assert request.commit_sha is None
        assert request.enemy_id is None
        assert request.event_id is None
        assert request.extra_context == {}
    
    def test_text_response_defaults(self):
        """Test TextResponse default values."""
        response = TextResponse(text="Hello", provider="test")
        
        assert response.cached is False
        assert response.meta == {}
        assert response.trimmed is False
        assert response.fallback_used is False
    
    def test_response_properties(self):
        """Test TextResponse computed properties."""
        # Trimmed
        response = TextResponse(
            text="Hello",
            provider="test",
            meta={"trimmed": True}
        )
        assert response.trimmed is True
        
        # Fallback
        response = TextResponse(
            text="Hello",
            provider="fallback",
            meta={}
        )
        assert response.fallback_used is True


class TestCacheKeyGeneration:
    """Test cache key generation."""
    
    def test_key_deterministic(self):
        """Same inputs should produce same key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = TextCache(cache_dir=tmpdir, backend="json")
            
            request = TextRequest(
                kind=TextKind.ENEMY_INTRO,
                lang="en",
                seed=123,
                repo_id="test"
            )
            
            key1 = cache.build_cache_key("mock", request, content_version="1.0")
            key2 = cache.build_cache_key("mock", request, content_version="1.0")
            
            assert key1 == key2
    
    def test_different_provider_different_key(self):
        """Different providers should produce different keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = TextCache(cache_dir=tmpdir, backend="json")
            
            request = TextRequest(
                kind=TextKind.ENEMY_INTRO,
                lang="en",
                seed=123,
                repo_id="test"
            )
            
            key1 = cache.build_cache_key("mock", request, content_version="1.0")
            key2 = cache.build_cache_key("openai", request, content_version="1.0")
            
            assert key1 != key2

    def test_different_extra_context_different_key(self):
        """Different extra_context should produce different keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = TextCache(cache_dir=tmpdir, backend="json")

            req1 = TextRequest(
                kind=TextKind.ENEMY_INTRO,
                lang="en",
                seed=123,
                repo_id="test",
                extra_context={"commit_type": "feat"},
            )
            req2 = TextRequest(
                kind=TextKind.ENEMY_INTRO,
                lang="en",
                seed=123,
                repo_id="test",
                extra_context={"commit_type": "fix"},
            )

            key1 = cache.build_cache_key("mock", req1, content_version="1.0")
            key2 = cache.build_cache_key("mock", req2, content_version="1.0")

            assert key1 != key2

    def test_extra_context_dict_order_same_key(self):
        """Dict key order in extra_context should not change key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = TextCache(cache_dir=tmpdir, backend="json")

            req1 = TextRequest(
                kind=TextKind.EVENT_FLAVOR,
                lang="en",
                seed=123,
                repo_id="test",
                extra_context={"event_type": "shop", "tier": "elite"},
            )
            req2 = TextRequest(
                kind=TextKind.EVENT_FLAVOR,
                lang="en",
                seed=123,
                repo_id="test",
                extra_context={"tier": "elite", "event_type": "shop"},
            )

            key1 = cache.build_cache_key("mock", req1, content_version="1.0")
            key2 = cache.build_cache_key("mock", req2, content_version="1.0")

            assert key1 == key2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
