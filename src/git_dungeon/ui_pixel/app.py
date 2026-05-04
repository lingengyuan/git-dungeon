"""Pygame application shell for the pixel UI."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from git_dungeon.ui_pixel.game_runner import GameRunner, RunSummary
from git_dungeon.ui_pixel.screens.base import Screen, ScreenAction

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

    def draw(self, surface, text: str, pos: tuple[int, int], color=TEXT, size: int = 16) -> None:
        img = self.get(size).render(text, False, color)
        surface.blit(img, pos)


class TitleScreen(Screen):
    def __init__(self, pygame_module, fonts: PixelFont, runner: GameRunner) -> None:
        self.pygame = pygame_module
        self.fonts = fonts
        self.runner = runner
        self.status = "Press Enter to load repository"
        self.summary: RunSummary | None = None
        self.error: str | None = None

    def handle(self, event) -> ScreenAction | None:
        if event.type == self.pygame.KEYDOWN:
            if event.key in (self.pygame.K_ESCAPE, self.pygame.K_q):
                return ScreenAction.quit()
            if event.key in (self.pygame.K_RETURN, self.pygame.K_SPACE):
                return ScreenAction.replace(LoadingScreen(self.pygame, self.fonts, self.runner))
        return None

    def draw(self, surface) -> None:
        surface.fill(BG)
        self.pygame.draw.rect(surface, SURFACE, (18, 18, 284, 144))
        self.pygame.draw.rect(surface, ACCENT, (18, 18, 284, 144), 1)

        self.fonts.draw(surface, "GIT DUNGEON", (86, 42), ACCENT, 28)
        self.fonts.draw(surface, "PIXEL MODE", (112, 70), TEXT, 18)
        self.fonts.draw(surface, self.status, (62, 110), MUTED, 16)
        self.fonts.draw(surface, "Enter: Start   Esc/Q: Quit", (62, 132), TEXT, 16)


class LoadingScreen(Screen):
    def __init__(self, pygame_module, fonts: PixelFont, runner: GameRunner) -> None:
        self.pygame = pygame_module
        self.fonts = fonts
        self.runner = runner
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

    def handle(self, event) -> ScreenAction | None:
        if event.type == self.pygame.KEYDOWN and event.key in (
            self.pygame.K_ESCAPE,
            self.pygame.K_q,
            self.pygame.K_RETURN,
        ):
            return ScreenAction.quit()
        return None

    def draw(self, surface) -> None:
        surface.fill(BG)
        self.pygame.draw.rect(surface, SURFACE, (14, 18, 292, 144))
        self.pygame.draw.rect(surface, ACCENT, (14, 18, 292, 144), 1)
        self.fonts.draw(surface, "LOADING REPOSITORY", (50, 34), ACCENT, 22)

        if self.error:
            self.fonts.draw(surface, "Load failed", (32, 70), BAD, 18)
            self.fonts.draw(surface, self.error[:38], (32, 94), TEXT, 16)
            self.fonts.draw(surface, "Enter/Esc: Quit", (32, 128), MUTED, 16)
            return

        if self.summary is None:
            self.fonts.draw(surface, "Reading git history...", (32, 82), MUTED, 16)
            return

        self.fonts.draw(surface, "Repository loaded", (32, 64), GOOD, 18)
        self.fonts.draw(surface, f"Commits:  {self.summary.total_commits}", (32, 88), TEXT, 16)
        self.fonts.draw(surface, f"Chapters: {self.summary.chapter_count}", (32, 106), TEXT, 16)
        self.fonts.draw(surface, f"First: {self.summary.current_chapter_name[:24]}", (32, 124), TEXT, 16)
        self.fonts.draw(surface, "Enter/Esc: Quit", (32, 146), MUTED, 16)


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
        runner = GameRunner(
            repo_path=repo_path,
            seed=seed,
            lang=lang,
            content_pack_args=content_pack_args,
        )
        stack = ScreenStack([TitleScreen(pygame, fonts, runner)])
        frames = 0

        while not stack.is_empty:
            dt = clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    stack.apply(ScreenAction.quit())
                    break
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
            pygame.transform.scale(surface, WINDOW_SIZE, window)
            pygame.display.flip()

            frames += 1
            if smoke_frames is not None and frames >= smoke_frames:
                stack.apply(ScreenAction.quit())

        return 0
    finally:
        pygame.quit()
