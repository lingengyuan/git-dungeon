"""Tests for main.py UI components."""


import pytest

from src.main import GitDungeonApp, InputScreen
from src.core.game_engine import GameState
from src.config.settings import GameConfig


class TestGitDungeonApp:
    """Tests for GitDungeonApp."""

    def test_app_initialization(self):
        """Test app initializes with default config."""
        app = GitDungeonApp()
        assert app.game_state is not None
        assert app._repo_loaded is False

    def test_app_initialization_with_config(self):
        """Test app initializes with custom config."""
        config = GameConfig(repo_path="/test/path")
        app = GitDungeonApp(config=config)
        assert app.game_state.config.repo_path == "/test/path"

    def test_action_pause_toggle(self):
        """Test pause toggle action."""
        app = GitDungeonApp()
        app.game_state.is_paused = False
        
        app.action_pause()
        assert app.game_state.is_paused is True
        
        app.action_pause()
        assert app.game_state.is_paused is False

    def test_repo_loaded_flag(self):
        """Test repo loaded flag management."""
        app = GitDungeonApp()
        assert app._repo_loaded is False
        
        app._repo_loaded = True
        assert app._repo_loaded is True


class TestInputScreen:
    """Tests for InputScreen."""

    def test_screen_initialization(self):
        """Test screen initializes correctly."""
        screen = InputScreen(
            prompt="Enter path:",
        )
        assert screen._prompt == "Enter path:"
        assert screen._on_submit is None
        assert screen._on_cancel is None

    def test_screen_with_callbacks(self):
        """Test screen with submit/cancel callbacks."""
        submit_called = []
        cancel_called = []

        def on_submit(path: str):
            submit_called.append(path)

        def on_cancel():
            cancel_called.append(True)

        screen = InputScreen(
            prompt="Enter path:",
            on_submit=on_submit,
            on_cancel=on_cancel,
        )
        assert screen._on_submit is not None
        assert screen._on_cancel is not None

    def test_screen_compose(self):
        """Test screen composes correctly."""
        screen = InputScreen(prompt="Test")
        # Input attribute is set during compose, but we can verify
        # the screen structure exists
        assert screen._prompt == "Test"


class TestActionLoadRepo:
    """Tests for action_load_repo logic."""

    def test_load_valid_repository(self, tmp_path):
        """Test loading a valid repository."""
        # Create a test git repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        
        import subprocess
        subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, capture_output=True)
        
        with open(repo_path / "test.txt", "w") as f:
            f.write("test")
        subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "test commit"], cwd=repo_path, capture_output=True)
        
        # Test with GameState directly (logic used by app)
        game = GameState()
        result = game.load_repository(str(repo_path))
        
        assert result is True
        assert len(game.commits) >= 1

    def test_load_invalid_repository(self):
        """Test loading invalid repository path."""
        game = GameState()
        result = game.load_repository("/nonexistent/path")
        
        assert result is False
        assert len(game.commits) == 0


class TestActionSave:
    """Tests for action_save logic."""

    def test_save_game_with_repo(self, tmp_path):
        """Test saving game after loading repo."""
        # Create test repo
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        
        import subprocess
        subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, capture_output=True)
        
        with open(repo_path / "test.txt", "w") as f:
            f.write("test")
        subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "test commit"], cwd=repo_path, capture_output=True)
        
        # Load and save
        game = GameState()
        game.load_repository(str(repo_path))
        
        from src.core.save_system import SaveSystem
        save_dir = tmp_path / "saves"
        save_system = SaveSystem(save_dir)
        
        result = save_system.save(game, 0)
        assert result is True
        
        # Verify save file exists
        assert (save_dir / "save_0.json").exists()


class TestGameStateRepository:
    """Tests for GameState repository operations."""

    def test_multiple_commits(self, tmp_path):
        """Test loading repository with multiple commits."""
        repo_path = tmp_path / "multi_commit"
        repo_path.mkdir()
        
        import subprocess
        subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, capture_output=True)
        
        # Create multiple commits
        for i in range(3):
            with open(repo_path / f"file{i}.txt", "w") as f:
                f.write(f"content {i}")
            subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True)
            subprocess.run(["git", "commit", "-m", f"feat: Commit {i}"], cwd=repo_path, capture_output=True)
        
        game = GameState()
        game.load_repository(str(repo_path))
        
        assert len(game.commits) == 3

    def test_defeated_commits(self, tmp_path):
        """Test defeated commits tracking."""
        repo_path = tmp_path / "test"
        repo_path.mkdir()
        
        import subprocess
        subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, capture_output=True)
        
        with open(repo_path / "test.txt", "w") as f:
            f.write("test")
        subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "test commit"], cwd=repo_path, capture_output=True)
        
        game = GameState()
        game.load_repository(str(repo_path))
        
        assert len(game.defeated_commits) == 0
        
        # Simulate defeating a commit
        game.defeated_commits.append(game.commits[0].hash)
        assert len(game.defeated_commits) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
