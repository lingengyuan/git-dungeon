"""Title and loading screens for the pixel UI."""

from __future__ import annotations

from typing import Any

from git_dungeon.ui_pixel.game_runner import GameRunner, RunSummary
from git_dungeon.ui_pixel.screens.base import Screen, ScreenAction
from git_dungeon.ui_pixel.screens.map import MapScreen
from git_dungeon.ui_pixel.screens.settings import SettingsScreen
from git_dungeon.ui_pixel.text import audio_label, tr
from git_dungeon.ui_pixel.widgets import ACCENT, BAD, BG, GOOD, MUTED, TEXT, Button, draw_panel


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

    def enter(self) -> None:
        if self.audio is not None:
            self.audio.play_bgm("title")

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
        draw_panel(self.pygame, surface, (18, 18, 284, 144))
        self.assets.draw(surface, "player_default", (36, 42, 32, 32))
        self.assets.draw(surface, "enemy_default", (252, 42, 32, 32))
        self.fonts.draw(surface, "GIT DUNGEON", (86, 42), ACCENT, 28)
        self.fonts.draw(surface, "PIXEL MODE", (112, 70), TEXT, 18)
        self.fonts.draw_fit(surface, tr(self.status, lang), (54, 100), 212, MUTED, 16)
        for button in self._buttons().values():
            button.draw(self.pygame, surface, self.fonts, button.contains(self.hover_pos))
        self.fonts.draw_fit(
            surface,
            tr("Enter: Start   S: Settings   Esc/Q: Quit", lang),
            (42, 132),
            238,
            TEXT,
            13,
        )
        if self.settings_error:
            self.fonts.draw_fit(surface, self.settings_error, (42, 146), 144, BAD, 11)
        if self.audio is not None:
            self.fonts.draw_fit(
                surface,
                audio_label(self.audio.status().label(), lang),
                (194, 146),
                86,
                MUTED,
                11,
            )

    def _buttons(self) -> dict[str, Button]:
        lang = self._lang()
        return {
            "start": Button((74, 112, 68, 18), tr("Start", lang)),
            "settings": Button((156, 112, 80, 18), tr("Settings", lang)),
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
            MapScreen(
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
                self.fonts.draw_fit(
                    surface,
                    audio_label(self.audio.status().label(), lang),
                    (32, 118),
                    240,
                    MUTED,
                    13,
                )
            if self.settings_error:
                self.fonts.draw_fit(surface, self.settings_error, (32, 136), 244, BAD, 12)
            return

        self.fonts.draw(surface, tr("Repository loaded", lang), (32, 64), GOOD, 18)
