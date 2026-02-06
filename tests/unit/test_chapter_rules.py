"""Unit tests for chapter boss determinism."""

from __future__ import annotations

from types import SimpleNamespace

from git_dungeon.engine.rng import create_rng
from git_dungeon.engine.rules.chapter_rules import CHAPTER_CONFIGS, Chapter, ChapterSystem, ChapterType


class _CountingRNG:
    """Minimal RNG that counts how many times random() is called."""

    def __init__(self, value: float = 0.0) -> None:
        self.value = value
        self.calls = 0

    def random(self) -> float:
        self.calls += 1
        return self.value


def _build_commits() -> list[SimpleNamespace]:
    """Build deterministic commit-like objects for chapter parsing."""
    messages = [
        "chore: init project",
        "docs: bootstrap",
        "feat: add login",
        "feat: add profile",
        "feat: add settings",
        "feat: add dashboard",
        "feat: add search",
        "fix: patch token refresh",
        "fix: patch api timeout",
        "fix: patch cache invalidation",
        "fix: patch race condition",
        "fix: patch retry loop",
        "release: v1.0.0",
    ]
    return [SimpleNamespace(message=msg) for msg in messages]


def test_is_boss_chapter_is_stable_within_same_chapter() -> None:
    """Boss decision should be rolled once and stay stable for the chapter."""
    rng = _CountingRNG(value=0.0)
    chapter = Chapter(
        chapter_id="chapter_1",
        chapter_index=1,
        chapter_type=ChapterType.FEATURE,
        config=CHAPTER_CONFIGS[ChapterType.FEATURE],
        commits=[SimpleNamespace(message="feat: add feature")],
        start_index=0,
        end_index=0,
        _rng=rng,
    )

    first_result = chapter.is_boss_chapter
    for _ in range(10):
        assert chapter.is_boss_chapter == first_result

    assert rng.calls == 1


def test_boss_distribution_is_reproducible_with_fixed_seed() -> None:
    """Given the same seed and commits, chapter boss layout should be reproducible."""
    commits = _build_commits()

    system_a = ChapterSystem(rng=create_rng(2026))
    system_b = ChapterSystem(rng=create_rng(2026))

    chapters_a = system_a.parse_chapters(commits)
    chapters_b = system_b.parse_chapters(commits)

    distribution_a = [chapter.is_boss_chapter for chapter in chapters_a]
    distribution_b = [chapter.is_boss_chapter for chapter in chapters_b]

    assert distribution_a == distribution_b
    assert any(chapter.config.boss_chance > 0 for chapter in chapters_a)
