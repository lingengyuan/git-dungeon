#!/usr/bin/env python3
"""Git Dungeon - Main entry point."""

import sys
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

__version__ = "1.0.0"


def _setup_src_path():
    """Ensure imports work from anywhere."""
    try:
        import git_dungeon
        # git_dungeon is in src/git_dungeon/, so grandparent is project root
        project_root = Path(git_dungeon.__file__).parent.parent.parent
        
        # Add project root to path (contains src/)
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
    except Exception:
        pass


# Setup path BEFORE any other imports that might need it
_setup_src_path()


class JsonFileHandler(logging.FileHandler):
    """File handler that writes JSONL format."""
    
    def __init__(self, filename, mode='a', encoding=None, delay=False):
        super().__init__(filename, mode, encoding, delay)
        # Create a standard formatter for timestamp formatting
        self._time_formatter = logging.Formatter("%(asctime)s", datefmt="%Y-%m-%dT%H:%M:%S")
    
    def emit(self, record: logging.LogRecord):
        """Emit a JSON log line."""
        try:
            log_entry = {
                "timestamp": self._time_formatter.format(record),
                "level": record.levelname,
                "name": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }
            # Add extra fields if present
            if hasattr(record, 'data') and record.data:
                log_entry["data"] = record.data
            # Add exception info if present
            if record.exc_info:
                log_entry["exception"] = self.formatException(record.exc_info)
            
            self.stream.write(json.dumps(log_entry) + "\n")
            self.flush()
        except Exception:
            self.handleError(record)


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    json_log: Optional[str] = None,
    no_color: bool = False
) -> logging.Logger:
    """Set up logging configuration."""
    logger = logging.getLogger("git-dungeon")
    logger.setLevel(level)
    logger.handlers.clear()
    
    # Formatter
    if no_color:
        fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    else:
        fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    formatter = logging.Formatter(fmt, datefmt="%H:%M:%S")
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # JSON log handler (JSONL format)
    if json_log:
        json_handler = JsonFileHandler(json_log)
        json_handler.setLevel(level)
        logger.addHandler(json_handler)
    
    # File handler (plain text)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def run_cli(
    repository: str,
    seed: Optional[int] = None,
    verbose: bool = False,
    log_file: Optional[str] = None,
    json_log: Optional[str] = None,
    no_color: bool = False,
    auto: bool = False
):
    """Run the CLI game."""
    from git_dungeon.main_cli import GitDungeonCLI
    
    log_level = logging.DEBUG if verbose else logging.INFO
    logger = setup_logging(log_level, log_file, json_log, no_color)
    logger.info(f"Starting Git Dungeon v{__version__}")
    
    try:
        game = GitDungeonCLI(seed=seed, verbose=verbose, auto_mode=auto)
        success = game.start(repository)
        logger.info(f"Game ended with success={success}")
        return 0 if success else 1
    except KeyboardInterrupt:
        logger.info("User interrupted")
        return 130
    except Exception as e:
        logger.error(f"Game error: {e}", exc_info=verbose)
        if not verbose:
            print(f"Error: {e}", file=sys.stderr)
            print("Run with --verbose for details", file=sys.stderr)
        return 1


def main():
    """Main entry point for CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Git Dungeon - Battle through your commits!",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("repository", nargs="?", default=None,
                        help="Repository path or user/repo")
    parser.add_argument("--seed", "-s", type=int, default=None,
                        help="Random seed for reproducibility")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose output")
    parser.add_argument("--version", action="version",
                        version=f"Git Dungeon {__version__}")
    parser.add_argument("--no-color", action="store_true",
                        help="Disable colored output")
    parser.add_argument("--log-file", type=str, default=None,
                        help="Write plain text log to file")
    parser.add_argument("--json-log", type=str, default=None,
                        help="Write JSON log to file (JSONL format)")
    parser.add_argument("--auto", "-a", action="store_true",
                        help="Auto-battle mode (automatic combat)")
    
    args = parser.parse_args()
    
    if not args.repository:
        parser.print_help()
        print("\nExamples:")
        print("  git-dungeon .                    # Local repo")
        print("  git-dungeon username/repo        # GitHub repo")
        print("  git-dungeon . --seed 12345       # With seed")
        print("  git-dungeon . --auto             # Auto-battle")
        print("  git-dungeon . --json-log run.jsonl  # JSON logging")
        return 0
    
    return run_cli(
        repository=args.repository,
        seed=args.seed,
        verbose=args.verbose,
        log_file=args.log_file,
        json_log=args.json_log,
        no_color=args.no_color,
        auto=args.auto
    )


if __name__ == "__main__":
    sys.exit(main())
