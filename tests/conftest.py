"""Pytest configuration."""

import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))


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
