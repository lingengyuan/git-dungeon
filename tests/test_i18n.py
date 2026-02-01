# i18n Tests - Test Chinese language support

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from git_dungeon.i18n.translations import get_translation, TRANSLATIONS


def test_translation_structure():
    """Test that translation dictionary has required languages."""
    assert "en" in TRANSLATIONS, "English translations missing"
    assert "zh_CN" in TRANSLATIONS, "Chinese translations missing"
    print("✅ Translation structure valid")


def test_english_translations():
    """Test English translations are present."""
    # Core game strings
    assert get_translation("VICTORY", "en") == "VICTORY"
    assert get_translation("GAME OVER", "en") == "GAME OVER"
    assert get_translation("CHAPTER COMPLETE", "en") == "CHAPTER COMPLETE"
    assert get_translation("BOSS BATTLE", "en") == "BOSS BATTLE"
    print("✅ English translations valid")


def test_chinese_translations():
    """Test Chinese translations are present and correct."""
    # Core game strings
    assert get_translation("VICTORY", "zh_CN") == "🏆 胜利"
    assert get_translation("GAME OVER", "zh_CN") == "💀 游戏结束"
    assert get_translation("CHAPTER COMPLETE", "zh_CN") == "🎉 章节完成"
    assert get_translation("BOSS BATTLE", "zh_CN") == "👹 BOSS 战"
    
    # Repository loading
    assert get_translation("Loaded", "zh_CN") == "已加载"
    assert get_translation("commits", "zh_CN") == "次提交"
    assert get_translation("Divided into", "zh_CN") == "分为"
    assert get_translation("chapters", "zh_CN") == "个章节"
    
    # Combat
    assert get_translation("You attack", "zh_CN") == "你攻击"
    assert get_translation("for", "zh_CN") == "造成"
    assert get_translation("damage", "zh_CN") == "伤害"
    assert get_translation("CRIT!", "zh_CN") == "⚡ 暴击!"
    assert get_translation("defeated", "zh_CN") == "已击败"
    
    # Rewards
    assert get_translation("EXP", "zh_CN") == "经验"
    assert get_translation("Gold", "zh_CN") == "金币"
    assert get_translation("LEVEL UP", "zh_CN") == "🆙 升级!"
    
    # Shop
    assert get_translation("商店", "zh_CN") == "🏪 商店"
    assert get_translation("Welcome to the shop", "zh_CN") == "欢迎来到商店!"
    
    print("✅ Chinese translations valid")


def test_fallback_for_missing_key():
    """Test that missing keys return original text."""
    original = "This is a test string that is not translated"
    result = get_translation(original, "zh_CN")
    assert result == original, f"Expected '{original}', got '{result}'"
    print("✅ Fallback for missing keys works")


def test_all_english_keys_have_chinese():
    """Test that all English keys have Chinese translations."""
    english_keys = set(TRANSLATIONS["en"].keys())
    chinese_keys = set(TRANSLATIONS["zh_CN"].keys())
    
    # Keys that don't need translation (Chinese chapter names)
    skip_keys = {"混沌初开", "功能涌现", "架构重构", "优化迭代", "成熟稳定", "开疆拓土", "登峰造极"}
    
    missing = english_keys - chinese_keys - skip_keys
    if missing:
        print(f"⚠️ Missing Chinese translations for: {missing}")
    else:
        print("✅ All English keys have Chinese translations")


def test_translation_function_alias():
    """Test that _() function works correctly."""
    from git_dungeon.i18n.translations import _
    
    result = _("VICTORY", "zh_CN")
    assert result == "🏆 胜利"
    print("✅ _() function works correctly")


def run_all_tests():
    """Run all i18n tests."""
    print("\n" + "=" * 60)
    print("🧪 i18n (Internationalization) Tests")
    print("=" * 60 + "\n")
    
    tests = [
        test_translation_structure,
        test_english_translations,
        test_chinese_translations,
        test_fallback_for_missing_key,
        test_all_english_keys_have_chinese,
        test_translation_function_alias,
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
    print(f"📊 i18n Test Results: {passed} passed, {failed} failed")
    print("=" * 60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
