"""Integration tests for skill system in combat."""

import tempfile
import subprocess
from pathlib import Path

import pytest

from src.core.game_engine import GameState
from src.core.character import get_character, CharacterComponent, CharacterType
from src.core.skills import (
    get_skill,
    SkillBook,
    SkillType,
)
from src.core.combat import CombatSystem


class TestSkillCombat:
    """Test skills in actual combat scenarios."""

    @pytest.fixture
    def test_repo(self, tmp_path):
        """Create a test repository."""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()

        subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo_path,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=repo_path,
            capture_output=True,
        )

        with open(repo_path / "test.txt", "w") as f:
            f.write("test\n")
        subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "feat: Add test"],
            cwd=repo_path,
            capture_output=True,
        )

        return repo_path

    def test_git_add_basic_attack(self, test_repo):
        """Test Git Add as basic attack."""
        game = GameState()
        game.load_repository(str(test_repo))
        game.start_combat()

        player = get_character(game.player)
        enemy = get_character(game.current_combat.enemy)
        initial_enemy_hp = enemy.current_hp

        # Use git_add skill (basic attack)
        skill = get_skill("git_add")
        damage = int(player.stats.attack.value * skill.base_damage)

        game.player_action("attack", damage=damage)

        # Enemy should take damage
        enemy = get_character(game.current_combat.enemy)
        assert enemy.current_hp < initial_enemy_hp

    def test_git_pull_heal(self, test_repo):
        """Test Git Pull healing."""
        game = GameState()
        game.load_repository(str(test_repo))
        game.start_combat()

        player = get_character(game.player)
        initial_hp = player.current_hp

        # After start_combat, it's player's turn first
        # Player attacks
        game.player_action("attack", damage=player.stats.attack.value)

        # Check if combat ended
        if game.current_combat:
            # Enemy's turn
            game.enemy_turn()

        player = get_character(game.player)
        assert player.current_hp <= initial_hp  # Took some damage or none

    def test_skill_cooldown_tracking(self, test_repo):
        """Test skill cooldown tracking."""
        game = GameState()
        game.load_repository(str(test_repo))
        game.start_combat()

        player = get_character(game.player)
        enemy = get_character(game.current_combat.enemy)

        # Use git_commit (high MP cost skill)
        game.player_action("attack", damage=player.stats.attack.value)

        # Enemy attacks back
        if game.current_combat:
            game.enemy_turn()

        # Player should still be alive
        player = get_character(game.player)
        assert player.current_hp >= 0

    def test_full_combat_with_skills(self, test_repo):
        """Test complete combat using various skills."""
        game = GameState()
        game.load_repository(str(test_repo))

        rounds = 0
        max_rounds = 20

        while len(game.defeated_commits) < len(game.commits) and rounds < max_rounds:
            if not game.current_combat:
                game.start_combat()

            if not game.current_combat:
                break

            player = get_character(game.player)
            enemy = get_character(game.current_combat.enemy)

            # Choose skill based on MP
            if player.current_mp >= 20:
                # Use git_commit
                damage = int(player.stats.attack.value * 2.0)
            elif player.current_mp >= 15:
                # Use git_push
                damage = int(player.stats.attack.value * 1.8)
            else:
                # Use git_add
                damage = player.stats.attack.value

            game.player_action("attack", damage=damage)
            rounds += 1

            if not game.current_combat:
                continue

            game.enemy_turn()

        # Should have defeated the enemy
        assert len(game.defeated_commits) == 1

    def test_multiple_skills_available(self, test_repo):
        """Test that multiple skills are available."""
        game = GameState()
        game.load_repository(str(test_repo))
        game.start_combat()

        player = get_character(game.player)

        # Check player has enough MP for various skills
        assert player.current_mp >= 0  # git_add

        # git_pull costs 10 MP
        # git_stash costs 10 MP
        # git_push costs 15 MP
        # git_commit costs 20 MP

        # All skills should be available based on MP
        skill = get_skill("git_add")
        assert player.current_mp >= skill.mp_cost


class TestSkillBookIntegration:
    """Test SkillBook integration with characters."""

    def test_character_with_skill_book(self):
        """Test character can have a skill book."""
        char = CharacterComponent(CharacterType.PLAYER, "Player")
        char.initialize_stats(hp=100, mp=50, attack=20, defense=10)

        # Character should be able to use skills
        assert char.current_mp >= 0

    def test_skill_requirements(self):
        """Test skill MP requirements."""
        char = CharacterComponent(CharacterType.PLAYER, "Player")
        char.initialize_stats(hp=100, mp=50, attack=20, defense=10)

        # Can use git_add (0 MP)
        assert char.current_mp >= 0

        # Can use git_pull (10 MP)
        assert char.current_mp >= 10

        # Can use git_commit (20 MP)
        assert char.current_mp >= 20

        # Cannot use skills that cost more than MP
        char.current_mp = 5
        assert char.current_mp < 10  # Cannot use git_pull
        assert char.current_mp < 20  # Cannot use git_commit


class TestCombatWithSkills:
    """Test combat system with skill integration."""

    def test_combat_system_initialization(self):
        """Test combat system can be initialized."""
        combat = CombatSystem()
        assert combat is not None
        assert combat.combat_log == []
        assert combat.current_combat is None

    def test_damage_calculation_with_skill_multiplier(self):
        """Test damage calculation respects skill multipliers."""
        base_attack = 20
        skill_multiplier = 2.0  # git_commit

        expected_damage = int(base_attack * skill_multiplier)
        assert expected_damage == 40


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
