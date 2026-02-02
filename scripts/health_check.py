#!/usr/bin/env python3
"""
Git Dungeon Health Check

Run this before pushing to GitHub to catch common issues:
- Lint errors
- Test failures
- Import errors
- File synchronization issues
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and report results."""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout[:2000])
    
    if result.stderr:
        print(result.stderr[:1000])
    
    if result.returncode != 0:
        print(f"❌ FAILED (exit code: {result.returncode})")
        return False
    
    print("✅ PASSED")
    return True


def check_sync() -> bool:
    """Check if src/ and src/git_dungeon/ are synchronized."""
    print(f"\n{'='*60}")
    print("🔍 Checking file synchronization")
    print(f"{'='*60}")
    
    src_root = Path("src")
    src_git_dungeon = Path("src/git_dungeon")
    
    issues = []
    
    # Check for files that exist in both locations
    for f in src_root.rglob("*.py"):
        rel = f.relative_to(src_root)
        git_dungeon_path = src_git_dungeon / rel
        
        if git_dungeon_path.exists():
            if f.stat().st_mtime > git_dungeon_path.stat().st_mtime:
                issues.append(f"⚠️  {rel} is newer in src/ than in src/git_dungeon/")
            elif git_dungeon_path.stat().st_mtime > f.stat().st_mtime:
                issues.append(f"⚠️  {rel} is newer in src/git_dungeon/ than in src/")
    
    if issues:
        print("File synchronization issues:")
        for issue in issues[:10]:
            print(f"  {issue}")
        return False
    
    print("✅ Files are synchronized")
    return True


def main() -> int:
    """Run all health checks."""
    print("🩺 Git Dungeon Health Check")
    print("="*60)
    
    all_passed = True
    
    # Check 1: File synchronization
    if not check_sync():
        all_passed = False
    
    # Check 2: Ruff lint
    if not run_command(["ruff", "check", "src/", "tests/", "--no-cache"], "Running Ruff Lint"):
        all_passed = False
    
    # Check 3: Type check
    if not run_command(["mypy", "src/", "--ignore-missing-imports"], "Running MyPy Type Check"):
        all_passed = False
    
    # Check 4: Unit tests (non-slow)
    if not run_command(
        ["python3", "-m", "pytest", "tests/", "-m", "not functional and not golden and not slow", "-q"],
        "Running Unit Tests"
    ):
        all_passed = False
    
    # Check 5: Functional tests
    if not run_command(
        ["python3", "-m", "pytest", "tests/functional/", "-q"],
        "Running Functional Tests"
    ):
        all_passed = False
    
    # Check 6: Golden tests
    if not run_command(
        ["python3", "-m", "pytest", "tests/golden_test.py", "-q"],
        "Running Golden Tests"
    ):
        all_passed = False
    
    print(f"\n{'='*60}")
    if all_passed:
        print("🎉 All health checks passed!")
        return 0
    else:
        print("❌ Some checks failed. Please fix before pushing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
