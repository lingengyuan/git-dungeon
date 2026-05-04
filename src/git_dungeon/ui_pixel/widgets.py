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
        label_width = fonts.measure(self.label, 15)
        x = self.rect[0] + max(4, (self.rect[2] - label_width) // 2)
        y = self.rect[1] + max(2, (self.rect[3] - 15) // 2)
        fonts.draw(surface, self.label, (x, y), text_color, 15)


def draw_panel(
    pygame: Any,
    surface: Any,
    rect: tuple[int, int, int, int],
    *,
    border: tuple[int, int, int] = ACCENT,
) -> None:
    pygame.draw.rect(surface, SURFACE, rect)
    pygame.draw.rect(surface, border, rect, 1)


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
