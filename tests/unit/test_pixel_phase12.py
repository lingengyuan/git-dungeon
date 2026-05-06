"""Phase 12 tests for keyed dungeon side rooms."""

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
    hp: int = 70
    gold: int = 0
    dungeon_player_coord: tuple[int, int] | None = None
    claimed_rewards: set[str] = field(default_factory=set)
    collected_keys: set[str] = field(default_factory=set)

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

    def has_dungeon_key(self, key_id: str) -> bool:
        return key_id in self.collected_keys

    def claim_dungeon_reward(self, reward_id: str, heal: int, gold: int, key_id: str | None = None) -> Any:
        if reward_id in self.claimed_rewards:
            return SimpleNamespace(reward_id=reward_id, heal=0, gold=0, key_id=None, already_claimed=True)
        actual_heal = min(heal, 100 - self.hp)
        self.hp += actual_heal
        self.gold += gold
        if key_id is not None:
            self.collected_keys.add(key_id)
        self.claimed_rewards.add(reward_id)
        return SimpleNamespace(
            reward_id=reward_id,
            heal=actual_heal,
            gold=gold,
            key_id=key_id,
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
    return tuple(_node(index, "battle", current=index == 5, visited=index < 5) for index in range(6))


def _key(key: str) -> Any:
    return SimpleNamespace(type=FakePygame.KEYDOWN, key=key)


def test_dungeon_floor_adds_key_room_and_locked_vault() -> None:
    floor = build_dungeon_floor(_nodes())
    rewards = {reward.reward_id: reward for reward in floor.reward_rooms}

    assert rewards["iron_key_00"].coord == (4, 1)
    assert rewards["iron_key_00"].anchor == (4, 2)
    assert rewards["iron_key_00"].grants_key == "iron_key"
    assert rewards["vault_00"].coord == (5, 1)
    assert rewards["vault_00"].anchor == (5, 2)
    assert rewards["vault_00"].requires_key == "iron_key"
    assert floor.has_door((4, 2), (4, 1))
    assert floor.has_door((5, 2), (5, 1))
    assert floor.trap_at((4, 1)) is None
    assert floor.trap_at((5, 1)) is None


def test_vault_requires_key_before_reward_can_be_claimed_once() -> None:
    runner = FakeRunner(_nodes())
    screen = DungeonScreen(FakePygame, fonts=None, runner=runner, assets=None)

    for key in (FakePygame.K_RIGHT, FakePygame.K_RIGHT, FakePygame.K_RIGHT, FakePygame.K_RIGHT):
        assert screen.handle(_key(key)) is None
    assert screen.player_coord == (5, 2)

    assert screen.handle(_key(FakePygame.K_UP)) is None

    assert screen.player_coord == (5, 2)
    assert screen.message == "Locked: need iron_key"
    assert runner.gold == 0

    assert screen.handle(_key(FakePygame.K_LEFT)) is None
    assert screen.player_coord == (4, 2)
    assert screen.handle(_key(FakePygame.K_UP)) is None
    assert screen.player_coord == (4, 1)
    assert screen.message == "Press Enter to claim"

    assert screen.handle(_key(FakePygame.K_RETURN)) is None

    assert runner.collected_keys == {"iron_key"}
    assert screen.message == "Key found: iron_key"

    assert screen.handle(_key(FakePygame.K_DOWN)) is None
    assert screen.handle(_key(FakePygame.K_RIGHT)) is None
    assert screen.handle(_key(FakePygame.K_UP)) is None
    assert screen.player_coord == (5, 1)
    assert screen.message == "Press Enter to claim"

    assert screen.handle(_key(FakePygame.K_RETURN)) is None

    assert runner.hp == 78
    assert runner.gold == 30
    assert screen.message == "Vault: +8 HP +30 Gold"

    assert screen.handle(_key(FakePygame.K_RETURN)) is None

    assert runner.hp == 78
    assert runner.gold == 30
    assert screen.message == "Vault already claimed"
