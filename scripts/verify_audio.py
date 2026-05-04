#!/usr/bin/env python3
"""Verify all required audio assets are present, valid, and credited.

Checks:
  1. 4 BGM slots exist as OGG files (`OggS` magic) and look like vorbis streams.
  2. Each BGM filename is referenced in `assets/CREDITS.md`.
  3. SFX directories (Kenney RPG / UI Audio) exist and contain at least one OGG.
  4. License.txt or equivalent exists in each Kenney pack root.

No silent fallback: any missing or unreadable file is a hard error.

Exit codes:
  0  all checks passed
  1  any required file missing / unreadable / uncredited
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BGM_DIR = ROOT / "assets/audio/bgm"
SFX_DIR = ROOT / "assets/audio/sfx"
CREDITS = ROOT / "assets/CREDITS.md"

REQUIRED_BGM = ["title.ogg", "chapter.ogg", "boss.ogg", "gameover.ogg"]
REQUIRED_SFX_PACKS = [
    ("kenney_rpg_audio", "Kenney RPG Audio"),
    ("kenney_ui_audio", "Kenney UI Audio"),
]


def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)


def info(msg: str) -> None:
    print(msg)


def is_ogg(path: Path) -> bool:
    """Check OGG magic bytes (`OggS` at offset 0)."""
    try:
        with path.open("rb") as f:
            return f.read(4) == b"OggS"
    except OSError:
        return False


def first_packet_codec(path: Path) -> str | None:
    """Read the first Ogg page payload and return a best-guess codec name.

    Vorbis identification headers start with byte 0x01 then `vorbis`.
    Opus identification headers start with `OpusHead`.
    """
    try:
        data = path.read_bytes()[:128]
    except OSError:
        return None
    if b"\x01vorbis" in data:
        return "vorbis"
    if b"OpusHead" in data:
        return "opus"
    return None


def check_bgm() -> list[str]:
    errors: list[str] = []
    if not BGM_DIR.is_dir():
        errors.append(f"BGM dir missing: {BGM_DIR}")
        return errors

    credits_text = CREDITS.read_text(encoding="utf-8") if CREDITS.exists() else ""

    for name in REQUIRED_BGM:
        path = BGM_DIR / name
        if not path.is_file():
            errors.append(f"BGM missing: {name}")
            continue
        if not is_ogg(path):
            errors.append(f"BGM not OGG (bad magic): {name}")
            continue
        codec = first_packet_codec(path)
        if codec != "vorbis":
            errors.append(f"BGM not vorbis (got {codec!r}): {name}")
        if name not in credits_text:
            errors.append(f"BGM not credited in CREDITS.md: {name}")

    return errors


def check_sfx() -> list[str]:
    errors: list[str] = []
    if not SFX_DIR.is_dir():
        errors.append(f"SFX dir missing: {SFX_DIR}")
        return errors

    for pack_dir, pack_label in REQUIRED_SFX_PACKS:
        path = SFX_DIR / pack_dir
        if not path.is_dir():
            errors.append(f"SFX pack missing: {pack_label} ({path})")
            continue
        oggs = list(path.rglob("*.ogg"))
        if not oggs:
            errors.append(f"SFX pack {pack_label}: no OGG files under {path}")
            continue
        # license file (Kenney ships License.txt at pack root)
        if not any((path / name).is_file() for name in ("License.txt", "license.txt", "LICENSE")):
            errors.append(f"SFX pack {pack_label}: no License.txt at {path}")

    return errors


def main() -> int:
    if not CREDITS.is_file():
        fail(f"CREDITS.md missing at {CREDITS}")
        return 1

    errors = check_bgm() + check_sfx()
    if errors:
        for e in errors:
            fail(e)
        return 1

    info(f"BGM: {len(REQUIRED_BGM)}/4 slots filled, all vorbis OGG, all credited.")
    info(f"SFX: {len(REQUIRED_SFX_PACKS)} packs present with License.txt.")
    info("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
