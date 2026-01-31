"""Git parser for reading commit history."""

import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from git import Repo, Commit as GitCommit
from git.exc import InvalidGitRepositoryError, GitCommandError

from ..config import GameConfig, Difficulty
from ..utils.exceptions import GitError, ResourceLimitError, ParseError
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class FileChange:
    """Represents a file change in a commit."""

    filepath: str
    change_type: str  # 'A', 'M', 'D', 'R'
    additions: int
    deletions: int
    old_path: Optional[str] = None


@dataclass
class CommitInfo:
    """Represents parsed commit information for the game."""

    hash: str
    short_hash: str
    message: str
    author: str
    author_email: str
    datetime: datetime
    additions: int
    deletions: int
    files_changed: int
    file_changes: list[FileChange] = field(default_factory=list)
    is_merge: bool = False
    is_revert: bool = False
    branches: list[str] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        """Total lines changed."""
        return self.additions + self.deletions

    @property
    def difficulty_factor(self) -> float:
        """Calculate difficulty factor based on changes."""
        # More changes = harder
        base = 1.0
        if self.additions > 100:
            base += 0.5
        if self.deletions > 50:
            base += 0.3
        if self.is_merge:
            base += 0.2
        if self.is_revert:
            base += 0.5
        return base

    def get_creature_name(self) -> str:
        """Generate a creature name from commit message."""
        # Extract key words from commit message
        words = self.message.split()

        # Filter out common prefixes
        prefixes = ["feat:", "fix:", "docs:", "style:", "refactor:", "test:", "chore:"]
        filtered = [w for w in words if w not in prefixes and not w.startswith("#")]

        if filtered:
            # Use first meaningful word or two
            name = filtered[0].capitalize()
            if len(filtered) > 1 and len(filtered[1]) > 3:
                name += " " + filtered[1].capitalize()
        else:
            name = f"Commit_{self.short_hash[:6]}"

        return name


