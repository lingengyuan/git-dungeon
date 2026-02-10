#!/usr/bin/env python3
"""Git Dungeon - Main entry point."""

import sys
import json
import logging
from pathlib import Path
from typing import Optional
from importlib.metadata import PackageNotFoundError, version


def _get_version() -> str:
    try:
        return version("git-dungeon")
    except PackageNotFoundError:
        return "0.0.0+dev"


__version__ = _get_version()


def _setup_src_path() -> None:
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

    def __init__(self, filename: str, mode: str = 'a', encoding: Optional[str] = None, delay: bool = False) -> None:
        super().__init__(filename, mode, encoding, delay)
        # Create a standard formatter for timestamp formatting
        self._time_formatter = logging.Formatter("%(asctime)s", datefmt="%Y-%m-%dT%H:%M:%S")

    def emit(self, record: logging.LogRecord) -> None:
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
                log_entry["exception"] = super().formatException(record.exc_info)

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
    compact: bool = False,
    log_file: Optional[str] = None,
    json_log: Optional[str] = None,
    no_color: bool = False,
    auto: bool = False,
    metrics_out: Optional[str] = None,
    print_metrics: bool = False,
    lang: str = "en",
    ai: str = "off",
    ai_provider: str = "mock",
    ai_model: Optional[str] = None,
    ai_cache: str = ".git_dungeon_cache",
    ai_timeout: int = 5,
    ai_prefetch: str = "chapter",
    content_pack: Optional[list[str]] = None,
    mutator: str = "none",
    daily: bool = False,
    daily_date: Optional[str] = None,
) -> int:
    """Run the CLI game."""
    from git_dungeon.engine.daily import resolve_run_seed
    # Add src to path for imports
    src_path = Path(__file__).parent
    project_root = src_path.parent.parent
    
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    from git_dungeon.i18n import normalize_lang
    lang = normalize_lang(lang)

    log_level = logging.DEBUG if verbose else logging.INFO
    logger = setup_logging(log_level, log_file, json_log, no_color)
    logger.info(f"Starting Git Dungeon v{__version__}")
    effective_seed, daily_info = resolve_run_seed(seed=seed, daily=daily, daily_date=daily_date)
    if daily_info:
        logger.info(f"Daily challenge active: date={daily_info.date_iso} seed={daily_info.seed}")
    
    try:
        if ai == "on":
            from git_dungeon.main_cli_ai import GitDungeonAICLI
            game = GitDungeonAICLI(
                seed=effective_seed,
                verbose=verbose,
                compact=compact,
                auto_mode=auto,
                metrics_out=metrics_out,
                print_metrics=print_metrics,
                lang=lang,
                content_pack_args=content_pack,
                mutator=mutator,
                daily_info=daily_info,
                ai_enabled=True,
                ai_provider=ai_provider,
                ai_model=ai_model,
                ai_cache_dir=ai_cache,
                ai_timeout=ai_timeout,
                ai_prefetch=ai_prefetch,
            )
        else:
            from git_dungeon.main_cli import GitDungeonCLI
            game = GitDungeonCLI(
                seed=effective_seed,
                verbose=verbose,
                compact=compact,
                auto_mode=auto,
                metrics_out=metrics_out,
                print_metrics=print_metrics,
                lang=lang,
                content_pack_args=content_pack,
                mutator=mutator,
                daily_info=daily_info,
            )
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


def main() -> int:
    """Main entry point for CLI."""
    import argparse
    from git_dungeon.main_cli_ai import add_ai_args
    
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
    parser.add_argument("--compact", action="store_true",
                        help="Compact one-line combat summaries")
    parser.add_argument("--version", action="version",
                        version=f"Git Dungeon {__version__}")
    parser.add_argument("--no-color", action="store_true",
                        help="Disable colored output")
    parser.add_argument("--log-file", type=str, default=None,
                        help="Write plain text log to file")
    parser.add_argument("--json-log", type=str, default=None,
                        help="Write JSON log to file (JSONL format)")
    parser.add_argument("--auto", action="store_true",
                        help="Auto-battle mode (automatic combat)")
    parser.add_argument("--metrics-out", type=str, default=None,
                        help="Write gameplay metrics to JSON")
    parser.add_argument("--print-metrics", action="store_true",
                        help="Print gameplay metrics summary")
    parser.add_argument(
        "--content-pack",
        action="append",
        default=[],
        help="Content pack id/path (repeatable). Also supports GIT_DUNGEON_CONTENT_DIR",
    )
    parser.add_argument(
        "--mutator",
        type=str,
        default="none",
        choices=["none", "hard"],
        help="Gameplay mutator preset",
    )
    parser.add_argument("--daily", action="store_true",
                        help="Use daily challenge seed based on date")
    parser.add_argument("--daily-date", type=str, default=None,
                        help="Daily challenge date (YYYY-MM-DD)")
    parser.add_argument("--lang", "-l", type=str, default="en",
                        choices=["en", "zh", "zh_CN"],
                        help="Language (en/zh_CN, zh alias)")
    add_ai_args(parser)
    
    args = parser.parse_args()
    
    if not args.repository:
        parser.print_help()
        print("\nExamples:")
        print("  git-dungeon .                    # Local repo")
        print("  git-dungeon username/repo        # GitHub repo")
        print("  git-dungeon . --seed 12345       # With seed")
        print("  git-dungeon . --auto             # Auto-battle")
        print("  git-dungeon . --auto --compact   # Compact auto battle logs")
        print("  git-dungeon . --auto --metrics-out run_metrics.json")
        print("  git-dungeon . --daily --mutator hard")
        print("  git-dungeon . --content-pack content_packs/example_pack")
        print("  git-dungeon . --ai=on --ai-provider=mock")
        print("  git-dungeon . --json-log run.jsonl  # JSON logging")
        return 0
    
    return run_cli(
        repository=args.repository,
        seed=args.seed,
        verbose=args.verbose,
        compact=args.compact,
        log_file=args.log_file,
        json_log=args.json_log,
        no_color=args.no_color,
        auto=args.auto,
        metrics_out=args.metrics_out,
        print_metrics=args.print_metrics,
        lang=args.lang,
        ai=args.ai,
        ai_provider=args.ai_provider,
        ai_model=args.ai_model,
        ai_cache=args.ai_cache,
        ai_timeout=args.ai_timeout,
        ai_prefetch=args.ai_prefetch,
        content_pack=args.content_pack,
        mutator=args.mutator,
        daily=args.daily,
        daily_date=args.daily_date,
    )


if __name__ == "__main__":
    sys.exit(main())
