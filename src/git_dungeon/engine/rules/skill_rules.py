# skill_rules.py - Skill system

"""
Skill system for Git Dungeon.

Features:
- Active skills (fireball, heal, shield, etc.)
- Passive skills (stat bonuses)
- Skill mastery
- Skill tree
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

from git_dungeon.engine.rng import RNG


class SkillType(Enum):
    """Types of skills."""
    ACTIVE = "active"
    PASSIVE = "passive"
    ULTIMATE = "ultimate"


class SkillTarget(Enum):
    """Skill target types."""
    SELF = "self"
    ENEMY = "enemy"
    ALL_ENEMIES = "all_enemies"
    ALL_ALLIES = "all_allies"


class DamageType(Enum):
    """Damage types for skills."""
    PHYSICAL = "physical"
    MAGICAL = "magical"
    TRUE = "true"
    HEALING = "healing"


@dataclass
class SkillEffect:
    """An effect applied by a skill."""
    effect_type: str  # "damage", "heal", "buff", "debuff"
    value: int
    damage_type: DamageType = DamageType.PHYSICAL
    duration: int = 0  # 0 = instant
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "effect_type": self.effect_type,
            "value": self.value,
            "damage_type": self.damage_type.value,
            "duration": self.duration,
            "description": self.description,
        }


@dataclass
class Skill:
    """A skill that can be used in combat."""
    skill_id: str
    name: str
    skill_type: SkillType
    target: SkillTarget
    mana_cost: int
    cooldown: int
    current_cooldown: int = 0
    description: str = ""
    effects: List[SkillEffect] = field(default_factory=list)
    
    # Requirements
    level_required: int = 1
    character_class: Optional[str] = None
    
    # Mastery
    mastery_level: int = 0
    max_mastery: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "type": self.skill_type.value,
            "target": self.target.value,
            "mana_cost": self.mana_cost,
            "cooldown": self.cooldown,
            "description": self.description,
            "effects": [e.to_dict() for e in self.effects],
            "level_required": self.level_required,
            "mastery_level": self.mastery_level,
        }
    
    @property
    def is_ready(self) -> bool:
        """Check if skill is ready to use."""
        return self.current_cooldown <= 0
    
    @property
    def mastery_bonus(self) -> float:
        """Get multiplier based on mastery level."""
        return 1.0 + (self.mastery_level * 0.1)
    
    def use(self) -> bool:
        """Use skill (returns True if successful)."""
        if self.is_ready:
            self.current_cooldown = self.cooldown
            return True
        return False
    
    def tick(self):
        """Reduce cooldown."""
        if self.current_cooldown > 0:
            self.current_cooldown -= 1


@dataclass
class SkillCategory:
    """Category of skills (e.g., Fire, Ice, Support)."""
    category_id: str
    name: str
    icon: str = "✨"
    description: str = ""
    skills: List[str] = field(default_factory=list)  # Skill IDs
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category_id": self.category_id,
            "name": self.name,
            "icon": self.icon,
            "description": self.description,
            "skills": self.skills,
        }


@dataclass
class SkillTree:
    """A skill tree containing categorized skills."""
    tree_id: str
    name: str
    description: str = ""
    categories: List[SkillCategory] = field(default_factory=list)
    total_skill_points: int = 0
    available_skill_points: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tree_id": self.tree_id,
            "name": self.name,
            "description": self.description,
            "categories": [c.to_dict() for c in self.categories],
            "total_skill_points": self.total_skill_points,
            "available_skill_points": self.available_skill_points,
        }
    
    def get_category(self, category_id: str) -> Optional[SkillCategory]:
        """Get category by ID."""
        for cat in self.categories:
            if cat.category_id == category_id:
                return cat
        return None


class SkillSystem:
    """
    Manages skills, skill trees, and skill execution.
    
    Features:
    - Skill templates
    - Skill execution
    - Mastery system
    - Skill point acquisition
    """
    
    # Pre-defined skill templates
    SKILL_TEMPLATES = {
        # Fire skills
        "fireball": Skill(
            skill_id="fireball",
            name="火球术",
            skill_type=SkillType.ACTIVE,
            target=SkillTarget.ENEMY,
            mana_cost=20,
            cooldown=3,
            description="向敌人发射火球，造成魔法伤害",
            effects=[
                SkillEffect(
                    effect_type="damage",
                    value=50,
                    damage_type=DamageType.MAGICAL,
                    description="造成 {value} 魔法伤害"
                )
            ],
            level_required=5,
        ),
        "inferno": Skill(
            skill_id="inferno",
            name="烈焰风暴",
            skill_type=SkillType.ACTIVE,
            target=SkillTarget.ALL_ENEMIES,
            mana_cost=40,
            cooldown=5,
            description="对所有敌人造成火焰伤害",
            effects=[
                SkillEffect(
                    effect_type="damage",
                    value=80,
                    damage_type=DamageType.MAGICAL,
                    description="所有敌人受到 {value} 伤害"
                )
            ],
            level_required=15,
        ),
        
        # Ice skills
        "ice_bolt": Skill(
            skill_id="ice_bolt",
            name="冰霜箭",
            skill_type=SkillType.ACTIVE,
            target=SkillTarget.ENEMY,
            mana_cost=15,
            cooldown=2,
            description="发射冰霜箭，造成伤害并减速敌人",
            effects=[
                SkillEffect(
                    effect_type="damage",
                    value=30,
                    damage_type=DamageType.MAGICAL,
                    description="造成 {value} 魔法伤害"
                ),
                SkillEffect(
                    effect_type="debuff",
                    value=10,
                    description="降低敌人 10% 速度"
                )
            ],
            level_required=3,
        ),
        "blizzard": Skill(
            skill_id="blizzard",
            name="暴风雪",
            skill_type=SkillType.ACTIVE,
            target=SkillTarget.ALL_ENEMIES,
            mana_cost=35,
            cooldown=4,
            description="召唤暴风雪，冰冻所有敌人",
            effects=[
                SkillEffect(
                    effect_type="damage",
                    value=60,
                    damage_type=DamageType.MAGICAL,
                    description="所有敌人受到 {value} 伤害"
                ),
                SkillEffect(
                    effect_type="debuff",
                    value=20,
                    description="降低敌人 20% 速度"
                )
            ],
            level_required=12,
        ),
        
        # Healing skills
        "heal": Skill(
            skill_id="heal",
            name="治疗术",
            skill_type=SkillType.ACTIVE,
            target=SkillTarget.SELF,
            mana_cost=25,
            cooldown=4,
            description="恢复自身生命值",
            effects=[
                SkillEffect(
                    effect_type="heal",
                    value=60,
                    damage_type=DamageType.HEALING,
                    description="恢复 {value} HP"
                )
            ],
            level_required=5,
        ),
        "group_heal": Skill(
            skill_id="group_heal",
            name="群体治疗",
            skill_type=SkillType.ACTIVE,
            target=SkillTarget.ALL_ALLIES,
            mana_cost=45,
            cooldown=6,
            description="恢复全体友军生命值",
            effects=[
                SkillEffect(
                    effect_type="heal",
                    value=40,
                    damage_type=DamageType.HEALING,
                    description="所有友军恢复 {value} HP"
                )
            ],
            level_required=15,
        ),
        
        # Support skills
        "shield": Skill(
            skill_id="shield",
            name="护盾",
            skill_type=SkillType.ACTIVE,
            target=SkillTarget.SELF,
            mana_cost=15,
            cooldown=3,
            description="为自己施加护盾，临时增加防御",
            effects=[
                SkillEffect(
                    effect_type="buff",
                    value=20,
                    description="获得 {value} 临时防御"
                )
            ],
            level_required=3,
        ),
        "haste": Skill(
            skill_id="haste",
            name="加速",
            skill_type=SkillType.ACTIVE,
            target=SkillTarget.SELF,
            mana_cost=20,
            cooldown=4,
            description="加速，提升攻击速度",
            effects=[
                SkillEffect(
                    effect_type="buff",
                    value=30,
                    description="提升 {value}% 攻击速度"
                )
            ],
            level_required=8,
        ),
        
        # Ultimate skills
        "meteor": Skill(
            skill_id="meteor",
            name="陨石术",
            skill_type=SkillType.ULTIMATE,
            target=SkillTarget.ALL_ENEMIES,
            mana_cost=100,
            cooldown=10,
            description="召唤陨石，对所有敌人造成巨额伤害",
            effects=[
                SkillEffect(
                    effect_type="damage",
                    value=200,
                    damage_type=DamageType.MAGICAL,
                    description="所有敌人受到 {value} 伤害"
                )
            ],
            level_required=25,
        ),
        "divine_blade": Skill(
            skill_id="divine_blade",
            name="神圣剑刃",
            skill_type=SkillType.ULTIMATE,
            target=SkillTarget.ENEMY,
            mana_cost=80,
            cooldown=8,
            description="召唤神圣之剑，对单体敌人造成巨大伤害",
            effects=[
                SkillEffect(
                    effect_type="damage",
                    value=300,
                    damage_type=DamageType.TRUE,
                    description="造成 {value} 真实伤害"
                )
            ],
            level_required=30,
        ),
        
        # Passive skills
        "powerStrike": Skill(
            skill_id="powerStrike",
            name="力量打击",
            skill_type=SkillType.PASSIVE,
            target=SkillTarget.SELF,
            mana_cost=0,
            cooldown=0,
            description="被动增加攻击力",
            effects=[
                SkillEffect(
                    effect_type="buff",
                    value=5,
                    description="永久 +5 攻击力"
                )
            ],
            level_required=1,
        ),
        "toughness": Skill(
            skill_id="toughness",
            name="坚韧",
            skill_type=SkillType.PASSIVE,
            target=SkillTarget.SELF,
            mana_cost=0,
            cooldown=0,
            description="被动增加防御力",
            effects=[
                SkillEffect(
                    effect_type="buff",
                    value=3,
                    description="永久 +3 防御力"
                )
            ],
            level_required=1,
        ),
        "critical_mind": Skill(
            skill_id="critical_mind",
            name="暴击之心",
            skill_type=SkillType.PASSIVE,
            target=SkillTarget.SELF,
            mana_cost=0,
            cooldown=0,
            description="被动增加暴击率",
            effects=[
                SkillEffect(
                    effect_type="buff",
                    value=5,
                    description="永久 +5% 暴击率"
                )
            ],
            level_required=5,
        ),
    }
    
    def __init__(self, rng: RNG):
        self.rng = rng
    
    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """Get skill by ID."""
        template = self.SKILL_TEMPLATES.get(skill_id)
        if template:
            # Return a copy
            return Skill(
                skill_id=template.skill_id,
                name=template.name,
                skill_type=template.skill_type,
                target=template.target,
                mana_cost=template.mana_cost,
                cooldown=template.cooldown,
                description=template.description,
                effects=template.effects.copy(),
                level_required=template.level_required,
            )
        return None
    
    def get_skills_by_type(self, skill_type: SkillType) -> List[Skill]:
        """Get all skills of a type."""
        skills = []
        for template in self.SKILL_TEMPLATES.values():
            if template.skill_type == skill_type:
                skills.append(self.get_skill(template.skill_id))
        return skills
    
    def get_skill_tree(self) -> SkillTree:
        """Get default skill tree."""
        tree = SkillTree(
            tree_id="default",
            name="技能树",
            description="学习和升级你的技能",
        )
        
        # Fire category
        fire = SkillCategory(
            category_id="fire",
            name="火焰",
            icon="🔥",
            description="火焰系技能",
            skills=["fireball", "inferno"],
        )
        
        # Ice category
        ice = SkillCategory(
            category_id="ice",
            name="冰霜",
            icon="❄️",
            description="冰霜系技能",
            skills=["ice_bolt", "blizzard"],
        )
        
        # Healing category
        healing = SkillCategory(
            category_id="healing",
            name="治疗",
            icon="💚",
            description="治疗系技能",
            skills=["heal", "group_heal"],
        )
        
        # Support category
        support = SkillCategory(
            category_id="support",
            name="辅助",
            icon="✨",
            description="辅助系技能",
            skills=["shield", "haste"],
        )
        
        # Ultimate category
        ultimate = SkillCategory(
            category_id="ultimate",
            name="终极",
            icon="🌟",
            description="终极技能",
            skills=["meteor", "divine_blade"],
        )
        
        # Passive category
        passive = SkillCategory(
            category_id="passive",
            name="被动",
            icon="📖",
            description="被动技能",
            skills=["powerStrike", "toughness", "critical_mind"],
        )
        
        tree.categories = [fire, ice, healing, support, ultimate, passive]
        return tree
    
    def can_use_skill(
        self,
        skill: Skill,
        player_mp: int,
        player_level: int
    ) -> tuple[bool, str]:
        """Check if skill can be used."""
        if not skill.is_ready:
            return False, f"技能冷却中 ({skill.current_cooldown} 回合)"
        
        if player_mp < skill.mana_cost:
            return False, f"法力不足 (需要 {skill.mana_cost}, 当前 {player_mp})"
        
        if player_level < skill.level_required:
            return False, f"等级不足 (需要 {skill.level_required}, 当前 {player_level})"
        
        return True, ""
    
    def execute_skill(
        self,
        skill: Skill,
        attacker_stats: Dict[str, int],
        defender_stats: Dict[str, int] = None
    ) -> Dict[str, Any]:
        """
        Execute a skill and return results.
        
        Returns:
            Dict with damage, healing, effects applied
        """
        if not skill.is_ready:
            return {"success": False, "reason": "Skill on cooldown"}
        
        # Calculate mastery bonus
        multiplier = skill.mastery_bonus
        
        # Calculate effects
        results = {
            "skill_id": skill.skill_id,
            "skill_name": skill.name,
            "success": True,
            "effects_applied": [],
            "total_damage": 0,
            "total_heal": 0,
        }
        
        for effect in skill.effects:
            effect_result = self._apply_effect(effect, attacker_stats, defender_stats, multiplier)
            results["effects_applied"].append(effect_result)
            
            if effect.effect_type == "damage":
                results["total_damage"] += effect_result["value"]
            elif effect.effect_type == "heal":
                results["total_heal"] += effect_result["value"]
        
        # Use skill (apply cooldown)
        skill.use()
        
        return results
    
    def _apply_effect(
        self,
        effect: SkillEffect,
        attacker_stats: Dict[str, int],
        defender_stats: Dict[str, int],
        multiplier: float
    ) -> Dict[str, Any]:
        """Apply a single effect."""
        value = int(effect.value * multiplier)
        
        # Apply damage type modifiers
        if effect.damage_type == DamageType.PHYSICAL:
            # Physical damage reduced by defense
            defense = defender_stats.get("defense", 0) if defender_stats else 0
            value = max(1, value - defense)
        elif effect.damage_type == DamageType.MAGICAL:
            # Magical damage reduced by magic defense (if exists)
            magic_def = defender_stats.get("magic_defense", 0) if defender_stats else 0
            value = max(1, value - magic_def // 2)
        elif effect.damage_type == DamageType.TRUE:
            # True damage - no reduction
            pass
        elif effect.damage_type == DamageType.HEALING:
            # Healing - don't apply to enemies
            pass
        
        return {
            "effect_type": effect.effect_type,
            "value": value,
            "description": effect.description.format(value=value),
        }
    
    def get_skill_info(self, skill: Skill) -> str:
        """Get formatted skill info."""
        lines = [
            f"{skill.name} ({skill.skill_type.value})",
            f"消耗: {skill.mana_cost} MP | 冷却: {skill.cooldown} 回合",
            f"需要等级: {skill.level_required}",
            skill.description,
        ]
        
        if skill.effects:
            lines.append("效果:")
            for effect in skill.effects:
                lines.append(f"  • {effect.description}")
        
        if skill.mastery_level > 0:
            lines.append(f"熟练度: Lv.{skill.mastery_level} (+{int((skill.mastery_bonus - 1) * 100)}%)")
        
        return "\n".join(lines)
    
    def render_skill_menu(
        self,
        skills: List[Skill],
        player_mp: int = 999,
        player_level: int = 99
    ) -> str:
        """Render skill menu for combat."""
        lines = [
            "",
            "=" * 40,
            "✨ 技能 / SKILLS",
            "=" * 40,
            f"MP: {player_mp}",
            "-" * 40,
            "",
        ]
        
        for i, skill in enumerate(skills, 1):
            can_use, _ = self.can_use_skill(skill, player_mp, player_level)
            status = "✅" if can_use else "❌"
            
            lines.append(f"  [{i}] {status} {skill.name}")
            lines.append(f"      MP: {skill.mana_cost} | CD: {skill.cooldown}")
            
            if not can_use and skill.current_cooldown > 0:
                lines.append(f"      ⏳ 冷却: {skill.current_cooldown}")
            
            lines.append(f"      {skill.description}")
            lines.append("")
        
        lines.extend([
            "-" * 40,
            "[0] 返回",
            "=" * 40,
        ])
        
        return "\n".join(lines)
    
    def render_skill_tree_ui(self, tree: SkillTree) -> str:
        """Render skill tree UI."""
        lines = [
            "",
            "=" * 50,
            f"🎮 {tree.name}",
            f"技能点: {tree.available_skill_points}/{tree.total_skill_points}",
            "=" * 50,
            "",
        ]
        
        for cat in tree.categories:
            lines.append(f"{cat.icon} {cat.name}")
            lines.append(f"   {cat.description}")
            
            for skill_id in cat.skills:
                skill = self.get_skill(skill_id)
                if skill:
                    mastery_stars = "⭐" * skill.mastery_level
                    lines.append(f"   • {skill.name} {mastery_stars}")
                    lines.append(f"     Lv.{skill.level_required} | {skill.description[:30]}...")
            lines.append("")
        
        lines.append("=" * 50)
        
        return "\n".join(lines)
    
    def tick_all_cooldowns(self, skills: List[Skill]):
        """Reduce cooldown for all skills."""
        for skill in skills:
            skill.tick()


# Export
__all__ = [
    "SkillType",
    "SkillTarget",
    "DamageType",
    "SkillEffect",
    "Skill",
    "SkillCategory",
    "SkillTree",
    "SkillSystem",
]
