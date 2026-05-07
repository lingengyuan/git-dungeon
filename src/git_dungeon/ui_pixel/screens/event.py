"""Event node screen."""

from __future__ import annotations

from typing import Any

from git_dungeon.ui_pixel.screens.base import Screen, ScreenAction
from git_dungeon.ui_pixel.screens.dungeon import DungeonScreen
from git_dungeon.ui_pixel.text import (
    event_choice_label,
    event_description,
    event_effect_preview,
    event_result_feedback,
    event_title,
    tr,
)
from git_dungeon.ui_pixel.widgets import (
    ACCENT,
    BAD,
    BG,
    MUTED,
    TEXT,
    Button,
    draw_action_bar,
    draw_choice_card,
    draw_panel,
)


class EventScreen(Screen):
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
        self.event = runner.event_for_node()
        self.error = "" if self.event else "No event definition"

    def handle(self, event: Any) -> ScreenAction | None:
        if event.type == self.pygame.KEYDOWN:
            if event.key in (self.pygame.K_ESCAPE, self.pygame.K_q):
                from git_dungeon.ui_pixel.screens.pause import PauseScreen

                return ScreenAction.push(
                    PauseScreen(self.pygame, self.fonts, self.settings, self.audio)
                )
            if self.event:
                for idx, key in enumerate((self.pygame.K_1, self.pygame.K_2, self.pygame.K_3)):
                    if event.key == key and idx < len(self.event.choices):
                        return self._choose(idx)
        if event.type == self.pygame.MOUSEMOTION:
            self.hover_pos = getattr(event, "logical_pos", None)
        if event.type == self.pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.hover_pos = getattr(event, "logical_pos", None)
            for index, button in self._buttons().items():
                if button.contains(self.hover_pos) and button.enabled:
                    return self._choose(index)
        return None

    def draw(self, surface: Any) -> None:
        surface.fill(BG)
        lang = self._lang()
        draw_panel(self.pygame, surface, (14, 14, 292, 138))
        self.assets.draw(surface, "node_event", (28, 28, 24, 24))
        self.fonts.draw(surface, tr("EVENT", lang), (62, 28), ACCENT, 22)

        if not self.event:
            self.fonts.draw(surface, tr(self.error, lang), (32, 78), BAD, 16)
            return

        self.fonts.draw_fit(
            surface, event_title(self.event.event_id, lang), (62, 50), 190, TEXT, 15
        )
        self.fonts.draw_fit(
            surface,
            event_description(self.event.event_id, lang),
            (32, 66),
            210,
            MUTED,
            13,
        )
        for choice in self.event.choices:
            rect = (30, 80 + choice.index * 24, 188, 23)
            button = self._buttons()[choice.index]
            detail = event_effect_preview(choice.effects, lang)
            draw_choice_card(
                self.pygame,
                surface,
                self.fonts,
                rect,
                event_choice_label(choice.index, choice.effects, lang),
                detail,
                hover=button.contains(self.hover_pos),
            )

        for button in self._buttons().values():
            button.draw(self.pygame, surface, self.fonts, button.contains(self.hover_pos))
        draw_action_bar(
            self.pygame,
            surface,
            self.fonts,
            tr("Choose visibly; effects apply once", lang),
        )

    def _buttons(self) -> dict[int, Button]:
        if not self.event:
            return {}
        return {
            choice.index: Button((234, 83 + choice.index * 24, 48, 18), tr("Pick", self._lang()))
            for choice in self.event.choices[:3]
        }

    def _choose(self, index: int) -> ScreenAction:
        result = self.runner.resolve_current_event(index)
        if self.audio is not None:
            self.audio.play_sfx("event")
        return ScreenAction.replace(
            DungeonScreen(
                self.pygame,
                self.fonts,
                self.runner,
                self.assets,
                message=event_result_feedback(result.hp_delta, result.gold_delta, self._lang()),
                audio=self.audio,
                settings=self.settings,
            )
        )

    def _lang(self) -> str:
        return getattr(self.settings, "lang", "en")
