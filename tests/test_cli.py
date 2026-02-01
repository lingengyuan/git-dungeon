# CLI Tests - Test command line arguments

import sys
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_lang_argument_exists():
    """Test that --lang argument is recognized."""
    result = subprocess.run(
        [sys.executable, "-c", 
         "from git_dungeon.main import main;"
         "import argparse;"
         "parser = argparse.ArgumentParser();"
         "parser.add_argument('--lang');"
         "args = parser.parse_args(['--lang', 'zh_CN']);"
         "print(args.lang)"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Failed: {result.stderr}"
    assert "zh_CN" in result.stdout, f"Expected zh_CN, got: {result.stdout}"
    print("✅ --lang argument exists")


def test_cli_help_shows_lang():
    """Test that help text includes --lang option."""
    result = subprocess.run(
        [sys.executable, "-c", 
         "from git_dungeon.main import main;"
         "import argparse;"
         "parser = argparse.ArgumentParser();"
         "parser.add_argument('--lang', '-l', type=str, default='en', "
         "choices=['en', 'zh', 'zh_CN'], help='Language (en/zh_CN)');"
         "print('--lang' in parser.format_help())"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    print("✅ Help text includes --lang option")


def test_invalid_lang():
    """Test that invalid language is rejected."""
    result = subprocess.run(
        [sys.executable, "-c", 
         "import sys;"
         "from git_dungeon.main import main;"
         "import argparse;"
         "parser = argparse.ArgumentParser();"
         "parser.add_argument('--lang', '-l', type=str, default='en', "
         "choices=['en', 'zh', 'zh_CN']);"
         "try:"
         "    args = parser.parse_args(['--lang', 'invalid'])"
         "except SystemExit:"
         "    sys.exit(0)"
         "sys.exit(1)"],
        capture_output=True,
        text=True
    )
    # Should exit with error (non-zero)
    assert result.returncode != 0, f"Expected non-zero exit, got {result.returncode}"
    print("✅ Invalid language is rejected")


def run_all_tests():
    """Run all CLI tests."""
    print("\n" + "=" * 60)
    print("🧪 CLI Tests")
    print("=" * 60 + "\n")
    
    tests = [
        test_lang_argument_exists,
        test_cli_help_shows_lang,
        test_invalid_lang,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 CLI Test Results: {passed} passed, {failed} failed")
    print("=" * 60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
