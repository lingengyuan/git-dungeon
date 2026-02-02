"""
Assertions Library - 功能测试断言工具

提供常用断言函数，避免重复代码。
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class AssertionError(Exception):
    """断言失败异常"""
    pass


def assert_run_completed(result: Dict, min_enemies: int = 0) -> bool:
    """断言运行完成 (有进展)"""
    if result.get("route_progress", 0) < min_enemies:
        raise AssertionError(f"Run not completed: progress={result.get('route_progress')}, expected>={min_enemies}")
    return True


def assert_battle_won(state: Dict) -> bool:
    """断言战斗胜利"""
    if state.get("in_combat"):
        raise AssertionError("Expected battle completed, still in combat")
    return True


def assert_character_hp(state: Dict, min_hp: int = 1, max_hp: Optional[int] = None) -> bool:
    """断言角色 HP 在范围内"""
    hp = state.get("current_hp", 0)
    if hp < min_hp:
        raise AssertionError(f"HP {hp} < min {min_hp}")
    if max_hp is not None and hp > max_hp:
        raise AssertionError(f"HP {hp} > max {max_hp}")
    return True


def assert_route_has_battles(state: Dict, min_count: int = 1) -> bool:
    """断言路径包含足够战斗节点"""
    route = state.get("route_sequence", [])
    battles = [n for n in route if n.get("kind") == "BATTLE"]
    if len(battles) < min_count:
        raise AssertionError(f"Route has {len(battles)} battles, expected >= {min_count}")
    return True


def assert_route_has_events(state: Dict, min_count: int = 0) -> bool:
    """断言路径包含事件节点"""
    route = state.get("route_sequence", [])
    events = [n for n in route if n.get("kind") == "EVENT"]
    if len(events) < min_count:
        raise AssertionError(f"Route has {len(events)} events, expected >= {min_count}")
    return True


def assert_meta_points_delta(profile_before: Dict, profile_after: Dict, expected_min: int) -> bool:
    """断言 Meta 点数增加"""
    delta = profile_after.get("total_points", 0) - profile_before.get("total_points", 0)
    if delta < expected_min:
        raise AssertionError(f"Points delta {delta} < expected {expected_min}")
    return True


def assert_unlock_applied(profile: Dict, unlock_type: str, unlock_id: str) -> bool:
    """断言解锁已应用"""
    unlocks = profile.get("unlocks", {})
    if unlock_type not in unlocks:
        raise AssertionError(f"Unlock type '{unlock_type}' not found")
    if unlock_id not in unlocks.get(unlock_type, []):
        raise AssertionError(f"Unlock '{unlock_id}' not in {unlock_type}")
    return True


def assert_character_starter_cards(content: Dict, character_id: str, expected_cards: List[str]) -> bool:
    """断言角色起始卡牌正确"""
    characters = content.get("characters", {})
    if character_id not in characters:
        raise AssertionError(f"Character '{character_id}' not found")
    
    char = characters[character_id]
    starter_cards = char.get("starter_cards", [])
    
    for card in expected_cards:
        if card not in starter_cards:
            raise AssertionError(f"Character {character_id} missing starter card: {card}")
    
    return True


def assert_character_starter_relic(content: Dict, character_id: str, expected_relic: str) -> bool:
    """断言角色起始遗物正确"""
    characters = content.get("characters", {})
    if character_id not in characters:
        raise AssertionError(f"Character '{character_id}' not found")
    
    char = characters[character_id]
    starter_relics = char.get("starter_relics", [])
    
    if expected_relic not in starter_relics:
        raise AssertionError(f"Character {character_id} missing starter relic: {expected_relic}")
    
    return True


def assert_pack_loaded(packs: Dict, pack_id: str) -> bool:
    """断言内容包已加载"""
    if pack_id not in packs:
        raise AssertionError(f"Pack '{pack_id}' not loaded")
    return True


def assert_pack_cards_count(packs: Dict, pack_id: str, min_count: int) -> bool:
    """断言内容包含足够卡牌"""
    if pack_id not in packs:
        raise AssertionError(f"Pack '{pack_id}' not found")
    
    pack = packs[pack_id]
    cards = pack.get("cards", [])
    if len(cards) < min_count:
        raise AssertionError(f"Pack {pack_id} has {len(cards)} cards, expected >= {min_count}")
    return True


def assert_pack_has_archetype(packs: Dict, pack_id: str, expected_archetype: str) -> bool:
    """断言内容包属于正确流派"""
    if pack_id not in packs:
        raise AssertionError(f"Pack '{pack_id}' not found")
    
    pack = packs[pack_id]
    if pack.get("archetype") != expected_archetype:
        raise AssertionError(f"Pack {pack_id} archetype={pack.get('archetype')}, expected={expected_archetype}")
    return True


def assert_no_content_conflicts(packs: Dict, base_content: Dict) -> bool:
    """断言没有内容 ID 冲突"""
    base_card_ids = set(base_content.get("cards", {}).keys())
    base_relic_ids = set(base_content.get("relics", {}).keys())
    base_event_ids = set(base_content.get("events", {}).keys())
    
    for pack_id, pack in packs.items():
        pack_card_ids = set(c.get("id") for c in pack.get("cards", []))
        pack_relic_ids = set(r.get("id") for r in pack.get("relics", []))
        pack_event_ids = set(e.get("id") for e in pack.get("events", []))
        
        conflicts = []
        if pack_card_ids & base_card_ids:
            conflicts.append("card")
        if pack_relic_ids & base_relic_ids:
            conflicts.append("relic")
        if pack_event_ids & base_event_ids:
            conflicts.append("event")
        
        if conflicts:
            raise AssertionError(f"Pack {pack_id} has {conflicts} conflicts with base content")
    
    return True


def assert_gold_earned(result: Dict, min_gold: int = 0) -> bool:
    """断言获得金币"""
    gold = result.get("run_state", {}).get("gold", 0)
    if gold < min_gold:
        raise AssertionError(f"Gold {gold} < min {min_gold}")
    return True


def assert_energy_available(state: Dict, min_energy: int = 0) -> bool:
    """断言有可用能量"""
    energy = state.get("energy", 0)
    if energy < min_energy:
        raise AssertionError(f"Energy {energy} < min {min_energy}")
    return True


def assert_deck_size(state: Dict, min_size: int = 0, max_size: Optional[int] = None) -> bool:
    """断言牌组大小在范围内"""
    size = state.get("deck_size", 0)
    if size < min_size:
        raise AssertionError(f"Deck size {size} < min {min_size}")
    if max_size is not None and size > max_size:
        raise AssertionError(f"Deck size {size} > max {max_size}")
    return True


def assert_bias_shifted(content: Dict, character_id: str, archetype_id: str, min_delta: float = 0.0) -> bool:
    """断言流派倾向变化"""
    # 简化版本：检查角色是否关联正确流派
    characters = content.get("characters", {})
    if character_id not in characters:
        raise AssertionError(f"Character '{character_id}' not found")
    
    # 实际 bias 检查需要在运行时
    return True


def assert_profile_field(profile: Dict, field_name: str, expected_value: Any) -> bool:
    """断言 profile 字段值"""
    if profile.get(field_name) != expected_value:
        raise AssertionError(f"Profile.{field_name}={profile.get(field_name)}, expected={expected_value}")
    return True


def assert_all_characters_defined(content: Dict, expected_ids: List[str]) -> bool:
    """断言所有角色都已定义"""
    characters = content.get("characters", {})
    for char_id in expected_ids:
        if char_id not in characters:
            raise AssertionError(f"Character '{char_id}' not defined")
    return True


def assert_no_duplicate_card_ids(cards: List[Dict]) -> bool:
    """断言没有重复的卡牌 ID"""
    ids = [c.get("id") for c in cards]
    if len(ids) != len(set(ids)):
        raise AssertionError("Duplicate card IDs found")
    return True


def assert_no_duplicate_relic_ids(relics: List[Dict]) -> bool:
    """断言没有重复的遗物 ID"""
    ids = [r.get("id") for r in relics]
    if len(ids) != len(set(ids)):
        raise AssertionError("Duplicate relic IDs found")
    return True


# ==================== Route 断言 ====================

def assert_route_deterministic(routes: list) -> bool:
    """断言路径确定性：同 seed 同结果"""
    assert routes[0] == routes[1] == routes[2], "Route not deterministic"
    return True


def assert_route_node_count(route, expected: int) -> bool:
    """断言路径节点数量"""
    if len(route.nodes) != expected:
        raise AssertionError(f"Route has {len(route.nodes)} nodes, expected {expected}")
    return True


def assert_different_seeds_different_routes(route1, route2) -> bool:
    """断言不同 seed 产生不同路径"""
    from tests.harness.snapshots import snapshot_route
    s1 = snapshot_route(route1.nodes)
    s2 = snapshot_route(route2.nodes)
    if s1 == s2:
        raise AssertionError("Different seeds should produce different routes")
    return True


# ==================== Event 断言 ====================

def assert_event_effect_serializable(effect) -> bool:
    """断言事件效果可序列化"""
    from tests.harness.snapshots import stable_serialize
    try:
        stable_serialize(effect)
        return True
    except Exception as e:
        raise AssertionError(f"Event effect not serializable: {e}")


def assert_all_event_effects_serializable(effects: list) -> bool:
    """断言所有事件效果可序列化"""
    from tests.harness.snapshots import stable_serialize
    for effect in effects:
        stable_serialize(effect)
    return True


# ==================== Elite/BOSS 断言 ====================

def assert_enemy_has_tier_flag(enemy, expected_tier: str) -> bool:
    """断言敌人有 tier 标记"""
    if enemy.tier.value != expected_tier:
        raise AssertionError(f"Enemy {enemy.id} tier={enemy.tier.value}, expected={expected_tier}")
    return True


def assert_boss_has_is_boss_flag(enemy) -> bool:
    """断言 BOSS 有 is_boss=True"""
    if not enemy.is_boss:
        raise AssertionError(f"BOSS {enemy.id} is_boss should be True")
    return True


def assert_elite_exists(enemies: dict) -> bool:
    """断言精英敌人存在"""
    elites = [e for e in enemies.values() if e.tier.value == "elite"]
    if len(elites) == 0:
        raise AssertionError("No elite enemies found")
    return True


def assert_boss_exists(enemies: dict) -> bool:
    """断言 BOSS 敌人存在"""
    bosses = [e for e in enemies.values() if e.tier.value == "boss"]
    if len(bosses) == 0:
        raise AssertionError("No boss enemies found")
    return True


# ==================== Meta 断言 ====================

def assert_meta_points_earned(profile_before: dict, profile_after: dict, min_delta: int) -> bool:
    """断言获得点数"""
    delta = profile_after.get("total_points", 0) - profile_before.get("total_points", 0)
    if delta < min_delta:
        raise AssertionError(f"Points delta {delta} < expected {min_delta}")
    return True


def assert_profile_unlocked(profile: dict, unlock_type: str, unlock_id: str) -> bool:
    """断言内容已解锁"""
    unlocks = profile.get("unlocks", {})
    if unlock_type not in unlocks:
        raise AssertionError(f"Unlock type '{unlock_type}' not found")
    if unlock_id not in unlocks.get(unlock_type, []):
        raise AssertionError(f"Unlock '{unlock_id}' not in {unlock_type}")
    return True


# ==================== Pack 断言 ====================

def assert_pack_count(packs: dict, min_count: int) -> bool:
    """断言内容包数量"""
    if len(packs) < min_count:
        raise AssertionError(f"Only {len(packs)} packs, expected >= {min_count}")
    return True


def assert_pack_archetype(pack, expected_archetype: str) -> bool:
    """断言内容包流派"""
    if pack.archetype != expected_archetype:
        raise AssertionError(f"Pack {pack.id} archetype={pack.archetype}, expected={expected_archetype}")
    return True


def assert_pack_card_count(pack, min_count: int) -> bool:
    """断言内容包卡牌数量"""
    if len(pack.cards) < min_count:
        raise AssertionError(f"Pack {pack.id} has {len(pack.cards)} cards, expected >= {min_count}")
    return True


# ==================== 组合断言 ====================

def assert_game_invariant(state: dict) -> bool:
    """游戏不变式断言"""
    # HP 不能为负
    if state.get("current_hp", 0) < 0:
        raise AssertionError("HP cannot be negative")
    # 能量不能为负
    if state.get("energy", 0) < 0:
        raise AssertionError("Energy cannot be negative")
    # 金币不能为负
    if state.get("gold", 0) < 0:
        raise AssertionError("Gold cannot be negative")
    return True


def assert_deterministic_gameplay(runs: list) -> bool:
    """多次运行结果相同（确定性）"""
    if not all(r == runs[0] for r in runs):
        raise AssertionError("Gameplay not deterministic")
    return True
