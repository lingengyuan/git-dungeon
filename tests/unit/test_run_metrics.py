"""Unit tests for gameplay run metrics."""

import json

from git_dungeon.engine.run_metrics import RunMetrics


def test_metrics_accumulate_and_keep_schema() -> None:
    metrics = RunMetrics(seed=7, auto_mode=True)
    metrics.record_chapter_started()
    metrics.record_action("1")
    metrics.record_action("2")
    metrics.record_action("1")
    metrics.record_node("battle")
    metrics.record_node("event")
    metrics.record_node("rest")
    metrics.record_node("shop")
    metrics.record_event_choice("rest_site", "rest")
    metrics.record_rest_choice("heal")
    metrics.record_shop_choice("patch_kit")
    metrics.record_battle(turns=3, won=True, is_boss=False)
    metrics.record_battle(turns=5, won=False, is_boss=True)
    metrics.record_chapter_complete()
    metrics.record_rewards(exp=20, gold=10, drops=1, level_up=True)
    metrics.finalize(run_victory=False)

    data = metrics.to_dict()
    assert data["schema_version"] == "m1_metrics_v1"
    assert data["seed"] == 7
    assert data["auto_mode"] is True
    assert data["chapters_started"] == 1
    assert data["battles_total"] == 2
    assert data["boss_battles_total"] == 1
    assert data["battles_won"] == 1
    assert data["battles_lost"] == 1
    assert data["battle_turns_total"] == 8
    assert data["chapters_completed"] == 1
    assert data["level_up_count"] == 1
    assert data["drops_count"] == 1
    assert data["total_exp_gained"] == 20
    assert data["total_gold_gained"] == 10
    assert data["action_distribution"]["attack"] == 2
    assert data["action_distribution"]["defend"] == 1
    assert data["node_type_counts"]["event"] == 1
    assert data["node_type_counts"]["rest"] == 1
    assert data["events_seen"] == ["rest_site"]
    assert data["event_choice_distribution"]["rest_site:rest"] == 1
    assert data["rest_choice_distribution"]["heal"] == 1
    assert data["shop_choice_distribution"]["patch_kit"] == 1


def test_metrics_json_output(tmp_path) -> None:
    metrics = RunMetrics(seed=11, auto_mode=True)
    metrics.record_chapter_started()
    metrics.record_node("event")
    metrics.record_event_choice("merchant", "buy_card")
    metrics.record_battle(turns=2, won=True)
    metrics.finalize(run_victory=True)

    output = tmp_path / "metrics" / "run.json"
    metrics.write_json(output)

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "m1_metrics_v1"
    assert payload["run_victory"] is True
    assert payload["battles_total"] == 1
    assert payload["events_seen"] == ["merchant"]
    assert payload["event_choice_distribution"]["merchant:buy_card"] == 1
