"""Repository loading and run bootstrap for the pixel UI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from git_dungeon.config import GameConfig
from git_dungeon.content.runtime_loader import load_runtime_content
from git_dungeon.core.git_parser import CommitInfo, GitParser
from git_dungeon.engine import GameState, create_rng
from git_dungeon.engine.node_flow import ChapterNodeGenerator
from git_dungeon.engine.rules import ChapterSystem
from git_dungeon.engine.rules.chapter_rules import build_chapter_configs
from git_dungeon.i18n import i18n, normalize_lang


@dataclass(frozen=True)
class RunSummary:
    """Small load summary for Phase 1 pixel screens."""

    repo_path: str
    total_commits: int
    chapter_count: int
    current_chapter_name: str
    seed: int | None


class GameRunner:
    """Owns non-interactive repository loading for the pixel UI."""

    def __init__(
        self,
        repo_path: str,
        seed: int | None = None,
        lang: str = "en",
        content_pack_args: list[str] | None = None,
        content_dir: str | None = None,
    ) -> None:
        self.repo_path = repo_path
        self.seed = seed
        self.lang = normalize_lang(lang)
        i18n.load_language(self.lang)

        self.content_runtime = load_runtime_content(
            content_dir=content_dir,
            content_pack_args=content_pack_args,
        )
        self.rng = create_rng(seed)
        self.chapter_system = ChapterSystem(
            rng=self.rng,
            chapter_configs=build_chapter_configs(self.content_runtime.chapter_overrides),
        )
        self.node_generator = ChapterNodeGenerator()
        self.parser: GitParser | None = None
        self.commits: list[CommitInfo] = []
        self.state: GameState | None = None
        self.loaded = False

    def load_repository(self) -> RunSummary:
        """Load commits and build the initial state without printing or reading input."""
        repo_path = Path(self.repo_path)
        if not repo_path.exists():
            raise ValueError(f"Repository not found: {self.repo_path}")

        parser = GitParser(GameConfig())
        if not parser.load_repository(str(repo_path)):
            raise ValueError(f"Failed to load repository: {self.repo_path}")

        commits = parser.get_commit_history()
        if not commits:
            raise ValueError("No commits found")

        self.chapter_system.parse_chapters(commits)
        if not self.chapter_system.chapters:
            raise ValueError("No chapters could be built")

        self.parser = parser
        self.commits = commits
        self.state = GameState(
            seed=self.seed,
            repo_path=str(repo_path),
            total_commits=len(commits),
            current_commit_index=0,
            difficulty="normal",
        )
        self.state.player.character.current_hp = 100
        self.state.player.character.current_mp = 50
        self.state.route_state = {
            "current_node_id": "",
            "visited_nodes": [],
            "route_flags": {},
            "chapter_nodes": {},
        }
        self.loaded = True
        return self.summary()

    def summary(self) -> RunSummary:
        """Return the current load summary."""
        if not self.loaded or self.state is None:
            raise RuntimeError("Repository is not loaded")
        chapter = self.chapter_system.get_current_chapter()
        return RunSummary(
            repo_path=self.state.repo_path,
            total_commits=self.state.total_commits,
            chapter_count=len(self.chapter_system.chapters),
            current_chapter_name=getattr(chapter, "name", "") if chapter else "",
            seed=self.seed,
        )

    def current_chapter(self) -> Any:
        """Return the current chapter object for later screens."""
        return self.chapter_system.get_current_chapter()
