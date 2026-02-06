"""Configuration and settings management."""

from pathlib import Path
from typing import Optional
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class Difficulty(Enum):
    """Game difficulty levels."""

    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    HARDCORE = "harcore"


class GameConfig(BaseModel):
    """Game configuration."""
    model_config = ConfigDict(env_prefix="GIT_DUNGEON_")

    # Base settings
    repo_path: str = "./"
    save_dir: Optional[str] = None
    difficulty: Difficulty = Difficulty.NORMAL

    # Resource limits
    max_commits: int = Field(default=1000, ge=1, le=10000)
    max_files_per_commit: int = Field(default=50, ge=1, le=1000)
    max_commit_message_len: int = Field(default=500, ge=1, le=10000)
    max_memory_mb: int = Field(default=100, ge=10, le=1000)
    cache_size: int = Field(default=100, ge=10, le=1000)
    chunk_size: int = Field(default=100, ge=10, le=1000)

    # Game settings
    auto_save: bool = True
    auto_save_interval: int = Field(default=10, ge=1, le=100)
    show_combat_log: bool = True
    enable_sound: bool = True

    # Theme
    theme: str = "default"


def load_config(config_path: Optional[Path] = None) -> GameConfig:
    """Load configuration from file or use defaults."""
    if config_path and config_path.exists():
        import toml

        config_data = toml.load(config_path)
        return GameConfig(**config_data)

    return GameConfig()


# Default configuration instance
DEFAULT_CONFIG = GameConfig()
