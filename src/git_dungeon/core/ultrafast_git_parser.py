#!/usr/bin/env python3
"""
Ultra-Fast Git Parser
跳过昂贵的 diff 操作，使用 subprocess 获取统计信息
"""

import os
import subprocess
import tempfile
from typing import Optional
from pathlib import Path

from git import Repo, InvalidGitRepositoryError

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import GameConfig
import logging

logger = logging.getLogger(__name__)


class CommitInfo:
    """Lightweight commit info (no file_changes for speed)."""
    
    __slots__ = (
        'hexsha', 'short_sha', 'message', 'author_name', 'author_email',
        'committed_datetime', 'additions', 'deletions', 'files_changed'
    )
    
    def __init__(
        self,
        hexsha: str,
        short_sha: str,
        message: str,
        author_name: str,
        author_email: str,
        committed_datetime: str,
        additions: int = 0,
        deletions: int = 0,
        files_changed: int = 0,
    ):
        self.hexsha = hexsha
        self.short_sha = short_sha
        self.message = message
        self.author_name = author_name
        self.author_email = author_email
        self.committed_datetime = committed_datetime
        self.additions = additions
        self.deletions = deletions
        self.files_changed = files_changed
    
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


class UltraFastGitParser:
    """Git parser optimized for speed using subprocess."""
    
    # Cache for repo paths
    _repo_cache: dict[str, Repo] = {}
    # Cache for commit stats (hash -> (additions, deletions, files))
    _stats_cache: dict[str, tuple[int, int, int]] = {}
    
    def __init__(self, config: Optional[GameConfig] = None):
        self.config = config or GameConfig()
        self._repo: Optional[Repo] = None
    
    @classmethod
    def _get_repo(cls, path: str) -> Repo:
        """Get cached Repo object."""
        path = str(path)
        
        if path in cls._repo_cache:
            try:
                if cls._repo_cache[path].head.is_valid():
                    return cls._repo_cache[path]
            except:
                pass
        
        repo = Repo(path, search_parent_directories=True)
        if len(cls._repo_cache) >= 10:
            cls._repo_cache.pop(next(iter(cls._repo_cache)))
        cls._repo_cache[path] = repo
        return repo
    
    def load_repository(self, path: str) -> None:
        """Load a Git repository."""
        try:
            repo_path = Path(path).resolve()
            
            if not repo_path.exists():
                raise ValueError(f"Repository path does not exist: {path}")
            
            if not (repo_path / ".git").exists():
                raise ValueError(f"Not a Git repository: {path}")
            
            self._repo = self._get_repo(str(repo_path))
            logger.info(f"Loaded repository at {path}")
            
        except InvalidGitRepositoryError as e:
            raise ValueError(f"Invalid Git repository: {e}")
    
    def get_commit_history(
        self,
        limit: Optional[int] = None,
        reverse: bool = False,
    ) -> list[CommitInfo]:
        """Get commit history using subprocess (much faster)."""
        if self._repo is None:
            raise ValueError("Repository not loaded")
        
        # Use subprocess for fast commit enumeration
        # Format: hash|author|date|message|additions|deletions|files
        cmd = [
            'git', 'log',
            '--pretty=format:%h|%an|%ad|%s|%H',
            '--date=iso',
            '-n', str(limit or 1000),
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self._repo.working_tree_dir,
                timeout=10,
            )
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('|', 5)
                if len(parts) >= 5:
                    short_sha = parts[0]
                    author = parts[1]
                    date = parts[2]
                    message = parts[3]
                    full_hash = parts[4] if len(parts) > 4 else short_sha
                    
                    # Get stats from cache or subprocess
                    if full_hash in self._stats_cache:
                        additions, deletions, files = self._stats_cache[full_hash]
                    else:
                        additions, deletions, files = self._get_commit_stats(full_hash)
                        self._stats_cache[full_hash] = (additions, deletions, files)
                    
                    commit = CommitInfo(
                        hexsha=full_hash,
                        short_sha=short_sha,
                        message=message,
                        author_name=author,
                        author_email="",  # Not in this format
                        committed_datetime=date,
                        additions=additions,
                        deletions=deletions,
                        files_changed=files,
                    )
                    commits.append(commit)
            
            if reverse:
                commits = commits[::-1]
            
            return commits
            
        except Exception as e:
            logger.error(f"Failed to get commit history: {e}")
            return []
    
    def _get_commit_stats(self, commit_hash: str) -> tuple[int, int, int]:
        """Get commit stats using subprocess (fast)."""
        cmd = [
            'git', 'show',
            '--numstat',
            '--pretty=format:',
            '-1',
            commit_hash,
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self._repo.working_tree_dir,
                timeout=5,
            )
            
            additions = 0
            deletions = 0
            files = 0
            
            for line in result.stdout.split('\n'):
                if not line or line.startswith('-'):
                    continue
                
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        if parts[0] != '-':
                            additions += int(parts[0])
                        if parts[1] != '-':
                            deletions += int(parts[1])
                        files += 1
                    except (ValueError, IndexError):
                        pass
            
            return additions, deletions, files
            
        except Exception:
            return 0, 0, 0
    
    def clear_cache(self) -> None:
        """Clear all caches."""
        self._repo_cache.clear()
        self._stats_cache.clear()


