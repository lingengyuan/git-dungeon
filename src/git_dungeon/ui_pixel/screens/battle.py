"""Battle and boss combat screen."""

from __future__ import annotations

from typing import Any

from git_dungeon.engine.auto_policy import ACTION_ATTACK, ACTION_DEFEND, ACTION_ESCAPE, ACTION_SKILL
from git_dungeon.ui_pixel.screens.base import Screen, ScreenAction
from git_dungeon.ui_pixel.screens.game_over import GameOverScreen
from git_dungeon.ui_pixel.screens.map import MapScreen
from git_dungeon.ui_pixel.widgets import (
    ACCENT,
    BAD,
    BG,
    GOOD,
    MUTED,
    TEXT,
    Button,
    draw_panel,
    draw_stat_bar,
)


class BattleScreen(Screen):
    def __init__(self, pygame_module: Any, fonts: Any, runner: Any, assets: Any) -> None:
        self.pygame = pygame_module
        self.fonts = fonts
        self.runner = runner
        self.assets = assets
        self.hover_pos: tuple[int, int] | None = None
        self.snapshot = runner.start_current_battle()
        self.message = self.snapshot.message
        self.flash_timer = 0.0

    def handle(self, event: Any) -> ScreenAction | None:
        if event.type == self.pygame.KEYDOWN:
            if event.key in (self.pygame.K_1, self.pygame.K_a):
                return self._act(ACTION_ATTACK)
            if event.key in (self.pygame.K_2, self.pygame.K_d):
                return self._act(ACTION_DEFEND)
            if event.key in (self.pygame.K_3, self.pygame.K_s):
                return self._act(ACTION_SKILL)
            if event.key in (self.pygame.K_4, self.pygame.K_e):
                return self._act(ACTION_ESCAPE)
        if event.type == self.pygame.MOUSEMOTION:
            self.hover_pos = getattr(event, "logical_pos", None)
        if event.type == self.pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.hover_pos = getattr(event, "logical_pos", None)
            for action, button in self._buttons().items():
                if button.contains(self.hover_pos) and button.enabled:
                    return self._act(action)
        return None

    def update(self, dt: float) -> ScreenAction | None:
        self.flash_timer = max(0.0, self.flash_timer - dt)
        return None

    def draw(self, surface: Any) -> None:
        surface.fill(BG)
        snap = self.snapshot
        title = "BOSS" if snap.enemy.is_boss else "ELITE" if snap.enemy.is_elite else "BATTLE"
        draw_panel(self.pygame, surface, (10, 10, 300, 158), border=BAD if snap.enemy.is_boss else ACCENT)
        self.fonts.draw(surface, title, (22, 20), BAD if snap.enemy.is_boss else ACCENT, 22)
        self.fonts.draw(surface, f"Turn {snap.turn}", (244, 24), MUTED, 14)

        self.assets.draw(surface, "player_default", (42, 76, 32, 32))
        self.assets.draw(surface, "enemy_default", (238, 66, 32, 32))
        if self.flash_timer > 0:
            self.pygame.draw.rect(surface, BAD, (236, 64, 36, 36), 1)

        self.fonts.draw(surface, "Developer", (28, 48), TEXT, 15)
        draw_stat_bar(self.pygame, surface, (28, 62, 92, 8), snap.player.hp, snap.player.max_hp, GOOD)
        self.fonts.draw(surface, f"HP {snap.player.hp}/{snap.player.max_hp}", (28, 112), TEXT, 13)
        self.fonts.draw(surface, f"MP {snap.player.mp}/{snap.player.max_mp}", (28, 126), ACCENT, 13)

        enemy_name = snap.enemy.name[:24]
        self.fonts.draw(surface, enemy_name, (184, 48), TEXT, 15)
        draw_stat_bar(self.pygame, surface, (184, 62, 92, 8), snap.enemy.hp, snap.enemy.max_hp, BAD)
        self.fonts.draw(surface, f"HP {snap.enemy.hp}/{snap.enemy.max_hp}", (184, 102), TEXT, 13)
        self.fonts.draw(surface, f"ATK {snap.enemy.attack}", (184, 116), MUTED, 13)
        if snap.enemy.phase:
            self.fonts.draw(surface, snap.enemy.phase[:16], (184, 130), BAD, 13)

        for button in self._buttons().values():
            button.draw(self.pygame, surface, self.fonts, button.contains(self.hover_pos))
        self.fonts.draw(surface, self.message[:38], (22, 150), BAD if "Need" in self.message else TEXT, 13)

    def _buttons(self) -> dict[str, Button]:
        snap = self.snapshot
        can_skill = snap.player.mp >= snap.skill_cost
        return {
            ACTION_ATTACK: Button((18, 132, 54, 16), "Attack"),
            ACTION_DEFEND: Button((78, 132, 54, 16), "Defend"),
            ACTION_SKILL: Button(
                (138, 132, 54, 16),
                "Skill",
                enabled=can_skill,
                tooltip=f"Need {snap.skill_cost} MP",
            ),
            ACTION_ESCAPE: Button((198, 132, 54, 16), "Escape", enabled=snap.can_escape),
        }

    def _act(self, action: str) -> ScreenAction | None:
        if action == ACTION_ESCAPE and not self.snapshot.can_escape:
            self.message = "Cannot escape from Boss battle"
            return None
        if action == ACTION_SKILL and self.snapshot.player.mp < self.snapshot.skill_cost:
            self.message = f"Need {self.snapshot.skill_cost} MP"
            return None
        result, snapshot = self.runner.resolve_battle_action(action)
        self.snapshot = snapshot
        self.message = _message_for_result(result, snapshot)
        if result.player_damage > 0 or result.critical:
            self.flash_timer = 0.18
        if result.battle_over:
            reward = self.runner.last_reward_snapshot()
            if result.player_defeated:
                return ScreenAction.replace(
                    GameOverScreen(self.pygame, self.fonts, self.runner, self.assets, won=False)
                )
            if result.won:
                reward_text = ""
                if reward is not None:
                    reward_text = f" +{reward.exp} EXP +{reward.gold} Gold"
                return ScreenAction.replace(
                    MapScreen(
                        self.pygame,
                        self.fonts,
                        self.runner,
                        self.assets,
                        message=f"Won battle.{reward_text}",
                    )
                )
            if result.escaped:
                return ScreenAction.replace(
                    MapScreen(self.pygame, self.fonts, self.runner, self.assets, message="Escaped battle")
                )
        return None


def _message_for_result(result: Any, snapshot: Any) -> str:
    if not result.accepted:
        return str(result.message)
    parts: list[str] = []
    if result.player_damage:
        parts.append(f"Dealt {result.player_damage}")
    if result.enemy_damage:
        parts.append(f"Took {result.enemy_damage}")
    if result.critical:
        parts.append("Critical")
    if result.defended:
        parts.append("Defended")
    if result.escaped:
        parts.append("Escaped")
    if not parts:
        parts.append(snapshot.message)
    return " / ".join(parts)
