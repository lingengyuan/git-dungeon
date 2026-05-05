"""Explicit startup error screen for pixel mode."""

from __future__ import annotations

from typing import Any

from git_dungeon.ui_pixel.screens.base import Screen, ScreenAction
from git_dungeon.ui_pixel.widgets import ACCENT, BAD, BG, MUTED, TEXT, draw_panel


class ErrorScreen(Screen):
    def __init__(self, pygame_module: Any, fonts: Any, title: str, message: str) -> None:
        self.pygame = pygame_module
        self.fonts = fonts
        self.title = title
        self.message = message

    def handle(self, event: Any) -> ScreenAction | None:
        if event.type == self.pygame.KEYDOWN and event.key in (
            self.pygame.K_ESCAPE,
            self.pygame.K_RETURN,
            self.pygame.K_q,
        ):
            return ScreenAction.quit()
        return None

    def draw(self, surface: Any) -> None:
        surface.fill(BG)
        draw_panel(self.pygame, surface, (14, 20, 292, 140), border=BAD)
        self.fonts.draw(surface, self.title, (28, 34), BAD, 22)
        self.fonts.draw_fit(surface, self.message, (28, 68), 252, TEXT, 14)
        self.fonts.draw(surface, "Fix assets, then restart.", (28, 112), ACCENT, 14)
        self.fonts.draw(surface, "Enter/Esc/Q: Quit", (28, 136), MUTED, 13)
