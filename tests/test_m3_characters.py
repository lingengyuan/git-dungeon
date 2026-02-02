"""
M3.2 角色系统测试

测试角色差异、起始配置、能力触发
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from git_dungeon.engine.model import (
    GameState, PlayerState, CharacterState, DeckState, EnergyState, CardInstance
)
from git_dungeon.engine.rng import DefaultRNG
from git_dungeon.content.loader import load_content
from git_dungeon.content.schema import CharacterDef, CharacterStats


def test_character_stats():
    """测试角色属性差异"""
    print("=" * 50)
    print("🧪 测试: 角色属性")
    print("=" * 50)
    
    content_dir = Path("src/git_dungeon/content")
    content = load_content(str(content_dir))
    
    developer = content.characters["developer"]
    reviewer = content.characters["reviewer"]
    devops = content.characters["devops"]
    
    # Developer: 均衡
    assert developer.stats.hp == 100, f"Developer HP 期望 100, 实际 {developer.stats.hp}"
    assert developer.stats.energy == 3
    assert developer.stats.start_relics == 1
    
    # Reviewer: 高血量
    assert reviewer.stats.hp == 110, f"Reviewer HP 期望 110, 实际 {reviewer.stats.hp}"
    assert reviewer.stats.energy == 3
    assert len(reviewer.abilities) == 1  # 有能力
    
    # DevOps: 低血量高爆发
    assert devops.stats.hp == 90, f"DevOps HP 期望 90, 实际 {devops.stats.hp}"
    assert len(devops.abilities) == 1  # 有能力
    
    print(f"✅ 角色属性差异:")
    print(f"   Developer: HP={developer.stats.hp}, Energy={developer.stats.energy}")
    print(f"   Reviewer: HP={reviewer.stats.hp}, Energy={reviewer.stats.energy}, Abilities={len(reviewer.abilities)}")
    print(f"   DevOps: HP={devops.stats.hp}, Energy={devops.stats.energy}, Abilities={len(devops.abilities)}")


def test_starter_deck():
    """测试角色起始套牌"""
    print("\n" + "=" * 50)
    print("🧪 测试: 起始套牌")
    print("=" * 50)
    
    content_dir = Path("src/git_dungeon/content")
    content = load_content(str(content_dir))
    
    developer = content.characters["developer"]
    reviewer = content.characters["reviewer"]
    devops = content.characters["devops"]
    
    # Developer 起始卡
    assert "strike" in developer.starter_cards, "Developer 应该有 strike"
    assert "defend" in developer.starter_cards, "Developer 应该有 defend"
    assert len(developer.starter_cards) >= 5, f"Developer 起始卡应 >= 5, 实际 {len(developer.starter_cards)}"
    
    # Reviewer 起始卡 (Test 风格)
    assert "test_guard" in reviewer.starter_cards, "Reviewer 应该有 test_guard"
    assert len(reviewer.starter_cards) >= 5, f"Reviewer 起始卡应 >= 5, 实际 {len(reviewer.starter_cards)}"
    
    # DevOps 起始卡 (管道流)
    assert len(devops.starter_cards) >= 5, f"DevOps 起始卡应 >= 5, 实际 {len(devops.starter_cards)}"
    
    print(f"✅ 起始套牌:")
    print(f"   Developer: {len(developer.starter_cards)} 卡 - {developer.starter_cards}")
    print(f"   Reviewer: {len(reviewer.starter_cards)} 卡 - {reviewer.starter_cards}")
    print(f"   DevOps: {len(devops.starter_cards)} 卡 - {devops.starter_cards}")


def test_starter_relics():
    """测试角色起始遗物"""
    print("\n" + "=" * 50)
    print("🧪 测试: 起始遗物")
    print("=" * 50)
    
    content_dir = Path("src/git_dungeon/content")
    content = load_content(str(content_dir))
    
    developer = content.characters["developer"]
    reviewer = content.characters["reviewer"]
    devops = content.characters["devops"]
    
    # 所有角色都有起始遗物
    assert len(developer.starter_relics) >= 1, "Developer 应该有起始遗物"
    assert len(reviewer.starter_relics) >= 1, "Reviewer 应该有起始遗物"
    assert len(devops.starter_relics) >= 1, "DevOps 应该有起始遗物"
    
    # 起始遗物应该不同
    assert developer.starter_relics[0] != reviewer.starter_relics[0], "起始遗物应该不同"
    
    print(f"✅ 起始遗物:")
    print(f"   Developer: {developer.starter_relics}")
    print(f"   Reviewer: {reviewer.starter_relics}")
    print(f"   DevOps: {devops.starter_relics}")


def test_character_abilities():
    """测试角色能力"""
    print("\n" + "=" * 50)
    print("🧪 测试: 角色能力")
    print("=" * 50)
    
    content_dir = Path("src/git_dungeon/content")
    content = load_content(str(content_dir))
    
    developer = content.characters["developer"]
    reviewer = content.characters["reviewer"]
    devops = content.characters["devops"]
    
    # Developer 没有主动能力 (被动)
    assert len(developer.abilities) == 0, "Developer 应该没有能力"
    
    # Reviewer 有净化能力
    assert len(reviewer.abilities) == 1, "Reviewer 应该有 1 个能力"
    purify = reviewer.abilities[0]
    assert purify.trigger == "on_turn_start", "Reviewer 应该是回合开始触发"
    assert purify.effect == "clear_negative_status", "Reviewer 应该是净化效果"
    
    # DevOps 有管道能力
    assert len(devops.abilities) == 1, "DevOps 应该有 1 个能力"
    pipeline = devops.abilities[0]
    assert pipeline.trigger == "on_turn_end", "DevOps 应该是回合结束触发"
    assert "add_energy" in pipeline.effect or "draw" in pipeline.effect
    
    print(f"✅ 角色能力:")
    print(f"   Developer: 无 (被动)")
    print(f"   Reviewer: {reviewer.abilities[0].effect} ({reviewer.abilities[0].trigger})")
    print(f"   DevOps: {devops.abilities[0].effect} ({devops.abilities[0].trigger})")


def test_character_initialization():
    """测试根据角色初始化游戏状态"""
    print("\n" + "=" * 50)
    print("🧪 测试: 角色初始化")
    print("=" * 50)
    
    content_dir = Path("src/git_dungeon/content")
    content = load_content(str(content_dir))
    
    def init_game_with_character(character_id: str) -> GameState:
        """根据角色初始化游戏状态"""
        char = content.characters[character_id]
        state = GameState(seed=12345)
        state.character_id = character_id
        
        # 设置角色属性
        state.player.character.current_hp = char.stats.hp
        state.player.energy.max_energy = char.stats.energy
        
        # 初始化套牌
        state.player.deck.draw_pile = [
            CardInstance(card_id=card_id, upgrade_level=0)
            for card_id in char.starter_cards
        ]
        
        # 初始化遗物
        state.player.relics = list(char.starter_relics)
        
        return state
    
    # 测试 Developer
    dev_state = init_game_with_character("developer")
    assert dev_state.player.character.current_hp == 100, f"Developer HP 错误: {dev_state.player.character.current_hp}"
    assert len(dev_state.player.deck.draw_pile) == len(content.characters["developer"].starter_cards)
    assert "git_init" in dev_state.player.relics
    
    # 测试 Reviewer
    rev_state = init_game_with_character("reviewer")
    assert rev_state.player.character.current_hp == 110, f"Reviewer HP 错误: {rev_state.player.character.current_hp}"
    assert "test_framework" in rev_state.player.relics
    
    # 测试 DevOps
    ops_state = init_game_with_character("devops")
    assert ops_state.player.character.current_hp == 90, f"DevOps HP 错误: {ops_state.player.character.current_hp}"
    assert "ci_badge" in ops_state.player.relics
    
    print(f"✅ 角色初始化正确:")
    print(f"   Developer: HP={dev_state.player.character.current_hp}, 卡={len(dev_state.player.deck.draw_pile)}")
    print(f"   Reviewer: HP={rev_state.player.character.current_hp}, 卡={len(rev_state.player.deck.draw_pile)}")
    print(f"   DevOps: HP={ops_state.player.character.current_hp}, 卡={len(ops_state.player.deck.draw_pile)}")


def test_character_determinism():
    """测试角色选择的确定性"""
    print("\n" + "=" * 50)
    print("🧪 测试: 角色选择确定性")
    print("=" * 50)
    
    content_dir = Path("src/git_dungeon/content")
    content = load_content(str(content_dir))
    
    def init_game_with_character(character_id: str) -> GameState:
        char = content.characters[character_id]
        state = GameState(seed=12345)
        state.character_id = character_id
        state.player.character.current_hp = char.stats.hp
        state.player.energy.max_energy = char.stats.energy
        state.player.deck.draw_pile = [
            CardInstance(card_id=card_id, upgrade_level=0)
            for card_id in char.starter_cards
        ]
        state.player.relics = list(char.starter_relics)
        return state
    
    # 两次初始化 Developer 应该完全相同
    state1 = init_game_with_character("developer")
    state2 = init_game_with_character("developer")
    
    assert state1.player.character.current_hp == state2.player.character.current_hp
    assert len(state1.player.deck.draw_pile) == len(state2.player.deck.draw_pile)
    assert state1.player.relics == state2.player.relics
    
    print(f"✅ 角色选择确定性验证通过")


def test_character_content_integrity():
    """测试角色内容完整性"""
    print("\n" + "=" * 50)
    print("🧪 测试: 内容完整性")
    print("=" * 50)
    
    content_dir = Path("src/git_dungeon/content")
    content = load_content(str(content_dir))
    
    # 检查所有角色定义
    assert len(content.characters) == 3, f"期望 3 角色, 实际 {len(content.characters)}"
    
    for char_id, char in content.characters.items():
        # 检查 ID 唯一
        assert char.id == char_id, f"角色 ID 不匹配: {char.id} vs {char_id}"
        
        # 检查起始卡牌存在
        for card_id in char.starter_cards:
            card = content.get_card(card_id)
            assert card is not None, f"角色 {char_id} 的卡牌 {card_id} 不存在"
        
        # 检查起始遗物存在
        for relic_id in char.starter_relics:
            relic = content.get_relic(relic_id)
            assert relic is not None, f"角色 {char_id} 的遗物 {relic_id} 不存在"
    
    print(f"✅ 内容完整性验证通过")
    print(f"   角色: {len(content.characters)}")
    for char_id, char in content.characters.items():
        print(f"      {char_id}: {len(char.starter_cards)} 卡, {len(char.starter_relics)} 遗物")


def test_all_characters_defined():
    """测试所有角色都正确定义"""
    print("\n" + "=" * 50)
    print("🧪 测试: 角色定义")
    print("=" * 50)
    
    content_dir = Path("src/git_dungeon/content")
    content = load_content(str(content_dir))
    
    expected_characters = {"developer", "reviewer", "devops"}
    actual_characters = set(content.characters.keys())
    
    assert actual_characters == expected_characters, f"角色不匹配: {actual_characters} vs {expected_characters}"
    
    for char_id in expected_characters:
        char = content.characters[char_id]
        assert char.name_key, f"角色 {char_id} 缺少 name_key"
        assert char.desc_key, f"角色 {char_id} 缺少 desc_key"
        assert len(char.starter_cards) >= 5, f"角色 {char_id} 起始卡不足"
        assert len(char.starter_relics) >= 1, f"角色 {char_id} 起始遗物不足"
    
    print(f"✅ 所有角色正确定义:")
    for char_id in expected_characters:
        char = content.characters[char_id]
        print(f"   {char_id}: {char.name_key}")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🧪 Git Dungeon M3.2 角色系统测试")
    print("=" * 60 + "\n")
    
    test_character_stats()
    test_starter_deck()
    test_starter_relics()
    test_character_abilities()
    test_character_initialization()
    test_character_determinism()
    test_character_content_integrity()
    test_all_characters_defined()
    
    print("\n" + "=" * 60)
    print("✅ M3.2 角色系统测试全部通过!")
    print("=" * 60)


if __name__ == "__main__":
    main()
