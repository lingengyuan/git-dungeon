"""Phase 9 tests for dungeon trap consumption."""

from __future__ import annotations

from dataclasses import dataclass, field
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
    hp: int = 100
    dungeon_player_coord: tuple[int, int] | None = None
    consumed_traps: set[str] = field(default_factory=set)

    def route_nodes(self) -> tuple[NodeSnapshot, ...]:
        return self.nodes

    def player_snapshot(self) -> PlayerSnapshot:
        return PlayerSnapshot(hp=self.hp, max_hp=100, mp=50, max_mp=50, attack=12, gold=0)

    def current_node_snapshot(self) -> NodeSnapshot | None:
        return next((node for node in self.nodes if node.is_current), None)

    def current_node(self) -> RouteNode:
        current = self.current_node_snapshot()
        assert current is not None
        return RouteNode(node_id=current.node_id, kind=NodeKind.REST, position=current.position)

    def is_dungeon_trap_consumed(self, trap_id: str) -> bool:
        return trap_id in self.consumed_traps

    def trigger_dungeon_trap(self, trap_id: str, damage: int) -> Any:
        if trap_id in self.consumed_traps:
            return SimpleNamespace(trap_id=trap_id, damage=0, already_triggered=True)
        actual_damage = min(damage, max(0, self.hp))
        self.hp -= actual_damage
        self.consumed_traps.add(trap_id)
        return SimpleNamespace(trap_id=trap_id, damage=actual_damage, already_triggered=False)


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


def _screen_for_trap(hp: int = 100) -> tuple[DungeonScreen, FakeRunner]:
    runner = FakeRunner(
        (
            _node(0, "battle", visited=True),
            _node(1, "event", visited=True),
            _node(2, "rest", current=True),
        ),
        hp=hp,
        dungeon_player_coord=(3, 2),
    )
    return DungeonScreen(FakePygame, fonts=None, runner=runner, assets=None), runner


def test_dungeon_trap_consumes_hp_once() -> None:
    screen, runner = _screen_for_trap()

    assert screen.handle(_key(FakePygame.K_UP)) is None

    assert runner.hp == 92
    assert runner.consumed_traps == {"trap_00"}
    assert screen.player_coord == (3, 2)
    assert screen.message == "Trap hit: Health -8"

    assert screen.handle(_key(FakePygame.K_UP)) is None

    assert runner.hp == 92
    assert screen.message == "Trap already spent"


def test_dungeon_trap_can_defeat_player_at_low_hp() -> None:
    screen, runner = _screen_for_trap(hp=5)

    action = screen.handle(_key(FakePygame.K_UP))

    assert runner.hp == 0
    assert action is not None
    assert action.kind == "replace"
    assert action.screen.__class__.__name__ == "GameOverScreen"
    assert action.screen.won is False
    assert action.screen.message == "Trap defeated you"


def test_dungeon_trap_defeats_player_at_one_hp() -> None:
    screen, runner = _screen_for_trap(hp=1)

    action = screen.handle(_key(FakePygame.K_UP))

    assert runner.hp == 0
    assert action is not None
    assert action.kind == "replace"
    assert action.screen.__class__.__name__ == "GameOverScreen"
