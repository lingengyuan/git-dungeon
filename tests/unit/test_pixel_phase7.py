"""Phase 7 tests for dungeon room layout."""

from __future__ import annotations

from git_dungeon.ui_pixel.dungeon import build_dungeon_floor
from git_dungeon.ui_pixel.game_runner import NodeSnapshot


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


def test_dungeon_floor_keeps_route_order_and_current_room() -> None:
    floor = build_dungeon_floor(
        [
            _node(0, "battle", visited=True),
            _node(1, "event", current=True),
            _node(2, "rest"),
        ]
    )

    assert [room.node_id for room in floor.rooms] == ["node_0", "node_1", "node_2"]
    assert floor.start_coord == floor.rooms[0].coord
    assert floor.current_coord == floor.rooms[1].coord
    assert floor.has_door(floor.rooms[0].coord, floor.rooms[1].coord)
    assert floor.has_door(floor.rooms[1].coord, floor.rooms[2].coord)


def test_dungeon_floor_adds_visible_traps_off_main_path() -> None:
    floor = build_dungeon_floor([_node(index, "battle", current=index == 0) for index in range(6)])

    room_coords = {room.coord for room in floor.rooms}
    assert floor.traps
    assert all(trap.coord not in room_coords for trap in floor.traps)


def test_dungeon_floor_uses_unique_room_coords_for_long_route() -> None:
    floor = build_dungeon_floor([_node(index, "battle", current=index == 0) for index in range(12)])

    coords = [room.coord for room in floor.rooms]
    assert len(coords) == len(set(coords))
