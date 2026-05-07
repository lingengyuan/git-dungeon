"""Phase 10 tests for optional dungeon reward rooms."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

from git_dungeon.engine.route import NodeKind, RouteNode
from git_dungeon.ui_pixel.dungeon import build_dungeon_floor
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
    hp: int = 80
    gold: int = 0
    dungeon_player_coord: tuple[int, int] | None = None
    claimed_rewards: set[str] = field(default_factory=set)

    def route_nodes(self) -> tuple[NodeSnapshot, ...]:
        return self.nodes

    def player_snapshot(self) -> PlayerSnapshot:
        return PlayerSnapshot(hp=self.hp, max_hp=100, mp=50, max_mp=50, attack=12, gold=self.gold)

    def current_node_snapshot(self) -> NodeSnapshot | None:
        return next((node for node in self.nodes if node.is_current), None)

    def current_node(self) -> RouteNode:
        current = self.current_node_snapshot()
        assert current is not None
        return RouteNode(node_id=current.node_id, kind=NodeKind.REST, position=current.position)

    def is_dungeon_reward_claimed(self, reward_id: str) -> bool:
        return reward_id in self.claimed_rewards

    def claim_dungeon_reward(
        self, reward_id: str, heal: int, gold: int, key_id: str | None = None
    ) -> Any:
        if reward_id in self.claimed_rewards:
            return SimpleNamespace(reward_id=reward_id, heal=0, gold=0, already_claimed=True)
        actual_heal = min(heal, 100 - self.hp)
        self.hp += actual_heal
        self.gold += gold
        self.claimed_rewards.add(reward_id)
        return SimpleNamespace(
            reward_id=reward_id,
            heal=actual_heal,
            gold=gold,
            already_claimed=False,
        )


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


def _nodes() -> tuple[NodeSnapshot, ...]:
    return (
        _node(0, "battle", visited=True),
        _node(1, "event", visited=True),
        _node(2, "rest", current=True),
    )


def _key(key: str) -> Any:
    return SimpleNamespace(type=FakePygame.KEYDOWN, key=key)


def test_dungeon_floor_adds_optional_reward_room_branch() -> None:
    floor = build_dungeon_floor(_nodes())
    reward = floor.reward_rooms[0]

    assert reward.reward_id == "cache_00"
    assert reward.coord == (2, 1)
    assert reward.anchor == (2, 2)
    assert floor.has_door(reward.anchor, reward.coord)
    assert floor.room_at(reward.coord) == reward
    assert floor.trap_at(reward.coord) is None


def test_dungeon_reward_room_can_be_claimed_once_and_return_to_route() -> None:
    runner = FakeRunner(_nodes())
    screen = DungeonScreen(FakePygame, fonts=None, runner=runner, assets=None)

    assert screen.handle(_key(FakePygame.K_RIGHT)) is None
    assert screen.player_coord == (2, 2)
    assert screen.handle(_key(FakePygame.K_UP)) is None
    assert screen.player_coord == (2, 1)
    assert screen.message == "Press Enter to claim"

    assert screen.handle(_key(FakePygame.K_RETURN)) is None

    assert runner.hp == 92
    assert runner.gold == 15
    assert runner.claimed_rewards == {"cache_00"}
    assert screen.message == "Cache: +12 Health +15 Gold"

    assert screen.handle(_key(FakePygame.K_RETURN)) is None

    assert runner.hp == 92
    assert runner.gold == 15
    assert screen.message == "Cache already claimed"

    assert screen.handle(_key(FakePygame.K_DOWN)) is None
    assert screen.player_coord == (2, 2)
    assert screen.handle(_key(FakePygame.K_RIGHT)) is None
    assert screen.player_coord == (3, 2)
    assert screen.message == "Press Enter to enter"
