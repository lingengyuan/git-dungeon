"""Runtime content-pack loading for CLI gameplay.

This loader is stricter than legacy M3 helpers:
- clear exceptions on malformed packs
- deterministic merge order
- support built-in packs, explicit external paths, and env directory discovery
"""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import yaml

from .loader import load_content
from .packs import PackLoader
from .schema import ContentPack, ContentRegistry


PACK_FILE_CANDIDATES = ("pack.yml", "cards.yml")
CHAPTER_OVERRIDE_FIELDS = {
    "name",
    "description",
    "min_commits",
    "max_commits",
    "boss_chance",
    "shop_enabled",
    "gold_bonus",
    "exp_bonus",
    "enemy_hp_multiplier",
    "enemy_atk_multiplier",
}


class ContentPackLoadError(ValueError):
    """Raised when a runtime content pack cannot be loaded safely."""


@dataclass(frozen=True)
class LoadedPackInfo:
    """Metadata for one loaded pack."""

    pack_id: str
    source_path: str


@dataclass
class RuntimeContent:
    """Runtime content bundle used by CLI."""

    registry: ContentRegistry
    loaded_packs: List[LoadedPackInfo] = field(default_factory=list)
    chapter_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    @property
    def loaded_pack_ids(self) -> List[str]:
        return [pack.pack_id for pack in self.loaded_packs]


@dataclass
class _ParsedRuntimePack:
    pack: ContentPack
    source_dir: Path
    chapter_overrides: Dict[str, Dict[str, Any]]


def _default_content_dir() -> Path:
    return Path(__file__).parent


def _pick_pack_file(pack_dir: Path) -> Optional[Path]:
    for filename in PACK_FILE_CANDIDATES:
        candidate = pack_dir / filename
        if candidate.exists():
            return candidate
    return None


def _is_pack_dir(path: Path) -> bool:
    return path.is_dir() and _pick_pack_file(path) is not None


def _discover_pack_dirs(root: Path) -> List[Path]:
    pack_dirs = [item for item in root.iterdir() if _is_pack_dir(item)]
    return sorted(pack_dirs, key=lambda item: item.name)


