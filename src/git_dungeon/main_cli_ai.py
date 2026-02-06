"""AI-capable CLI wrapper."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any, Optional

from git_dungeon.ai import NullAIClient, TextCache, TextKind
from git_dungeon.i18n import normalize_lang
from git_dungeon.ai.integration import (
    AIAggregator,
    add_ai_args as add_ai_args_to_parser,
    create_ai_client,
    get_ai_text as get_ai_text_direct,
)
from git_dungeon.engine.daily import DailyChallengeInfo, resolve_run_seed


class GitDungeonAICLI:
    """Wrap `GitDungeonCLI` and attach AI settings/runtime helpers."""

    def __init__(
        self,
        seed: Optional[int] = None,
        verbose: bool = False,
        compact: bool = False,
        auto_mode: bool = False,
        metrics_out: Optional[str] = None,
        print_metrics: bool = False,
        lang: str = "en",
        content_pack_args: Optional[list[str]] = None,
        mutator: str = "none",
        daily_info: Optional[DailyChallengeInfo] = None,
        ai_enabled: bool = False,
        ai_provider: str = "mock",
        ai_cache_dir: str = ".git_dungeon_cache",
        ai_timeout: int = 5,
        ai_prefetch: str = "chapter",
    ) -> None:
        self.seed = seed or 0
        self.lang = normalize_lang(lang)
        self.ai_enabled = ai_enabled
        self.ai_provider = ai_provider
        self.ai_cache_dir = ai_cache_dir
        self.ai_prefetch_requested = ai_prefetch
        self.ai_prefetch_auto_adjusted = False
        self.ai_prefetch = self._resolve_prefetch_strategy(ai_prefetch)
        self._content_version = self._build_content_version()
        self._repo_id_value = "unknown"
        self._hooks_installed = False
        self._run_prefetched = False
        self._prefetched_chapters: set[int] = set()

        from git_dungeon.main_cli import GitDungeonCLI

        self._base_cli: Any = GitDungeonCLI(
            seed=seed,
            verbose=verbose,
            compact=compact,
            auto_mode=auto_mode,
            metrics_out=metrics_out,
            print_metrics=print_metrics,
            lang=self.lang,
            content_pack_args=content_pack_args,
            mutator=mutator,
            daily_info=daily_info,
        )

        provider = ai_provider if ai_enabled else "off"
        self.ai_client = create_ai_client(provider=provider, timeout=ai_timeout)
        self.ai_cache = TextCache(cache_dir=ai_cache_dir, backend="sqlite")
        self.ai_aggregator: Optional[AIAggregator] = None

    def _resolve_prefetch_strategy(self, ai_prefetch: str) -> str:
        """Auto-tune prefetch strategy for providers with strict free-tier RPM limits."""
        strategy = ai_prefetch
        if (
            self.ai_enabled
            and self.ai_provider == "gemini"
            and ai_prefetch != "off"
        ):
            strategy = "off"
            self.ai_prefetch_auto_adjusted = True
        return strategy

    def _repo_id(self, repo_input: str) -> str:
        return hashlib.md5(repo_input.encode("utf-8")).hexdigest()[:8]

    def _build_content_version(self) -> str:
        """Hash AI text assets so cache invalidates when templates change."""
        digest = hashlib.sha256()
        try:
            from git_dungeon.ai import fallbacks, prompts, sanitize

            for module in (prompts, fallbacks, sanitize):
                module_file = getattr(module, "__file__", "")
                if not module_file:
                    continue
                path = Path(module_file)
                if path.exists():
                    digest.update(path.read_bytes())
        except Exception:
            pass
        return f"m6-{digest.hexdigest()[:12]}"

    def _commit_type_from_message(self, message: str) -> str:
        """Normalize commit message to fallback/prompt commit type buckets."""
        msg = (message or "").lower().strip()
        if "merge" in msg:
            return "merge"
        if msg.startswith("feat"):
            return "feat"
        if msg.startswith("fix") or "bug" in msg:
            return "fix"
        if msg.startswith("docs"):
            return "docs"
        if msg.startswith("refactor"):
            return "refactor"
        if msg.startswith("test"):
            return "test"
        if msg.startswith("chore"):
            return "chore"
        if msg.startswith("perf"):
            return "perf"
        if msg.startswith("style"):
            return "style"
        if msg.startswith("ci"):
            return "ci"
        return "default"

    def _commit_type_from_enemy(self, enemy: Any) -> str:
        enemy_type = getattr(enemy, "enemy_type", "")
        mapping = {
            "feature": "feat",
            "bug": "fix",
            "docs": "docs",
            "merge": "merge",
        }
        if enemy_type in mapping:
            return mapping[enemy_type]
        message = getattr(enemy, "commit_message", "")
        return self._commit_type_from_message(message)

    def _enemy_tier_from_chapter(self, chapter: Any) -> str:
        if getattr(chapter, "is_boss_chapter", False):
            return "boss"
        chapter_index = int(getattr(chapter, "chapter_index", 0))
        return "elite" if chapter_index >= 2 else "normal"

    def _emit_ai_line(self, text: str) -> None:
        clean = text.strip()
        if clean:
            print(f"   🧠 {clean}")

    def _safe_ai_text(self, kind: TextKind, extra_context: Optional[dict] = None) -> str:
        try:
            return self.get_ai_text(kind=kind, extra_context=extra_context or {})
        except Exception as exc:
            if getattr(self._base_cli, "verbose", False):
                print(f"[AI] warning: text generation failed: {exc}")
            return ""

    def _schedule_prefetch_for_chapter(self, chapter: Any) -> None:
        if not self.ai_aggregator:
            return

        chapter_id = str(getattr(chapter, "chapter_id", f"chapter_{getattr(chapter, 'chapter_index', 0)}"))
        chapter_name = str(getattr(chapter, "name", "unknown chapter"))
        tier = self._enemy_tier_from_chapter(chapter)
        chapter_type = getattr(getattr(chapter, "chapter_type", None), "value", "default")

        self.ai_aggregator.add_request(
            TextKind.BATTLE_START,
            key=f"{chapter_id}:battle_start:{tier}",
            extra_context={"tier": tier, "commit_type": chapter_type, "player_class": "Developer"},
        )
        self.ai_aggregator.add_request(
            TextKind.BATTLE_END,
            key=f"{chapter_id}:battle_end:victory",
            extra_context={"victory": True, "commit_type": chapter_type, "loot": "chapter rewards"},
        )
        self.ai_aggregator.add_request(
            TextKind.BATTLE_END,
            key=f"{chapter_id}:battle_end:defeat",
            extra_context={"victory": False, "commit_type": chapter_type, "loot": "none"},
        )
        self.ai_aggregator.add_request(
            TextKind.EVENT_FLAVOR,
            key=f"{chapter_id}:event:chapter",
            extra_context={
                "event_type": "mystery",
                "event_location": chapter_name,
                "event_tags": ["chapter", str(chapter_type)],
            },
        )

        config = getattr(chapter, "config", None)
        if getattr(config, "shop_enabled", False):
            self.ai_aggregator.add_request(
                TextKind.EVENT_FLAVOR,
                key=f"{chapter_id}:event:shop",
                extra_context={
                    "event_type": "shop",
                    "event_location": chapter_name,
                    "event_tags": ["shop", str(chapter_type)],
                },
            )

        if getattr(chapter, "is_boss_chapter", False):
            self.ai_aggregator.add_request(
                TextKind.BOSS_PHASE,
                key=f"{chapter_id}:boss_phase",
                extra_context={
                    "boss_name": chapter_name,
                    "phase": "1",
                    "prev_ability": "none",
                },
            )

        commits = getattr(chapter, "commits", []) or []
        commit_types = {
            self._commit_type_from_message(getattr(commit, "message", ""))
            for commit in commits
        }
        for commit_type in sorted(commit_types):
            self.ai_aggregator.add_request(
                TextKind.ENEMY_INTRO,
                key=f"{chapter_id}:enemy_intro:{commit_type}",
                extra_context={"commit_type": commit_type},
            )

    def _prefetch_chapter(self, chapter: Any) -> None:
        if not self.ai_aggregator:
            return
        chapter_index = int(getattr(chapter, "chapter_index", -1))
        if chapter_index in self._prefetched_chapters:
            return
        self._schedule_prefetch_for_chapter(chapter)
        self.ai_aggregator.prefetch()
        self._prefetched_chapters.add(chapter_index)

    def _prefetch_run(self) -> None:
        if self._run_prefetched or not self.ai_aggregator:
            return
        chapters = getattr(getattr(self._base_cli, "chapter_system", None), "chapters", []) or []
        for chapter in chapters:
            self._schedule_prefetch_for_chapter(chapter)
            self._prefetched_chapters.add(int(getattr(chapter, "chapter_index", -1)))
        self.ai_aggregator.prefetch()
        self._run_prefetched = True

    def _install_ai_hooks(self) -> None:
        """Attach AI text to the existing CLI output points."""
        if self._hooks_installed or not self.ai_enabled or isinstance(self.ai_client, NullAIClient):
            return

        base = self._base_cli
        original_print_chapter_intro = base._print_chapter_intro
        original_combat = base._combat
        original_open_shop = base._open_shop
        original_boss_combat = base._boss_combat

        def wrapped_print_chapter_intro(chapter: Any) -> None:
            if self.ai_prefetch == "run":
                self._prefetch_run()
            elif self.ai_prefetch == "chapter":
                self._prefetch_chapter(chapter)

            original_print_chapter_intro(chapter)

            text = self._safe_ai_text(
                TextKind.EVENT_FLAVOR,
                {
                    "event_type": "mystery",
                    "event_location": getattr(chapter, "name", "unknown chapter"),
                    "event_tags": ["chapter", str(getattr(getattr(chapter, "chapter_type", None), "value", "default"))],
                },
            )
            self._emit_ai_line(text)

        def wrapped_combat(enemy: Any, chapter: Any) -> bool:
            commit_type = self._commit_type_from_enemy(enemy)
            player_hp = 0
            if getattr(base, "state", None) and getattr(base.state, "player", None):
                player_hp = int(getattr(base.state.player.character, "current_hp", 0))

            intro_text = self._safe_ai_text(
                TextKind.ENEMY_INTRO,
                {
                    "commit_type": commit_type,
                    "commit_sha": getattr(enemy, "commit_hash", "unknown"),
                    "enemy_id": getattr(enemy, "entity_id", "unknown"),
                },
            )
            self._emit_ai_line(intro_text)

            start_text = self._safe_ai_text(
                TextKind.BATTLE_START,
                {
                    "tier": self._enemy_tier_from_chapter(chapter),
                    "commit_type": commit_type,
                    "player_class": "Developer",
                    "player_hp": player_hp,
                    "enemy_hp": getattr(enemy, "current_hp", 0),
                },
            )
            self._emit_ai_line(start_text)

            result = original_combat(enemy, chapter)

            end_text = self._safe_ai_text(
                TextKind.BATTLE_END,
                {
                    "victory": result,
                    "result": "victory" if result else "defeat",
                    "commit_type": commit_type,
                    "loot": "gold" if result else "none",
                },
            )
            self._emit_ai_line(end_text)
            return result

        def wrapped_open_shop(chapter: Any) -> None:
            text = self._safe_ai_text(
                TextKind.EVENT_FLAVOR,
                {
                    "event_type": "shop",
                    "event_location": getattr(chapter, "name", "shop"),
                    "event_tags": ["shop"],
                },
            )
            self._emit_ai_line(text)
            original_open_shop(chapter)

        def wrapped_boss_combat(chapter: Any) -> bool:
            phase_text = self._safe_ai_text(
                TextKind.BOSS_PHASE,
                {
                    "boss_name": getattr(chapter, "name", "Boss"),
                    "phase": "1",
                    "prev_ability": "none",
                },
            )
            self._emit_ai_line(phase_text)

            result = original_boss_combat(chapter)

            end_text = self._safe_ai_text(
                TextKind.BATTLE_END,
                {
                    "victory": result,
                    "result": "victory" if result else "defeat",
                    "commit_type": "merge",
                    "loot": "boss reward" if result else "none",
                },
            )
            self._emit_ai_line(end_text)
            return result

        base._print_chapter_intro = wrapped_print_chapter_intro
        base._combat = wrapped_combat
        base._open_shop = wrapped_open_shop
        base._boss_combat = wrapped_boss_combat
        self._hooks_installed = True

    def _ensure_aggregator(self, repo_input: str) -> None:
        if not self.ai_enabled or isinstance(self.ai_client, NullAIClient):
            return
        if self.ai_aggregator is not None:
            return
        self._repo_id_value = self._repo_id(repo_input)

        self.ai_aggregator = AIAggregator(
            client=self.ai_client,
            cache=self.ai_cache,
            lang=self.lang,
            seed=self.seed,
            repo_id=self._repo_id_value,
            content_version=self._content_version,
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
            repo_id=self._repo_id_value,
            extra_context=extra_context or {},
            content_version=self._content_version,
        )

    def print_ai_status(self) -> None:
        if self.ai_enabled:
            print(f"\n[AI] enabled provider={self.ai_provider}")
            stats = self.ai_cache.get_stats()
            print(f"[AI] cache entries={stats.get('entries', 0)} backend={stats.get('backend')}")
            print(f"[AI] content_version={self._content_version}")
            if self.ai_prefetch_auto_adjusted:
                print(
                    f"[AI] prefetch auto-adjusted: {self.ai_prefetch_requested} -> {self.ai_prefetch}"
                    " (gemini free-tier safety)"
                )
            else:
                print(f"[AI] prefetch={self.ai_prefetch}")
        else:
            print("\n[AI] disabled")

    def start(self, repo_input: str) -> bool:
        self.print_ai_status()
        self._ensure_aggregator(repo_input)
        self._install_ai_hooks()
        return self._base_cli.start(repo_input)


def add_ai_args(parser: argparse.ArgumentParser) -> None:
    """Add AI flags to an existing parser."""
    add_ai_args_to_parser(parser)


def create_ai_cli_from_args(args: argparse.Namespace) -> GitDungeonAICLI:
    """Factory from parsed CLI args."""
    effective_seed, daily_info = resolve_run_seed(
        seed=args.seed,
        daily=getattr(args, "daily", False),
        daily_date=getattr(args, "daily_date", None),
    )
    return GitDungeonAICLI(
        seed=effective_seed,
        verbose=args.verbose,
        compact=getattr(args, "compact", False),
        auto_mode=getattr(args, "auto", False),
        metrics_out=getattr(args, "metrics_out", None),
        print_metrics=getattr(args, "print_metrics", False),
        lang=args.lang,
        content_pack_args=getattr(args, "content_pack", []),
        mutator=getattr(args, "mutator", "none"),
        daily_info=daily_info,
        ai_enabled=(args.ai == "on"),
        ai_provider=args.ai_provider,
        ai_cache_dir=args.ai_cache,
        ai_timeout=args.ai_timeout,
        ai_prefetch=args.ai_prefetch,
    )
