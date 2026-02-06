"""Unit tests for deterministic chapter node generation."""

from __future__ import annotations

from git_dungeon.engine.node_flow import ChapterNodeGenerator, summarize_node_kinds
from git_dungeon.engine.route import NodeKind


def test_node_generator_is_deterministic_for_same_seed() -> None:
    gen = ChapterNodeGenerator()
    nodes_a = gen.build_nodes(
        seed=123,
        chapter_index=2,
        chapter_enemy_count=8,
        difficulty=1.0,
        has_boss=True,
        has_events=True,
    )
    nodes_b = gen.build_nodes(
        seed=123,
        chapter_index=2,
        chapter_enemy_count=8,
        difficulty=1.0,
        has_boss=True,
        has_events=True,
    )

    assert [node.kind.value for node in nodes_a] == [node.kind.value for node in nodes_b]
    assert [node.node_id for node in nodes_a] == [node.node_id for node in nodes_b]


def test_node_generator_has_event_and_boss_tail() -> None:
    gen = ChapterNodeGenerator()
    nodes = gen.build_nodes(
        seed=7,
        chapter_index=0,
        chapter_enemy_count=6,
        difficulty=1.0,
        has_boss=True,
        has_events=True,
    )
    counts = summarize_node_kinds(nodes)

    assert nodes[-1].kind == NodeKind.BOSS
    assert counts.get("event", 0) >= 1
    assert counts.get("battle", 0) >= 1
    assert counts.get("rest", 0) >= 1
    assert counts.get("shop", 0) >= 1