class GitParser:
    """Parser for Git repositories."""

    def __init__(self, config: Optional[GameConfig] = None):
        """Initialize the Git parser.

        Args:
            config: Game configuration
        """
        self.config = config or GameConfig()
        self._repo: Optional[Repo] = None
        self._commits_cache: list[CommitInfo] = []

    @property
    def is_loaded(self) -> bool:
        """Check if repository is loaded."""
        return self._repo is not None

    def load_repository(self, path: str) -> None:
        """Load a Git repository.

        Args:
            path: Path to the repository

        Raises:
            GitError: If repository cannot be loaded
            ResourceLimitError: If repository is too large
        """
        try:
            repo_path = Path(path).resolve()

            # Check if directory exists
            if not repo_path.exists():
                raise GitError(f"Repository path does not exist: {path}")

            # Check if it's a Git repository
            if not (repo_path / ".git").exists():
                # Try to initialize
                try:
                    self._repo = Repo.init(str(repo_path))
                    logger.info(f"Initialized new Git repository at {path}")
                except Exception as e:
                    raise GitError(f"Failed to initialize repository: {e}")
            else:
                self._repo = Repo(str(repo_path))

            # Check repository size
            if self._is_too_large():
                raise ResourceLimitError(
                    f"Repository is too large. "
                    f"Max commits: {self.config.max_commits}"
                )

            logger.info(f"Loaded repository at {path}")

        except InvalidGitRepositoryError as e:
            raise GitError(f"Invalid Git repository: {e}")

    def _is_too_large(self) -> bool:
        """Check if repository has too many commits."""
        if self._repo is None:
            return False

        try:
            total_commits = len(list(self._repo.iter_commits("--all")))
            return total_commits > self.config.max_commits * 2  # Allow some buffer
        except Exception:
            return False

    def parse_commit(self, commit: GitCommit) -> CommitInfo:
        """Parse a single Git commit.

        Args:
            commit: GitPython Commit object

        Returns:
            Parsed CommitInfo
        """
        try:
            # Get commit message
            message = commit.message.strip()

            # Get author info
            author = commit.author.name if commit.author else "Unknown"
            author_email = commit.author.email if commit.author else ""

            # Get file changes
            file_changes = self._get_file_changes(commit)

            # Calculate totals
            additions = sum(fc.additions for fc in file_changes)
            deletions = sum(fc.deletions for fc in file_changes)

            # Detect merge commit
            is_merge = len(commit.parents) > 1

            # Detect revert commit
            is_revert = message.lower().startswith("revert")

            # Get branches containing this commit
            branches = self._get_branches(commit)

            return CommitInfo(
                hash=commit.hexsha,
                short_hash=commit.hexsha[:8],
                message=message,
                author=author,
                author_email=author_email,
                datetime=commit.committed_datetime,
                additions=additions,
                deletions=deletions,
                files_changed=len(file_changes),
                file_changes=file_changes,
                is_merge=is_merge,
                is_revert=is_revert,
                branches=branches,
            )

        except Exception as e:
            raise ParseError(f"Failed to parse commit: {e}")

    def _get_file_changes(self, commit: GitCommit) -> list[FileChange]:
        """Get file changes for a commit.

        Args:
            commit: GitPython Commit object

        Returns:
            List of FileChange objects
        """
        file_changes = []

        try:
            # Get diff - try multiple methods
            diffs = commit.diff(commit.parents[0]) if commit.parents else []

            for diff in diffs:
                # Determine change type
                if diff.new_file:
                    change_type = "A"  # Added
                elif diff.deleted_file:
                    change_type = "D"  # Deleted
                elif diff.renamed_file:
                    change_type = "R"  # Renamed
                else:
                    change_type = "M"  # Modified

                # Parse diff - count lines from diff content
                insertions = 0
                deletions = 0

                if hasattr(diff, 'diff') and diff.diff:
                    try:
                        diff_bytes = diff.diff
                        if isinstance(diff_bytes, bytes):
                            diff_bytes = diff_bytes.decode('utf-8', errors='ignore')
                        insertions = diff_bytes.count('\n+')
                        deletions = diff_bytes.count('\n-')
                    except Exception:
                        pass

                # If no diff content, use default values
                if insertions == 0 and deletions == 0:
                    insertions = 1  # Default minimal change

                file_change = FileChange(
                    filepath=diff.b_path or diff.a_path or "unknown",
                    change_type=change_type,
                    additions=insertions,
                    deletions=deletions,
                    old_path=diff.a_path if change_type == "R" else None,
                )
                file_changes.append(file_change)

                # Limit files per commit
                if len(file_changes) >= self.config.max_files_per_commit:
                    logger.warning(
                        f"Limiting files to {self.config.max_files_per_commit} "
                        f"in commit {commit.hexsha[:8]}"
                    )
                    break

        except Exception as e:
            logger.warning(f"Failed to get file changes: {e}")

        return file_changes

    def _get_branches(self, commit: GitCommit) -> list[str]:
        """Get branches containing this commit.

        Args:
            commit: GitPython Commit object

        Returns:
            List of branch names
        """
        if self._repo is None:
            return []

        branches = []
        try:
            for branch in self._repo.branches:
                if branch.commit == commit:
                    branches.append(branch.name)
        except Exception:
            pass

        return branches

    def get_commit_history(
        self,
        limit: Optional[int] = None,
        reverse: bool = False,
    ) -> list[CommitInfo]:
        """Get commit history.

        Args:
            limit: Maximum number of commits to return
            reverse: If True, return from oldest to newest

        Returns:
            List of CommitInfo objects
        """
        if self._repo is None:
            raise GitError("Repository not loaded. Call load_repository first.")

        # Get branch name or use HEAD
        try:
            branch_name = self._repo.active_branch.name
        except TypeError:
            # No branch (bare repo or detached HEAD)
            branch_name = "HEAD"

        # Get commits from the branch
        try:
            commits = list(self._repo.iter_commits(branch_name, max_count=limit or 1000))
        except Exception:
            # Fallback: try --all
            commits = list(self._repo.iter_commits("--all", max_count=limit or 1000))

        # Parse commits
        commit_infos = [self.parse_commit(c) for c in commits]

        # Reverse if needed (oldest first)
        if reverse:
            commit_infos = commit_infos[::-1]

        return commit_infos

    def get_latest_commit(self) -> Optional[CommitInfo]:
        """Get the latest commit.

        Returns:
            Latest CommitInfo or None
        """
        commits = self.get_commit_history(limit=1)
        return commits[0] if commits else None

    def get_commit_by_hash(self, short_hash: str) -> Optional[CommitInfo]:
        """Get a commit by short hash.

        Args:
            short_hash: 8-character commit hash

        Returns:
            CommitInfo or None
        """
        if self._repo is None:
            return None

        try:
            # Try to find commit
            for commit in self._repo.iter_commits("--all"):
                if commit.hexsha.startswith(short_hash):
                    return self.parse_commit(commit)
        except Exception as e:
            logger.warning(f"Failed to find commit {short_hash}: {e}")

        return None

    def close(self) -> None:
        """Close the repository."""
        self._repo = None
        self._commits_cache.clear()

    def __enter__(self) -> "GitParser":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()


def parse_commit_info(
    repo_path: str,
    config: Optional[GameConfig] = None,
    limit: int = 1000,
) -> list[CommitInfo]:
    """Convenience function to parse commit history.

    Args:
        repo_path: Path to repository
        config: Game configuration
        limit: Maximum commits to parse

    Returns:
        List of CommitInfo objects
    """
    parser = GitParser(config)
    try:
        parser.load_repository(repo_path)
        return parser.get_commit_history(limit=limit)
    finally:
        parser.close()
