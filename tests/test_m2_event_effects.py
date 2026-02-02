"""
M2.2 事件效果测试

测试事件选择效果的执行和边界条件
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from git_dungeon.engine.events import (
    apply_event_choice
)
from git_dungeon.engine.model import (
    GameState, CardInstance
)
from git_dungeon.engine.rng import DefaultRNG


def test_event_effect_gain_gold():
    """测试获得金币效果"""
    print("=" * 50)
    print("🧪 测试: gain_gold")
    print("=" * 50)
    
    state = GameState(seed=12345)
    state.player.gold = 50
    
    effects = [{"opcode": "gain_gold", "value": 30}]
    result = apply_event_choice(state, effects, DefaultRNG(seed=1))
    
    assert result["success"], "执行应该成功"
    assert state.player.gold == 80, f"期望 80, 实际 {state.player.gold}"
    assert "gain_gold:30" in result["effects_applied"]
    print("✅ 金币: 50 -> 80")


def test_event_effect_lose_gold():
    """测试失去金币效果（边界：不负数）"""
    print("\n" + "=" * 50)
    print("🧪 测试: lose_gold (边界)")
    print("=" * 50)
    
    state = GameState(seed=12345)
    state.player.gold = 20
    
    effects = [{"opcode": "lose_gold", "value": 50}]
    result = apply_event_choice(state, effects, DefaultRNG(seed=1))
    
    assert result["success"], "执行应该成功"
    assert state.player.gold == 0, f"期望 0, 实际 {state.player.gold}"
    assert "lose_gold:50" in result["effects_applied"]
    print("✅ 金币: 20 -> 0 (不小于0)")


def test_event_effect_heal():
    """测试治疗效果"""
    print("\n" + "=" * 50)
    print("🧪 测试: heal")
    print("=" * 50)
    
    state = GameState(seed=12345)
    # 先造成伤害使 HP < max_hp
    state.player.character.current_hp = 70
    max_hp = state.player.character.stats.hp.value
    
    effects = [{"opcode": "heal", "value": 20}]
    result = apply_event_choice(state, effects, DefaultRNG(seed=1))
    
    assert result["success"], "执行应该成功"
    expected = min(70 + 20, max_hp)
    assert state.player.character.current_hp == expected, f"期望 {expected}, 实际 {state.player.character.current_hp}"
    print(f"✅ HP: 70 -> {state.player.character.current_hp}")


def test_event_effect_take_damage():
    """测试受伤效果"""
    print("\n" + "=" * 50)
    print("🧪 测试: take_damage")
    print("=" * 50)
    
    state = GameState(seed=12345)
    # 先造成伤害使 HP < max_hp
    state.player.character._current_hp = 100
    
    effects = [{"opcode": "take_damage", "value": 25}]
    result = apply_event_choice(state, effects, DefaultRNG(seed=1))
    
    assert result["success"], "执行应该成功"
    assert state.player.character.current_hp == 75, f"期望 75, 实际 {state.player.character.current_hp}"
    print("✅ HP: 100 -> 75")


def test_event_effect_add_card():
    """测试添加卡牌"""
    print("\n" + "=" * 50)
    print("🧪 测试: add_card")
    print("=" * 50)
    
    state = GameState(seed=12345)
    initial_count = state.player.deck.total_cards
    
    effects = [{"opcode": "add_card", "value": "debug_strike"}]
    result = apply_event_choice(state, effects, DefaultRNG(seed=1))
    
    assert result["success"], "执行应该成功"
    assert state.player.deck.total_cards == initial_count + 1, f"期望 {initial_count + 1}"
    assert "add_card:debug_strike" in result["effects_applied"]
    print(f"✅ 卡牌: {initial_count} -> {state.player.deck.total_cards}")


def test_event_effect_remove_card():
    """测试移除卡牌（边界：有卡才删）"""
    print("\n" + "=" * 50)
    print("🧪 测试: remove_card (边界)")
    print("=" * 50)
    
    state = GameState(seed=12345)
    state.player.deck.draw_pile = [CardInstance(card_id="strike")]
    initial_count = state.player.deck.total_cards
    
    effects = [{"opcode": "remove_card", "value": "strike"}]
    result = apply_event_choice(state, effects, DefaultRNG(seed=1))
    
    assert result["success"], "执行应该成功"
    assert state.player.deck.total_cards == initial_count - 1, f"期望 {initial_count - 1}"
    print(f"✅ 卡牌: {initial_count} -> {state.player.deck.total_cards}")


def test_event_effect_add_relic():
    """测试添加遗物"""
    print("\n" + "=" * 50)
    print("🧪 测试: add_relic")
    print("=" * 50)
    
    state = GameState(seed=12345)
    state.player.relics = ["starter_relic"]
    
    effects = [{"opcode": "add_relic", "value": "power_relic"}]
    result = apply_event_choice(state, effects, DefaultRNG(seed=1))
    
    assert result["success"], "执行应该成功"
    assert "power_relic" in state.player.relics
    print(f"✅ 遗物: {state.player.relics}")


def test_event_effect_modify_bias():
    """测试流派倾向修改"""
    print("\n" + "=" * 50)
    print("🧪 测试: modify_bias")
    print("=" * 50)
    
    state = GameState(seed=12345)
    
    effects = [{"opcode": "modify_bias", "value": "debug_beatdown:0.2"}]
    result = apply_event_choice(state, effects, DefaultRNG(seed=1))
    
    assert result["success"], "执行应该成功"
    bias = state.route_state.get("bias", {})
    assert "debug_beatdown" in bias
    assert abs(bias["debug_beatdown"] - 0.2) < 0.01
    print(f"✅ bias: {bias}")


def test_event_effect_set_flag():
    """测试设置事件标记"""
    print("\n" + "=" * 50)
    print("🧪 测试: set_flag")
    print("=" * 50)
    
    state = GameState(seed=12345)
    
    effects = [{"opcode": "set_flag", "value": "visited_shrine:true"}]
    result = apply_event_choice(state, effects, DefaultRNG(seed=1))
    
    assert result["success"], "执行应该成功"
    assert state.route_state["event_flags"]["visited_shrine"] == "true"
    print(f"✅ flags: {state.route_state['event_flags']}")


def test_event_effect_trigger_battle():
    """测试触发战斗"""
    print("\n" + "=" * 50)
    print("🧪 测试: trigger_battle")
    print("=" * 50)
    
    state = GameState(seed=12345)
    
    effects = [{"opcode": "trigger_battle", "value": "elite"}]
    result = apply_event_choice(state, effects, DefaultRNG(seed=1))
    
    assert result["success"], "执行应该成功"
    assert state.route_state["event_flags"]["trigger_battle"] == "elite"
    print(f"✅ trigger_battle: {state.route_state['event_flags']['trigger_battle']}")


def test_event_effect_multiple():
    """测试多效果组合"""
    print("\n" + "=" * 50)
    print("🧪 测试: 多效果组合")
    print("=" * 50)
    
    state = GameState(seed=12345)
    state.player.gold = 50
    state.player.character.current_hp = 80
    initial_cards = state.player.deck.total_cards
    
    effects = [
        {"opcode": "gain_gold", "value": 25},
        {"opcode": "heal", "value": 10},
        {"opcode": "add_card", "value": "test_guard"}
    ]
    result = apply_event_choice(state, effects, DefaultRNG(seed=1))
    
    assert result["success"], "执行应该成功"
    assert state.player.gold == 75, f"期望 75, 实际 {state.player.gold}"
    assert state.player.character.current_hp == 90, f"期望 90, 实际 {state.player.character.current_hp}"
    assert state.player.deck.total_cards == initial_cards + 1
    print("✅ 组合效果:")
    print("   金币: 50 -> 75")
    print("   HP: 80 -> 90")
    print(f"   卡牌: {initial_cards} -> {state.player.deck.total_cards}")


def test_event_state_changes():
    """测试状态变化返回值"""
    print("\n" + "=" * 50)
    print("🧪 测试: state_changes 返回值")
    print("=" * 50)
    
    state = GameState(seed=12345)
    state.player.gold = 100
    state.player.character.current_hp = 90  # 低于满血
    
    effects = [{"opcode": "heal", "value": 30}]
    result = apply_event_choice(state, effects, DefaultRNG(seed=1))
    
    assert "state_changes" in result
    changes = result["state_changes"]
    assert changes["gold"] == 100
    assert changes["hp"] == 100  # 治疗到满血
    print(f"✅ state_changes: {changes}")
    print(f"✅ state_changes: {changes}")


def test_event_unknown_opcode():
    """测试未知 opcode（不应崩溃）"""
    print("\n" + "=" * 50)
    print("🧪 测试: 未知 opcode")
    print("=" * 50)
    
    state = GameState(seed=12345)
    
    effects = [{"opcode": "unknown_opcode", "value": 123}]
    result = apply_event_choice(state, effects, DefaultRNG(seed=1))
    
    # 应该仍然成功，只是效果未知
    assert result["success"], "执行应该仍然成功"
    print(f"✅ 未知 opcode 处理: {result['effects_applied']}")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("🧪 Git Dungeon M2.2 事件效果测试")
    print("=" * 60 + "\n")
    
    test_event_effect_gain_gold()
    test_event_effect_lose_gold()
    test_event_effect_heal()
    test_event_effect_take_damage()
    test_event_effect_add_card()
    test_event_effect_remove_card()
    test_event_effect_add_relic()
    test_event_effect_modify_bias()
    test_event_effect_set_flag()
    test_event_effect_trigger_battle()
    test_event_effect_multiple()
    test_event_state_changes()
    test_event_unknown_opcode()
    
    print("\n" + "=" * 60)
    print("✅ M2.2 事件效果测试全部通过!")
    print("=" * 60)


if __name__ == "__main__":
    main()
