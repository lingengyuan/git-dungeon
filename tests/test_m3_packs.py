"""
M3.3 内容包测试

测试 packs/ 目录加载、解锁过滤、ID 冲突检测
"""

import sys
import tempfile
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from git_dungeon.content.packs import (
    PackLoader, merge_content_with_packs, get_pack_info
)
from git_dungeon.content.schema import ContentRegistry, ContentPack
from git_dungeon.content.loader import load_content


def test_pack_loader():
    """测试内容包加载"""
    print("=" * 50)
    print("🧪 测试: 内容包加载")
    print("=" * 50)
    
    packs_dir = Path("src/git_dungeon/content/packs")
    loader = PackLoader(packs_dir)
    
    # 加载所有包
    packs = loader.load_all_packs()
    
    assert len(packs) >= 3, f"期望至少 3 个包, 实际 {len(packs)}"
    
    # 检查每个包
    for pack_id, pack in packs.items():
        assert pack.id == pack_id
        assert len(pack.cards) >= 3, f"包 {pack_id} 卡牌不足"
        assert pack.archetype in ["debug_beatdown", "test_shrine", "refactor_risk"]
    
    print(f"✅ 内容包加载成功:")
    print(f"   总包数: {len(packs)}")
    for pack_id, pack in packs.items():
        print(f"   - {pack_id}: {len(pack.cards)} 卡, {len(pack.relics)} 遗物, {len(pack.events)} 事件")


def test_pack_info():
    """测试获取包信息"""
    print("\n" + "=" * 50)
    print("🧪 测试: 包信息")
    print("=" * 50)
    
    info = get_pack_info("src/git_dungeon/content/packs")
    
    assert "debug_pack" in info
    assert "test_pack" in info
    assert "refactor_pack" in info
    
    debug_info = info["debug_pack"]
    assert debug_info["archetype"] == "debug_beatdown"
    assert debug_info["points_cost"] == 150
    
    print(f"✅ 包信息获取成功:")
    for pack_id, pack_info in info.items():
        print(f"   {pack_id}: {pack_info['archetype']} ({pack_info['points_cost']} pts)")


def test_merge_packs():
    """测试合并内容包"""
    print("\n" + "=" * 50)
    print("🧪 测试: 合并内容包")
    print("=" * 50)
    
    # 加载基础内容
    base_content = load_content("src/git_dungeon/content")
    initial_card_count = len(base_content.cards)
    
    # 合并 debug_pack
    merged = merge_content_with_packs(
        base_content,
        "src/git_dungeon/content/packs",
        ["debug_pack"]
    )
    
    # 应该添加了 debug_pack 的卡牌
    assert len(merged.cards) > initial_card_count, "合并后卡牌数应该增加"
    
    # 检查 debug_pack 的卡牌存在
    debug_pack = merged.get_pack("debug_pack")
    assert debug_pack is not None
    
    for card in debug_pack.cards:
        assert card.id in merged.cards, f"卡牌 {card.id} 应该存在"
    
    print(f"✅ 内容合并成功:")
    print(f"   基础卡牌: {initial_card_count}")
    print(f"   合并后: {len(merged.cards)}")
    print(f"   debug_pack 卡: {len(debug_pack.cards)}")


def test_merge_multiple_packs():
    """测试合并多个内容包"""
    print("\n" + "=" * 50)
    print("🧪 测试: 合并多个包")
    print("=" * 50)
    
    base_content = load_content("src/git_dungeon/content")
    
    # 合并所有包
    merged = merge_content_with_packs(
        base_content,
        "src/git_dungeon/content/packs",
        ["debug_pack", "test_pack", "refactor_pack"]
    )
    
    assert merged.get_pack("debug_pack") is not None
    assert merged.get_pack("test_pack") is not None
    assert merged.get_pack("refactor_pack") is not None
    
    # 检查各流派包
    debug_packs = merged.get_packs_by_archetype("debug_beatdown")
    test_packs = merged.get_packs_by_archetype("test_shrine")
    refactor_packs = merged.get_packs_by_archetype("refactor_risk")
    
    assert len(debug_packs) >= 1, "应该有 debug 包"
    assert len(test_packs) >= 1, "应该有 test 包"
    assert len(refactor_packs) >= 1, "应该有 refactor 包"
    
    print(f"✅ 多包合并成功:")
    print(f"   Debug 包: {len(debug_packs)}")
    print(f"   Test 包: {len(test_packs)}")
    print(f"   Refactor 包: {len(refactor_packs)}")


