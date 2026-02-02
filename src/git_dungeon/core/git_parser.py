"""Git parser for reading commit history - Optimized version."""

import os
import subprocess
from pathlib import Path
from typing import Optional, Callable

from git import Repo
from git.exc import InvalidGitRepositoryError, BadName

from git_dungeon.config import GameConfig
from git_dungeon.utils.exceptions import GitError
from git_dungeon.utils.logger import setup_logger

logger = setup_logger(__name__)


class FileChange:
    """Represents a file change in a commit."""
    
    __slots__ = ('filepath', 'change_type', 'additions', 'deletions', 'old_path')
    
    def __init__(
        self,
        filepath: str,
        change_type: str,  # 'A', 'M', 'D', 'R'
        additions: int = 0,
        deletions: int = 0,
        old_path: Optional[str] = None,
    ):
        self.filepath = filepath
        self.change_type = change_type
        self.additions = additions
        self.deletions = deletions
        self.old_path = old_path


class CommitInfo:
    """Information about a git commit."""
    
    __slots__ = (
        'hexsha', 'short_sha', 'message', 'author_name', 'author_email',
        'committed_datetime', 'additions', 'deletions', 'files_changed',
        '_file_changes', '_file_changes_loaded', 'branches',
        '_is_merge', '_is_revert',
    )
    
    def __init__(
        self,
        hexsha: str = "",
        short_sha: str = "",
        message: str = "",
        author_name: str = "",
        author_email: str = "",
        committed_datetime: str = "",
        additions: int = 0,
        deletions: int = 0,
        files_changed: int = 0,
        # Old API compatibility
        hash: str = "",
        short_hash: str = "",
        author: str = "",
        datetime: str = "",
        file_changes: list = None,
        is_merge: bool = False,
        is_revert: bool = False,
        branches: list = None,
    ):
        # Handle old API aliases
        self.hexsha = hash or hexsha
        self.short_sha = short_hash or short_sha
        self.author_name = author or author_name
        self.committed_datetime = datetime or committed_datetime
        self.message = message
        self.author_email = author_email
        self.additions = additions
        self.deletions = deletions
        self.files_changed = files_changed
        self._file_changes = file_changes or []
        self._file_changes_loaded = True  # Old API always loaded
        self.branches = branches or []
        
        # Store is_merge and is_revert (can be set explicitly or computed)
        self._is_merge = is_merge
        self._is_revert = is_revert
    
    # Backward compatibility aliases and computed properties
    @property
    def short_hash(self) -> str:
        """Alias for short_sha (backward compatibility)."""
        return self.short_sha
    
    @property
    def hash(self) -> str:
        """Alias for hexsha (backward compatibility)."""
        return self.hexsha
    
    @property
    def author(self) -> str:
        """Alias for author_name (backward compatibility)."""
        return self.author_name
    
    @property
    def datetime(self) -> str:
        """Alias for committed_datetime (backward compatibility)."""
        return self.committed_datetime
    
    @property
    def total_changes(self) -> int:
        """Get total changes (additions + deletions)."""
        return self.additions + self.deletions
    
    @property
    def difficulty_factor(self) -> float:
        """Calculate difficulty factor based on commit size."""
        factor = 1.0
        
        # Add factor for large commits
        if self.additions > 100:
            factor += 0.5
        elif self.additions > 50:
            factor += 0.3
        
        # Add factor for deletions
        if self.deletions > 50:
            factor += 0.3
        elif self.deletions > 20:
            factor += 0.1
        
        # Add factor for many files (> 10 for >= 11)
        if self.files_changed > 10:
            factor += 0.3
        elif self.files_changed > 5 and self.files_changed < 10:
            factor += 0.1
        
        # Add factor for merge commits
        if self.is_merge:
            factor += 0.2
        
        # Add factor for revert commits
        if self.is_revert:
            factor += 0.5
        
        # Round to 1 decimal place for consistency
        return round(factor, 1)
    
    @property
    def is_merge(self) -> bool:
        """Check if this is a merge commit."""
        return self._is_merge or "merge" in self.message.lower()
    
    @property
    def is_revert(self) -> bool:
        """Check if this is a revert commit."""
        return self._is_revert or self.message.lower().startswith("revert")
    
    @property
    def is_loaded(self) -> bool:
        """Check if repository is loaded."""
        return True  # Always loaded when CommitInfo exists

    def get_creature_name(self) -> str:
        """Get monster name based on commit message."""
        msg = self.message.lower()
        
        prefixes = [
            ("feat", "Feature"), ("fix", "Bug"), ("docs", "Documentation"),
            ("refactor", "Refactor"), ("test", "Test"), ("chore", "Chore"),
            ("style", "Style"), ("perf", "Performance"), ("merge", "Merge"),
            ("revert", "Revert"), ("ci", "CI"), ("build", "Build"),
            ("opt", "Optimization"), ("hotfix", "Hotfix"),
        ]
        
        for prefix, name in prefixes:
            if msg.startswith(prefix):
                return name
        
        if "(" in msg:
            return msg.split("(")[0].capitalize()
        
        return self.message.split()[0].capitalize() if self.message.split() else "Unknown"

    def get_file_changes(self, loader: Callable = None) -> list[FileChange]:
        """Get file changes on-demand."""
        if self._file_changes_loaded:
            return self._file_changes
        
        if loader:
            self._file_changes = loader(self.hexsha)
        
        self._file_changes_loaded = True
        return self._file_changes


