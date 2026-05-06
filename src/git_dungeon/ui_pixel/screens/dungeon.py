"""Room-by-room dungeon exploration screen."""

from __future__ import annotations

from typing import Any

from git_dungeon.ui_pixel.dungeon import (
    GRID_HEIGHT,
    GRID_WIDTH,
    Coord,
    DungeonFloor,
    DungeonRewardRoom,
    build_dungeon_floor,
)
from git_dungeon.ui_pixel.screens.base import Screen, ScreenAction
from git_dungeon.ui_pixel.text import audio_label, tr
from git_dungeon.ui_pixel.widgets import (
    ACCENT,
    BAD,
    BG,
    GOOD,
    MUTED,
    SURFACE_2,
    TEXT,
    Button,
    draw_panel,
    draw_stat_bar,
)


NODE_SPRITES = {
    "battle": "node_battle",
    "event": "node_event",
    "rest": "node_rest",
    "shop": "node_shop",
    "elite": "node_elite",
    "boss": "node_boss",
}


class DungeonScreen(Screen):
    def __init__(
        self,
        pygame_module: Any,
        fonts: Any,
        runner: Any,
        assets: Any,
        message: str = "Move to the current room",
        audio: Any | None = None,
        settings: Any | None = None,
    ) -> None:
        self.pygame = pygame_module
        self.fonts = fonts
        self.runner = runner
        self.assets = assets
        self.audio = audio
        self.settings = settings
        self.hover_pos: tuple[int, int] | None = None
        self.floor: DungeonFloor = build_dungeon_floor(self.runner.route_nodes())
        self.player_coord: Coord | None = self._initial_player_coord()
        self.message = message
        if self._can_enter_current_room():
            self.message = "Press Enter to enter"

    def enter(self) -> None:
        if self.audio is not None:
            self.audio.play_bgm("chapter")

    def handle(self, event: Any) -> ScreenAction | None:
        if event.type == self.pygame.KEYDOWN:
            if event.key in (self.pygame.K_ESCAPE, self.pygame.K_q):
                return ScreenAction.quit()
            if event.key in (self.pygame.K_RETURN, self.pygame.K_SPACE):
                return self._open_current()
            move = {
                self.pygame.K_LEFT: (-1, 0),
                self.pygame.K_a: (-1, 0),
                self.pygame.K_RIGHT: (1, 0),
                self.pygame.K_d: (1, 0),
                self.pygame.K_UP: (0, -1),
                self.pygame.K_w: (0, -1),
                self.pygame.K_DOWN: (0, 1),
                self.pygame.K_s: (0, 1),
            }.get(event.key)
            if move:
                return self._move(move)
        if event.type == self.pygame.MOUSEMOTION:
            self.hover_pos = getattr(event, "logical_pos", None)
        if event.type == self.pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.hover_pos = getattr(event, "logical_pos", None)
            button = self._enter_button()
            if button.contains(self.hover_pos) and button.enabled:
                return self._open_current()
        return None

    def draw(self, surface: Any) -> None:
        surface.fill(BG)
        lang = self._lang()
        player = self.runner.player_snapshot()
        self.fonts.draw(surface, tr("DUNGEON", lang), (12, 8), ACCENT, 22)
        self.fonts.draw_fit(surface, tr(self.message, lang), (96, 12), 190, MUTED, 14)

        draw_panel(self.pygame, surface, (10, 28, 300, 36))
        draw_stat_bar(self.pygame, surface, (20, 40, 92, 8), player.hp, player.max_hp, GOOD)
        self.fonts.draw(surface, f"HP {player.hp}/{player.max_hp}", (20, 50), TEXT, 12)
        draw_stat_bar(self.pygame, surface, (122, 40, 70, 8), player.mp, player.max_mp, ACCENT)
        self.fonts.draw(surface, f"MP {player.mp}/{player.max_mp}", (122, 50), TEXT, 12)
        self.fonts.draw(surface, f"ATK {player.attack}", (204, 38), TEXT, 13)
        self.fonts.draw(surface, f"{tr('Gold', lang)} {player.gold}", (204, 51), TEXT, 13)

        self._draw_floor(surface)
        button = self._enter_button()
        button.draw(self.pygame, surface, self.fonts, button.contains(self.hover_pos))
        self.fonts.draw_fit(surface, tr("Arrows/WASD: Move", lang), (18, 154), 120, MUTED, 12)
        if self.audio is not None:
            self.fonts.draw_fit(
                surface,
                audio_label(self.audio.status().label(), lang),
                (204, 154),
                92,
                MUTED,
                11,
            )

    def _draw_floor(self, surface: Any) -> None:
        origin_x, origin_y = 18, 72
        tile = 20
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                self.pygame.draw.rect(
                    surface,
                    (23, 22, 31),
                    (origin_x + x * tile, origin_y + y * tile, 18, 18),
                )
        for left, right in self.floor.doors:
            lx, ly = left
            rx, ry = right
            x1, y1 = origin_x + lx * tile + 9, origin_y + ly * tile + 9
            x2, y2 = origin_x + rx * tile + 9, origin_y + ry * tile + 9
            self.pygame.draw.line(surface, MUTED, (x1, y1), (x2, y2), 2)
        for trap in self.floor.traps:
            x, y = trap.coord
            color = MUTED if self._trap_consumed(trap.trap_id) else BAD
            self.pygame.draw.rect(
                surface,
                color,
                (origin_x + x * tile + 5, origin_y + y * tile + 5, 8, 8),
                1,
            )
        for reward in self.floor.reward_rooms:
            x, y = reward.coord
            rect = (origin_x + x * tile, origin_y + y * tile, 18, 18)
            border = self._reward_border(reward)
            self.pygame.draw.rect(surface, SURFACE_2, rect)
            self.pygame.draw.rect(surface, border, rect, 1)
            self.assets.draw(surface, "node_shop", (rect[0] + 3, rect[1] + 3, 12, 12))
        for room in self.floor.rooms:
            x, y = room.coord
            rect = (origin_x + x * tile, origin_y + y * tile, 18, 18)
            border = ACCENT if room.is_current else GOOD if room.is_visited else MUTED
            self.pygame.draw.rect(surface, SURFACE_2, rect)
            self.pygame.draw.rect(surface, border, rect, 1)
            self.assets.draw(
                surface,
                NODE_SPRITES.get(room.kind, "node_event"),
                (rect[0] + 3, rect[1] + 3, 12, 12),
            )
        if self.player_coord is not None:
            px, py = self.player_coord
            self.assets.draw(
                surface,
                "player_default",
                (origin_x + px * tile + 1, origin_y + py * tile + 1, 16, 16),
            )

    def _move(self, delta: tuple[int, int]) -> ScreenAction | None:
        if self.player_coord is None:
            self.message = "No current room"
            return None
        target = (self.player_coord[0] + delta[0], self.player_coord[1] + delta[1])
        trap = self.floor.trap_at(target)
        if trap is not None:
            action = self._trigger_trap(trap.trap_id, trap.damage)
            if self.audio is not None:
                self.audio.play_sfx("combat_hurt")
            return action
        reward = self.floor.reward_at(target)
        if reward is not None and not self._reward_unlocked(reward):
            self.message = f"Locked: need {reward.requires_key}"
            if self.audio is not None:
                self.audio.play_sfx("ui_denied")
            return None
        if self.floor.room_at(target) is None or not self.floor.has_door(self.player_coord, target):
            self.message = "No door there"
            if self.audio is not None:
                self.audio.play_sfx("ui_denied")
            return None
        self.player_coord = target
        self.runner.dungeon_player_coord = target
        self.message = self._room_message()
        return None

    def _trigger_trap(self, trap_id: str, damage: int) -> ScreenAction | None:
        trigger = getattr(self.runner, "trigger_dungeon_trap", None)
        if trigger is None:
            self.message = "Trap blocks this path"
            return None
        result = trigger(trap_id, damage)
        if result.already_triggered:
            self.message = "Trap already spent"
            return None
        if result.damage <= 0:
            self.message = "Trap hit: no HP lost"
            return None
        player = self.runner.player_snapshot()
        if player.hp <= 0:
            from git_dungeon.ui_pixel.screens.game_over import GameOverScreen

            return ScreenAction.replace(
                GameOverScreen(
                    self.pygame,
                    self.fonts,
                    self.runner,
                    self.assets,
                    won=False,
                    message="Trap defeated you",
                    audio=self.audio,
                    settings=self.settings,
                )
            )
        self.message = f"Trap hit: -{result.damage} HP"
        return None

    def _trap_consumed(self, trap_id: str) -> bool:
        checker = getattr(self.runner, "is_dungeon_trap_consumed", None)
        if checker is None:
            return False
        return bool(checker(trap_id))

    def _reward_claimed(self, reward_id: str) -> bool:
        checker = getattr(self.runner, "is_dungeon_reward_claimed", None)
        if checker is None:
            return False
        return bool(checker(reward_id))

    def _reward_unlocked(self, reward: DungeonRewardRoom) -> bool:
        if reward.requires_key is None:
            return True
        checker = getattr(self.runner, "has_dungeon_key", None)
        if checker is None:
            return False
        return bool(checker(reward.requires_key))

    def _reward_border(self, reward: DungeonRewardRoom) -> tuple[int, int, int]:
        if self._reward_claimed(reward.reward_id):
            return GOOD
        if not self._reward_unlocked(reward):
            return BAD
        return ACCENT

    def _room_message(self) -> str:
        if self.player_coord is not None:
            reward = self.floor.reward_at(self.player_coord)
            if reward is not None:
                if self._reward_claimed(reward.reward_id):
                    return f"{reward.label} already claimed"
                if not self._reward_unlocked(reward):
                    return f"Locked: need {reward.requires_key}"
                return "Press Enter to claim"
        return "Move to the current room" if not self._can_enter_current_room() else "Press Enter to enter"

    def _initial_player_coord(self) -> Coord | None:
        stored = getattr(self.runner, "dungeon_player_coord", None)
        if stored is not None and self.floor.room_at(stored) is not None:
            return stored
        self.runner.dungeon_player_coord = self.floor.start_coord
        return self.floor.start_coord

    def _enter_button(self) -> Button:
        label = tr("Enter Room", self._lang())
        enabled = self._can_enter_current_room() or self._claimable_reward() is not None
        return Button((144, 150, 56, 18), label, enabled=enabled)

    def _can_enter_current_room(self) -> bool:
        current = self.runner.current_node_snapshot()
        return bool(current and current.is_playable_now and self.player_coord == self.floor.current_coord)

    def _open_current(self) -> ScreenAction | None:
        reward = self._claimable_reward()
        if reward is not None:
            self._claim_reward(reward)
            return None
        if not self._can_enter_current_room():
            self.message = "Move to the current room"
            if self.audio is not None:
                self.audio.play_sfx("ui_denied")
            return None
        current = self.runner.current_node()
        if current is None:
            self.message = "No current room"
            return None
        if self.audio is not None:
            self.audio.play_sfx("ui_confirm")
        if current.kind.value in {"battle", "elite", "boss"}:
            from git_dungeon.ui_pixel.screens.battle import BattleScreen

            return ScreenAction.replace(
                BattleScreen(self.pygame, self.fonts, self.runner, self.assets, self.audio, self.settings)
            )
        if current.kind.value == "event":
            from git_dungeon.ui_pixel.screens.event import EventScreen

            return ScreenAction.replace(
                EventScreen(self.pygame, self.fonts, self.runner, self.assets, self.audio, self.settings)
            )
        if current.kind.value == "rest":
            from git_dungeon.ui_pixel.screens.rest import RestScreen

            return ScreenAction.replace(
                RestScreen(self.pygame, self.fonts, self.runner, self.assets, self.audio, self.settings)
            )
        if current.kind.value == "shop":
            from git_dungeon.ui_pixel.screens.shop import ShopScreen

            return ScreenAction.replace(
                ShopScreen(self.pygame, self.fonts, self.runner, self.assets, self.audio, self.settings)
            )
        self.message = f"{current.kind.value.title()} is not playable yet"
        return None

    def _claimable_reward(self) -> Any | None:
        if self.player_coord is None:
            return None
        return self.floor.reward_at(self.player_coord)

    def _claim_reward(self, reward: DungeonRewardRoom) -> None:
        if not self._reward_unlocked(reward):
            self.message = f"Locked: need {reward.requires_key}"
            if self.audio is not None:
                self.audio.play_sfx("ui_denied")
            return
        claim = getattr(self.runner, "claim_dungeon_reward", None)
        if claim is None:
            self.message = f"{reward.label} unavailable"
            return
        result = claim(reward.reward_id, reward.heal, reward.gold, reward.grants_key)
        if result.already_claimed:
            self.message = f"{reward.label} already claimed"
            if self.audio is not None:
                self.audio.play_sfx("ui_denied")
            return
        if getattr(result, "key_id", None):
            self.message = f"Key found: {result.key_id}"
        else:
            self.message = f"{reward.label}: +{result.heal} HP +{result.gold} Gold"
        if self.audio is not None:
            self.audio.play_sfx("economy")

    def _lang(self) -> str:
        return getattr(self.settings, "lang", "en")