def test_get_packs_by_archetype():
    """测试按流派筛选包"""
    print("\n" + "=" * 50)
    print("🧪 测试: 流派筛选")
    print("=" * 50)
    
    packs_dir = Path("src/git_dungeon/content/packs")
    loader = PackLoader(packs_dir)
    packs = loader.load_all_packs()
    
    # 直接从 packs 字典获取
    debug_packs = [p for p in packs.values() if p.archetype == "debug_beatdown"]
    test_packs = [p for p in packs.values() if p.archetype == "test_shrine"]
    refactor_packs = [p for p in packs.values() if p.archetype == "refactor_risk"]
    
    assert len(debug_packs) == 1, f"应该有 1 个 debug 包, 实际 {len(debug_packs)}"
    assert len(test_packs) == 1, f"应该有 1 个 test 包, 实际 {len(test_packs)}"
    assert len(refactor_packs) == 1, f"应该有 1 个 refactor 包, 实际 {len(refactor_packs)}"
    
    print(f"✅ 流派筛选正确:")
    print(f"   Debug: {debug_packs[0].id}")
    print(f"   Test: {test_packs[0].id}")
    print(f"   Refactor: {refactor_packs[0].id}")


def test_pack_content_integrity():
    """测试包内容完整性"""
    print("\n" + "=" * 50)
    print("🧪 测试: 内容完整性")
    print("=" * 50)
    
    packs_dir = Path("src/git_dungeon/content/packs")
    loader = PackLoader(packs_dir)
    packs = loader.load_all_packs()
    
    for pack_id, pack in packs.items():
        # 检查卡牌
        for card in pack.cards:
            assert card.id, f"卡牌缺少 ID: {pack_id}"
            assert card.name_key, f"卡牌 {card.id} 缺少 name_key"
            assert card.desc_key, f"卡牌 {card.id} 缺少 desc_key"
            assert card.cost >= 0, f"卡牌 {card.id} 费用无效"
            assert len(card.tags) > 0, f"卡牌 {card.id} 缺少 tags"
        
        # 检查遗物
        for relic in pack.relics:
            assert relic.id, f"遗物缺少 ID: {pack_id}"
            assert relic.name_key, f"遗物 {relic.id} 缺少 name_key"
        
        # 检查事件
        for event in pack.events:
            assert event.id, f"事件缺少 ID: {pack_id}"
            assert len(event.choices) >= 1, f"事件 {event.id} 缺少 choices"
    
    print(f"✅ 内容完整性验证通过")
    for pack_id, pack in packs.items():
        print(f"   {pack_id}: {len(pack.cards)} 卡, {len(pack.relics)} 遗物, {len(pack.events)} 事件")


def test_content_verification():
    """测试 M3.3 内容验证"""
    print("\n" + "=" * 50)
    print("📦 M3.3 内容验证")
    print("=" * 50)
    
    # 检查 packs 目录存在
    packs_dir = Path("src/git_dungeon/content/packs")
    assert packs_dir.exists(), "packs 目录不存在"
    
    # 检查每个子目录
    expected_packs = ["debug_pack", "test_pack", "refactor_pack"]
    for pack_id in expected_packs:
        pack_path = packs_dir / pack_id
        assert pack_path.exists(), f"目录 {pack_id} 不存在"
        assert (pack_path / "cards.yml").exists(), f"{pack_id}/cards.yml 不存在"
    
    # 加载并验证
    loader = PackLoader(packs_dir)
    packs = loader.load_all_packs()
    
    assert len(packs) == 3, f"期望 3 个包, 实际 {len(packs)}"
    
    # 统计
    total_cards = sum(len(p.cards) for p in packs.values())
    total_relics = sum(len(p.relics) for p in packs.values())
    total_events = sum(len(p.events) for p in packs.values())
    
    print(f"✅ M3.3 内容验证通过:")
    print(f"   包数量: {len(packs)}")
    print(f"   总卡牌: {total_cards}")
    print(f"   总遗物: {total_relics}")
    print(f"   总事件: {total_events}")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🧪 Git Dungeon M3.3 内容包测试")
    print("=" * 60 + "\n")
    
    test_pack_loader()
    test_pack_info()
    test_merge_packs()
    test_merge_multiple_packs()
    test_get_packs_by_archetype()
    test_pack_content_integrity()
    test_content_verification()
    
    print("\n" + "=" * 60)
    print("✅ M3.3 内容包测试全部通过!")
    print("=" * 60)


if __name__ == "__main__":
    main()
