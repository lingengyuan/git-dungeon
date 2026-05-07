"""Pixel settings screen."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from git_dungeon.ui_pixel.screens.base import Screen, ScreenAction
from git_dungeon.ui_pixel.settings import LANGUAGES, WINDOW_MODES, PixelSettings
from git_dungeon.ui_pixel.text import tr
from git_dungeon.ui_pixel.widgets import ACCENT, BAD, BG, GOOD, MUTED, TEXT, Button, draw_panel


class SettingsScreen(Screen):
    def __init__(
        self,
        pygame_module: Any,
        fonts: Any,
        settings: PixelSettings,
        store: Any,
        audio: Any | None = None,
        load_error: str = "",
        apply_settings: Any | None = None,
    ) -> None:
        self.pygame = pygame_module
        self.fonts = fonts
        self.settings = settings
        self.store = store
        self.audio = audio
        self.load_error = load_error
        self.apply_settings = apply_settings
        self.hover_pos: tuple[int, int] | None = None
        self.message = tr("Restart applies window mode", settings.lang)

    def handle(self, event: Any) -> ScreenAction | None:
        if event.type == self.pygame.KEYDOWN:
            if event.key in (self.pygame.K_ESCAPE, self.pygame.K_b):
                return ScreenAction.pop()
            if event.key in (self.pygame.K_RETURN, self.pygame.K_s):
                self._save()
                return None
            if event.key == self.pygame.K_1:
                self._change_bgm(10)
            if event.key == self.pygame.K_q:
                self._change_bgm(-10)
            if event.key == self.pygame.K_2:
                self._change_sfx(10)
            if event.key == self.pygame.K_w:
                self._change_sfx(-10)
            if event.key == self.pygame.K_l:
                self._cycle_lang()
            if event.key == self.pygame.K_m:
                self._cycle_window()
        if event.type == self.pygame.MOUSEMOTION:
            self.hover_pos = getattr(event, "logical_pos", None)
        if event.type == self.pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.hover_pos = getattr(event, "logical_pos", None)
            for key, button in self._buttons().items():
                if button.contains(self.hover_pos) and button.enabled:
                    return self._activate(key)
        return None

    def draw(self, surface: Any) -> None:
        lang = self.settings.lang
        surface.fill(BG)
        draw_panel(self.pygame, surface, (14, 12, 292, 156))
        self.fonts.draw(surface, tr("SETTINGS", lang), (28, 24), ACCENT, 22)

        rows = [
            (tr("BGM Volume", lang), f"{self.settings.bgm_volume:3d}%"),
            (tr("SFX Volume", lang), f"{self.settings.sfx_volume:3d}%"),
            (tr("Language", lang), self._lang_label()),
            (tr("Window", lang), tr(self.settings.window_mode.title(), lang)),
        ]
        for index, (label, value) in enumerate(rows):
            y = 54 + index * 20
            self.fonts.draw_fit(surface, label, (28, y), 84, TEXT, 15)
            self.fonts.draw_fit(surface, value, (126, y), 76, ACCENT, 15)

        for key, button in self._buttons().items():
            button.draw(self.pygame, surface, self.fonts, button.contains(self.hover_pos))

        if self.load_error:
            self.fonts.draw_fit(
                surface, self._localized_error(self.load_error), (28, 134), 250, BAD, 12
            )
        self.fonts.draw_fit(
            surface,
            self.message,
            (28, 150),
            252,
            GOOD if tr("Saved", lang) in self.message else MUTED,
            12,
        )

    def _buttons(self) -> dict[str, Button]:
        lang = self.settings.lang
        return {
            "bgm_minus": Button((184, 50, 18, 16), "-"),
            "bgm_plus": Button((204, 50, 18, 16), "+"),
            "sfx_minus": Button((184, 70, 18, 16), "-"),
            "sfx_plus": Button((204, 70, 18, 16), "+"),
            "lang": Button((184, 90, 38, 16), tr("Language", lang)),
            "window": Button((184, 110, 38, 16), tr("Window", lang)),
            "save": Button((228, 132, 48, 18), tr("Save", lang)),
            "back": Button((174, 132, 48, 18), tr("Back", lang)),
        }

    def _activate(self, key: str) -> ScreenAction | None:
        if key == "bgm_minus":
            self._change_bgm(-10)
        elif key == "bgm_plus":
            self._change_bgm(10)
        elif key == "sfx_minus":
            self._change_sfx(-10)
        elif key == "sfx_plus":
            self._change_sfx(10)
        elif key == "lang":
            self._cycle_lang()
        elif key == "window":
            self._cycle_window()
        elif key == "save":
            self._save()
        elif key == "back":
            return ScreenAction.pop()
        return None

    def _change_bgm(self, delta: int) -> None:
        self.settings = replace(
            self.settings,
            bgm_volume=max(0, min(100, self.settings.bgm_volume + delta)),
        ).normalized()
        self._apply_settings()

    def _change_sfx(self, delta: int) -> None:
        self.settings = replace(
            self.settings,
            sfx_volume=max(0, min(100, self.settings.sfx_volume + delta)),
        ).normalized()
        self._apply_settings()
        if self.audio is not None:
            self.audio.play_sfx("ui_confirm")

    def _cycle_lang(self) -> None:
        current = LANGUAGES.index(self.settings.lang) if self.settings.lang in LANGUAGES else 0
        self.settings = replace(
            self.settings, lang=LANGUAGES[(current + 1) % len(LANGUAGES)]
        ).normalized()
        self._apply_settings()
        self.message = tr("Restart applies window mode", self.settings.lang)

    def _cycle_window(self) -> None:
        current = (
            WINDOW_MODES.index(self.settings.window_mode)
            if self.settings.window_mode in WINDOW_MODES
            else 0
        )
        self.settings = replace(
            self.settings,
            window_mode=WINDOW_MODES[(current + 1) % len(WINDOW_MODES)],
        ).normalized()
        self._apply_settings()
        self.message = tr("Restart applies window mode", self.settings.lang)

    def _save(self) -> None:
        try:
            self.store.save(self.settings)
        except OSError as exc:
            self.message = f"{tr('Save failed', self.settings.lang)}: {exc}"
            if self.audio is not None:
                self.audio.play_sfx("ui_denied")
            return
        self.message = tr("Saved", self.settings.lang)
        if self.audio is not None:
            self.audio.play_sfx("ui_confirm")

    def _apply_settings(self) -> None:
        self.fonts.set_lang(self.settings.lang)
        if self.audio is not None:
            self.audio.set_volumes(self.settings.bgm_volume, self.settings.sfx_volume)
        if self.apply_settings is not None:
            self.apply_settings(self.settings)

    def _lang_label(self) -> str:
        return "English" if self.settings.lang == "en" else "中文"

    def _localized_error(self, error: str) -> str:
        for prefix in ("settings damaged", "settings write failed"):
            if error.startswith(prefix):
                return error.replace(prefix, tr(prefix, self.settings.lang), 1)
        return error
