"""Pixel UI entrypoints for Git Dungeon."""

__all__ = ["run"]


def run(*args, **kwargs):
    """Import lazily so CLI installs do not require pygame."""
    from git_dungeon.ui_pixel.app import run as _run

    return _run(*args, **kwargs)
