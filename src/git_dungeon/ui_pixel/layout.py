"""Pixel UI layout helpers."""

from __future__ import annotations


def window_to_logical(
    pos: tuple[int, int],
    window_size: tuple[int, int],
    logical_size: tuple[int, int],
) -> tuple[int, int] | None:
    """Map a window pixel position into the fixed logical canvas.

    The scaled canvas is letterboxed when the window aspect ratio differs from
    the logical aspect ratio. Positions in the letterbox area return None.
    """
    win_w, win_h = window_size
    logical_w, logical_h = logical_size
    if win_w <= 0 or win_h <= 0 or logical_w <= 0 or logical_h <= 0:
        raise ValueError("window and logical sizes must be positive")

    scale = _pixel_scale(window_size, logical_size)
    scaled_w = int(logical_w * scale)
    scaled_h = int(logical_h * scale)
    offset_x = (win_w - scaled_w) // 2
    offset_y = (win_h - scaled_h) // 2
    x, y = pos

    if x < offset_x or y < offset_y or x >= offset_x + scaled_w or y >= offset_y + scaled_h:
        return None
    logical_x = int((x - offset_x) / scale)
    logical_y = int((y - offset_y) / scale)
    return (
        max(0, min(logical_w - 1, logical_x)),
        max(0, min(logical_h - 1, logical_y)),
    )


def scale_rect(
    logical_size: tuple[int, int],
    window_size: tuple[int, int],
) -> tuple[int, int, int, int]:
    """Return the destination rect for drawing logical canvas into a window."""
    logical_w, logical_h = logical_size
    win_w, win_h = window_size
    scale = _pixel_scale(window_size, logical_size)
    scaled_w = int(logical_w * scale)
    scaled_h = int(logical_h * scale)
    return ((win_w - scaled_w) // 2, (win_h - scaled_h) // 2, scaled_w, scaled_h)


def _pixel_scale(
    window_size: tuple[int, int],
    logical_size: tuple[int, int],
) -> float:
    win_w, win_h = window_size
    logical_w, logical_h = logical_size
    integer_scale = min(win_w // logical_w, win_h // logical_h)
    if integer_scale >= 1:
        return float(integer_scale)
    return min(win_w / logical_w, win_h / logical_h)
