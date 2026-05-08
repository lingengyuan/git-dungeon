"""Phase 16 tests for non-combat location scenes."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from PIL import Image

from git_dungeon.ui_pixel.screens.event import EventScreen
from git_dungeon.ui_pixel.screens.rest import RestScreen
from git_dungeon.ui_pixel.screens.shop import ShopScreen
from git_dungeon.ui_pixel.text import event_choice_label, shop_offer_title


ROOT = Path(__file__).resolve().parents[2]
ASSET_PLAN = ROOT / "assets/generated/phase16/asset_plan.json"
MANIFEST = ROOT / "assets/manifest_sprites.json"


class FakeDraw:
    @staticmethod
    def rect(*_args: Any, **_kwargs: Any) -> None:
        return None

    @staticmethod
    def line(*_args: Any, **_kwargs: Any) -> None:
        return None


class FakePygame:
    draw = FakeDraw()


class RecordingFonts:
    def __init__(self) -> None:
        self.texts: list[str] = []

    def draw(self, _surface: Any, text: str, *_args: Any, **_kwargs: Any) -> None:
        self.texts.append(text)

    def draw_fit(self, _surface: Any, text: str, *_args: Any, **_kwargs: Any) -> None:
        self.texts.append(text)

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


class RecordingAssets:
    def __init__(self) -> None:
        self.drawn: list[str] = []

    def draw(self, _surface: Any, sprite_id: str, _rect: tuple[int, int, int, int]) -> None:
        self.drawn.append(sprite_id)


class FakeRunner:
    def event_for_node(self) -> Any:
        return SimpleNamespace(
            event_id="debug_event_id",
            choices=(
                SimpleNamespace(index=0, choice_id="safe", effects=("heal", "gain_gold")),
                SimpleNamespace(index=1, choice_id="risk", effects=("take_damage", "gain_gold")),
                SimpleNamespace(index=2, choice_id="battle", effects=("start_battle",)),
            ),
        )

    def shop_offers(self) -> tuple[Any, ...]:
        return (
            SimpleNamespace(
                index=0,
                label="Restore 30 HP",
                cost=20,
                heal=30,
                attack=0,
                mp=0,
                max_hp=0,
                affordable=True,
            ),
            SimpleNamespace(
                index=1,
                label="Attack +2, Max HP +5, HP +5",
                cost=60,
                heal=5,
                attack=2,
                mp=0,
                max_hp=5,
                affordable=True,
            ),
            SimpleNamespace(
                index=2,
                label="Focus",
                cost=90,
                heal=0,
                attack=0,
                mp=15,
                max_hp=0,
                affordable=False,
            ),
        )

    def rest_options(self) -> tuple[Any, ...]:
        return (
            SimpleNamespace(action="heal", label="Heal", detail="Restore 30 HP"),
            SimpleNamespace(action="focus", label="Focus", detail="Attack +2, Max HP +5, HP +5"),
        )

    @staticmethod
    def player_snapshot() -> Any:
        return SimpleNamespace(gold=60)


def test_phase16_asset_plan_has_complete_generation_chain() -> None:
    plan = json.loads(ASSET_PLAN.read_text(encoding="utf-8"))

    assert plan["source"] == "codex_builtin_gpt_image_2"
    assert Path(ROOT / plan["prompt_file"]).is_file()
    assert Path(ROOT / plan["raw_file"]).is_file()
    assert Path(ROOT / plan["contact_sheet"]).is_file()
    assert len(plan["assets"]) == 8


def test_phase16_processed_assets_match_declared_sizes_and_manifest() -> None:
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


def test_event_screen_draws_location_and_choice_icons() -> None:
    assets = RecordingAssets()
    EventScreen(
        FakePygame(), RecordingFonts(), FakeRunner(), assets, settings=SimpleNamespace(lang="zh_CN")
    ).draw(FakeSurface())

    assert {
        "tile_wall_stone",
        "tile_floor_stone",
        "choice_icon_reward",
        "choice_icon_risk",
    }.issubset(set(assets.drawn))
    assert {"event_shrine", "event_terminal_ruin"} & set(assets.drawn)
    assert event_choice_label(1, ("take_damage", "gain_gold"), "zh_CN") == "2. 冒险选择"


def test_shop_screen_draws_merchant_scene_and_sanitized_titles() -> None:
    assets = RecordingAssets()
    fonts = RecordingFonts()

    ShopScreen(
        FakePygame(), fonts, FakeRunner(), assets, settings=SimpleNamespace(lang="zh_CN")
    ).draw(FakeSurface())

    assert "shopkeeper" in assets.drawn
    assert "shop_counter" in assets.drawn
    assert shop_offer_title("Restore 30 HP", "zh_CN") == "恢复生命"
    assert any("恢复生命" in text for text in fonts.texts)
    assert "Restore 30 HP" not in fonts.texts


def test_rest_screen_draws_campfire_and_shrine_scene() -> None:
    assets = RecordingAssets()
    RestScreen(
        FakePygame(), RecordingFonts(), FakeRunner(), assets, settings=SimpleNamespace(lang="zh_CN")
    ).draw(FakeSurface())

    assert "rest_campfire" in assets.drawn
    assert "rest_shrine" in assets.drawn
