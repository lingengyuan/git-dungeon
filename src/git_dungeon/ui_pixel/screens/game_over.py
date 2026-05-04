"""Game over screen."""

from __future__ import annotations

from typing import Any

from git_dungeon.ui_pixel.screens.base import Screen, ScreenAction
from git_dungeon.ui_pixel.widgets import ACCENT, BAD, BG, GOOD, MUTED, TEXT, draw_panel


class GameOverScreen(Screen):
    def __init__(
        self,
        pygame_module: Any,
        fonts: Any,
        runner: Any,
        assets: Any,
        won: bool,
        audio: Any | None = None,
    ) -> None:
        self.pygame = pygame_module
        self.fonts = fonts
        self.runner = runner
        self.assets = assets
        self.won = won
        self.audio = audio

    def enter(self) -> None:
        if self.audio is not None:
            self.audio.play_bgm("gameover")

    def handle(self, event: Any) -> ScreenAction | None:
        if event.type == self.pygame.KEYDOWN:
            if event.key in (self.pygame.K_ESCAPE, self.pygame.K_RETURN, self.pygame.K_q):
                return ScreenAction.quit()
        return None

    def draw(self, surface: Any) -> None:
        surface.fill(BG)
        draw_panel(self.pygame, surface, (18, 22, 284, 136), border=GOOD if self.won else BAD)
        player = self.runner.player_snapshot()
        title = "VICTORY" if self.won else "GAME OVER"
        self.fonts.draw(surface, title, (92, 42), GOOD if self.won else BAD, 28)
        self.fonts.draw(surface, f"HP {player.hp}/{player.max_hp}", (82, 82), TEXT, 16)
        self.fonts.draw(surface, f"Gold {player.gold}", (82, 102), ACCENT, 16)
        self.fonts.draw(surface, "Enter/Esc/Q: Quit", (82, 130), MUTED, 15)
        if self.audio is not None:
            self.fonts.draw(surface, self.audio.status().label()[:36], (82, 146), MUTED, 12)
