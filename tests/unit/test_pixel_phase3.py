"""Phase 3 tests for pixel battle flow."""

from __future__ import annotations

import subprocess
from pathlib import Path

from git_dungeon.engine.auto_policy import ACTION_ATTACK, ACTION_ESCAPE, ACTION_SKILL
from git_dungeon.engine.route import NodeKind
from git_dungeon.ui_pixel.game_runner import GameRunner


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
        message = f"feat: battle node {idx}"
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


def test_runner_attack_can_win_battle_and_advance_route(tmp_path: Path) -> None:
    runner = _loaded_runner(tmp_path)
    _move_cursor_to_kind(runner, NodeKind.BATTLE)
    node = runner.current_node()
    assert node is not None
    snapshot = runner.start_current_battle()
    assert snapshot.can_escape is True
    assert runner.current_enemy is not None
    runner.current_enemy.current_hp = 1

    result, ended = runner.resolve_battle_action(ACTION_ATTACK)

    assert result.battle_over is True
    assert result.won is True
    assert ended.won is True
    assert runner.last_reward_snapshot() is not None
    assert node.node_id in runner.state.route_state["visited_nodes"]  # type: ignore[union-attr,index]


def test_runner_rejects_skill_without_mp_without_enemy_turn(tmp_path: Path) -> None:
    runner = _loaded_runner(tmp_path)
    _move_cursor_to_kind(runner, NodeKind.BATTLE)
    runner.start_current_battle()
    state = runner.state
    assert state is not None
    state.player.character.current_mp = 0
    before_hp = state.player.character.current_hp

    result, snapshot = runner.resolve_battle_action(ACTION_SKILL)

    assert result.accepted is False
    assert "Need 10 MP" in result.message
    assert state.player.character.current_hp == before_hp
    assert snapshot.player.mp == 0


def test_runner_boss_disables_escape(tmp_path: Path) -> None:
    runner = _loaded_runner(tmp_path)
    _move_cursor_to_kind(runner, NodeKind.BOSS)
    snapshot = runner.start_current_battle()

    result, after = runner.resolve_battle_action(ACTION_ESCAPE)

    assert snapshot.can_escape is False
    assert result.accepted is False
    assert "Cannot escape" in result.message
    assert after.can_escape is False
    assert runner.current_enemy is not None
