"""Pygame application shell for the pixel UI."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from git_dungeon.ui_pixel.assets import SpriteCatalog
from git_dungeon.ui_pixel.audio import AudioManager
from git_dungeon.ui_pixel.game_runner import GameRunner
from git_dungeon.ui_pixel.layout import scale_rect, window_to_logical
from git_dungeon.ui_pixel.screens.base import Screen, ScreenAction
from git_dungeon.ui_pixel.screens.error import ErrorScreen
from git_dungeon.ui_pixel.screens.title import LoadingScreen, TitleScreen
from git_dungeon.ui_pixel.resources import resolve_asset_root
from git_dungeon.ui_pixel.settings import PixelSettingsStore

LOGICAL_SIZE = (320, 180)
WINDOW_SIZE = (960, 540)
FPS = 60
CJK_OVERLAY_FONT_SCALE = 0.65

BG = (17, 16, 24)
SURFACE = (33, 31, 45)
TEXT = (238, 232, 213)
MUTED = (148, 139, 130)
ACCENT = (235, 177, 88)
GOOD = (99, 199, 122)
BAD = (219, 87, 87)


def display_flags_for_window_mode(pygame_module, window_mode: str) -> int:
    return pygame_module.FULLSCREEN if window_mode == "fullscreen" else 0


class PixelWindow:
    def __init__(self, pygame_module: Any, window_mode: str) -> None:
        self._pygame = pygame_module
        self._window: Any | None = None
        self.surface: Any = None
        self.window_mode = ""
        self.set_mode(window_mode)

    def set_mode(self, window_mode: str) -> None:
        if self._window is not None:
            self._window.destroy()
            self._window = None

        window_cls = getattr(self._pygame, "Window", None)
        if window_cls is not None:
            try:
                self._window = window_cls(
                    title="Git Dungeon Pixel",
                    size=WINDOW_SIZE,
                    fullscreen=window_mode == "fullscreen",
                    allow_high_dpi=True,
                )
                self.surface = self._window.get_surface()
                self.window_mode = window_mode
                return
            except (TypeError, self._pygame.error):
                self._window = None

        self.surface = self._pygame.display.set_mode(
            WINDOW_SIZE,
            display_flags_for_window_mode(self._pygame, window_mode),
        )
        self._pygame.display.set_caption("Git Dungeon Pixel")
        self.window_mode = window_mode

    def event_size_for_pos(self, pos: tuple[int, int]) -> tuple[int, int]:
        if self._window is None:
            return self.surface.get_size()
        window_size = self._window.size
        if pos[0] >= window_size[0] or pos[1] >= window_size[1]:
            return self.surface.get_size()
        return window_size

    def flip(self) -> None:
        if self._window is not None:
            self._window.flip()
            return
        self._pygame.display.flip()


@dataclass(frozen=True)
class PixelRunConfig:
    repo_path: str
    seed: int | None = None
    lang: str | None = None
    content_pack_args: list[str] | None = None
    smoke_frames: int | None = None


@dataclass(frozen=True)
class TextDrawCommand:
    text: str
    pos: tuple[int, int]
    color: tuple[int, int, int]
    size: int
    family: str


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
        if action.kind == "reset" and action.screen is not None:
            while self._screens:
                self._screens.pop().exit()
            self._screens.append(action.screen)
            action.screen.enter()
            return
        if action.kind == "push" and action.screen is not None:
            self._screens.append(action.screen)
            action.screen.enter()


class PixelFont:
    def __init__(self, pygame_module, lang: str = "en", text_size: str = "normal") -> None:
        self._pygame = pygame_module
        self.lang = lang
        self.text_size = text_size
        try:
            root = resolve_asset_root()
        except FileNotFoundError:
            root = Path()
        self._latin_font = root / "fonts" / "vt323" / "VT323-Regular.ttf"
        self._bundled_cjk_font = (
            root
            / "fonts"
            / "ark_pixel"
            / "ark-pixel-12px-proportional-zh_cn.ttf"
        )
        self._cjk_font = self._resolve_cjk_font()
        self._cache: dict[tuple[str, str, int], object] = {}
        self._overlay_commands: list[TextDrawCommand] | None = None

    def get(self, size: int, text: str = "", family: str | None = None):
        family = family or self._font_family(text)
        render_size = self._render_size(size, family)
        return self._font(family, render_size)

    def _font(self, family: str, render_size: int) -> Any:
        key = (family, self.text_size, render_size)
        if key not in self._cache:
            path = self._font_path(family)
            self._cache[key] = self._pygame.font.Font(
                str(path) if path.exists() else None,
                render_size,
            )
        return self._cache[key]

    def _font_path(self, family: str) -> Path:
        if family == "cjk" and self._cjk_font.exists():
            return self._cjk_font
        return self._latin_font

    def _font_family(self, text: str) -> str:
        if self.lang == "zh_CN" and any(ord(char) > 127 for char in text):
            return "cjk"
        return "latin"

    def _resolve_cjk_font(self) -> Path:
        candidates: list[Path] = []
        for family in ("hiragino sans gb", "arialunicode"):
            matched = self._pygame.font.match_font(family)
            if matched:
                candidates.append(Path(matched))
        candidates.extend(
            [
                Path("/System/Library/Fonts/Hiragino Sans GB.ttc"),
                Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
                Path("/Library/Fonts/Arial Unicode.ttf"),
                self._bundled_cjk_font,
            ]
        )
        for path in candidates:
            if path.exists():
                return path
        return self._bundled_cjk_font

    def set_lang(self, lang: str) -> None:
        self.lang = lang

    def set_text_size(self, text_size: str) -> None:
        if text_size == self.text_size:
            return
        self.text_size = text_size
        self._cache.clear()

    def _render_size(self, size: int, family: str | None = None) -> int:
        size = size + 1 if self.text_size == "large" else size
        if family != "cjk":
            return size
        return max(8, size - 2)

    def measure(self, text: str, size: int = 16) -> int:
        family = self._font_family(text)
        return self.get(size, text, family).size(text)[0]

    def fit(self, text: str, max_width: int, size: int = 16) -> str:
        family = self._font_family(text)
        if self.get(size, text, family).size(text)[0] <= max_width:
            return text
        suffix = "..."
        available = max(1, max_width - self.get(size, suffix, family).size(suffix)[0])
        result = ""
        for char in text:
            if self.get(size, result + char, family).size(result + char)[0] > available:
                break
            result += char
        return (result or text[:1]) + suffix

    def draw(self, surface, text: str, pos: tuple[int, int], color=TEXT, size: int = 16) -> None:
        family = self._font_family(text)
        if family == "cjk" and self._overlay_commands is not None:
            self._overlay_commands.append(TextDrawCommand(text, pos, color, size, family))
            return
        img = self.get(size, text, family).render(text, self._should_antialias(family), color)
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

    def _should_antialias(self, family: str | None = None) -> bool:
        return family == "cjk" and self._cjk_font != self._bundled_cjk_font

    def begin_overlay(self) -> None:
        self._overlay_commands = []

    def flush_overlay(
        self,
        surface,
        dest_rect: tuple[int, int, int, int],
        logical_size: tuple[int, int],
    ) -> None:
        commands = self._overlay_commands
        self._overlay_commands = None
        if not commands:
            return
        scale_x = dest_rect[2] / logical_size[0]
        scale_y = dest_rect[3] / logical_size[1]
        text_scale = min(scale_x, scale_y)
        for command in commands:
            family_scale = CJK_OVERLAY_FONT_SCALE if command.family == "cjk" else 1.0
            render_size = max(
                1,
                round(self._render_size(command.size, command.family) * text_scale * family_scale),
            )
            font = self._font(command.family, render_size)
            img = font.render(command.text, self._should_antialias(command.family), command.color)
            x = dest_rect[0] + round(command.pos[0] * scale_x)
            y = dest_rect[1] + round(command.pos[1] * scale_y)
            surface.blit(img, (x, y))


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
        window = PixelWindow(pygame, settings.window_mode)

        def apply_display_mode(next_settings) -> None:
            if next_settings.window_mode == window.window_mode:
                return
            window.set_mode(next_settings.window_mode)

        surface = pygame.Surface(LOGICAL_SIZE)
        clock = pygame.time.Clock()
        fonts = PixelFont(pygame, settings.lang, settings.text_size)
        try:
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
                    apply_display_mode,
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
                    apply_display_mode,
                )
        except Exception as exc:
            initial_screen = ErrorScreen(pygame, fonts, "PIXEL STARTUP ERROR", str(exc))
        stack = ScreenStack([initial_screen])
        frames = 0
        scaled_surface: Any | None = None
        scaled_size: tuple[int, int] | None = None

        while not stack.is_empty:
            dt = clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    stack.apply(ScreenAction.quit())
                    break
                if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                    logical_pos = window_to_logical(
                        event.pos,
                        window.event_size_for_pos(event.pos),
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

            fonts.begin_overlay()
            stack.top.draw(surface)
            window_surface = window.surface
            window_surface.fill(BG)
            dest_rect = scale_rect(LOGICAL_SIZE, window_surface.get_size())
            next_scaled_size = (dest_rect[2], dest_rect[3])
            if scaled_surface is None or scaled_size != next_scaled_size:
                scaled_surface = pygame.Surface(next_scaled_size)
                scaled_size = next_scaled_size
            pygame.transform.scale(
                surface,
                next_scaled_size,
                scaled_surface,
            )
            window_surface.blit(scaled_surface, (dest_rect[0], dest_rect[1]))
            fonts.flush_overlay(window_surface, dest_rect, LOGICAL_SIZE)
            window.flip()

            frames += 1
            if smoke_frames is not None and frames >= smoke_frames:
                stack.apply(ScreenAction.quit())

        return 0
    finally:
        pygame.quit()
