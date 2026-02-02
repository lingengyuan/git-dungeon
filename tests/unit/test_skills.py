"""Tests for skill system."""

import pytest

from src.core.skills import (
    Skill,
    SkillType,
    TargetType,
    SkillEffect,
    get_skill,
    get_all_skills,
    get_skills_by_type,
    SkillBook,
)


class TestSkill:
    """Tests for Skill dataclass."""

    def test_skill_creation(self):
        """Test basic skill creation."""
        skill = Skill(
            id="test_skill",
            name="Test Skill",
            description="A test skill",
            skill_type=SkillType.ATTACK,
            mp_cost=10,
            base_damage=1.5,
        )

        assert skill.id == "test_skill"
        assert skill.name == "Test Skill"
        assert skill.description == "A test skill"
        assert skill.skill_type == SkillType.ATTACK
        assert skill.mp_cost == 10
        assert skill.base_damage == 1.5
        assert skill.critical_bonus == 0.0
        assert skill.target == TargetType.ENEMY
        assert skill.cooldown == 0
        assert skill.effect is None

    def test_skill_with_effect(self):
        """Test skill with effect."""
        effect = SkillEffect(
            type="stun",
            value=1.0,
            duration=1,
            description="Stun enemy",
        )

        skill = Skill(
            id="stun_skill",
            name="Stun",
            description="Stun enemy",
            skill_type=SkillType.DEBUFF,
            mp_cost=15,
            effect=effect,
        )

        assert skill.effect is not None
        assert skill.effect.type == "stun"
        assert skill.effect.duration == 1


class TestSkillEffects:
    """Tests for SkillEffect."""

    def test_effect_creation(self):
        """Test effect creation."""
        effect = SkillEffect(
            type="shield",
            value=20.0,
            duration=2,
            description="Gain shield",
        )

        assert effect.type == "shield"
        assert effect.value == 20.0
        assert effect.duration == 2


class TestSkillsCollection:
    """Tests for skills collection."""

    def test_get_skill(self):
        """Test getting a skill by ID."""
        skill = get_skill("git_add")
        assert skill is not None
        assert skill.id == "git_add"
        assert skill.name == "Git Add"

    def test_get_nonexistent_skill(self):
        """Test getting a non-existent skill returns None."""
        skill = get_skill("nonexistent")
        assert skill is None

    def test_get_all_skills(self):
        """Test getting all skills."""
        skills = get_all_skills()
        assert len(skills) == 8  # We have 8 skills
        assert any(s.id == "git_add" for s in skills)
        assert any(s.id == "git_commit" for s in skills)

    def test_get_skills_by_type(self):
        """Test filtering skills by type."""
        attack_skills = get_skills_by_type(SkillType.ATTACK)
        assert len(attack_skills) >= 4  # git_add, git_commit, git_push, git_merge

        heal_skills = get_skills_by_type(SkillType.HEAL)
        assert len(heal_skills) == 1
        assert heal_skills[0].id == "git_pull"

        buff_skills = get_skills_by_type(SkillType.BUFF)
        assert len(buff_skills) == 1
        assert buff_skills[0].id == "git_stash"


class TestSkillBook:
    """Tests for SkillBook."""

    def test_empty_book(self):
        """Test empty skill book."""
        book = SkillBook()
        assert len(book.skills) == 0

    def test_add_skill(self):
        """Test adding a skill."""
        book = SkillBook()
        result = book.add_skill("git_add")
        assert result is True
        assert "git_add" in book.skills

    def test_add_invalid_skill(self):
        """Test adding invalid skill returns False."""
        book = SkillBook()
        result = book.add_skill("invalid_skill")
        assert result is False
        assert len(book.skills) == 0

    def test_has_skill(self):
        """Test checking if skill exists."""
        book = SkillBook()
        assert book.has_skill("git_add") is False

        book.add_skill("git_add")
        assert book.has_skill("git_add") is True

    def test_get_mastery(self):
        """Test getting mastery level."""
        book = SkillBook()
        assert book.get_mastery("git_add") == 0

        book.add_skill("git_add", level=3)
        assert book.get_mastery("git_add") == 3

    def test_get_available_skills(self):
        """Test getting available skills."""
        book = SkillBook()
        skills = book.get_available_skills()
        assert len(skills) == 0

        book.add_skill("git_add")
        book.add_skill("git_commit")

        skills = book.get_available_skills()
        assert len(skills) == 2
        skill_ids = [s[0].id for s in skills]
        assert "git_add" in skill_ids
        assert "git_commit" in skill_ids


class TestGitSkills:
    """Tests for Git-specific skills."""

    def test_git_add_skill(self):
        """Test Git Add skill properties."""
        skill = get_skill("git_add")
        assert skill is not None
        assert skill.mp_cost == 0  # Basic attack costs no MP
        assert skill.skill_type == SkillType.ATTACK
        assert skill.target == TargetType.ENEMY

    def test_git_commit_skill(self):
        """Test Git Commit skill properties."""
        skill = get_skill("git_commit")
        assert skill is not None
        assert skill.mp_cost == 20
        assert skill.base_damage == 2.0  # Powerful
        assert skill.critical_bonus == 50.0  # High crit chance

    def test_git_pull_skill(self):
        """Test Git Pull is a heal skill."""
        skill = get_skill("git_pull")
        assert skill is not None
        assert skill.skill_type == SkillType.HEAL
        assert skill.target == TargetType.SELF
        assert skill.base_damage == 0.3  # 30% heal

    def test_git_stash_skill(self):
        """Test Git Stash is a buff skill."""
        skill = get_skill("git_stash")
        assert skill is not None
        assert skill.skill_type == SkillType.BUFF
        assert skill.effect is not None
        assert skill.effect.type == "shield"

    def test_git_reset_skill(self):
        """Test Git Reset is a special skill."""
        skill = get_skill("git_reset")
        assert skill is not None
        assert skill.skill_type == SkillType.SPECIAL
        assert skill.effect is not None
        assert skill.effect.type == "cleanse"

    def test_git_merge_skill(self):
        """Test Git Merge is multi-hit."""
        skill = get_skill("git_merge")
        assert skill is not None
        assert skill.base_damage == 0.8  # Lower per hit

    def test_git_rebase_skill(self):
        """Test Git Rebase is a debuff."""
        skill = get_skill("git_rebase")
        assert skill is not None
        assert skill.skill_type == SkillType.DEBUFF
        assert skill.effect is not None
        assert skill.effect.type == "stun"


class TestSkillBookCombat:
    """Tests for skill usage in combat context."""

    def test_skill_execution_requirements(self):
        """Test skill MP cost requirements."""
        book = SkillBook()
        book.add_skill("git_add", level=1)
        book.add_skill("git_commit", level=1)
        book.add_skill("git_pull", level=1)

        # Should have these skills
        assert book.has_skill("git_add")
        assert book.has_skill("git_commit")
        assert book.has_skill("git_pull")

        # Get mastery levels
        assert book.get_mastery("git_add") == 1
        assert book.get_mastery("git_commit") == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
