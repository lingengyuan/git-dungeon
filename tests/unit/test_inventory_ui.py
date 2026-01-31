"""Tests for inventory UI components."""

import pytest

from src.ui.inventory_screen import (
    format_item_slot,
    ITEM_TYPE_ICONS,
    RARITY_COLORS,
    InventorySlot,
    ItemDetailPanel,
    InventoryScreen,
)
from src.core.inventory import Item, ItemType, ItemRarity


class TestFormatItemSlot:
    """Tests for item slot formatting."""

    def test_empty_slot(self):
        """Test formatting empty slot."""
        result = format_item_slot(1, None)
        assert "Empty" in result
        assert "1:" in result

    def test_empty_slot_selected(self):
        """Test formatting selected empty slot."""
        result = format_item_slot(1, None, selected=True)
        assert "◎" in result or "[★]" in result

    def test_weapon_item(self):
        """Test formatting weapon item."""
        item = Item(
            id="sword",
            name="Sword",
            item_type=ItemType.WEAPON,
            rarity=ItemRarity.RARE,
            value=100,
        )
        result = format_item_slot(1, item)
        assert "Sword" in result
        assert ITEM_TYPE_ICONS[ItemType.WEAPON] in result

    def test_consumable_with_stack(self):
        """Test formatting consumable with stack."""
        item = Item(
            id="potion",
            name="Health Potion",
            item_type=ItemType.CONSUMABLE,
            stackable=True,
            stack_count=5,
        )
        result = format_item_slot(2, item)
        assert "Health Potion" in result
        assert "x5" in result

    def test_legendary_rarity(self):
        """Test legendary item shows gold color."""
        item = Item(
            id="legend",
            name="Legendary Item",
            item_type=ItemType.SPECIAL,
            rarity=ItemRarity.LEGENDARY,
        )
        result = format_item_slot(1, item)
        assert "Legendary Item" in result


class TestItemTypeIcons:
    """Tests for item type icons."""

    def test_all_types_have_icons(self):
        """Test all item types have icons."""
        for item_type in ItemType:
            assert item_type in ITEM_TYPE_ICONS
            assert ITEM_TYPE_ICONS[item_type] is not None


class TestRarityColors:
    """Tests for rarity colors."""

    def test_all_rarities_have_colors(self):
        """Test all rarities have colors."""
        for rarity in ItemRarity:
            assert rarity in RARITY_COLORS
            assert RARITY_COLORS[rarity] is not None


class TestInventorySlot:
    """Tests for InventorySlot component."""

    def test_slot_creation_empty(self):
        """Test creating empty slot."""
        slot = InventorySlot(index=1, item=None)
        assert slot.index == 1
        assert slot.item is None
        assert slot.selected is False

    def test_slot_creation_with_item(self):
        """Test creating slot with item."""
        item = Item(
            id="potion",
            name="Potion",
            item_type=ItemType.CONSUMABLE,
        )
        slot = InventorySlot(index=3, item=item, selected=True)
        assert slot.index == 3
        assert slot.item is item
        assert slot.selected is True


class TestItemDetailPanel:
    """Tests for ItemDetailPanel component."""

    def test_empty_panel(self):
        """Test panel with no item."""
        panel = ItemDetailPanel(item=None)
        assert panel._item is None

    def test_panel_with_item(self):
        """Test panel with item."""
        item = Item(
            id="sword",
            name="Magic Sword",
            item_type=ItemType.WEAPON,
            rarity=ItemRarity.EPIC,
            value=150,
            description="A powerful sword",
        )
        panel = ItemDetailPanel(item=item)
        assert panel._item is item
        assert panel._item.name == "Magic Sword"

    def test_update_item(self):
        """Test updating item."""
        panel = ItemDetailPanel(item=None)
        item = Item(
            id="shield",
            name="Shield",
            item_type=ItemType.ARMOR,
        )
        panel.update_item(item)
        assert panel._item is item


