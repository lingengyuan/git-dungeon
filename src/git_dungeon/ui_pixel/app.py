"""Pygame application shell for the pixel UI."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from git_dungeon.ui_pixel.assets import SpriteCatalog
from git_dungeon.ui_pixel.game_runner import GameRunner
from git_dungeon.ui_pixel.layout import scale_rect, window_to_logical
from git_dungeon.ui_pixel.screens.base import Screen, ScreenAction
from git_dungeon.ui_pixel.screens.title import LoadingScreen, TitleScreen

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
    lang: str = "en"
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
    def __init__(self, pygame_module) -> None:
        self._pygame = pygame_module
        self._cache: dict[int, object] = {}

    def get(self, size: int):
        if size not in self._cache:
            self._cache[size] = self._pygame.font.Font(None, size)
        return self._cache[size]

    def measure(self, text: str, size: int = 16) -> int:
        return self.get(size).size(text)[0]

    def draw(self, surface, text: str, pos: tuple[int, int], color=TEXT, size: int = 16) -> None:
        img = self.get(size).render(text, False, color)
        surface.blit(img, pos)


def _import_pygame():
    try:
        import pygame
    except ImportError as exc:
        raise RuntimeError('Pixel mode requires: pip install -e ".[pixel]"') from exc
    return pygame


def run(
    repo_path: str,
    seed: int | None = None,
    lang: str = "en",
    content_pack_args: list[str] | None = None,
    smoke_frames: int | None = None,
) -> int:
    """Run the interactive pixel shell."""
    pygame = _import_pygame()
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
    pygame.init()
    try:
        window = pygame.display.set_mode(WINDOW_SIZE)
        pygame.display.set_caption("Git Dungeon Pixel")
        surface = pygame.Surface(LOGICAL_SIZE)
        clock = pygame.time.Clock()
        fonts = PixelFont(pygame)
        assets = SpriteCatalog(pygame)
        assets.load()
        runner = GameRunner(
            repo_path=repo_path,
            seed=seed,
            lang=lang,
            content_pack_args=content_pack_args,
        )
        initial_screen: Screen
        if smoke_frames is not None:
            initial_screen = LoadingScreen(pygame, fonts, runner, assets)
        else:
            initial_screen = TitleScreen(pygame, fonts, runner, assets)
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
