"""Phase 8 tests for dungeon screen input replay."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

from git_dungeon.engine.route import NodeKind, RouteNode
from git_dungeon.ui_pixel.game_runner import NodeSnapshot, PlayerSnapshot
from git_dungeon.ui_pixel.screens.dungeon import DungeonScreen


class FakePygame:
    KEYDOWN = "keydown"
    MOUSEMOTION = "mousemotion"
    MOUSEBUTTONDOWN = "mousebuttondown"
    K_ESCAPE = "escape"
    K_q = "q"
    K_RETURN = "return"
    K_SPACE = "space"
    K_LEFT = "left"
    K_a = "a"
    K_RIGHT = "right"
    K_d = "d"
    K_UP = "up"
    K_w = "w"
    K_DOWN = "down"
    K_s = "s"


@dataclass
class FakeRunner:
    nodes: tuple[NodeSnapshot, ...]
    current_kind: NodeKind = NodeKind.REST
    dungeon_player_coord: tuple[int, int] | None = None

    def route_nodes(self) -> tuple[NodeSnapshot, ...]:
        return self.nodes

    def player_snapshot(self) -> PlayerSnapshot:
        return PlayerSnapshot(hp=100, max_hp=100, mp=50, max_mp=50, attack=12, gold=0)

    def current_node_snapshot(self) -> NodeSnapshot | None:
        return next((node for node in self.nodes if node.is_current), None)

    def current_node(self) -> RouteNode:
        current = self.current_node_snapshot()
        assert current is not None
        return RouteNode(node_id=current.node_id, kind=self.current_kind, position=current.position)


def _node(index: int, kind: str, *, current: bool = False, visited: bool = False) -> NodeSnapshot:
    return NodeSnapshot(
        node_id=f"node_{index}",
        kind=kind,
        position=index,
        label=f"{index} {kind}",
        is_current=current,
        is_visited=visited,
        is_playable_now=current,
    )


def _key(key: str) -> Any:
    return SimpleNamespace(type=FakePygame.KEYDOWN, key=key)


def test_dungeon_screen_replays_move_to_current_room_and_enter_node() -> None:
    runner = FakeRunner(
        (
            _node(0, "battle", visited=True),
            _node(1, "rest", current=True),
            _node(2, "battle"),
        )
    )
    screen = DungeonScreen(FakePygame, fonts=None, runner=runner, assets=None)

    assert screen.player_coord == (1, 2)
    assert screen.message == "Move to the current room"
    assert screen.handle(_key(FakePygame.K_RETURN)) is None
    assert screen.message == "Move to the current room"

    assert screen.handle(_key(FakePygame.K_RIGHT)) is None

    assert screen.player_coord == (2, 2)
    assert runner.dungeon_player_coord == (2, 2)
    assert screen.message == "Press Enter to enter"

    action = screen.handle(_key(FakePygame.K_RETURN))

    assert action is not None
    assert action.kind == "replace"
    assert action.screen.__class__.__name__ == "RestScreen"


def test_dungeon_screen_rejects_trap_before_door_check() -> None:
    runner = FakeRunner(
        (
            _node(0, "battle", visited=True),
            _node(1, "event", visited=True),
            _node(2, "rest", current=True),
        ),
        dungeon_player_coord=(3, 2),
    )
    screen = DungeonScreen(FakePygame, fonts=None, runner=runner, assets=None)

    assert screen.player_coord == (3, 2)
    assert screen.floor.trap_at((3, 1)) is not None

    assert screen.handle(_key(FakePygame.K_UP)) is None

    assert screen.player_coord == (3, 2)
    assert runner.dungeon_player_coord == (3, 2)
    assert screen.message == "Trap blocks this path"


def test_dungeon_screen_reuses_previous_player_room_after_node_resolution() -> None:
    runner = FakeRunner(
        (
            _node(0, "battle", visited=True),
            _node(1, "event", visited=True),
            _node(2, "rest", current=True),
        ),
        dungeon_player_coord=(2, 2),
    )
    screen = DungeonScreen(FakePygame, fonts=None, runner=runner, assets=None)

    assert screen.player_coord == (2, 2)
    assert screen.message == "Move to the current room"
