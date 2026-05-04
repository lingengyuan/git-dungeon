"""Event node screen."""

from __future__ import annotations

from typing import Any

from git_dungeon.ui_pixel.screens.base import Screen, ScreenAction
from git_dungeon.ui_pixel.screens.map import MapScreen
from git_dungeon.ui_pixel.text import tr
from git_dungeon.ui_pixel.widgets import ACCENT, BAD, BG, GOOD, MUTED, TEXT, Button, draw_panel


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
            if event.key == self.pygame.K_ESCAPE:
                if self.audio is not None:
                    self.audio.play_sfx("ui_cancel")
                return ScreenAction.replace(
                    MapScreen(
                        self.pygame,
                        self.fonts,
                        self.runner,
                        self.assets,
                        audio=self.audio,
                        settings=self.settings,
                    )
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
        draw_panel(self.pygame, surface, (14, 14, 292, 152))
        self.assets.draw(surface, "node_event", (28, 28, 24, 24))
        self.fonts.draw(surface, tr("EVENT", lang), (62, 28), ACCENT, 22)

        if not self.event:
            self.fonts.draw(surface, tr(self.error, lang), (32, 78), BAD, 16)
            return

        self.fonts.draw_fit(surface, self.event.event_id, (62, 50), 190, TEXT, 15)
        for choice in self.event.choices:
            y = 76 + choice.index * 28
            self.fonts.draw_fit(surface, f"{choice.index + 1}. {choice.choice_id}", (32, y), 176, TEXT, 15)
            detail = ", ".join(choice.effects) or tr("no effect", lang)
            self.fonts.draw_fit(surface, detail, (48, y + 13), 168, MUTED, 13)

        for button in self._buttons().values():
            button.draw(self.pygame, surface, self.fonts, button.contains(self.hover_pos))
        self.fonts.draw_fit(surface, tr("Choose visibly; effects apply once", lang), (32, 148), 248, GOOD, 13)

    def _buttons(self) -> dict[int, Button]:
        if not self.event:
            return {}
        return {
            choice.index: Button((234, 74 + choice.index * 28, 48, 18), tr("Pick", self._lang()))
            for choice in self.event.choices[:3]
        }

    def _choose(self, index: int) -> ScreenAction:
        result = self.runner.resolve_current_event(index)
        if self.audio is not None:
            self.audio.play_sfx("event")
        hp_text = f"HP {result.hp_delta:+d}" if result.hp_delta else "HP 0"
        gold_text = f"Gold {result.gold_delta:+d}" if result.gold_delta else "Gold 0"
        return ScreenAction.replace(
            MapScreen(
                self.pygame,
                self.fonts,
                self.runner,
                self.assets,
                message=f"Event: {result.choice_id} {hp_text} {gold_text}",
                audio=self.audio,
                settings=self.settings,
            )
        )

    def _lang(self) -> str:
        return getattr(self.settings, "lang", "en")
