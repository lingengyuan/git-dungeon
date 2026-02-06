"""AI-capable CLI wrapper."""

from __future__ import annotations

import argparse
import hashlib
from typing import Optional

from git_dungeon.ai import NullAIClient, TextCache, TextKind
from git_dungeon.ai.integration import (
    AIAggregator,
    add_ai_args as add_ai_args_to_parser,
    create_ai_client,
    get_ai_text as get_ai_text_direct,
)


class GitDungeonAICLI:
    """Wrap `GitDungeonCLI` and attach AI settings/runtime helpers."""

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
        ai_prefetch: str = "chapter",
    ) -> None:
        self.seed = seed or 0
        self.lang = lang
        self.ai_enabled = ai_enabled
        self.ai_provider = ai_provider
        self.ai_cache_dir = ai_cache_dir
        self.ai_prefetch = ai_prefetch

        from git_dungeon.main_cli import GitDungeonCLI

        self._base_cli = GitDungeonCLI(
            seed=seed,
            verbose=verbose,
            auto_mode=auto_mode,
            lang=lang,
        )

        provider = ai_provider if ai_enabled else "off"
        self.ai_client = create_ai_client(provider=provider, timeout=ai_timeout)
        self.ai_cache = TextCache(cache_dir=ai_cache_dir, backend="sqlite")
        self.ai_aggregator: Optional[AIAggregator] = None

    def _repo_id(self, repo_input: str) -> str:
        return hashlib.md5(repo_input.encode("utf-8")).hexdigest()[:8]

    def _ensure_aggregator(self, repo_input: str) -> None:
        if not self.ai_enabled or isinstance(self.ai_client, NullAIClient):
            return
        if self.ai_aggregator is not None:
            return

        self.ai_aggregator = AIAggregator(
            client=self.ai_client,
            cache=self.ai_cache,
            lang=self.lang,
            seed=self.seed,
            repo_id=self._repo_id(repo_input),
            content_version="1.0",
        )

    def get_ai_text(self, kind: TextKind, extra_context: Optional[dict] = None) -> str:
        """Fetch one AI text line through cache + fallback policy."""
        if not self.ai_enabled or isinstance(self.ai_client, NullAIClient):
            return ""

        if self.ai_aggregator is not None:
            return self.ai_aggregator.get(
                kind=kind,
                key=f"{kind.value}_dynamic",
                extra_context=extra_context or {},
            )

        return get_ai_text_direct(
            client=self.ai_client,
            cache=self.ai_cache,
            kind=kind,
            lang=self.lang,
            seed=self.seed,
            repo_id="unknown",
            extra_context=extra_context or {},
        )

    def print_ai_status(self) -> None:
        if self.ai_enabled:
            print(f"\n[AI] enabled provider={self.ai_provider}")
            stats = self.ai_cache.get_stats()
            print(f"[AI] cache entries={stats.get('entries', 0)} backend={stats.get('backend')}")
        else:
            print("\n[AI] disabled")

    def start(self, repo_input: str) -> bool:
        self.print_ai_status()
        self._ensure_aggregator(repo_input)
        return self._base_cli.start(repo_input)


def add_ai_args(parser: argparse.ArgumentParser) -> None:
    """Add AI flags to an existing parser."""
    add_ai_args_to_parser(parser)


def create_ai_cli_from_args(args: argparse.Namespace) -> GitDungeonAICLI:
    """Factory from parsed CLI args."""
    return GitDungeonAICLI(
        seed=args.seed,
        verbose=args.verbose,
        auto_mode=getattr(args, "auto", False),
        lang=args.lang,
        ai_enabled=(args.ai == "on"),
        ai_provider=args.ai_provider,
        ai_cache_dir=args.ai_cache,
        ai_timeout=args.ai_timeout,
        ai_prefetch=args.ai_prefetch,
    )
