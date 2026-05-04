"""Route map screen for the pixel UI."""

from __future__ import annotations

from typing import Any

from git_dungeon.ui_pixel.screens.base import Screen, ScreenAction
from git_dungeon.ui_pixel.text import audio_label, tr
from git_dungeon.ui_pixel.widgets import (
    ACCENT,
    BAD,
    BG,
    GOOD,
    MUTED,
    TEXT,
    Button,
    draw_panel,
    draw_stat_bar,
)


NODE_SPRITES = {
    "battle": "node_battle",
    "event": "node_event",
    "rest": "node_rest",
    "shop": "node_shop",
    "elite": "node_elite",
    "boss": "node_boss",
}


class MapScreen(Screen):
    def __init__(
        self,
        pygame_module: Any,
        fonts: Any,
        runner: Any,
        assets: Any,
        message: str = "Choose the current non-combat node",
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
        self.message = message

    def enter(self) -> None:
        if self.audio is not None:
            self.audio.play_bgm("chapter")

    def handle(self, event: Any) -> ScreenAction | None:
        if event.type == self.pygame.KEYDOWN:
            if event.key in (self.pygame.K_ESCAPE, self.pygame.K_q):
                return ScreenAction.quit()
            if event.key in (self.pygame.K_RETURN, self.pygame.K_SPACE):
                return self._open_current()
        if event.type == self.pygame.MOUSEMOTION:
            self.hover_pos = getattr(event, "logical_pos", None)
        if event.type == self.pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.hover_pos = getattr(event, "logical_pos", None)
            current_button = self._current_button()
            if current_button.contains(self.hover_pos) and current_button.enabled:
                return self._open_current()
        return None

    def draw(self, surface: Any) -> None:
        surface.fill(BG)
        lang = self._lang()
        player = self.runner.player_snapshot()
        current = self.runner.current_node_snapshot()
        nodes = self.runner.route_nodes()

        self.fonts.draw(surface, tr("ROUTE", lang), (12, 8), ACCENT, 22)
        self.fonts.draw_fit(surface, tr(self.message, lang), (82, 12), 212, MUTED, 15)
        draw_panel(self.pygame, surface, (10, 28, 300, 42))
        draw_stat_bar(self.pygame, surface, (20, 42, 92, 8), player.hp, player.max_hp, GOOD)
        self.fonts.draw(surface, f"HP {player.hp}/{player.max_hp}", (20, 52), TEXT, 13)
        draw_stat_bar(self.pygame, surface, (122, 42, 70, 8), player.mp, player.max_mp, ACCENT)
        self.fonts.draw(surface, f"MP {player.mp}/{player.max_mp}", (122, 52), TEXT, 13)
        self.fonts.draw(surface, f"ATK {player.attack}", (204, 40), TEXT, 14)
        self.fonts.draw(surface, f"{tr('Gold', lang)} {player.gold}", (204, 54), TEXT, 14)

        for index, node in enumerate(nodes):
            row = index // 6
            col = index % 6
            x = 18 + col * 48
            y = 84 + row * 38
            border = ACCENT if node.is_current else MUTED
            if node.is_visited:
                border = GOOD
            draw_panel(self.pygame, surface, (x - 3, y - 3, 38, 30), border=border)
            sprite_id = NODE_SPRITES.get(node.kind, "node_event")
            self.assets.draw(surface, sprite_id, (x + 6, y, 16, 16))
            label_color = TEXT if node.is_current else MUTED
            self.fonts.draw(surface, f"{node.position + 1:02d}", (x + 6, y + 17), label_color, 12)

        button = self._current_button()
        button.draw(self.pygame, surface, self.fonts, button.contains(self.hover_pos))

        if current is None:
            self.fonts.draw(surface, tr("No current node", lang), (18, 156), BAD, 14)
        elif not current.is_playable_now:
            self.fonts.draw(surface, tr("Node is not playable yet", lang), (18, 156), MUTED, 14)
        if self.audio is not None:
            self.fonts.draw_fit(
                surface,
                audio_label(self.audio.status().label(), lang),
                (204, 72),
                92,
                MUTED,
                12,
            )

    def _current_button(self) -> Button:
        current = self.runner.current_node_snapshot()
        lang = self._lang()
        label = tr("Open Node", lang)
        enabled = bool(current and current.is_playable_now)
        if current:
            label = tr(f"Open {current.kind.title()}", lang)
        return Button((202, 146, 96, 22), label, enabled=enabled)

    def _open_current(self) -> ScreenAction | None:
        current = self.runner.current_node()
        if current is None:
            self.message = "No current node"
            return None
        if current.kind.value in {"battle", "elite", "boss"}:
            from git_dungeon.ui_pixel.screens.battle import BattleScreen

            if self.audio is not None:
                self.audio.play_sfx("ui_confirm")
            return ScreenAction.replace(
                BattleScreen(self.pygame, self.fonts, self.runner, self.assets, self.audio, self.settings)
            )
        if current.kind.value == "event":
            from git_dungeon.ui_pixel.screens.event import EventScreen

            if self.audio is not None:
                self.audio.play_sfx("event")
            return ScreenAction.replace(
                EventScreen(self.pygame, self.fonts, self.runner, self.assets, self.audio, self.settings)
            )
        if current.kind.value == "rest":
            from git_dungeon.ui_pixel.screens.rest import RestScreen

            if self.audio is not None:
                self.audio.play_sfx("rest")
            return ScreenAction.replace(
                RestScreen(self.pygame, self.fonts, self.runner, self.assets, self.audio, self.settings)
            )
        if current.kind.value == "shop":
            from git_dungeon.ui_pixel.screens.shop import ShopScreen

            if self.audio is not None:
                self.audio.play_sfx("ui_confirm")
            return ScreenAction.replace(
                ShopScreen(self.pygame, self.fonts, self.runner, self.assets, self.audio, self.settings)
            )
        self.message = f"{current.kind.value.title()} is not playable yet"
        if self.audio is not None:
            self.audio.play_sfx("ui_denied")
        return None

    def _lang(self) -> str:
        return getattr(self.settings, "lang", "en")
