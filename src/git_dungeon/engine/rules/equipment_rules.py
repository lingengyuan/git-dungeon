# equipment_rules.py - Equipment system

"""
Equipment system for Git Dungeon.

Features:
- Equipment types (weapon, armor, accessory)
- Equipment stats and bonuses
- Equipment slots
- Equipment acquisition
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
import random

from git_dungeon.engine.rng import RNG, roll_chance


class EquipmentType(Enum):
    """Types of equipment."""
    WEAPON = "weapon"
    ARMOR = "armor"
    ACCESSORY = "accessory"


class EquipmentRarity(Enum):
    """Equipment rarity levels."""
    COMMON = "common"      # ⚪
    UNCOMMON = "uncommon"  # 🟢
    RARE = "rare"          # 🔵
    EPIC = "epic"          # 🟣
    LEGENDARY = "legendary"  # 🟡


class StatType(Enum):
    """Stat types that can be modified by equipment."""
    HP = "hp"
    MP = "mp"
    ATTACK = "attack"
    DEFENSE = "defense"
    SPEED = "speed"
    CRITICAL = "critical"
    EVASION = "evasion"
    LUCK = "luck"


@dataclass
class EquipmentStats:
    """Stats provided by equipment."""
    hp_bonus: int = 0
    mp_bonus: int = 0
    attack_bonus: int = 0
    defense_bonus: int = 0
    speed_bonus: int = 0
    critical_bonus: int = 0
    evasion_bonus: int = 0
    luck_bonus: int = 0
    
    def to_dict(self) -> Dict[str, int]:
        return {
            "hp": self.hp_bonus,
            "mp": self.mp_bonus,
            "attack": self.attack_bonus,
            "defense": self.defense_bonus,
            "speed": self.speed_bonus,
            "critical": self.critical_bonus,
            "evasion": self.evasion_bonus,
            "luck": self.luck_bonus,
        }
    
    def total_bonus(self) -> int:
        """Calculate total stat bonus."""
        return (self.hp_bonus + self.mp_bonus + self.attack_bonus +
                self.defense_bonus + self.speed_bonus + self.critical_bonus +
                self.evasion_bonus + self.luck_bonus)


@dataclass
class EquipmentSet:
    """A set of equipment that provides bonuses when complete."""
    set_id: str
    name: str
    pieces: List[str]  # Equipment IDs in the set
    bonuses: Dict[int, str]  # {piece_count: bonus_description}
    
    def get_bonus_description(self, owned_count: int) -> Optional[str]:
        """Get bonus description for number of pieces owned."""
        max_pieces = max(self.bonuses.keys())
        for count in range(max_pieces, 0, -1):
            if owned_count >= count:
                return self.bonuses[count]
        return None


@dataclass
class Equipment:
    """An equipment item."""
    equipment_id: str
    name: str
    equipment_type: EquipmentType
    rarity: EquipmentRarity
    level_required: int
    stats: EquipmentStats
    description: str = ""
    set_id: Optional[str] = None
    
    # Price
    base_price: int = 100
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "equipment_id": self.equipment_id,
            "name": self.name,
            "type": self.equipment_type.value,
            "rarity": self.rarity.value,
            "level_required": self.level_required,
            "stats": self.stats.to_dict(),
            "description": self.description,
            "set_id": self.set_id,
            "base_price": self.base_price,
        }
    
    @property
    def rarity_multiplier(self) -> float:
        """Get price/stats multiplier based on rarity."""
        multipliers = {
            EquipmentRarity.COMMON: 1.0,
            EquipmentRarity.UNCOMMON: 1.5,
            EquipmentRarity.RARE: 2.5,
            EquipmentRarity.EPIC: 4.0,
            EquipmentRarity.LEGENDARY: 8.0,
        }
        return multipliers.get(self.rarity, 1.0)
    
    @property
    def rarity_icon(self) -> str:
        """Get icon for rarity."""
        icons = {
            EquipmentRarity.COMMON: "⚪",
            EquipmentRarity.UNCOMMON: "🟢",
            EquipmentRarity.RARE: "🔵",
            EquipmentRarity.EPIC: "🟣",
            EquipmentRarity.LEGENDARY: "🟡",
        }
        return icons.get(self.rarity, "⚪")
    
    @property
    def type_icon(self) -> str:
        """Get icon for equipment type."""
        icons = {
            EquipmentType.WEAPON: "⚔️",
            EquipmentType.ARMOR: "🛡️",
            EquipmentType.ACCESSORY: "💍",
        }
        return icons.get(self.equipment_type, "📦")


@dataclass
class PlayerEquipment:
    """Player's equipment inventory."""
    weapon: Optional[Equipment] = None
    armor: Optional[Equipment] = None
    accessory: Optional[Equipment] = None
    
    def get_equipment_by_type(self, eq_type: EquipmentType) -> Optional[Equipment]:
        """Get equipment by type."""
        if eq_type == EquipmentType.WEAPON:
            return self.weapon
        elif eq_type == EquipmentType.ARMOR:
            return self.armor
        elif eq_type == EquipmentType.ACCESSORY:
            return self.accessory
        return None
    
    def set_equipment(self, equipment: Equipment) -> Optional[Equipment]:
        """Equip an item, return old item if replaced."""
        old_item = None
        
        if equipment.equipment_type == EquipmentType.WEAPON:
            old_item = self.weapon
            self.weapon = equipment
        elif equipment.equipment_type == EquipmentType.ARMOR:
            old_item = self.armor
            self.armor = equipment
        elif equipment.equipment_type == EquipmentType.ACCESSORY:
            old_item = self.accessory
            self.accessory = equipment
        
        return old_item
    
    def unequip(self, eq_type: EquipmentType) -> Optional[Equipment]:
        """Unequip an item."""
        item = None
        
        if eq_type == EquipmentType.WEAPON:
            item = self.weapon
            self.weapon = None
        elif eq_type == EquipmentType.ARMOR:
            item = self.armor
            self.armor = None
        elif eq_type == EquipmentType.ACCESSORY:
            item = self.accessory
            self.accessory = None
        
        return item
    
    def get_total_stats(self) -> EquipmentStats:
        """Calculate total stats from all equipped items."""
        total = EquipmentStats()
        
        for equipment in [self.weapon, self.armor, self.accessory]:
            if equipment:
                total.hp_bonus += equipment.stats.hp_bonus
                total.mp_bonus += equipment.stats.mp_bonus
                total.attack_bonus += equipment.stats.attack_bonus
                total.defense_bonus += equipment.stats.defense_bonus
                total.speed_bonus += equipment.stats.speed_bonus
                total.critical_bonus += equipment.stats.critical_bonus
                total.evasion_bonus += equipment.stats.evasion_bonus
                total.luck_bonus += equipment.stats.luck_bonus
        
        return total
    
    def get_equipped_items(self) -> List[Equipment]:
        """Get list of all equipped items."""
        items = []
        if self.weapon:
            items.append(self.weapon)
        if self.armor:
            items.append(self.armor)
        if self.accessory:
            items.append(self.accessory)
        return items
    
    def is_equipped(self, equipment_id: str) -> bool:
        """Check if an equipment is equipped."""
        return any(e and e.equipment_id == equipment_id for e in 
                   [self.weapon, self.armor, self.accessory])


