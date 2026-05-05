"""Focused unit tests for pixel settings module."""

from __future__ import annotations

from pathlib import Path

from git_dungeon.ui_pixel.settings import PixelSettings, PixelSettingsStore


def test_default_settings_path_uses_save_dir_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GIT_DUNGEON_SAVE_DIR", str(tmp_path))

    assert PixelSettingsStore.default_path() == tmp_path / "settings.toml"


def test_settings_normalize_supported_values() -> None:
    settings = PixelSettings(bgm_volume=999, sfx_volume=-2, lang="zh", window_mode="missing")

    assert settings.normalized() == PixelSettings(
        bgm_volume=100,
        sfx_volume=0,
        lang="zh_CN",
        window_mode="windowed",
    )
