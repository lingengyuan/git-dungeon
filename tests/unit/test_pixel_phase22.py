"""Phase 22 tests for responsive repository loading."""

from __future__ import annotations

from pathlib import Path
from threading import Event
from types import SimpleNamespace
from typing import Any

from git_dungeon.ui_pixel.screens.title import LoadingScreen
from git_dungeon.ui_pixel.settings import PixelSettings, PixelSettingsStore


class FakePygame:
    KEYDOWN = "keydown"
    K_ESCAPE = "escape"
    K_q = "q"
    K_RETURN = "return"


class FastRunner:
    def __init__(self) -> None:
        self.loaded = False

    def load_repository(self) -> Any:
        self.loaded = True
        return SimpleNamespace()


class SlowRunner:
    def __init__(self) -> None:
        self.started = Event()
        self.release = Event()
        self.fresh_created = False

    def load_repository(self) -> Any:
        self.started.set()
        self.release.wait(timeout=2)
        return SimpleNamespace()

    def fresh_copy(self) -> FastRunner:
        self.fresh_created = True
        return FastRunner()


def _key(key: str) -> Any:
    return SimpleNamespace(type=FakePygame.KEYDOWN, key=key)


def test_loading_screen_returns_before_repository_finishes(tmp_path: Path) -> None:
    runner = SlowRunner()
    screen = LoadingScreen(
        FakePygame,
        fonts=None,
        runner=runner,
        assets=None,
        settings=PixelSettings(tutorial_seen=True),
        settings_store=PixelSettingsStore(tmp_path / "settings.toml"),
    )

    assert screen.update(0.016) is None
    assert runner.started.wait(timeout=1)

    action = screen.handle(_key(FakePygame.K_q))
    runner.release.set()

    assert action is not None
    assert action.kind == "replace"
    assert action.screen.__class__.__name__ == "TitleScreen"
    assert runner.fresh_created is True


def test_loading_screen_enters_tutorial_when_background_load_finishes(tmp_path: Path) -> None:
    screen = LoadingScreen(
        FakePygame,
        fonts=None,
        runner=FastRunner(),
        assets=None,
        settings=PixelSettings(tutorial_seen=False),
        settings_store=PixelSettingsStore(tmp_path / "settings.toml"),
    )

    assert screen.update(0.016) is None
    action = None
    for _ in range(20):
        action = screen.update(0.016)
        if action is not None:
            break

    assert action is not None
    assert action.kind == "replace"
    assert action.screen.__class__.__name__ == "TutorialScreen"


def test_loading_status_progresses_for_large_repositories() -> None:
    screen = LoadingScreen(
        FakePygame,
        fonts=None,
        runner=FastRunner(),
        assets=None,
        settings=PixelSettings(tutorial_seen=True),
    )

    screen.elapsed = 0.2
    assert screen._loading_status() == "Preparing run..."
    screen.elapsed = 0.8
    assert screen._loading_status() == "Reading git history..."
    screen.elapsed = 1.8
    assert screen._loading_status() == "Building dungeon route..."
    screen.elapsed = 3.0
    assert screen._loading_status() == "Still working on this repository..."
