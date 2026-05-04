"""Title and loading screens for the pixel UI."""

from __future__ import annotations

from typing import Any

from git_dungeon.ui_pixel.game_runner import GameRunner, RunSummary
from git_dungeon.ui_pixel.screens.base import Screen, ScreenAction
from git_dungeon.ui_pixel.screens.map import MapScreen
from git_dungeon.ui_pixel.widgets import ACCENT, BAD, BG, GOOD, MUTED, TEXT, draw_panel


class TitleScreen(Screen):
    def __init__(self, pygame_module: Any, fonts: Any, runner: GameRunner, assets: Any) -> None:
        self.pygame = pygame_module
        self.fonts = fonts
        self.runner = runner
        self.assets = assets
        self.status = "Press Enter to load repository"

    def handle(self, event: Any) -> ScreenAction | None:
        if event.type == self.pygame.KEYDOWN:
            if event.key in (self.pygame.K_ESCAPE, self.pygame.K_q):
                return ScreenAction.quit()
            if event.key in (self.pygame.K_RETURN, self.pygame.K_SPACE):
                return ScreenAction.replace(
                    LoadingScreen(self.pygame, self.fonts, self.runner, self.assets)
                )
        return None

    def draw(self, surface: Any) -> None:
        surface.fill(BG)
        draw_panel(self.pygame, surface, (18, 18, 284, 144))
        self.assets.draw(surface, "player_default", (36, 42, 32, 32))
        self.assets.draw(surface, "enemy_default", (252, 42, 32, 32))
        self.fonts.draw(surface, "GIT DUNGEON", (86, 42), ACCENT, 28)
        self.fonts.draw(surface, "PIXEL MODE", (112, 70), TEXT, 18)
        self.fonts.draw(surface, self.status, (62, 110), MUTED, 16)
        self.fonts.draw(surface, "Enter: Start   Esc/Q: Quit", (62, 132), TEXT, 16)


class LoadingScreen(Screen):
    def __init__(self, pygame_module: Any, fonts: Any, runner: GameRunner, assets: Any) -> None:
        self.pygame = pygame_module
        self.fonts = fonts
        self.runner = runner
        self.assets = assets
        self.started = False
        self.summary: RunSummary | None = None
        self.error: str | None = None

    def update(self, dt: float) -> ScreenAction | None:
        if self.started:
            return None
        self.started = True
        try:
            self.summary = self.runner.load_repository()
        except Exception as exc:
            self.error = str(exc)
            return None
        return ScreenAction.replace(MapScreen(self.pygame, self.fonts, self.runner, self.assets))

    def handle(self, event: Any) -> ScreenAction | None:
        if event.type == self.pygame.KEYDOWN and event.key in (
            self.pygame.K_ESCAPE,
            self.pygame.K_q,
            self.pygame.K_RETURN,
        ):
            return ScreenAction.quit()
        return None

    def draw(self, surface: Any) -> None:
        surface.fill(BG)
        draw_panel(self.pygame, surface, (14, 18, 292, 144))
        self.fonts.draw(surface, "LOADING REPOSITORY", (50, 34), ACCENT, 22)

        if self.error:
            self.fonts.draw(surface, "Load failed", (32, 70), BAD, 18)
            self.fonts.draw(surface, self.error[:38], (32, 94), TEXT, 16)
            self.fonts.draw(surface, "Enter/Esc: Quit", (32, 128), MUTED, 16)
            return

        if self.summary is None:
            self.fonts.draw(surface, "Reading git history...", (32, 82), MUTED, 16)
            return

        self.fonts.draw(surface, "Repository loaded", (32, 64), GOOD, 18)
