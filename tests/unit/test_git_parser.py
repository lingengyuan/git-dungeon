"""Unit tests for git_parser module."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.core.git_parser import GitParser, CommitInfo, FileChange
from src.core.character import CharacterComponent, CharacterType


class TestCommitInfo:
    """Tests for CommitInfo dataclass."""

    def test_total_changes(self):
        """Test total_changes calculation."""
        commit = CommitInfo(
            hash="abc123",
            short_hash="abc12345",
            message="Test commit",
            author="Test",
            author_email="test@example.com",
            datetime=None,  # type: ignore
            additions=100,
            deletions=50,
            files_changed=5,
            file_changes=[],
        )

        assert commit.total_changes == 150

    def test_difficulty_factor(self):
        """Test difficulty_factor calculation."""
        # Normal commit
        normal = CommitInfo(
            hash="abc",
            short_hash="abc",
            message="Fix bug",
            author="Test",
            author_email="test@example.com",
            datetime=None,  # type: ignore
            additions=10,
            deletions=5,
            files_changed=2,
            file_changes=[],
        )
        assert normal.difficulty_factor == 1.0

        # Large commit with merge
        large = CommitInfo(
            hash="def",
            short_hash="def",
            message="Merge branch",
            author="Test",
            author_email="test@example.com",
            datetime=None,  # type: ignore
            additions=150,
            deletions=80,
            files_changed=10,
            is_merge=True,
        )
        assert large.difficulty_factor == 2.0  # 1.0 + 0.5 (additions) + 0.3 (deletions) + 0.2 (merge)

    def test_get_creature_name(self):
        """Test creature name generation."""
        commit = CommitInfo(
            hash="abc",
            short_hash="abc",
            message="feat: Add new feature",
            author="Test",
            author_email="test@example.com",
            datetime=None,  # type: ignore
            additions=10,
            deletions=5,
            files_changed=2,
            file_changes=[],
        )

        name = commit.get_creature_name()
        assert "Add" in name or "feature" in name


class TestGitParser:
    """Tests for GitParser class."""

    def test_init_with_default_config(self):
        """Test initialization with default config."""
        parser = GitParser()
        assert parser._repo is None
        assert parser._commits_cache == []

    def test_init_with_custom_config(self):
        """Test initialization with custom config."""
        from src.config.settings import GameConfig

        config = GameConfig(max_commits=500)
        parser = GitParser(config)
        assert parser.config.max_commits == 500

    def test_is_loaded_property(self):
        """Test is_loaded property."""
        parser = GitParser()
        assert parser.is_loaded is False

    @patch("src.core.git_parser.Repo")
    def test_load_repository_success(self, mock_repo_class):
        """Test successful repository loading."""
        # Setup mock
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.iter_commits.return_value = []

        parser = GitParser()
        parser.load_repository(".")

        assert parser.is_loaded is True
        assert parser._repo == mock_repo

    def test_load_repository_not_exists(self):
        """Test loading non-existent repository."""
        parser = GitParser()

        with pytest.raises(Exception):  # GitError
            parser.load_repository("/nonexistent/path")

    def test_parse_commit_message_handling(self):
        """Test commit message parsing."""
        parser = GitParser()

        # Create a mock commit
        mock_commit = MagicMock()
        mock_commit.hexsha = "abc123def456"
        mock_commit.message = "   Test commit message   "
        mock_commit.author.name = "Test Author"
        mock_commit.author.email = "test@example.com"
        mock_commit.committed_datetime = None  # type: ignore
        mock_commit.diff.return_value = []
        mock_commit.parents = []

        result = parser.parse_commit(mock_commit)

        assert result.message == "Test commit message"
        assert result.author == "Test Author"


class TestFileChange:
    """Tests for FileChange dataclass."""

    def test_file_change_creation(self):
        """Test FileChange creation."""
        fc = FileChange(
            filepath="src/main.py",
            change_type="M",
            additions=10,
            deletions=5,
        )

        assert fc.filepath == "src/main.py"
        assert fc.change_type == "M"
        assert fc.additions == 10
        assert fc.deletions == 5
