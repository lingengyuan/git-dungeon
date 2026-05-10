"""Phase 11 tests for removing the legacy pixel route map."""

from __future__ import annotations

import importlib.util
from types import SimpleNamespace
from typing import Any

from git_dungeon.ui_pixel.game_runner import NodeSnapshot
from git_dungeon.ui_pixel.screens.dungeon import DungeonScreen
from git_dungeon.ui_pixel.screens.title import LoadingScreen


class FakePygame:
    KEYDOWN = "keydown"
    K_ESCAPE = "escape"
    K_q = "q"
    K_RETURN = "return"


class FakeRunner:
    def __init__(self) -> None:
        self.loaded = False
        self.dungeon_player_coord: tuple[int, int] | None = None

    def load_repository(self) -> Any:
        self.loaded = True
        return SimpleNamespace(total_commits=1, chapter_count=1, seed=42)

    def route_nodes(self) -> tuple[NodeSnapshot, ...]:
        return (
            NodeSnapshot(
                node_id="node_0",
                kind="battle",
                position=0,
                label="01 BATTLE",
                is_current=True,
                is_visited=False,
                is_playable_now=True,
            ),
        )

    def current_node_snapshot(self) -> NodeSnapshot | None:
        return self.route_nodes()[0]


def test_legacy_map_screen_module_is_removed() -> None:
    assert importlib.util.find_spec("git_dungeon.ui_pixel.screens.map") is None


def test_loading_screen_enters_dungeon_screen() -> None:
    runner = FakeRunner()
    loading = LoadingScreen(FakePygame, fonts=None, runner=runner, assets=None)

    assert loading.update(0.0) is None
    action = None
    for _ in range(20):
        action = loading.update(0.016)
        if action is not None:
            break

    assert runner.loaded is True
    assert action is not None
    assert action.kind == "replace"
    assert isinstance(action.screen, DungeonScreen)
