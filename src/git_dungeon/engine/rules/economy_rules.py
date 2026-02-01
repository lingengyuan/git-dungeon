# economy_rules.py - Shop and economy system

"""
Shop and economy system for Git Dungeon.

Features:
- Multiple item types (consumables, equipment, skills)
- Price scaling based on chapter
- Purchase history
- Inventory management
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

from git_dungeon.engine.rng import RNG, random_weighted_choice, roll_chance
from git_dungeon.engine.events import GameEvent, EventType


class ItemType(Enum):
    """Types of items"""
    CONSUMABLE = "consumable"
    WEAPON = "weapon"
    ARMOR = "armor"
    ACCESSORY = "accessory"
    SKILL = "skill"


class ItemRarity(Enum):
    """Item rarity levels"""
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


@dataclass
class Item:
    """A shop item"""
    item_id: str
    name: str
    item_type: ItemType
    rarity: ItemRarity
    price: int
    effect: str  # Description of effect
    value: int  # Effect value (HP heal, ATK bonus, etc.)
    description: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "name": self.name,
            "type": self.item_type.value,
            "rarity": self.rarity.value,
            "price": self.price,
            "effect": self.effect,
            "value": self.value,
            "description": self.description,
        }


@dataclass
class ShopInventory:
    """Items available in a shop"""
    items: List[Item] = field(default_factory=list)
    refresh_cost: int = 100
    reroll_cost: int = 50


@dataclass
class PlayerInventory:
    """Player's inventory"""
    items: List[Item] = field(default_factory=list)
    gold: int = 0
    max_items: int = 20
    
    def add_item(self, item: Item) -> bool:
        """Add item to inventory."""
        if len(self.items) >= self.max_items:
            return False
        self.items.append(item)
        return True
    
    def remove_item(self, item_id: str) -> Optional[Item]:
        """Remove item from inventory by ID."""
        for i, item in enumerate(self.items):
            if item.item_id == item_id:
                return self.items.pop(i)
        return None
    
    def has_item(self, item_id: str) -> bool:
        """Check if player has item."""
        return any(item.item_id == item_id for item in self.items)
    
    def get_items_by_type(self, item_type: ItemType) -> List[Item]:
        """Get all items of a type."""
        return [item for item in self.items if item.item_type == item_type]
    
    def get_total_value(self) -> int:
        """Get total value of all items."""
        return sum(item.price for item in self.items)


