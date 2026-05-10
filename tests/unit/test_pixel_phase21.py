"""Phase 21 tests for PC window mode switching."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from git_dungeon.ui_pixel.app import display_flags_for_window_mode
from git_dungeon.ui_pixel.screens.settings import SettingsScreen
from git_dungeon.ui_pixel.settings import PixelSettings


class FakePygame:
    FULLSCREEN = 8
    KEYDOWN = "keydown"
    MOUSEMOTION = "mousemotion"
    MOUSEBUTTONDOWN = "mousebuttondown"
    K_ESCAPE = "escape"
    K_b = "b"
    K_RETURN = "return"
    K_s = "s"
    K_1 = "1"
    K_q = "q"
    K_2 = "2"
    K_w = "w"
    K_l = "l"
    K_m = "m"
    K_t = "t"
    K_h = "h"
    K_r = "r"


class FakeFonts:
    def __init__(self) -> None:
        self.lang = "en"
        self.text_size = "normal"

    def set_lang(self, lang: str) -> None:
        self.lang = lang

    def set_text_size(self, text_size: str) -> None:
        self.text_size = text_size


class FakeStore:
    def save(self, _settings: PixelSettings) -> None:
        return None


def _key(key: str) -> Any:
    return SimpleNamespace(type=FakePygame.KEYDOWN, key=key)


def test_display_flags_match_pc_window_modes() -> None:
    assert display_flags_for_window_mode(FakePygame, "windowed") == 0
    assert display_flags_for_window_mode(FakePygame, "fullscreen") == FakePygame.FULLSCREEN


def test_settings_screen_applies_window_mode_immediately() -> None:
    applied: list[str] = []

    def apply(settings: PixelSettings) -> None:
        applied.append(settings.window_mode)

    screen = SettingsScreen(
        FakePygame,
        FakeFonts(),
        PixelSettings(window_mode="windowed"),
        FakeStore(),
        apply_settings=apply,
    )

    screen.handle(_key(FakePygame.K_m))

    assert screen.settings.window_mode == "fullscreen"
    assert applied == ["fullscreen"]
    assert screen.message == "Window applied"
