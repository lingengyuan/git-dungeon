"""
路径系统 - Chapter Route (节点图)

定义游戏的章节路径结构，包括战斗、事件、商店、休息、精英、BOSS 等节点类型。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

from git_dungeon.engine.rng import RNG, DefaultRNG


class NodeKind(Enum):
    """节点类型"""
    BATTLE = "battle"
    EVENT = "event"
    SHOP = "shop"
    REST = "rest"
    ELITE = "elite"
    BOSS = "boss"
    TREASURE = "treasure"


class NodeTag(Enum):
    """节点标签（用于路径选择 bias）"""
    RISK = "risk"           # 高风险路径
    SAFE = "safe"           # 安全路径
    GREED = "greed"         # 贪心路径
    DEBUG_HEAVY = "debug_heavy"   # Debug 敌人较多
    TEST_HEAVY = "test_heavy"     # Test 敌人较多
    REFACTOR_HEAVY = "refactor_heavy"  # Refactor 敌人较多


@dataclass
class RouteNode:
    """路径节点"""
    node_id: str
    kind: NodeKind
    position: int  # 在路径中的位置 (0=起点)
    tags: List[NodeTag] = field(default_factory=list)
    meta: Dict = field(default_factory=dict)  # 额外数据 (enemy_id, event_id 等)
    
    def __hash__(self):
        return hash(self.node_id)
    
    def __eq__(self, other):
        if isinstance(other, RouteNode):
            return self.node_id == other.node_id
        return False


@dataclass 
class RouteGraph:
    """章节路径图"""
    chapter_index: int
    nodes: List[RouteNode]
    edges: Dict[str, List[str]]  # node_id -> [next_node_ids]
    seed: int
    
    def __post_init__(self):
        # 构建节点索引
        self._node_index: Dict[str, RouteNode] = {}
        for node in self.nodes:
            self._node_index[node.node_id] = node
    
    def get_node(self, node_id: str) -> Optional[RouteNode]:
        """获取节点"""
        return self._node_index.get(node_id)
    
    def get_next_nodes(self, node_id: str) -> List[RouteNode]:
        """获取下一批可选节点"""
        next_ids = self.edges.get(node_id, [])
        return [self._node_index[nid] for nid in next_ids if nid in self._node_index]
    
    def get_start_node(self) -> RouteNode:
        """获取起始节点"""
        return self.nodes[0]
    
    def get_end_nodes(self) -> List[RouteNode]:
        """获取终点节点（BOSS）"""
        return [n for n in self.nodes if n.kind == NodeKind.BOSS]
    
    def get_node_sequence(self) -> List[NodeKind]:
        """获取节点类型序列（用于 Golden 测试）"""
        return [n.kind for n in self.nodes]
    
    def get_path_tags(self) -> List[NodeTag]:
        """获取路径上的所有标签"""
        tags = []
        for node in self.nodes:
            tags.extend(node.tags)
        return tags


def build_route(
    commits: List,
    seed: int,
    chapter_index: int,
    difficulty: float = 1.0,
    node_count: int = 12
) -> RouteGraph:
    """
    构建章节路径
    
    Args:
        commits: Git 提交列表
        seed: 随机种子
        chapter_index: 章节索引 (0-based)
        difficulty: 难度系数 (1.0 = 正常)
        node_count: 节点数量 (10-14)
    
    Returns:
        RouteGraph: 章节路径图
    """
    rng = DefaultRNG(seed=seed + chapter_index * 1000)
    
    nodes: List[RouteNode] = []
    edges: Dict[str, List[str]] = {}
    
    # 定义节点类型权重（根据位置）
    def get_kind_weights(position: int, total: int) -> Dict[NodeKind, float]:
        """根据位置获取节点类型权重"""
        weights = {
            NodeKind.BATTLE: 0.5,
            NodeKind.EVENT: 0.2,
            NodeKind.SHOP: 0.1,
            NodeKind.REST: 0.1,
            NodeKind.ELITE: 0.0,
            NodeKind.BOSS: 0.0,
            NodeKind.TREASURE: 0.1,
        }
        
        # 精英节点：1/3 概率出现在中段
        if position > total // 3 and position < total * 2 // 3:
            weights[NodeKind.ELITE] = 0.15
            weights[NodeKind.BATTLE] -= 0.05
            weights[NodeKind.EVENT] -= 0.05
        
        # BOSS 在末尾
        if position == total - 1:
            return {NodeKind.BOSS: 1.0}
        
        return weights
    
    def choose_kind(weights: Dict[NodeKind, float], rng: RNG) -> NodeKind:
        """根据权重选择节点类型"""
        total = sum(weights.values())
        r = rng.random() * total
        cumsum = 0
        for kind, weight in weights.items():
            cumsum += weight
            if r <= cumsum:
                return kind
        return NodeKind.BATTLE
    
    def get_tags_for_kind(kind: NodeKind, rng: RNG) -> List[NodeTag]:
        """根据节点类型生成标签"""
        tags = []
        
        if kind in (NodeKind.BATTLE, NodeKind.ELITE):
            # 随机选择风险标签
            if rng.random() < 0.3:
                tags.append(NodeTag.RISK)
            else:
                tags.append(NodeTag.SAFE)
        
        if kind == NodeKind.EVENT:
            # 事件有贪心选项
            if rng.random() < 0.4:
                tags.append(NodeTag.GREED)
        
        if kind == NodeKind.REST:
            tags.append(NodeTag.SAFE)
        
        if kind == NodeKind.ELITE:
            tags.append(NodeTag.RISK)
        
        return tags
    
    # 构建节点
    for i in range(node_count):
        weights = get_kind_weights(i, node_count)
        kind = choose_kind(weights, rng)
        tags = get_tags_for_kind(kind, rng)
        
        # 生成节点 ID
        node_id = f"ch{chapter_index}_node{i}_{kind.value}"
        
        node = RouteNode(
            node_id=node_id,
            kind=kind,
            position=i,
            tags=tags,
            meta={}
        )
        nodes.append(node)
    
    # 构建边（分叉逻辑）
    for i in range(len(nodes) - 1):
        current = nodes[i]
        next_node = nodes[i + 1]
        
        # 起点节点有 2-3 个分支
        if i == 0:
            # 创建分叉点
            fork_node = RouteNode(
                node_id=f"ch{chapter_index}_fork{i}",
                kind=NodeKind.BATTLE,  # 分叉点本身是个战斗
                position=i,
                tags=[NodeTag.SAFE],
                meta={}
            )
            nodes[i] = fork_node
            current = fork_node
            
            # 2-3 个分支
            num_choices = 2 if rng.random() < 0.7 else 3
            edge_ids = []
            for j in range(num_choices):
                # 每个分支至少 1 个节点
                branch_end = i + 1 + rng.randint(1, 3)
                if branch_end >= len(nodes):
                    branch_end = len(nodes) - 1
                
                branch_end_node = nodes[branch_end]
                edge_ids.append(branch_end_node.node_id)
                
                # 如果分支中间有节点，连接它们
                if branch_end > i + 1:
                    nodes[i + 1].position = i + 1
                    edge_ids = [nodes[i + 1].node_id, branch_end_node.node_id]
                    break
            
            edges[current.node_id] = edge_ids
        else:
            # 普通节点：单一路径
            if current.node_id not in edges:
                edges[current.node_id] = [next_node.node_id]
    
    # 确保 BOSS 有入边
    boss = nodes[-1]
    if boss.kind == NodeKind.BOSS:
        # 找到最后一个非 BOSS 节点，指向 BOSS
        for i in range(len(nodes) - 2, -1, -1):
            if nodes[i].kind != NodeKind.BOSS:
                if nodes[i].node_id not in edges:
                    edges[nodes[i].node_id] = []
                if boss.node_id not in edges[nodes[i].node_id]:
                    edges[nodes[i].node_id].append(boss.node_id)
                break
    
    return RouteGraph(
        chapter_index=chapter_index,
        nodes=nodes,
        edges=edges,
        seed=seed
    )


def next_nodes(current_node_id: str, route: RouteGraph) -> List[RouteNode]:
    """
    获取当前节点的下一批可选节点
    
    Args:
        current_node_id: 当前节点 ID
        route: 路径图
    
    Returns:
        下一批可选节点列表
    """
    return route.get_next_nodes(current_node_id)


def get_route_stats(route: RouteGraph) -> Dict:
    """获取路径统计信息"""
    stats = {
        "total_nodes": len(route.nodes),
        "battles": 0,
        "events": 0,
        "shops": 0,
        "rests": 0,
        "elites": 0,
        "bosses": 0,
        "treasures": 0,
        "risk_count": 0,
        "safe_count": 0,
    }
    
    for node in route.nodes:
        kind_stats = {
            NodeKind.BATTLE: "battles",
            NodeKind.EVENT: "events",
            NodeKind.SHOP: "shops",
            NodeKind.REST: "rests",
            NodeKind.ELITE: "elites",
            NodeKind.BOSS: "bosses",
            NodeKind.TREASURE: "treasures",
        }
        stats[kind_stats[node.kind]] += 1
        
        if NodeTag.RISK in node.tags:
            stats["risk_count"] += 1
        if NodeTag.SAFE in node.tags:
            stats["safe_count"] += 1
    
    stats["fork_count"] = sum(1 for n in route.nodes if len(route.edges.get(n.node_id, [])) > 1)
    
    return stats