class EquipmentSystem:
    """
    Manages equipment creation and acquisition.
    
    Features:
    - Generate equipment
    - Equipment rarities
    - Equipment drops
    - Equipment shop
    """
    
    # Equipment templates
    WEAPON_TEMPLATES = [
        ("dagger", "匕首", 5, 8, 1, EquipmentRarity.COMMON),
        ("short_sword", "短剑", 8, 12, 3, EquipmentRarity.COMMON),
        ("longsword", "长剑", 12, 18, 5, EquipmentRarity.UNCOMMON),
        ("broadsword", "阔剑", 18, 25, 8, EquipmentRarity.UNCOMMON),
        ("rapier", "细剑", 22, 30, 10, EquipmentRarity.RARE),
        ("katana", "武士刀", 28, 38, 12, EquipmentRarity.RARE),
        ("flame_blade", "烈焰之刃", 35, 50, 15, EquipmentRarity.EPIC),
        ("thunder_axe", "雷霆战斧", 42, 60, 18, EquipmentRarity.EPIC),
        ("dragon_slayer", "屠龙剑", 55, 80, 22, EquipmentRarity.LEGENDARY),
        ("godslayer", "弑神刀", 70, 100, 25, EquipmentRarity.LEGENDARY),
    ]
    
    ARMOR_TEMPLATES = [
        ("leather_armor", "皮甲", 3, 5, 1, EquipmentRarity.COMMON),
        ("studded_armor", "钉甲", 5, 8, 3, EquipmentRarity.COMMON),
        ("chain_mail", "锁甲", 8, 12, 5, EquipmentRarity.UNCOMMON),
        ("scale_mail", "鳞甲", 12, 18, 8, EquipmentRarity.UNCOMMON),
        ("plate_mail", "板甲", 18, 25, 10, EquipmentRarity.RARE),
        ("knight_armor", "骑士甲", 25, 35, 12, EquipmentRarity.RARE),
        ("dragon_scale", "龙鳞甲", 35, 50, 15, EquipmentRarity.EPIC),
        ("holy_plate", "神圣板甲", 45, 65, 18, EquipmentRarity.EPIC),
        ("god_armor", "神甲", 60, 90, 22, EquipmentRarity.LEGENDARY),
        ("divine_robe", "神圣法袍", 80, 100, 25, EquipmentRarity.LEGENDARY),
    ]
    
    ACCESSORY_TEMPLATES = [
        ("ring", "戒指", 1, 3, 1, EquipmentRarity.COMMON),
        ("necklace", "项链", 2, 4, 2, EquipmentRarity.COMMON),
        ("belt", "腰带", 2, 5, 3, EquipmentRarity.COMMON),
        ("bracelet", "手镯", 3, 6, 4, EquipmentRarity.UNCOMMON),
        ("charm", "护身符", 4, 8, 5, EquipmentRarity.UNCOMMON),
        ("amulet", "护符", 5, 10, 7, EquipmentRarity.RARE),
        ("talisman", "法珠", 8, 15, 10, EquipmentRarity.RARE),
        ("relic", "圣遗物", 12, 20, 12, EquipmentRarity.EPIC),
        ("artifact", "神器", 18, 30, 15, EquipmentRarity.LEGENDARY),
        ("god_tear", "神之泪", 25, 50, 20, EquipmentRarity.LEGENDARY),
    ]
    
    def __init__(self, rng: RNG):
        self.rng = rng
    
    def generate_weapon(
        self,
        chapter_index: int = 0,
        level_bonus: int = 0
    ) -> Equipment:
        """Generate a random weapon."""
        template = self.rng.choice(self.WEAPON_TEMPLATES)
        return self._create_equipment(template, EquipmentType.WEAPON, chapter_index, level_bonus)
    
    def generate_armor(
        self,
        chapter_index: int = 0,
        level_bonus: int = 0
    ) -> Equipment:
        """Generate a random armor."""
        template = self.rng.choice(self.ARMOR_TEMPLATES)
        return self._create_equipment(template, EquipmentType.ARMOR, chapter_index, level_bonus)
    
    def generate_accessory(
        self,
        chapter_index: int = 0,
        level_bonus: int = 0
    ) -> Equipment:
        """Generate a random accessory."""
        template = self.rng.choice(self.ACCESSORY_TEMPLATES)
        return self._create_equipment(template, EquipmentType.ACCESSORY, chapter_index, level_bonus)
    
    def _create_equipment(
        self,
        template: tuple,
        eq_type: EquipmentType,
        chapter_index: int,
        level_bonus: int = 0
    ) -> Equipment:
        """Create equipment from template."""
        eq_id, name, base_atk, base_def, base_level, rarity = template
        
        # Scale by chapter
        scale = 1.0 + (chapter_index * 0.1) + (level_bonus * 0.05)
        
        # Random variance using random()
        variance = 0.9 + self.rng.random() * 0.2  # Range [0.9, 1.1)
        
        stats = EquipmentStats()
        
        if eq_type == EquipmentType.WEAPON:
            stats.attack_bonus = int(base_atk * scale * variance)
            stats.defense_bonus = int(base_def * scale * variance)
        elif eq_type == EquipmentType.ARMOR:
            stats.attack_bonus = int(base_atk * scale * variance)
            stats.defense_bonus = int(base_def * scale * variance)
        else:
            # Accessories - random stat distribution
            stat_bonus = int(base_atk * scale * variance)
            stat_type = self.rng.choice(list(StatType))
            setattr(stats, f"{stat_type.value}_bonus", stat_bonus)
        
        # Calculate level requirement
        level_required = int(base_level + (chapter_index * 0.5))
        
        # Calculate price
        base_price = (stats.total_bonus() * 10 + level_required * 5)
        
        return Equipment(
            equipment_id=f"{eq_id}_{chapter_index}_{random.randint(1000, 9999)}",
            name=name,
            equipment_type=eq_type,
            rarity=rarity,
            level_required=level_required,
            stats=stats,
            description=self._get_description(rarity, eq_type),
            base_price=base_price,
        )
    
    def _get_description(self, rarity: EquipmentRarity, eq_type: EquipmentType) -> str:
        """Generate equipment description."""
        type_name = {
            EquipmentType.WEAPON: "武器",
            EquipmentType.ARMOR: "防具",
            EquipmentType.ACCESSORY: "饰品",
        }.get(eq_type, "装备")
        
        rarity_desc = {
            EquipmentRarity.COMMON: "普通",
            EquipmentRarity.UNCOMMON: "优秀",
            EquipmentRarity.RARE: "稀有",
            EquipmentRarity.EPIC: "史诗",
            EquipmentRarity.LEGENDARY: "传说",
        }.get(rarity, "")
        
        return f"{rarity_desc} {type_name}"
    
    def generate_random_equipment(
        self,
        chapter_index: int = 0,
        level_bonus: int = 0
    ) -> Equipment:
        """Generate random equipment of any type."""
        eq_type = self.rng.choice(list(EquipmentType))
        
        if eq_type == EquipmentType.WEAPON:
            return self.generate_weapon(chapter_index, level_bonus)
        elif eq_type == EquipmentType.ARMOR:
            return self.generate_armor(chapter_index, level_bonus)
        else:
            return self.generate_accessory(chapter_index, level_bonus)
    
    def generate_equipment_for_enemy(
        self,
        enemy_level: int = 1,
        drop_chance: float = 0.2
    ) -> Optional[Equipment]:
        """
        Generate equipment as enemy drop.
        
        Args:
            enemy_level: Enemy level
            drop_chance: Chance to drop equipment
            
        Returns:
            Equipment or None
        """
        if not roll_chance(self.rng, drop_chance):
            return None
        
        # Higher chance for common/rare
        roll = self.rng.random()
        
        if roll < 0.5:
            rarity = EquipmentRarity.COMMON
        elif roll < 0.8:
            rarity = EquipmentRarity.UNCOMMON
        elif roll < 0.95:
            rarity = EquipmentRarity.RARE
        elif roll < 0.99:
            rarity = EquipmentRarity.EPIC
        else:
            rarity = EquipmentRarity.LEGENDARY
        
        eq_type = self.rng.choice(list(EquipmentType))
        
        if eq_type == EquipmentType.WEAPON:
            template = self.rng.choice(self.WEAPON_TEMPLATES)
        elif eq_type == EquipmentType.ARMOR:
            template = self.rng.choice(self.ARMOR_TEMPLATES)
        else:
            template = self.rng.choice(self.ACCESSORY_TEMPLATES)
        
        # Use enemy level as chapter index approximation
        chapter_index = max(0, enemy_level - 1)
        
        equipment = self._create_equipment(template, eq_type, chapter_index)
        equipment.rarity = rarity
        
        return equipment
    
    def render_equipment_menu(self, equipment: Equipment, index: int = 0) -> str:
        """Render equipment as a menu item."""
        lines = []
        
        if index > 0:
            lines.append(f"  [{index}] ", end="")
        else:
            lines.append("  • ")
        
        lines.append(f"{equipment.rarity_icon}{equipment.type_icon} {equipment.name}")
        lines.append(f"      Lv.{equipment.level_required} | {equipment.rarity.value}")
        
        # Stats
        stat_parts = []
        if equipment.stats.attack_bonus > 0:
            stat_parts.append(f"ATK+{equipment.stats.attack_bonus}")
        if equipment.stats.defense_bonus > 0:
            stat_parts.append(f"DEF+{equipment.stats.defense_bonus}")
        if equipment.stats.hp_bonus > 0:
            stat_parts.append(f"HP+{equipment.stats.hp_bonus}")
        if equipment.stats.critical_bonus > 0:
            stat_parts.append(f"CRIT+{equipment.stats.critical_bonus}")
        if equipment.stats.evasion_bonus > 0:
            stat_parts.append(f"EVADE+{equipment.stats.evasion_bonus}")
        
        if stat_parts:
            lines.append(f"      {', '.join(stat_parts)}")
        
        lines.append(f"      💰 {equipment.base_price} Gold")
        
        return "\n".join(lines)
    
    def render_equipment_panel(self, equipment: PlayerEquipment) -> str:
        """Render equipment panel."""
        lines = [
            "",
            "=" * 40,
            "🎽 装备 / EQUIPMENT",
            "=" * 40,
            "",
        ]
        
        # Weapon
        if equipment.weapon:
            eq = equipment.weapon
            lines.append(f"⚔️  武器: {eq.rarity_icon} {eq.name}")
            lines.append(f"      ATK+{eq.stats.attack_bonus} | Lv.{eq.level_required}")
        else:
            lines.append("⚔️  武器: (未装备)")
        
        # Armor
        if equipment.armor:
            eq = equipment.armor
            lines.append(f"🛡️  防具: {eq.rarity_icon} {eq.name}")
            lines.append(f"      DEF+{eq.stats.defense_bonus} | Lv.{eq.level_required}")
        else:
            lines.append("🛡️  防具: (未装备)")
        
        # Accessory
        if equipment.accessory:
            eq = equipment.accessory
            lines.append(f"💍  饰品: {eq.rarity_icon} {eq.name}")
            stat_bonus = (eq.stats.critical_bonus or eq.stats.evasion_bonus or 
                         eq.stats.luck_bonus or eq.stats.speed_bonus)
            if stat_bonus:
                lines.append(f"      +{stat_bonus} | Lv.{eq.level_required}")
        else:
            lines.append("💍  饰品: (未装备)")
        
        # Total bonus
        total = equipment.get_total_stats()
        lines.extend([
            "",
            "📊 属性加成:",
            f"   ATK: +{total.attack_bonus}  DEF: +{total.defense_bonus}",
            f"   HP: +{total.hp_bonus}  MP: +{total.mp_bonus}",
            "",
            "=" * 40,
        ])
        
        return "\n".join(lines)


# Export
__all__ = [
    "EquipmentType",
    "EquipmentRarity",
    "StatType",
    "EquipmentStats",
    "EquipmentSet",
    "Equipment",
    "PlayerEquipment",
    "EquipmentSystem",
]