def _dedupe_preserve_order(paths: Iterable[Path]) -> List[Path]:
    unique: List[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def resolve_runtime_pack_dirs(
    content_pack_args: Optional[Sequence[str]],
    *,
    built_in_packs_dir: Path,
    env_content_dir: Optional[str],
) -> List[Path]:
    """Resolve deterministic pack directories from CLI args and env.

    Priority order (low -> high):
    1. explicit args, in user-provided order
    2. env directory packs (alphabetical by pack folder name)
    Later packs override earlier IDs.
    """

    resolved: List[Path] = []

    for raw in content_pack_args or []:
        candidate = Path(raw).expanduser()
        if candidate.exists():
            if _is_pack_dir(candidate):
                resolved.append(candidate)
                continue
            if candidate.is_dir():
                discovered = _discover_pack_dirs(candidate)
                if not discovered:
                    raise ContentPackLoadError(
                        f"No content packs found under directory: {candidate}"
                    )
                resolved.extend(discovered)
                continue
            raise ContentPackLoadError(f"Invalid content-pack target: {candidate}")

        built_in = built_in_packs_dir / raw
        if _is_pack_dir(built_in):
            resolved.append(built_in)
            continue
        raise ContentPackLoadError(
            f"Content pack '{raw}' not found. Checked path '{candidate}' and built-in '{built_in}'."
        )

    if env_content_dir:
        env_root = Path(env_content_dir).expanduser()
        if not env_root.exists() or not env_root.is_dir():
            raise ContentPackLoadError(
                f"GIT_DUNGEON_CONTENT_DIR is not a valid directory: {env_root}"
            )
        discovered = _discover_pack_dirs(env_root)
        if not discovered:
            raise ContentPackLoadError(f"No content packs found in GIT_DUNGEON_CONTENT_DIR: {env_root}")
        resolved.extend(discovered)

    return _dedupe_preserve_order(resolved)


def _load_pack_yaml(pack_dir: Path) -> Dict[str, Any]:
    pack_file = _pick_pack_file(pack_dir)
    if pack_file is None:
        raise ContentPackLoadError(
            f"Missing pack file in '{pack_dir}'. Expected one of: {', '.join(PACK_FILE_CANDIDATES)}"
        )
    try:
        raw = yaml.safe_load(pack_file.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ContentPackLoadError(f"Invalid YAML in '{pack_file}': {exc}") from exc
    if raw is None:
        raise ContentPackLoadError(f"Pack file is empty: {pack_file}")
    if not isinstance(raw, dict):
        raise ContentPackLoadError(f"Pack file root must be a mapping: {pack_file}")
    return raw


def _validate_pack_info(raw: Dict[str, Any], pack_dir: Path) -> Dict[str, Any]:
    pack_info = raw.get("pack_info")
    if not isinstance(pack_info, dict):
        raise ContentPackLoadError(f"Missing required 'pack_info' mapping in pack: {pack_dir}")
    if not pack_info.get("id"):
        raise ContentPackLoadError(f"Missing required 'pack_info.id' in pack: {pack_dir}")
    return pack_info


def _parse_chapter_overrides(raw: Dict[str, Any], pack_dir: Path) -> Dict[str, Dict[str, Any]]:
    overrides_raw = raw.get("chapter_overrides", {})
    if overrides_raw is None:
        return {}
    if not isinstance(overrides_raw, dict):
        raise ContentPackLoadError(f"'chapter_overrides' must be a mapping in pack: {pack_dir}")

    parsed: Dict[str, Dict[str, Any]] = {}
    for chapter_type, values in overrides_raw.items():
        if not isinstance(values, dict):
            raise ContentPackLoadError(
                f"chapter_overrides.{chapter_type} must be a mapping in pack: {pack_dir}"
            )
        normalized = str(chapter_type).strip().lower()
        if not normalized:
            raise ContentPackLoadError(f"Invalid empty chapter type key in pack: {pack_dir}")
        filtered = {key: values[key] for key in CHAPTER_OVERRIDE_FIELDS if key in values}
        if not filtered:
            raise ContentPackLoadError(
                f"chapter_overrides.{chapter_type} has no supported fields in pack: {pack_dir}"
            )
        parsed[normalized] = filtered
    return parsed


def _parse_runtime_pack(pack_dir: Path) -> _ParsedRuntimePack:
    raw = _load_pack_yaml(pack_dir)
    pack_info = _validate_pack_info(raw, pack_dir)
    chapter_overrides = _parse_chapter_overrides(raw, pack_dir)

    parser = PackLoader(pack_dir.parent)

    cards_raw = raw.get("cards", [])
    relics_raw = raw.get("relics", [])
    events_raw = raw.get("events", [])
    if not isinstance(cards_raw, list):
        raise ContentPackLoadError(f"'cards' must be a list in pack: {pack_dir}")
    if not isinstance(relics_raw, list):
        raise ContentPackLoadError(f"'relics' must be a list in pack: {pack_dir}")
    if not isinstance(events_raw, list):
        raise ContentPackLoadError(f"'events' must be a list in pack: {pack_dir}")

    cards = []
    for index, item in enumerate(cards_raw):
        if not isinstance(item, dict):
            raise ContentPackLoadError(f"cards[{index}] must be a mapping in pack: {pack_dir}")
        parsed = parser._parse_card(item)
        if parsed is None:
            raise ContentPackLoadError(f"Invalid card payload at cards[{index}] in pack: {pack_dir}")
        cards.append(parsed)

    relics = []
    for index, item in enumerate(relics_raw):
        if not isinstance(item, dict):
            raise ContentPackLoadError(f"relics[{index}] must be a mapping in pack: {pack_dir}")
        parsed = parser._parse_relic(item)
        if parsed is None:
            raise ContentPackLoadError(f"Invalid relic payload at relics[{index}] in pack: {pack_dir}")
        relics.append(parsed)

    events = []
    for index, item in enumerate(events_raw):
        if not isinstance(item, dict):
            raise ContentPackLoadError(f"events[{index}] must be a mapping in pack: {pack_dir}")
        parsed = parser._parse_event(item)
        if parsed is None:
            raise ContentPackLoadError(f"Invalid event payload at events[{index}] in pack: {pack_dir}")
        events.append(parsed)

    pack_id = str(pack_info["id"])
    pack = ContentPack(
        id=pack_id,
        name_key=str(pack_info.get("name_key", f"pack.{pack_id}.name")),
        desc_key=str(pack_info.get("desc_key", f"pack.{pack_id}.desc")),
        archetype=str(pack_info.get("archetype", "general")),
        rarity=str(pack_info.get("rarity", "uncommon")),
        points_cost=int(pack_info.get("points_cost", 100)),
        cards=cards,
        relics=relics,
        events=events,
    )
    return _ParsedRuntimePack(pack=pack, source_dir=pack_dir, chapter_overrides=chapter_overrides)


def _clone_registry(base: ContentRegistry) -> ContentRegistry:
    return ContentRegistry(
        cards=base.cards.copy(),
        relics=base.relics.copy(),
        statuses=base.statuses.copy(),
        enemies=base.enemies.copy(),
        archetypes=base.archetypes.copy(),
        events=base.events.copy(),
        characters=base.characters.copy(),
        packs=base.packs.copy(),
    )


def load_runtime_content(
    *,
    content_dir: Optional[str] = None,
    content_pack_args: Optional[Sequence[str]] = None,
    env_content_dir: Optional[str] = None,
) -> RuntimeContent:
    """Load base content + runtime packs with deterministic merge."""

    resolved_content_dir = Path(content_dir).expanduser() if content_dir else _default_content_dir()
    base_registry = load_content(str(resolved_content_dir))
    built_in_packs_dir = resolved_content_dir / "packs"

    effective_env_dir = env_content_dir
    if effective_env_dir is None:
        effective_env_dir = os.getenv("GIT_DUNGEON_CONTENT_DIR")

    pack_dirs = resolve_runtime_pack_dirs(
        content_pack_args,
        built_in_packs_dir=built_in_packs_dir,
        env_content_dir=effective_env_dir,
    )
    if not pack_dirs:
        return RuntimeContent(registry=base_registry)

    merged_registry = _clone_registry(base_registry)
    loaded: List[LoadedPackInfo] = []
    chapter_overrides: Dict[str, Dict[str, Any]] = {}

    for pack_dir in pack_dirs:
        parsed = _parse_runtime_pack(pack_dir)
        pack = parsed.pack

        for card in pack.cards:
            merged_registry.cards[card.id] = card
        for relic in pack.relics:
            merged_registry.relics[relic.id] = relic
        for event in pack.events:
            merged_registry.events[event.id] = event
        merged_registry.packs[pack.id] = pack

        for chapter_type, values in parsed.chapter_overrides.items():
            existing = chapter_overrides.setdefault(chapter_type, {})
            existing.update(values)

        loaded.append(LoadedPackInfo(pack_id=pack.id, source_path=str(pack_dir)))

    return RuntimeContent(
        registry=merged_registry,
        loaded_packs=loaded,
        chapter_overrides=chapter_overrides,
    )
