"""Tests for M5 chapter-node flow in compact mode."""

from __future__ import annotations

from types import SimpleNamespace

from git_dungeon.content.schema import EventChoice, EventDef, EventEffect
from git_dungeon.engine import GameState
from git_dungeon.engine.route import NodeKind, RouteNode
from git_dungeon.main_cli import GitDungeonCLI


class _DummyChapterSystem:
    def __init__(self, chapter):
        self._chapter = chapter
        self._done = False

    def get_current_chapter(self):
        if self._done:
            return None
        return self._chapter

    def complete_current_chapter(self):
        return self._chapter

    def advance_chapter(self):
        self._done = True
        return False


def test_compact_node_flow_has_stable_event_rest_shop_lines(capsys) -> None:
    cli = GitDungeonCLI(seed=19, auto_mode=True, compact=True)
    cli.state = GameState(seed=19, repo_path=".", total_commits=5, current_commit_index=0, difficulty="normal")
    cli.state.route_state = {"current_node_id": "", "visited_nodes": [], "route_flags": {}, "chapter_nodes": {}}
    cli.state.player.character.current_hp = 20
    cli.state.player.gold = 100

    chapter = SimpleNamespace(
        chapter_id="chapter_0",
        chapter_index=0,
        name="Node Chapter",
        description="Node flow test",
        commits=[SimpleNamespace(hexsha="a" * 40, message="feat: a", total_changes=5)],
        start_index=0,
        enemies_defeated=0,
        enemy_count=1,
        is_boss_chapter=False,
        config=SimpleNamespace(
            gold_bonus=1.0,
            exp_bonus=1.0,
            enemy_hp_multiplier=1.0,
            enemy_atk_multiplier=1.0,
            shop_enabled=True,
        ),
    )
    cli.chapter_system = _DummyChapterSystem(chapter)

    cli.content_runtime.registry.events = {
        "node_camp": EventDef(
            id="node_camp",
            name_key="event.node_camp.name",
            desc_key="event.node_camp.desc",
            choices=[
                EventChoice(
                    id="heal",
                    text_key="event.node_camp.choice.heal",
                    effects=[EventEffect(opcode="heal", value=15)],
                ),
                EventChoice(
                    id="risk",
                    text_key="event.node_camp.choice.risk",
                    effects=[
                        EventEffect(opcode="take_damage", value=8),
                        EventEffect(opcode="gain_gold", value=25),
                    ],
                ),
            ],
            route_tags=["safe"],
            weights={"default": 10},
        )
    }

    nodes = [
        RouteNode("ch0_node0_battle", NodeKind.BATTLE, 0, [], {}),
        RouteNode("ch0_node1_event", NodeKind.EVENT, 1, [], {}),
        RouteNode("ch0_node2_rest", NodeKind.REST, 2, [], {}),
        RouteNode("ch0_node3_shop", NodeKind.SHOP, 3, [], {}),
        RouteNode("ch0_node4_boss", NodeKind.BOSS, 4, [], {}),
    ]
    cli._chapter_nodes[chapter.chapter_id] = nodes
    cli._chapter_node_cursor[chapter.chapter_id] = 0

    cli.metrics.record_chapter_started()

    def fake_combat(_chapter, node):
        print(f"N{node.position + 1:02d} node={node.kind.value} enemy=stub")
        return True

    def fake_boss(_chapter, node):
        print(f"N{node.position + 1:02d} node=boss enemy=stub_boss")
        return True

    cli._resolve_combat_node = fake_combat  # type: ignore[method-assign]
    cli._resolve_boss_node = fake_boss  # type: ignore[method-assign]

    result = cli._game_loop()
    out = capsys.readouterr().out

    assert result is True
    assert "node=event event=node_camp choice=heal" in out
    assert "node=rest" in out
    assert "node=shop" in out
    assert "node=boss" in out
    metrics = cli.metrics.to_dict()
    assert metrics["node_type_counts"]["event"] == 1
    assert metrics["node_type_counts"]["rest"] == 1
    assert metrics["node_type_counts"]["shop"] == 1
    assert metrics["event_choice_distribution"]["node_camp:heal"] == 1
