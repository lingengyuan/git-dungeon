"""First-run tutorial for PC pixel play."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from git_dungeon.ui_pixel.screens.base import Screen, ScreenAction
from git_dungeon.ui_pixel.screens.dungeon import DungeonScreen
from git_dungeon.ui_pixel.text import tr
from git_dungeon.ui_pixel.widgets import ACCENT, BAD, BG, GOOD, MUTED, TEXT, Button, draw_panel

TUTORIAL_PANEL = (18, 14, 284, 152)
TUTORIAL_STAGE = (32, 42, 256, 56)
TUTORIAL_BUTTON = (206, 136, 74, 18)
TUTORIAL_LINES = (
    ("Move: arrows, WASD, or click next room", TEXT),
    ("Confirm: enter glowing rooms and choose", GOOD),
    ("Pause: Esc/Q; traps hurt, caches help", ACCENT),
)


class TutorialScreen(Screen):
    def __init__(
        self,
        pygame_module: Any,
        fonts: Any,
        runner: Any,
        assets: Any,
        *,
        settings: Any,
        settings_store: Any,
        audio: Any | None = None,
    ) -> None:
        self.pygame = pygame_module
        self.fonts = fonts
        self.runner = runner
        self.assets = assets
        self.settings = settings
        self.settings_store = settings_store
        self.audio = audio
        self.hover_pos: tuple[int, int] | None = None
        self.message = "Learn the PC controls before entering the run"

    def handle(self, event: Any) -> ScreenAction | None:
        if event.type == self.pygame.KEYDOWN:
            if event.key in (self.pygame.K_RETURN, self.pygame.K_SPACE):
                return self._finish()
            if event.key in (self.pygame.K_ESCAPE, self.pygame.K_q):
                return self._finish()
        if event.type == self.pygame.MOUSEMOTION:
            self.hover_pos = getattr(event, "logical_pos", None)
        if event.type == self.pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.hover_pos = getattr(event, "logical_pos", None)
            if self._start_button().contains(self.hover_pos):
                return self._finish()
        return None

    def draw(self, surface: Any) -> None:
        lang = self._lang()
        surface.fill(BG)
        draw_panel(self.pygame, surface, TUTORIAL_PANEL)
        self.fonts.draw(surface, tr("FIRST RUN", lang), (32, 26), ACCENT, 22)
        self.fonts.draw_fit(surface, tr(self.message, lang), (138, 30), 146, MUTED, 12)
        self._draw_stage(surface)
        for index, (line, color) in enumerate(TUTORIAL_LINES):
            y = 108 + index * 13
            self.fonts.draw_fit(surface, tr(line, lang), (36, y), 174, color, 9)
        button = self._start_button()
        button.draw(self.pygame, surface, self.fonts, button.contains(self.hover_pos))

    def _draw_stage(self, surface: Any) -> None:
        x, y, w, h = TUTORIAL_STAGE
        self.pygame.draw.rect(surface, (22, 20, 30), TUTORIAL_STAGE)
        for tile_x in range(x, x + w, 16):
            self.assets.draw(surface, "tile_floor_stone", (tile_x, y + h - 16, 16, 16))
            self.assets.draw(surface, "tile_wall_stone", (tile_x, y, 16, 16))
        self.assets.draw(surface, "player_idle", (48, 62, 24, 24))
        self.assets.draw(surface, "room_marker_current", (108, 62, 22, 22))
        self.assets.draw(surface, "merge_conflict_trap", (166, 62, 22, 22))
        self.assets.draw(surface, "commit_shard", (224, 62, 22, 22))
        self.pygame.draw.line(surface, ACCENT, (76, 74), (104, 74), 1)
        self.pygame.draw.line(surface, BAD, (134, 74), (162, 74), 1)
        self.pygame.draw.line(surface, GOOD, (190, 74), (220, 74), 1)
        self.pygame.draw.rect(surface, ACCENT, TUTORIAL_STAGE, 1)

    def _finish(self) -> ScreenAction:
        next_settings = replace(self.settings, tutorial_seen=True).normalized()
        try:
            self.settings_store.save(next_settings)
            self.settings = next_settings
            if self.audio is not None:
                self.audio.play_sfx("ui_confirm")
        except OSError as exc:
            self.message = f"{tr('Save tutorial state failed', self._lang())}: {exc}"
            if self.audio is not None:
                self.audio.play_sfx("ui_denied")
            return None
        return ScreenAction.replace(
            DungeonScreen(
                self.pygame,
                self.fonts,
                self.runner,
                self.assets,
                audio=self.audio,
                settings=self.settings,
                settings_store=self.settings_store,
            )
        )

    def _start_button(self) -> Button:
        return Button(TUTORIAL_BUTTON, tr("Start Run", self._lang()))

    def _lang(self) -> str:
        return getattr(self.settings, "lang", "en")
