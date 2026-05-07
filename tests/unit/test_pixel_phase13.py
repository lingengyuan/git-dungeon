"""Phase 13 tests for pixel readability and safe in-run controls."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

from git_dungeon.ui_pixel.app import WINDOW_SIZE
from git_dungeon.ui_pixel.game_runner import NodeSnapshot, PlayerSnapshot
from git_dungeon.ui_pixel.screens.dungeon import DungeonScreen
from git_dungeon.ui_pixel.screens.event import EventScreen
from git_dungeon.ui_pixel.screens.pause import PauseScreen
from git_dungeon.ui_pixel.screens.rest import RestScreen
from git_dungeon.ui_pixel.screens.shop import ShopScreen
from git_dungeon.ui_pixel.text import (
    audio_label,
    battle_reward_feedback,
    event_choice_label,
    event_effect_preview,
    event_result_feedback,
    event_title,
    locked_message,
    reward_feedback,
    stat_label,
    tr,
)


class FakePygame:
    KEYDOWN = "keydown"
    MOUSEMOTION = "mousemotion"
    MOUSEBUTTONDOWN = "mousebuttondown"
    K_ESCAPE = "escape"
    K_q = "q"
    K_RETURN = "return"
    K_SPACE = "space"
    K_0 = "0"
    K_1 = "1"
    K_2 = "2"
    K_3 = "3"
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
    collected_keys: set[str] = field(default_factory=set)

    def route_nodes(self) -> tuple[NodeSnapshot, ...]:
        return self.nodes

    def player_snapshot(self) -> PlayerSnapshot:
        return PlayerSnapshot(hp=self.hp, max_hp=100, mp=50, max_mp=50, attack=12, gold=self.gold)

    def current_node_snapshot(self) -> NodeSnapshot | None:
        return next((node for node in self.nodes if node.is_current), None)

    def event_for_node(self) -> Any:
        return SimpleNamespace(
            event_id="debug_event_id",
            choices=(
                SimpleNamespace(index=0, choice_id="raw_choice_id", effects=("heal", "gain_gold")),
                SimpleNamespace(index=1, choice_id="risky_choice_id", effects=("take_damage",)),
            ),
        )

    def rest_options(self) -> tuple[Any, ...]:
        return ()

    def shop_offers(self) -> tuple[Any, ...]:
        return ()

    def is_dungeon_reward_claimed(self, reward_id: str) -> bool:
        return reward_id in self.claimed_rewards

    def has_dungeon_key(self, key_id: str) -> bool:
        return key_id in self.collected_keys

    def claim_dungeon_reward(
        self, reward_id: str, heal: int, gold: int, key_id: str | None = None
    ) -> Any:
        if reward_id in self.claimed_rewards:
            return SimpleNamespace(
                reward_id=reward_id, heal=0, gold=0, key_id=None, already_claimed=True
            )
        self.claimed_rewards.add(reward_id)
        if key_id:
            self.collected_keys.add(key_id)
        self.hp = min(100, self.hp + heal)
        self.gold += gold
        return SimpleNamespace(
            reward_id=reward_id,
            heal=heal,
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
    return (
        _node(0, "battle", visited=True),
        _node(1, "event", visited=True),
        _node(2, "rest", current=True),
        _node(3, "shop"),
        _node(4, "battle"),
    )


def _key(key: str) -> Any:
    return SimpleNamespace(type=FakePygame.KEYDOWN, key=key)


def _click(pos: tuple[int, int]) -> Any:
    return SimpleNamespace(type=FakePygame.MOUSEBUTTONDOWN, button=1, logical_pos=pos)


def test_default_window_is_desktop_safe_scale() -> None:
    assert WINDOW_SIZE == (960, 540)


def test_normal_audio_slot_label_is_hidden_but_muted_state_remains_visible() -> None:
    assert audio_label("Audio: chapter", "zh_CN") == ""
    assert audio_label("Audio muted: device unavailable", "zh_CN").startswith("音频静音")


def test_chinese_player_facing_terms_do_not_expose_raw_stat_abbreviations() -> None:
    assert stat_label("hp", "zh_CN") == "生命"
    assert stat_label("mp", "zh_CN") == "魔力"
    assert stat_label("attack", "zh_CN") == "攻击"
    assert reward_feedback("Cache", 12, 15, "zh_CN") == "补给：+12 生命 +15 金币"
    assert locked_message("iron_key", "zh_CN") == "锁住了：需要铁钥匙"
    assert tr("Trap hit: -10 HP", "zh_CN") == "触发陷阱: -10 生命"
    battle_reward = battle_reward_feedback(12, 15, "zh_CN")
    assert "经验" in battle_reward
    assert "金币" in battle_reward
    assert "EXP" not in battle_reward
    assert "Gold" not in battle_reward


def test_event_player_facing_terms_do_not_expose_raw_ids_or_stat_abbreviations() -> None:
    assert event_title("debug_event_id", "zh_CN") == "地牢事件"
    assert "debug_event_id" not in event_title("debug_event_id", "zh_CN")
    assert "raw_choice_id" not in event_choice_label(0, ("heal", "gain_gold"), "zh_CN")
    assert "heal" not in event_effect_preview(("heal", "gain_gold"), "zh_CN")
    result = event_result_feedback(-5, 12, "zh_CN")
    assert "生命 -5" in result
    assert "金币 +12" in result
    assert "HP" not in result
    assert "Gold" not in result


def test_escape_pushes_pause_screen_instead_of_quitting_run() -> None:
    screen = DungeonScreen(FakePygame, fonts=None, runner=FakeRunner(_nodes()), assets=None)

    action = screen.handle(_key(FakePygame.K_ESCAPE))

    assert action is not None
    assert action.kind == "push"
    assert isinstance(action.screen, PauseScreen)


def test_pause_quit_requires_second_confirmation() -> None:
    pause = PauseScreen(FakePygame, fonts=None)

    first = pause.handle(_key(FakePygame.K_q))
    second = pause.handle(_key(FakePygame.K_q))

    assert first is None
    assert pause.message == "Press Q again to close game"
    assert pause._buttons()["quit"].label == "Close Game"
    assert second is not None
    assert second.kind == "quit"


def test_q_pushes_pause_screen_on_event_rest_and_shop() -> None:
    runner = FakeRunner(_nodes())
    screens = (
        EventScreen(FakePygame, fonts=None, runner=runner, assets=None),
        RestScreen(FakePygame, fonts=None, runner=runner, assets=None),
        ShopScreen(FakePygame, fonts=None, runner=runner, assets=None),
    )

    for screen in screens:
        action = screen.handle(_key(FakePygame.K_q))

        assert action is not None
        assert action.kind == "push"
        assert isinstance(action.screen, PauseScreen)


def test_clicking_adjacent_route_room_moves_player() -> None:
    runner = FakeRunner(_nodes())
    screen = DungeonScreen(FakePygame, fonts=None, runner=runner, assets=None)

    action = screen.handle(_click((20 + 2 * 18 + 8, 62 + 2 * 18 + 8)))

    assert action is None
    assert screen.player_coord == (2, 2)
    assert runner.dungeon_player_coord == (2, 2)
