"""Phase 23 tests for run log and chapter summary."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from git_dungeon.ui_pixel.game_runner import ChapterSummarySnapshot, GameRunner, RunLogEntry
from git_dungeon.ui_pixel.screens.dungeon import DungeonScreen


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


class FakePygame:
    draw = FakeDraw()


class RecordingFonts:
    def __init__(self) -> None:
        self.texts: list[str] = []

    def draw(self, _surface: Any, text: str, *_args: Any, **_kwargs: Any) -> None:
        self.texts.append(text)

    def draw_fit(self, _surface: Any, text: str, *_args: Any, **_kwargs: Any) -> None:
        self.texts.append(text)

    @staticmethod
    def measure(text: str, _size: int = 16) -> int:
        return len(text) * 6

    @staticmethod
    def fit(text: str, _max_width: int, _size: int = 16) -> str:
        return text


class FakeSurface:
    def fill(self, *_args: Any, **_kwargs: Any) -> None:
        return None


class FakeAssets:
    def draw(self, *_args: Any, **_kwargs: Any) -> None:
        return None


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

    def player_snapshot(self) -> Any:
        return SimpleNamespace(hp=80, max_hp=100, mp=40, max_mp=50, attack=12, gold=60)

    def current_node_snapshot(self) -> Any:
        return self.route_nodes()[1]

    def recent_run_events(self, _limit: int = 4) -> tuple[RunLogEntry, ...]:
        return (
            RunLogEntry("battle", "Battle won"),
            RunLogEntry("trap", "Trap hit: -8 HP"),
            RunLogEntry("reward", "Reward claimed"),
        )

    def chapter_summary_snapshot(self) -> ChapterSummarySnapshot:
        return ChapterSummarySnapshot("Demo", 1, 2, 80, 100, 60)

    def is_dungeon_trap_consumed(self, _trap_id: str) -> bool:
        return False

    def is_dungeon_reward_claimed(self, _reward_id: str) -> bool:
        return False

    def has_dungeon_key(self, _key_id: str) -> bool:
        return False


def test_game_runner_recent_log_keeps_latest_entries() -> None:
    runner = GameRunner(repo_path=".", seed=1)

    for index in range(14):
        runner.record_run_event("event", f"event {index}")

    recent = runner.recent_run_events(3)

    assert [entry.message for entry in recent] == ["event 11", "event 12", "event 13"]
    assert len(runner.run_log) == 12


def test_dungeon_screen_draws_recent_log_and_summary() -> None:
    fonts = RecordingFonts()
    screen = DungeonScreen(
        FakePygame,
        fonts,
        FakeRunner(),
        FakeAssets(),
        settings=SimpleNamespace(lang="zh_CN"),
    )

    screen.draw(FakeSurface())

    assert "记录" in fonts.texts
    assert "房间 1/2" in fonts.texts
    assert "战斗胜利" in fonts.texts
    assert any("触发陷阱" in text for text in fonts.texts)
    assert "奖励已领取" in fonts.texts
