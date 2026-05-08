"""Phase 18 tests for visual regression hooks and accessibility settings."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from git_dungeon.ui_pixel.app import LOGICAL_SIZE
from git_dungeon.ui_pixel.layout import scale_rect, window_to_logical
from git_dungeon.ui_pixel.screens.settings import SettingsScreen
from git_dungeon.ui_pixel.settings import PixelSettings, PixelSettingsStore
from scripts.render_pixel_screens import LANGUAGES, SCREEN_ORDER, render


class FakeFonts:
    def __init__(self) -> None:
        self.lang = "en"
        self.text_size = "normal"

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

    def set_lang(self, lang: str) -> None:
        self.lang = lang

    def set_text_size(self, text_size: str) -> None:
        self.text_size = text_size


def test_pixel_settings_accessibility_options_round_trip(tmp_path: Path) -> None:
    store = PixelSettingsStore(tmp_path / "settings.toml")
    settings = PixelSettings(
        bgm_volume=30,
        sfx_volume=40,
        lang="zh_CN",
        window_mode="windowed",
        text_size="large",
        high_contrast=True,
        reduce_motion=True,
    )

    store.save(settings)
    result = store.load(lang_override=None)

    assert result.settings == settings
    text = result.path.read_text(encoding="utf-8")
    assert 'text_size = "large"' in text
    assert "high_contrast = true" in text
    assert "reduce_motion = true" in text


def test_settings_screen_toggles_accessibility_options(tmp_path: Path) -> None:
    pygame = SimpleNamespace(
        KEYDOWN=1,
        K_ESCAPE=27,
        K_b=98,
        K_RETURN=13,
        K_s=115,
        K_1=49,
        K_q=113,
        K_2=50,
        K_w=119,
        K_l=108,
        K_m=109,
        K_t=116,
        K_h=104,
        K_r=114,
        MOUSEMOTION=2,
        MOUSEBUTTONDOWN=3,
    )
    fonts = FakeFonts()
    screen = SettingsScreen(
        pygame,
        fonts,
        PixelSettings(),
        PixelSettingsStore(tmp_path / "settings.toml"),
    )

    screen.handle(SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_t))
    screen.handle(SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_h))
    screen.handle(SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_r))

    assert screen.settings.text_size == "large"
    assert screen.settings.high_contrast is True
    assert screen.settings.reduce_motion is True
    assert fonts.text_size == "large"


def test_common_window_sizes_keep_integer_pixel_scale() -> None:
    assert scale_rect(LOGICAL_SIZE, (960, 540)) == (0, 0, 960, 540)
    assert scale_rect(LOGICAL_SIZE, (1280, 720)) == (0, 0, 1280, 720)
    assert scale_rect(LOGICAL_SIZE, (1440, 900)) == (80, 90, 1280, 720)
    assert window_to_logical((80, 90), (1440, 900), LOGICAL_SIZE) == (0, 0)
    assert window_to_logical((79, 90), (1440, 900), LOGICAL_SIZE) is None


def test_render_pixel_screens_writes_all_core_screens(tmp_path: Path) -> None:
    manifest = render(tmp_path, scale=1)

    assert len(manifest) == len(LANGUAGES) * len(SCREEN_ORDER)
    for item in manifest:
        path = Path(item["path"])
        assert path.is_file()
        assert item["size"] == list(LOGICAL_SIZE)

    saved = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert {(item["lang"], item["screen"]) for item in saved} == {
        (lang, screen) for lang in LANGUAGES for screen in SCREEN_ORDER
    }
