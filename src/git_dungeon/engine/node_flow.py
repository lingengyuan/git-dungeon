"""Deterministic chapter node generation for CLI progression."""

from __future__ import annotations

from dataclasses import dataclass

from git_dungeon.engine.rng import DefaultRNG
from git_dungeon.engine.route import NodeKind, NodeTag, RouteNode


@dataclass(frozen=True)
class NodeGenerationConfig:
    """Configurable knobs for chapter node generation."""

    min_nodes: int = 6
    max_nodes: int = 12
    event_ratio: float = 0.30
    battle_ratio: float = 0.50
    rest_ratio: float = 0.10
    shop_ratio: float = 0.10


class ChapterNodeGenerator:
    """Build deterministic node lists from seed/chapter inputs."""

    def __init__(self, config: NodeGenerationConfig | None = None) -> None:
        self.config = config or NodeGenerationConfig()

    def build_nodes(
        self,
        *,
        seed: int,
        chapter_index: int,
        chapter_enemy_count: int,
        difficulty: float = 1.0,
        has_boss: bool = True,
        has_events: bool = True,
    ) -> list[RouteNode]:
        """Generate one deterministic list of route nodes for a chapter."""
        rng = DefaultRNG(seed=seed + (chapter_index * 9973))
        node_count = self._resolve_node_count(chapter_enemy_count, difficulty)

        if node_count <= 0:
            return []

        reserve_tail = 1 if has_boss else 0
        body_count = max(1, node_count - reserve_tail)

        event_count = 1 if has_events and body_count >= 4 else 0
        rest_count = 1 if body_count >= 5 else 0
        shop_count = 1 if body_count >= 6 else 0
        elite_count = 1 if chapter_index >= 1 and body_count >= 7 else 0

        minimum_non_battle = event_count + rest_count + shop_count + elite_count
        battle_count = max(1, body_count - minimum_non_battle)

        kinds: list[NodeKind] = [NodeKind.BATTLE] * battle_count
        kinds.extend([NodeKind.EVENT] * event_count)
        kinds.extend([NodeKind.REST] * rest_count)
        kinds.extend([NodeKind.SHOP] * shop_count)
        kinds.extend([NodeKind.ELITE] * elite_count)

        while len(kinds) < body_count:
            kinds.append(NodeKind.BATTLE)

        rng.shuffle(kinds)

        # Keep opening pacing predictable: first node is always combat.
        if kinds and kinds[0] != NodeKind.BATTLE:
            for idx, kind in enumerate(kinds):
                if kind == NodeKind.BATTLE:
                    kinds[0], kinds[idx] = kinds[idx], kinds[0]
                    break

        if has_boss:
            kinds.append(NodeKind.BOSS)

        nodes: list[RouteNode] = []
        for idx, kind in enumerate(kinds):
            node = RouteNode(
                node_id=f"ch{chapter_index}_node{idx}_{kind.value}",
                kind=kind,
                position=idx,
                tags=self._tags_for_kind(kind, rng),
                meta={"chapter_index": chapter_index, "node_index": idx},
            )
            nodes.append(node)

        return nodes

    def _resolve_node_count(self, chapter_enemy_count: int, difficulty: float) -> int:
        base = max(self.config.min_nodes, chapter_enemy_count + 2)
        if difficulty >= 1.5:
            base += 1
        if difficulty <= 0.8:
            base -= 1
        return max(self.config.min_nodes, min(self.config.max_nodes, base))

    @staticmethod
    def _tags_for_kind(kind: NodeKind, rng: DefaultRNG) -> list[NodeTag]:
        if kind == NodeKind.EVENT:
            return [NodeTag.GREED] if rng.random() < 0.4 else [NodeTag.SAFE]
        if kind == NodeKind.SHOP:
            return [NodeTag.GREED]
        if kind == NodeKind.REST:
            return [NodeTag.SAFE]
        if kind == NodeKind.ELITE:
            return [NodeTag.RISK]
        if kind == NodeKind.BOSS:
            return [NodeTag.RISK]
        return [NodeTag.RISK] if rng.random() < 0.35 else [NodeTag.SAFE]


def summarize_node_kinds(nodes: list[RouteNode]) -> dict[str, int]:
    """Return deterministic node type counts for metrics/printing."""
    counts: dict[str, int] = {}
    for node in nodes:
        key = node.kind.value
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))
