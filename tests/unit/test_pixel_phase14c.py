"""Phase 14C tests for tile-based dungeon scene rendering."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from git_dungeon.ui_pixel.game_runner import NodeSnapshot, PlayerSnapshot
from git_dungeon.ui_pixel.screens.dungeon import FLOOR_TILE, FLOOR_ORIGIN, DungeonScreen


class FakeDraw:
    @staticmethod
    def rect(*_args: Any, **_kwargs: Any) -> None:
        return None

    @staticmethod
    def line(*_args: Any, **_kwargs: Any) -> None:
        return None

    @staticmethod
    def circle(*_args: Any, **_kwargs: Any) -> None:
        return None


class FakeFonts:
    @staticmethod
    def draw(*_args: Any, **_kwargs: Any) -> None:
        return None

    @staticmethod
    def draw_fit(*_args: Any, **_kwargs: Any) -> None:
        return None

    @staticmethod
    def measure(text: str, _size: int) -> int:
        return len(text) * 6

    @staticmethod
    def fit(text: str, _max_width: int, _size: int) -> str:
        return text


class FakeSurface:
    @staticmethod
    def fill(*_args: Any, **_kwargs: Any) -> None:
        return None


class RecordingAssets:
    def __init__(self) -> None:
        self.drawn: list[str] = []

    def draw(self, _surface: Any, sprite_id: str, _rect: tuple[int, int, int, int]) -> None:
        self.drawn.append(sprite_id)


class FakeRunner:
    def __init__(
        self,
        *,
        claimed_rewards: set[str] | None = None,
        collected_keys: set[str] | None = None,
        consumed_traps: set[str] | None = None,
    ) -> None:
        self.dungeon_player_coord: tuple[int, int] | None = None
        self.claimed_rewards = claimed_rewards or set()
        self.collected_keys = collected_keys or set()
        self.consumed_traps = consumed_traps or set()
        self.nodes = (
            NodeSnapshot("n0", "battle", 0, "Battle", False, True, False),
            NodeSnapshot("n1", "event", 1, "Event", False, True, False),
            NodeSnapshot("n2", "rest", 2, "Rest", True, False, True),
            NodeSnapshot("n3", "shop", 3, "Shop", False, False, False),
            NodeSnapshot("n4", "boss", 4, "Boss", False, False, False),
        )

    def route_nodes(self) -> tuple[NodeSnapshot, ...]:
        return self.nodes

    def player_snapshot(self) -> PlayerSnapshot:
        return PlayerSnapshot(hp=80, max_hp=100, mp=40, max_mp=50, attack=12, gold=60)

    def current_node_snapshot(self) -> NodeSnapshot:
        return self.nodes[2]

    def is_dungeon_reward_claimed(self, reward_id: str) -> bool:
        return reward_id in self.claimed_rewards

    def has_dungeon_key(self, key_id: str) -> bool:
        return key_id in self.collected_keys

    def is_dungeon_trap_consumed(self, trap_id: str) -> bool:
        return trap_id in self.consumed_traps


def _screen(
    *,
    runner: FakeRunner | None = None,
    assets: RecordingAssets | None = None,
    lang: str = "zh_CN",
) -> DungeonScreen:
    return DungeonScreen(
        SimpleNamespace(draw=FakeDraw()),
        FakeFonts(),
        runner or FakeRunner(),
        assets or RecordingAssets(),
        settings=SimpleNamespace(lang=lang),
    )


def test_dungeon_draw_uses_phase14b_tile_scene_sprites() -> None:
    assets = RecordingAssets()
    screen = _screen(assets=assets)

    screen.draw(FakeSurface())

    drawn = set(assets.drawn)
    assert "tile_wall_stone" in drawn
    assert "tile_floor_stone" in drawn
    assert "tile_corridor" in drawn
    assert "door_open" in drawn
    assert "trap_spikes_armed" in drawn
    assert "chest_closed" in drawn
    assert "key_iron" in drawn
    assert "vault_locked" in drawn
    assert "room_marker_current" in drawn
    assert "boss_gate" in drawn


def test_claimed_rewards_draw_open_state_sprites() -> None:
    assets = RecordingAssets()
    runner = FakeRunner(
        claimed_rewards={"cache_00", "iron_key_00", "vault_00"},
        collected_keys={"iron_key"},
    )
    screen = _screen(runner=runner, assets=assets)

    screen.draw(FakeSurface())

    assert "chest_open" in assets.drawn
    assert "vault_open" in assets.drawn


def test_hovering_trap_shows_expected_health_loss() -> None:
    screen = _screen()
    trap = screen.floor.traps[0]
    screen.hover_pos = (
        FLOOR_ORIGIN[0] + trap.coord[0] * FLOOR_TILE + 2,
        FLOOR_ORIGIN[1] + trap.coord[1] * FLOOR_TILE + 2,
    )

    assert screen._action_hint() == "陷阱: 生命 -8"
