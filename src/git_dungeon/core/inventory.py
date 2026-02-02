"""Inventory and item system."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .component import Component
from .entity import Entity


class ItemType(Enum):
    """Types of items."""

    WEAPON = "weapon"
    ARMOR = "armor"
    CONSUMABLE = "consumable"
    ACCESSORY = "accessory"
    MATERIAL = "material"
    SPECIAL = "special"


class ItemRarity(Enum):
    """Item rarity levels."""

    COMMON = "common"      # 白色
    RARE = "rare"          # 蓝色
    EPIC = "epic"          # 紫色
    LEGENDARY = "legendary"  # 金色
    CORRUPTED = "corrupted"  # 红色


@dataclass
class ItemStats:
    """Stats provided by an item."""

    attack: int = 0
    defense: int = 0
    hp_bonus: int = 0
    mp_bonus: int = 0
    critical_bonus: int = 0
    evasion_bonus: int = 0
    luck_bonus: int = 0


@dataclass
class Item:
    """Base item class."""

    id: str
    name: str
    item_type: ItemType
    rarity: ItemRarity = ItemRarity.COMMON
    description: str = ""
    value: int = 0
    stats: ItemStats = field(default_factory=ItemStats)
    stackable: bool = False
    stack_count: int = 1
    max_stack: int = 99

    @property
    def display_name(self) -> str:
        """Get display name with rarity prefix."""
        prefixes = {
            ItemRarity.COMMON: "",
            ItemRarity.RARE: "Rare ",
            ItemRarity.EPIC: "Epic ",
            ItemRarity.LEGENDARY: "Legendary ",
            ItemRarity.CORRUPTED: "Corrupted ",
        }
        return f"{prefixes[self.rarity]}{self.name}"

    @property
    def total_stats(self) -> ItemStats:
        """Get total stats (for stacks)."""
        stats = ItemStats()
        multiplier = self.stack_count if self.stackable else 1

        stats.attack = self.stats.attack * multiplier
        stats.defense = self.stats.defense * multiplier
        stats.hp_bonus = self.stats.hp_bonus * multiplier
        stats.mp_bonus = self.stats.mp_bonus * multiplier

        return stats

    def can_stack_with(self, other: "Item") -> bool:
        """Check if item can stack with another."""
        return (
            self.stackable
            and self.id == other.id
            and self.stack_count < self.max_stack
        )

    def add_to_stack(self, count: int = 1) -> int:
        """Add to stack, return number added."""
        can_add = min(count, self.max_stack - self.stack_count)
        self.stack_count += can_add
        return can_add


class InventoryComponent(Component):
    """Inventory component for entities with items."""

    def __init__(self, max_slots: int = 50):
        """Initialize inventory.

        Args:
            max_slots: Maximum number of item slots
        """
        super().__init__()
        self.max_slots = max_slots
        self.items: list[Optional[Item]] = [None] * max_slots
        self.gold: int = 0

    @property
    def item_count(self) -> int:
        """Get number of items in inventory."""
        return sum(1 for item in self.items if item is not None)

    @property
    def empty_slots(self) -> int:
        """Get number of empty slots."""
        return self.max_slots - self.item_count

    def add_item(self, item: Item) -> tuple[bool, int]:
        """Add an item to inventory.

        Args:
            item: Item to add

        Returns:
            Tuple of (success, slot_index or -1)
        """
        # Try to stack first
        if item.stackable:
            for i, inv_item in enumerate(self.items):
                if inv_item and inv_item.can_stack_with(item):
                    added = inv_item.add_to_stack(item.stack_count)
                    if added >= item.stack_count:
                        return True, i
                    item.stack_count -= added

        # Find empty slot
        for i, slot in enumerate(self.items):
            if slot is None:
                self.items[i] = item
                return True, i

        return False, -1

    def remove_item(self, slot_index: int) -> Optional[Item]:
        """Remove an item from inventory.

        Args:
            slot_index: Index of item to remove

        Returns:
            Removed item or None
        """
        if 0 <= slot_index < self.max_slots:
            item = self.items[slot_index]
            self.items[slot_index] = None
            return item
        return None

    def get_item(self, slot_index: int) -> Optional[Item]:
        """Get item at slot."""
        if 0 <= slot_index < self.max_slots:
            return self.items[slot_index]
        return None

    def use_item(self, slot_index: int, character: Entity) -> bool:
        """Use an item from inventory.

        Args:
            slot_index: Index of item to use
            character: Character to apply item to

        Returns:
            True if item was used
        """
        item = self.get_item(slot_index)
        if not item:
            return False

        if item.item_type == ItemType.CONSUMABLE:
            # Apply stats
            from .character import get_character

            char = get_character(character)
            if item.stats.hp_bonus > 0:
                char.heal(item.stats.hp_bonus)
            if item.stats.mp_bonus > 0:
                char.current_mp = min(
                    char.stats.mp.value,
                    char.current_mp + item.stats.mp_bonus,
                )

            # Reduce stack or remove
            if item.stackable:
                item.stack_count -= 1
                if item.stack_count <= 0:
                    self.remove_item(slot_index)
            else:
                self.remove_item(slot_index)

            return True

        return False

    def find_items_by_id(self, item_id: str) -> list[int]:
        """Find all slots containing an item ID."""
        return [
            i for i, item in enumerate(self.items)
            if item and item.id == item_id
        ]

    def get_all_items(self) -> list[tuple[int, Item]]:
        """Get all items with their indices."""
        return [
            (i, item) for i, item in enumerate(self.items)
            if item is not None
        ]

    def clear(self) -> list[Item]:
        """Clear inventory, return all items."""
        items = [item for item in self.items if item is not None]
        self.items = [None] * self.max_slots
        return items


# Item factory
class ItemFactory:
    """Factory for creating items from commit data."""

    # Mapping of file extensions to item types
    FILE_EXTENSION_MAP = {
        ".py": (ItemType.WEAPON, "魔法书"),
        ".go": (ItemType.WEAPON, "武器"),
        ".js": (ItemType.CONSUMABLE, "药水"),
        ".ts": (ItemType.WEAPON, "法杖"),
        ".rs": (ItemType.ARMOR, "护甲"),
        ".java": (ItemType.WEAPON, "圣剑"),
        ".cpp": (ItemType.WEAPON, "重剑"),
        ".c": (ItemType.ARMOR, "盾牌"),
        ".md": (ItemType.SPECIAL, "地图碎片"),
        ".sql": (ItemType.ACCESSORY, "护符"),
        ".json": (ItemType.ACCESSORY, "符文"),
        ".yaml": (ItemType.SPECIAL, "卷轴"),
        ".yml": (ItemType.SPECIAL, "卷轴"),
        ".html": (ItemType.CONSUMABLE, "面包"),
        ".css": (ItemType.ARMOR, "披风"),
    }

    RARITY_CHANCES = {
        ItemRarity.COMMON: 0.60,
        ItemRarity.RARE: 0.25,
        ItemRarity.EPIC: 0.10,
        ItemRarity.LEGENDARY: 0.04,
        ItemRarity.CORRUPTED: 0.01,
    }

    @classmethod
    def create_from_file(
        cls,
        filepath: str,
        change_count: int = 1,
    ) -> Item:
        """Create an item from a file path.

        Args:
            filepath: Path to the file
            change_count: Number of changes (affects power)

        Returns:
            Generated Item
        """
        import random

        # Get extension
        ext = "." + filepath.split(".")[-1] if "." in filepath else ""

        # Get item type and base name
        item_info = cls.FILE_EXTENSION_MAP.get(ext, (ItemType.MATERIAL, "材料"))
        item_type, base_name = item_info

        # Determine rarity
        roll = random.random()
        cumulative = 0
        for rarity, chance in cls.RARITY_CHANCES.items():
            cumulative += chance
            if roll <= cumulative:
                selected_rarity = rarity
                break
        else:
            selected_rarity = ItemRarity.COMMON

        # Create item
        item_id = f"item_{filepath.replace('/', '_').replace('.', '_')}"
        stats = ItemStats()

        if item_type == ItemType.WEAPON:
            stats.attack = change_count
        elif item_type == ItemType.ARMOR:
            stats.defense = change_count
        elif item_type == ItemType.CONSUMABLE:
            stats.hp_bonus = change_count * 10

        item = Item(
            id=item_id,
            name=f"{base_name} ({filepath.split('/')[-1][:10]})",
            item_type=item_type,
            rarity=selected_rarity,
            description=f"从 {filepath} 掉落的{item_type.value}",
            value=change_count * 10,
            stats=stats,
            stackable=item_type == ItemType.CONSUMABLE,
        )

        return item
