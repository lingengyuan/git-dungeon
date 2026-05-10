"""Shop node screen."""

from __future__ import annotations

from typing import Any

from git_dungeon.ui_pixel.screens.base import Screen, ScreenAction
from git_dungeon.ui_pixel.screens.dungeon import DungeonScreen
from git_dungeon.ui_pixel.text import (
    shop_offer_detail,
    shop_offer_title,
    shop_result_feedback,
    stat_value,
    tr,
)
from git_dungeon.ui_pixel.widgets import (
    ACCENT,
    BAD,
    BG,
    TEXT,
    Button,
    draw_action_bar,
    draw_item_card,
    draw_location_stage,
    draw_panel,
)

SHOP_SKIP_BUTTON_RECT = (236, 157, 44, 16)
SHOP_ACTION_BAR_RESERVE = 70
SHOP_STAGE_RECT = (22, 22, 276, 44)
SHOP_GROUND_Y = 54
SHOPKEEPER_RECT = (34, 30, 34, 34)
SHOP_COUNTER_RECT = (72, 31, 50, 32)
SHOP_OFFER_X = 28
SHOP_OFFER_Y = 70
SHOP_OFFER_GAP = 28
SHOP_OFFER_W = 196
SHOP_OFFER_H = 26
SHOP_BUY_X = 236
SHOP_BUY_Y = 74


class ShopScreen(Screen):
    def __init__(
        self,
        pygame_module: Any,
        fonts: Any,
        runner: Any,
        assets: Any,
        audio: Any | None = None,
        settings: Any | None = None,
        settings_store: Any | None = None,
        settings_error: str = "",
        apply_display_mode: Any | None = None,
    ) -> None:
        self.pygame = pygame_module
        self.fonts = fonts
        self.runner = runner
        self.assets = assets
        self.audio = audio
        self.settings = settings
        self.settings_store = settings_store
        self.settings_error = settings_error
        self.apply_display_mode = apply_display_mode
        self.hover_pos: tuple[int, int] | None = None
        self.offers = runner.shop_offers()
        self.message = "Unavailable items are disabled"

    def handle(self, event: Any) -> ScreenAction | None:
        if event.type == self.pygame.KEYDOWN:
            if event.key in (self.pygame.K_ESCAPE, self.pygame.K_q):
                from git_dungeon.ui_pixel.screens.pause import PauseScreen

                return ScreenAction.push(
                    PauseScreen(
                        self.pygame,
                        self.fonts,
                        self.settings,
                        self.audio,
                        self.runner,
                        self.assets,
                        self.settings_store,
                        self.settings_error,
                        self.apply_display_mode,
                    )
                )
            if event.key == self.pygame.K_0:
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
        draw_panel(self.pygame, surface, (14, 12, 292, 142))
        draw_location_stage(
            self.pygame,
            surface,
            self.assets,
            SHOP_STAGE_RECT,
            ground_y=SHOP_GROUND_Y,
        )
        self.assets.draw(surface, "shopkeeper", SHOPKEEPER_RECT)
        self.assets.draw(surface, "shop_counter", SHOP_COUNTER_RECT)
        player = self.runner.player_snapshot()
        self.fonts.draw(surface, tr("SHOP", lang), (132, 26), ACCENT, 22)
        self.fonts.draw_fit(surface, stat_value("gold", player.gold, lang), (202, 30), 82, TEXT, 15)

        for offer in self.offers:
            rect = (
                SHOP_OFFER_X,
                SHOP_OFFER_Y + offer.index * SHOP_OFFER_GAP,
                SHOP_OFFER_W,
                SHOP_OFFER_H,
            )
            button = self._buttons()[offer.index]
            title = f"{offer.index + 1}. {shop_offer_title(offer.label, lang)}"
            detail = shop_offer_detail(offer, lang)
            draw_item_card(
                self.pygame,
                surface,
                self.fonts,
                rect,
                title,
                detail,
                disabled=not offer.affordable,
                hover=button.contains(self.hover_pos),
            )
            if not offer.affordable:
                self.fonts.draw_fit(
                    surface, tr("not enough gold", lang), (164, rect[1] + 5), 58, BAD, 11
                )

        for index, button in self._buttons().items():
            offer = self.offers[index]
            button.enabled = offer.affordable
            button.draw(self.pygame, surface, self.fonts, button.contains(self.hover_pos))
        draw_action_bar(
            self.pygame,
            surface,
            self.fonts,
            tr(self.message, lang),
            reserve_right=SHOP_ACTION_BAR_RESERVE,
            alert=self.message == "Not enough gold",
        )
        skip = self._skip_button()
        skip.draw(self.pygame, surface, self.fonts, skip.contains(self.hover_pos))

    def _buttons(self) -> dict[int, Button]:
        return {
            offer.index: Button(
                (SHOP_BUY_X, SHOP_BUY_Y + offer.index * SHOP_OFFER_GAP, 44, 18),
                tr("Buy", self._lang()),
                enabled=offer.affordable,
                tooltip=tr("not enough gold", self._lang()),
            )
            for offer in self.offers
        }

    def _skip_button(self) -> Button:
        return Button(SHOP_SKIP_BUTTON_RECT, tr("Skip", self._lang()))

    def _choose(self, index: int | None) -> ScreenAction | None:
        if index is not None and not self.offers[index].affordable:
            self.message = "Not enough gold"
            if self.audio is not None:
                self.audio.play_sfx("ui_denied")
            return None
        result = self.runner.resolve_current_shop(index)
        if self.audio is not None:
            self.audio.play_sfx("economy" if index is not None else "ui_cancel")
        return ScreenAction.replace(
            DungeonScreen(
                self.pygame,
                self.fonts,
                self.runner,
                self.assets,
                message=shop_result_feedback(result.message, self._lang()),
                audio=self.audio,
                settings=self.settings,
                settings_store=self.settings_store,
                settings_error=self.settings_error,
                apply_display_mode=self.apply_display_mode,
            )
        )

    def _lang(self) -> str:
        return getattr(self.settings, "lang", "en")
