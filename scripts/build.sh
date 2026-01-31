"""Build script for Git Dungeon."""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], cwd: Path) -> bool:
    """Run a command and return success status."""
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {cmd}")
        print(f"Error: {e}")
        return False


def build() -> bool:
    """Build the project."""
    root = Path(__file__).parent

    # Install dependencies
    print("Installing dependencies...")
    if not run_command([sys.executable, "-m", "pip", "install", "-e", "."], root):
        return False

    print("Build complete!")
    return True


def test() -> bool:
    """Run tests."""
    root = Path(__file__).parent

    print("Running tests...")
    return run_command(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        root,
    )


def lint() -> bool:
    """Run linters."""
    root = Path(__file__).parent

    print("Running linters...")

    # Black
    if not run_command([sys.executable, "-m", "black", "--check", "src/", root]):
        return False

    # Isort
    if not run_command([sys.executable, "-m", "isort", "--check-only", "src/", root]):
        return False

    # Flake8
    if not run_command([sys.executable, "-m", "flake8", "src/", root]):
        return False

    print("Linting complete!")
    return True


def package() -> bool:
    """Package the application."""
    root = Path(__file__).parent

    print("Packaging with PyInstaller...")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name", "git-dungeon",
        "--clean",
        "--noconfirm",
        "--hidden-import", "git",
        "--hidden-import", "git.ext",
        "--hidden-import", "git.repo.base",
        "--collect-all", "git",
        "src/main.py",
    ]

    if not run_command(cmd, root):
        return False

    print(f"Package created in {root / 'dist'}")
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Git Dungeon Build Script")
    parser.add_argument("action", choices=["build", "test", "lint", "package"])

    args = parser.parse_args()

    if args.action == "build":
        sys.exit(0 if build() else 1)
    elif args.action == "test":
        sys.exit(0 if test() else 1)
    elif args.action == "lint":
        sys.exit(0 if lint() else 1)
    elif args.action == "package":
        sys.exit(0 if package() else 1)
