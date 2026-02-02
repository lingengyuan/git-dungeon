"""Tests for combat UI components."""

import pytest

from src.ui.combat_screen import (
    format_hp_bar,
    format_mp_bar,
    CharacterPanel,
    CombatLog,
    CombatScreen,
)


class TestFormatBars:
    """Tests for HP/MP bar formatting."""

    def test_full_hp_bar(self):
        """Test HP bar at 100%."""
        bar = format_hp_bar(100, 100, width=10)
        assert "█" * 10 in bar
        assert "100/100" in bar

    def test_half_hp_bar(self):
        """Test HP bar at 50%."""
        bar = format_hp_bar(50, 100, width=10)
        assert "█" * 5 in bar
        assert "░" * 5 in bar

    def test_empty_hp_bar(self):
        """Test HP bar at 0%."""
        bar = format_hp_bar(0, 100, width=10)
        assert "░" * 10 in bar
        assert "0/100" in bar

    def test_overheal_hp_bar(self):
        """Test HP bar with overheal (capped at 100%)."""
        bar = format_hp_bar(150, 100, width=10)
        assert "█" * 10 in bar  # Capped

    def test_full_mp_bar(self):
        """Test MP bar at 100%."""
        bar = format_mp_bar(50, 50, width=10)
        assert "▓" * 10 in bar
        assert "50/50" in bar

    def test_empty_mp_bar(self):
        """Test MP bar at 0%."""
        bar = format_mp_bar(0, 50, width=10)
        assert "░" * 10 in bar

    def test_zero_max_hp(self):
        """Test HP bar with zero max HP."""
        bar = format_hp_bar(0, 0, width=10)
        assert bar is not None


class TestCharacterPanel:
    """Tests for CharacterPanel component."""

    def test_panel_creation_player(self):
        """Test creating player panel."""
        panel = CharacterPanel(
            name="Player",
            hp=100,
            max_hp=100,
            mp=50,
            max_mp=50,
            attack=10,
            defense=5,
            is_player=True,
        )
        assert panel._name == "Player"
        assert panel._hp == 100
        assert panel._is_player is True

    def test_panel_creation_enemy(self):
        """Test creating enemy panel."""
        panel = CharacterPanel(
            name="Enemy",
            hp=50,
            max_hp=50,
            attack=8,
            defense=3,
            is_player=False,
        )
        assert panel._name == "Enemy"
        assert panel._is_player is False

    def test_panel_update(self):
        """Test updating panel stats."""
        panel = CharacterPanel(
            name="Player",
            hp=100,
            max_hp=100,
            attack=10,
            defense=5,
        )
        panel.update_stats(hp=80, attack=12)
        assert panel._hp == 80
        assert panel._attack == 12


class TestCombatLog:
    """Tests for CombatLog component."""

    def test_log_creation(self):
        """Test creating empty log."""
        log = CombatLog(max_lines=5)
        assert log._max_lines == 5
        assert log._lines == []

    def test_add_message(self):
        """Test adding messages."""
        log = CombatLog(max_lines=5)
        log.add_message("Test message")
        assert len(log._lines) == 1
        assert "Test message" in log._lines[0]

    def test_log_max_lines(self):
        """Test log respects max lines."""
        log = CombatLog(max_lines=3)
        for i in range(10):
            log.add_message(f"Message {i}")
        assert len(log._lines) == 3
        assert "Message 9" in log._lines[-1]

    def test_log_clear(self):
        """Test clearing the log."""
        log = CombatLog()
        log.add_message("Test")
        log.clear()
        assert log._lines == []


class TestCombatScreen:
    """Tests for CombatScreen component."""

    def test_screen_creation(self):
        """Test creating combat screen."""
        screen = CombatScreen()
        assert screen is not None
        assert hasattr(screen, "_combat_log")

    def test_add_log_message(self):
        """Test adding log messages."""
        screen = CombatScreen()
        screen.add_log_message("Player attacks!")
        assert "Player attacks!" in screen._combat_log._lines[0]

    def test_combat_log_integration(self):
        """Test combat log works with screen."""
        screen = CombatScreen()
        # Add multiple messages
        for i in range(5):
            screen.add_log_message(f"Action {i}")
        assert len(screen._combat_log._lines) == 5


class TestCombatUIIntegration:
    """Integration tests for combat UI components."""

    def test_full_combat_display(self):
        """Test full combat UI display."""
        # Create all components
        player_panel = CharacterPanel(
            name="Player",
            hp=100,
            max_hp=100,
            mp=50,
            max_mp=50,
            attack=10,
            defense=5,
        )
        enemy_panel = CharacterPanel(
            name="Enemy",
            hp=20,
            max_hp=20,
            attack=5,
            defense=3,
            is_player=False,
        )
        combat_log = CombatLog()

        # Add messages
        combat_log.add_message("Combat started!")
        combat_log.add_message("Player attacks for 10 damage!")

        # Verify
        assert player_panel._hp == 100
        assert enemy_panel._hp == 20
        assert len(combat_log._lines) == 2

    def test_combat_flow_updates(self):
        """Test combat flow updates panels correctly."""
        # Initial state
        enemy_hp = 20

        # Simulate damage
        damage = 5
        enemy_hp = max(0, enemy_hp - damage)

        # Update panel
        enemy_panel = CharacterPanel(
            name="Enemy",
            hp=enemy_hp,
            max_hp=20,
            attack=5,
            defense=3,
            is_player=False,
        )

        # Verify
        assert enemy_panel._hp == 15


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
