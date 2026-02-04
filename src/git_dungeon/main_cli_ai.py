"""
Git Dungeon - AI-Powered CLI Extension

CLI with AI text generation integration (M6).
"""

import argparse
import os
from typing import Optional, Any, Dict, List, Tuple

from git_dungeon.engine import (
    Engine, GameState, EnemyState,
    create_rng, EventType,
)
from git_dungeon.engine.rules import (
    ChapterSystem, ShopSystem, PlayerInventory,
    CombatRules, ProgressionRules,
    BossSystem, BossState,
)
from git_dungeon.config import GameConfig
from git_dungeon.core.git_parser import GitParser, CommitInfo
from git_dungeon.i18n import i18n
from git_dungeon.i18n.translations import get_translation
from git_dungeon.ai import (
    TextKind,
    NullAIClient, MockAIClient, GeminiAIClient,
    TextCache
)
from git_dungeon.ai.integration import AIAggregator


class GitDungeonAICLI:
    """Main CLI game with AI text generation support (M6)."""
    
    def __init__(
        self,
        seed: Optional[int] = None,
        verbose: bool = False,
        auto_mode: bool = False,
        lang: str = "en",
        ai_enabled: bool = False,
        ai_provider: str = "mock",
        ai_cache_dir: str = ".git_dungeon_cache",
        ai_timeout: int = 5,
        ai_prefetch: str = "chapter"
    ):
        self.seed = seed
        self.lang = lang
        self.verbose = verbose
        self.ai_enabled = ai_enabled
        self.ai_provider = ai_provider
        self.ai_cache_dir = ai_cache_dir
        self.ai_prefetch = ai_prefetch
        
        # Load language
        i18n.load_language(lang)
        
        # Initialize RNG and engine
        self.rng = create_rng(seed)
        self.engine = Engine(rng=self.rng)
        self.combat_rules = CombatRules(rng=self.rng)
        self.progression_rules = ProgressionRules(rng=self.rng)
        self.chapter_system = ChapterSystem(rng=self.rng)
        self.shop_system = ShopSystem(rng=self.rng)
        self.boss_system = BossSystem(rng=self.rng)
        
        # Initialize AI
        self.ai_client = self._init_ai_client(ai_provider, ai_timeout)
        self.ai_cache = TextCache(cache_dir=ai_cache_dir, backend="sqlite")
        self.ai_aggregator: Optional[AIAggregator] = None
        
        # Game state
        self.state: Optional[GameState] = None
        self.repo_info: Any = None
        self.inventory = PlayerInventory()
        self.current_shop: Any = None
        self.current_boss: Optional[BossState] = None
        self.auto_mode = auto_mode
        
        # AI statistics
        self.ai_stats = {
            "requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "fallbacks": 0,
        }
    
    def _init_ai_client(self, provider: str, timeout: int):
        """Initialize AI client."""
        if not self.ai_enabled:
            return NullAIClient()
        
        if provider == "mock":
            return MockAIClient()
        
        elif provider == "gemini":
            # API key from environment - NEVER hardcode
            gemini_key = os.environ.get("GEMINI_API_KEY")
            if gemini_key:
                print(f"[AI] Using Gemini with env GEMINI_API_KEY")
            else:
                print(f"[AI] Warning: GEMINI_API_KEY not set, using mock fallback")
            return GeminiAIClient(api_key=gemini_key, timeout=timeout)
        
        elif provider == "openai":
            openai_key = os.environ.get("OPENAI_API_KEY")
            if openai_key:
                print(f"[AI] Using OpenAI with env OPENAI_API_KEY")
            else:
                print(f"[AI] Warning: OPENAI_API_KEY not set, using mock fallback")
            try:
                from git_dungeon.ai.client_openai import OpenAIClient
                return OpenAIClient(api_key=openai_key, timeout=timeout)
            except ImportError:
                print(f"[AI] Warning: openai package not installed, using mock")
                return MockAIClient()
        
        else:
            print(f"[AI] Unknown provider: {provider}, using mock")
            return MockAIClient()
    
    def _init_ai_aggregator(self, repo_path: str):
        """Initialize AI aggregator for batch processing."""
        if not self.ai_enabled:
            return
        
        # Get stable repo ID (use path hash)
        import hashlib
        repo_id = hashlib.md5(repo_path.encode()).hexdigest()[:8]
        
        self.ai_aggregator = AIAggregator(
            client=self.ai_client,
            cache=self.ai_cache,
            lang=self.lang,
            seed=self.seed or 0,
            repo_id=repo_id,
            content_version="1.0"
        )
        
        # Prefetch strategy
        if self.ai_prefetch == "chapter":
            self._prefetch_chapter()
    
    def _prefetch_chapter(self):
        """Prefetch AI text for current chapter."""
        if not self.ai_aggregator or not self.chapter_system.chapters:
            return
        
        # Get current chapter enemies
        current_chapter = self.chapter_system.get_current_chapter()
        if not current_chapter:
            return
        
        # Add enemy intros
        for enemy_info in current_chapter.enemies[:5]:  # Prefetch first 5
            self.ai_aggregator.add_request(
                TextKind.ENEMY_INTRO,
                f"enemy_{enemy_info.enemy_id}",
                extra_context={
                    "commit_type": enemy_info.commit_type,
                    "enemy_id": enemy_info.enemy_id
                }
            )
        
        # Prefetch battle starts
        for i in range(min(5, len(current_chapter.enemies))):
            self.ai_aggregator.add_request(
                TextKind.BATTLE_START,
                f"battle_{i}",
                extra_context={
                    "commit_type": "commit",
                    "tier": "normal"
                }
            )
        
        # Prefetch event flavors
        for event in current_chapter.events[:3]:
            self.ai_aggregator.add_request(
                TextKind.EVENT_FLAVOR,
                f"event_{event.event_id}",
                extra_context={
                    "event_type": event.event_type,
                    "event_tags": event.tags
                }
            )
        
        # Execute prefetch
        results = self.ai_aggregator.prefetch()
        if results:
            print(f"[AI] Prefetched {len(results)} text entries")
    
    def get_ai_text(
        self,
        kind: TextKind,
        extra_context: dict = None
    ) -> str:
        """
        Get AI-generated text.
        
        Args:
            kind: Type of text to generate
            extra_context: Additional context
            
        Returns:
            Generated text (or empty if AI disabled)
        """
        if not self.ai_enabled or isinstance(self.ai_client, NullAIClient):
            return ""
        
        # Use aggregator if available
        if self.ai_aggregator:
            return self.ai_aggregator.get(
                kind,
                f"{kind.value}_dynamic",
                extra_context
            )
        
        # Direct generation
        from git_dungeon.ai.integration import get_ai_text as direct_get
        import hashlib
        repo_path = self.state.repo_path if self.state else "unknown"
        repo_id = hashlib.md5(repo_path.encode()).hexdigest()[:8]
        
        return direct_get(
            client=self.ai_client,
            cache=self.ai_cache,
            kind=kind,
            lang=self.lang,
            seed=self.seed or 0,
            repo_id=repo_id,
            extra_context=extra_context or {}
        )
    
    def print_ai_status(self):
        """Print current AI status."""
        if self.ai_enabled:
            print(f"\n🤖 AI: on (provider={self.ai_provider})")
            if hasattr(self.ai_cache, 'get_stats'):
                stats = self.ai_cache.get_stats()
                print(f"   Cache: {stats.get('entries', 0)} entries")
        else:
            print(f"\n🤖 AI: off")
    
    def _t(self, text: str) -> str:
        """Translate text based on current language."""
        if self.lang == "zh_CN":
            return get_translation(text, "zh_CN")
        return text
    
    # ... rest of the methods from original CLI ...


def add_ai_args(parser: argparse.ArgumentParser) -> None:
    """Add AI arguments to CLI parser."""
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
        help="AI cache directory"
    )
    ai_group.add_argument(
        "--ai-timeout",
        type=int,
        default=5,
        help="AI API timeout in seconds"
    )
    ai_group.add_argument(
        "--ai-prefetch",
        choices=["chapter", "run", "off"],
        default="chapter",
        help="AI text prefetch strategy"
    )


def create_ai_cli_from_args(args, original_cli) -> GitDungeonAICLI:
    """Create AI CLI from parsed arguments."""
    return GitDungeonAICLI(
        seed=args.seed,
        verbose=args.verbose,
        auto_mode=args.auto_mode,
        lang=args.lang,
        ai_enabled=(args.ai == "on"),
        ai_provider=args.ai_provider,
        ai_cache_dir=args.ai_cache,
        ai_timeout=args.ai_timeout,
        ai_prefetch=args.ai_prefetch
    )
