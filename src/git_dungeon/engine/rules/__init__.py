# __init__.py - Rules package

from .combat_rules import CombatRules
from .progression_rules import ProgressionRules
from .chapter_rules import (
    ChapterType, ChapterConfig, CHAPTER_CONFIGS,
    Chapter, ChapterSystem, build_chapter_configs, get_chapter_config
)
from .economy_rules import (
    ItemType, ItemRarity, Item,
    ShopInventory, PlayerInventory, ShopSystem
)
from .boss_rules import (
    BossPhase, BossAbilityType, BossAIType,
    BossAbility, BossPhaseData, BossTemplate,
    BossState, BossSystem
)
from .equipment_rules import (
    EquipmentType, EquipmentRarity, StatType,
    EquipmentStats, EquipmentSet, Equipment,
    PlayerEquipment, EquipmentSystem
)
from .skill_rules import (
    SkillType, SkillTarget, DamageType,
    SkillEffect, Skill, SkillCategory,
    SkillTree, SkillSystem
)

__all__ = [
    "CombatRules",
    "ProgressionRules",
    # Chapter
    "ChapterType",
    "ChapterConfig",
    "CHAPTER_CONFIGS",
    "Chapter",
    "ChapterSystem",
    "build_chapter_configs",
    "get_chapter_config",
    # Economy
    "ItemType",
    "ItemRarity",
    "Item",
    "ShopInventory",
    "PlayerInventory",
    "ShopSystem",
    # Boss
    "BossPhase",
    "BossAbilityType",
    "BossAIType",
    "BossAbility",
    "BossPhaseData",
    "BossTemplate",
    "BossState",
    "BossSystem",
    # Equipment
    "EquipmentType",
    "EquipmentRarity",
    "StatType",
    "EquipmentStats",
    "EquipmentSet",
    "Equipment",
    "PlayerEquipment",
    "EquipmentSystem",
    # Skills
    "SkillType",
    "SkillTarget",
    "DamageType",
    "SkillEffect",
    "Skill",
    "SkillCategory",
    "SkillTree",
    "SkillSystem",
]
