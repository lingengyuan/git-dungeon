"""Tests for save_system.py"""

import tempfile
import subprocess
from pathlib import Path

import pytest

from src.core.save_system import SaveSystem, GameSaveData, SaveMetadata
from src.core.game_engine import GameState
from src.core.character import get_character


class TestSaveSystem:
    """Tests for SaveSystem."""

    def test_save_and_load(self, tmp_path):
        """Test basic save and load cycle."""
        # Create test repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        
        subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, capture_output=True)
        
        with open(repo_path / "test.txt", "w") as f:
            f.write("test")
        subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "feat: Add test"], cwd=repo_path, capture_output=True)
        
        # Create game and save
        game = GameState()
        game.load_repository(str(repo_path))
        
        save_dir = tmp_path / "saves"
        save_system = SaveSystem(save_dir)
        
        # Save
        result = save_system.save(game, 0)
        assert result is True
        assert (save_dir / "save_0.json").exists()
        
        # Load into new game state (with repo loaded first)
        loaded_game = GameState()
        loaded_game.load_repository(str(repo_path))
        
        load_result = save_system.load(loaded_game, 0)
        assert load_result is True
        assert len(loaded_game.defeated_commits) == 0

    def test_load_game_class_method(self, tmp_path):
        """Test the new load_game class method."""
        # Create test repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        
        subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, capture_output=True)
        
        with open(repo_path / "test.txt", "w") as f:
            f.write("test")
        subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "feat: Add test"], cwd=repo_path, capture_output=True)
        
        # Create and save game
        game = GameState()
        game.load_repository(str(repo_path))
        
        # Battle and defeat commit
        game.start_combat()
        while game.current_combat:
            player = get_character(game.player)
            game.player_action("attack", damage=player.stats.attack.value)
            if not game.current_combat:
                break
            game.enemy_turn()
        
        save_dir = tmp_path / "saves"
        save_system = SaveSystem(save_dir)
        save_system.save(game, 0)
        
        # Load using class method
        loaded = SaveSystem.load_game(save_dir / "save_0.json")
        
        assert loaded is not None
        assert len(loaded.defeated_commits) == 1
        assert len(loaded.commits) >= 1

    def test_save_metadata(self):
        """Test SaveMetadata creation."""
        metadata = SaveMetadata.create()
        
        assert metadata.save_version == "1.0.0"
        assert metadata.save_time != ""
        assert metadata.player_level >= 1

    def test_save_with_empty_game(self, tmp_path):
        """Test saving a game with no repository loaded."""
        game = GameState()
        
        save_dir = tmp_path / "saves"
        save_system = SaveSystem(save_dir)
        
        result = save_system.save(game, 0)
        # Should not crash, may fail depending on implementation
        # At minimum should not raise exception

    def test_load_nonexistent_save(self, tmp_path):
        """Test loading a non-existent save file."""
        save_dir = tmp_path / "saves"
        save_system = SaveSystem(save_dir)
        
        game = GameState()
        result = save_system.load(game, 999)  # Non-existent slot
        
        assert result is False

    def test_get_save_path(self, tmp_path):
        """Test save path generation."""
        save_dir = tmp_path / "saves"
        save_system = SaveSystem(save_dir)
        
        for slot in range(10):
            path = save_system.get_save_path(slot)
            assert path == save_dir / f"save_{slot}.json"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
