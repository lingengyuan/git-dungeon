"""Unit tests for character module."""

import pytest
from src.core.character import (
    CharacterComponent,
    CharacterStats,
    CharacterType,
    Stat,
    StatType,
    get_character,
)
from src.core.entity import Entity
from src.utils.exceptions import GameError


class TestStat:
    """Tests for Stat dataclass."""

    def test_stat_value(self):
        """Test stat value calculation."""
        stat = Stat(base_value=10, modifier=5)
        assert stat.value == 15

    def test_add_modifier(self):
        """Test adding modifiers."""
        stat = Stat(base_value=10)
        stat.add_modifier(3)
        assert stat.modifier == 3
        assert stat.value == 13

    def test_remove_modifier(self):
        """Test removing modifiers."""
        stat = Stat(base_value=10, modifier=5)
        stat.remove_modifier(3)
        assert stat.modifier == 2

    def test_reset_modifiers(self):
        """Test resetting modifiers."""
        stat = Stat(base_value=10, modifier=7)
        stat.reset_modifiers()
        assert stat.modifier == 0


class TestCharacterStats:
    """Tests for CharacterStats class."""

    def test_create(self):
        """Test creating character stats."""
        stats = CharacterStats.create(
            hp=100,
            mp=50,
            attack=20,
            defense=10,
            speed=15,
            critical=10,
            evasion=5,
            luck=5,
        )

        assert stats.hp.value == 100
        assert stats.mp.value == 50
        assert stats.attack.value == 20
        assert stats.defense.value == 10

    def test_get(self):
        """Test getting stats by type."""
        stats = CharacterStats.create(
            hp=100, mp=50, attack=20, defense=10
        )

        hp_stat = stats.get(StatType.HP)
        assert hp_stat.value == 100

    def test_total(self):
        """Test total stat calculation."""
        stats = CharacterStats.create(
            hp=100, mp=50, attack=20, defense=10, speed=15
        )

        # Total = 100 + 50 + 20 + 10 + 15 = 195
        assert stats.total() == 195

    def test_reset(self):
        """Test resetting modifiers."""
        stats = CharacterStats.create(hp=100, mp=50, attack=20, defense=10)

        # Add modifiers
        stats.hp.add_modifier(10)
        stats.attack.add_modifier(5)

        # Reset
        stats.reset()

        assert stats.hp.modifier == 0
        assert stats.attack.modifier == 0


class TestCharacterComponent:
    """Tests for CharacterComponent class."""

    def test_initialization(self):
        """Test character initialization."""
        char = CharacterComponent(
            char_type=CharacterType.PLAYER,
            name="TestPlayer",
            level=5,
            experience=500,
        )

        assert char.char_type == CharacterType.PLAYER
        assert char.name == "TestPlayer"
        assert char.level == 5
        assert char.experience == 500
        assert char.is_alive is True

    def test_initialize_stats(self):
        """Test initializing character stats."""
        char = CharacterComponent(CharacterType.PLAYER, "Test")

        char.initialize_stats(hp=100, mp=50, attack=20, defense=10)

        assert char.stats is not None
        assert char.current_hp == 100
        assert char.current_mp == 50
        assert char.stats.hp.value == 100

    def test_take_damage(self):
        """Test taking damage."""
        char = CharacterComponent(CharacterType.MONSTER, "Enemy")
        char.initialize_stats(hp=100, mp=0, attack=10, defense=5)

        damage_taken = char.take_damage(20)

        # Damage = 20 - defense (5) = 15
        assert damage_taken == 15
        assert char.current_hp == 85

    def test_take_fatal_damage(self):
        """Test taking fatal damage."""
        char = CharacterComponent(CharacterType.MONSTER, "Enemy")
        char.initialize_stats(hp=20, mp=0, attack=10, defense=0)

        damage_taken = char.take_damage(50)

        # Actual damage = max(1, 50 - 0) = 50
        assert damage_taken == 50
        # HP is capped at 0
        assert char.current_hp == 0
        assert char.is_dead is True

    def test_heal(self):
        """Test healing."""
        char = CharacterComponent(CharacterType.PLAYER, "Player")
        char.initialize_stats(hp=100, mp=50, attack=20, defense=10)

        # Defense: 10, damage taken = max(1, 40-10) = 30
        char.take_damage(40)
        # HP: 100 - 30 = 70
        assert char.current_hp == 70

        healed = char.heal(30)
        # Can heal 30 (to reach 100)
        assert healed == 30
        assert char.current_hp == 100

    def test_heal_overflow(self):
        """Test healing doesn't exceed max."""
        char = CharacterComponent(CharacterType.PLAYER, "Player")
        char.initialize_stats(hp=100, mp=50, attack=20, defense=10)

        # Defense: 10, damage taken = max(1, 10-10) = 1
        char.take_damage(10)
        # HP: 100 - 1 = 99

        healed = char.heal(50)
        # Can only heal 1 (to reach 100)
        assert healed == 1
        assert char.current_hp == 100

    def test_use_mp(self):
        """Test using MP."""
        char = CharacterComponent(CharacterType.PLAYER, "Player")
        char.initialize_stats(hp=100, mp=50, attack=20, defense=10)

        # Use 20 MP
        success = char.use_mp(20)
        assert success is True
        assert char.current_mp == 30

        # Use more than remaining
        success = char.use_mp(40)
        assert success is False
        assert char.current_mp == 30

    def test_gain_experience(self):
        """Test gaining experience and leveling up."""
        char = CharacterComponent(CharacterType.PLAYER, "Player")
        char.initialize_stats(hp=100, mp=50, attack=20, defense=10)

        # Level 1 needs 100 XP (1^2 * 100)
        gained, leveled_up = char.gain_experience(50)
        assert gained == 50
        assert leveled_up is False
        assert char.level == 1

        # Level up!
        gained, leveled_up = char.gain_experience(60)
        assert leveled_up is True
        assert char.level == 2

        # Stats should increase
        assert char.stats.hp.base_value > 100


class TestGetCharacter:
    """Tests for get_character helper function."""

    def test_get_character_success(self):
        """Test getting character from entity."""
        entity = Entity(id="test", name="Test")
        char = CharacterComponent(CharacterType.PLAYER, "Test")
        entity.add_component(char)

        result = get_character(entity)
        assert result == char

    def test_get_character_not_found(self):
        """Test getting character from entity without one."""
        entity = Entity(id="test", name="Test")

        with pytest.raises(GameError):
            get_character(entity)
