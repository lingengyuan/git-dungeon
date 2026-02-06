"""Runtime metrics for CLI simulation and balancing."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .auto_policy import ACTION_LABELS


@dataclass
class RunMetrics:
    """Collect lightweight gameplay metrics during one run."""

    seed: int | None
    auto_mode: bool
    battles_total: int = 0
    boss_battles_total: int = 0
    battles_won: int = 0
    battles_lost: int = 0
    battle_turns_total: int = 0
    chapters_completed: int = 0
    run_victory: bool = False
    chapters_started: int = 0
    level_up_count: int = 0
    drops_count: int = 0
    total_exp_gained: int = 0
    total_gold_gained: int = 0
    action_distribution: dict[str, int] = field(
        default_factory=lambda: {"attack": 0, "defend": 0, "skill": 0, "escape": 0}
    )
    node_type_counts: dict[str, int] = field(
        default_factory=lambda: {
            "battle": 0,
            "event": 0,
            "rest": 0,
            "shop": 0,
            "elite": 0,
            "boss": 0,
        }
    )
    events_seen: list[str] = field(default_factory=list)
    event_choice_distribution: dict[str, int] = field(default_factory=dict)
    rest_choice_distribution: dict[str, int] = field(default_factory=dict)
    shop_choice_distribution: dict[str, int] = field(default_factory=dict)

    def record_action(self, action: str) -> None:
        """Record one selected combat action."""
        action_name = ACTION_LABELS.get(action, action)
        self.action_distribution[action_name] = self.action_distribution.get(action_name, 0) + 1

    def record_battle(self, turns: int, won: bool, is_boss: bool = False) -> None:
        """Record one battle result."""
        self.battles_total += 1
        self.battle_turns_total += max(0, turns)
        if is_boss:
            self.boss_battles_total += 1
        if won:
            self.battles_won += 1
        else:
            self.battles_lost += 1

    def record_chapter_complete(self) -> None:
        """Record one chapter completion."""
        self.chapters_completed += 1

    def record_chapter_started(self) -> None:
        """Record one chapter start."""
        self.chapters_started += 1

    def record_node(self, node_kind: str) -> None:
        """Record one visited route node kind."""
        key = str(node_kind).strip().lower()
        self.node_type_counts[key] = self.node_type_counts.get(key, 0) + 1

    def record_event_choice(self, event_id: str, choice_id: str) -> None:
        """Record one event decision."""
        if event_id:
            self.events_seen.append(event_id)
        if event_id and choice_id:
            key = f"{event_id}:{choice_id}"
        elif choice_id:
            key = choice_id
        else:
            key = "unknown"
        self.event_choice_distribution[key] = self.event_choice_distribution.get(key, 0) + 1

    def record_rest_choice(self, choice: str) -> None:
        """Record rest-node decision distribution."""
        key = choice or "unknown"
        self.rest_choice_distribution[key] = self.rest_choice_distribution.get(key, 0) + 1

    def record_shop_choice(self, choice: str) -> None:
        """Record shop-node decision distribution."""
        key = choice or "skip"
        self.shop_choice_distribution[key] = self.shop_choice_distribution.get(key, 0) + 1

    def record_rewards(self, exp: int, gold: int, drops: int = 0, level_up: bool = False) -> None:
        """Record rewards from battle or chapter completion."""
        self.total_exp_gained += max(0, exp)
        self.total_gold_gained += max(0, gold)
        self.drops_count += max(0, drops)
        if level_up:
            self.level_up_count += 1

    def finalize(self, run_victory: bool) -> None:
        """Finalize run-level fields."""
        self.run_victory = run_victory

    def to_dict(self) -> dict:
        """Serialize metrics to a stable JSON-friendly structure."""
        avg_turns = self.battle_turns_total / self.battles_total if self.battles_total else 0.0
        win_rate = self.battles_won / self.battles_total if self.battles_total else 0.0
        chapter_base = self.chapters_started if self.chapters_started else max(1, self.chapters_completed)
        avg_events_per_chapter = self.node_type_counts.get("event", 0) / chapter_base
        avg_rest_per_chapter = self.node_type_counts.get("rest", 0) / chapter_base
        avg_shop_per_chapter = self.node_type_counts.get("shop", 0) / chapter_base
        return {
            "schema_version": "m1_metrics_v1",
            "seed": self.seed,
            "auto_mode": self.auto_mode,
            "battles_total": self.battles_total,
            "boss_battles_total": self.boss_battles_total,
            "battles_won": self.battles_won,
            "battles_lost": self.battles_lost,
            "win_rate": round(win_rate, 4),
            "battle_turns_total": self.battle_turns_total,
            "avg_battle_turns": round(avg_turns, 4),
            "chapters_started": self.chapters_started,
            "chapters_completed": self.chapters_completed,
            "run_victory": self.run_victory,
            "level_up_count": self.level_up_count,
            "drops_count": self.drops_count,
            "total_exp_gained": self.total_exp_gained,
            "total_gold_gained": self.total_gold_gained,
            "action_distribution": dict(sorted(self.action_distribution.items())),
            "node_type_counts": dict(sorted(self.node_type_counts.items())),
            "events_seen": list(self.events_seen),
            "event_choice_distribution": dict(sorted(self.event_choice_distribution.items())),
            "rest_choice_distribution": dict(sorted(self.rest_choice_distribution.items())),
            "shop_choice_distribution": dict(sorted(self.shop_choice_distribution.items())),
            "avg_events_per_chapter": round(avg_events_per_chapter, 4),
            "avg_rest_per_chapter": round(avg_rest_per_chapter, 4),
            "avg_shop_per_chapter": round(avg_shop_per_chapter, 4),
        }

    def write_json(self, path: str | Path) -> None:
        """Write metrics snapshot to JSON file."""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    def summary_lines(self) -> list[str]:
        """Render concise summary lines for console output."""
        data = self.to_dict()
        action_parts = [f"{k}={v}" for k, v in data["action_distribution"].items()]
        return [
            "METRICS SUMMARY",
            f"  battles={data['battles_total']} win_rate={data['win_rate']:.2f}",
            f"  avg_turns={data['avg_battle_turns']:.2f} chapters={data['chapters_completed']}",
            f"  level_ups={data['level_up_count']} drops={data['drops_count']}",
            f"  rewards: exp={data['total_exp_gained']} gold={data['total_gold_gained']}",
            f"  actions: {', '.join(action_parts)}",
            (
                "  nodes: "
                f"battle={data['node_type_counts'].get('battle', 0)} "
                f"event={data['node_type_counts'].get('event', 0)} "
                f"rest={data['node_type_counts'].get('rest', 0)} "
                f"shop={data['node_type_counts'].get('shop', 0)}"
            ),
        ]
