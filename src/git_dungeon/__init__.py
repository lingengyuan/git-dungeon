"""Git Dungeon - A Git commit history based roguelike game."""

__author__ = "OpenClaw"

# Version is now managed in pyproject.toml
# For runtime, use: importlib.metadata.version("git-dungeon")
try:
    from importlib.metadata import version
    __version__ = version("git-dungeon")
except Exception:
    __version__ = "1.2.0+dev"  # Fallback
