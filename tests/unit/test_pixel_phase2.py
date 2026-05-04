"""Phase 2 tests for non-combat pixel screens and runner actions."""

from __future__ import annotations

import subprocess
from pathlib import Path

from git_dungeon.engine.route import NodeKind
from git_dungeon.ui_pixel.game_runner import GameRunner
from git_dungeon.ui_pixel.layout import window_to_logical


def _make_git_repo(path: Path, commit_count: int = 10) -> Path:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "pixel@example.com"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Pixel Tester"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    for idx in range(commit_count):
        message = f"feat: route node {idx}"
        (path / f"file_{idx}.txt").write_text(f"{message}\n{idx}\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", message], cwd=path, check=True, capture_output=True)
    return path


def _loaded_runner(path: Path) -> GameRunner:
    repo = _make_git_repo(path)
    runner = GameRunner(str(repo), seed=42, lang="en")
    runner.load_repository()
    return runner


def _move_cursor_to_kind(runner: GameRunner, kind: NodeKind) -> None:
    for chapter_index, _chapter in enumerate(runner.chapter_system.chapters):
        runner.chapter_system.current_chapter_index = chapter_index
        chapter = runner.current_chapter()
        assert chapter is not None
        nodes = runner.prepare_current_chapter_nodes()
        for idx, node in enumerate(nodes):
            if node.kind == kind:
                runner._chapter_node_cursor[chapter.chapter_id] = idx
                return
    raise AssertionError(f"No node kind found: {kind.value}")


def test_window_to_logical_handles_letterbox_and_scale() -> None:
    assert window_to_logical((640, 360), (1280, 720), (320, 180)) == (160, 90)
    assert window_to_logical((400, 400), (800, 800), (320, 180)) == (160, 90)
    assert window_to_logical((20, 20), (800, 800), (320, 180)) is None


def test_runner_resolves_rest_with_real_state_change(tmp_path: Path) -> None:
    runner = _loaded_runner(tmp_path)
    _move_cursor_to_kind(runner, NodeKind.REST)
    state = runner.state
    assert state is not None
    state.player.character.current_hp = 50

    result = runner.resolve_current_rest("heal")

    assert result.choice == "heal"
    assert result.hp_delta > 0
    assert state.player.character.current_hp == 80


def test_runner_resolves_event_and_advances_route(tmp_path: Path) -> None:
    runner = _loaded_runner(tmp_path)
    _move_cursor_to_kind(runner, NodeKind.EVENT)
    before = runner.current_node()
    assert before is not None

    event = runner.event_for_node()
    assert event is not None
    result = runner.resolve_current_event(0)

    assert result.event_id == event.event_id
    assert result.choice_id == event.choices[0].choice_id
    assert before.node_id in runner.state.route_state["visited_nodes"]  # type: ignore[union-attr,index]


def test_runner_shop_purchase_and_insufficient_gold_are_explicit(tmp_path: Path) -> None:
    runner = _loaded_runner(tmp_path)
    _move_cursor_to_kind(runner, NodeKind.SHOP)
    state = runner.state
    assert state is not None
    state.player.gold = 0

    blocked = runner.resolve_current_shop(0)

    assert blocked.purchased is False
    assert blocked.reason == "insufficient_gold"
    assert state.player.gold == 0

    second = tmp_path / "second"
    second.mkdir()
    runner = _loaded_runner(second)
    _move_cursor_to_kind(runner, NodeKind.SHOP)
    state = runner.state
    assert state is not None
    state.player.gold = 999
    offer = runner.shop_offers()[0]

    bought = runner.resolve_current_shop(0)

    assert bought.purchased is True
    assert bought.choice == offer.offer_id
    assert state.player.gold == 999 - offer.cost
