#!/usr/bin/env python3
"""Render deterministic pixel UI screenshots for visual regression review."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from git_dungeon.ui_pixel.app import LOGICAL_SIZE, PixelFont
from git_dungeon.ui_pixel.assets import SpriteCatalog
from git_dungeon.ui_pixel.game_runner import ChapterSummarySnapshot, NodeSnapshot, PlayerSnapshot, RunLogEntry
from git_dungeon.ui_pixel.screens.battle import BattleScreen
from git_dungeon.ui_pixel.screens.dungeon import DungeonScreen
from git_dungeon.ui_pixel.screens.event import EventScreen
from git_dungeon.ui_pixel.screens.pause import PauseScreen
from git_dungeon.ui_pixel.screens.rest import RestScreen
from git_dungeon.ui_pixel.screens.settings import SettingsScreen
from git_dungeon.ui_pixel.screens.shop import ShopScreen
from git_dungeon.ui_pixel.screens.title import LoadingScreen, TitleScreen
from git_dungeon.ui_pixel.screens.tutorial import TutorialScreen
from git_dungeon.ui_pixel.settings import PixelSettings

LANGUAGES = ("en", "zh_CN")
SCREEN_ORDER = (
    "title",
    "loading",
    "tutorial",
    "dungeon",
    "battle",
    "event",
    "shop",
    "rest",
    "pause",
    "settings",
)


class DemoRunner:
    def __init__(self) -> None:
        self.dungeon_player_coord: tuple[int, int] | None = None
        self.saved_settings: PixelSettings | None = None
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

    def load_repository(self) -> Any:
        return SimpleNamespace()

    def is_dungeon_reward_claimed(self, _reward_id: str) -> bool:
        return False

    def has_dungeon_key(self, _key_id: str) -> bool:
        return True

    def is_dungeon_trap_consumed(self, _trap_id: str) -> bool:
        return False

    def start_current_battle(self) -> Any:
        enemy = SimpleNamespace(
            name="Merge Conflict",
            hp=40,
            max_hp=40,
            attack=8,
            is_boss=False,
            is_elite=False,
            phase="",
        )
        return SimpleNamespace(
            player=SimpleNamespace(hp=80, max_hp=100, mp=30, max_mp=50),
            enemy=enemy,
            turn=1,
            can_escape=True,
            skill_cost=10,
            message="Battle started",
        )

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

    def recent_run_events(self, _limit: int = 4) -> tuple[RunLogEntry, ...]:
        return (
            RunLogEntry("battle", "Battle won"),
            RunLogEntry("trap", "Trap hit: -8 HP"),
            RunLogEntry("reward", "Reward claimed"),
        )

    def chapter_summary_snapshot(self) -> ChapterSummarySnapshot:
        return ChapterSummarySnapshot("Demo", 2, 5, 80, 100, 60)


class DemoStore:
    def save(self, _settings: PixelSettings) -> None:
        return None


def _build_screens(pygame: Any, fonts: PixelFont, assets: SpriteCatalog, lang: str) -> dict[str, Any]:
    settings = PixelSettings(lang=lang).normalized()
    runner = DemoRunner()
    return {
        "title": TitleScreen(pygame, fonts, runner, assets, settings=settings),
        "loading": LoadingScreen(
            pygame,
            fonts,
            runner,
            assets,
            settings=settings,
            settings_store=DemoStore(),
        ),
        "tutorial": TutorialScreen(
            pygame,
            fonts,
            runner,
            assets,
            settings=settings,
            settings_store=DemoStore(),
        ),
        "dungeon": DungeonScreen(pygame, fonts, runner, assets, settings=settings),
        "battle": BattleScreen(pygame, fonts, runner, assets, settings=settings),
        "event": EventScreen(pygame, fonts, runner, assets, settings=settings),
        "shop": ShopScreen(pygame, fonts, runner, assets, settings=settings),
        "rest": RestScreen(pygame, fonts, runner, assets, settings=settings),
        "pause": PauseScreen(
            pygame,
            fonts,
            settings,
            runner=runner,
            assets=assets,
            settings_store=DemoStore(),
        ),
        "settings": SettingsScreen(pygame, fonts, settings, DemoStore()),
    }


def render(out_dir: Path, *, scale: int = 4) -> list[dict[str, Any]]:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    import pygame

    pygame.init()
    manifest: list[dict[str, Any]] = []
    try:
        pygame.display.set_mode((1, 1))
        assets = SpriteCatalog(pygame)
        assets.load()
        out_dir.mkdir(parents=True, exist_ok=True)
        for lang in LANGUAGES:
            fonts = PixelFont(pygame, lang)
            screens = _build_screens(pygame, fonts, assets, lang)
            for name in SCREEN_ORDER:
                surface = pygame.Surface(LOGICAL_SIZE)
                screen = screens[name]
                screen.update(0.25)
                screen.draw(surface)
                target = out_dir / f"{lang}-{name}.png"
                scaled = pygame.transform.scale(
                    surface,
                    (LOGICAL_SIZE[0] * scale, LOGICAL_SIZE[1] * scale),
                )
                pygame.image.save(scaled, str(target))
                manifest.append(
                    {
                        "lang": lang,
                        "screen": name,
                        "path": str(target),
                        "size": [LOGICAL_SIZE[0] * scale, LOGICAL_SIZE[1] * scale],
                    }
                )
        (out_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    finally:
        pygame.quit()
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--scale", type=int, default=4)
    args = parser.parse_args()
    manifest = render(args.out_dir, scale=args.scale)
    print(f"rendered {len(manifest)} screenshots to {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
