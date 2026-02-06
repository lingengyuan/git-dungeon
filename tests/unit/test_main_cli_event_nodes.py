"""Unit tests for deterministic event-node selection and auto decisions."""

from __future__ import annotations

from types import SimpleNamespace

from git_dungeon.content.schema import EventChoice, EventDef, EventEffect
from git_dungeon.engine import GameState
from git_dungeon.engine.route import NodeKind, NodeTag, RouteNode
from git_dungeon.main_cli import GitDungeonCLI


def _event(event_id: str, route_tags: list[str], heal: int, damage: int = 0) -> EventDef:
    effects = [EventEffect(opcode="heal", value=heal)]
    if damage:
        effects.append(EventEffect(opcode="take_damage", value=damage))
    return EventDef(
        id=event_id,
        name_key=f"event.{event_id}.name",
        desc_key=f"event.{event_id}.desc",
        route_tags=route_tags,
        weights={"default": 10},
        choices=[
            EventChoice(id="safe", text_key=f"event.{event_id}.choice.safe", effects=[EventEffect(opcode="heal", value=10)]),
            EventChoice(id="risk", text_key=f"event.{event_id}.choice.risk", effects=effects),
        ],
    )


def test_event_node_selection_and_choice_are_deterministic() -> None:
    cli = GitDungeonCLI(seed=77, auto_mode=True, compact=True)
    cli.state = GameState(seed=77, repo_path=".", total_commits=1, current_commit_index=0, difficulty="normal")
    cli.state.player.character.current_hp = 18
    cli.state.player.gold = 10

    cli.content_runtime.registry.events = {
        "safe_event": _event("safe_event", ["safe"], heal=8),
        "risk_event": _event("risk_event", ["risk"], heal=0, damage=9),
    }

    chapter = SimpleNamespace(
        chapter_id="chapter_0",
        chapter_index=0,
        chapter_type=SimpleNamespace(value="feature"),
        commits=[SimpleNamespace(hexsha="a" * 40, message="feat: start", total_changes=3)],
    )
    node = RouteNode("ch0_node1_event", NodeKind.EVENT, 1, [NodeTag.SAFE], {})

    first = cli._select_event_for_node(chapter, node)
    second = cli._select_event_for_node(chapter, node)

    assert first.id == second.id

    idx_1 = cli._choose_event_choice(chapter, node, first)
    idx_2 = cli._choose_event_choice(chapter, node, first)
    assert idx_1 == idx_2
