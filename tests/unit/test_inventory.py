"""Unit tests for inventory module."""

from src.core.inventory import (
    InventoryComponent,
    Item,
    ItemType,
    ItemRarity,
    ItemStats,
    ItemFactory,
)
from src.core.entity import Entity
from src.core.character import CharacterComponent, CharacterType


class TestItem:
    """Tests for Item class."""

    def test_item_creation(self):
        """Test basic item creation."""
        item = Item(
            id="test_sword",
            name="Test Sword",
            item_type=ItemType.WEAPON,
            rarity=ItemRarity.RARE,
            description="A test sword",
            value=100,
        )

        assert item.id == "test_sword"
        assert item.name == "Test Sword"
        assert item.item_type == ItemType.WEAPON
        assert item.rarity == ItemRarity.RARE

    def test_display_name_with_rarity(self):
        """Test display name with rarity prefix."""
        common = Item(
            id="test",
            name="Test",
            item_type=ItemType.WEAPON,
            rarity=ItemRarity.COMMON,
        )
        assert common.display_name == "Test"

        rare = Item(
            id="test",
            name="Test",
            item_type=ItemType.WEAPON,
            rarity=ItemRarity.RARE,
        )
        assert rare.display_name == "Rare Test"

        legendary = Item(
            id="test",
            name="Test",
            item_type=ItemType.WEAPON,
            rarity=ItemRarity.LEGENDARY,
        )
        assert legendary.display_name == "Legendary Test"

    def test_stacking(self):
        """Test item stacking."""
        item = Item(
            id="potion",
            name="Health Potion",
            item_type=ItemType.CONSUMABLE,
            stackable=True,
            stack_count=3,
            max_stack=5,
        )

        added = item.add_to_stack(2)
        assert added == 2
        assert item.stack_count == 5

        # Can't add more than max
        added = item.add_to_stack(1)
        assert added == 0
        assert item.stack_count == 5

    def test_can_stack_with(self):
        """Test stacking compatibility."""
        item1 = Item(
            id="potion",
            name="Potion",
            item_type=ItemType.CONSUMABLE,
            stackable=True,
        )
        item2 = Item(
            id="potion",
            name="Potion",
            item_type=ItemType.CONSUMABLE,
            stackable=True,
        )
        item3 = Item(
            id="sword",
            name="Sword",
            item_type=ItemType.WEAPON,
            stackable=True,
        )

        assert item1.can_stack_with(item2) is True
        assert item1.can_stack_with(item3) is False


class TestInventoryComponent:
    """Tests for InventoryComponent class."""

    def test_inventory_creation(self):
        """Test inventory creation."""
        inv = InventoryComponent(max_slots=20)

        assert inv.max_slots == 20
        assert inv.item_count == 0
        assert inv.empty_slots == 20

    def test_add_item(self):
        """Test adding items to inventory."""
        inv = InventoryComponent(max_slots=5)

        item = Item(id="sword", name="Sword", item_type=ItemType.WEAPON)

        success, slot = inv.add_item(item)

        assert success is True
        assert slot == 0
        assert inv.item_count == 1
        assert inv.get_item(0) == item

    def test_add_full_inventory(self):
        """Test adding to full inventory."""
        inv = InventoryComponent(max_slots=2)

        item1 = Item(id="item1", name="Item1", item_type=ItemType.WEAPON)
        item2 = Item(id="item2", name="Item2", item_type=ItemType.WEAPON)
        item3 = Item(id="item3", name="Item3", item_type=ItemType.WEAPON)

        inv.add_item(item1)
        inv.add_item(item2)

        success, slot = inv.add_item(item3)

        assert success is False
        assert slot == -1

    def test_remove_item(self):
        """Test removing items from inventory."""
        inv = InventoryComponent(max_slots=5)

        item = Item(id="sword", name="Sword", item_type=ItemType.WEAPON)
        inv.add_item(item)

        removed = inv.remove_item(0)

        assert removed == item
        assert inv.get_item(0) is None

    def test_use_consumable(self):
        """Test using a consumable item."""
        inv = InventoryComponent(max_slots=5)

        # Create character
        entity = Entity(id="player", name="Player")
        char = CharacterComponent(CharacterType.PLAYER, "Player")
        char.initialize_stats(hp=100, mp=50, attack=20, defense=10)
        entity.add_component(char)
        entity.add_component(inv)

        # Create and add potion
        potion = Item(
            id="health_potion",
            name="Health Potion",
            item_type=ItemType.CONSUMABLE,
            stats=ItemStats(hp_bonus=30),
        )
        inv.add_item(potion)

        # Use potion
        char.take_damage(50)
        # Defense 10, actual damage = max(1, 50-10) = 40
        assert char.current_hp == 60

        success = inv.use_item(0, entity)
        assert success is True
        # Potion heals 30, HP = 60 + 30 = 90
        assert char.current_hp == 90

    def test_find_items_by_id(self):
        """Test finding items by ID."""
        inv = InventoryComponent(max_slots=10)

        item1 = Item(id="potion", name="Potion", item_type=ItemType.CONSUMABLE)
        item2 = Item(id="potion", name="Potion", item_type=ItemType.CONSUMABLE)

        inv.add_item(item1)
        inv.add_item(item2)

        slots = inv.find_items_by_id("potion")
        assert len(slots) == 2

    def test_clear(self):
        """Test clearing inventory."""
        inv = InventoryComponent(max_slots=5)

        inv.add_item(Item(id="item1", name="Item1", item_type=ItemType.WEAPON))
        inv.add_item(Item(id="item2", name="Item2", item_type=ItemType.WEAPON))

        items = inv.clear()

        assert len(items) == 2
        assert inv.item_count == 0


class TestItemFactory:
    """Tests for ItemFactory class."""

    def test_create_from_python_file(self):
        """Test creating item from Python file."""
        item = ItemFactory.create_from_file("src/main.py", change_count=20)

        assert item.item_type == ItemType.WEAPON  # .py maps to WEAPON
        assert item.stats.attack == 20

    def test_create_from_javascript_file(self):
        """Test creating item from JavaScript file."""
        item = ItemFactory.create_from_file("app.js", change_count=10)

        assert item.item_type == ItemType.CONSUMABLE  # .js maps to CONSUMABLE
        assert item.stats.hp_bonus == 100  # 10 * 10

    def test_create_from_markdown_file(self):
        """Test creating item from Markdown file."""
        item = ItemFactory.create_from_file("README.md", change_count=5)

        assert item.item_type == ItemType.SPECIAL  # .md maps to SPECIAL

    def test_rarity_distribution(self):
        """Test that rarity follows expected distribution."""
        import random

        # Set seed once for reproducibility
        random.seed(42)

        # Run many times to check distribution
        rarities = []
        for _ in range(1000):
            item = ItemFactory.create_from_file("test.py", change_count=10)
            rarities.append(item.rarity)

        # Check that we get a reasonable distribution
        common_count = sum(1 for r in rarities if r == ItemRarity.COMMON)
        assert common_count > 500  # Should be ~60%
