#!/usr/bin/env python3
"""
Git Dungeon - Main CLI Entry Point

Features:
- M0: Event-driven architecture
- M1: Chapter system + Shop
- M2: Boss battles
- M3: Economy/Shop system
- M4: Skill system
"""

import os
import re
import subprocess
import tempfile
import argparse
from typing import Optional, Any
from types import SimpleNamespace

from git_dungeon.engine import (
    Engine, GameState, EnemyState,
    create_rng, EventType,
)
from git_dungeon.engine.rules import (
    ChapterSystem, ShopSystem, PlayerInventory,
    CombatRules, ProgressionRules,
    BossSystem, BossState,
)
from git_dungeon.engine.auto_policy import (
    ACTION_ATTACK,
    ACTION_LABELS,
    AutoCombatContext,
    AutoEventContext,
    AutoEventOptionContext,
    AutoPolicyConfig,
    AutoRestContext,
    AutoShopContext,
    AutoShopOptionContext,
    REST_ACTION_FOCUS,
    REST_ACTION_HEAL,
    RuleBasedAutoPolicy,
)
from git_dungeon.engine.daily import DailyChallengeInfo, build_shareable_run_id, resolve_run_seed
from git_dungeon.engine.events import apply_event_choice
from git_dungeon.engine.mutators import (
    MutatorConfig,
    apply_enemy_mutator,
    apply_reward_mutator,
    get_mutator_config,
)
from git_dungeon.engine.rng import DefaultRNG
from git_dungeon.engine.node_flow import ChapterNodeGenerator, summarize_node_kinds
from git_dungeon.engine.route import NodeKind, RouteNode
from git_dungeon.engine.run_metrics import RunMetrics
from git_dungeon.content.runtime_loader import load_runtime_content
from git_dungeon.config import GameConfig
from git_dungeon.core.git_parser import GitParser, CommitInfo
from git_dungeon.engine.rules.chapter_rules import build_chapter_configs
from git_dungeon.i18n import i18n, normalize_lang
from git_dungeon.i18n.translations import get_translation


