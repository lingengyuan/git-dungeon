"""Shop node screen."""

from __future__ import annotations

from typing import Any

from git_dungeon.ui_pixel.screens.base import Screen, ScreenAction
from git_dungeon.ui_pixel.screens.map import MapScreen
from git_dungeon.ui_pixel.widgets import ACCENT, BAD, BG, GOOD, MUTED, TEXT, Button, draw_panel


class ShopScreen(Screen):
    def __init__(
        self,
        pygame_module: Any,
        fonts: Any,
        runner: Any,
        assets: Any,
        audio: Any | None = None,
    ) -> None:
        self.pygame = pygame_module
        self.fonts = fonts
        self.runner = runner
        self.assets = assets
        self.audio = audio
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
        draw_panel(self.pygame, surface, (14, 12, 292, 156))
        self.assets.draw(surface, "node_shop", (26, 24, 24, 24))
        player = self.runner.player_snapshot()
        self.fonts.draw(surface, "SHOP", (58, 24), ACCENT, 22)
        self.fonts.draw(surface, f"Gold {player.gold}", (220, 28), TEXT, 15)

        for offer in self.offers:
            y = 58 + offer.index * 30
            color = TEXT if offer.affordable else MUTED
            self.fonts.draw(surface, f"{offer.index + 1}. {offer.label}", (28, y), color, 15)
            detail = (
                f"cost {offer.cost} hp {offer.heal} atk {offer.attack} "
                f"mp {offer.mp} maxhp {offer.max_hp}"
            )
            self.fonts.draw(surface, detail[:38], (42, y + 13), MUTED, 12)
            if not offer.affordable:
                self.fonts.draw(surface, "not enough gold", (196, y), BAD, 12)

        for index, button in self._buttons().items():
            offer = self.offers[index]
            button.enabled = offer.affordable
            button.draw(self.pygame, surface, self.fonts, button.contains(self.hover_pos))
        skip = self._skip_button()
        skip.draw(self.pygame, surface, self.fonts, skip.contains(self.hover_pos))
        self.fonts.draw(surface, self.message[:34], (28, 148), GOOD, 13)

    def _buttons(self) -> dict[int, Button]:
        return {
            offer.index: Button((236, 56 + offer.index * 30, 44, 18), "Buy", enabled=offer.affordable)
            for offer in self.offers
        }

    def _skip_button(self) -> Button:
        return Button((236, 134, 44, 18), "Skip")

    def _choose(self, index: int | None) -> ScreenAction:
        if index is not None and not self.offers[index].affordable:
            self.message = "Not enough gold"
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
            )
        )
