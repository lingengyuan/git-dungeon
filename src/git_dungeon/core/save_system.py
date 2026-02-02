"""Save and load system for game state."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from .character import CharacterComponent
from .entity import Entity
from .inventory import InventoryComponent, Item, ItemType, ItemRarity, ItemStats
from git_dungeon.utils.logger import setup_logger

logger = setup_logger(__name__)

# Import GameState only for type checking (avoid circular import)
if TYPE_CHECKING:
    from .game_engine import GameState


def _config_to_dict(config: Any) -> dict:
    """Convert config to dict, handling enums and Pydantic models."""
    if hasattr(config, 'model_dump'):
        result = {}
        for key, value in config.model_dump().items():
            if isinstance(value, Enum):
                result[key] = value.value
            else:
                result[key] = value
        return result
    return {}


@dataclass
class SaveMetadata:
    """Metadata for a save file."""

    schema_version: str = "1.0.0"
    save_time: str = ""
    game_time: float = 0
    player_level: int = 1
    player_hp: int = 0
    player_max_hp: int = 0
    current_commit_index: int = 0
    total_commits_defeated: int = 0

    @classmethod
    def create(cls) -> "SaveMetadata":
        """Create new metadata with current time."""
        return cls(save_time=datetime.now().isoformat())


@dataclass
class GameSaveData:
    """Complete game save data."""

    metadata: SaveMetadata
    player_entity: dict[str, Any]
    inventory: dict[str, Any]
    defeated_commits: list[str]
    current_commit_hash: str
    settings: dict[str, Any]


class SaveSystem:
    """System for saving and loading game state."""

    def __init__(self, save_dir: Optional[Path | str] = None):
        """Initialize save system.

        Args:
            save_dir: Directory for save files (Path or str)
        """
        if save_dir is None:
            save_dir = Path.home() / ".local" / "share" / "git-dungeon"
        elif isinstance(save_dir, str):
            save_dir = Path(save_dir)

        self.save_dir = save_dir
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.auto_save_enabled = True
        self.auto_save_interval: int = 10

    def get_save_path(self, slot: int = 0) -> Path:
        """Get path for a save slot.

        Args:
            slot: Save slot number (0-9)

        Returns:
            Path to save file
        """
        return self.save_dir / f"save_{slot}.json"

    def save(
        self,
        game_state: "GameState",
        slot: int = 0,
    ) -> bool:
        """Save game state to a slot.

        Args:
            game_state: Current game state
            slot: Save slot number

        Returns:
            True if save was successful
        """
        try:
            save_data = self._collect_save_data(game_state)
            save_path = self.get_save_path(slot)
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"Saved game to slot {slot}")
            return True

        except Exception as e:
            logger.error(f"Failed to save game: {e}")
            return False

    def load(
        self,
        game_state: "GameState",
        slot: int = 0,
    ) -> bool:
        """Load game state from a slot.

        Args:
            game_state: Game state to load into
            slot: Save slot number

        Returns:
            True if load was successful
        """
        try:
            save_path = self.get_save_path(slot)

            if not save_path.exists():
                logger.warning(f"Save file not found: {save_path}")
                return False

            with open(save_path, "r", encoding="utf-8") as f:
                save_data = json.load(f)

            self._restore_save_data(game_state, save_data)

            logger.info(f"Loaded game from slot {slot}")
            return True

        except Exception as e:
            logger.error(f"Failed to load game: {e}")
            return False

    @classmethod
    def load_game(cls, save_path: Path | str) -> Optional["GameState"]:
        """Load a complete game state from a save file.

        Args:
            save_path: Path to the save file

        Returns:
            Loaded GameState or None if failed
        """
        from .game_engine import GameState
        from git_dungeon.config import GameConfig

        try:
            if isinstance(save_path, str):
                save_path = Path(save_path)

            with open(save_path, "r", encoding="utf-8") as f:
                save_data = json.load(f)

            settings_data = save_data.get("settings", {})
            config = GameConfig(**settings_data) if settings_data else GameConfig()

            game = GameState(config=config)

            repo_path = config.repo_path
            if repo_path and repo_path != "./":
                game.load_repository(repo_path)

            save_system = cls()
            save_system._restore_save_data(game, save_data)

            logger.info(f"Loaded game from {save_path}")
            return game

        except Exception as e:
            logger.error(f"Failed to load game: {e}")
            return None

    def _collect_save_data(self, game_state: "GameState") -> dict:
        """Collect all data needed for saving."""
        player_entity = game_state.player
        player_char = player_entity.get_component(CharacterComponent)
        inventory_comp = player_entity.get_component(InventoryComponent)

        metadata = SaveMetadata.create()
        if player_char:
            metadata.player_level = player_char.level
            metadata.player_hp = player_char.current_hp
            metadata.player_max_hp = player_char.stats.hp.value if player_char.stats else 0
            metadata.current_commit_index = game_state.current_commit_index
            metadata.total_commits_defeated = len(game_state.defeated_commits)

        return {
            "version": "1.0.0",
            "metadata": asdict(metadata),
            "player": self._serialize_entity(player_entity) if player_entity else {},
            "inventory": self._serialize_inventory(inventory_comp),
            "defeated_commits": game_state.defeated_commits,
            "current_commit": game_state.current_commit.hash if game_state.current_commit else "",
            "settings": _config_to_dict(game_state.config),
        }

    def _restore_save_data(self, game_state: "GameState", data: dict) -> None:
        """Restore game state from save data."""
        metadata_data = data.get("metadata", {})
        game_state.game_time = metadata_data.get("game_time", 0)

        player_data = data.get("player", {})
        if game_state.player:
            self._deserialize_entity(game_state.player, player_data)

        inventory_data = data.get("inventory", {})
        if game_state.player:
            self._deserialize_inventory(game_state.player, inventory_data)

        game_state.defeated_commits = data.get("defeated_commits", [])
        current_commit_hash = data.get("current_commit", "")

        if current_commit_hash and game_state.parser:
            game_state.current_commit = game_state.parser.get_commit_by_hash(
                current_commit_hash[:8]
            )

    def _serialize_entity(self, entity: Entity) -> dict:
        """Serialize an entity."""
        char = entity.get_component(CharacterComponent)  # type: ignore[assignment]
        if not char:
            return {}

        return {
            "name": entity.name,
            "level": char.level,  # type: ignore[union-attr]
            "experience": char.experience,  # type: ignore[union-attr]
            "total_experience": char._total_exp_gained,  # type: ignore[union-attr]
            "hp": char.current_hp,  # type: ignore[union-attr]
            "mp": char.current_mp,  # type: ignore[union-attr]
            "stats": {
                "hp": char.stats.hp.value if char.stats else 0,  # type: ignore[union-attr]
                "mp": char.stats.mp.value if char.stats else 0,  # type: ignore[union-attr]
                "attack": char.stats.attack.value if char.stats else 0,  # type: ignore[union-attr]
                "defense": char.stats.defense.value if char.stats else 0,  # type: ignore[union-attr]
                "speed": char.stats.speed.value if char.stats else 0,  # type: ignore[union-attr]
                "critical": char.stats.critical.value if char.stats else 0,  # type: ignore[union-attr]
                "evasion": char.stats.evasion.value if char.stats else 0,  # type: ignore[union-attr]
                "luck": char.stats.luck.value if char.stats else 0,  # type: ignore[union-attr]
            } if char.stats else {},
        }

    def _deserialize_entity(self, entity: Entity, data: dict) -> None:
        """Deserialize an entity."""
        char = entity.get_component(CharacterComponent)  # type: ignore[assignment]
        if not char or not data:
            return

        char.level = data.get("level", 1)  # type: ignore[union-attr]
        char.experience = data.get("experience", 0)  # type: ignore[union-attr]
        char._total_exp_gained = data.get("total_experience", 0)  # type: ignore[union-attr]
        char.current_hp = data.get("hp", 100)  # type: ignore[union-attr]
        char.current_mp = data.get("mp", 50)  # type: ignore[union-attr]

        stats_data = data.get("stats", {})
        if stats_data and char.stats:  # type: ignore[union-attr]
            char.stats.hp.base_value = stats_data.get("hp", 100)  # type: ignore[union-attr]
            char.stats.mp.base_value = stats_data.get("mp", 50)  # type: ignore[union-attr]
            char.stats.attack.base_value = stats_data.get("attack", 10)  # type: ignore[union-attr]
            char.stats.defense.base_value = stats_data.get("defense", 5)  # type: ignore[union-attr]
            char.stats.speed.base_value = stats_data.get("speed", 10)  # type: ignore[union-attr]
            char.stats.critical.base_value = stats_data.get("critical", 10)  # type: ignore[union-attr]
            char.stats.evasion.base_value = stats_data.get("evasion", 5)  # type: ignore[union-attr]
            char.stats.luck.base_value = stats_data.get("luck", 5)  # type: ignore[union-attr]

    def _serialize_inventory(self, inventory: Optional[InventoryComponent]) -> dict:
        """Serialize inventory."""
        if not inventory:
            return {"items": [], "gold": 0}

        items_data = []
        for i, item in enumerate(inventory.items):
            if item:
                items_data.append({
                    "slot": i,
                    "id": item.id,
                    "name": item.name,
                    "type": item.item_type.value,
                    "rarity": item.rarity.value,
                    "description": item.description,
                    "value": item.value,
                    "stackable": item.stackable,
                    "stack_count": item.stack_count,
                    "stats": asdict(item.stats),
                })

        return {
            "items": items_data,
            "gold": inventory.gold,
            "max_slots": inventory.max_slots,
        }

    def _deserialize_inventory(
        self,
        entity: Entity,
        data: dict,
    ) -> None:
        """Deserialize inventory."""
        inventory = entity.get_component(InventoryComponent)  # type: ignore[assignment]
        if not inventory:
            return

        inventory.gold = data.get("gold", 0)  # type: ignore[union-attr]
        inventory.items = [None] * inventory.max_slots  # type: ignore[union-attr]

        for item_data in data.get("items", []):
            slot = item_data.get("slot", 0)
            if 0 <= slot < inventory.max_slots:
                stats_data = item_data.get("stats", {})
                stats = ItemStats(**stats_data)

                item = Item(
                    id=item_data["id"],
                    name=item_data["name"],
                    item_type=ItemType(item_data["type"]),
                    rarity=ItemRarity(item_data["rarity"]),
                    description=item_data.get("description", ""),
                    value=item_data.get("value", 0),
                    stats=stats,
                    stackable=item_data.get("stackable", False),
                    stack_count=item_data.get("stack_count", 1),
                )
                inventory.items[slot] = item

    def get_save_slots(self) -> list[dict]:
        """Get info about all save slots."""
        slots = []
        for i in range(10):
            path = self.get_save_path(i)
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    metadata = data.get("metadata", {})
                    slots.append({
                        "slot": i,
                        "exists": True,
                        "save_time": metadata.get("save_time", ""),
                        "player_level": metadata.get("player_level", 0),
                        "commits_defeated": metadata.get("total_commits_defeated", 0),
                    })
                except Exception:
                    slots.append({"slot": i, "exists": True, "error": True})
            else:
                slots.append({"slot": i, "exists": False})

        return slots

    def delete_save(self, slot: int) -> bool:
        """Delete a save slot.

        Args:
            slot: Slot number to delete

        Returns:
            True if successful
        """
        try:
            path = self.get_save_path(slot)
            if path.exists():
                path.unlink()
            return True
        except Exception as e:
            logger.error(f"Failed to delete save: {e}")
            return False
