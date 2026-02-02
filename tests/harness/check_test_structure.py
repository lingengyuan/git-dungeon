#!/usr/bin/env python3
"""
Pre-commit hook: Check test structure

验证 functional tests 有对应的 golden 快照（如果需要）
"""

import sys
from pathlib import Path


def check_functional_tests():
    """检查 functional tests 结构"""
    tests_dir = Path("tests/functional")
    golden_dir = Path("tests/golden")
    
    # 获取所有 golden 文件
    golden_files = set(f.stem for f in golden_dir.glob("*.json"))
    
    # 功能测试应该有对应的 snapshot 验证
    expected_snapshots = {
        "m3_meta_profile_default",
        "m3_character_starters",
        "m3_packs_info",
        "m3_points_calculation",
        "m2_route_graph_determinism",
        "m2_elite_boss_rewards",
    }
    
    missing = expected_snapshots - golden_files
    
    if missing:
        print(f"⚠️  Missing golden snapshots: {missing}")
        return False
    
    print("✅ All required golden snapshots exist")
    return True


def check_assertions_importable():
    """检查 assertions 可导入"""
    try:
        from tests.harness.assertions import (
            assert_run_completed,
            assert_battle_won,
            assert_character_hp,
            assert_pack_loaded,
            assert_no_content_conflicts,
        )
        print("✅ Assertions importable")
        return True
    except ImportError as e:
        print(f"❌ Assertion import error: {e}")
        return False


def check_snapshots_importable():
    """检查 snapshots 可导入"""
    try:
        from tests.harness.snapshots import (
            stable_serialize,
            save_snapshot,
            load_snapshot,
            SnapshotManager,
        )
        print("✅ Snapshots importable")
        return True
    except ImportError as e:
        print(f"❌ Snapshot import error: {e}")
        return False


def main():
    """主函数"""
    checks = [
        ("Functional tests", check_functional_tests),
        ("Assertions", check_assertions_importable),
        ("Snapshots", check_snapshots_importable),
    ]
    
    all_passed = True
    for name, check in checks:
        print(f"\n🔍 Checking {name}...")
        if not check():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All checks passed!")
        return 0
    else:
        print("❌ Some checks failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