class TestInventoryScreen:
    """Tests for InventoryScreen component."""

    def test_screen_creation_empty(self):
        """Test creating screen with empty inventory."""
        screen = InventoryScreen(max_slots=5)
        assert screen is not None
        assert screen._max_slots == 5
        assert len(screen._items) == 5

    def test_screen_creation_with_items(self):
        """Test creating screen with items."""
        items = [
            Item(id="p1", name="Potion1", item_type=ItemType.CONSUMABLE),
            Item(id="p2", name="Potion2", item_type=ItemType.CONSUMABLE),
            None,
        ]
        screen = InventoryScreen(items=items, max_slots=5)
        assert screen._items[0] is not None
        assert screen._items[1] is not None
        assert screen._items[2] is None

    def test_selection_index(self):
        """Test selection index management."""
        items = [None] * 5
        screen = InventoryScreen(items=items, max_slots=5)
        assert screen._selected_index == 0

    def test_use_item_empty_slot(self):
        """Test using empty slot returns False."""
        items = [None] * 5
        screen = InventoryScreen(items=items, max_slots=5)
        result = screen.use_item()
        assert result is False

    def test_use_item_callback(self):
        """Test using item calls callback."""
        items = [
            Item(id="potion", name="Potion", item_type=ItemType.CONSUMABLE),
            None,
        ]
        used = []

        def on_use(idx, item):
            used.append((idx, item))

        screen = InventoryScreen(items=items, max_slots=5, on_use=on_use)
        result = screen.use_item()
        assert result is True
        assert len(used) == 1
        assert used[0][0] == 0
        assert used[0][1].name == "Potion"

    def test_discard_item_empty_slot(self):
        """Test discarding empty slot returns False."""
        items = [None] * 5
        screen = InventoryScreen(items=items, max_slots=5)
        result = screen.discard_item()
        assert result is False

    def test_discard_item_callback(self):
        """Test discarding item calls callback."""
        items = [
            Item(id="sword", name="Sword", item_type=ItemType.WEAPON),
            None,
        ]
        discarded = []

        def on_discard(idx, item):
            discarded.append((idx, item))

        screen = InventoryScreen(items=items, max_slots=5, on_discard=on_discard)
        result = screen.discard_item()
        assert result is True
        assert len(discarded) == 1
        assert discarded[0][1].name == "Sword"

    def test_back_callback(self):
        """Test back button calls callback."""
        back_called = []

        def on_back():
            back_called.append(True)

        screen = InventoryScreen(on_back=on_back)
        screen.back()
        assert len(back_called) == 1

    def test_update_items(self):
        """Test updating items."""
        items = [None] * 5
        screen = InventoryScreen(items=items, max_slots=5)

        new_items = [
            Item(id="a", name="A", item_type=ItemType.WEAPON),
            Item(id="b", name="B", item_type=ItemType.ARMOR),
        ]

        screen.update_items(new_items)
        assert screen._items[0] is not None
        assert screen._items[0].name == "A"


class TestInventoryUIIntegration:
    """Integration tests for inventory UI."""

    def test_full_inventory_workflow(self):
        """Test complete inventory workflow."""
        # Create items
        items = [
            Item(id="potion", name="Health Potion", item_type=ItemType.CONSUMABLE),
            Item(id="sword", name="Iron Sword", item_type=ItemType.WEAPON),
            Item(id="shield", name="Wood Shield", item_type=ItemType.ARMOR),
            None,
            None,
        ]

        # Create screen
        screen = InventoryScreen(items=items, max_slots=5)

        # Verify items are correct
        assert screen._items[0] is not None
        assert screen._items[0].name == "Health Potion"
        assert screen._items[1] is not None
        assert screen._items[1].name == "Iron Sword"
        assert screen._items[2] is not None
        assert screen._items[2].name == "Wood Shield"

    def test_stackable_item_usage(self):
        """Test using stackable item decreases count."""
        items = [
            Item(
                id="potion",
                name="Potion",
                item_type=ItemType.CONSUMABLE,
                stackable=True,
                stack_count=3,
            ),
        ]

        screen = InventoryScreen(items=items, max_slots=5)

        # Use item twice
        screen.use_item()
        assert screen._items[0] is not None
        assert screen._items[0].stack_count == 2

        screen.use_item()
        assert screen._items[0] is not None
        assert screen._items[0].stack_count == 1

        # Third use removes item
        screen.use_item()
        assert screen._items[0] is None

    def test_item_discard_removes_item(self):
        """Test discarding item removes it from inventory."""
        items = [
            Item(id="sword", name="Sword", item_type=ItemType.WEAPON),
            None,
        ]

        screen = InventoryScreen(items=items, max_slots=5)
        assert screen._items[0] is not None

        screen.discard_item()
        assert screen._items[0] is None

    def test_item_use_removes_single_from_stack(self):
        """Test using item from stack only removes one."""
        items = [
            Item(
                id="arrow",
                name="Arrow",
                item_type=ItemType.CONSUMABLE,
                stackable=True,
                stack_count=10,
            ),
        ]

        screen = InventoryScreen(items=items, max_slots=5)
        screen.use_item()
        assert screen._items[0] is not None
        assert screen._items[0].stack_count == 9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
