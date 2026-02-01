"""Logger module."""

import logging
import sys
from typing import Optional

# Default logger instance
_default_logger: Optional[logging.Logger] = None


def setup_logger(
    name: str = "git-dungeon",
    level: int = logging.INFO,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """Set up and return a logger.

    Args:
        name: Logger name
        level: Log level
        log_file: Optional log file path

    Returns:
        Configured logger
    """
    global _default_logger

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(formatter)

    # Add console handler
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _default_logger = logger
    return logger


def get_logger(name: str = "git-dungeon") -> logging.Logger:
    """Get a logger by name.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
