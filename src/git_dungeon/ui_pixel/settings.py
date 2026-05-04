"""Persistent settings for the pixel UI."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, replace
from pathlib import Path

from git_dungeon.i18n import normalize_lang

LANGUAGES = ("en", "zh_CN")
WINDOW_MODES = ("windowed", "fullscreen")


@dataclass(frozen=True)
class PixelSettings:
    bgm_volume: int = 45
    sfx_volume: int = 70
    lang: str = "en"
    window_mode: str = "windowed"

    def normalized(self) -> "PixelSettings":
        lang = normalize_lang(self.lang)
        if lang not in LANGUAGES:
            lang = "en"
        window_mode = self.window_mode if self.window_mode in WINDOW_MODES else "windowed"
        return replace(
            self,
            bgm_volume=max(0, min(100, int(self.bgm_volume))),
            sfx_volume=max(0, min(100, int(self.sfx_volume))),
            lang=lang,
            window_mode=window_mode,
        )


@dataclass(frozen=True)
class SettingsLoadResult:
    settings: PixelSettings
    path: Path
    error: str = ""


class PixelSettingsStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or self.default_path()

    @staticmethod
    def default_path() -> Path:
        base = os.getenv("GIT_DUNGEON_SAVE_DIR")
        root = Path(base) if base else Path.home() / ".local" / "share" / "git-dungeon"
        return root / "settings.toml"

    def load(self, *, lang_override: str | None = None) -> SettingsLoadResult:
        default = PixelSettings(lang=normalize_lang(lang_override or "en")).normalized()
        if not self.path.exists():
            try:
                self.save(default)
            except OSError as exc:
                return SettingsLoadResult(default, self.path, f"settings write failed: {exc}")
            return SettingsLoadResult(default, self.path)

        try:
            data = tomllib.loads(self.path.read_text(encoding="utf-8"))
            settings_data = data.get("pixel", data)
            settings = PixelSettings(
                bgm_volume=int(settings_data.get("bgm_volume", default.bgm_volume)),
                sfx_volume=int(settings_data.get("sfx_volume", default.sfx_volume)),
                lang=str(settings_data.get("lang", default.lang)),
                window_mode=str(settings_data.get("window_mode", default.window_mode)),
            ).normalized()
        except Exception as exc:
            return SettingsLoadResult(default, self.path, f"settings damaged: {exc}")

        if lang_override is not None:
            settings = replace(settings, lang=normalize_lang(lang_override)).normalized()
        return SettingsLoadResult(settings, self.path)

    def save(self, settings: PixelSettings) -> None:
        normalized = settings.normalized()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        text = (
            "[pixel]\n"
            f"bgm_volume = {normalized.bgm_volume}\n"
            f"sfx_volume = {normalized.sfx_volume}\n"
            f'lang = "{normalized.lang}"\n'
            f'window_mode = "{normalized.window_mode}"\n'
        )
        self.path.write_text(text, encoding="utf-8")
