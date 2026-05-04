"""Rest node screen."""

from __future__ import annotations

from typing import Any

from git_dungeon.ui_pixel.screens.base import Screen, ScreenAction
from git_dungeon.ui_pixel.screens.map import MapScreen
from git_dungeon.ui_pixel.widgets import ACCENT, BG, GOOD, MUTED, TEXT, Button, draw_panel


class RestScreen(Screen):
    def __init__(self, pygame_module: Any, fonts: Any, runner: Any, assets: Any) -> None:
        self.pygame = pygame_module
        self.fonts = fonts
        self.runner = runner
        self.assets = assets
        self.hover_pos: tuple[int, int] | None = None
        self.result = ""

    def handle(self, event: Any) -> ScreenAction | None:
        if event.type == self.pygame.KEYDOWN:
            if event.key == self.pygame.K_ESCAPE:
                return ScreenAction.replace(MapScreen(self.pygame, self.fonts, self.runner, self.assets))
            if event.key in (self.pygame.K_1, self.pygame.K_h):
                return self._choose("heal")
            if event.key in (self.pygame.K_2, self.pygame.K_f):
                return self._choose("focus")
            if event.key == self.pygame.K_RETURN and self.result:
                return ScreenAction.replace(MapScreen(self.pygame, self.fonts, self.runner, self.assets))
        if event.type == self.pygame.MOUSEMOTION:
            self.hover_pos = getattr(event, "logical_pos", None)
        if event.type == self.pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.hover_pos = getattr(event, "logical_pos", None)
            for option, button in self._buttons().items():
                if button.contains(self.hover_pos) and button.enabled:
                    return self._choose(option)
        return None

    def draw(self, surface: Any) -> None:
        surface.fill(BG)
        draw_panel(self.pygame, surface, (14, 18, 292, 144))
        self.assets.draw(surface, "node_rest", (28, 32, 24, 24))
        self.fonts.draw(surface, "REST NODE", (62, 34), ACCENT, 22)
        self.fonts.draw(surface, "Pick one real state change", (62, 56), MUTED, 14)

        for option in self.runner.rest_options():
            self.fonts.draw(surface, option.label, (32, 82 if option.action == "heal" else 116), TEXT, 16)
            self.fonts.draw(surface, option.detail, (84, 82 if option.action == "heal" else 116), MUTED, 14)

        for button in self._buttons().values():
            button.draw(self.pygame, surface, self.fonts, button.contains(self.hover_pos))

        if self.result:
            self.fonts.draw(surface, self.result[:34], (32, 144), GOOD, 14)
        else:
            self.fonts.draw(surface, "1/H: Heal   2/F: Focus", (32, 144), MUTED, 14)

    def _buttons(self) -> dict[str, Button]:
        return {
            "heal": Button((220, 78, 60, 20), "Heal"),
            "focus": Button((220, 112, 60, 20), "Focus"),
        }

    def _choose(self, action: str) -> ScreenAction | None:
        result = self.runner.resolve_current_rest(action)
        return ScreenAction.replace(
            MapScreen(
                self.pygame,
                self.fonts,
                self.runner,
                self.assets,
                message=f"Rest: {result.message}",
            )
        )