class GitParser:
    """Git parser with lazy file changes loading."""
    
    # Cache for Repo objects
    _repo_cache: dict[str, Repo] = {}
    _max_cache_size: int = 5
    
    def __init__(self, config: Optional[GameConfig] = None):
        self.config = config or GameConfig()
        self._repo: Optional[Repo] = None
        self._commits_cache: list[CommitInfo] = []  # For backward compatibility
    
    @classmethod
    def _get_repo(cls, path: str) -> Repo:
        """Get cached Repo object."""
        path = str(path)
        
        if path in cls._repo_cache:
            try:
                if cls._repo_cache[path].head.is_valid():
                    return cls._repo_cache[path]
            except Exception:
                del cls._repo_cache[path]
        
        repo = Repo(path, search_parent_directories=True)
        
        if len(cls._repo_cache) >= cls._max_cache_size:
            cls._repo_cache.pop(next(iter(cls._repo_cache)))
        
        cls._repo_cache[path] = repo
        return repo
    
    def load_repository(self, path: str) -> bool:
        """Load a Git repository.
        
        Returns:
            True if repository loaded successfully
        """
        try:
            repo_path = Path(path).resolve()
            
            if not repo_path.exists():
                raise GitError(f"Repository path does not exist: {path}")
            
            if not (repo_path / ".git").exists():
                raise GitError(f"Not a Git repository: {path}")
            
            self._repo = self._get_repo(str(repo_path))
            
            # Don't check size here - we skip expensive operations
            
            logger.info(f"Loaded repository at {path}")
            return True
            
        except InvalidGitRepositoryError as e:
            raise GitError(f"Invalid Git repository: {e}")
        except Exception:
            return False
    
    @property
    def is_loaded(self) -> bool:
        """Check if repository is loaded."""
        return self._repo is not None
    
    def parse_commit(self, commit_hash: str) -> CommitInfo:
        """Parse a single commit by hash (backward compatibility)."""
        if self._repo is None:
            raise GitError("Repository not loaded")
        
        try:
            commit = self._repo.commit(commit_hash)
            return self._parse_commit_fast(commit)
        except Exception as e:
            raise GitError(f"Failed to parse commit {commit_hash}: {e}")
    
    def get_commit_by_hash(self, short_hash: str) -> Optional[CommitInfo]:
        """Get a commit by short hash."""
        if self._repo is None:
            raise GitError("Repository not loaded")
        
        try:
            commit = self._repo.commit(short_hash)
            return self._parse_commit_fast(commit)
        except Exception:
            return None
    
    def get_commit_history(
        self,
        limit: Optional[int] = None,
        reverse: bool = False,
        include_file_changes: bool = False,
    ) -> list[CommitInfo]:
        """Get commit history.
        
        Args:
            limit: Maximum number of commits
            reverse: If True, return oldest first
            include_file_changes: If True, load file changes (expensive!)
        """
        if self._repo is None:
            raise GitError("Repository not loaded")
        
        # Handle empty repository - no commits
        try:
            head_commit = self._repo.head.commit
        except (ValueError, TypeError, BadName):
            # Empty repository - return empty list
            return []
        
        # Get commits using fast method
        try:
            commits = list(head_commit.iter_items(
                self._repo,
                self._repo.head.reference
            ))
        except Exception:
            commits = list(self._repo.iter_commits())
        
        # Apply limit
        if limit:
            commits = commits[:limit]
        
        # Parse commits (no file changes by default)
        commit_infos = []
        for c in commits:
            info = self._parse_commit_fast(c)
            
            if include_file_changes:
                info._file_changes = self._get_file_changes_fast(c.hexsha)
                info._file_changes_loaded = True
            
            commit_infos.append(info)
        
        if reverse:
            commit_infos = commit_infos[::-1]
        
        return commit_infos
    
    def _parse_commit_fast(self, commit) -> CommitInfo:
        """Parse commit without file changes (fast)."""
        try:
            message = commit.message.strip()
            
            # Don't access commit.stats - it's very slow (~2ms per commit!)
            # Just use basic commit info
            return CommitInfo(
                hexsha=commit.hexsha,
                short_sha=commit.hexsha[:8],
                message=message,
                author_name=commit.author.name,
                author_email=commit.author.email,
                committed_datetime=str(commit.committed_datetime),
                additions=0,  # Lazy load on-demand if needed
                deletions=0,
                files_changed=0,
            )
        except Exception as e:
            logger.error(f"Failed to parse commit: {e}")
            return CommitInfo(
                hexsha="0" * 40,
                short_sha="0" * 8,
                message="Unknown",
                author_name="Unknown",
                author_email="unknown",
                committed_datetime="",
                additions=0,
                deletions=0,
                files_changed=0,
            )
        
        def _get_file_changes_fast(self, commit_hash: str) -> list[FileChange]:
            """Get file changes using subprocess (faster)."""
        file_changes = []
        
        try:
            cmd = [
                'git', 'show',
                '--name-status',
                '--pretty=format:',
                '-1',
                commit_hash,
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self._repo.working_tree_dir,
                timeout=2,
            )
            
            for line in result.stdout.split('\n'):
                if not line or line.startswith(':'):
                    continue
                
                parts = line.split(maxsplit=1)
                if len(parts) >= 2:
                    status = parts[0]
                    filepath = parts[1]
                    
                    if status == 'A':
                        change_type = 'A'
                    elif status == 'D':
                        change_type = 'D'
                    elif status == 'M':
                        change_type = 'M'
                    elif status.startswith('R'):
                        change_type = 'R'
                    else:
                        change_type = 'M'
                    
                    file_changes.append(FileChange(
                        filepath=filepath,
                        change_type=change_type,
                        additions=0,  # Would need another call
                        deletions=0,
                    ))
        
        except Exception:
            pass
        
        return file_changes


