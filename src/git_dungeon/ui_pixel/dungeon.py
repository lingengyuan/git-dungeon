"""Deterministic room layout for the pixel dungeon layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


Coord = tuple[int, int]

PATH_COORDS: tuple[Coord, ...] = (
    (1, 2),
    (2, 2),
    (3, 2),
    (4, 2),
    (5, 2),
    (6, 2),
    (7, 2),
    (8, 2),
    (8, 3),
    (7, 3),
    (6, 3),
    (5, 3),
)
GRID_WIDTH = 10
GRID_HEIGHT = 5


@dataclass(frozen=True)
class DungeonRoom:
    node_id: str
    kind: str
    position: int
    coord: Coord
    is_current: bool
    is_visited: bool
    is_playable_now: bool


@dataclass(frozen=True)
class DungeonRewardRoom:
    reward_id: str
    coord: Coord
    anchor: Coord
    label: str = "Cache"
    heal: int = 12
    gold: int = 15


@dataclass(frozen=True)
class DungeonTrap:
    trap_id: str
    coord: Coord
    label: str = "Trap"
    damage: int = 8


@dataclass(frozen=True)
class DungeonFloor:
    rooms: tuple[DungeonRoom, ...]
    reward_rooms: tuple[DungeonRewardRoom, ...]
    traps: tuple[DungeonTrap, ...]
    doors: frozenset[tuple[Coord, Coord]]
    start_coord: Coord | None
    current_coord: Coord | None

    def room_at(self, coord: Coord) -> DungeonRoom | DungeonRewardRoom | None:
        route_room = next((room for room in self.rooms if room.coord == coord), None)
        if route_room is not None:
            return route_room
        return self.reward_at(coord)

    def reward_at(self, coord: Coord) -> DungeonRewardRoom | None:
        return next((reward for reward in self.reward_rooms if reward.coord == coord), None)

    def trap_at(self, coord: Coord) -> DungeonTrap | None:
        return next((trap for trap in self.traps if trap.coord == coord), None)

    def has_door(self, left: Coord, right: Coord) -> bool:
        return _door_key(left, right) in self.doors


def build_dungeon_floor(nodes: Iterable[object]) -> DungeonFloor:
    """Build a compact room path from route node snapshots."""
    snapshots = tuple(nodes)
    rooms = tuple(
        DungeonRoom(
            node_id=str(getattr(node, "node_id")),
            kind=str(getattr(node, "kind")),
            position=int(getattr(node, "position")),
            coord=_coord_for_index(index),
            is_current=bool(getattr(node, "is_current")),
            is_visited=bool(getattr(node, "is_visited")),
            is_playable_now=bool(getattr(node, "is_playable_now")),
        )
        for index, node in enumerate(snapshots)
    )
    reward_rooms = tuple(_reward_rooms_for_rooms(rooms))
    route_doors = {
        _door_key(rooms[index].coord, rooms[index + 1].coord)
        for index in range(max(0, len(rooms) - 1))
    }
    reward_doors = {_door_key(reward.anchor, reward.coord) for reward in reward_rooms}
    doors = frozenset(route_doors.union(reward_doors))
    current_room = next((room for room in rooms if room.is_current), None)
    first_room = rooms[0] if rooms else None
    trap_coords = _trap_coords_for_rooms(rooms, reward_rooms)
    traps = tuple(
        DungeonTrap(trap_id=f"trap_{index:02d}", coord=coord)
        for index, coord in enumerate(trap_coords)
    )
    return DungeonFloor(
        rooms=rooms,
        reward_rooms=reward_rooms,
        traps=traps,
        doors=doors,
        start_coord=first_room.coord if first_room else None,
        current_coord=current_room.coord if current_room else first_room.coord if first_room else None,
    )


def _coord_for_index(index: int) -> Coord:
    if index < len(PATH_COORDS):
        return PATH_COORDS[index]
    x = 1 + index % (GRID_WIDTH - 2)
    y = 1 + (index // (GRID_WIDTH - 2)) % (GRID_HEIGHT - 2)
    return (x, y)


def _reward_rooms_for_rooms(rooms: tuple[DungeonRoom, ...]) -> list[DungeonRewardRoom]:
    if len(rooms) < 2:
        return []
    occupied = {room.coord for room in rooms}
    anchor = rooms[1].coord
    for offset in ((0, -1), (0, 1), (1, 0), (-1, 0)):
        candidate = (anchor[0] + offset[0], anchor[1] + offset[1])
        if 0 <= candidate[0] < GRID_WIDTH and 0 <= candidate[1] < GRID_HEIGHT and candidate not in occupied:
            return [DungeonRewardRoom(reward_id="cache_00", coord=candidate, anchor=anchor)]
    return []


def _trap_coords_for_rooms(
    rooms: tuple[DungeonRoom, ...],
    reward_rooms: tuple[DungeonRewardRoom, ...] = (),
) -> list[Coord]:
    occupied = {room.coord for room in rooms}
    occupied.update(reward.coord for reward in reward_rooms)
    traps: list[Coord] = []
    for index, room in enumerate(rooms):
        if index % 3 != 2:
            continue
        for offset in ((0, -1), (0, 1), (1, 0), (-1, 0)):
            candidate = (room.coord[0] + offset[0], room.coord[1] + offset[1])
            if (
                0 <= candidate[0] < GRID_WIDTH
                and 0 <= candidate[1] < GRID_HEIGHT
                and candidate not in occupied
                and candidate not in traps
            ):
                traps.append(candidate)
                break
    return traps


def _door_key(left: Coord, right: Coord) -> tuple[Coord, Coord]:
    return (left, right) if left <= right else (right, left)
