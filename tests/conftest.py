"""Pytest configuration."""

import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent.parent
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
