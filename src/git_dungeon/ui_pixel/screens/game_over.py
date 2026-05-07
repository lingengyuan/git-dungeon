"""Game over screen."""

from __future__ import annotations

from typing import Any

from git_dungeon.ui_pixel.screens.base import Screen, ScreenAction
from git_dungeon.ui_pixel.text import audio_label, stat_value, tr
from git_dungeon.ui_pixel.widgets import ACCENT, BAD, BG, GOOD, MUTED, TEXT, draw_panel


class GameOverScreen(Screen):
    def __init__(
        self,
        pygame_module: Any,
        fonts: Any,
        runner: Any,
        assets: Any,
        won: bool,
        message: str = "",
        audio: Any | None = None,
        settings: Any | None = None,
    ) -> None:
        self.pygame = pygame_module
        self.fonts = fonts
        self.runner = runner
        self.assets = assets
        self.won = won
        self.message = message
        self.audio = audio
        self.settings = settings

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
        lang = getattr(self.settings, "lang", "en")
        draw_panel(self.pygame, surface, (18, 22, 284, 136), border=GOOD if self.won else BAD)
        player = self.runner.player_snapshot()
        title = "VICTORY" if self.won else "GAME OVER"
        self.fonts.draw(surface, tr(title, lang), (92, 42), GOOD if self.won else BAD, 28)
        self.fonts.draw(
            surface, stat_value("hp", player.hp, lang, player.max_hp), (82, 82), TEXT, 16
        )
        self.fonts.draw(surface, stat_value("gold", player.gold, lang), (82, 102), ACCENT, 16)
        if self.message:
            self.fonts.draw_fit(surface, tr(self.message, lang), (82, 118), 170, BAD, 12)
        self.fonts.draw(surface, tr("Enter/Esc/Q: Quit", lang), (82, 130), MUTED, 15)
        if self.audio is not None:
            label = audio_label(self.audio.status().label(), lang)
            if label:
                self.fonts.draw_fit(surface, label, (82, 146), 188, MUTED, 12)
