"""Repository loading and run bootstrap for the pixel UI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from git_dungeon.config import GameConfig
from git_dungeon.content.runtime_loader import load_runtime_content
from git_dungeon.core.git_parser import CommitInfo, GitParser
from git_dungeon.engine import GameState, create_rng
from git_dungeon.engine.auto_policy import REST_ACTION_FOCUS, REST_ACTION_HEAL
from git_dungeon.engine.node_actions import (
    EventResolution,
    RestResolution,
    ShopResolution,
    apply_event_resolution,
    resolve_rest_action,
    resolve_shop_purchase,
    select_event_for_node,
    shop_offers_for_node,
)
from git_dungeon.engine.node_flow import ChapterNodeGenerator
from git_dungeon.engine.route import NodeKind, RouteNode
from git_dungeon.engine.rules import ChapterSystem
from git_dungeon.engine.rules.economy_rules import PlayerInventory
from git_dungeon.engine.rules.chapter_rules import build_chapter_configs
from git_dungeon.i18n import i18n, normalize_lang


@dataclass(frozen=True)
class RunSummary:
    """Small load summary for Phase 1 pixel screens."""

    repo_path: str
    total_commits: int
    chapter_count: int
    current_chapter_name: str
    seed: int | None


@dataclass(frozen=True)
class PlayerSnapshot:
    hp: int
    max_hp: int
    mp: int
    max_mp: int
    attack: int
    gold: int


@dataclass(frozen=True)
class NodeSnapshot:
    node_id: str
    kind: str
    position: int
    label: str
    is_current: bool
    is_visited: bool
    is_playable_now: bool


@dataclass(frozen=True)
class EventChoiceSnapshot:
    index: int
    choice_id: str
    effects: tuple[str, ...]


@dataclass(frozen=True)
class EventSnapshot:
    event_id: str
    choices: tuple[EventChoiceSnapshot, ...]


@dataclass(frozen=True)
class RestOptionSnapshot:
    action: str
    label: str
    detail: str


@dataclass(frozen=True)
class ShopOfferSnapshot:
    index: int
    offer_id: str
    label: str
    cost: int
    heal: int
    attack: int
    mp: int
    max_hp: int
    affordable: bool


class GameRunner:
    """Owns non-interactive repository loading for the pixel UI."""

    def __init__(
        self,
        repo_path: str,
        seed: int | None = None,
        lang: str = "en",
        content_pack_args: list[str] | None = None,
        content_dir: str | None = None,
    ) -> None:
        self.repo_path = repo_path
        self.seed = seed
        self.lang = normalize_lang(lang)
        i18n.load_language(self.lang)

        self.content_runtime = load_runtime_content(
            content_dir=content_dir,
            content_pack_args=content_pack_args,
        )
        self.rng = create_rng(seed)
        self.chapter_system = ChapterSystem(
            rng=self.rng,
            chapter_configs=build_chapter_configs(self.content_runtime.chapter_overrides),
        )
        self.node_generator = ChapterNodeGenerator()
        self.parser: GitParser | None = None
        self.commits: list[CommitInfo] = []
        self.state: GameState | None = None
        self.inventory = PlayerInventory()
        self._chapter_nodes: dict[str, list[RouteNode]] = {}
        self._chapter_node_cursor: dict[str, int] = {}
        self.loaded = False

    def load_repository(self) -> RunSummary:
        """Load commits and build the initial state without printing or reading input."""
        repo_path = Path(self.repo_path)
        if not repo_path.exists():
            raise ValueError(f"Repository not found: {self.repo_path}")

        parser = GitParser(GameConfig())
        if not parser.load_repository(str(repo_path)):
            raise ValueError(f"Failed to load repository: {self.repo_path}")

        commits = parser.get_commit_history()
        if not commits:
            raise ValueError("No commits found")

        self.chapter_system.parse_chapters(commits)
        if not self.chapter_system.chapters:
            raise ValueError("No chapters could be built")

        self.parser = parser
        self.commits = commits
        self.state = GameState(
            seed=self.seed,
            repo_path=str(repo_path),
            total_commits=len(commits),
            current_commit_index=0,
            difficulty="normal",
        )
        self.state.player.character.current_hp = 100
        self.state.player.character.current_mp = 50
        self.state.route_state = {
            "current_node_id": "",
            "visited_nodes": [],
            "route_flags": {},
            "chapter_nodes": {},
        }
        self.inventory.gold = self.state.player.gold
        self.loaded = True
        self.prepare_current_chapter_nodes()
        return self.summary()

    def summary(self) -> RunSummary:
        """Return the current load summary."""
        if not self.loaded or self.state is None:
            raise RuntimeError("Repository is not loaded")
        chapter = self.chapter_system.get_current_chapter()
        return RunSummary(
            repo_path=self.state.repo_path,
            total_commits=self.state.total_commits,
            chapter_count=len(self.chapter_system.chapters),
            current_chapter_name=getattr(chapter, "name", "") if chapter else "",
            seed=self.seed,
        )

    def current_chapter(self) -> Any:
        """Return the current chapter object for later screens."""
        return self.chapter_system.get_current_chapter()

    def player_snapshot(self) -> PlayerSnapshot:
        """Return display-safe player stats."""
        state = self._require_state()
        player = state.player.character
        return PlayerSnapshot(
            hp=player.current_hp,
            max_hp=player.stats.hp.value,
            mp=player.current_mp,
            max_mp=player.stats.mp.value,
            attack=player.stats.attack.value,
            gold=state.player.gold,
        )

    def prepare_current_chapter_nodes(self) -> list[RouteNode]:
        """Generate and cache deterministic nodes for the current chapter."""
        state = self._require_state()
        chapter = self.current_chapter()
        if chapter is None:
            return []
        chapter_id = chapter.chapter_id
        if chapter_id not in self._chapter_nodes:
            nodes = self.node_generator.build_nodes(
                seed=int(self.seed or 0),
                chapter_index=chapter.chapter_index,
                chapter_enemy_count=len(getattr(chapter, "commits", [])),
                difficulty=1.0,
                has_boss=True,
                has_events=bool(self.content_runtime.registry.events),
            )
            self._chapter_nodes[chapter_id] = nodes
            self._chapter_node_cursor[chapter_id] = 0
            chapter.enemies_defeated = 0
            if state.route_state is not None:
                chapter_nodes = state.route_state.setdefault("chapter_nodes", {})
                chapter_nodes[chapter_id] = [node.kind.value for node in nodes]
        return self._chapter_nodes[chapter_id]

    def route_nodes(self) -> tuple[NodeSnapshot, ...]:
        """Return current chapter route nodes for MapScreen."""
        state = self._require_state()
        chapter = self.current_chapter()
        if chapter is None:
            return ()
        nodes = self.prepare_current_chapter_nodes()
        cursor = self._chapter_node_cursor.get(chapter.chapter_id, 0)
        visited = set()
        if state.route_state is not None:
            visited = set(state.route_state.setdefault("visited_nodes", []))
        return tuple(
            NodeSnapshot(
                node_id=node.node_id,
                kind=node.kind.value,
                position=node.position,
                label=f"{node.position + 1:02d} {node.kind.value.upper()}",
                is_current=index == cursor,
                is_visited=node.node_id in visited,
                is_playable_now=index == cursor and node.kind in self.non_combat_kinds(),
            )
            for index, node in enumerate(nodes)
        )

    def current_node(self) -> RouteNode | None:
        """Return the next unresolved route node."""
        chapter = self.current_chapter()
        if chapter is None:
            return None
        nodes = self.prepare_current_chapter_nodes()
        cursor = self._chapter_node_cursor.get(chapter.chapter_id, 0)
        if cursor >= len(nodes):
            return None
        node = nodes[cursor]
        state = self._require_state()
        if state.route_state is not None:
            state.route_state["current_node_id"] = node.node_id
        return node

    def current_node_snapshot(self) -> NodeSnapshot | None:
        """Return display-safe data for the current route node."""
        current = self.current_node()
        if current is None:
            return None
        for snapshot in self.route_nodes():
            if snapshot.node_id == current.node_id:
                return snapshot
        return None

    def event_for_node(self, node: RouteNode | None = None) -> EventSnapshot | None:
        """Return the deterministic event for an event node."""
        node = node or self._require_current_node(NodeKind.EVENT)
        chapter = self._require_chapter()
        event = select_event_for_node(
            list(self.content_runtime.registry.events.values()),
            seed=int(self.seed or 0),
            chapter=chapter,
            node=node,
        )
        if event is None or not event.choices:
            return None
        return EventSnapshot(
            event_id=str(event.id),
            choices=tuple(
                EventChoiceSnapshot(
                    index=index,
                    choice_id=str(choice.id),
                    effects=tuple(str(effect.opcode) for effect in choice.effects),
                )
                for index, choice in enumerate(event.choices)
            ),
        )

    def resolve_current_event(self, choice_index: int) -> EventResolution:
        """Apply the selected event choice and advance the route cursor."""
        node = self._require_current_node(NodeKind.EVENT)
        chapter = self._require_chapter()
        event = select_event_for_node(
            list(self.content_runtime.registry.events.values()),
            seed=int(self.seed or 0),
            chapter=chapter,
            node=node,
        )
        if event is None:
            raise RuntimeError("Current event node has no event definition")
        result = apply_event_resolution(self._require_state(), event, choice_index, self.rng)
        self._mark_current_node_resolved()
        return result

    def rest_options(self) -> tuple[RestOptionSnapshot, ...]:
        """Return rest actions with concrete effects."""
        state = self._require_state()
        player = state.player.character
        heal_amount = max(10, int(player.stats.hp.value * 0.3))
        actual_heal = min(heal_amount, player.stats.hp.value - player.current_hp)
        return (
            RestOptionSnapshot(
                action=REST_ACTION_HEAL,
                label="Heal",
                detail=f"Restore {actual_heal} HP",
            ),
            RestOptionSnapshot(
                action=REST_ACTION_FOCUS,
                label="Focus",
                detail="Attack +2, Max HP +5, HP +5",
            ),
        )

    def resolve_current_rest(self, action: str) -> RestResolution:
        """Apply a rest action and advance the route cursor."""
        self._require_current_node(NodeKind.REST)
        result = resolve_rest_action(self._require_state(), action)
        self._mark_current_node_resolved()
        return result

    def shop_offers(self) -> tuple[ShopOfferSnapshot, ...]:
        """Return deterministic offers for the current shop node."""
        node = self._require_current_node(NodeKind.SHOP)
        chapter = self._require_chapter()
        gold = self._require_state().player.gold
        offers = shop_offers_for_node(int(self.seed or 0), chapter, node)
        return tuple(
            ShopOfferSnapshot(
                index=index,
                offer_id=str(offer["id"]),
                label=str(offer["label"]),
                cost=int(offer["cost"]),
                heal=int(offer.get("heal", 0)),
                attack=int(offer.get("atk", 0)),
                mp=int(offer.get("mp", 0)),
                max_hp=int(offer.get("hp_max", 0)),
                affordable=int(offer["cost"]) <= gold,
            )
            for index, offer in enumerate(offers)
        )

    def resolve_current_shop(self, selected_idx: int | None) -> ShopResolution:
        """Apply a shop choice and advance the route cursor."""
        node = self._require_current_node(NodeKind.SHOP)
        chapter = self._require_chapter()
        offers = shop_offers_for_node(int(self.seed or 0), chapter, node)
        result = resolve_shop_purchase(self._require_state(), self.inventory, offers, selected_idx)
        self._mark_current_node_resolved()
        return result

    @staticmethod
    def non_combat_kinds() -> set[NodeKind]:
        return {NodeKind.EVENT, NodeKind.REST, NodeKind.SHOP}

    def _mark_current_node_resolved(self) -> None:
        state = self._require_state()
        chapter = self._require_chapter()
        nodes = self.prepare_current_chapter_nodes()
        cursor = self._chapter_node_cursor.get(chapter.chapter_id, 0)
        if cursor >= len(nodes):
            return
        node = nodes[cursor]
        self._chapter_node_cursor[chapter.chapter_id] = cursor + 1
        if state.route_state is not None:
            visited = state.route_state.setdefault("visited_nodes", [])
            visited.append(node.node_id)
            state.route_state["current_node_id"] = ""

    def _require_state(self) -> GameState:
        if not self.loaded or self.state is None:
            raise RuntimeError("Repository is not loaded")
        return self.state

    def _require_chapter(self) -> Any:
        chapter = self.current_chapter()
        if chapter is None:
            raise RuntimeError("No current chapter")
        return chapter

    def _require_current_node(self, expected_kind: NodeKind) -> RouteNode:
        node = self.current_node()
        if node is None:
            raise RuntimeError("No current route node")
        if node.kind != expected_kind:
            raise RuntimeError(f"Current node is {node.kind.value}, not {expected_kind.value}")
        return node
