"""Pygame application shell for the pixel UI."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from git_dungeon.ui_pixel.assets import SpriteCatalog
from git_dungeon.ui_pixel.audio import AudioManager
from git_dungeon.ui_pixel.game_runner import GameRunner
from git_dungeon.ui_pixel.layout import scale_rect, window_to_logical
from git_dungeon.ui_pixel.screens.base import Screen, ScreenAction
from git_dungeon.ui_pixel.screens.title import LoadingScreen, TitleScreen
from git_dungeon.ui_pixel.settings import PixelSettingsStore

LOGICAL_SIZE = (320, 180)
WINDOW_SIZE = (1280, 720)
FPS = 60

BG = (17, 16, 24)
SURFACE = (33, 31, 45)
TEXT = (238, 232, 213)
MUTED = (148, 139, 130)
ACCENT = (235, 177, 88)
GOOD = (99, 199, 122)
BAD = (219, 87, 87)


@dataclass(frozen=True)
class PixelRunConfig:
    repo_path: str
    seed: int | None = None
    lang: str | None = None
    content_pack_args: list[str] | None = None
    smoke_frames: int | None = None


class ScreenStack:
    def __init__(self, screens: Sequence[Screen]) -> None:
        self._screens = list(screens)
        for screen in self._screens:
            screen.enter()

    @property
    def is_empty(self) -> bool:
        return not self._screens

    @property
    def top(self) -> Screen:
        return self._screens[-1]

    def apply(self, action: ScreenAction) -> None:
        if action.kind == "quit":
            while self._screens:
                self._screens.pop().exit()
            return
        if action.kind == "pop":
            if self._screens:
                self._screens.pop().exit()
            return
        if action.kind == "replace":
            if self._screens:
                self._screens.pop().exit()
            if action.screen is not None:
                self._screens.append(action.screen)
                action.screen.enter()
            return
        if action.kind == "push" and action.screen is not None:
            self._screens.append(action.screen)
            action.screen.enter()


class PixelFont:
    def __init__(self, pygame_module, lang: str = "en") -> None:
        self._pygame = pygame_module
        self.lang = lang
        root = Path(__file__).resolve().parents[3]
        self._latin_font = root / "assets" / "fonts" / "vt323" / "VT323-Regular.ttf"
        self._cjk_font = (
            root
            / "assets"
            / "fonts"
            / "ark_pixel"
            / "ark-pixel-12px-proportional-zh_cn.ttf"
        )
        self._cache: dict[tuple[str, int], object] = {}

    def get(self, size: int):
        family = "cjk" if self.lang == "zh_CN" else "latin"
        key = (family, size)
        if key not in self._cache:
            path = self._cjk_font if family == "cjk" and self._cjk_font.exists() else self._latin_font
            self._cache[key] = self._pygame.font.Font(str(path) if path.exists() else None, size)
        return self._cache[key]

    def set_lang(self, lang: str) -> None:
        self.lang = lang

    def measure(self, text: str, size: int = 16) -> int:
        return self.get(size).size(text)[0]

    def fit(self, text: str, max_width: int, size: int = 16) -> str:
        if self.measure(text, size) <= max_width:
            return text
        suffix = "..."
        available = max(1, max_width - self.measure(suffix, size))
        result = ""
        for char in text:
            if self.measure(result + char, size) > available:
                break
            result += char
        return (result or text[:1]) + suffix

    def draw(self, surface, text: str, pos: tuple[int, int], color=TEXT, size: int = 16) -> None:
        img = self.get(size).render(text, False, color)
        surface.blit(img, pos)

    def draw_fit(
        self,
        surface,
        text: str,
        pos: tuple[int, int],
        max_width: int,
        color=TEXT,
        size: int = 16,
    ) -> None:
        self.draw(surface, self.fit(text, max_width, size), pos, color, size)


def _import_pygame():
    try:
        import pygame
    except ImportError as exc:
        raise RuntimeError('Pixel mode requires: pip install -e ".[pixel]"') from exc
    return pygame


def run(
    repo_path: str,
    seed: int | None = None,
    lang: str | None = None,
    content_pack_args: list[str] | None = None,
    smoke_frames: int | None = None,
) -> int:
    """Run the interactive pixel shell."""
    pygame = _import_pygame()
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
    pygame.init()
    try:
        settings_store = PixelSettingsStore()
        settings_result = settings_store.load(lang_override=lang)
        settings = settings_result.settings
        display_flags = pygame.FULLSCREEN if settings.window_mode == "fullscreen" else 0
        window = pygame.display.set_mode(WINDOW_SIZE, display_flags)
        pygame.display.set_caption("Git Dungeon Pixel")
        surface = pygame.Surface(LOGICAL_SIZE)
        clock = pygame.time.Clock()
        fonts = PixelFont(pygame, settings.lang)
        assets = SpriteCatalog(pygame)
        assets.load()
        audio = AudioManager(pygame)
        audio.load()
        audio.set_volumes(settings.bgm_volume, settings.sfx_volume)
        runner = GameRunner(
            repo_path=repo_path,
            seed=seed,
            lang=settings.lang,
            content_pack_args=content_pack_args,
        )
        initial_screen: Screen
        if smoke_frames is not None:
            initial_screen = LoadingScreen(
                pygame,
                fonts,
                runner,
                assets,
                audio,
                settings,
                settings_store,
                settings_result.error,
            )
        else:
            initial_screen = TitleScreen(
                pygame,
                fonts,
                runner,
                assets,
                audio,
                settings,
                settings_store,
                settings_result.error,
            )
        stack = ScreenStack([initial_screen])
        frames = 0

        while not stack.is_empty:
            dt = clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    stack.apply(ScreenAction.quit())
                    break
                if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                    logical_pos = window_to_logical(
                        event.pos,
                        window.get_size(),
                        LOGICAL_SIZE,
                    )
                    event = pygame.event.Event(
                        event.type,
                        {**event.dict, "logical_pos": logical_pos},
                    )
                action = stack.top.handle(event)
                if action is not None:
                    stack.apply(action)
                    break
            if stack.is_empty:
                break

            action = stack.top.update(dt)
            if action is not None:
                stack.apply(action)
                if stack.is_empty:
                    break

            stack.top.draw(surface)
            window.fill(BG)
            dest_rect = scale_rect(LOGICAL_SIZE, window.get_size())
            pygame.transform.scale(surface, (dest_rect[2], dest_rect[3]), window.subsurface(dest_rect))
            pygame.display.flip()

            frames += 1
            if smoke_frames is not None and frames >= smoke_frames:
                stack.apply(ScreenAction.quit())

        return 0
    finally:
        pygame.quit()
