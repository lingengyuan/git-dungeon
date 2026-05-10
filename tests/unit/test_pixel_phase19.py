"""Phase 19 tests for the first-run PC tutorial."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from git_dungeon.ui_pixel.screens.base import ScreenAction
from git_dungeon.ui_pixel.screens.title import LoadingScreen
from git_dungeon.ui_pixel.screens.tutorial import TutorialScreen
from git_dungeon.ui_pixel.settings import PixelSettings, PixelSettingsStore


class FakePygame:
    KEYDOWN = "keydown"
    MOUSEMOTION = "mousemotion"
    MOUSEBUTTONDOWN = "mousebuttondown"
    K_RETURN = "return"
    K_SPACE = "space"
    K_ESCAPE = "escape"
    K_q = "q"


class FakeFonts:
    def draw(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def draw_fit(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    @staticmethod
    def measure(text: str, _size: int = 16) -> int:
        return len(text) * 6

    @staticmethod
    def fit(text: str, _max_width: int, _size: int = 16) -> str:
        return text


class FakeAssets:
    def draw(self, *_args: Any, **_kwargs: Any) -> None:
        return None


@dataclass
class FakeRunner:
    loaded: bool = False

    def load_repository(self) -> Any:
        self.loaded = True
        return SimpleNamespace()

    def route_nodes(self) -> tuple[Any, ...]:
        return ()

    def player_snapshot(self) -> Any:
        return SimpleNamespace(hp=80, max_hp=100, mp=30, max_mp=50, attack=12, gold=10)

    def current_node_snapshot(self) -> None:
        return None


def _key(key: str) -> Any:
    return SimpleNamespace(type=FakePygame.KEYDOWN, key=key)


def test_loading_screen_opens_tutorial_until_seen(tmp_path: Path) -> None:
    store = PixelSettingsStore(tmp_path / "settings.toml")
    settings = PixelSettings(tutorial_seen=False)
    screen = LoadingScreen(
        FakePygame,
        FakeFonts(),
        FakeRunner(),
        FakeAssets(),
        settings=settings,
        settings_store=store,
    )

    action = screen.update(0.016)

    assert action is not None
    assert action.kind == "replace"
    assert action.screen.__class__.__name__ == "TutorialScreen"


def test_loading_screen_skips_tutorial_after_seen(tmp_path: Path) -> None:
    store = PixelSettingsStore(tmp_path / "settings.toml")
    settings = PixelSettings(tutorial_seen=True)
    screen = LoadingScreen(
        FakePygame,
        FakeFonts(),
        FakeRunner(),
        FakeAssets(),
        settings=settings,
        settings_store=store,
    )

    action = screen.update(0.016)

    assert action is not None
    assert action.kind == "replace"
    assert action.screen.__class__.__name__ == "DungeonScreen"


def test_tutorial_marks_seen_and_enters_dungeon(tmp_path: Path) -> None:
    store = PixelSettingsStore(tmp_path / "settings.toml")
    screen = TutorialScreen(
        FakePygame,
        FakeFonts(),
        FakeRunner(),
        FakeAssets(),
        settings=PixelSettings(tutorial_seen=False),
        settings_store=store,
    )

    action = screen.handle(_key(FakePygame.K_RETURN))

    assert isinstance(action, ScreenAction)
    assert action.kind == "replace"
    assert action.screen.__class__.__name__ == "DungeonScreen"
    assert store.load().settings.tutorial_seen is True