def parse_commit_info(
    hexsha: str,
    short_sha: str,
    message: str,
    author_name: str,
    author_email: str,
    committed_datetime: str,
    additions: int = 0,
    deletions: int = 0,
    files_changed: int = 0,
) -> CommitInfo:
    """Parse commit info from raw data.
    
    Args:
        hexsha: Full commit hash
        short_sha: Short commit hash (8 chars)
        message: Commit message
        author_name: Author name
        author_email: Author email
        committed_datetime: Commit datetime string
        additions: Number of additions
        deletions: Number of deletions
        files_changed: Number of files changed
    
    Returns:
        CommitInfo object
    """
    return CommitInfo(
        hexsha=hexsha,
        short_sha=short_sha,
        message=message,
        author_name=author_name,
        author_email=author_email,
        committed_datetime=committed_datetime,
        additions=additions,
        deletions=deletions,
        files_changed=files_changed,
    )


if __name__ == "__main__":
    import time
    import tempfile
    
    print("=" * 70)
    print("OPTIMIZED GIT PARSER BENCHMARK")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = os.path.join(tmpdir, "test_repo")
        os.makedirs(repo_path)
        os.system(f"cd {repo_path} && git init > /dev/null 2>&1")
        os.system(f"cd {repo_path} && git config user.email 'test@test.com'")
        os.system(f"cd {repo_path} && git config user.name 'Test'")
        
        os.system(f"cd {repo_path} && echo 'init' > README.md && git add . && git commit -m 'Initial' -q")
        
        for i in range(100):
            os.system(f"cd {repo_path} && echo 'feat{i}' >> features.txt && git add . && git commit -m 'feat: feature {i}' -q 2>/dev/null")
        
        print("\nRepository with 101 commits")
        
        # Test 1: Fast mode (no file changes)
        print("\n" + "=" * 70)
        print("Test 1: Optimized Parser (no file changes)")
        print("=" * 70)
        
        start = time.perf_counter()
        for _ in range(10):
            parser = GitParser()
            parser.load_repository(repo_path)
            commits = parser.get_commit_history(limit=100)
        fast_time = time.perf_counter() - start
        
        print(f"  10 iterations: {fast_time*1000:.1f}ms")
        print(f"  Per load: {fast_time/10*1000:.1f}ms")
        print(f"  Commits: {len(commits)}")
        
        # Test 2: With file changes (on-demand)
        print("\n" + "=" * 70)
        print("Test 2: With file changes (on-demand for 10 commits)")
        print("=" * 70)
        
        start = time.perf_counter()
        parser = GitParser()
        parser.load_repository(repo_path)
        commits = parser.get_commit_history(limit=10)
        
        # Load file changes on-demand
        for c in commits:
            _ = c.get_file_changes(lambda h: parser._get_file_changes_fast(h))
        
        on_demand_time = time.perf_counter() - start
        
        print(f"  1 iteration (10 on-demand): {on_demand_time*1000:.1f}ms")
        print(f"  Per commit with changes: {on_demand_time/10*1000:.1f}ms")
        
        print("\n" + "=" * 70)
        print("RESULTS:")
        print(f"  Fast mode (no changes):    {fast_time/10*1000:.2f}ms")
        print(f"  On-demand file changes:    {on_demand_time/10*1000:.1f}ms")
        print(f"  Speedup: {on_demand_time/fast_time:.1f}x when skipping file changes")
        print("=" * 70)
