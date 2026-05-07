"""Rest node screen."""

from __future__ import annotations

from typing import Any

from git_dungeon.ui_pixel.screens.base import Screen, ScreenAction
from git_dungeon.ui_pixel.screens.dungeon import DungeonScreen
from git_dungeon.ui_pixel.text import rest_detail, rest_result_feedback, tr
from git_dungeon.ui_pixel.widgets import (
    ACCENT,
    BG,
    MUTED,
    Button,
    draw_action_bar,
    draw_choice_card,
    draw_panel,
)


class RestScreen(Screen):
    def __init__(
        self,
        pygame_module: Any,
        fonts: Any,
        runner: Any,
        assets: Any,
        audio: Any | None = None,
        settings: Any | None = None,
    ) -> None:
        self.pygame = pygame_module
        self.fonts = fonts
        self.runner = runner
        self.assets = assets
        self.audio = audio
        self.settings = settings
        self.hover_pos: tuple[int, int] | None = None
        self.result = ""

    def handle(self, event: Any) -> ScreenAction | None:
        if event.type == self.pygame.KEYDOWN:
            if event.key in (self.pygame.K_ESCAPE, self.pygame.K_q):
                from git_dungeon.ui_pixel.screens.pause import PauseScreen

                return ScreenAction.push(
                    PauseScreen(self.pygame, self.fonts, self.settings, self.audio)
                )
            if event.key in (self.pygame.K_1, self.pygame.K_h):
                return self._choose("heal")
            if event.key in (self.pygame.K_2, self.pygame.K_f):
                return self._choose("focus")
            if event.key == self.pygame.K_RETURN and self.result:
                if self.audio is not None:
                    self.audio.play_sfx("ui_confirm")
                return ScreenAction.replace(
                    DungeonScreen(
                        self.pygame,
                        self.fonts,
                        self.runner,
                        self.assets,
                        audio=self.audio,
                        settings=self.settings,
                    )
                )
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
        lang = self._lang()
        draw_panel(self.pygame, surface, (14, 18, 292, 136))
        self.assets.draw(surface, "node_rest", (28, 32, 24, 24))
        self.fonts.draw(surface, tr("REST NODE", lang), (62, 34), ACCENT, 22)
        self.fonts.draw_fit(
            surface, tr("Pick one real state change", lang), (62, 56), 194, MUTED, 14
        )

        for option in self.runner.rest_options():
            rect = (28, 78 if option.action == "heal" else 112, 184, 28)
            button = self._buttons()[option.action]
            draw_choice_card(
                self.pygame,
                surface,
                self.fonts,
                rect,
                tr(option.label, lang),
                rest_detail(option.detail, lang),
                hover=button.contains(self.hover_pos),
            )

        for button in self._buttons().values():
            button.draw(self.pygame, surface, self.fonts, button.contains(self.hover_pos))

        message = self.result if self.result else tr("1/H: Heal   2/F: Focus", lang)
        draw_action_bar(self.pygame, surface, self.fonts, message)

    def _buttons(self) -> dict[str, Button]:
        return {
            "heal": Button((224, 82, 58, 18), tr("Heal", self._lang())),
            "focus": Button((224, 116, 58, 18), tr("Focus", self._lang())),
        }

    def _choose(self, action: str) -> ScreenAction | None:
        result = self.runner.resolve_current_rest(action)
        if self.audio is not None:
            self.audio.play_sfx("rest")
        return ScreenAction.replace(
            DungeonScreen(
                self.pygame,
                self.fonts,
                self.runner,
                self.assets,
                message=rest_result_feedback(result.message, self._lang()),
                audio=self.audio,
                settings=self.settings,
            )
        )

    def _lang(self) -> str:
        return getattr(self.settings, "lang", "en")
