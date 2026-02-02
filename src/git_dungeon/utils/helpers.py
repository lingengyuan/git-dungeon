"""Utility functions and helpers."""

import logging
import sys
from pathlib import Path
from typing import Callable, TypeVar


# Type variable for generic functions
T = TypeVar("T")


def setup_logger(name: str = "git-dungeon") -> logging.Logger:
    """Set up and return a logger."""
    logger = logging.getLogger(name)

    # Set level based on environment
    log_level = logging.DEBUG if "--verbose" in sys.argv else logging.INFO
    logger.setLevel(log_level)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    if not logger.handlers:
        logger.addHandler(handler)

    return logger


def clamp(value: T, min_value: T, max_value: T) -> T:
    """Clamp a value between min and max."""
    return max(min_value, min(value, max_value))


def format_number(n: int) -> str:
    """Format a number with commas."""
    return f"{n:,}"


def truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to max length."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def safe_call(func: Callable[..., T], default: T, *args, **kwargs) -> T:
    """Safely call a function, returning default on exception."""
    try:
        return func(*args, **kwargs)
    except Exception:
        return default
