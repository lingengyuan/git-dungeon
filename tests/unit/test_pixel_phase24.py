"""Phase 24 tests for room identity and content polish."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from git_dungeon.ui_pixel.screens.dungeon import DungeonScreen
from git_dungeon.ui_pixel.text import room_description, room_title, tr


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


class FakeRunner:
    dungeon_player_coord: tuple[int, int] | None = None

    def route_nodes(self) -> tuple[Any, ...]:
        return (
            SimpleNamespace(
                node_id="n0",
                kind="battle",
                position=0,
                is_current=False,
                is_visited=True,
                is_playable_now=False,
            ),
            SimpleNamespace(
                node_id="n1",
                kind="event",
                position=1,
                is_current=True,
                is_visited=False,
                is_playable_now=True,
            ),
        )

    def current_node_snapshot(self) -> Any:
        return self.route_nodes()[1]

    def player_snapshot(self) -> Any:
        return SimpleNamespace(hp=80, max_hp=100, mp=40, max_mp=50, attack=12, gold=60)

    def recent_run_events(self, _limit: int = 4) -> tuple[Any, ...]:
        return ()

    def chapter_summary_snapshot(self) -> Any:
        return SimpleNamespace(cleared_rooms=1, total_rooms=2)


def test_room_identity_copy_is_localized() -> None:
    assert room_title("battle", "zh_CN") == "战斗房"
    assert room_description("shop", "zh_CN") == "花金币补给后继续前进"
    assert tr("Cache opened", "zh_CN") == "补给已开启"
    assert tr("Vault opened", "zh_CN") == "宝库已开启"


def test_hovered_route_room_explains_what_happens() -> None:
    screen = DungeonScreen(
        FakePygame,
        fonts=None,
        runner=FakeRunner(),
        assets=None,
        settings=SimpleNamespace(lang="zh_CN"),
    )
    screen.hover_pos = (20 + 2 * 18 + 8, 62 + 2 * 18 + 8)

    assert screen._action_hint() == "事件房: 选择一次地牢遭遇"
