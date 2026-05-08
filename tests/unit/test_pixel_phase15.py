"""Phase 15 tests for generated battle sprites and combat scene rendering."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from PIL import Image

from git_dungeon.engine.auto_policy import ACTION_ATTACK
from git_dungeon.ui_pixel.screens.battle import BattleScreen
from git_dungeon.ui_pixel.text import boss_phase_label, enemy_name_label


ROOT = Path(__file__).resolve().parents[2]
ASSET_PLAN = ROOT / "assets/generated/phase15/asset_plan.json"
MANIFEST = ROOT / "assets/manifest_sprites.json"


class FakeSprite:
    def set_alpha(self, _alpha: int) -> None:
        return None


class FakeTransform:
    @staticmethod
    def scale(_sprite: Any, _size: tuple[int, int]) -> FakeSprite:
        return FakeSprite()


class FakeDraw:
    @staticmethod
    def rect(*_args: Any, **_kwargs: Any) -> None:
        return None

    @staticmethod
    def line(*_args: Any, **_kwargs: Any) -> None:
        return None


class FakePygame:
    draw = FakeDraw()
    transform = FakeTransform()


class FakeFonts:
    @staticmethod
    def draw(*_args: Any, **_kwargs: Any) -> None:
        return None

    @staticmethod
    def draw_fit(*_args: Any, **_kwargs: Any) -> None:
        return None

    @staticmethod
    def measure(text: str, _size: int) -> int:
        return len(text) * 6

    @staticmethod
    def fit(text: str, _max_width: int, _size: int) -> str:
        return text


class FakeSurface:
    @staticmethod
    def fill(*_args: Any, **_kwargs: Any) -> None:
        return None

    @staticmethod
    def blit(*_args: Any, **_kwargs: Any) -> None:
        return None


class RecordingAssets:
    def __init__(self) -> None:
        self.drawn: list[str] = []
        self.loaded: list[str] = []

    def draw(self, _surface: Any, sprite_id: str, _rect: tuple[int, int, int, int]) -> None:
        self.drawn.append(sprite_id)

    def get(self, sprite_id: str) -> FakeSprite:
        self.loaded.append(sprite_id)
        return FakeSprite()


class FakeRunner:
    def __init__(self, enemy: Any) -> None:
        self.enemy = enemy
        self.snapshot = self._snapshot(enemy)

    def start_current_battle(self) -> Any:
        return self.snapshot

    def resolve_battle_action(self, _action: str) -> tuple[Any, Any]:
        result = SimpleNamespace(
            accepted=True,
            player_damage=7,
            enemy_damage=0,
            critical=False,
            defended=False,
            battle_over=False,
            won=False,
            player_defeated=False,
            escaped=False,
            message="Dealt 7",
        )
        return result, self.snapshot

    def _snapshot(self, enemy: Any) -> Any:
        return SimpleNamespace(
            player=SimpleNamespace(hp=80, max_hp=100, mp=30, max_mp=50),
            enemy=enemy,
            turn=1,
            can_escape=not enemy.is_boss,
            skill_cost=10,
            message="Battle started",
        )


def _enemy(name: str, *, boss: bool = False, elite: bool = False) -> Any:
    return SimpleNamespace(
        name=name,
        hp=40,
        max_hp=40,
        attack=8,
        is_boss=boss,
        is_elite=elite,
        phase="",
    )


def _screen(enemy: Any, assets: RecordingAssets) -> BattleScreen:
    return BattleScreen(
        FakePygame(),
        FakeFonts(),
        FakeRunner(enemy),
        assets,
        settings=SimpleNamespace(lang="zh_CN"),
    )


def test_phase15_asset_plan_has_complete_generation_chain() -> None:
    plan = json.loads(ASSET_PLAN.read_text(encoding="utf-8"))

    assert plan["source"] == "codex_builtin_gpt_image_2"
    assert Path(ROOT / plan["prompt_file"]).is_file()
    assert Path(ROOT / plan["raw_file"]).is_file()
    assert Path(ROOT / plan["contact_sheet"]).is_file()
    assert len(plan["assets"]) == 13


def test_phase15_processed_assets_match_declared_sizes_and_manifest() -> None:
    plan = json.loads(ASSET_PLAN.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert f"assets/generated/processed/{plan['phase']}" in {
        source["root"] for source in manifest["sources"]
    }
    for asset in plan["assets"]:
        processed = ROOT / "assets/generated/processed" / plan["phase"] / f"{asset['id']}.png"
        with Image.open(processed) as image:
            assert image.mode == "RGBA"
            assert image.size == tuple(asset["size"])
        assert manifest["sprites"][asset["id"]] == (
            f"assets/generated/processed/{plan['phase']}/{asset['id']}.png"
        )


def test_enemy_names_use_player_language_for_common_battle_identities() -> None:
    assert enemy_name_label("Git Goblin", "zh_CN") == "Git 小怪"
    assert enemy_name_label("Merge Conflict", "zh_CN") == "合并冲突"
    assert enemy_name_label("Elite Bug: crash on launch", "zh_CN") == "精英 缺陷：crash on launch"
    assert enemy_name_label("Feature: dungeon room", "zh_CN") == "功能：dungeon room"
    assert boss_phase_label("phase_1", "zh_CN") == "阶段 1"
    assert boss_phase_label("enraged", "zh_CN") == "狂暴"


def test_battle_draw_uses_phase15_player_enemy_and_scene_sprites() -> None:
    assets = RecordingAssets()
    screen = _screen(_enemy("Git Goblin"), assets)

    assert screen.message == "战斗开始"

    screen.draw(FakeSurface())

    assert "player_idle" in assets.drawn
    assert "enemy_default_git_goblin" in assets.loaded
    assert "tile_wall_stone" in assets.drawn
    assert "tile_floor_stone" in assets.drawn


def test_boss_draw_uses_named_boss_sprite() -> None:
    assets = RecordingAssets()
    screen = _screen(_enemy("Merge Conflict", boss=True), assets)

    screen.draw(FakeSurface())

    assert "boss_merge_conflict" in assets.loaded


def test_attack_action_draws_attack_pose_and_slash_fx() -> None:
    assets = RecordingAssets()
    screen = _screen(_enemy("Git Goblin"), assets)

    screen._act(ACTION_ATTACK)
    screen.draw(FakeSurface())

    assert "player_attack" in assets.drawn
    assert "fx_slash" in assets.drawn
