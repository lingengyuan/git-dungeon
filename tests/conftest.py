"""Pytest configuration."""

import sys
from pathlib import Path
import pytest

# Add repository root and src directory to path
repo_root = Path(__file__).resolve().parent.parent
src_path = repo_root / "src"
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(src_path))


class TestResult:
    """Simple test result collector."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, name):
        self.passed += 1
        print(f"  ✅ {name}")
    
    def add_fail(self, name, reason):
        self.failed += 1
        self.errors.append((name, reason))
        print(f"  ❌ {name}: {reason}")


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "functional: marks functional gameplay tests"
    )
    config.addinivalue_line(
        "markers", "golden: marks deterministic snapshot/replay tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "fuzzy: marks tests as fuzzy/random tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    # Mark test_m3_full_automation tests as slow
    config.addinivalue_line(
        "markers", "m3: marks M3 automation tests"
    )


def pytest_collection_modifyitems(config, items):
    """Auto-tag tests by location so marker filtering stays reliable."""
    for item in items:
        item_path = Path(str(item.fspath))
        parts = item_path.parts

        if "functional" in parts:
            item.add_marker(pytest.mark.functional)

        if "golden" in parts or item_path.name in {"golden_test.py", "test_golden.py"}:
            item.add_marker(pytest.mark.golden)
