"""Inventory UI components for Git Dungeon."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static, Button
from git_dungeon.core.inventory import Item, ItemType, ItemRarity


# 物品类型到 emoji 的映射
ITEM_TYPE_ICONS = {
    ItemType.WEAPON: "⚔️",
    ItemType.ARMOR: "🛡️",
    ItemType.CONSUMABLE: "🧪",
    ItemType.ACCESSORY: "💎",
    ItemType.MATERIAL: "📦",
    ItemType.SPECIAL: "⭐",
}

# 稀有度到颜色的映射
RARITY_COLORS = {
    ItemRarity.COMMON: "white",
    ItemRarity.RARE: "blue",
    ItemRarity.EPIC: "purple",
    ItemRarity.LEGENDARY: "gold",
    ItemRarity.CORRUPTED: "red",
}


def format_item_slot(index: int, item: Item | None, selected: bool = False) -> str:
    """Format a single inventory slot.

    Args:
        index: Slot index (1-based for display)
        item: Item in slot or None
        selected: Whether this slot is selected

    Returns:
        Formatted slot string
    """
    if item is None:
        prefix = "◎" if selected else "○"
        return f"{prefix} {index}: Empty"

    icon = ITEM_TYPE_ICONS.get(item.item_type, "📦")
    rarity_color = RARITY_COLORS.get(item.rarity, "white")

    # Format stats
    stats = []
    if hasattr(item, 'stats') and item.stats:
        if hasattr(item.stats, 'attack') and item.stats.attack:
            stats.append(f"ATK:{item.stats.attack}")
        if hasattr(item.stats, 'defense') and item.stats.defense:
            stats.append(f"DEF:{item.stats.defense}")
        if hasattr(item.stats, 'hp_bonus') and item.stats.hp_bonus:
            stats.append(f"HP:+{item.stats.hp_bonus}")

    stats_str = f" | {', '.join(stats)}" if stats else ""
    count_str = f" x{item.stack_count}" if item.stackable and item.stack_count > 1 else ""

    selected_mark = "[★]" if selected else ""

    return f"{selected_mark} {icon} {item.name}{count_str}{stats_str}"


class InventorySlot(Button):
    """Button representing an inventory slot."""

    def __init__(self, index: int, item: Item | None = None, selected: bool = False):
        """Initialize inventory slot.

        Args:
            index: Slot index
            item: Item in slot or None
            selected: Whether this slot is selected
        """
        self.index = index
        self.item = item
        self.selected = selected
        label = format_item_slot(index, item, selected)
        super().__init__(label, id=f"slot-{index}")


class InventoryPanel(Static):
    """Panel showing inventory contents."""

    def __init__(self, items: list[Item | None], max_slots: int = 10, selected_index: int = -1, **kwargs):
        """Initialize inventory panel.

        Args:
            items: List of items (None for empty slots)
            max_slots: Maximum number of slots
            selected_index: Currently selected slot index (-1 for none)
        """
        super().__init__(**kwargs)
        self._items = items
        self._max_slots = max_slots
        self._selected_index = selected_index

    def compose(self) -> ComposeResult:
        """Compose the inventory panel."""
        # Create slot buttons
        for i in range(self._max_slots):
            item = self._items[i] if i < len(self._items) else None
            selected = (i == self._selected_index)
            yield InventorySlot(index=i + 1, item=item, selected=selected)


class ItemDetailPanel(Static):
    """Panel showing detailed item information."""

    def __init__(self, item: Item | None = None, **kwargs):
        """Initialize item detail panel.

        Args:
            item: Item to show details for, or None
        """
        super().__init__(**kwargs)
        self._item = item

    def compose(self) -> ComposeResult:
        """Compose the item detail panel."""
        if self._item is None:
            yield Static("选择物品查看详情", classes="detail-empty")
            return

        icon = ITEM_TYPE_ICONS.get(self._item.item_type, "📦")
        rarity_color = RARITY_COLORS.get(self._item.rarity, "white")

        yield Container(
            Static(f"{icon} {self._item.name}", classes="item-name"),
            Static(f"类型: {self._item.item_type.value}", classes="item-type"),
            Static(f"稀有度: {self._item.rarity.value}", classes="item-rarity"),
            Static(f"价值: {self._item.value}", classes="item-value"),
            Static(f"描述: {self._item.description or '无'}", classes="item-desc"),
            classes="item-details",
        )

    def update_item(self, item: Item | None) -> None:
        """Update displayed item."""
        self._item = item
        self.refresh()


class InventoryScreen(Static):
    """Main inventory screen."""

    CSS = """
    InventoryScreen {
        layout: vertical;
        height: 100%;
        width: 100%;
    }

    .inventory-header {
        text-style: bold;
        color: $accent;
        margin: 1;
    }

    .inventory-grid {
        layout: grid;
        grid-size: 5 2;
        margin: 1;
        border: solid $accent;
        padding: 1;
    }

    .inventory-slot {
        width: 30;
        height: 3;
    }

    .item-details {
        layout: vertical;
        border: solid $text-muted;
        margin: 1;
        padding: 1;
        height: 12;
    }

    .item-details .item-name {
        text-style: bold;
        color: $accent;
    }

    .item-details .item-type {
        color: $text-muted;
    }

    .item-details .item-rarity {
        color: $success;
    }

    .item-details .item-value {
        color: $warning;
    }

    .item-details .item-desc {
        color: $text-muted;
    }

    .action-area {
        layout: horizontal;
        height: 3;
        margin: 1;
    }

    .action-button {
        width: 20;
        margin: 0 1;
    }

    .help-text {
        color: $text-muted;
        margin: 1;
    }
    """

    def __init__(
        self,
        items: list[Item | None] | None = None,
        max_slots: int = 10,
        on_use=None,
        on_discard=None,
        on_back=None,
        **kwargs,
    ):
        """Initialize inventory screen.

        Args:
            items: List of items (None for empty slots)
            max_slots: Maximum inventory slots
            on_use: Callback when item is used (slot_index, item)
            on_discard: Callback when item is discarded (slot_index, item)
            on_back: Callback when going back
        """
        super().__init__(**kwargs)
        self._items = items or [None] * max_slots
        self._max_slots = max_slots
        self._selected_index = 0
        self._on_use = on_use
        self._on_discard = on_discard
        self._on_back = on_back
        self._detail_panel = ItemDetailPanel(id="item-detail")

    def compose(self) -> ComposeResult:
        """Compose the inventory screen."""
        # Header
        item_count = sum(1 for i in self._items if i is not None)
        yield Static(f"💼 物品栏 ({item_count}/{self._max_slots})", classes="inventory-header")

        # Inventory grid
        yield Container(
            *(InventorySlot(index=i + 1, item=self._items[i], selected=(i == self._selected_index))
              for i in range(self._max_slots)),
            classes="inventory-grid",
            id="inventory-slots",
        )

        # Item details
        yield self._detail_panel

        # Action buttons
        yield Container(
            Button("[1-9/方向键] 选择", id="btn-select", classes="action-button"),
            Button("[回车] 使用", id="btn-use", classes="action-button"),
            Button("[d] 丢弃", id="btn-discard", classes="action-button"),
            Button("[b/ESC] 返回", id="btn-back", classes="action-button"),
            classes="action-area",
        )

        # Help text
        yield Static("提示: 使用数字键或方向键选择物品，按回车使用，按d丢弃", classes="help-text")

    def _update_slots(self) -> None:
        """Update slot button labels."""
        # Skip DOM update if not mounted
        if not self.is_mounted:
            return

        try:
            container = self.query_one("#inventory-slots", Container)
            for i, widget in enumerate(container.children):
                if isinstance(widget, InventorySlot):
                    widget.label = format_item_slot(i + 1, self._items[i], i == self._selected_index)

            # Update detail panel
            item = self._items[self._selected_index] if self._selected_index < len(self._items) else None
            self._detail_panel.update_item(item)
        except Exception:
            pass  # Ignore DOM errors if not properly mounted

    def select_next(self) -> None:
        """Select next slot."""
        self._selected_index = (self._selected_index + 1) % self._max_slots
        self._update_slots()

    def select_previous(self) -> None:
        """Select previous slot."""
        self._selected_index = (self._selected_index - 1) % self._max_slots
        self._update_slots()

    def use_item(self) -> bool:
        """Use the selected item.

        Returns:
            True if item was used
        """
        if self._selected_index >= len(self._items):
            return False

        item = self._items[self._selected_index]
        if item is None:
            return False

        if self._on_use:
            self._on_use(self._selected_index, item)

        # Remove item if not stackable
        if not item.stackable or item.stack_count <= 1:
            self._items[self._selected_index] = None
        else:
            item.stack_count -= 1

        self._update_slots()
        return True

    def discard_item(self) -> bool:
        """Discard the selected item.

        Returns:
            True if item was discarded
        """
        if self._selected_index >= len(self._items):
            return False

        item = self._items[self._selected_index]
        if item is None:
            return False

        if self._on_discard:
            self._on_discard(self._selected_index, item)

        self._items[self._selected_index] = None
        self._update_slots()
        return True

    def back(self) -> None:
        """Go back to previous screen."""
        if self._on_back:
            self._on_back()

    def update_items(self, items: list[Item | None]) -> None:
        """Update inventory items."""
        self._items = items
        self._update_slots()
