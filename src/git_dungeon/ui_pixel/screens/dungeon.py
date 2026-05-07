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
from git_dungeon.ui_pixel.text import (
    audio_label,
    key_label,
    locked_message,
    reward_feedback,
    stat_value,
    trap_feedback,
    tr,
)
from git_dungeon.ui_pixel.widgets import (
    ACCENT,
    BAD,
    BG,
    GOOD,
    MUTED,
    SURFACE_2,
    TEXT,
    Button,
    draw_action_bar,
    draw_panel,
    draw_stat_bar,
)


FLOOR_ORIGIN = (20, 62)
FLOOR_TILE = 18
FLOOR_CELL = 16

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
                from git_dungeon.ui_pixel.screens.pause import PauseScreen

                return ScreenAction.push(
                    PauseScreen(self.pygame, self.fonts, self.settings, self.audio)
                )
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
            clicked_coord = self._coord_at(self.hover_pos)
            if clicked_coord is not None:
                return self._click_coord(clicked_coord)
            button = self._enter_button()
            if button.contains(self.hover_pos) and button.enabled:
                return self._open_current()
        return None

    def draw(self, surface: Any) -> None:
        surface.fill(BG)
        lang = self._lang()
        player = self.runner.player_snapshot()
        self.fonts.draw(surface, tr("DUNGEON", lang), (12, 8), ACCENT, 22)
        self.fonts.draw_fit(surface, tr(self.message, lang), (92, 12), 202, MUTED, 13)

        draw_panel(self.pygame, surface, (10, 27, 300, 30))
        draw_stat_bar(self.pygame, surface, (20, 37, 78, 7), player.hp, player.max_hp, GOOD)
        self.fonts.draw_fit(
            surface,
            stat_value("hp", player.hp, lang, player.max_hp),
            (20, 46),
            88,
            TEXT,
            11,
        )
        draw_stat_bar(self.pygame, surface, (112, 37, 62, 7), player.mp, player.max_mp, ACCENT)
        self.fonts.draw_fit(
            surface,
            stat_value("mp", player.mp, lang, player.max_mp),
            (112, 46),
            78,
            TEXT,
            11,
        )
        self.fonts.draw_fit(
            surface, stat_value("attack", player.attack, lang), (204, 35), 76, TEXT, 12
        )
        self.fonts.draw_fit(
            surface, stat_value("gold", player.gold, lang), (204, 48), 76, ACCENT, 12
        )
        self._draw_key_status(surface)

        self._draw_floor(surface)
        audio_text = ""
        if self.audio is not None:
            audio_text = audio_label(self.audio.status().label(), lang)
        draw_action_bar(
            self.pygame,
            surface,
            self.fonts,
            audio_text or self._action_hint(),
            reserve_right=70,
            alert=bool(audio_text),
        )
        button = self._enter_button()
        button.draw(self.pygame, surface, self.fonts, button.contains(self.hover_pos))

    def _draw_floor(self, surface: Any) -> None:
        origin_x, origin_y = FLOOR_ORIGIN
        tile = FLOOR_TILE
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                tone = (28, 27, 38) if (x + y) % 2 == 0 else (24, 24, 34)
                self.pygame.draw.rect(
                    surface,
                    tone,
                    (origin_x + x * tile, origin_y + y * tile, FLOOR_CELL, FLOOR_CELL),
                )
        for left, right in self.floor.doors:
            lx, ly = left
            rx, ry = right
            x1, y1 = origin_x + lx * tile + FLOOR_CELL // 2, origin_y + ly * tile + FLOOR_CELL // 2
            x2, y2 = origin_x + rx * tile + FLOOR_CELL // 2, origin_y + ry * tile + FLOOR_CELL // 2
            self.pygame.draw.line(surface, (61, 56, 72), (x1, y1), (x2, y2), 4)
            self.pygame.draw.line(surface, MUTED, (x1, y1), (x2, y2), 1)
        for trap in self.floor.traps:
            x, y = trap.coord
            color = MUTED if self._trap_consumed(trap.trap_id) else BAD
            rect = (origin_x + x * tile + 3, origin_y + y * tile + 3, 10, 10)
            self.pygame.draw.rect(surface, (45, 28, 38), rect)
            self.pygame.draw.polygon(
                surface,
                color,
                [
                    (rect[0] + 1, rect[1] + 9),
                    (rect[0] + 3, rect[1] + 3),
                    (rect[0] + 5, rect[1] + 9),
                    (rect[0] + 7, rect[1] + 3),
                    (rect[0] + 9, rect[1] + 9),
                ],
                1,
            )
        for reward in self.floor.reward_rooms:
            x, y = reward.coord
            rect = (origin_x + x * tile, origin_y + y * tile, FLOOR_CELL, FLOOR_CELL)
            border = self._reward_border(reward)
            fill = (34, 35, 44) if self._reward_claimed(reward.reward_id) else SURFACE_2
            self.pygame.draw.rect(surface, fill, rect)
            self.pygame.draw.rect(surface, border, rect, 1)
            self._draw_reward_icon(surface, reward, rect)
        for room in self.floor.rooms:
            x, y = room.coord
            rect = (origin_x + x * tile, origin_y + y * tile, FLOOR_CELL, FLOOR_CELL)
            border = ACCENT if room.is_current else MUTED if room.is_visited else (87, 82, 99)
            self.pygame.draw.rect(surface, SURFACE_2, rect)
            self.pygame.draw.rect(surface, border, rect, 1)
            if room.is_current:
                self.pygame.draw.rect(
                    surface, ACCENT, (rect[0] + 2, rect[1] + 2, rect[2] - 4, rect[3] - 4), 1
                )
            if room.is_visited:
                self.pygame.draw.line(
                    surface,
                    GOOD,
                    (rect[0] + 3, rect[1] + rect[3] - 4),
                    (rect[0] + 7, rect[1] + rect[3] - 1),
                    1,
                )
            self.assets.draw(
                surface,
                NODE_SPRITES.get(room.kind, "node_event"),
                (rect[0] + 3, rect[1] + 3, 10, 10),
            )
        if self.player_coord is not None:
            px, py = self.player_coord
            rect = (origin_x + px * tile, origin_y + py * tile, FLOOR_CELL, FLOOR_CELL)
            self.pygame.draw.rect(surface, TEXT, (rect[0] + 5, rect[1] + 11, 6, 3))
            self.assets.draw(surface, "player_default", (rect[0] + 3, rect[1] + 4, 10, 10))
            self.pygame.draw.rect(surface, TEXT, rect, 1)

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
            self.message = locked_message(reward.requires_key, self._lang())
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
            self.message = trap_feedback(0, self._lang())
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
        self.message = trap_feedback(result.damage, self._lang())
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
                    return locked_message(reward.requires_key, self._lang())
                return "Press Enter to claim"
        return (
            "Move to the current room"
            if not self._can_enter_current_room()
            else "Press Enter to enter"
        )

    def _initial_player_coord(self) -> Coord | None:
        stored = getattr(self.runner, "dungeon_player_coord", None)
        if stored is not None and self.floor.room_at(stored) is not None:
            return stored
        self.runner.dungeon_player_coord = self.floor.start_coord
        return self.floor.start_coord

    def _enter_button(self) -> Button:
        label = self._primary_button_label()
        enabled = self._can_enter_current_room() or self._claimable_reward() is not None
        return Button((238, 157, 58, 16), label, enabled=enabled)

    def _can_enter_current_room(self) -> bool:
        current = self.runner.current_node_snapshot()
        return bool(
            current and current.is_playable_now and self.player_coord == self.floor.current_coord
        )

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
                BattleScreen(
                    self.pygame, self.fonts, self.runner, self.assets, self.audio, self.settings
                )
            )
        if current.kind.value == "event":
            from git_dungeon.ui_pixel.screens.event import EventScreen

            return ScreenAction.replace(
                EventScreen(
                    self.pygame, self.fonts, self.runner, self.assets, self.audio, self.settings
                )
            )
        if current.kind.value == "rest":
            from git_dungeon.ui_pixel.screens.rest import RestScreen

            return ScreenAction.replace(
                RestScreen(
                    self.pygame, self.fonts, self.runner, self.assets, self.audio, self.settings
                )
            )
        if current.kind.value == "shop":
            from git_dungeon.ui_pixel.screens.shop import ShopScreen

            return ScreenAction.replace(
                ShopScreen(
                    self.pygame, self.fonts, self.runner, self.assets, self.audio, self.settings
                )
            )
        self.message = f"{current.kind.value.title()} is not playable yet"
        return None

    def _claimable_reward(self) -> Any | None:
        if self.player_coord is None:
            return None
        return self.floor.reward_at(self.player_coord)

    def _claim_reward(self, reward: DungeonRewardRoom) -> None:
        if not self._reward_unlocked(reward):
            self.message = locked_message(reward.requires_key, self._lang())
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
            self.message = (
                f"{tr('Key found', self._lang())}: {key_label(result.key_id, self._lang())}"
            )
        else:
            self.message = reward_feedback(reward.label, result.heal, result.gold, self._lang())
        if self.audio is not None:
            self.audio.play_sfx("economy")

    def _lang(self) -> str:
        return getattr(self.settings, "lang", "en")

    def _draw_key_status(self, surface: Any) -> None:
        if not any(reward.grants_key or reward.requires_key for reward in self.floor.reward_rooms):
            return
        has_key = getattr(self.runner, "has_dungeon_key", lambda key_id: False)
        color = ACCENT if has_key("iron_key") else MUTED
        self.pygame.draw.rect(surface, (43, 39, 52), (282, 36, 14, 14))
        self.pygame.draw.circle(surface, color, (286, 43), 3, 1)
        self.pygame.draw.line(surface, color, (289, 43), (294, 43), 1)
        self.pygame.draw.line(surface, color, (292, 43), (292, 46), 1)

    def _draw_reward_icon(
        self, surface: Any, reward: DungeonRewardRoom, rect: tuple[int, int, int, int]
    ) -> None:
        claimed = self._reward_claimed(reward.reward_id)
        color = MUTED if claimed else self._reward_border(reward)
        if reward.grants_key:
            self.pygame.draw.circle(surface, color, (rect[0] + 6, rect[1] + 8), 3, 1)
            self.pygame.draw.line(
                surface, color, (rect[0] + 9, rect[1] + 8), (rect[0] + 13, rect[1] + 8), 1
            )
            self.pygame.draw.line(
                surface, color, (rect[0] + 12, rect[1] + 8), (rect[0] + 12, rect[1] + 11), 1
            )
            return
        if reward.requires_key:
            self.pygame.draw.rect(surface, color, (rect[0] + 4, rect[1] + 7, 8, 6), 1)
            self.pygame.draw.arc(surface, color, (rect[0] + 5, rect[1] + 3, 6, 8), 3.14, 6.28, 1)
            return
        lid_y = rect[1] + (8 if claimed else 5)
        self.pygame.draw.rect(surface, color, (rect[0] + 4, rect[1] + 8, 8, 5), 1)
        self.pygame.draw.line(surface, color, (rect[0] + 5, lid_y), (rect[0] + 11, lid_y), 1)

    def _coord_at(self, pos: tuple[int, int] | None) -> Coord | None:
        if pos is None:
            return None
        origin_x, origin_y = FLOOR_ORIGIN
        x, y = pos
        rel_x = x - origin_x
        rel_y = y - origin_y
        if rel_x < 0 or rel_y < 0:
            return None
        grid_x = rel_x // FLOOR_TILE
        grid_y = rel_y // FLOOR_TILE
        if 0 <= grid_x < GRID_WIDTH and 0 <= grid_y < GRID_HEIGHT:
            return (int(grid_x), int(grid_y))
        return None

    def _click_coord(self, coord: Coord) -> ScreenAction | None:
        if self.player_coord is None:
            self.message = "No current room"
            return None
        if coord == self.player_coord:
            self.message = self._room_message()
            return None
        if abs(coord[0] - self.player_coord[0]) + abs(coord[1] - self.player_coord[1]) == 1:
            return self._move((coord[0] - self.player_coord[0], coord[1] - self.player_coord[1]))
        if self.floor.trap_at(coord) is not None:
            trap = self.floor.trap_at(coord)
            assert trap is not None
            self.message = trap_feedback(trap.damage, self._lang())
            return None
        reward = self.floor.reward_at(coord)
        if reward is not None:
            if not self._reward_unlocked(reward):
                self.message = locked_message(reward.requires_key, self._lang())
            elif self._reward_claimed(reward.reward_id):
                self.message = tr(f"{reward.label} already claimed", self._lang())
            else:
                self.message = tr(reward.label, self._lang())
            return None
        room = self.floor.room_at(coord)
        if room is not None:
            self.message = tr("Selected room is too far", self._lang())
            return None
        self.message = "No room there"
        return None

    def _primary_button_label(self) -> str:
        if self._claimable_reward() is not None:
            return tr("Claim", self._lang())
        if self._can_enter_current_room():
            return tr("Enter Room", self._lang())
        return tr("Move", self._lang())

    def _action_hint(self) -> str:
        lang = self._lang()
        reward = self._claimable_reward()
        if reward is not None:
            if not self._reward_unlocked(reward):
                return locked_message(reward.requires_key, lang)
            if self._reward_claimed(reward.reward_id):
                return tr(f"{reward.label} already claimed", lang)
            return tr("Confirm: claim reward", lang)
        if self._can_enter_current_room():
            return tr("Confirm: enter current room", lang)
        return tr("Move to the glowing room", lang)
