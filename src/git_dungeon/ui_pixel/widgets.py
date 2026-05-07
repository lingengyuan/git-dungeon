"""Small pixel UI widgets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

BG = (17, 16, 24)
TEXT = (238, 232, 213)
MUTED = (148, 139, 130)
SURFACE = (33, 31, 45)
SURFACE_2 = (45, 42, 60)
ACCENT = (235, 177, 88)
DISABLED = (83, 78, 94)
GOOD = (99, 199, 122)
BAD = (219, 87, 87)


@dataclass
class Button:
    rect: tuple[int, int, int, int]
    label: str
    enabled: bool = True
    tooltip: str = ""

    def contains(self, pos: tuple[int, int] | None) -> bool:
        if pos is None:
            return False
        x, y = pos
        rx, ry, rw, rh = self.rect
        return rx <= x < rx + rw and ry <= y < ry + rh

    def draw(self, pygame: Any, surface: Any, fonts: Any, hover: bool = False) -> None:
        color = SURFACE_2 if self.enabled else DISABLED
        border = ACCENT if self.enabled and hover else MUTED
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, border, self.rect, 1)
        text_color = TEXT if self.enabled else MUTED
        text_size = max(9, min(15, self.rect[3] - 4))
        label = (
            fonts.fit(self.label, self.rect[2] - 8, text_size)
            if hasattr(fonts, "fit")
            else self.label
        )
        label_width = fonts.measure(label, text_size)
        x = self.rect[0] + max(4, (self.rect[2] - label_width) // 2)
        y = self.rect[1] + max(2, (self.rect[3] - text_size) // 2)
        fonts.draw(surface, label, (x, y), text_color, text_size)


@dataclass(frozen=True)
class PixelUIRects:
    """Shared logical-space regions for running screens."""

    main_panel: tuple[int, int, int, int] = (14, 12, 292, 156)
    action_bar: tuple[int, int, int, int] = (14, 156, 292, 18)


def draw_panel(
    pygame: Any,
    surface: Any,
    rect: tuple[int, int, int, int],
    *,
    border: tuple[int, int, int] = ACCENT,
) -> None:
    pygame.draw.rect(surface, SURFACE, rect)
    pygame.draw.rect(surface, border, rect, 1)


def draw_dialog(
    pygame: Any,
    surface: Any,
    fonts: Any,
    rect: tuple[int, int, int, int],
    title: str,
    body: str = "",
    *,
    border: tuple[int, int, int] = ACCENT,
) -> None:
    draw_panel(pygame, surface, rect, border=border)
    fonts.draw_fit(surface, title, (rect[0] + 10, rect[1] + 10), rect[2] - 20, border, 18)
    if body:
        fonts.draw_fit(surface, body, (rect[0] + 10, rect[1] + 32), rect[2] - 20, MUTED, 13)


def draw_action_bar(
    pygame: Any,
    surface: Any,
    fonts: Any,
    message: str,
    *,
    rect: tuple[int, int, int, int] = PixelUIRects().action_bar,
    right_text: str = "",
    reserve_right: int = 0,
    alert: bool = False,
) -> None:
    pygame.draw.rect(surface, (27, 25, 35), rect)
    pygame.draw.rect(surface, BAD if alert else SURFACE_2, rect, 1)
    color = BAD if alert else TEXT
    right_width = max(reserve_right, 82 if right_text else 0)
    fonts.draw_fit(
        surface, message, (rect[0] + 4, rect[1] + 4), rect[2] - 10 - right_width, color, 12
    )
    if right_text:
        fonts.draw_fit(
            surface,
            right_text,
            (rect[0] + rect[2] - right_width + 4, rect[1] + 4),
            right_width - 8,
            MUTED,
            11,
        )


def draw_tooltip(
    pygame: Any,
    surface: Any,
    fonts: Any,
    text: str,
    anchor: tuple[int, int],
    *,
    width: int = 112,
) -> None:
    rect = (anchor[0], anchor[1], width, 18)
    pygame.draw.rect(surface, (27, 25, 35), rect)
    pygame.draw.rect(surface, ACCENT, rect, 1)
    fonts.draw_fit(surface, text, (rect[0] + 5, rect[1] + 4), rect[2] - 10, TEXT, 11)


def draw_toast(
    pygame: Any,
    surface: Any,
    fonts: Any,
    message: str,
    *,
    rect: tuple[int, int, int, int] = (42, 18, 236, 20),
    alert: bool = False,
) -> None:
    pygame.draw.rect(surface, (27, 25, 35), rect)
    pygame.draw.rect(surface, BAD if alert else ACCENT, rect, 1)
    fonts.draw_fit(
        surface, message, (rect[0] + 6, rect[1] + 4), rect[2] - 12, BAD if alert else TEXT, 12
    )


def draw_choice_card(
    pygame: Any,
    surface: Any,
    fonts: Any,
    rect: tuple[int, int, int, int],
    title: str,
    detail: str,
    *,
    disabled: bool = False,
    hover: bool = False,
) -> None:
    fill = (31, 29, 40) if not disabled else (25, 24, 32)
    border = ACCENT if hover and not disabled else MUTED if not disabled else DISABLED
    pygame.draw.rect(surface, fill, rect)
    pygame.draw.rect(surface, border, rect, 1)
    fonts.draw_fit(
        surface,
        title,
        (rect[0] + 5, rect[1] + 4),
        rect[2] - 10,
        TEXT if not disabled else MUTED,
        10,
    )
    fonts.draw_fit(surface, detail, (rect[0] + 8, rect[1] + 14), rect[2] - 12, MUTED, 8)


def draw_item_card(
    pygame: Any,
    surface: Any,
    fonts: Any,
    rect: tuple[int, int, int, int],
    title: str,
    detail: str,
    *,
    disabled: bool = False,
    hover: bool = False,
) -> None:
    draw_choice_card(
        pygame,
        surface,
        fonts,
        rect,
        title,
        detail,
        disabled=disabled,
        hover=hover,
    )


def draw_stat_bar(
    pygame: Any,
    surface: Any,
    rect: tuple[int, int, int, int],
    current: int,
    maximum: int,
    color: tuple[int, int, int],
) -> None:
    pygame.draw.rect(surface, DISABLED, rect)
    if maximum > 0:
        fill_w = int(rect[2] * max(0, min(current, maximum)) / maximum)
        if fill_w > 0:
            pygame.draw.rect(surface, color, (rect[0], rect[1], fill_w, rect[3]))
    pygame.draw.rect(surface, MUTED, rect, 1)


def wrap_text(text: str, max_chars: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word[:max_chars]
    if current:
        lines.append(current)
    return lines


def effect_text(parts: list[str]) -> str:
    visible = [part for part in parts if part and not part.endswith(":0")]
    return ", ".join(visible) if visible else "No stat change"
