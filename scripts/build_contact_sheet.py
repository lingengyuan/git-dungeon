#!/usr/bin/env python3
"""Build a labeled contact sheet for a sprite directory.

Used by Phase 0 to produce `assets/contact_sheets/<pack>.png` for human
inspection — pinning numeric `tile_NNNN.png` filenames to game IDs in
`assets/manifest_sprites.json`. Source plan §7.1 forbids guessing
filenames; the contact sheet is the verification surface.

Usage:
    python scripts/build_contact_sheet.py \
        --src assets/sprites/kenney_tiny_dungeon/Tiles \
        --out assets/contact_sheets/kenney_tiny_dungeon.png \
        --columns 12 --scale 4
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def load_font(size: int) -> ImageFont.ImageFont:
    """VT323 if shipped with the project, else PIL default."""
    candidates = [
        Path(__file__).resolve().parent.parent / "assets/fonts/vt323/VT323-Regular.ttf",
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def build_sheet(src: Path, out: Path, columns: int, scale: int, label_h: int) -> None:
    files = sorted(p for p in src.iterdir() if p.suffix.lower() == ".png")
    if not files:
        sys.exit(f"error: no PNG files under {src}")

    tile_w, tile_h = Image.open(files[0]).size
    cell_w = tile_w * scale
    cell_h = tile_h * scale + label_h
    rows = (len(files) + columns - 1) // columns

    margin = 4
    sheet_w = columns * cell_w + (columns + 1) * margin
    sheet_h = rows * cell_h + (rows + 1) * margin

    sheet = Image.new("RGBA", (sheet_w, sheet_h), (32, 32, 40, 255))
    draw = ImageDraw.Draw(sheet)
    font = load_font(label_h - 2)

    for idx, fp in enumerate(files):
        col, row = idx % columns, idx // columns
        x = margin + col * (cell_w + margin)
        y = margin + row * (cell_h + margin)

        tile = Image.open(fp).convert("RGBA")
        if tile.size != (tile_w, tile_h):
            sys.exit(
                f"error: {fp.name} is {tile.size}, expected {(tile_w, tile_h)} "
                "(contact sheet assumes uniform tile size)"
            )
        scaled = tile.resize((cell_w, tile_h * scale), Image.NEAREST)
        sheet.paste(scaled, (x, y), scaled)

        label = fp.stem
        bbox = draw.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(
            (x + (cell_w - tw) // 2, y + tile_h * scale + 1),
            label,
            font=font,
            fill=(220, 220, 220, 255),
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, "PNG", optimize=True)
    print(f"wrote {out} ({sheet.size[0]}×{sheet.size[1]}, {len(files)} tiles)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", required=True, type=Path, help="sprite directory")
    parser.add_argument("--out", required=True, type=Path, help="output PNG")
    parser.add_argument("--columns", type=int, default=12)
    parser.add_argument("--scale", type=int, default=4, help="nearest-neighbor upscale")
    parser.add_argument("--label-h", type=int, default=14, help="label strip height (px)")
    args = parser.parse_args()

    if not args.src.is_dir():
        sys.exit(f"error: {args.src} is not a directory")

    build_sheet(args.src, args.out, args.columns, args.scale, args.label_h)
    return 0


if __name__ == "__main__":
    sys.exit(main())
