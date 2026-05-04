"""Phase 5 tests for pixel settings."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from git_dungeon.ui_pixel.screens.settings import SettingsScreen
from git_dungeon.ui_pixel.screens.title import TitleScreen
from git_dungeon.ui_pixel.settings import PixelSettings, PixelSettingsStore
from git_dungeon.ui_pixel.text import audio_label, tr


class _FakeFonts:
    def __init__(self) -> None:
        self.lang = "en"

    def set_lang(self, lang: str) -> None:
        self.lang = lang


def test_settings_file_is_created_with_lang_override(tmp_path: Path) -> None:
    store = PixelSettingsStore(tmp_path / "settings.toml")

    result = store.load(lang_override="zh_CN")

    assert result.error == ""
    assert result.settings.lang == "zh_CN"
    assert result.path.exists()
    assert 'lang = "zh_CN"' in result.path.read_text(encoding="utf-8")


def test_settings_persist_when_no_cli_lang_override(tmp_path: Path) -> None:
    path = tmp_path / "settings.toml"
    store = PixelSettingsStore(path)
    store.save(PixelSettings(bgm_volume=20, sfx_volume=30, lang="zh_CN", window_mode="fullscreen"))

    result = store.load(lang_override=None)

    assert result.settings == PixelSettings(
        bgm_volume=20,
        sfx_volume=30,
        lang="zh_CN",
        window_mode="fullscreen",
    )


def test_damaged_settings_are_visible_and_use_defaults(tmp_path: Path) -> None:
    path = tmp_path / "settings.toml"
    path.write_text("[pixel\nlang = zh_CN", encoding="utf-8")
    store = PixelSettingsStore(path)

    result = store.load(lang_override=None)

    assert result.settings == PixelSettings()
    assert result.error.startswith("settings damaged:")


def test_settings_save_clamps_values(tmp_path: Path) -> None:
    path = tmp_path / "settings.toml"
    store = PixelSettingsStore(path)

    store.save(PixelSettings(bgm_volume=120, sfx_volume=-4, lang="zh", window_mode="bad"))

    text = path.read_text(encoding="utf-8")
    assert "bgm_volume = 100" in text
    assert "sfx_volume = 0" in text
    assert 'lang = "zh_CN"' in text
    assert 'window_mode = "windowed"' in text


def test_pixel_text_has_chinese_settings_labels() -> None:
    assert tr("Settings", "zh_CN") == "设置"
    assert tr("BGM Volume", "zh_CN") == "音乐音量"
    assert tr("Windowed", "zh_CN") == "窗口"
    assert audio_label("Audio muted: device unavailable", "zh_CN").startswith("音频静音")


def test_title_opens_settings_and_applies_language_change(tmp_path: Path) -> None:
    fake_pygame = SimpleNamespace(
        KEYDOWN=1,
        K_s=19,
        K_ESCAPE=27,
        K_q=113,
        K_RETURN=13,
        K_SPACE=32,
        K_b=98,
        K_1=49,
        K_2=50,
        K_w=119,
        K_l=108,
        K_m=109,
        MOUSEMOTION=2,
        MOUSEBUTTONDOWN=3,
    )
    fonts = _FakeFonts()
    settings = PixelSettings()
    title = TitleScreen(
        fake_pygame,
        fonts,
        runner=object(),
        assets=object(),
        audio=None,
        settings=settings,
        settings_store=PixelSettingsStore(tmp_path / "settings.toml"),
        settings_error="",
    )

    action = title.handle(SimpleNamespace(type=fake_pygame.KEYDOWN, key=fake_pygame.K_s))

    assert action is not None
    assert action.kind == "push"
    assert isinstance(action.screen, SettingsScreen)

    action.screen.handle(SimpleNamespace(type=fake_pygame.KEYDOWN, key=fake_pygame.K_l))

    assert title.settings.lang == "zh_CN"
    assert fonts.lang == "zh_CN"
