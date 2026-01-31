"""Unit tests for combat module."""

import pytest
from unittest.mock import MagicMock

from src.core.combat import (
    CombatSystem,
    CombatEncounter,
    CombatAction,
    DamageType,
    CombatResult,
)
from src.core.character import CharacterComponent, CharacterType
from src.core.entity import Entity
from src.core.character import CharacterStats, StatType


class TestCombatSystem:
    """Tests for CombatSystem class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.combat = CombatSystem()

    def test_calculate_damage_basic(self):
        """Test basic damage calculation."""
        # Create attacker and defender
        attacker = Entity(id="attacker", name="Attacker")
        defender = Entity(id="defender", name="Defender")

        attacker_char = CharacterComponent(CharacterType.PLAYER, "Attacker")
        attacker_char.initialize_stats(hp=100, mp=50, attack=20, defense=10)
        attacker.add_component(attacker_char)

        defender_char = CharacterComponent(CharacterType.MONSTER, "Defender")
        defender_char.initialize_stats(hp=50, mp=0, attack=10, defense=5)
        defender.add_component(defender_char)

        damage, is_critical = self.combat.calculate_damage(
            attacker=attacker,
            defender=defender,
            base_damage=10,
            critical_chance=0,  # No critical hits in this test
        )

        # Damage should be: base (10) + attack (20) - defense (5) = 25
        assert damage == 25
        assert is_critical is False

    def test_calculate_damage_critical(self):
        """Test critical hit calculation."""
        attacker = Entity(id="attacker", name="Attacker")
        defender = Entity(id="defender", name="Defender")

        attacker_char = CharacterComponent(CharacterType.PLAYER, "Attacker")
        attacker_char.initialize_stats(hp=100, mp=50, attack=20, defense=10, critical=100)
        attacker.add_component(attacker_char)

        defender_char = CharacterComponent(CharacterType.MONSTER, "Defender")
        defender_char.initialize_stats(hp=50, mp=0, attack=10, defense=5)
        defender.add_component(defender_char)

        damage, is_critical = self.combat.calculate_damage(
            attacker=attacker,
            defender=defender,
            base_damage=10,
        )

        # With 100% critical chance, should be critical
        # Critical damage = (base + attack - defense) * 1.5 = 25 * 1.5 = 37.5
        assert damage == 38  # Rounded
        assert is_critical is True

    def test_check_evasion(self):
        """Test evasion check."""
        attacker = Entity(id="attacker", name="Attacker")
        defender = Entity(id="defender", name="Defender")

        attacker_char = CharacterComponent(CharacterType.PLAYER, "Attacker")
        attacker_char.initialize_stats(hp=100, mp=50, attack=20, defense=10)
        attacker.add_component(attacker_char)

        defender_char = CharacterComponent(CharacterType.MONSTER, "Defender")
        defender_char.initialize_stats(hp=50, mp=0, attack=10, defense=5, evasion=100)
        defender.add_component(defender_char)

        # With 100% evasion, should always evade
        assert self.combat.check_evasion(attacker, defender) is True

    def test_execute_action_damage(self):
        """Test executing a damage action."""
        attacker = Entity(id="attacker", name="Attacker")
        defender = Entity(id="defender", name="Defender")

        attacker_char = CharacterComponent(CharacterType.PLAYER, "Attacker")
        attacker_char.initialize_stats(hp=100, mp=50, attack=20, defense=10)
        attacker.add_component(attacker_char)

        defender_char = CharacterComponent(CharacterType.MONSTER, "Defender")
        defender_char.initialize_stats(hp=50, mp=0, attack=10, defense=5)
        defender.add_component(defender_char)

        action = CombatAction(
            action_type="attack",
            source=attacker,
            target=defender,
            damage=20,
        )

        result = self.combat.execute_action(action)

        # Damage should be applied
        assert defender_char.current_hp == 35  # 50 - 15 (reduced by defense)
        assert result == CombatResult.DRAW

    def test_execute_action_kill(self):
        """Test executing a killing blow."""
        attacker = Entity(id="attacker", name="Attacker")
        defender = Entity(id="defender", name="Defender")

        attacker_char = CharacterComponent(CharacterType.PLAYER, "Attacker")
        attacker_char.initialize_stats(hp=100, mp=50, attack=20, defense=10)
        attacker.add_component(attacker_char)

        defender_char = CharacterComponent(CharacterType.MONSTER, "Defender")
        defender_char.initialize_stats(hp=20, mp=0, attack=10, defense=0)
        defender.add_component(defender_char)

        action = CombatAction(
            action_type="attack",
            source=attacker,
            target=defender,
            damage=30,
        )

        result = self.combat.execute_action(action)

        # Defender should be dead
        assert defender_char.is_dead is True
        assert result == CombatResult.PLAYER_WIN


class TestCombatEncounter:
    """Tests for CombatEncounter class."""

    def test_start_combat(self):
        """Test starting a combat encounter."""
        combat_system = CombatSystem()
        player = Entity(id="player", name="Player")
        enemy = Entity(id="enemy", name="Enemy")

        player_char = CharacterComponent(CharacterType.PLAYER, "Player")
        player_char.initialize_stats(hp=100, mp=50, attack=20, defense=10)
        player.add_component(player_char)

        enemy_char = CharacterComponent(CharacterType.MONSTER, "Enemy")
        enemy_char.initialize_stats(hp=50, mp=0, attack=10, defense=5)
        enemy.add_component(enemy_char)

        encounter = combat_system.start_combat(player, enemy)

        assert encounter.player == player
        assert encounter.enemy == enemy
        assert encounter.turn_number == 1
        assert encounter.is_player_turn is True

    def test_player_action(self):
        """Test player action in combat."""
        combat_system = CombatSystem()
        player = Entity(id="player", name="Player")
        enemy = Entity(id="enemy", name="Enemy")

        player_char = CharacterComponent(CharacterType.PLAYER, "Player")
        player_char.initialize_stats(hp=100, mp=50, attack=20, defense=10)
        player.add_component(player_char)

        enemy_char = CharacterComponent(CharacterType.MONSTER, "Enemy")
        enemy_char.initialize_stats(hp=50, mp=0, attack=10, defense=5)
        enemy.add_component(enemy_char)

        encounter = combat_system.start_combat(player, enemy)

        result = encounter.player_action("attack", damage=15)

        # Damage should be applied
        assert enemy_char.current_hp == 40  # 50 - 10 (after defense)
        assert encounter.turn_phase == "enemy"
        assert result == CombatResult.DRAW

    def test_enemy_turn(self):
        """Test enemy turn in combat."""
        combat_system = CombatSystem()
        player = Entity(id="player", name="Player")
        enemy = Entity(id="enemy", name="Enemy")

        player_char = CharacterComponent(CharacterType.PLAYER, "Player")
        player_char.initialize_stats(hp=100, mp=50, attack=20, defense=10)
        player.add_component(player_char)

        enemy_char = CharacterComponent(CharacterType.MONSTER, "Enemy")
        enemy_char.initialize_stats(hp=50, mp=0, attack=10, defense=5)
        enemy.add_component(enemy_char)

        encounter = combat_system.start_combat(player, enemy)
        encounter.turn_phase = "enemy"  # Skip player turn

        result = encounter.enemy_turn()

        # Enemy attack 10, player defense 10
        # Actual damage = max(1, 10 - 10) = 1
        # HP should be 99 after taking damage
        assert player_char.current_hp == 99  # 100 - 1
        assert encounter.turn_number == 2
        assert encounter.is_player_turn is True


class TestCombatAction:
    """Tests for CombatAction dataclass."""

    def test_combat_action_creation(self):
        """Test CombatAction creation."""
        source = Entity(id="source", name="Source")
        target = Entity(id="target", name="Target")

        action = CombatAction(
            action_type="attack",
            source=source,
            target=target,
            damage=20,
            description="Attacks with sword!",
        )

        assert action.action_type == "attack"
        assert action.damage == 20
        assert action.description == "Attacks with sword!"
        assert action.is_critical is False
        assert action.is_evaded is False
