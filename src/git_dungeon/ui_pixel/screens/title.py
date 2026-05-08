"""Title and loading screens for the pixel UI."""

from __future__ import annotations

from typing import Any

from git_dungeon.ui_pixel.game_runner import GameRunner, RunSummary
from git_dungeon.ui_pixel.screens.base import Screen, ScreenAction
from git_dungeon.ui_pixel.screens.dungeon import DungeonScreen
from git_dungeon.ui_pixel.screens.settings import SettingsScreen
from git_dungeon.ui_pixel.text import audio_label, tr
from git_dungeon.ui_pixel.widgets import ACCENT, BAD, BG, GOOD, MUTED, TEXT, Button, draw_panel

TITLE_PLAYER_SPRITE_RECT = (42, 88, 32, 32)
TITLE_ENEMY_SPRITE_RECT = (260, 88, 32, 32)
TITLE_BANNER_RECT = (70, 20, 180, 46)
TITLE_ENTRANCE_RECT = (134, 72, 52, 52)
TITLE_TORCH_LEFT_RECT = (112, 82, 22, 22)
TITLE_TORCH_RIGHT_RECT = (186, 82, 22, 22)
TITLE_LOGO_POS = (82, 32)
TITLE_LOGO_WIDTH = 162
TITLE_LOGO_SIZE = 24
TITLE_SUBTITLE_POS = (112, 58)
TITLE_SUBTITLE_WIDTH = 108
TITLE_SUBTITLE_SIZE = 14
TITLE_STATUS_POS = (62, 122)
TITLE_BUTTON_START_RECT = (74, 132, 68, 18)
TITLE_BUTTON_SETTINGS_RECT = (156, 132, 80, 18)
TITLE_HELP_POS = (42, 154)
TITLE_FOOTER_POS = (42, 166)


class TitleScreen(Screen):
    def __init__(
        self,
        pygame_module: Any,
        fonts: Any,
        runner: GameRunner,
        assets: Any,
        audio: Any | None = None,
        settings: Any | None = None,
        settings_store: Any | None = None,
        settings_error: str = "",
    ) -> None:
        self.pygame = pygame_module
        self.fonts = fonts
        self.runner = runner
        self.assets = assets
        self.audio = audio
        self.settings = settings
        self.settings_store = settings_store
        self.settings_error = settings_error
        self.hover_pos: tuple[int, int] | None = None
        self.status = "Press Enter to load repository"
        self.anim_time = 0.0

    def enter(self) -> None:
        if self.audio is not None:
            self.audio.play_bgm("title")

    def update(self, dt: float) -> ScreenAction | None:
        self.anim_time += dt
        return None

    def handle(self, event: Any) -> ScreenAction | None:
        if event.type == self.pygame.KEYDOWN:
            if event.key in (self.pygame.K_ESCAPE, self.pygame.K_q):
                return ScreenAction.quit()
            if event.key == self.pygame.K_s:
                return self._open_settings()
            if event.key in (self.pygame.K_RETURN, self.pygame.K_SPACE):
                if self.audio is not None:
                    self.audio.play_sfx("ui_confirm")
                return ScreenAction.replace(
                    LoadingScreen(
                        self.pygame,
                        self.fonts,
                        self.runner,
                        self.assets,
                        self.audio,
                        self.settings,
                        self.settings_store,
                        self.settings_error,
                    )
                )
        if event.type == self.pygame.MOUSEMOTION:
            self.hover_pos = getattr(event, "logical_pos", None)
        if event.type == self.pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.hover_pos = getattr(event, "logical_pos", None)
            for key, button in self._buttons().items():
                if button.contains(self.hover_pos):
                    if key == "start":
                        return ScreenAction.replace(
                            LoadingScreen(
                                self.pygame,
                                self.fonts,
                                self.runner,
                                self.assets,
                                self.audio,
                                self.settings,
                                self.settings_store,
                                self.settings_error,
                            )
                        )
                    if key == "settings":
                        return self._open_settings()
        return None

    def draw(self, surface: Any) -> None:
        lang = self._lang()
        surface.fill(BG)
        self._draw_backdrop(surface)
        draw_panel(self.pygame, surface, (18, 14, 284, 152))
        self.assets.draw(surface, "title_banner", TITLE_BANNER_RECT)
        self.fonts.draw_fit(
            surface,
            "GIT DUNGEON",
            TITLE_LOGO_POS,
            TITLE_LOGO_WIDTH,
            ACCENT,
            TITLE_LOGO_SIZE,
        )
        self.fonts.draw_fit(
            surface,
            "像素模式" if lang == "zh_CN" else "PIXEL MODE",
            TITLE_SUBTITLE_POS,
            TITLE_SUBTITLE_WIDTH,
            TEXT,
            TITLE_SUBTITLE_SIZE,
        )
        torch_lift = 1 if int(self.anim_time * 6) % 2 else 0
        self.assets.draw(surface, "dungeon_entrance", TITLE_ENTRANCE_RECT)
        self.assets.draw(
            surface,
            "torch_lit",
            (TITLE_TORCH_LEFT_RECT[0], TITLE_TORCH_LEFT_RECT[1] - torch_lift, 22, 22),
        )
        self.assets.draw(
            surface,
            "torch_lit",
            (TITLE_TORCH_RIGHT_RECT[0], TITLE_TORCH_RIGHT_RECT[1] - torch_lift, 22, 22),
        )
        self.assets.draw(surface, "player_idle", TITLE_PLAYER_SPRITE_RECT)
        self.assets.draw(surface, "ci_sentinel", TITLE_ENEMY_SPRITE_RECT)
        self.fonts.draw_fit(surface, tr(self.status, lang), TITLE_STATUS_POS, 196, MUTED, 13)
        for button in self._buttons().values():
            button.draw(self.pygame, surface, self.fonts, button.contains(self.hover_pos))
        self.fonts.draw_fit(
            surface,
            tr("Enter: Start   S: Settings   Esc/Q: Quit", lang),
            TITLE_HELP_POS,
            238,
            TEXT,
            13,
        )
        if self.settings_error:
            self.fonts.draw_fit(surface, self.settings_error, TITLE_FOOTER_POS, 144, BAD, 11)
        if self.audio is not None:
            label = audio_label(self.audio.status().label(), lang)
            if label:
                self.fonts.draw_fit(surface, label, (194, TITLE_FOOTER_POS[1]), 86, MUTED, 11)

    def _draw_backdrop(self, surface: Any) -> None:
        for x in range(0, 320, 16):
            self.assets.draw(surface, "tile_wall_stone", (x, 0, 16, 16))
            self.assets.draw(surface, "tile_floor_stone", (x, 164, 16, 16))
        for y in range(16, 164, 16):
            self.assets.draw(surface, "tile_wall_stone", (0, y, 16, 16))
            self.assets.draw(surface, "tile_wall_stone", (304, y, 16, 16))

    def _buttons(self) -> dict[str, Button]:
        lang = self._lang()
        return {
            "start": Button(TITLE_BUTTON_START_RECT, tr("Start", lang)),
            "settings": Button(TITLE_BUTTON_SETTINGS_RECT, tr("Settings", lang)),
        }

    def _open_settings(self) -> ScreenAction | None:
        if self.settings is None or self.settings_store is None:
            return None
        if self.audio is not None:
            self.audio.play_sfx("ui_confirm")
        return ScreenAction.push(
            SettingsScreen(
                self.pygame,
                self.fonts,
                self.settings,
                self.settings_store,
                self.audio,
                self.settings_error,
                self._apply_settings,
            )
        )

    def _apply_settings(self, settings: Any) -> None:
        self.settings = settings
        self.fonts.set_lang(settings.lang)
        if self.audio is not None:
            self.audio.set_volumes(settings.bgm_volume, settings.sfx_volume)

    def _lang(self) -> str:
        return getattr(self.settings, "lang", "en")


