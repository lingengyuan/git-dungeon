"""
Snapshots - 结构化快照工具

提供标准化的序列化、快照生成与比对。
"""

import json
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import is_dataclass, asdict


def stable_serialize(obj: Any) -> Any:
    """稳定序列化 - 保证同输入同输出"""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (list, tuple)):
        return [stable_serialize(item) for item in obj]
    if isinstance(obj, dict):
        # dict: 按 key 排序
        return {k: stable_serialize(obj[k]) for k in sorted(obj.keys())}
    if is_dataclass(obj):
        # dataclass: 转 dict 后递归
        return stable_serialize(asdict(obj))
    if hasattr(obj, '__dict__'):
        # 其他对象: 转 dict
        return stable_serialize(obj.__dict__)
    return str(obj)


def compute_snapshot_hash(data: Dict) -> str:
    """计算快照 hash"""
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()[:8]


def save_snapshot(snapshot_dir: Path, snapshot_id: str, data: Dict) -> Path:
    """保存快照到文件"""
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    # 稳定序列化
    stable_data = stable_serialize(data)
    
    # 添加 metadata
    snapshot = {
        "id": snapshot_id,
        "hash": compute_snapshot_hash(stable_data),
        "data": stable_data
    }
    
    # 写入 JSON
    snapshot_path = snapshot_dir / f"{snapshot_id}.json"
    with open(snapshot_path, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    
    return snapshot_path


def load_snapshot(snapshot_dir: Path, snapshot_id: str) -> Optional[Dict]:
    """加载快照"""
    snapshot_path = snapshot_dir / f"{snapshot_id}.json"
    if not snapshot_path.exists():
        return None
    
    with open(snapshot_path, 'r', encoding='utf-8') as f:
        snapshot = json.load(f)
    
    return snapshot.get("data")


def compare_snapshots(actual: Dict, expected: Dict, keys: Optional[List[str]] = None) -> tuple[bool, List[str]]:
    """
    比较快照
    
    Returns:
        (是否相同, 不同字段列表)
    """
    diffs = []
    
    if keys is None:
        # 比较所有 key
        all_keys = set(actual.keys()) | set(expected.keys())
    else:
        all_keys = keys
    
    for key in all_keys:
        actual_val = stable_serialize(actual.get(key))
        expected_val = stable_serialize(expected.get(key))
        
        if actual_val != expected_val:
            diffs.append(key)
    
    return len(diffs) == 0, diffs


def snapshot_route(route_nodes: List) -> List[Dict]:
    """生成路径快照"""
    return [
        {
            "kind": node.kind.value if hasattr(node.kind, 'value') else str(node.kind),
            "enemy_id": getattr(node, 'enemy_id', None),
            "event_id": getattr(node, 'event_id', None),
        }
        for node in route_nodes
    ]


def snapshot_battle_state(state: Dict, turns: int = 3) -> Dict:
    """生成战斗状态快照 (前 N 回合)"""
    return {
        "player_hp": state.get("current_hp"),
        "player_energy": state.get("energy"),
        "enemy_hp": state.get("enemy_hp"),
        "hand_size": len(state.get("hand", [])),
        "deck_size": state.get("deck_size"),
        "turns_captured": turns,
    }


def snapshot_rewards(reward_candidates: Dict) -> Dict:
    """生成奖励候选快照"""
    return {
        "cards": sorted([c.get("id") for c in reward_candidates.get("cards", [])]),
        "relics": sorted([r.get("id") for r in reward_candidates.get("relics", [])]),
    }


def snapshot_meta(profile: Dict) -> Dict:
    """生成 meta profile 快照"""
    return {
        "total_points": profile.get("total_points"),
        "available_points": profile.get("available_points"),
        "unlocks": {
            k: sorted(v) for k, v in profile.get("unlocks", {}).items()
        },
        "stats": profile.get("stats", {}),
    }


def generate_golden_snapshots(snapshot_dir: Path, scenarios: Dict[str, Any]):
    """
    为多个 scenario 生成 golden 快照
    
    Usage:
        generate_golden_snapshots(
            Path("tests/golden"),
            {
                "m3_meta_points": {"points": 100, "unlocks": [...]},
                "m3_character_starters": {"developer": {...}},
            }
        )
    """
    for snapshot_id, data in scenarios.items():
        save_snapshot(snapshot_dir, snapshot_id, data)
        print(f"✅ Created: {snapshot_id}.json")


class SnapshotManager:
    """快照管理器"""
    
    def __init__(self, snapshot_dir: str = "tests/golden"):
        self.snapshot_dir = Path(snapshot_dir)
    
    def verify(self, snapshot_id: str, actual: Dict, keys: Optional[List[str]] = None) -> tuple[bool, str]:
        """
        验证快照
        
        Returns:
            (是否通过, 消息)
        """
        expected = load_snapshot(self.snapshot_dir, snapshot_id)
        
        if expected is None:
            return False, f"Snapshot not found: {snapshot_id}"
        
        is_same, diffs = compare_snapshots(actual, expected, keys)
        
        if is_same:
            return True, f"✅ {snapshot_id}: matched"
        else:
            return False, f"❌ {snapshot_id} diff: {diffs}"
    
    def update(self, snapshot_id: str, data: Dict):
        """更新快照"""
        save_snapshot(self.snapshot_dir, snapshot_id, data)
        print(f"✅ Updated: {snapshot_id}.json")
    
    def diff(self, snapshot_id: str, actual: Dict) -> Dict:
        """获取差异"""
        expected = load_snapshot(self.snapshot_dir, snapshot_id)
        if expected is None:
            return {"error": f"Snapshot not found: {snapshot_id}"}
        
        is_same, diffs = compare_snapshots(actual, expected)
        
        return {
            "snapshot_id": snapshot_id,
            "matched": is_same,
            "differences": diffs,
            "expected": expected,
            "actual": actual,
        }
