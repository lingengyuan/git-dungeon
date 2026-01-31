"""Tests for character leveling system."""

import pytest

from src.core.character import (
    CharacterComponent,
    CharacterType,
    CharacterStats,
    Stat,
    StatType,
    get_character,
)


class TestCharacterLeveling:
    """Tests for character leveling system."""

    def test_initial_level(self):
        """Test character starts at level 1."""
        char = CharacterComponent(CharacterType.PLAYER, "Player")
        assert char.level == 1
        assert char.experience == 0
        assert char.experience_to_next == 100  # 1^2 * 100

    def test_exp_needed_formula(self):
        """Test experience formula: level^2 * 100."""
        char = CharacterComponent(CharacterType.PLAYER, "Player")

        # Level 1: 1^2 * 100 = 100
        assert char.experience_to_next == 100

        # Level 2: 2^2 * 100 = 400
        char.experience = 100
        char.gain_experience(100)
        assert char.experience_to_next == 400

    def test_gain_experience(self):
        """Test gaining experience."""
        char = CharacterComponent(CharacterType.PLAYER, "Player")
        char.initialize_stats(hp=100, mp=50, attack=10, defense=5)

        gained, leveled = char.gain_experience(50)
        assert gained == 50
        assert leveled is False
        assert char.experience == 50

    def test_single_level_up(self):
        """Test single level up."""
        char = CharacterComponent(CharacterType.PLAYER, "Player")
        char.initialize_stats(hp=100, mp=50, attack=10, defense=5)
        initial_hp = char.stats.hp.value
        initial_atk = char.stats.attack.value

        # Gain enough for level up (100 exp)
        gained, leveled = char.gain_experience(100)
        assert gained == 100
        assert leveled is True
        assert char.level == 2
        assert char.experience == 0

        # Stats should increase
        assert char.stats.hp.value > initial_hp
        assert char.stats.attack.value >= initial_atk

    def test_multi_level_up(self):
        """Test multiple level ups at once."""
        char = CharacterComponent(CharacterType.PLAYER, "Player")
        char.initialize_stats(hp=100, mp=50, attack=10, defense=5)

        # Gain huge amount for multiple levels
        gained, leveled = char.gain_experience(1000)
        assert gained == 1000
        assert leveled is True
        assert char.level > 2

    def test_stats_increase_on_level_up(self):
        """Test stats increase on level up."""
        char = CharacterComponent(CharacterType.PLAYER, "Player")
        char.initialize_stats(hp=100, mp=50, attack=20, defense=10)

        initial_hp = char.stats.hp.value
        initial_mp = char.stats.mp.value
        initial_atk = char.stats.attack.value
        initial_def = char.stats.defense.value

        char.gain_experience(200)  # Should trigger at least one level up

        # All stats should increase
        assert char.stats.hp.value > initial_hp
        assert char.stats.mp.value > initial_mp
        assert char.stats.attack.value > initial_atk
        assert char.stats.defense.value >= initial_def

    def test_full_heal_on_level_up(self):
        """Test character heals to full on level up."""
        char = CharacterComponent(CharacterType.PLAYER, "Player")
        char.initialize_stats(hp=100, mp=50, attack=10, defense=5)

        # Take damage
        char.current_hp = 50
        char.current_mp = 25

        # Level up
        char.gain_experience(100)

        # Should be full health
        assert char.current_hp == char.stats.hp.value
        assert char.current_mp == char.stats.mp.value

    def test_get_level_info(self):
        """Test getting level information."""
        char = CharacterComponent(CharacterType.PLAYER, "Player")
        char.initialize_stats(hp=100, mp=50, attack=10, defense=5)

        char.experience = 50
        info = char.get_level_info()

        assert info['level'] == 1
        assert info['experience'] == 50
        assert info['experience_to_next'] == 100
        assert info['progress'] == 50.0

    def test_get_stat_summary(self):
        """Test getting stat summary."""
        char = CharacterComponent(CharacterType.PLAYER, "Player")
        char.initialize_stats(hp=100, mp=50, attack=20, defense=10)

        summary = char.get_stat_summary()

        assert summary['hp'] == 100
        assert summary['max_hp'] == 100
        assert summary['mp'] == 50
        assert summary['attack'] == 20
        assert summary['defense'] == 10

    def test_get_power_level(self):
        """Test power level calculation."""
        char = CharacterComponent(CharacterType.PLAYER, "Player")
        char.initialize_stats(hp=100, mp=50, attack=20, defense=10)

        power = char.get_power_level()

        # Power should be positive
        assert power > 0
        # Power should be less than sum of stats
        total = 100 + 50 + 20 + 10 + 10 + 10 + 5 + 5  # hp+mp+atk+def+speed+crit+eva+luck
        assert power < total

    def test_total_exp_gained(self):
        """Test total experience gained tracking."""
        char = CharacterComponent(CharacterType.PLAYER, "Player")
        char.initialize_stats(hp=100, mp=50, attack=10, defense=5)

        assert char._total_exp_gained == 0

        char.gain_experience(50)
        assert char._total_exp_gained == 50

        char.gain_experience(100)
        assert char._total_exp_gained == 150

    def test_experience_overflow(self):
        """Test experience overflow on level up."""
        char = CharacterComponent(CharacterType.PLAYER, "Player")
        char.initialize_stats(hp=100, mp=50, attack=10, defense=5)

        # Gain exactly level up amount + extra
        char.gain_experience(150)

        # Should be level 2 with 50 excess experience
        assert char.level == 2
        assert char.experience == 50