class LoadingScreen(Screen):
    def __init__(
        self,
        pygame_module: Any,
        fonts: Any,
        runner: GameRunner,
        assets: Any,
        audio: Any | None = None,
        settings: Any | None = None,
        settings_store: Any | None = None,
        settings_error: str = "",
    ) -> None:
        self.pygame = pygame_module
        self.fonts = fonts
        self.runner = runner
        self.assets = assets
        self.audio = audio
        self.settings = settings
        self.settings_store = settings_store
        self.settings_error = settings_error
        self.started = False
        self.summary: RunSummary | None = None
        self.error: str | None = None

    def update(self, dt: float) -> ScreenAction | None:
        if self.started:
            return None
        self.started = True
        try:
            self.summary = self.runner.load_repository()
        except Exception as exc:
            self.error = str(exc)
            return None
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

    def handle(self, event: Any) -> ScreenAction | None:
        if event.type == self.pygame.KEYDOWN and event.key in (
            self.pygame.K_ESCAPE,
            self.pygame.K_q,
            self.pygame.K_RETURN,
        ):
            return ScreenAction.quit()
        return None

    def draw(self, surface: Any) -> None:
        surface.fill(BG)
        draw_panel(self.pygame, surface, (14, 18, 292, 144))
        lang = getattr(self.settings, "lang", "en")
        self.fonts.draw(surface, tr("LOADING REPOSITORY", lang), (50, 34), ACCENT, 22)

        if self.error:
            self.fonts.draw(surface, tr("Load failed", lang), (32, 70), BAD, 18)
            self.fonts.draw_fit(surface, self.error, (32, 94), 244, TEXT, 16)
            self.fonts.draw(surface, tr("Enter/Esc: Quit", lang), (32, 128), MUTED, 16)
            return

        if self.summary is None:
            self.fonts.draw(surface, tr("Reading git history...", lang), (32, 82), MUTED, 16)
            if self.audio is not None:
                label = audio_label(self.audio.status().label(), lang)
                if label:
                    self.fonts.draw_fit(surface, label, (32, 118), 240, MUTED, 13)
            if self.settings_error:
                self.fonts.draw_fit(surface, self.settings_error, (32, 136), 244, BAD, 12)
            return

        self.fonts.draw(surface, tr("Repository loaded", lang), (32, 64), GOOD, 18)
