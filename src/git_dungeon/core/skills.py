"""Skill system for Git Dungeon.

Maps Git commands to game skills.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SkillType(Enum):
    """Types of skills."""

    ATTACK = "attack"
    HEAL = "heal"
    BUFF = "buff"
    DEBUFF = "debuff"
    SPECIAL = "special"


class TargetType(Enum):
    """Targeting type for skills."""

    ENEMY = "enemy"
    SELF = "self"
    ALL = "all"


@dataclass
class SkillEffect:
    """Effect applied by a skill."""

    type: str
    value: float = 0.0
    duration: int = 0  # 0 = permanent
    description: str = ""


@dataclass
class Skill:
    """A skill that can be used in combat.

    Attributes:
        id: Unique skill identifier (e.g., 'git_add')
        name: Display name (e.g., 'Git Add')
        description: Skill description
        skill_type: Type of skill
        mp_cost: MP cost to use
        base_damage: Base damage multiplier
        critical_bonus: Bonus critical chance (0-100)
        target: Who the skill targets
        cooldown: Cooldown turns (0 = no cooldown)
        effect: Optional additional effect
    """

    id: str
    name: str
    description: str
    skill_type: SkillType
    mp_cost: int
    base_damage: float = 1.0
    critical_bonus: float = 0.0
    target: TargetType = TargetType.ENEMY
    cooldown: int = 0
    effect: Optional[SkillEffect] = None


# Git command mappings to skills
SKILLS = {
    "git_add": Skill(
        id="git_add",
        name="Git Add",
        description="Add file to staging - Basic attack",
        skill_type=SkillType.ATTACK,
        mp_cost=0,
        base_damage=1.0,
        target=TargetType.ENEMY,
    ),
    "git_commit": Skill(
        id="git_commit",
        name="Git Commit",
        description="Commit changes - Powerful attack with high critical chance",
        skill_type=SkillType.ATTACK,
        mp_cost=20,
        base_damage=2.0,
        critical_bonus=50.0,
        target=TargetType.ENEMY,
    ),
    "git_push": Skill(
        id="git_push",
        name="Git Push",
        description="Push to remote - Long-range attack",
        skill_type=SkillType.ATTACK,
        mp_cost=15,
        base_damage=1.8,
        critical_bonus=30.0,
        target=TargetType.ENEMY,
    ),
    "git_pull": Skill(
        id="git_pull",
        name="Git Pull",
        description="Pull changes - Heal HP",
        skill_type=SkillType.HEAL,
        mp_cost=10,
        base_damage=0.3,  # Heals 30% of max HP
        target=TargetType.SELF,
    ),
    "git_stash": Skill(
        id="git_stash",
        name="Git Stash",
        description="Stash changes - Gain temporary shield",
        skill_type=SkillType.BUFF,
        mp_cost=10,
        base_damage=0,
        target=TargetType.SELF,
        effect=SkillEffect(
            type="shield",
            value=20.0,
            duration=1,
            description="Gain 20 shield for 1 turn",
        ),
    ),
    "git_reset": Skill(
        id="git_reset",
        name="Git Reset",
        description="Reset to previous state - Full heal and remove debuffs",
        skill_type=SkillType.SPECIAL,
        mp_cost=25,
        base_damage=0,
        target=TargetType.SELF,
        effect=SkillEffect(
            type="cleanse",
            value=1.0,
            description="Remove all debuffs and restore HP",
        ),
    ),
    "git_merge": Skill(
        id="git_merge",
        name="Git Merge",
        description="Merge branches - Multi-hit attack",
        skill_type=SkillType.ATTACK,
        mp_cost=30,
        base_damage=0.8,
        critical_bonus=20.0,
        target=TargetType.ENEMY,
    ),
    "git_rebase": Skill(
        id="git_rebase",
        name="Git Rebase",
        description="Rebase onto branch - Skip enemy turn",
        skill_type=SkillType.DEBUFF,
        mp_cost=20,
        base_damage=0,
        target=TargetType.ENEMY,
        effect=SkillEffect(
            type="stun",
            value=1.0,
            duration=1,
            description="Stun enemy for 1 turn",
        ),
    ),
}


def get_skill(skill_id: str) -> Optional[Skill]:
    """Get a skill by ID.

    Args:
        skill_id: Skill identifier

    Returns:
        Skill or None if not found
    """
    return SKILLS.get(skill_id)


def get_all_skills() -> list[Skill]:
    """Get all available skills.

    Returns:
        List of all skills
    """
    return list(SKILLS.values())


def get_skills_by_type(skill_type: SkillType) -> list[Skill]:
    """Get skills filtered by type.

    Args:
        skill_type: Skill type to filter

    Returns:
        List of skills of the given type
    """
    return [s for s in SKILLS.values() if s.skill_type == skill_type]


@dataclass
class SkillBook:
    """Collection of skills available to a character."""

    skills: dict[str, int] = field(default_factory=dict)  # skill_id -> mastery_level

    def add_skill(self, skill_id: str, level: int = 1) -> bool:
        """Add a skill to the book.

        Args:
            skill_id: Skill to add
            level: Mastery level

        Returns:
            True if added successfully
        """
        if skill_id not in SKILLS:
            return False
        self.skills[skill_id] = level
        return True

    def has_skill(self, skill_id: str) -> bool:
        """Check if character has a skill."""
        return skill_id in self.skills

    def get_mastery(self, skill_id: str) -> int:
        """Get mastery level of a skill."""
        return self.skills.get(skill_id, 0)

    def get_available_skills(self) -> list[tuple[Skill, int]]:
        """Get all skills with their mastery levels."""
        return [
            (SKILLS[skill_id], level)
            for skill_id, level in self.skills.items()
            if skill_id in SKILLS
        ]
