"""Pause confirmation screen for in-run pixel play."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from git_dungeon.ui_pixel.screens.base import Screen, ScreenAction
from git_dungeon.ui_pixel.screens.settings import SettingsScreen
from git_dungeon.ui_pixel.text import tr
from git_dungeon.ui_pixel.widgets import BAD, BG, MUTED, Button, draw_dialog


class PauseScreen(Screen):
    def __init__(
        self,
        pygame_module: Any,
        fonts: Any,
        settings: Any | None = None,
        audio: Any | None = None,
        runner: Any | None = None,
        assets: Any | None = None,
        settings_store: Any | None = None,
        settings_error: str = "",
        apply_display_mode: Any | None = None,
    ) -> None:
        self.pygame = pygame_module
        self.fonts = fonts
        self.settings = settings
        self.audio = audio
        self.runner = runner
        self.assets = assets
        self.settings_store = settings_store
        self.settings_error = settings_error
        self.apply_display_mode = apply_display_mode
        self.hover_pos: tuple[int, int] | None = None
        self.quit_armed = False
        self.message = "Esc/Enter: Resume"

    def handle(self, event: Any) -> ScreenAction | None:
        if event.type == self.pygame.KEYDOWN:
            if event.key in (self.pygame.K_ESCAPE, self.pygame.K_RETURN, self.pygame.K_SPACE):
                if self.audio is not None:
                    self.audio.play_sfx("ui_cancel")
                return ScreenAction.pop()
            if event.key == self.pygame.K_q:
                if self.quit_armed:
                    return self._quit_run()
                self.quit_armed = True
                self.message = "Press Q again to return to title"
                if self.audio is not None:
                    self.audio.play_sfx("ui_denied")
                return None
            if event.key == self.pygame.K_s:
                return self._open_settings()
        if event.type == self.pygame.MOUSEMOTION:
            self.hover_pos = getattr(event, "logical_pos", None)
        if event.type == self.pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.hover_pos = getattr(event, "logical_pos", None)
            for key, button in self._buttons().items():
                if not button.contains(self.hover_pos):
                    continue
                if key == "resume":
                    if self.audio is not None:
                        self.audio.play_sfx("ui_cancel")
                    return ScreenAction.pop()
                if key == "settings":
                    return self._open_settings()
                if key == "quit":
                    if self.quit_armed:
                        return self._quit_run()
                    self.quit_armed = True
                    self.message = "Press Q again to return to title"
                    if self.audio is not None:
                        self.audio.play_sfx("ui_denied")
                    return None
        return None

    def draw(self, surface: Any) -> None:
        lang = self._lang()
        surface.fill(BG)
        draw_dialog(self.pygame, surface, self.fonts, (58, 36, 204, 108), tr("PAUSED", lang))
        self.fonts.draw_fit(
            surface,
            tr(self.message, lang),
            (76, 82),
            168,
            BAD if self.quit_armed else MUTED,
            14,
        )
        for button in self._buttons().values():
            button.draw(self.pygame, surface, self.fonts, button.contains(self.hover_pos))

    def _buttons(self) -> dict[str, Button]:
        lang = self._lang()
        return {
            "resume": Button((70, 104, 58, 18), tr("Resume", lang)),
            "settings": Button(
                (134, 104, 58, 18),
                tr("Settings", lang),
                enabled=self.settings is not None and self.settings_store is not None,
                tooltip=tr("Settings open over the paused run", lang),
            ),
            "quit": Button((198, 104, 62, 18), tr("Quit Run", lang)),
        }

    def _open_settings(self) -> ScreenAction | None:
        if self.settings is None or self.settings_store is None:
            return None
        if self.audio is not None:
            self.audio.play_sfx("ui_confirm")
        return ScreenAction.push(
            SettingsScreen(
                self.pygame,
                self.fonts,
                self.settings,
                self.settings_store,
                self.audio,
                self.settings_error,
                self._apply_settings,
            )
        )

    def _apply_settings(self, settings: Any) -> None:
        self.settings = settings
        self.fonts.set_lang(settings.lang)
        if hasattr(self.fonts, "set_text_size"):
            self.fonts.set_text_size(settings.text_size)
        if self.audio is not None:
            self.audio.set_volumes(settings.bgm_volume, settings.sfx_volume)
        if self.apply_display_mode is not None:
            self.apply_display_mode(settings)

    def _quit_run(self) -> ScreenAction:
        if self.audio is not None:
            self.audio.play_sfx("ui_cancel")
        if self.runner is None or self.assets is None:
            return ScreenAction.quit()
        from git_dungeon.ui_pixel.screens.title import TitleScreen

        settings = replace(self.settings, tutorial_seen=True).normalized() if self.settings else None
        return ScreenAction.reset(
            TitleScreen(
                self.pygame,
                self.fonts,
                self.runner,
                self.assets,
                self.audio,
                settings,
                self.settings_store,
                self.settings_error,
                self.apply_display_mode,
            )
        )

    def _lang(self) -> str:
        return getattr(self.settings, "lang", "en")
