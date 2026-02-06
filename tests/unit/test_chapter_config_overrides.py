"""Tests for chapter config overrides and determinism."""

from __future__ import annotations

from dataclasses import dataclass

from git_dungeon.content.runtime_loader import load_runtime_content
from git_dungeon.engine.rng import create_rng
from git_dungeon.engine.rules.chapter_rules import ChapterSystem, build_chapter_configs


@dataclass
class _Commit:
    message: str


def _make_commits() -> list[_Commit]:
    return [
        _Commit("feat: bootstrap"),
        _Commit("feat: auth"),
        _Commit("fix: edge case"),
        _Commit("fix: race condition"),
        _Commit("merge: release branch"),
        _Commit("docs: polish"),
        _Commit("feat: add extension"),
    ]


def test_example_pack_chapter_overrides_are_applied() -> None:
    runtime = load_runtime_content(
        content_dir="src/git_dungeon/content",
        content_pack_args=["content_packs/example_pack"],
        env_content_dir="",
    )
    chapter_configs = build_chapter_configs(runtime.chapter_overrides)
    feature = chapter_configs[next(key for key in chapter_configs if key.value == "feature")]
    fix = chapter_configs[next(key for key in chapter_configs if key.value == "fix")]

    assert feature.name == "Plugin Bazaar"
    assert abs(feature.gold_bonus - 1.15) < 1e-9
    assert fix.name == "Hotfix Gauntlet"
    assert abs(fix.enemy_atk_multiplier - 1.55) < 1e-9


def test_chapter_flow_stays_deterministic_with_fixed_seed_and_pack() -> None:
    runtime = load_runtime_content(
        content_dir="src/git_dungeon/content",
        content_pack_args=["content_packs/example_pack"],
        env_content_dir="",
    )
    chapter_configs = build_chapter_configs(runtime.chapter_overrides)
    commits = _make_commits()

    system_a = ChapterSystem(rng=create_rng(42), chapter_configs=chapter_configs)
    chapters_a = system_a.parse_chapters(commits)
    snapshot_a = [(chapter.chapter_type.value, chapter.name, chapter.is_boss_chapter) for chapter in chapters_a]

    system_b = ChapterSystem(rng=create_rng(42), chapter_configs=chapter_configs)
    chapters_b = system_b.parse_chapters(commits)
    snapshot_b = [(chapter.chapter_type.value, chapter.name, chapter.is_boss_chapter) for chapter in chapters_b]

    assert snapshot_a == snapshot_b