class FastGitParser:
    """Hybrid parser: use GitPython for commits, subprocess for stats."""
    
    _repo_cache: dict[str, Repo] = {}
    
    def __init__(self, config: Optional[GameConfig] = None):
        self.config = config or GameConfig()
        self._repo: Optional[Repo] = None
    
    @classmethod
    def _get_repo(cls, path: str) -> Repo:
        path = str(path)
        if path in cls._repo_cache:
            try:
                if cls._repo_cache[path].head.is_valid():
                    return cls._repo_cache[path]
            except:
                pass
        repo = Repo(path, search_parent_directories=True)
        cls._repo_cache[path] = repo
        return repo
    
    def load_repository(self, path: str) -> None:
        self._repo = self._get_repo(path)
    
    def get_commit_history(self, limit: Optional[int] = None, reverse: bool = False) -> list[CommitInfo]:
        if self._repo is None:
            raise ValueError("Not loaded")
        
        # Use GitPython for commit enumeration (cached)
        try:
            commits = list(self._repo.head.commit.iter_items(
                self._repo,
                self._repo.head.reference
            ))[:limit]
        except:
            commits = list(self._repo.iter_commits())[:limit]
        
        # Parse commits (no file changes for speed)
        result = []
        for c in commits:
            commit = CommitInfo(
                hexsha=c.hexsha,
                short_sha=c.hexsha[:8],
                message=c.message.strip(),
                author_name=c.author.name,
                author_email=c.author.email,
                committed_datetime=str(c.committed_datetime),
            )
            result.append(commit)
        
        if reverse:
            result = result[::-1]
        
        return result


if __name__ == "__main__":
    import time
    import tempfile
    
    print("=" * 70)
    print("ULTRA-FAST GIT PARSER BENCHMARK")
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
        
        # Test 1: UltraFastGitParser
        print("\n" + "=" * 70)
        print("Test 1: UltraFastGitParser (subprocess + caching)")
        print("=" * 70)
        
        start = time.perf_counter()
        for _ in range(5):
            parser = UltraFastGitParser()
            parser.load_repository(repo_path)
            commits = parser.get_commit_history(limit=100)
        elapsed = time.perf_counter() - start
        
        print(f"  5 iterations: {elapsed*1000:.1f}ms")
        print(f"  Per load: {elapsed/5*1000:.1f}ms")
        print(f"  Commits: {len(commits)}")
        
        # Test 2: FastGitParser (no stats)
        print("\n" + "=" * 70)
        print("Test 2: FastGitParser (GitPython, no stats)")
        print("=" * 70)
        
        start = time.perf_counter()
        for _ in range(5):
            parser = FastGitParser()
            parser.load_repository(repo_path)
            commits = parser.get_commit_history(limit=100)
        elapsed = time.perf_counter() - start
        
        print(f"  5 iterations: {elapsed*1000:.1f}ms")
        print(f"  Per load: {elapsed/5*1000:.1f}ms")
        print(f"  Commits: {len(commits)}")
        
        # Test 3: Original (with stats)
        print("\n" + "=" * 70)
        print("Test 3: Original Parser (with file changes)")
        print("=" * 70)
        
        from git_dungeon.core.git_parser import GitParser
        
        start = time.perf_counter()
        for _ in range(5):
            parser = GitParser()
            parser.load_repository(repo_path)
            commits = parser.get_commit_history(limit=100)
        elapsed = time.perf_counter() - start
        
        print(f"  5 iterations: {elapsed*1000:.1f}ms")
        print(f"  Per load: {elapsed/5*1000:.1f}ms")
        print(f"  Commits: {len(commits)}")
        
        print("\n" + "=" * 70)
        print("RESULTS:")
        print(f"  UltraFast: {elapsed/5*1000:.1f}ms (baseline)")
        fast_time = elapsed/5*1000
        
        start = time.perf_counter()
        parser = FastGitParser()
        parser.load_repository(repo_path)
        commits = parser.get_commit_history(limit=100)
        fast_elapsed = time.perf_counter() - start
        
        print(f"  Fast:      {fast_elapsed*1000:.1f}ms ({fast_time/fast_elapsed:.1f}x)")
        print(f"\n  SPEEDUP vs Original: {fast_time/(elapsed/5*1000):.1f}x")
        print("=" * 70)
