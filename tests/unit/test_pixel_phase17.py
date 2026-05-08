"""Phase 17 tests for title, theme sprites, animation, and BGM policy."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from PIL import Image

from git_dungeon.ui_pixel.audio import BGM_FILES, BGM_LOOPS
from git_dungeon.ui_pixel.game_runner import NodeSnapshot, PlayerSnapshot
from git_dungeon.ui_pixel.screens.dungeon import CHAPTER_ACCENTS, DungeonScreen
from git_dungeon.ui_pixel.screens.title import TitleScreen

ROOT = Path(__file__).resolve().parents[2]
ASSET_PLAN = ROOT / "assets/generated/phase17/asset_plan.json"
MANIFEST = ROOT / "assets/manifest_sprites.json"


class FakeDraw:
    @staticmethod
    def rect(*_args: Any, **_kwargs: Any) -> None:
        return None

    @staticmethod
    def line(*_args: Any, **_kwargs: Any) -> None:
        return None

    @staticmethod
    def circle(*_args: Any, **_kwargs: Any) -> None:
        return None


class FakeFonts:
    @staticmethod
    def draw(*_args: Any, **_kwargs: Any) -> None:
        return None

    @staticmethod
    def draw_fit(*_args: Any, **_kwargs: Any) -> None:
        return None

    @staticmethod
    def measure(text: str, _size: int = 16) -> int:
        return len(text) * 6

    @staticmethod
    def fit(text: str, _max_width: int, _size: int = 16) -> str:
        return text


class FakeSurface:
    @staticmethod
    def fill(*_args: Any, **_kwargs: Any) -> None:
        return None


class RecordingAssets:
    def __init__(self) -> None:
        self.drawn: list[str] = []

    def draw(self, _surface: Any, sprite_id: str, _rect: tuple[int, int, int, int]) -> None:
        self.drawn.append(sprite_id)


class FakeRunner:
    def __init__(self) -> None:
        self.dungeon_player_coord: tuple[int, int] | None = None
        self.nodes = (
            NodeSnapshot("n0", "battle", 0, "Battle", False, True, False),
            NodeSnapshot("n1", "elite", 1, "Elite", False, True, False),
            NodeSnapshot("n2", "event", 2, "Event", True, True, False),
            NodeSnapshot("n3", "shop", 3, "Shop", False, False, False),
            NodeSnapshot("n4", "boss", 4, "Boss", False, False, False),
        )

    def route_nodes(self) -> tuple[NodeSnapshot, ...]:
        return self.nodes

    def player_snapshot(self) -> PlayerSnapshot:
        return PlayerSnapshot(hp=80, max_hp=100, mp=40, max_mp=50, attack=12, gold=60)

    def current_node_snapshot(self) -> NodeSnapshot:
        return self.nodes[2]

    def current_chapter(self) -> Any:
        return SimpleNamespace(chapter_index=2)

    @staticmethod
    def is_dungeon_reward_claimed(_reward_id: str) -> bool:
        return False

    @staticmethod
    def has_dungeon_key(_key_id: str) -> bool:
        return True

    @staticmethod
    def is_dungeon_trap_consumed(_trap_id: str) -> bool:
        return False


def test_phase17_asset_plan_has_complete_generation_chain() -> None:
    plan = json.loads(ASSET_PLAN.read_text(encoding="utf-8"))

    assert plan["source"] == "codex_builtin_gpt_image_2"
    assert Path(ROOT / plan["prompt_file"]).is_file()
    assert Path(ROOT / plan["raw_file"]).is_file()
    assert Path(ROOT / plan["contact_sheet"]).is_file()
    assert len(plan["assets"]) == 8

    ids = [asset["id"] for asset in plan["assets"]]
    assert ids == [
        "title_banner",
        "dungeon_entrance",
        "commit_shard",
        "branch_door",
        "merge_conflict_trap",
        "ci_sentinel",
        "release_gate",
        "torch_lit",
    ]


def test_phase17_processed_assets_match_declared_sizes() -> None:
    plan = json.loads(ASSET_PLAN.read_text(encoding="utf-8"))

    for asset in plan["assets"]:
        path = ROOT / "assets/generated/processed" / plan["phase"] / f"{asset['id']}.png"
        with Image.open(path) as image:
            assert image.mode == "RGBA"
            assert image.size == tuple(asset["size"])


def test_phase17_assets_are_declared_in_runtime_manifest() -> None:
    plan = json.loads(ASSET_PLAN.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    source_roots = {source["root"] for source in manifest["sources"]}
    assert f"assets/generated/processed/{plan['phase']}" in source_roots
    for asset in plan["assets"]:
        expected = f"assets/generated/processed/{plan['phase']}/{asset['id']}.png"
        assert manifest["sprites"][asset["id"]] == expected


def test_phase17_verifier_accepts_generated_assets() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/verify_pixel_assets.py",
            "--asset-cards",
            "assets/generated/phase17/asset_plan.json",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_title_draws_git_dungeon_theme_assets_and_animates() -> None:
    assets = RecordingAssets()
    screen = TitleScreen(
        SimpleNamespace(draw=FakeDraw()),
        FakeFonts(),
        runner=object(),
        assets=assets,
        settings=SimpleNamespace(lang="zh_CN"),
    )

    screen.update(0.2)
    screen.draw(FakeSurface())

    drawn = set(assets.drawn)
    assert screen.anim_time == 0.2
    assert "title_banner" in drawn
    assert "dungeon_entrance" in drawn
    assert "torch_lit" in drawn
    assert "player_idle" in drawn
    assert "ci_sentinel" in drawn


def test_dungeon_draws_git_theme_objects_and_chapter_palette() -> None:
    assets = RecordingAssets()
    screen = DungeonScreen(
        SimpleNamespace(draw=FakeDraw()),
        FakeFonts(),
        FakeRunner(),
        assets,
        settings=SimpleNamespace(lang="zh_CN"),
    )

    screen.update(0.25)
    screen.draw(FakeSurface())

    drawn = set(assets.drawn)
    assert screen.anim_time == 0.25
    assert screen._chapter_accent() == CHAPTER_ACCENTS[2]
    assert "branch_door" in drawn
    assert "merge_conflict_trap" in drawn
    assert "commit_shard" in drawn
    assert "ci_sentinel" in drawn
    assert "release_gate" in drawn
    assert "torch_lit" in drawn


def test_bgm_loop_policy_is_explicit_for_every_slot() -> None:
    assert set(BGM_LOOPS) == set(BGM_FILES)
    assert BGM_LOOPS["title"] == -1
    assert BGM_LOOPS["chapter"] == -1
    assert BGM_LOOPS["boss"] == -1
    assert BGM_LOOPS["gameover"] == 0
