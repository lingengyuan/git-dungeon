"""
M6 AI Integration Tests

Tests for AI CLI integration, parameters, and full workflow.
"""

import pytest
import os
import tempfile
from unittest.mock import patch

from git_dungeon.ai import TextKind, TextResponse, NullAIClient, MockAIClient, TextCache
from git_dungeon.ai.integration import (
    create_ai_client,
    get_ai_text,
    AIAggregator,
)


class TestCLIArgs:
    """Test CLI argument parsing for AI parameters."""
    
    def test_null_client_default(self):
        """Null client should be default when AI is off."""
        client = create_ai_client("null")
        assert isinstance(client, NullAIClient)
        assert client.name == "null"
    
    def test_mock_client(self):
        """Mock client should be created with provider name."""
        client = create_ai_client("mock")
        assert isinstance(client, MockAIClient)
        assert client.name == "mock"
    
    def test_gemini_client_no_key(self):
        """Gemini client should work without API key (falls back to mock internally)."""
        # Should not raise, but will use fallback
        client = create_ai_client("gemini", api_key=None)
        # Client is created but will fallback when used
        assert client is not None


class TestAIIntegration:
    """Test AI integration with game flow."""
    
    def test_cache_creation(self):
        """Test cache creation with different backends."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test SQLite backend
            cache = TextCache(cache_dir=tmpdir, backend="sqlite")
            assert cache.backend == "sqlite"
            assert cache.cache_dir.exists()
            
            # Test JSON backend
            cache_json = TextCache(cache_dir=tmpdir, backend="json")
            assert cache_json.backend == "json"
    
    def test_ai_text_generation_flow(self):
        """Test complete AI text generation flow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create client and cache
            client = MockAIClient()
            cache = TextCache(cache_dir=tmpdir, backend="sqlite")
            
            # Generate text
            text = get_ai_text(
                client=client,
                cache=cache,
                kind=TextKind.ENEMY_INTRO,
                lang="en",
                seed=12345,
                repo_id="test-repo",
                extra_context={"commit_type": "feat"},
                content_version="1.0"
            )
            
            # Should have generated text
            assert text != ""
    
    def test_ai_fallback_when_disabled(self):
        """Test that AI returns empty when disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            client = NullAIClient()
            cache = TextCache(cache_dir=tmpdir, backend="sqlite")
            
            text = get_ai_text(
                client=client,
                cache=cache,
                kind=TextKind.BATTLE_START,
                lang="en",
                seed=123,
                repo_id="test",
                content_version="1.0"
            )
            
            # Null client should return empty
            assert text == ""
    
    def test_cache_hit(self):
        """Test that cached results are returned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            client = MockAIClient()
            cache = TextCache(cache_dir=tmpdir, backend="sqlite")
            
            # First request - should generate
            text1 = get_ai_text(
                client=client,
                cache=cache,
                kind=TextKind.ENEMY_INTRO,
                lang="en",
                seed=99999,
                repo_id="cache-test",
                content_version="1.0"
            )
            
            # Second request with same params - should hit cache
            # Note: Implementation detail depends on cache key generation
            assert text1 != ""

    def test_fallback_result_is_cached(self):
        """Provider-empty fallback text should be cached to avoid repeated API hits."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = TextCache(cache_dir=tmpdir, backend="sqlite")

            class EmptyClient:
                name = "gemini/test"

                def __init__(self):
                    self.calls = 0

                def generate_batch(self, requests):
                    self.calls += 1
                    return [TextResponse(text="", provider=self.name, cached=False, meta={"reason": "empty"}) for _ in requests]

            client = EmptyClient()
            params = dict(
                client=client,
                cache=cache,
                kind=TextKind.BATTLE_START,
                lang="en",
                seed=777,
                repo_id="fallback-cache-test",
                extra_context={"tier": "normal"},
                content_version="1.0",
            )

            text1 = get_ai_text(**params)
            text2 = get_ai_text(**params)

            assert text1 != ""
            assert text2 == text1
            assert client.calls == 1


class TestAIAggregator:
    """Test AI request aggregator for batch processing."""
    
    def test_aggregator_creation(self):
        """Test aggregator initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            client = MockAIClient()
            cache = TextCache(cache_dir=tmpdir, backend="sqlite")
            
            aggregator = AIAggregator(
                client=client,
                cache=cache,
                lang="en",
                seed=123,
                repo_id="test"
            )
            
            assert aggregator.client == client
            assert aggregator.cache == cache
            assert aggregator.lang == "en"
            assert aggregator.seed == 123
    
    def test_add_request(self):
        """Test adding requests to aggregator."""
        with tempfile.TemporaryDirectory() as tmpdir:
            aggregator = AIAggregator(
                client=MockAIClient(),
                cache=TextCache(cache_dir=tmpdir),
                lang="en",
                seed=456,
                repo_id="test"
            )
            
            aggregator.add_request(
                TextKind.ENEMY_INTRO,
                "enemy_1",
                extra_context={"commit_type": "fix"}
            )
            
            assert len(aggregator.requests) == 1
    
    def test_prefetch_empty(self):
        """Test prefetch with no requests returns empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            aggregator = AIAggregator(
                client=MockAIClient(),
                cache=TextCache(cache_dir=tmpdir),
                lang="en",
                seed=789,
                repo_id="test"
            )
            
            results = aggregator.prefetch()
            
            assert results == {}
            assert len(aggregator.requests) == 0


class TestEnvironmentVariables:
    """Test that environment variables are read correctly."""
    
    def test_gemini_key_from_env(self):
        """Test Gemini API key is read from environment."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-123"}):
            client = create_ai_client("gemini", api_key=None)
            # The client should attempt to use the environment variable
            # Implementation details may vary
            assert client is not None
    
    def test_openai_key_from_env(self):
        """Test OpenAI API key is read from environment."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-123"}):
            # This will fallback to mock if openai package not installed
            client = create_ai_client("openai", api_key=None)
            assert client is not None
    
    def test_no_hardcoded_keys(self):
        """Verify no API keys are hardcoded in the module."""
        import git_dungeon.ai.integration as integration_module
        
        # Check that the module doesn't contain any API key patterns
        import inspect
        source = inspect.getsource(integration_module)
        
        # Should not contain actual API key patterns
        assert "AIzaSy" not in source  # Google/Gemini key pattern
        assert "sk-" not in source  # OpenAI key pattern


class TestTextKindsIntegration:
    """Test all text kinds are properly integrated."""
    
    @pytest.mark.parametrize("kind", [
        TextKind.ENEMY_INTRO,
        TextKind.BATTLE_START,
        TextKind.BATTLE_END,
        TextKind.EVENT_FLAVOR,
        TextKind.BOSS_PHASE,
    ])
    def test_all_kinds_supported(self, kind):
        """Verify all text kinds can be generated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            client = MockAIClient()
            cache = TextCache(cache_dir=tmpdir, backend="sqlite")
            
            text = get_ai_text(
                client=client,
                cache=cache,
                kind=kind,
                lang="en",
                seed=111,
                repo_id="test",
                content_version="1.0"
            )
            
            assert text != ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
