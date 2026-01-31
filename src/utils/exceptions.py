"""Custom exceptions for Git Dungeon."""

from typing import Optional


class GitDungeonError(Exception):
    """Base exception for Git Dungeon."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class GitError(GitDungeonError):
    """Exception for Git-related errors."""

    pass


class ParseError(GitDungeonError):
    """Exception for parsing errors."""

    pass


class ResourceLimitError(GitDungeonError):
    """Exception for resource limit violations."""

    pass


class GameError(GitDungeonError):
    """Exception for game-related errors."""

    pass
