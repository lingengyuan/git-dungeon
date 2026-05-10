"""Phase 20 tests for the paused-run menu."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

from git_dungeon.ui_pixel.screens.pause import PauseScreen
from git_dungeon.ui_pixel.settings import PixelSettings, PixelSettingsStore


class FakePygame:
    KEYDOWN = "keydown"
    MOUSEMOTION = "mousemotion"
    MOUSEBUTTONDOWN = "mousebuttondown"
    K_ESCAPE = "escape"
    K_RETURN = "return"
    K_SPACE = "space"
    K_q = "q"
    K_s = "s"


class FakeFonts:
    def __init__(self) -> None:
        self.lang = "en"
        self.text_size = "normal"

    def set_lang(self, lang: str) -> None:
        self.lang = lang

    def set_text_size(self, text_size: str) -> None:
        self.text_size = text_size


class FakeAudio:
    def __init__(self) -> None:
        self.sfx: list[str] = []
        self.volumes: tuple[int, int] | None = None

    def play_sfx(self, name: str) -> None:
        self.sfx.append(name)

    def set_volumes(self, bgm: int, sfx: int) -> None:
        self.volumes = (bgm, sfx)


def _key(key: str) -> Any:
    return SimpleNamespace(type=FakePygame.KEYDOWN, key=key)


def test_pause_settings_opens_over_current_run(tmp_path: Path) -> None:
    screen = PauseScreen(
        FakePygame,
        FakeFonts(),
        PixelSettings(),
        FakeAudio(),
        runner=object(),
        assets=object(),
        settings_store=PixelSettingsStore(tmp_path / "settings.toml"),
    )

    action = screen.handle(_key(FakePygame.K_s))

    assert action is not None
    assert action.kind == "push"
    assert action.screen.__class__.__name__ == "SettingsScreen"


def test_pause_quit_run_returns_to_title_when_runtime_is_available(tmp_path: Path) -> None:
    screen = PauseScreen(
        FakePygame,
        FakeFonts(),
        PixelSettings(tutorial_seen=True),
        FakeAudio(),
        runner=object(),
        assets=object(),
        settings_store=PixelSettingsStore(tmp_path / "settings.toml"),
    )

    assert screen.handle(_key(FakePygame.K_q)) is None
    action = screen.handle(_key(FakePygame.K_q))

    assert action is not None
    assert action.kind == "reset"
    assert action.screen.__class__.__name__ == "TitleScreen"
