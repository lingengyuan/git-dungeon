"""Shop node screen."""

from __future__ import annotations

from typing import Any

from git_dungeon.ui_pixel.screens.base import Screen, ScreenAction
from git_dungeon.ui_pixel.screens.map import MapScreen
from git_dungeon.ui_pixel.text import tr
from git_dungeon.ui_pixel.widgets import ACCENT, BAD, BG, GOOD, MUTED, TEXT, Button, draw_panel


class ShopScreen(Screen):
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
        self.offers = runner.shop_offers()
        self.message = "Unavailable items are disabled"

    def handle(self, event: Any) -> ScreenAction | None:
        if event.type == self.pygame.KEYDOWN:
            if event.key == self.pygame.K_ESCAPE or event.key == self.pygame.K_0:
                return self._choose(None)
            for idx, key in enumerate((self.pygame.K_1, self.pygame.K_2, self.pygame.K_3)):
                if event.key == key and idx < len(self.offers):
                    return self._choose(idx)
        if event.type == self.pygame.MOUSEMOTION:
            self.hover_pos = getattr(event, "logical_pos", None)
        if event.type == self.pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.hover_pos = getattr(event, "logical_pos", None)
            if self._skip_button().contains(self.hover_pos):
                return self._choose(None)
            for index, button in self._buttons().items():
                if button.contains(self.hover_pos) and button.enabled:
                    return self._choose(index)
        return None

    def draw(self, surface: Any) -> None:
        surface.fill(BG)
        lang = self._lang()
        draw_panel(self.pygame, surface, (14, 12, 292, 156))
        self.assets.draw(surface, "node_shop", (26, 24, 24, 24))
        player = self.runner.player_snapshot()
        self.fonts.draw(surface, tr("SHOP", lang), (58, 24), ACCENT, 22)
        self.fonts.draw(surface, f"{tr('Gold', lang)} {player.gold}", (210, 28), TEXT, 15)

        for offer in self.offers:
            y = 58 + offer.index * 30
            color = TEXT if offer.affordable else MUTED
            self.fonts.draw_fit(surface, f"{offer.index + 1}. {offer.label}", (28, y), 150, color, 15)
            detail = (
                f"cost {offer.cost} hp {offer.heal} atk {offer.attack} "
                f"mp {offer.mp} maxhp {offer.max_hp}"
            )
            self.fonts.draw_fit(surface, detail, (42, y + 13), 184, MUTED, 12)
            if not offer.affordable:
                self.fonts.draw(surface, tr("not enough gold", lang), (176, y), BAD, 12)

        for index, button in self._buttons().items():
            offer = self.offers[index]
            button.enabled = offer.affordable
            button.draw(self.pygame, surface, self.fonts, button.contains(self.hover_pos))
        skip = self._skip_button()
        skip.draw(self.pygame, surface, self.fonts, skip.contains(self.hover_pos))
        self.fonts.draw_fit(surface, tr(self.message, lang), (28, 148), 200, GOOD, 13)

    def _buttons(self) -> dict[int, Button]:
        return {
            offer.index: Button((236, 56 + offer.index * 30, 44, 18), tr("Buy", self._lang()), enabled=offer.affordable)
            for offer in self.offers
        }

    def _skip_button(self) -> Button:
        return Button((236, 134, 44, 18), tr("Skip", self._lang()))

    def _choose(self, index: int | None) -> ScreenAction:
        if index is not None and not self.offers[index].affordable:
            self.message = tr("Not enough gold", self._lang())
            if self.audio is not None:
                self.audio.play_sfx("ui_denied")
            return None
        result = self.runner.resolve_current_shop(index)
        if self.audio is not None:
            self.audio.play_sfx("economy" if index is not None else "ui_cancel")
        return ScreenAction.replace(
            MapScreen(
                self.pygame,
                self.fonts,
                self.runner,
                self.assets,
                message=f"Shop: {result.message}",
                audio=self.audio,
                settings=self.settings,
            )
        )

    def _lang(self) -> str:
        return getattr(self.settings, "lang", "en")
