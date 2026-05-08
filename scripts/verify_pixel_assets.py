#!/usr/bin/env python3
"""Verify generated pixel asset cards, processed sprites, contact sheet, and manifest links."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "assets/manifest_sprites.json"


def _project_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _readable_image_ok(path: Path) -> list[str]:
    if not path.is_file():
        return [f"missing image: {path.relative_to(ROOT)}"]
    try:
        with Image.open(path) as image:
            image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        return [f"unreadable image {path.relative_to(ROOT)}: {exc}"]
    return []


def _sprite_image_ok(path: Path, expected_size: tuple[int, int]) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"missing image: {path.relative_to(ROOT)}"]
    try:
        with Image.open(path) as image:
            image.load()
            if image.size != expected_size:
                errors.append(f"{path.relative_to(ROOT)} size {image.size}, expected {expected_size}")
            if image.mode != "RGBA":
                errors.append(f"{path.relative_to(ROOT)} mode {image.mode}, expected RGBA")
    except (UnidentifiedImageError, OSError) as exc:
        errors.append(f"unreadable image {path.relative_to(ROOT)}: {exc}")
    return errors


def verify(asset_cards: Path) -> list[str]:
    config = _load_json(asset_cards)
    errors: list[str] = []
    prompt_file = _project_path(config.get("prompt_file"))
    raw_file = _project_path(config.get("raw_file"))
    contact_sheet = _project_path(config.get("contact_sheet"))
    if prompt_file is None or not prompt_file.is_file():
        errors.append(f"missing prompt_file: {config.get('prompt_file')}")
    if raw_file is None or not raw_file.is_file():
        errors.append(f"missing raw_file: {config.get('raw_file')}")
    if contact_sheet is None or not contact_sheet.is_file():
        errors.append(f"missing contact_sheet: {config.get('contact_sheet')}")
    else:
        errors.extend(_readable_image_ok(contact_sheet))

    manifest = _load_json(MANIFEST)
    sprites = manifest.get("sprites", {})
    source_roots = {source.get("root") for source in manifest.get("sources", [])}
    phase_root = f"assets/generated/processed/{config['phase']}"
    if phase_root not in source_roots:
        errors.append(f"manifest missing generated source root: {phase_root}")

    for asset in config.get("assets", []):
        asset_id = str(asset.get("id", ""))
        if not asset_id:
            errors.append("asset entry missing id")
            continue
        expected_size = tuple(int(value) for value in asset.get("size", []))
        if len(expected_size) != 2:
            errors.append(f"{asset_id}: invalid size {asset.get('size')}")
            continue
        processed = ROOT / phase_root / f"{asset_id}.png"
        errors.extend(_sprite_image_ok(processed, (expected_size[0], expected_size[1])))
        manifest_path = sprites.get(asset_id)
        expected_manifest_path = f"{phase_root}/{asset_id}.png"
        if manifest_path != expected_manifest_path:
            errors.append(
                f"{asset_id}: manifest path {manifest_path!r}, expected {expected_manifest_path!r}"
            )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--asset-cards",
        type=Path,
        default=ROOT / "assets/generated/phase14b/asset_plan.json",
    )
    args = parser.parse_args(argv)
    try:
        errors = verify(args.asset_cards)
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: generated pixel assets verified from {args.asset_cards}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