class GitDungeonCLI:
    """Main CLI game with chapter and shop support."""
    
    def __init__(
        self,
        seed: Optional[int] = None,
        verbose: bool = False,
        auto_mode: bool = False,
        lang: str = "en",
        compact: bool = False,
        metrics_out: Optional[str] = None,
        print_metrics: bool = False,
        auto_policy: Optional[RuleBasedAutoPolicy] = None,
        auto_policy_config: Optional[AutoPolicyConfig] = None,
        content_pack_args: Optional[list[str]] = None,
        content_dir: Optional[str] = None,
        mutator: str = "none",
        daily_info: Optional[DailyChallengeInfo] = None,
    ):
        self.seed = seed
        self.lang = normalize_lang(lang)
        self.verbose = verbose
        self.compact = compact
        self.daily_info = daily_info
        self.mutator: MutatorConfig = get_mutator_config(mutator)
        self.content_runtime = load_runtime_content(
            content_dir=content_dir,
            content_pack_args=content_pack_args,
        )
        self.loaded_content_packs = self.content_runtime.loaded_pack_ids
        self.run_id: Optional[str] = None
        
        # Load language
        i18n.load_language(self.lang)
        
        self.rng = create_rng(seed)
        self.engine = Engine(rng=self.rng)
        self.combat_rules = CombatRules(rng=self.rng)
        self.progression_rules = ProgressionRules(rng=self.rng)
        self.chapter_system = ChapterSystem(
            rng=self.rng,
            chapter_configs=build_chapter_configs(self.content_runtime.chapter_overrides),
        )
        self.shop_system = ShopSystem(rng=self.rng)
        self.boss_system = BossSystem(rng=self.rng)
        
        self.state: GameState | None = None
        self.repo_info: Any = None
        self.inventory = PlayerInventory()
        self.current_shop: Any = None
        self.current_boss: Optional[BossState] = None
        self.verbose = verbose
        self.auto_mode = auto_mode
        self.auto_policy_config = auto_policy_config or AutoPolicyConfig()
        self.auto_policy = auto_policy or RuleBasedAutoPolicy(config=self.auto_policy_config)
        self.metrics_out = metrics_out
        self.print_metrics = print_metrics
        self.metrics = RunMetrics(seed=seed, auto_mode=auto_mode)
        self.node_generator = ChapterNodeGenerator()
        self._chapter_nodes: dict[str, list[RouteNode]] = {}
        self._chapter_node_cursor: dict[str, int] = {}
    
    def _t(self, text: str) -> str:
        """Translate text based on current language."""
        if self.lang == "zh_CN":
            return get_translation(text, "zh_CN")  # type: ignore[no-any-return]
        return text

    @property
    def _compact_mode(self) -> bool:
        return self.compact and not self.verbose

    def _emit_key_event(self, tag: str, message: str) -> None:
        """Highlight critical events in both compact and verbose modes."""
        print(f"   ✨[{tag}] {message}")

    def _emit_turn_summary(
        self,
        turn: int,
        action: str,
        player_damage: int,
        enemy_damage: int,
        player_hp: int,
        player_hp_max: int,
        enemy_hp: int,
        enemy_hp_max: int,
        tags: Optional[list[str]] = None,
    ) -> None:
        """Compact per-turn summary line."""
        if not self._compact_mode:
            return
        action_name = ACTION_LABELS.get(action, action)
        suffix = ""
        if tags:
            suffix = " " + " ".join(f"[{tag}]" for tag in tags)
        print(
            f"T{turn:02d} action={action_name} dealt={player_damage} taken={enemy_damage} "
            f"hp={player_hp}/{player_hp_max} enemy={enemy_hp}/{enemy_hp_max}{suffix}"
        )

    def _finalize_metrics(self, run_success: bool) -> None:
        """Write and/or print metrics when requested."""
        self.metrics.finalize(run_victory=run_success)
        if self.metrics_out:
            self.metrics.write_json(self.metrics_out)
            print(f"📊 Metrics written: {self.metrics_out}")
        if self.print_metrics:
            print()
            for line in self.metrics.summary_lines():
                print(line)
    
    def start(self, repo_input: str) -> bool:
        """Start game with chapter system."""
        run_success = False
        # Handle GitHub URL or local path
        try:
            if self._is_github_url(repo_input):
                repo_path = self._clone_github_repo(repo_input)
                if not repo_path:
                    return False
            else:
                repo_path = repo_input
                if not os.path.exists(repo_path):
                    print(f"❌ Repository not found: {repo_path}")
                    return False

            self.run_id = build_shareable_run_id(
                repository=repo_path,
                seed=int(self.seed or 0),
                mutator=self.mutator.id,
                content_pack_ids=self.loaded_content_packs,
                daily_date_iso=(self.daily_info.date_iso if self.daily_info else None),
            )
            if self.daily_info:
                print(
                    f"📅 Daily challenge {self.daily_info.date_iso} "
                    f"(seed={self.daily_info.seed}) run_id={self.run_id}"
                )
            if self.mutator.id != "none":
                print(f"⚙️  Mutator: {self.mutator.id} ({self.mutator.summary})")
            if self.loaded_content_packs:
                packs = ", ".join(self.loaded_content_packs)
                print(f"🧩 Content packs: {packs}")
        
            # Load repository
            print(self._t("Loading repository..."))
            config = GameConfig()
            parser = GitParser(config)
        
            try:
                parser.load_repository(repo_path)
            except Exception as e:
                print(f"❌ Failed to load: {e}")
                return False
        
            commits = parser.get_commit_history()
            if not commits:
                print("❌ No commits found")
                return False
        
            print(f"{self._t('Loaded')} {len(commits)} {self._t('commits')}!")
        
            # Parse chapters
            self.chapter_system.parse_chapters(commits)
            self._parser = parser
            self._commits_cache = commits
        
            print(
                f"{self._t('Divided into')} {len(self.chapter_system.chapters)} "
                f"{self._t('chapters')}:"
            )
            summary = self.chapter_system.get_chapter_summary()
            if self.lang == "en":
                for chapter_item in self.chapter_system.chapters:
                    summary = summary.replace(chapter_item.name, self._t(chapter_item.name))
            print(summary)
        
            # Initialize state
            self.state = GameState(
                seed=self.seed,
                repo_path=repo_path,
                total_commits=len(commits),
                current_commit_index=0,
                difficulty="normal"
            )
            self.state.player.character.current_hp = 100
            self.state.player.character.current_mp = 50
            self.state.route_state = {
                "current_node_id": "",
                "visited_nodes": [],
                "route_flags": {},
                "chapter_nodes": {},
            }
        
            # Show banner
            self._print_banner()
        
            # Show chapter intro
            chapter = self.chapter_system.get_current_chapter()
            if chapter:
                self._print_chapter_intro(chapter)
        
            # Start game loop
            run_success = self._game_loop()
            return run_success
        finally:
            if self.metrics_out or self.print_metrics:
                self._finalize_metrics(run_success)
    
    def _game_loop(self) -> bool:
        """Main game loop with deterministic chapter-node progression."""
        while self.state and not self.state.is_game_over:
            chapter = self.chapter_system.get_current_chapter()
            if not chapter:
                self._print_victory()
                return True

            chapter_id = chapter.chapter_id
            if chapter_id not in self._chapter_nodes:
                self._prepare_chapter_nodes(chapter)
                self.metrics.record_chapter_started()

            nodes = self._chapter_nodes.get(chapter_id, [])
            cursor = self._chapter_node_cursor.get(chapter_id, 0)
            if cursor >= len(nodes):
                if not self._complete_chapter():
                    return False
                continue

            node = nodes[cursor]
            if self.state.route_state is not None:
                self.state.route_state["current_node_id"] = node.node_id

            if not self._resolve_node(chapter, node):
                self._print_defeat()
                return False

            self._chapter_node_cursor[chapter_id] = cursor + 1
            if self.state.route_state is not None:
                visited = self.state.route_state.setdefault("visited_nodes", [])
                visited.append(node.node_id)

        return True

    def _prepare_chapter_nodes(self, chapter: Any) -> None:
        """Generate and cache deterministic nodes for one chapter."""
        if not self.state:
            return
        seed = int(self.seed or 0)
        chapter_id = chapter.chapter_id
        nodes = self.node_generator.build_nodes(
            seed=seed,
            chapter_index=chapter.chapter_index,
            chapter_enemy_count=len(getattr(chapter, "commits", [])),
            difficulty=1.0,
            has_boss=True,
            has_events=bool(self.content_runtime.registry.events),
        )
        self._chapter_nodes[chapter_id] = nodes
        self._chapter_node_cursor[chapter_id] = 0
        chapter.enemies_defeated = 0

        if self.state.route_state is not None:
            chapter_nodes = self.state.route_state.setdefault("chapter_nodes", {})
            chapter_nodes[chapter_id] = [node.kind.value for node in nodes]

        counts = summarize_node_kinds(nodes)
        if self._compact_mode:
            parts = [f"{key}={value}" for key, value in counts.items()]
            print(f"🧭 Chapter route: {', '.join(parts)}")
        else:
            print("🧭 Chapter nodes:")
            for idx, node in enumerate(nodes, start=1):
                print(f"   {idx:02d}. {node.kind.value}")

    def _resolve_node(self, chapter: Any, node: RouteNode) -> bool:
        """Resolve one chapter node."""
        if not self.state:
            return False

        self.metrics.record_node(node.kind.value)

        if node.kind == NodeKind.EVENT:
            return self._handle_event_node(chapter, node)
        if node.kind == NodeKind.REST:
            return self._handle_rest_node(chapter, node)
        if node.kind == NodeKind.SHOP:
            return self._handle_shop_node(chapter, node)
        if node.kind == NodeKind.BOSS:
            return self._resolve_boss_node(chapter, node)
        if node.kind == NodeKind.TREASURE:
            return self._handle_event_node(chapter, node)
        return self._resolve_combat_node(chapter, node)

    def _resolve_combat_node(self, chapter: Any, node: RouteNode) -> bool:
        """Run one battle/elite node."""
        commit = self._resolve_commit_for_node(chapter, node)
        if not commit:
            return True

        enemy = self._create_enemy(commit)
        if node.kind == NodeKind.ELITE:
            enemy.current_hp = int(enemy.current_hp * 1.35)
            enemy.max_hp = enemy.current_hp
            enemy.attack = int(enemy.attack * 1.25)
            enemy.name = f"Elite {enemy.name}"
            self._emit_key_event("ELITE", enemy.name)
        if self._compact_mode:
            print(f"N{node.position + 1:02d} node={node.kind.value} enemy={enemy.name}")
        won = self._combat(enemy, chapter)
        if not won:
            return False

        chapter.enemies_defeated += 1
        self.state.enemies_defeated.append(commit.hexsha[:7])
        self._grant_rewards(enemy, chapter)
        return True

    def _resolve_boss_node(self, chapter: Any, node: RouteNode) -> bool:
        """Run chapter-end boss node."""
        if chapter.is_boss_chapter:
            if self._compact_mode:
                print(f"N{node.position + 1:02d} node=boss enemy=chapter_boss")
            return self._boss_combat(chapter)

        commit = self._resolve_commit_for_node(chapter, node)
        if not commit:
            return True
        enemy = self._create_enemy(commit)
        enemy.current_hp = int(enemy.current_hp * 1.6)
        enemy.max_hp = enemy.current_hp
        enemy.attack = int(enemy.attack * 1.45)
        enemy.name = f"{chapter.name} Guardian"
        self._emit_key_event("BOSS_PHASE", f"{enemy.name} appears")
        if self._compact_mode:
            print(f"N{node.position + 1:02d} node=boss enemy={enemy.name}")
        won = self._combat(enemy, chapter)
        if not won:
            return False
        chapter.enemies_defeated += 1
        self.state.enemies_defeated.append(commit.hexsha[:7])
        self._grant_rewards(enemy, chapter)
        return True

    def _resolve_commit_for_node(self, chapter: Any, node: RouteNode) -> Any:
        """Map a node to a representative chapter commit deterministically."""
        if not self.state:
            return None
        commits = list(getattr(chapter, "commits", []))
        if not commits:
            return SimpleNamespace(
                hexsha=f"synthetic_{chapter.chapter_index:02d}_{node.position:02d}",
                message=f"chapter_{chapter.chapter_index}_node_{node.kind.value}",
                total_changes=10,
            )

        chapter_id = chapter.chapter_id
        nodes = self._chapter_nodes.get(chapter_id, [])
        combat_nodes = [
            n for n in nodes if n.kind in {NodeKind.BATTLE, NodeKind.ELITE, NodeKind.BOSS}
        ]
        if not combat_nodes:
            commit_idx = 0
        elif len(combat_nodes) == 1:
            commit_idx = 0
        else:
            combat_index = 0
            for idx, combat_node in enumerate(combat_nodes):
                if combat_node.node_id == node.node_id:
                    combat_index = idx
                    break
            commit_idx = int(
                round((combat_index * (len(commits) - 1)) / (len(combat_nodes) - 1))
            )

        commit_idx = max(0, min(len(commits) - 1, commit_idx))
        self.state.current_commit_index = int(chapter.start_index + commit_idx)
        return commits[commit_idx]

    def _select_event_for_node(self, chapter: Any, node: RouteNode) -> Any:
        """Pick one deterministic event for a node."""
        all_events = sorted(self.content_runtime.registry.events.values(), key=lambda item: item.id)
        if not all_events:
            return None

        preferred_tags: set[str] = {tag.value for tag in node.tags}
        if node.kind == NodeKind.SHOP:
            preferred_tags.update({"shop", "greed"})
        elif node.kind == NodeKind.REST:
            preferred_tags.update({"safe"})
        elif node.kind == NodeKind.ELITE:
            preferred_tags.update({"risk"})

        filtered = [
            event
            for event in all_events
            if (
                not event.route_tags
                or not preferred_tags
                or bool(preferred_tags.intersection(event.route_tags))
            )
        ]
        candidates = filtered or all_events

        chapter_type = getattr(getattr(chapter, "chapter_type", None), "value", "default")
        weights = []
        for event in candidates:
            weight = event.weights.get(chapter_type, event.weights.get("default", 1))
            weights.append(max(1, int(weight)))

        seed = int(self.seed or 0) + chapter.chapter_index * 131 + node.position * 17
        picker = DefaultRNG(seed=seed)
        return picker.choices(candidates, weights=weights, k=1)[0]

    def _build_event_option_context(self, choice: Any) -> AutoEventOptionContext:
        """Build policy-scoring context for one event choice."""
        hp_delta = 0
        gold_delta = 0
        resource_delta = 0.0
        risk_level = 0
        for effect in choice.effects:
            opcode = str(effect.opcode)
            value = effect.value
            amount = int(value) if isinstance(value, (int, float)) else 0
            if opcode == "heal":
                hp_delta += amount
            elif opcode == "take_damage":
                hp_delta -= amount
                risk_level += 1
            elif opcode == "gain_gold":
                gold_delta += amount
            elif opcode == "lose_gold":
                gold_delta -= amount
            elif opcode in {"add_relic"}:
                resource_delta += 1.2
            elif opcode in {"add_card", "upgrade_card"}:
                resource_delta += 0.8
            elif opcode in {"apply_status", "trigger_battle"}:
                risk_level += 2
                resource_delta -= 0.4
        return AutoEventOptionContext(
            choice_id=choice.id,
            hp_delta=hp_delta,
            gold_delta=gold_delta,
            resource_delta=resource_delta,
            risk_level=risk_level,
        )

    def _choose_event_choice(self, chapter: Any, node: RouteNode, event: Any) -> int:
        """Choose one event option (manual or auto)."""
        if not event.choices:
            return 0
        if self.auto_mode and self.state:
            player = self.state.player.character
            option_ctx = tuple(
                self._build_event_option_context(choice) for choice in event.choices
            )
            ctx = AutoEventContext(
                seed=int(self.seed or 0),
                chapter_index=chapter.chapter_index,
                node_index=node.position,
                player_hp=player.current_hp,
                player_max_hp=player.stats.hp.value,
                player_gold=self.state.player.gold,
                options=option_ctx,
            )
            idx = self.auto_policy.choose_event_choice(ctx)
            return max(0, min(len(event.choices) - 1, idx))

        for idx, choice in enumerate(event.choices, start=1):
            print(f"   [{idx}] {choice.id}")
        print("> ", end="", flush=True)
        raw = input().strip()
        try:
            picked = int(raw) - 1
        except ValueError:
            picked = 0
        return max(0, min(len(event.choices) - 1, picked))

    def _handle_event_node(self, chapter: Any, node: RouteNode) -> bool:
        """Resolve event node and apply selected effects."""
        if not self.state:
            return False
        event = self._select_event_for_node(chapter, node)
        if event is None or not event.choices:
            if self._compact_mode:
                print(f"N{node.position + 1:02d} node=event event=none")
            else:
                print("🎲 Event node had no valid event definition.")
            return True

        player = self.state.player.character
        before_hp = player.current_hp
        before_gold = self.state.player.gold
        choice_idx = self._choose_event_choice(chapter, node, event)
        choice = event.choices[choice_idx]
        effect_payload = [
            {
                "opcode": effect.opcode,
                "value": effect.value,
                "target": effect.target,
                "condition": effect.condition,
            }
            for effect in choice.effects
        ]
        result = apply_event_choice(self.state, effect_payload, self.rng)
        after_hp = player.current_hp
        after_gold = self.state.player.gold

        self.metrics.record_event_choice(event.id, choice.id)
        hp_delta = after_hp - before_hp
        gold_delta = after_gold - before_gold
        hp_text = f"{hp_delta:+d}" if hp_delta else "0"
        gold_text = f"{gold_delta:+d}" if gold_delta else "0"

        if self._compact_mode:
            print(
                f"N{node.position + 1:02d} node=event event={event.id} choice={choice.id} "
                f"hpΔ={hp_text} goldΔ={gold_text}"
            )
            messages = result.get("messages", [])
            if messages:
                print(f"   {' '.join(messages[:3])}")
        else:
            print(f"\n🎲 EVENT: {event.id}")
            print(f"   choice={choice.id} hpΔ={hp_text} goldΔ={gold_text}")
            for message in result.get("messages", []):
                print(f"   - {message}")

        if player.current_hp <= 0:
            return False
        return True

    def _handle_rest_node(self, chapter: Any, node: RouteNode) -> bool:
        """Resolve rest node with heal/focus choices."""
        if not self.state:
            return False
        player = self.state.player.character
        if self.auto_mode:
            choice = self.auto_policy.choose_rest_action(
                AutoRestContext(
                    seed=int(self.seed or 0),
                    chapter_index=chapter.chapter_index,
                    node_index=node.position,
                    player_hp=player.current_hp,
                    player_max_hp=player.stats.hp.value,
                )
            )
        else:
            print("\n🛌 REST NODE")
            print("   [1] heal")
            print("   [2] focus")
            print("> ", end="", flush=True)
            raw = input().strip()
            choice = REST_ACTION_HEAL if raw in {"1", "heal"} else REST_ACTION_FOCUS

        if choice == REST_ACTION_HEAL:
            heal_amount = max(10, int(player.stats.hp.value * 0.3))
            actual = player.heal(heal_amount)
            output = f"heal={actual}"
        else:
            player.stats.attack.value += 2
            player.stats.hp.value += 5
            player.current_hp = min(player.stats.hp.value, player.current_hp + 5)
            output = "focus=atk+2 hp_max+5"

        self.metrics.record_rest_choice(choice)
        if self._compact_mode:
            print(f"N{node.position + 1:02d} node=rest choice={choice} {output}")
        else:
            print(f"🛌 Rest: {choice} -> {output}")
        return True

    def _shop_offers_for_node(self, chapter: Any, node: RouteNode) -> list[dict[str, Any]]:
        """Build deterministic light-weight shop offers for one node."""
        seed = int(self.seed or 0) + chapter.chapter_index * 211 + node.position * 41
        rng = DefaultRNG(seed=seed)
        tier = chapter.chapter_index
        templates = [
            {
                "id": "patch_kit",
                "label": "Patch Kit",
                "cost": 30 + tier * 5,
                "heal": 18,
                "atk": 0,
                "mp": 0,
            },
            {
                "id": "compiler_blade",
                "label": "Compiler Blade",
                "cost": 55 + tier * 8,
                "heal": 0,
                "atk": 2,
                "mp": 0,
            },
            {
                "id": "cache_tonic",
                "label": "Cache Tonic",
                "cost": 42 + tier * 6,
                "heal": 8,
                "atk": 0,
                "mp": 12,
            },
            {
                "id": "max_hp_patch",
                "label": "MaxHP Patch",
                "cost": 75 + tier * 10,
                "heal": 10,
                "atk": 1,
                "mp": 0,
                "hp_max": 10,
            },
        ]
        picked_ids = rng.sample(list(range(len(templates))), k=min(3, len(templates)))
        return [templates[index] for index in picked_ids]

    def _apply_shop_offer(self, offer: dict[str, Any]) -> None:
        """Apply one shop offer to current player state."""
        if not self.state:
            return
        player = self.state.player.character
        hp_max_gain = int(offer.get("hp_max", 0))
        if hp_max_gain:
            player.stats.hp.value += hp_max_gain
            player.current_hp += hp_max_gain
        atk_gain = int(offer.get("atk", 0))
        if atk_gain:
            player.stats.attack.value += atk_gain
        mp_gain = int(offer.get("mp", 0))
        if mp_gain:
            player.current_mp = min(
                player.stats.mp.value,
                player.current_mp + mp_gain,
            )
        heal_gain = int(offer.get("heal", 0))
        if heal_gain:
            player.heal(heal_gain)

    def _handle_shop_node(self, chapter: Any, node: RouteNode) -> bool:
        """Resolve shop node with deterministic offers and auto policy support."""
        if not self.state:
            return False
        offers = self._shop_offers_for_node(chapter, node)
        player = self.state.player.character
        gold = self.state.player.gold

        selected_idx: int | None = None
        if self.auto_mode:
            option_ctx = tuple(
                AutoShopOptionContext(
                    option_id=offer["id"],
                    cost=int(offer["cost"]),
                    value_score=(
                        int(offer.get("heal", 0)) * 0.12
                        + int(offer.get("atk", 0)) * 2.0
                        + int(offer.get("mp", 0)) * 0.10
                        + int(offer.get("hp_max", 0)) * 0.25
                    ),
                    hp_delta=int(offer.get("heal", 0)),
                )
                for offer in offers
            )
            selected_idx = self.auto_policy.choose_shop_option(
                AutoShopContext(
                    seed=int(self.seed or 0),
                    chapter_index=chapter.chapter_index,
                    node_index=node.position,
                    player_hp=player.current_hp,
                    player_max_hp=player.stats.hp.value,
                    player_gold=gold,
                    options=option_ctx,
                )
            )
        else:
            print("\n🏪 SHOP NODE")
            print(f"   gold={gold}")
            for idx, offer in enumerate(offers, start=1):
                print(
                    f"   [{idx}] {offer['label']} cost={offer['cost']} "
                    f"(heal={offer.get('heal', 0)} atk={offer.get('atk', 0)} mp={offer.get('mp', 0)})"
                )
            print("   [0] skip")
            print("> ", end="", flush=True)
            raw = input().strip()
            try:
                parsed = int(raw)
            except ValueError:
                parsed = 0
            if parsed > 0:
                selected_idx = parsed - 1

        if selected_idx is None or selected_idx < 0 or selected_idx >= len(offers):
            self.metrics.record_shop_choice("skip")
            if self._compact_mode:
                print(
                    f"N{node.position + 1:02d} node=shop choice=skip "
                    f"gold={self.state.player.gold}"
                )
            else:
                print("🏪 Shop skipped.")
            return True

        offer = offers[selected_idx]
        cost = int(offer["cost"])
        if cost > self.state.player.gold:
            self.metrics.record_shop_choice("insufficient_gold")
            if self._compact_mode:
                print(
                    f"N{node.position + 1:02d} node=shop choice=none "
                    "reason=insufficient_gold"
                )
            else:
                print("🏪 Not enough gold.")
            return True

        self.state.player.gold -= cost
        self.inventory.gold = self.state.player.gold
        self._apply_shop_offer(offer)
        self.metrics.record_shop_choice(str(offer["id"]))
        if self._compact_mode:
            print(
                f"N{node.position + 1:02d} node=shop choice={offer['id']} "
                f"cost={cost} gold={self.state.player.gold}"
            )
        else:
            print(f"🏪 Purchased {offer['label']} for {cost} gold.")
        return True
    
    def _combat(self, enemy: EnemyState, chapter: Any) -> bool:
        """Combat with chapter context."""
        if not self.state:
            return False
        self.state.in_combat = True
        self.state.current_enemy = enemy

        if self._compact_mode:
            print(f"\n⚔️  {chapter.name}: {enemy.name} [compact]")
        else:
            print(f"\n{'─'*50}")

            # Show chapter context
            if chapter.is_boss_chapter:
                print(f"{self._t('BOSS BATTLE')}: {enemy.name}")
                print(f"📖 Chapter: {chapter.name}")
            else:
                print(f"⚔️  {chapter.name}: {enemy.name}")

            print(f"{'─'*50}")

        turn = 0
        while self.state and self.state.in_combat:
            turn += 1

            self._print_combat_status(enemy)
            choice = self._get_combat_choice(
                enemy=enemy,
                turn_number=turn,
                is_boss=False,
                can_escape=True,
                skill_mp_cost=10,
                skill_damage_bonus=5,
            )

            player = self.state.player.character
            player_damage = 0
            enemy_damage = 0
            tags: list[str] = []

            if choice == "1":  # Attack
                is_crit, mult = self.combat_rules.roll_critical(player.stats.critical.value, 1.5)
                damage = int((player.stats.attack.value + 5) * mult)
                actual = enemy.take_damage(damage)
                player_damage = actual

                crit_str = " ⚡CRITICAL!" if is_crit else ""
                if not self._compact_mode:
                    print(f"   ⚔️  You attack {enemy.name} for {actual} damage{crit_str}!")
                if is_crit:
                    tags.append("CRIT")

                if not enemy.is_alive:
                    tags.append("KILL")
                    self._emit_key_event("KILL", f"{enemy.name} defeated")
                    self._emit_turn_summary(
                        turn=turn,
                        action=choice,
                        player_damage=player_damage,
                        enemy_damage=enemy_damage,
                        player_hp=player.current_hp,
                        player_hp_max=player.stats.hp.value,
                        enemy_hp=enemy.current_hp,
                        enemy_hp_max=enemy.max_hp,
                        tags=tags,
                    )
                    self.metrics.record_battle(turns=turn, won=True, is_boss=False)
                    return True

            elif choice == "2":  # Defend
                player.is_defending = True
                if not self._compact_mode:
                    print("   🛡️  Defensive stance!")
                tags.append("DEFEND")

            elif choice == "3":  # Skill
                if player.current_mp >= 10:
                    player.current_mp -= 10
                    is_crit, mult = self.combat_rules.roll_critical(player.stats.critical.value, 2.0)
                    damage = int((player.stats.attack.value + 5) * 2 * mult)
                    actual = enemy.take_damage(damage)
                    player_damage = actual
                    if not self._compact_mode:
                        print(f"   ✨ Skill! {enemy.name} takes {actual} damage!")
                    if is_crit:
                        tags.append("CRIT")
                    if not enemy.is_alive:
                        tags.append("KILL")
                        self._emit_key_event("KILL", f"{enemy.name} defeated")
                        self._emit_turn_summary(
                            turn=turn,
                            action=choice,
                            player_damage=player_damage,
                            enemy_damage=enemy_damage,
                            player_hp=player.current_hp,
                            player_hp_max=player.stats.hp.value,
                            enemy_hp=enemy.current_hp,
                            enemy_hp_max=enemy.max_hp,
                            tags=tags,
                        )
                        self.metrics.record_battle(turns=turn, won=True, is_boss=False)
                        return True
                else:
                    if not self._compact_mode:
                        print(f"   ⚠️  Need 10 MP, have {player.current_mp}")
                    continue

            elif choice == "4":  # Escape/Shop
                if self.combat_rules.roll_escape(0.7):
                    if not self._compact_mode:
                        print("   🏃  Escaped!")
                    self.state.in_combat = False
                    tags.append("ESCAPE")
                    self._emit_turn_summary(
                        turn=turn,
                        action=choice,
                        player_damage=player_damage,
                        enemy_damage=enemy_damage,
                        player_hp=player.current_hp,
                        player_hp_max=player.stats.hp.value,
                        enemy_hp=enemy.current_hp,
                        enemy_hp_max=enemy.max_hp,
                        tags=tags,
                    )
                    self.metrics.record_battle(turns=turn, won=False, is_boss=False)
                    return False
                else:
                    if not self._compact_mode:
                        print("   ❌  Escape failed!")

            else:
                damage = player.stats.attack.value + 5
                actual = enemy.take_damage(damage)
                player_damage = actual
                if not self._compact_mode:
                    print(f"   ⚔️  Attack for {actual} damage!")
                if not enemy.is_alive:
                    tags.append("KILL")
                    self._emit_key_event("KILL", f"{enemy.name} defeated")
                    self._emit_turn_summary(
                        turn=turn,
                        action=ACTION_ATTACK,
                        player_damage=player_damage,
                        enemy_damage=enemy_damage,
                        player_hp=player.current_hp,
                        player_hp_max=player.stats.hp.value,
                        enemy_hp=enemy.current_hp,
                        enemy_hp_max=enemy.max_hp,
                        tags=tags,
                    )
                    self.metrics.record_battle(turns=turn, won=True, is_boss=False)
                    return True

            # Enemy turn
            if enemy.is_alive:
                damage = enemy.attack
                if getattr(player, 'is_defending', False):
                    damage = damage // 2
                    player.is_defending = False
                    if not self._compact_mode:
                        print(f"   🛡️  Defense: {damage} damage!")

                actual = player.take_damage(damage)
                enemy_damage = actual
                if not self._compact_mode:
                    print(f"   💥 {enemy.name} attacks for {actual} damage!")

                if player.stats.hp.value > 0 and (player.current_hp / player.stats.hp.value) <= 0.2:
                    tags.append("LOW_HP")
                    self._emit_key_event("NEAR_DEATH", f"HP {player.current_hp}/{player.stats.hp.value}")

                if not player.is_alive:
                    tags.append("DEFEAT")
                    if not self._compact_mode:
                        print("   💀 Defeated!")
                    self._emit_turn_summary(
                        turn=turn,
                        action=choice,
                        player_damage=player_damage,
                        enemy_damage=enemy_damage,
                        player_hp=player.current_hp,
                        player_hp_max=player.stats.hp.value,
                        enemy_hp=enemy.current_hp,
                        enemy_hp_max=enemy.max_hp,
                        tags=tags,
                    )
                    self.metrics.record_battle(turns=turn, won=False, is_boss=False)
                    return False

            self._emit_turn_summary(
                turn=turn,
                action=choice,
                player_damage=player_damage,
                enemy_damage=enemy_damage,
                player_hp=player.current_hp,
                player_hp_max=player.stats.hp.value,
                enemy_hp=enemy.current_hp,
                enemy_hp_max=enemy.max_hp,
                tags=tags,
            )

        return False
    
    def _boss_combat(self, chapter: Any) -> bool:
        """Boss battle."""
        # Create boss
        self.current_boss = self.chapter_system.get_chapter_boss(chapter, self.boss_system)
        if not self.current_boss:
            return True
        
        boss = self.current_boss
        
        # Print boss intro
        print(self.boss_system.render_boss_intro(boss))
        
        if not self.auto_mode:
            input("\n按回车开始 Boss 战...")
        
        if not self.state:
            return False
        self.state.in_combat = True
        turn = 0
        
        while self.state and self.state.in_combat and boss.is_alive:
            turn += 1
            
            # Tick abilities
            boss.tick_abilities()
            
            if not self._compact_mode:
                print(self.boss_system.render_boss_status(boss))
            self._print_combat_status_for_boss()
            choice = self._get_combat_choice(
                enemy=boss,
                turn_number=turn,
                is_boss=True,
                can_escape=False,
                skill_mp_cost=15,
                skill_damage_bonus=15,
                threat_hint=boss.is_enraged,
            )
            
            player = self.state.player.character
            player_damage = 0
            enemy_damage = 0
            tags: list[str] = []
            
            if choice == "1":  # Attack
                is_crit, mult = self.combat_rules.roll_critical(player.stats.critical.value, 1.5)
                damage = int((player.stats.attack.value + 10) * mult)
                actual = boss.take_damage(damage)
                player_damage = actual
                
                crit_str = " ⚡CRITICAL!" if is_crit else ""
                if not self._compact_mode:
                    print(f"   ⚔️  You attack {boss.name} for {actual} damage{crit_str}!")
                if is_crit:
                    tags.append("CRIT")
                
                # Show phase change
                if boss.is_enraged and not hasattr(self, '_enrage_announced'):
                    self._emit_key_event("BOSS_PHASE", f"{boss.name} is enraged")
                    self._enrage_announced = True
                    tags.append("BOSS_PHASE")
                
                if not boss.is_alive:
                    tags.append("KILL")
                    self._emit_key_event("KILL", f"{boss.name} defeated")
                    if not self._compact_mode:
                        print(f"\n   💀 {boss.name} DEFEATED!")
                        print(self.boss_system.render_victory(boss))
                    self._grant_boss_rewards(boss)
                    self.current_boss = None
                    if hasattr(self, '_enrage_announced'):
                        del self._enrage_announced
                    self._emit_turn_summary(
                        turn=turn,
                        action=choice,
                        player_damage=player_damage,
                        enemy_damage=enemy_damage,
                        player_hp=player.current_hp,
                        player_hp_max=player.stats.hp.value,
                        enemy_hp=boss.current_hp,
                        enemy_hp_max=boss.max_hp,
                        tags=tags,
                    )
                    self.metrics.record_battle(turns=turn, won=True, is_boss=True)
                    return True
            
            elif choice == "2":  # Defend
                player.is_defending = True
                if not self._compact_mode:
                    print("   🛡️  Defensive stance!")
                tags.append("DEFEND")
            
            elif choice == "3":  # Skill
                if player.current_mp >= 15:
                    player.current_mp -= 15
                    is_crit, mult = self.combat_rules.roll_critical(player.stats.critical.value, 2.0)
                    damage = int((player.stats.attack.value + 15) * 2 * mult)
                    actual = boss.take_damage(damage)
                    player_damage = actual
                    if not self._compact_mode:
                        print(f"   ✨ Skill! {boss.name} takes {actual} damage!")
                    if is_crit:
                        tags.append("CRIT")
                    if not boss.is_alive:
                        tags.append("KILL")
                        self._emit_key_event("KILL", f"{boss.name} defeated")
                        if not self._compact_mode:
                            print(f"\n   💀 {boss.name} DEFEATED!")
                            print(self.boss_system.render_victory(boss))
                        self._grant_boss_rewards(boss)
                        self.current_boss = None
                        self._emit_turn_summary(
                            turn=turn,
                            action=choice,
                            player_damage=player_damage,
                            enemy_damage=enemy_damage,
                            player_hp=player.current_hp,
                            player_hp_max=player.stats.hp.value,
                            enemy_hp=boss.current_hp,
                            enemy_hp_max=boss.max_hp,
                            tags=tags,
                        )
                        self.metrics.record_battle(turns=turn, won=True, is_boss=True)
                        return True
                else:
                    if not self._compact_mode:
                        print(f"   ⚠️  Need 15 MP, have {player.current_mp}")
                    continue
            
            elif choice == "4":  # Escape (not allowed in boss fight)
                if not self._compact_mode:
                    print("   ⚠️  Cannot escape from Boss battle!")
                continue
            
            else:
                damage = player.stats.attack.value + 10
                actual = boss.take_damage(damage)
                player_damage = actual
                if not self._compact_mode:
                    print(f"   ⚔️  Attack for {actual} damage!")
                if not boss.is_alive:
                    tags.append("KILL")
                    self._emit_key_event("KILL", f"{boss.name} defeated")
                    if not self._compact_mode:
                        print(f"\n   💀 {boss.name} DEFEATED!")
                        print(self.boss_system.render_victory(boss))
                    self._grant_boss_rewards(boss)
                    self.current_boss = None
                    self._emit_turn_summary(
                        turn=turn,
                        action=ACTION_ATTACK,
                        player_damage=player_damage,
                        enemy_damage=enemy_damage,
                        player_hp=player.current_hp,
                        player_hp_max=player.stats.hp.value,
                        enemy_hp=boss.current_hp,
                        enemy_hp_max=boss.max_hp,
                        tags=tags,
                    )
                    self.metrics.record_battle(turns=turn, won=True, is_boss=True)
                    return True
            
            # Boss turn
            if boss.is_alive:
                # Get boss action
                player_hp_percent = player.current_hp / player.stats.hp.value
                action = boss.get_next_action(self.rng, player_hp_percent)
                
                if action == "attack":
                    base_damage = self.boss_system.calculate_boss_damage(boss, "attack")
                else:
                    base_damage = self.boss_system.calculate_boss_damage(boss, action)
                
                # Apply defense
                damage = max(1, base_damage - player.stats.defense.value)
                
                if getattr(player, 'is_defending', False):
                    damage = damage // 2
                    player.is_defending = False
                    if not self._compact_mode:
                        print(f"   🛡️  Defended: {damage} damage!")
                else:
                    if not self._compact_mode:
                        print(f"   💥 {boss.name} attacks for {damage} damage!")
                
                # Check for ability description
                if not self._compact_mode:
                    for ability in boss.abilities:
                        if ability.ability_id == action and ability.description:
                            print(f"   📝 {ability.name}: {ability.description}")
                
                actual = player.take_damage(damage)
                enemy_damage = actual

                if player.stats.hp.value > 0 and (player.current_hp / player.stats.hp.value) <= 0.2:
                    tags.append("LOW_HP")
                    self._emit_key_event("NEAR_DEATH", f"HP {player.current_hp}/{player.stats.hp.value}")
                
                if not player.is_alive:
                    tags.append("DEFEAT")
                    if not self._compact_mode:
                        print(f"\n   💀 你被 {boss.name} 击败了!")
                    self.current_boss = None
                    self._emit_turn_summary(
                        turn=turn,
                        action=choice,
                        player_damage=player_damage,
                        enemy_damage=enemy_damage,
                        player_hp=player.current_hp,
                        player_hp_max=player.stats.hp.value,
                        enemy_hp=boss.current_hp,
                        enemy_hp_max=boss.max_hp,
                        tags=tags,
                    )
                    self.metrics.record_battle(turns=turn, won=False, is_boss=True)
                    return False

            self._emit_turn_summary(
                turn=turn,
                action=choice,
                player_damage=player_damage,
                enemy_damage=enemy_damage,
                player_hp=player.current_hp,
                player_hp_max=player.stats.hp.value,
                enemy_hp=boss.current_hp,
                enemy_hp_max=boss.max_hp,
                tags=tags,
            )
        
        self.current_boss = None
        self.metrics.record_battle(turns=turn, won=False, is_boss=True)
        return False
    
    def _print_combat_status_for_boss(self) -> None:
        """Print player status during boss combat."""
        if self._compact_mode:
            return
        player = self.state.player.character  # type: ignore[union-attr]
        p_bar = self._render_hp_bar(player.current_hp, player.stats.hp.value)
        
        print(f"""
{'─'*50}
👤 {player.name} (Lv.{player.level})
{p_bar}
MP: {player.current_mp}/{player.stats.mp.value}
{'─'*50}""")
    
    def _grant_boss_rewards(self, boss: BossState) -> None:
        """Grant rewards for defeating a boss."""
        rewards = self.boss_system.get_boss_rewards(boss)
        reward_exp, reward_gold = apply_reward_mutator(
            int(rewards["exp"]),
            int(rewards["gold"]),
            self.mutator,
        )
        
        self.state.player.gold += reward_gold  # type: ignore[union-attr]
        self.inventory.gold += reward_gold  # Sync to inventory for shop
        
        did_level_up, new_level = self.state.player.character.gain_experience(reward_exp)  # type: ignore[union-attr]
        
        print(f"\n   💰 +{reward_gold} Gold")
        print(f"   ⭐ +{reward_exp} EXP")
        self.metrics.record_rewards(
            exp=reward_exp,
            gold=reward_gold,
            drops=len(rewards.get("items", [])),
            level_up=did_level_up,
        )
        
        if did_level_up:
            stats = self.progression_rules.calculate_level_up_stats(new_level)
            print(f"   🆙 LEVEL UP! Level {new_level}")
            print(f"      HP +{stats['hp_gain']}, MP +{stats['mp_gain']}, ATK +{stats['atk_gain']}")
            self._emit_key_event("LEVEL_UP", f"Level {new_level}")
        
        if rewards['items']:
            items_str = ", ".join(rewards['items'])
            print(f"   🎁 获得物品: {items_str}")
            self._emit_key_event("DROP", items_str)
    
    def _complete_chapter(self) -> bool:
        """Handle chapter completion and transition."""
        chapter = self.chapter_system.complete_current_chapter()
        self._chapter_nodes.pop(chapter.chapter_id, None)
        self._chapter_node_cursor.pop(chapter.chapter_id, None)
        
        # Calculate rewards
        gold_reward = int(50 * chapter.config.gold_bonus * (1 + chapter.chapter_index * 0.2))
        exp_reward = int(100 * chapter.config.exp_bonus * (1 + chapter.chapter_index * 0.2))
        exp_reward, gold_reward = apply_reward_mutator(exp_reward, gold_reward, self.mutator)
        
        self.state.player.gold += gold_reward  # type: ignore[union-attr]
        self.inventory.gold += gold_reward  # Sync to inventory for shop
        
        did_level_up, new_level = self.state.player.character.gain_experience(exp_reward)  # type: ignore[union-attr]
        
        print(f"""
{'='*50}
🎉 CHAPTER COMPLETE: {chapter.name}
{'='*50}
   Enemies: {chapter.enemies_defeated}/{chapter.enemy_count}
   💰 +{gold_reward} Gold
   ⭐ +{exp_reward} EXP
""")
        self.metrics.record_chapter_complete()
        self.metrics.record_rewards(exp=exp_reward, gold=gold_reward, level_up=did_level_up)
        
        if did_level_up:
            stats = self.progression_rules.calculate_level_up_stats(new_level)
            print(f"   🆙 LEVEL UP! Level {new_level}")
            print(f"      HP +{stats['hp_gain']}, MP +{stats['mp_gain']}, ATK +{stats['atk_gain']}")
            self._emit_key_event("LEVEL_UP", f"Level {new_level}")

        # Advance to next chapter
        if self.chapter_system.advance_chapter():
            next_chapter = self.chapter_system.get_current_chapter()
            if next_chapter:
                print()
                self._print_chapter_intro(next_chapter)
        else:
            self._print_victory()
            if self.state:
                self.state.is_game_over = True
                self.state.is_victory = True
            return True
        
        return True
    
    def _open_shop(self, chapter: Any) -> None:
        """Open shop for chapter."""
        if self.auto_mode:
            # Auto mode: skip shop
            return
        
        if not self.state:
            return
        
        print(f"\n{self._t('Welcome to the shop')}")
        print(f"💰 Gold: {self.state.player.gold}")
        
        self.current_shop = self.shop_system.generate_shop_inventory(
            chapter_index=chapter.chapter_index,
            base_gold=self.state.player.gold
        )
        
        while True:
            print(self.shop_system.render_shop_menu(self.current_shop, self.inventory))
            choice = input("> ").strip()
            
            if choice == "0":
                break
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(self.current_shop.items):
                    item = self.current_shop.items[idx]
                    success, events = self.shop_system.purchase_item(
                        self.current_shop, self.inventory, item.item_id
                    )
                    if success:
                        print(f"   ✅ Purchased {item.name}!")
                    else:
                        for e in events:
                            if e.type == EventType.ERROR:
                                print(f"   ❌ {e.data.get('message', 'Error')}")
                else:
                    print("   ❌ Invalid choice")
            except ValueError:
                print("   ❌ Invalid input")
    
    def _grant_rewards(self, enemy: EnemyState, chapter: Any) -> None:
        """Grant combat rewards with chapter bonuses."""
        # Apply chapter bonuses
        exp = int(enemy.exp_reward * chapter.config.exp_bonus)
        gold = int(enemy.gold_reward * chapter.config.gold_bonus)
        exp, gold = apply_reward_mutator(exp, gold, self.mutator)
        
        self.state.player.gold += gold  # type: ignore[union-attr]
        self.inventory.gold += gold  # Sync to inventory for shop
        
        did_level_up, new_level = self.state.player.character.gain_experience(exp)  # type: ignore[union-attr]
        
        print(f"   ⭐ +{exp} EXP  |  💰 +{gold} Gold")
        self.metrics.record_rewards(exp=exp, gold=gold, level_up=did_level_up)
        
        if did_level_up:
            self.progression_rules.calculate_level_up_stats(new_level)
            print(f"   🆙 LEVEL UP! Level {new_level}")
            self._emit_key_event("LEVEL_UP", f"Level {new_level}")
    
    def _create_enemy(self, commit: CommitInfo) -> EnemyState:
        """Create enemy from commit with chapter scaling."""
        msg = commit.message.lower()
        chapter = self.chapter_system.get_current_chapter()
        
        # Determine type
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
        
        # Calculate stats with chapter scaling
        diff = self.progression_rules.calculate_enemy_difficulty(
            commit.total_changes or 10,
            enemy_type,
            chapter.chapter_index if chapter else 0
        )
        
        # Apply chapter multipliers
        hp = int(diff["hp"] * chapter.config.enemy_hp_multiplier) if chapter else diff["hp"]
        atk = int(diff["attack"] * chapter.config.enemy_atk_multiplier) if chapter else diff["attack"]
        hp, atk = apply_enemy_mutator(hp, atk, self.mutator)
        
        name = self._generate_name(commit)
        
        return EnemyState(
            entity_id=f"enemy_{self.state.current_commit_index}",  # type: ignore[union-attr]
            name=name,
            enemy_type=enemy_type,
            commit_hash=commit.hexsha[:7],
            commit_message=commit.message[:30],
            current_hp=hp,
            max_hp=hp,
            attack=atk,
            defense=diff["defense"],
            exp_reward=diff["exp_reward"],
            gold_reward=diff["gold_reward"],
            is_boss="merge" in msg
        )
    
    def _generate_name(self, commit: CommitInfo) -> str:
        """Generate enemy name from commit."""
        msg = commit.message
        if msg.startswith("feat:"):
            return f"Feature: {msg[5:].strip()[:20]}"
        elif msg.startswith("fix:"):
            return f"Bug: {msg[4:].strip()[:20]}"
        elif msg.startswith("docs:"):
            return f"Docs: {msg[5:].strip()[:15]}"
        elif msg.startswith("merge"):
            return "Merge Conflict"
        else:
            return msg[:25] if msg else "Unknown"
    
    def _get_current_commit(self) -> Any:
        """Get current commit from parser."""
        if not self.state:
            return None

        if not hasattr(self, "_parser"):
            config = GameConfig()
            self._parser = GitParser(config)
            self._parser.load_repository(self.state.repo_path)

        commits = getattr(self, "_commits_cache", None)
        if commits is None:
            commits = self._parser.get_commit_history()
            self._commits_cache = commits

        idx = self.state.current_commit_index
        if 0 <= idx < len(commits):
            return commits[idx]
        return None
    
    def _print_banner(self) -> None:
        """Print banner."""
        if not self.state:
            return
        extras = []
        if self.mutator.id != "none":
            extras.append(f"🧪 Mutator: {self.mutator.id}")
        if self.daily_info and self.run_id:
            extras.append(f"🧷 Daily Run ID: {self.run_id}")
        elif self.loaded_content_packs and self.run_id:
            extras.append(f"🧷 Run ID: {self.run_id}")
        extras_block = "\n".join(extras)
        if extras_block:
            extras_block = "\n" + extras_block
        print(f"""
╔══════════════════════════════════════════════════════════╗
║              G I T   D U N G E O N                     ║
║         Battle through your commits!                   ║
╚══════════════════════════════════════════════════════════╝

📊 Repository: {self.state.repo_path}
📍 Total Commits: {self.state.total_commits}
📖 Chapters: {len(self.chapter_system.chapters)}
🎯 Objective: Defeat all commits!
{extras_block}
""")
    
    def _print_chapter_intro(self, chapter: Any) -> None:
        """Print chapter introduction."""
        preview_nodes = self._chapter_nodes.get(chapter.chapter_id)
        if preview_nodes is None:
            preview_nodes = self.node_generator.build_nodes(
                seed=int(self.seed or 0),
                chapter_index=chapter.chapter_index,
                chapter_enemy_count=len(getattr(chapter, "commits", [])),
                difficulty=1.0,
                has_boss=True,
                has_events=bool(self.content_runtime.registry.events),
            )
        node_summary = ", ".join(
            f"{kind}={count}" for kind, count in summarize_node_kinds(preview_nodes).items()
        )
        event_hint = ""
        if self.loaded_content_packs and self.content_runtime.registry.events:
            event_ids = sorted(self.content_runtime.registry.events.keys())
            seed = int(self.seed or 0)
            index = (seed + chapter.chapter_index * 17) % len(event_ids)
            label = "Event omen" if self.lang == "en" else "事件预兆"
            event_hint = f"\n🔮 {label}: {event_ids[index]}"

        if self.lang == "en":
            print(
                f"""
{'='*50}
📖 Chapter {chapter.chapter_index + 1}: {chapter.name}
{'='*50}
📝 {chapter.description}
🧭 Nodes: {node_summary}
🏆 Boss chapter: {"yes" if chapter.is_boss_chapter else "no"} (final boss node always exists)
{event_hint}
{'='*50}
"""
            )
            return

        print(
            f"""
{'='*50}
📖 第 {chapter.chapter_index + 1} 章：{chapter.name}
{'='*50}
📝 {chapter.description}
🧭 节点分布: {node_summary}
🏆 Boss 章节: {"是" if chapter.is_boss_chapter else "否"}（章末固定 Boss 节点）
{event_hint}
{'='*50}
"""
        )
    
    def _print_combat_status(self, enemy: EnemyState) -> None:
        """Print combat status."""
        if self._compact_mode:
            return
        if not self.state:
            return
        player = self.state.player.character
        p_bar = self._render_hp_bar(player.current_hp, player.stats.hp.value)
        e_bar = self._render_hp_bar(enemy.current_hp, enemy.max_hp)
        
        print(f"""
{'─'*50}
👤 DEVELOPER (Lv.{player.level})          👾 {enemy.name}
{p_bar}          {e_bar}
MP: {player.current_mp}/{player.stats.mp.value}                 
{'─'*50}""")
    
    def _render_hp_bar(self, current: int, maximum: int, width: int = 20) -> str:
        """Render HP bar."""
        if maximum <= 0:
            return " " * (width + 10)
        
        ratio = current / maximum
        filled = int(ratio * width)
        color = "🟢" if ratio > 0.6 else "🟡" if ratio > 0.3 else "🔴"
        bar = "█" * filled + "░" * (width - filled)
        return f"{color} HP:{current:3}/{maximum:3}|{bar}|"
    
    def _get_combat_choice(
        self,
        enemy: Any,
        turn_number: int,
        is_boss: bool,
        can_escape: bool,
        skill_mp_cost: int,
        skill_damage_bonus: int,
        threat_hint: bool = False,
    ) -> str:
        """Get combat choice."""
        if self.auto_mode:
            if not self.state:
                return ACTION_ATTACK
            player = self.state.player.character
            max_hp = getattr(player.stats.hp, "value", 0)
            context = AutoCombatContext(
                seed=int(self.seed or 0),
                turn_number=turn_number,
                player_hp=player.current_hp,
                player_max_hp=max_hp,
                player_mp=player.current_mp,
                player_attack=player.stats.attack.value,
                enemy_hp=int(getattr(enemy, "current_hp", 0)),
                enemy_max_hp=int(getattr(enemy, "max_hp", 0)),
                enemy_attack_hint=int(getattr(enemy, "attack", 0)),
                skill_mp_cost=skill_mp_cost,
                skill_damage_bonus=skill_damage_bonus,
                can_escape=can_escape,
                is_boss=is_boss,
                threat_hint=threat_hint,
            )
            choice = self.auto_policy.choose_action(context)
            self.metrics.record_action(choice)
            return choice
        
        print("""
🎯 YOUR TURN!
   [1] ⚔️  Attack    [2] 🛡️  Defend
   [3] ✨  Skill     [4] 🏃  Escape
""")
        print("> ", end="", flush=True)
        try:
            return input().strip().lower()
        except EOFError:
            return ACTION_ATTACK
    
    def _print_victory(self) -> None:
        """Print victory."""
        if not self.state:
            return
        player = self.state.player.character
        print(f"""
{'='*60}
🏆 VICTORY! All commits defeated!
{'='*60}

📊 FINAL STATISTICS
   Level: {player.level}
   EXP: {player.experience}
   Enemies: {len(self.state.enemies_defeated)}
   Gold: {self.state.player.gold}
   Items: {len(self.inventory.items)}
{'='*60}
🎉 Congratulations!
""")
    
    def _print_defeat(self) -> None:
        """Print defeat."""
        if not self.state:
            return
        print(f"""
{'='*60}
💀 GAME OVER
{'='*60}
   Level: {self.state.player.character.level}
   Enemies: {len(self.state.enemies_defeated)}
   HP: {self.state.player.character.current_hp}
{'='*60}
💡 Tip: Use Defend to reduce damage!
""")
    
    def _is_github_url(self, input_str: str) -> bool:
        """Check if input is GitHub URL."""
        return "/" in input_str and not os.path.exists(input_str)
    
    def _clone_github_repo(self, repo_input: str) -> Optional[str]:
        """Clone GitHub repository."""
        if repo_input.startswith("https://github.com/"):
            match = re.search(r'github\.com/([^/]+/[^/]+)', repo_input)
            if match:
                repo_path = match.group(1)
            else:
                return None
        else:
            repo_path = repo_input
        
        repo_path = repo_path.rstrip("/")
        if repo_path.endswith(".git"):
            repo_path = repo_path[:-4]
        temp_dir = tempfile.mkdtemp(prefix='git-dungeon-')
        clone_path = os.path.join(temp_dir, repo_path.split('/')[-1])
        
        url = f"https://github.com/{repo_path}.git"
        print(f"🔽 Cloning {url}...")
        
        try:
            result = subprocess.run(
                ['git', 'clone', url, clone_path],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                print("✅ Cloned!")
                return clone_path
            print(f"❌ {result.stderr}")
        except Exception as e:
            print(f"❌ {e}")
        return None


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Git Dungeon - Battle through your commits!",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("repository", nargs="?", default=None, help="Repository path or user/repo")
    parser.add_argument("--seed", "-s", type=int, default=None, help="Random seed")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--compact", action="store_true", help="Compact combat output")
    parser.add_argument("--auto", action="store_true", help="Auto-battle mode")
    parser.add_argument("--metrics-out", type=str, default=None, help="Write gameplay metrics JSON")
    parser.add_argument("--print-metrics", action="store_true", help="Print metrics summary")
    parser.add_argument(
        "--content-pack",
        action="append",
        default=[],
        help="Content pack id/path (repeatable). Also supports GIT_DUNGEON_CONTENT_DIR",
    )
    parser.add_argument(
        "--mutator",
        type=str,
        default="none",
        choices=["none", "hard"],
        help="Gameplay mutator preset",
    )
    parser.add_argument("--daily", action="store_true", help="Use daily challenge seed")
    parser.add_argument("--daily-date", type=str, default=None, help="Daily date (YYYY-MM-DD)")
    parser.add_argument("--lang", "-l", type=str, default="en", 
                        choices=["en", "zh", "zh_CN"],
                        help="Language (en/zh_CN, zh alias)")
    
    args = parser.parse_args()
    
    if not args.repository:
        print("""
🎮 Git Dungeon - CLI

Usage:
    python src/main_cli_new.py <repo> [options]

Examples:
    python src/main_cli_new.py username/repo --lang zh_CN
    python src/main_cli_new.py . --seed 12345 --lang zh_CN
    python src/main_cli_new.py . --content-pack content_packs/example_pack --auto --compact
""")
        return
    
    effective_seed, daily_info = resolve_run_seed(
        seed=args.seed,
        daily=args.daily,
        daily_date=args.daily_date,
    )
    game = GitDungeonCLI(
        seed=effective_seed,
        verbose=args.verbose,
        auto_mode=args.auto,
        lang=args.lang,
        compact=args.compact,
        metrics_out=args.metrics_out,
        print_metrics=args.print_metrics,
        content_pack_args=args.content_pack,
        mutator=args.mutator,
        daily_info=daily_info,
    )
    
    try:
        game.start(args.repository)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
