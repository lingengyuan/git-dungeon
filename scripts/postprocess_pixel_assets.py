#!/usr/bin/env python3
"""Postprocess generated pixel-art sprite sheets into runtime-sized PNG assets."""

from __future__ import annotations

import argparse
from collections import deque
import json
import sys
from pathlib import Path
from typing import Any, cast

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


def _project_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def _is_key(pixel: tuple[int, int, int, int]) -> bool:
    r, g, b, _a = pixel
    green_key = g >= 80 and g >= r + 20 and g >= b + 20
    grid_key = r >= 235 and g >= 235 and b >= 235
    dark_grid_key = r <= 28 and g <= 28 and b <= 28
    return green_key or _is_magenta_key(pixel) or grid_key or dark_grid_key


def _is_magenta_key(pixel: tuple[int, int, int, int]) -> bool:
    r, g, b, _a = pixel
    bright_magenta = r >= 70 and b >= 70 and r >= g + 20 and b >= g + 20
    dark_magenta = r >= 45 and b >= 45 and g <= 35 and r >= g + 30 and b >= g + 30
    return bright_magenta or dark_magenta


def _pixel_at(pixels: Any, x: int, y: int) -> tuple[int, int, int, int]:
    return cast(tuple[int, int, int, int], pixels[x, y])


def _background_mask(image: Image.Image) -> list[list[bool]]:
    pixels = image.load()
    seen = [[False for _x in range(image.width)] for _y in range(image.height)]
    queue: deque[tuple[int, int]] = deque()

    for x in range(image.width):
        for y in (0, image.height - 1):
            if not seen[y][x] and _is_key(_pixel_at(pixels, x, y)):
                seen[y][x] = True
                queue.append((x, y))
    for y in range(image.height):
        for x in (0, image.width - 1):
            if not seen[y][x] and _is_key(_pixel_at(pixels, x, y)):
                seen[y][x] = True
                queue.append((x, y))

    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if nx < 0 or ny < 0 or nx >= image.width or ny >= image.height:
                continue
            if seen[ny][nx] or not _is_key(_pixel_at(pixels, nx, ny)):
                continue
            seen[ny][nx] = True
            queue.append((nx, ny))
    return seen


def _trim_bbox(image: Image.Image, background: list[list[bool]]) -> tuple[int, int, int, int]:
    pixels = image.load()
    min_x, min_y = image.width, image.height
    max_x, max_y = -1, -1
    for y in range(image.height):
        for x in range(image.width):
            if background[y][x]:
                continue
            if pixels[x, y][3] == 0:
                continue
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
    if max_x < min_x or max_y < min_y:
        raise ValueError("cell has no visible non-key pixels")
    return (min_x, min_y, max_x + 1, max_y + 1)


def _remove_background(
    image: Image.Image,
    background: list[list[bool]],
    bbox: tuple[int, int, int, int],
) -> Image.Image:
    left, upper, right, lower = bbox
    rgba = image.convert("RGBA")
    cropped = rgba.crop(bbox)
    pixels = cropped.load()
    source_pixels = rgba.load()
    for y in range(upper, lower):
        for x in range(left, right):
            if background[y][x] or _is_magenta_key(_pixel_at(source_pixels, x, y)):
                pixels[x - left, y - upper] = (0, 0, 0, 0)
    return cropped


def _center_on_square(image: Image.Image, padding: int = 2) -> Image.Image:
    background = _background_mask(image)
    bbox = _trim_bbox(image, background)
    cropped = _remove_background(image, background, bbox)
    side = max(cropped.width, cropped.height) + padding * 2
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.alpha_composite(cropped, ((side - cropped.width) // 2, (side - cropped.height) // 2))
    return square


def postprocess(config_path: Path, out_dir: Path | None = None) -> list[Path]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    source = _project_path(str(config["raw_file"]))
    if not source.is_file():
        raise FileNotFoundError(f"raw source missing: {source}")
    sheet = Image.open(source).convert("RGBA")
    columns = int(config["sheet"]["columns"])
    rows = int(config["sheet"]["rows"])
    cell_w = sheet.width / columns
    cell_h = sheet.height / rows
    output_dir = out_dir or ROOT / "assets/generated/processed" / str(config["phase"])
    output_dir.mkdir(parents=True, exist_ok=True)

    outputs: list[Path] = []
    for asset in config["assets"]:
        asset_id = str(asset["id"])
        col, row = [int(value) for value in asset["cell"]]
        width, height = [int(value) for value in asset["size"]]
        left = round(col * cell_w)
        upper = round(row * cell_h)
        right = round((col + 1) * cell_w)
        lower = round((row + 1) * cell_h)
        trim_margin = max(2, round(min(cell_w, cell_h) * 0.05))
        left += trim_margin
        upper += trim_margin
        right -= trim_margin
        lower -= trim_margin
        cell = sheet.crop((left, upper, right, lower))
        sprite = _center_on_square(cell).resize((width, height), Image.Resampling.NEAREST)
        out_path = output_dir / f"{asset_id}.png"
        sprite.save(out_path, "PNG", optimize=True)
        outputs.append(out_path)
    return outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args(argv)
    try:
        outputs = postprocess(args.config, args.out_dir)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for path in outputs:
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
