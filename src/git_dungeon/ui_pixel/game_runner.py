"""Repository loading and run bootstrap for the pixel UI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from git_dungeon.config import GameConfig
from git_dungeon.content.runtime_loader import load_runtime_content
from git_dungeon.core.git_parser import CommitInfo, GitParser
from git_dungeon.engine import EnemyState, GameState, create_rng
from git_dungeon.engine.auto_policy import REST_ACTION_FOCUS, REST_ACTION_HEAL
from git_dungeon.engine.combat_actions import CombatStepResult, resolve_combat_step
from git_dungeon.engine.mutators import (
    MutatorConfig,
    apply_enemy_mutator,
    apply_reward_mutator,
    get_mutator_config,
)
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
from git_dungeon.engine.rules import BossState, BossSystem, ChapterSystem, CombatRules, ProgressionRules
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


@dataclass(frozen=True)
class EnemySnapshot:
    name: str
    hp: int
    max_hp: int
    attack: int
    is_boss: bool
    is_elite: bool
    phase: str = ""


@dataclass(frozen=True)
class BattleSnapshot:
    player: PlayerSnapshot
    enemy: EnemySnapshot
    turn: int
    can_escape: bool
    skill_cost: int
    message: str
    battle_over: bool
    won: bool


@dataclass(frozen=True)
class RewardSnapshot:
    exp: int
    gold: int
    level_up: bool
    new_level: int


@dataclass(frozen=True)
class DungeonTrapResult:
    trap_id: str
    damage: int
    already_triggered: bool


class GameRunner:
    """Owns non-interactive repository loading for the pixel UI."""

    def __init__(
        self,
        repo_path: str,
        seed: int | None = None,
        lang: str = "en",
        content_pack_args: list[str] | None = None,
        content_dir: str | None = None,
        mutator: str = "none",
    ) -> None:
        self.repo_path = repo_path
        self.seed = seed
        self.lang = normalize_lang(lang)
        i18n.load_language(self.lang)
        self.mutator: MutatorConfig = get_mutator_config(mutator)

        self.content_runtime = load_runtime_content(
            content_dir=content_dir,
            content_pack_args=content_pack_args,
        )
        self.rng = create_rng(seed)
        self.combat_rules = CombatRules(rng=self.rng)
        self.progression_rules = ProgressionRules(rng=self.rng)
        self.chapter_system = ChapterSystem(
            rng=self.rng,
            chapter_configs=build_chapter_configs(self.content_runtime.chapter_overrides),
        )
        self.boss_system = BossSystem(rng=self.rng)
        self.node_generator = ChapterNodeGenerator()
        self.parser: GitParser | None = None
        self.commits: list[CommitInfo] = []
        self.state: GameState | None = None
        self.inventory = PlayerInventory()
        self.current_enemy: EnemyState | BossState | None = None
        self.current_battle_node: RouteNode | None = None
        self.current_battle_commit: Any = None
        self.current_battle_is_boss = False
        self.current_battle_is_elite = False
        self.current_battle_turn = 0
        self.last_reward: RewardSnapshot | None = None
        self.dungeon_player_coord: tuple[int, int] | None = None
        self.dungeon_consumed_traps: set[str] = set()
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
                is_playable_now=(
                    index == cursor
                    and node.kind in self.non_combat_kinds().union(self.combat_kinds())
                ),
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

    def start_current_battle(self) -> BattleSnapshot:
        """Create the enemy for the current battle/elite/boss node."""
        node = self.current_node()
        if node is None:
            raise RuntimeError("No current route node")
        if node.kind not in {NodeKind.BATTLE, NodeKind.ELITE, NodeKind.BOSS}:
            raise RuntimeError(f"Current node is not combat: {node.kind.value}")
        chapter = self._require_chapter()
        enemy: EnemyState | BossState
        commit: Any = None
        is_boss = node.kind == NodeKind.BOSS
        is_elite = node.kind == NodeKind.ELITE

        if is_boss and getattr(chapter, "is_boss_chapter", False):
            boss = self.chapter_system.get_chapter_boss(chapter, self.boss_system)
            if boss is None:
                raise RuntimeError("Boss chapter has no boss definition")
            enemy = boss
        else:
            commit = self._resolve_commit_for_node(chapter, node)
            enemy_state = self._create_enemy(commit)
            if is_elite:
                enemy_state.current_hp = int(enemy_state.current_hp * 1.35)
                enemy_state.max_hp = enemy_state.current_hp
                enemy_state.attack = int(enemy_state.attack * 1.25)
                enemy_state.name = f"Elite {enemy_state.name}"
            if is_boss:
                enemy_state.current_hp = int(enemy_state.current_hp * 1.6)
                enemy_state.max_hp = enemy_state.current_hp
                enemy_state.attack = int(enemy_state.attack * 1.45)
                enemy_state.name = f"{chapter.name} Guardian"
            enemy = enemy_state

        state = self._require_state()
        state.in_combat = True
        if isinstance(enemy, EnemyState):
            state.current_enemy = enemy
        self.current_enemy = enemy
        self.current_battle_node = node
        self.current_battle_commit = commit
        self.current_battle_is_boss = is_boss
        self.current_battle_is_elite = is_elite
        self.current_battle_turn = 1
        self.last_reward = None
        return self.battle_snapshot("Battle started")

    def battle_snapshot(self, message: str = "") -> BattleSnapshot:
        """Return display-safe battle state."""
        enemy = self._require_current_enemy()
        return BattleSnapshot(
            player=self.player_snapshot(),
            enemy=self._enemy_snapshot(enemy),
            turn=max(1, self.current_battle_turn),
            can_escape=not self.current_battle_is_boss,
            skill_cost=15 if self.current_battle_is_boss else 10,
            message=message,
            battle_over=not enemy.is_alive or not self._require_state().player.character.is_alive,
            won=not enemy.is_alive,
        )

    def resolve_battle_action(self, action: str) -> tuple[CombatStepResult, BattleSnapshot]:
        """Resolve one battle action and advance route/rewards when battle ends."""
        state = self._require_state()
        enemy = self._require_current_enemy()
        result = resolve_combat_step(
            state,
            enemy,
            action,
            rng=self.rng,
            combat_rules=self.combat_rules,
            is_boss=self.current_battle_is_boss,
            boss_system=self.boss_system,
        )
        if result.accepted and not result.battle_over:
            self.current_battle_turn += 1

        if result.battle_over:
            state.in_combat = False
            if result.won:
                self._finish_battle_victory()
            elif result.escaped:
                self._clear_battle()
            elif result.player_defeated:
                state.is_game_over = True
            snapshot = self.battle_snapshot(result.message) if self.current_enemy else self._ended_snapshot(result)
            return result, snapshot

        return result, self.battle_snapshot(result.message)

    def last_reward_snapshot(self) -> RewardSnapshot | None:
        return self.last_reward

    @staticmethod
    def non_combat_kinds() -> set[NodeKind]:
        return {NodeKind.EVENT, NodeKind.REST, NodeKind.SHOP}

    @staticmethod
    def combat_kinds() -> set[NodeKind]:
        return {NodeKind.BATTLE, NodeKind.ELITE, NodeKind.BOSS}

    def _finish_battle_victory(self) -> None:
        chapter = self._require_chapter()
        enemy = self._require_current_enemy()
        if isinstance(enemy, BossState):
            self.last_reward = self._grant_boss_rewards(enemy)
        else:
            chapter.enemies_defeated += 1
            if self.current_battle_commit is not None:
                self._require_state().enemies_defeated.append(self.current_battle_commit.hexsha[:7])
            self.last_reward = self._grant_enemy_rewards(enemy, chapter)
        self._mark_current_node_resolved()
        self._clear_battle()

    def _grant_enemy_rewards(self, enemy: EnemyState, chapter: Any) -> RewardSnapshot:
        exp = int(enemy.exp_reward * chapter.config.exp_bonus)
        gold = int(enemy.gold_reward * chapter.config.gold_bonus)
        exp, gold = apply_reward_mutator(exp, gold, self.mutator)
        state = self._require_state()
        state.player.gold += gold
        self.inventory.gold += gold
        did_level_up, new_level = state.player.character.gain_experience(exp)
        return RewardSnapshot(exp=exp, gold=gold, level_up=did_level_up, new_level=new_level)

    def _grant_boss_rewards(self, boss: BossState) -> RewardSnapshot:
        rewards = self.boss_system.get_boss_rewards(boss)
        exp, gold = apply_reward_mutator(int(rewards["exp"]), int(rewards["gold"]), self.mutator)
        state = self._require_state()
        state.player.gold += gold
        self.inventory.gold += gold
        did_level_up, new_level = state.player.character.gain_experience(exp)
        return RewardSnapshot(exp=exp, gold=gold, level_up=did_level_up, new_level=new_level)

    def _clear_battle(self) -> None:
        state = self._require_state()
        state.current_enemy = None
        self.current_enemy = None
        self.current_battle_node = None
        self.current_battle_commit = None
        self.current_battle_is_boss = False
        self.current_battle_is_elite = False
        self.current_battle_turn = 0

    def _ended_snapshot(self, result: CombatStepResult) -> BattleSnapshot:
        player = self.player_snapshot()
        return BattleSnapshot(
            player=player,
            enemy=EnemySnapshot(
                name="Battle ended",
                hp=0,
                max_hp=1,
                attack=0,
                is_boss=False,
                is_elite=False,
            ),
            turn=max(1, self.current_battle_turn),
            can_escape=False,
            skill_cost=10,
            message=result.message,
            battle_over=True,
            won=result.won,
        )

    def _enemy_snapshot(self, enemy: EnemyState | BossState) -> EnemySnapshot:
        phase = ""
        if isinstance(enemy, BossState):
            phase = "enraged" if enemy.is_enraged else enemy.phase_name
        return EnemySnapshot(
            name=enemy.name,
            hp=enemy.current_hp,
            max_hp=enemy.max_hp,
            attack=enemy.attack,
            is_boss=self.current_battle_is_boss,
            is_elite=self.current_battle_is_elite,
            phase=phase,
        )

    def _require_current_enemy(self) -> EnemyState | BossState:
        if self.current_enemy is None:
            raise RuntimeError("No active battle")
        return self.current_enemy

    def _resolve_commit_for_node(self, chapter: Any, node: RouteNode) -> Any:
        commits = list(getattr(chapter, "commits", []))
        if not commits:
            return SimpleNamespace(
                hexsha=f"synthetic_{chapter.chapter_index:02d}_{node.position:02d}",
                message=f"chapter_{chapter.chapter_index}_node_{node.kind.value}",
                total_changes=10,
            )

        nodes = self._chapter_nodes.get(chapter.chapter_id, [])
        combat_nodes = [item for item in nodes if item.kind in self.combat_kinds()]
        if not combat_nodes or len(combat_nodes) == 1:
            commit_idx = 0
        else:
            combat_index = 0
            for idx, combat_node in enumerate(combat_nodes):
                if combat_node.node_id == node.node_id:
                    combat_index = idx
                    break
            commit_idx = int(round((combat_index * (len(commits) - 1)) / (len(combat_nodes) - 1)))
        self._require_state().current_commit_index = int(chapter.start_index + commit_idx)
        return commits[commit_idx]

    def _create_enemy(self, commit: Any) -> EnemyState:
        msg = str(commit.message).lower()
        chapter = self._require_chapter()
        if "merge" in msg:
            enemy_type = "merge"
        elif msg.startswith("fix") or "bug" in msg:
            enemy_type = "bug"
        elif msg.startswith("feat"):
            enemy_type = "feature"
        elif msg.startswith("docs"):
            enemy_type = "docs"
        else:
            enemy_type = "general"

        diff = self.progression_rules.calculate_enemy_difficulty(
            commit.total_changes or 10,
            enemy_type,
            chapter.chapter_index,
        )
        hp = int(diff["hp"] * chapter.config.enemy_hp_multiplier)
        atk = int(diff["attack"] * chapter.config.enemy_atk_multiplier)
        hp, atk = apply_enemy_mutator(hp, atk, self.mutator)
        return EnemyState(
            entity_id=f"enemy_{self._require_state().current_commit_index}",
            name=self._generate_enemy_name(commit),
            enemy_type=enemy_type,
            commit_hash=commit.hexsha[:7],
            commit_message=commit.message[:30],
            current_hp=hp,
            max_hp=hp,
            attack=atk,
            defense=diff["defense"],
            exp_reward=diff["exp_reward"],
            gold_reward=diff["gold_reward"],
            is_boss="merge" in msg,
        )

    @staticmethod
    def _generate_enemy_name(commit: Any) -> str:
        msg = str(commit.message)
        lowered = msg.lower()
        if lowered.startswith("feat:"):
            return f"Feature: {msg[5:].strip()[:20]}"
        if lowered.startswith("fix:"):
            return f"Bug: {msg[4:].strip()[:20]}"
        if lowered.startswith("docs:"):
            return f"Docs: {msg[5:].strip()[:15]}"
        if lowered.startswith("merge"):
            return "Merge Conflict"
        return msg[:25] if msg else "Unknown"

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

    def is_dungeon_trap_consumed(self, trap_id: str) -> bool:
        return self._dungeon_trap_key(trap_id) in self.dungeon_consumed_traps

    def trigger_dungeon_trap(self, trap_id: str, damage: int) -> DungeonTrapResult:
        trap_key = self._dungeon_trap_key(trap_id)
        if trap_key in self.dungeon_consumed_traps:
            return DungeonTrapResult(trap_id=trap_id, damage=0, already_triggered=True)

        state = self._require_state()
        player = state.player.character
        actual_damage = min(max(0, damage), max(0, player.current_hp - 1))
        player.current_hp -= actual_damage
        self.dungeon_consumed_traps.add(trap_key)
        return DungeonTrapResult(trap_id=trap_id, damage=actual_damage, already_triggered=False)

    def _dungeon_trap_key(self, trap_id: str) -> str:
        chapter = self.current_chapter()
        chapter_id = getattr(chapter, "chapter_id", "unknown") if chapter is not None else "unknown"
        return f"{chapter_id}:{trap_id}"

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