class TestStat:
    """Tests for Stat class."""

    def test_stat_creation(self):
        """Test stat creation."""
        stat = Stat(base_value=100)
        assert stat.base_value == 100
        assert stat.modifier == 0
        assert stat.value == 100

    def test_stat_with_modifier(self):
        """Test stat with modifier."""
        stat = Stat(base_value=100)
        stat.add_modifier(20)
        assert stat.modifier == 20
        assert stat.value == 120

    def test_stat_remove_modifier(self):
        """Test removing modifier."""
        stat = Stat(base_value=100)
        stat.add_modifier(20)
        stat.remove_modifier(10)
        assert stat.modifier == 10
        assert stat.value == 110

    def test_stat_reset_modifiers(self):
        """Test resetting modifiers."""
        stat = Stat(base_value=100)
        stat.add_modifier(50)
        stat.reset_modifiers()
        assert stat.modifier == 0
        assert stat.value == 100


class TestCharacterStats:
    """Tests for CharacterStats class."""

    def test_stats_creation(self):
        """Test creating character stats."""
        stats = CharacterStats.create(
            hp=100,
            mp=50,
            attack=20,
            defense=10,
            speed=15,
            critical=15,
            evasion=10,
            luck=5,
        )

        assert stats.hp.value == 100
        assert stats.mp.value == 50
        assert stats.attack.value == 20
        assert stats.defense.value == 10

    def test_get_stat_by_type(self):
        """Test getting stat by type."""
        stats = CharacterStats.create(
            hp=100,
            mp=50,
            attack=20,
            defense=10,
        )

        hp_stat = stats.get(StatType.HP)
        assert hp_stat.value == 100

        atk_stat = stats.get(StatType.ATTACK)
        assert atk_stat.value == 20

    def test_stats_total(self):
        """Test getting total of all stats."""
        stats = CharacterStats.create(
            hp=100,
            mp=50,
            attack=20,
            defense=10,
            speed=10,
            critical=10,
            evasion=5,
            luck=5,
        )

        total = stats.total()
        # total() only sums hp, mp, attack, defense, speed
        assert total == 190  # 100 + 50 + 20 + 10 + 10

    def test_stats_reset(self):
        """Test resetting all stat modifiers."""
        stats = CharacterStats.create(
            hp=100,
            mp=50,
            attack=20,
            defense=10,
        )

        # Add modifiers
        stats.hp.add_modifier(10)
        stats.attack.add_modifier(5)

        assert stats.hp.value == 110
        assert stats.attack.value == 25

        # Reset
        stats.reset()

        assert stats.hp.value == 100
        assert stats.attack.value == 20


class TestGetCharacter:
    """Tests for get_character helper."""

    def test_get_character_success(self):
        """Test getting character from entity."""
        from src.core.entity import Entity

        entity = Entity(id="player", name="Player")
        char_comp = CharacterComponent(CharacterType.PLAYER, "Player")
        entity.add_component(char_comp)

        char = get_character(entity)
        assert char is char_comp
        assert char.name == "Player"

    def test_get_character_not_found(self):
        """Test getting character from entity without one raises error."""
        from src.core.entity import Entity
        from src.utils.exceptions import GameError

        entity = Entity(id="npc", name="NPC")

        with pytest.raises(GameError):
            get_character(entity)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
