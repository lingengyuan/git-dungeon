"""Tests for daily challenge helpers."""

from git_dungeon.engine.daily import build_shareable_run_id, resolve_run_seed


def test_daily_seed_resolution_is_deterministic() -> None:
    seed, info = resolve_run_seed(seed=42, daily=True, daily_date="2026-02-06")
    assert seed == 20260206
    assert info is not None
    assert info.date_iso == "2026-02-06"
    assert info.seed == 20260206


def test_shareable_run_id_is_stable_and_pack_order_independent() -> None:
    run_id_1 = build_shareable_run_id(
        repository="/tmp/repo",
        seed=20260206,
        mutator="hard",
        content_pack_ids=["b_pack", "a_pack"],
        daily_date_iso="2026-02-06",
    )
    run_id_2 = build_shareable_run_id(
        repository="/tmp/repo",
        seed=20260206,
        mutator="hard",
        content_pack_ids=["a_pack", "b_pack"],
        daily_date_iso="2026-02-06",
    )
    assert run_id_1 == run_id_2
    assert run_id_1.startswith("daily-20260206-")
