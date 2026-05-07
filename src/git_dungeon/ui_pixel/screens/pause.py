"""Pause confirmation screen for in-run pixel play."""

from __future__ import annotations

from typing import Any

from git_dungeon.ui_pixel.screens.base import Screen, ScreenAction
from git_dungeon.ui_pixel.text import tr
from git_dungeon.ui_pixel.widgets import ACCENT, BAD, BG, MUTED, Button, draw_panel


class PauseScreen(Screen):
    def __init__(
        self,
        pygame_module: Any,
        fonts: Any,
        settings: Any | None = None,
        audio: Any | None = None,
    ) -> None:
        self.pygame = pygame_module
        self.fonts = fonts
        self.settings = settings
        self.audio = audio
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
                    return ScreenAction.quit()
                self.quit_armed = True
                self.message = "Press Q again to close game"
                if self.audio is not None:
                    self.audio.play_sfx("ui_denied")
                return None
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
                if key == "quit":
                    if self.quit_armed:
                        return ScreenAction.quit()
                    self.quit_armed = True
                    self.message = "Press Q again to close game"
                    if self.audio is not None:
                        self.audio.play_sfx("ui_denied")
                    return None
        return None

    def draw(self, surface: Any) -> None:
        lang = self._lang()
        surface.fill(BG)
        draw_panel(self.pygame, surface, (58, 36, 204, 108), border=ACCENT)
        self.fonts.draw(surface, tr("PAUSED", lang), (116, 54), ACCENT, 24)
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
            "resume": Button((82, 104, 70, 18), tr("Resume", lang)),
            "quit": Button((166, 104, 72, 18), tr("Close Game", lang)),
        }

    def _lang(self) -> str:
        return getattr(self.settings, "lang", "en")
