"""Exception classes for git_dungeon."""

class GitError(Exception):
    """Base exception for git-related errors."""
    pass


class GameError(Exception):
    """Base exception for game errors."""
    pass


class ResourceLimitError(Exception):
    """Exception for resource limit exceeded."""
    pass


class ParseError(Exception):
    """Exception for parsing errors."""
    pass
