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
    draw_location_stage,
    draw_panel,
)

EVENT_STAGE_RECT = (22, 24, 276, 50)
EVENT_GROUND_Y = 62
EVENT_LOCATION_RECT = (34, 36, 34, 34)
EVENT_TITLE_POS = (78, 31)
EVENT_DESC_POS = (78, 51)
EVENT_CHOICE_X = 30
EVENT_CHOICE_Y = 80
EVENT_CHOICE_GAP = 24
EVENT_CHOICE_RECT = (EVENT_CHOICE_X, EVENT_CHOICE_Y, 188, 23)
EVENT_BUTTON_X = 234
EVENT_BUTTON_Y = 83


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
        draw_location_stage(
            self.pygame,
            surface,
            self.assets,
            EVENT_STAGE_RECT,
            ground_y=EVENT_GROUND_Y,
        )
        self.assets.draw(surface, self._location_sprite(), EVENT_LOCATION_RECT)
        self.fonts.draw(surface, tr("EVENT", lang), EVENT_TITLE_POS, ACCENT, 22)

        if not self.event:
            self.fonts.draw(surface, tr(self.error, lang), (32, 78), BAD, 16)
            return

        self.fonts.draw_fit(
            surface, event_title(self.event.event_id, lang), (176, 33), 102, TEXT, 13
        )
        self.fonts.draw_fit(
            surface,
            event_description(self.event.event_id, lang),
            EVENT_DESC_POS,
            194,
            MUTED,
            12,
        )
        for choice in self.event.choices:
            rect = (EVENT_CHOICE_X, EVENT_CHOICE_Y + choice.index * EVENT_CHOICE_GAP, 188, 23)
            button = self._buttons()[choice.index]
            detail = event_effect_preview(choice.effects, lang)
            draw_choice_card(
                self.pygame,
                surface,
                self.fonts,
                rect,
                f"  {event_choice_label(choice.index, choice.effects, lang)}",
                detail,
                hover=button.contains(self.hover_pos),
            )
            self.assets.draw(
                surface,
                self._choice_sprite(choice.effects),
                (rect[0] + 5, rect[1] + 4, 14, 14),
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
            choice.index: Button(
                (EVENT_BUTTON_X, EVENT_BUTTON_Y + choice.index * EVENT_CHOICE_GAP, 48, 18),
                tr("Pick", self._lang()),
            )
            for choice in self.event.choices[:3]
        }

    def _location_sprite(self) -> str:
        if not self.event:
            return "event_shrine"
        event_id = str(getattr(self.event, "event_id", ""))
        return "event_terminal_ruin" if sum(ord(char) for char in event_id) % 2 else "event_shrine"

    @staticmethod
    def _choice_sprite(effects: tuple[str, ...]) -> str:
        risky = {"take_damage", "lose_health", "lose_gold", "trigger_battle", "start_battle"}
        return (
            "choice_icon_risk"
            if any(effect in risky for effect in effects)
            else "choice_icon_reward"
        )

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
