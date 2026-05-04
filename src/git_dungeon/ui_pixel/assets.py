"""Sprite manifest loading for the pixel UI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SpriteCatalog:
    """Loads sprite IDs from assets/manifest_sprites.json."""

    def __init__(self, pygame_module: Any, root: Path | None = None) -> None:
        self._pygame = pygame_module
        self._root = root or Path(__file__).resolve().parents[3]
        self._sprites: dict[str, Any] = {}

    def load(self) -> None:
        manifest_path = self._root / "assets" / "manifest_sprites.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Sprite manifest not found: {manifest_path}")
        with manifest_path.open("r", encoding="utf-8") as handle:
            manifest = json.load(handle)
        sprites = manifest.get("sprites", {})
        if not isinstance(sprites, dict):
            raise ValueError("Sprite manifest field 'sprites' must be an object")

        loaded: dict[str, Any] = {}
        for sprite_id, rel_path in sprites.items():
            if rel_path is None:
                raise ValueError(f"Sprite is not mapped: {sprite_id}")
            path = self._root / str(rel_path)
            if not path.exists():
                raise FileNotFoundError(f"Sprite file not found for {sprite_id}: {path}")
            loaded[str(sprite_id)] = self._pygame.image.load(str(path)).convert_alpha()
        self._sprites = loaded

    def get(self, sprite_id: str) -> Any:
        if sprite_id not in self._sprites:
            raise KeyError(f"Unknown sprite id: {sprite_id}")
        return self._sprites[sprite_id]

    def draw(self, surface: Any, sprite_id: str, rect: tuple[int, int, int, int]) -> None:
        sprite = self.get(sprite_id)
        scaled = self._pygame.transform.scale(sprite, (rect[2], rect[3]))
        surface.blit(scaled, (rect[0], rect[1]))