class ShopSystem:
    """
    Manages shop operations.
    
    Features:
    - Generate shop inventory
    - Handle purchases
    - Price scaling
    - Shop events
    """
    
    # Default shop inventory templates
    CONSUMABLES = [
        ("health_potion", "生命药水", ItemRarity.COMMON, 50, "heal_hp", 50, "恢复 50 HP"),
        ("mana_potion", "法力药水", ItemRarity.COMMON, 30, "heal_mp", 30, "恢复 30 MP"),
        ("super_potion", "超级药水", ItemRarity.RARE, 120, "heal_hp", 150, "恢复 150 HP"),
        ("elixir", "万能药剂", ItemRarity.EPIC, 200, "heal_all", 100, "恢复 100 HP 和 MP"),
    ]
    
    WEAPONS = [
        ("dagger", "匕首", ItemRarity.COMMON, 100, "atk", 3, "+3 攻击力"),
        ("sword", "利剑", ItemRarity.RARE, 250, "atk", 8, "+8 攻击力"),
        ("blade", "神剑", ItemRarity.EPIC, 500, "atk", 15, "+15 攻击力"),
        ("legendary_sword", "传奇之剑", ItemRarity.LEGENDARY, 1000, "atk", 25, "+25 攻击力"),
    ]
    
    ARMOR = [
        ("leather", "皮甲", ItemRarity.COMMON, 100, "def", 2, "+2 防御"),
        ("chainmail", "锁甲", ItemRarity.RARE, 200, "def", 5, "+5 防御"),
        ("plate", "板甲", ItemRarity.EPIC, 400, "def", 10, "+10 防御"),
        ("dragon_scale", "龙鳞甲", ItemRarity.LEGENDARY, 800, "def", 20, "+20 防御"),
    ]
    
    SKILLS = [
        ("fireball", "火球术", ItemRarity.RARE, 300, "skill_damage", 50, "造成 50 伤害"),
        ("heal", "治疗术", ItemRarity.RARE, 250, "skill_heal", 30, "恢复 30 HP"),
        ("shield", "护盾", ItemRarity.RARE, 200, "skill_shield", 20, "获得 20 临时防御"),
    ]
    
    def __init__(self, rng: RNG):
        self.rng = rng
    
    def generate_shop_inventory(
        self,
        chapter_index: int = 0,
        base_gold: int = 100
    ) -> ShopInventory:
        """
        Generate shop inventory for a chapter.
        
        Args:
            chapter_index: Current chapter (affects prices/items)
            base_gold: Expected gold at this point
            
        Returns:
            ShopInventory with items
        """
        # Price scaling
        price_multiplier = 1.0 + (chapter_index * 0.15)
        
        # Item pool based on chapter
        item_pool = []
        
        # Always add consumables
        for item_id, name, rarity, base_price, effect, value, desc in self.CONSUMABLES:
            item_pool.append(Item(
                item_id=f"{item_id}_{chapter_index}",
                name=name,
                item_type=ItemType.CONSUMABLE,
                rarity=rarity,
                price=int(base_price * price_multiplier),
                effect=effect,
                value=value,
                description=desc,
            ))
        
        # Add equipment based on chapter
        if chapter_index >= 1:
            for item_id, name, rarity, base_price, effect, value, desc in self.WEAPONS[:2]:
                item_pool.append(Item(
                    item_id=f"{item_id}_{chapter_index}",
                    name=name,
                    item_type=ItemType.WEAPON,
                    rarity=rarity,
                    price=int(base_price * price_multiplier),
                    effect=effect,
                    value=value,
                    description=desc,
                ))
        
        if chapter_index >= 2:
            for item_id, name, rarity, base_price, effect, value, desc in self.WEAPONS[2:]:
                item_pool.append(Item(
                    item_id=f"{item_id}_{chapter_index}",
                    name=name,
                    item_type=ItemType.WEAPON,
                    rarity=rarity,
                    price=int(base_price * price_multiplier),
                    effect=effect,
                    value=value,
                    description=desc,
                ))
            
            for item_id, name, rarity, base_price, effect, value, desc in self.ARMOR[:2]:
                item_pool.append(Item(
                    item_id=f"{item_id}_{chapter_index}",
                    name=name,
                    item_type=ItemType.ARMOR,
                    rarity=rarity,
                    price=int(base_price * price_multiplier),
                    effect=effect,
                    value=value,
                    description=desc,
                ))
        
        if chapter_index >= 3:
            for item_id, name, rarity, base_price, effect, value, desc in self.ARMOR[2:]:
                item_pool.append(Item(
                    item_id=f"{item_id}_{chapter_index}",
                    name=name,
                    item_type=ItemType.ARMOR,
                    rarity=rarity,
                    price=int(base_price * price_multiplier),
                    effect=effect,
                    value=value,
                    description=desc,
                ))
            
            for item_id, name, rarity, base_price, effect, value, desc in self.SKILLS:
                item_pool.append(Item(
                    item_id=f"{item_id}_{chapter_index}",
                    name=name,
                    item_type=ItemType.SKILL,
                    rarity=rarity,
                    price=int(base_price * price_multiplier),
                    effect=effect,
                    value=value,
                    description=desc,
                ))
        
        # Select random items for this shop
        num_items = min(6 + chapter_index, len(item_pool))
        selected_items = self.rng.sample(item_pool, num_items)
        
        return ShopInventory(items=selected_items)
    
    def purchase_item(
        self,
        shop: ShopInventory,
        inventory: PlayerInventory,
        item_id: str
    ) -> tuple:
        """
        Attempt to purchase an item.
        
        Returns:
            (success: bool, events: List[GameEvent])
        """
        events = []
        
        # Find item in shop
        item = None
        for shop_item in shop.items:
            if shop_item.item_id == item_id:
                item = shop_item
                break
        
        if not item:
            events.append(GameEvent(
                type=EventType.ERROR,
                data={"message": f"Item {item_id} not found in shop"}
            ))
            return False, events
        
        # Check gold
        if inventory.gold < item.price:
            events.append(GameEvent(
                type=EventType.ERROR,
                data={
                    "message": f"Not enough gold! Need {item.price}, have {inventory.gold}"
                }
            ))
            return False, events
        
        # Check inventory space
        if len(inventory.items) >= inventory.max_items:
            events.append(GameEvent(
                type=EventType.ERROR,
                data={"message": "Inventory full!"}
            ))
            return False, events
        
        # Purchase
        inventory.gold -= item.price
        inventory.add_item(item)
        
        # Events
        events.append(GameEvent(
            type=EventType.ITEM_PURCHASED,
            data={
                "item_id": item.item_id,
                "item_name": item.name,
                "item_type": item.item_type.value,
                "rarity": item.rarity.value,
                "price": item.price,
                "remaining_gold": inventory.gold,
            }
        ))
        
        events.append(GameEvent(
            type=EventType.GOLD_SPENT,
            data={
                "amount": item.price,
                "reason": f"purchased {item.name}",
                "remaining": inventory.gold,
            }
        ))
        
        events.append(GameEvent(
            type=EventType.ITEM_PICKED_UP,
            data={
                "item_id": item.item_id,
                "item_name": item.name,
                "inventory_count": len(inventory.items),
            }
        ))
        
        return True, events
    
    def sell_item(
        self,
        inventory: PlayerInventory,
        item_id: str
    ) -> tuple:
        """
        Sell an item from inventory.
        
        Returns:
            (success: bool, events: List[GameEvent])
        """
        events = []
        
        # Find item in inventory
        item = inventory.remove_item(item_id)
        
        if not item:
            events.append(GameEvent(
                type=EventType.ERROR,
                data={"message": f"Item {item_id} not found in inventory"}
            ))
            return False, events
        
        # Calculate sell price (50% of original)
        sell_price = item.price // 2
        inventory.gold += sell_price
        
        events.append(GameEvent(
            type=EventType.ITEM_SOLD,
            data={
                "item_id": item.item_id,
                "item_name": item.name,
                "sell_price": sell_price,
                "remaining_gold": inventory.gold,
            }
        ))
        
        return True, events
    
    def use_item(
        self,
        inventory: PlayerInventory,
        item_id: str,
        player_state
    ) -> tuple:
        """
        Use an item from inventory.
        
        Returns:
            (success: bool, events: List[GameEvent])
        """
        events = []
        
        # Find item in inventory
        item = inventory.remove_item(item_id)
        
        if not item:
            events.append(GameEvent(
                type=EventType.ERROR,
                data={"message": f"Item {item_id} not found"}
            ))
            return False, events
        
        # Apply effect
        if item.effect == "heal_hp":
            old_hp = player_state.current_hp
            player_state.current_hp = min(
                player_state.stats.hp.value,
                player_state.current_hp + item.value
            )
            healed = player_state.current_hp - old_hp
            events.append(GameEvent(
                type=EventType.STATUS_APPLIED,
                data={
                    "target": "player",
                    "status": "healed",
                    "amount": healed,
                }
            ))
        
        elif item.effect == "heal_mp":
            old_mp = player_state.current_mp
            player_state.current_mp = min(
                player_state.stats.mp.value,
                player_state.current_mp + item.value
            )
            events.append(GameEvent(
                type=EventType.STATUS_APPLIED,
                data={
                    "target": "player",
                    "status": "mana_restored",
                    "amount": item.value,
                }
            ))
        
        elif item.effect == "heal_all":
            player_state.current_hp = min(
                player_state.stats.hp.value,
                player_state.current_hp + item.value
            )
            player_state.current_mp = min(
                player_state.stats.mp.value,
                player_state.current_mp + item.value
            )
            events.append(GameEvent(
                type=EventType.STATUS_APPLIED,
                data={
                    "target": "player",
                    "status": "fully_restored",
                    "amount": item.value,
                }
            ))
        
        elif item.effect == "atk":
            player_state.stats.attack.add_modifier(item.value)
            events.append(GameEvent(
                type=EventType.STAT_CHANGED,
                data={
                    "stat": "attack",
                    "change": item.value,
                    "new_value": player_state.stats.attack.value,
                }
            ))
        
        elif item.effect == "def":
            player_state.stats.defense.add_modifier(item.value)
            events.append(GameEvent(
                type=EventType.STAT_CHANGED,
                data={
                    "stat": "defense",
                    "change": item.value,
                    "new_value": player_state.stats.defense.value,
                }
            ))
        
        else:
            events.append(GameEvent(
                type=EventType.WARNING,
                data={"message": f"Unknown effect: {item.effect}"}
            ))
        
        events.append(GameEvent(
            type=EventType.ITEM_CONSUMED,
            data={
                "item_id": item.item_id,
                "item_name": item.name,
                "effect": item.effect,
            }
        ))
        
        return True, events
    
    def render_shop_menu(
        self,
        shop: ShopInventory,
        inventory: PlayerInventory
    ) -> str:
        """Render shop menu as string."""
        lines = [
            "",
            "=" * 40,
            "🏪 商店 / SHOP",
            "=" * 40,
            f"💰 金币: {inventory.gold}",
            "-" * 40,
            "",
        ]
        
        for i, item in enumerate(shop.items, 1):
            rarity_icons = {
                ItemRarity.COMMON: "⚪",
                ItemRarity.RARE: "🔵",
                ItemRarity.EPIC: "🟣",
                ItemRarity.LEGENDARY: "🟡",
            }
            icon = rarity_icons.get(item.rarity, "⚪")
            
            type_icons = {
                ItemType.CONSUMABLE: "🧪",
                ItemType.WEAPON: "⚔️",
                ItemType.ARMOR: "🛡️",
                ItemType.SKILL: "✨",
                ItemType.ACCESSORY: "💍",
            }
            type_icon = type_icons.get(item.item_type, "📦")
            
            lines.append(f"  [{i}] {icon}{type_icon} {item.name}")
            lines.append(f"      {item.description}")
            lines.append(f"      💰 {item.price} 金币")
            lines.append("")
        
        lines.extend([
            "-" * 40,
            "💼 背包 ({}/{} items)".format(len(inventory.items), inventory.max_items),
            f"💰 金币: {inventory.gold}",
            "",
            "[0] 离开商店",
            "=" * 40,
        ])
        
        return "\n".join(lines)
    
    def render_inventory_menu(
        self,
        inventory: PlayerInventory
    ) -> str:
        """Render inventory menu as string."""
        lines = [
            "",
            "=" * 40,
            "💼 背包 / INVENTORY",
            "=" * 40,
            f"💰 金币: {inventory.gold}",
            f"📦 物品: {len(inventory.items)}/{inventory.max_items}",
            "-" * 40,
            "",
        ]
        
        if not inventory.items:
            lines.append("  (背包为空)")
        else:
            for i, item in enumerate(inventory.items, 1):
                rarity_icons = {
                    ItemRarity.COMMON: "⚪",
                    ItemRarity.RARE: "🔵",
                    ItemRarity.EPIC: "🟣",
                    ItemRarity.LEGENDARY: "🟡",
                }
                icon = rarity_icons.get(item.rarity, "⚪")
                
                type_icons = {
                    ItemType.CONSUMABLE: "🧪",
                    ItemType.WEAPON: "⚔️",
                    ItemType.ARMOR: "🛡️",
                    ItemType.SKILL: "✨",
                }
                type_icon = type_icons.get(item.item_type, "📦")
                
                sell_price = item.price // 2
                lines.append(f"  [{i}] {icon}{type_icon} {item.name}")
                lines.append(f"      💰 售价: {sell_price} 金币")
                lines.append("")
        
        lines.extend([
            "-" * 40,
            "[0] 返回",
            "[*] 出售物品 (输入编号)",
            "=" * 40,
        ])
        
        return "\n".join(lines)


# Export
__all__ = [
    "ItemType",
    "ItemRarity",
    "Item",
    "ShopInventory",
    "PlayerInventory",
    "ShopSystem",
]
