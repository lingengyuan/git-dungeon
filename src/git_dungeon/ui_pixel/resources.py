"""Asset root resolution for pixel UI resources."""

from __future__ import annotations

import os
import sys
from importlib import resources
from pathlib import Path


def candidate_asset_roots() -> list[Path]:
    """Return asset roots in the required lookup order."""
    candidates: list[Path] = []

    env_root = os.getenv("GIT_DUNGEON_ASSET_DIR")
    if env_root:
        candidates.append(Path(env_root))

    try:
        package_root = resources.files("git_dungeon") / "assets"
        candidates.append(Path(str(package_root)))
    except Exception:
        pass

    candidates.append(Path(sys.prefix) / "git_dungeon" / "assets")
    candidates.append(Path(__file__).resolve().parents[3] / "assets")

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(str(meipass)) / "assets")

    deduped: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.expanduser()
        if resolved not in seen:
            deduped.append(resolved)
            seen.add(resolved)
    return deduped


def resolve_asset_root() -> Path:
    """Resolve the first root containing the sprite manifest."""
    env_root = os.getenv("GIT_DUNGEON_ASSET_DIR")
    if env_root:
        root = Path(env_root).expanduser()
        if (root / "manifest_sprites.json").exists():
            return root
        raise FileNotFoundError(f"Pixel assets not found in GIT_DUNGEON_ASSET_DIR: {root}")

    checked = candidate_asset_roots()
    for root in checked:
        if (root / "manifest_sprites.json").exists():
            return root
    joined = ", ".join(str(path) for path in checked)
    raise FileNotFoundError(f"Pixel assets not found. Checked: {joined}")


def asset_path(*parts: str) -> Path:
    return resolve_asset_root().joinpath(*parts)
