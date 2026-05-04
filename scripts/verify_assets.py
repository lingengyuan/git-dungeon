#!/usr/bin/env python3
"""Verify the sprite manifest is consistent and all referenced files load.

Phase 0-5 (default mode):
  - Schema valid, source dirs exist, contact sheets readable
  - Non-null sprite paths exist, are PNG, openable by Pillow
  - null sprite entries are reported as PENDING (exit 0; not a failure)

Phase 6 (--strict):
  - Same checks, plus PENDING entries become errors

Errors print one line per offender to stderr and the script exits non-zero.
No silent fallback: anything broken must be visible.

Exit codes:
  0  all good (PENDING allowed unless --strict)
  1  schema error / broken file path / unreadable image
  2  --strict + at least one PENDING entry
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "assets/manifest_sprites.json"


def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)


def warn(msg: str) -> None:
    print(f"WARN:  {msg}", file=sys.stderr)


def info(msg: str) -> None:
    print(msg)


def load_manifest() -> dict:
    if not MANIFEST.exists():
        fail(f"manifest not found at {MANIFEST}")
        sys.exit(1)
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        fail(f"manifest is not valid JSON: {e}")
        sys.exit(1)


def validate_schema(m: dict) -> list[str]:
    errors: list[str] = []
    for key in ("version", "sources", "sprites"):
        if key not in m:
            errors.append(f"manifest missing required key: {key}")
    if "sources" in m and not isinstance(m["sources"], list):
        errors.append("sources must be a list")
    if "sprites" in m and not isinstance(m["sprites"], dict):
        errors.append("sprites must be an object")

    if "sprites" in m and isinstance(m["sprites"], dict):
        for sprite_id in m["sprites"]:
            if not sprite_id or not isinstance(sprite_id, str):
                errors.append(f"sprite id must be non-empty string, got: {sprite_id!r}")

    if "sources" in m and isinstance(m["sources"], list):
        seen_ids: set[str] = set()
        for src in m["sources"]:
            if not isinstance(src, dict):
                errors.append(f"source entry must be object, got: {type(src).__name__}")
                continue
            sid = src.get("id")
            if not sid:
                errors.append(f"source missing id: {src}")
                continue
            if sid in seen_ids:
                errors.append(f"duplicate source id: {sid}")
            seen_ids.add(sid)
            for required in ("root", "credit", "license"):
                if not src.get(required):
                    errors.append(f"source {sid} missing {required}")
    return errors


def check_sources(sources: list[dict]) -> list[str]:
    errors: list[str] = []
    for src in sources:
        sid = src.get("id", "<unknown>")
        root = ROOT / src.get("root", "")
        if not root.is_dir():
            errors.append(f"source {sid}: root not a directory: {root}")
            continue
        cs = src.get("contact_sheet")
        if cs:
            cs_path = ROOT / cs
            if not cs_path.is_file():
                errors.append(f"source {sid}: contact_sheet missing: {cs_path}")
                continue
            try:
                with Image.open(cs_path) as im:
                    im.verify()
            except (UnidentifiedImageError, OSError) as e:
                errors.append(f"source {sid}: contact_sheet unreadable: {cs_path} ({e})")
    return errors


def check_sprites(sprites: dict, sources: list[dict], strict: bool) -> tuple[list[str], list[str]]:
    """Return (errors, pendings)."""
    errors: list[str] = []
    pendings: list[str] = []
    source_roots = [str((ROOT / s["root"]).resolve()) for s in sources if s.get("root")]

    for sprite_id, value in sprites.items():
        if value is None:
            pendings.append(sprite_id)
            continue
        if not isinstance(value, str):
            errors.append(f"sprite {sprite_id}: value must be string or null, got {type(value).__name__}")
            continue

        sprite_path = (ROOT / value).resolve()
        if not sprite_path.is_file():
            errors.append(f"sprite {sprite_id}: file missing: {value}")
            continue

        if not any(str(sprite_path).startswith(r) for r in source_roots):
            errors.append(
                f"sprite {sprite_id}: path {value} is not under any declared source root "
                "(typo? unauthorized location?)"
            )
            continue

        try:
            with Image.open(sprite_path) as im:
                im.verify()
        except (UnidentifiedImageError, OSError) as e:
            errors.append(f"sprite {sprite_id}: image unreadable ({e}): {value}")

    return errors, pendings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat PENDING (null path) sprites as errors (Phase 6 CI gate)",
    )
    args = parser.parse_args()

    manifest = load_manifest()
    schema_errors = validate_schema(manifest)
    if schema_errors:
        for e in schema_errors:
            fail(e)
        return 1

    info(f"manifest: {MANIFEST.relative_to(ROOT)}")
    info(f"sources: {len(manifest['sources'])}, sprites declared: {len(manifest['sprites'])}")

    src_errors = check_sources(manifest["sources"])
    sprite_errors, pendings = check_sprites(manifest["sprites"], manifest["sources"], args.strict)
    errors = src_errors + sprite_errors

    if errors:
        for e in errors:
            fail(e)

    if pendings:
        info("")
        info(f"{len(pendings)} sprite(s) PENDING manual mapping:")
        for sid in pendings:
            info(f"  - {sid}")
        info("  Open assets/contact_sheets/kenney_tiny_dungeon.png to fill them.")

    if errors:
        return 1
    if args.strict and pendings:
        fail(f"--strict: {len(pendings)} sprite(s) still PENDING — see list above")
        return 2

    info("")
    info(f"OK: {len(manifest['sprites']) - len(pendings)}/{len(manifest['sprites'])} sprites mapped, all valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
