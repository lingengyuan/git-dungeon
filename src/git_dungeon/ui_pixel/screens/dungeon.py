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
    stat_delta,
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
    TEXT,
    Button,
    draw_action_bar,
    draw_panel,
    draw_stat_bar,
)


FLOOR_ORIGIN = (20, 62)
FLOOR_TILE = 18
FLOOR_CELL = 16
DOOR_GAP = 4

NODE_SPRITES = {
    "battle": "node_battle",
    "event": "node_event",
    "rest": "node_rest",
    "shop": "node_shop",
    "elite": "ci_sentinel",
    "boss": "release_gate",
}

TILE_WALL_SPRITE = "tile_wall_stone"
TILE_FLOOR_SPRITE = "tile_floor_stone"
TILE_CORRIDOR_SPRITE = "tile_corridor"
DOOR_OPEN_SPRITE = "branch_door"
CHEST_CLOSED_SPRITE = "commit_shard"
CHEST_OPEN_SPRITE = "chest_open"
TRAP_ARMED_SPRITE = "merge_conflict_trap"
TRAP_SPENT_SPRITE = "trap_spikes_spent"
KEY_IRON_SPRITE = "key_iron"
VAULT_LOCKED_SPRITE = "vault_locked"
VAULT_OPEN_SPRITE = "vault_open"
ROOM_MARKER_CURRENT_SPRITE = "room_marker_current"
ROOM_MARKER_AVAILABLE_SPRITE = "room_marker_available"
BOSS_GATE_SPRITE = "release_gate"
CHAPTER_ACCENTS = (
    ACCENT,
    (95, 210, 167),
    (98, 181, 230),
    (213, 126, 104),
)


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
        settings_store: Any | None = None,
        settings_error: str = "",
        apply_display_mode: Any | None = None,
    ) -> None:
        self.pygame = pygame_module
        self.fonts = fonts
        self.runner = runner
        self.assets = assets
        self.audio = audio
        self.settings = settings
        self.settings_store = settings_store
        self.settings_error = settings_error
        self.apply_display_mode = apply_display_mode
        self.hover_pos: tuple[int, int] | None = None
        self.floor: DungeonFloor = build_dungeon_floor(self.runner.route_nodes())
        self.player_coord: Coord | None = self._initial_player_coord()
        self.message = message
        self.anim_time = 0.0
        if self._can_enter_current_room():
            self.message = "Press Enter to enter"

    def enter(self) -> None:
        if self.audio is not None:
            self.audio.play_bgm("chapter")

    def update(self, dt: float) -> ScreenAction | None:
        if getattr(self.settings, "reduce_motion", False):
            return None
        self.anim_time += dt
        return None

    def handle(self, event: Any) -> ScreenAction | None:
        if event.type == self.pygame.KEYDOWN:
            if event.key in (self.pygame.K_ESCAPE, self.pygame.K_q):
                from git_dungeon.ui_pixel.screens.pause import PauseScreen

                return ScreenAction.push(
                    PauseScreen(
                        self.pygame,
                        self.fonts,
                        self.settings,
                        self.audio,
                        self.runner,
                        self.assets,
                        self.settings_store,
                        self.settings_error,
                        self.apply_display_mode,
                    )
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
        accent = self._chapter_accent()
        self.fonts.draw(surface, tr("DUNGEON", lang), (12, 8), accent, 22)
        self.fonts.draw_fit(surface, tr(self.message, lang), (92, 12), 202, MUTED, 13)

        draw_panel(self.pygame, surface, (10, 27, 300, 34), border=accent)
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
            surface, stat_value("attack", player.attack, lang), (204, 36), 76, TEXT, 11
        )
        self.fonts.draw_fit(
            surface, stat_value("gold", player.gold, lang), (204, 49), 76, ACCENT, 11
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
        accent = self._chapter_accent()
        chapter_index = self._chapter_index()
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                self.assets.draw(surface, TILE_WALL_SPRITE, self._coord_rect((x, y)))

        floor_coords = {room.coord for room in self.floor.rooms}
        floor_coords.update(reward.coord for reward in self.floor.reward_rooms)
        for coord in floor_coords:
            rect = self._coord_rect(coord)
            self.assets.draw(surface, TILE_FLOOR_SPRITE, rect)
            if (coord[0] + coord[1] + chapter_index) % 3 == 0:
                self.pygame.draw.rect(surface, accent, (rect[0] + 12, rect[1] + 12, 2, 2))

        for left, right in self.floor.doors:
            self._draw_door(surface, left, right)

        for trap in self.floor.traps:
            sprite = TRAP_SPENT_SPRITE if self._trap_consumed(trap.trap_id) else TRAP_ARMED_SPRITE
            rect = self._coord_rect(trap.coord)
            self.assets.draw(surface, sprite, rect)
            if not self._trap_consumed(trap.trap_id) and int(self.anim_time * 4) % 2:
                self.pygame.draw.rect(surface, BAD, rect, 1)

        for reward in self.floor.reward_rooms:
            rect = self._coord_rect(reward.coord)
            border = self._reward_border(reward)
            self.assets.draw(surface, self._reward_sprite(reward), rect)
            if not self._reward_claimed(reward.reward_id) and int(self.anim_time * 3) % 2:
                border = accent
            self.pygame.draw.rect(surface, border, rect, 1)

        for room in self.floor.rooms:
            rect = self._coord_rect(room.coord)
            border = ACCENT if room.is_current else MUTED if room.is_visited else (87, 82, 99)
            if room.is_current:
                self.assets.draw(surface, ROOM_MARKER_CURRENT_SPRITE, rect)
            elif room.is_playable_now:
                self.assets.draw(surface, ROOM_MARKER_AVAILABLE_SPRITE, rect)
            self.pygame.draw.rect(surface, border, rect, 1)
            if room.is_current:
                pulse = accent if int(self.anim_time * 4) % 2 else TEXT
                self.pygame.draw.rect(
                    surface, pulse, (rect[0] + 2, rect[1] + 2, rect[2] - 4, rect[3] - 4), 1
                )
            if room.is_visited:
                self.pygame.draw.line(
                    surface,
                    GOOD,
                    (rect[0] + 3, rect[1] + rect[3] - 4),
                    (rect[0] + 7, rect[1] + rect[3] - 1),
                    1,
                )
            room_sprite = BOSS_GATE_SPRITE if room.kind == "boss" else NODE_SPRITES.get(
                room.kind, "node_event"
            )
            inset = 1 if room.kind in {"boss", "elite"} else 3
            size = 14 if room.kind in {"boss", "elite"} else 10
            self.assets.draw(surface, room_sprite, (rect[0] + inset, rect[1] + inset, size, size))
        self.assets.draw(surface, "torch_lit", (14, 65, 14, 14))
        self.assets.draw(surface, "torch_lit", (292, 65, 14, 14))
        if self.player_coord is not None:
            rect = self._coord_rect(self.player_coord)
            self.pygame.draw.rect(surface, TEXT, (rect[0] + 5, rect[1] + 11, 6, 3))
            y_offset = 1 if int(self.anim_time * 5) % 2 else 0
            self.assets.draw(surface, "player_idle", (rect[0] + 3, rect[1] + 4 - y_offset, 10, 10))
            self.pygame.draw.rect(surface, TEXT, rect, 1)

    def _coord_rect(self, coord: Coord) -> tuple[int, int, int, int]:
        x, y = coord
        origin_x, origin_y = FLOOR_ORIGIN
        return (origin_x + x * FLOOR_TILE, origin_y + y * FLOOR_TILE, FLOOR_CELL, FLOOR_CELL)

    def _draw_door(self, surface: Any, left: Coord, right: Coord) -> None:
        left_rect = self._coord_rect(left)
        right_rect = self._coord_rect(right)
        if left[1] == right[1]:
            x = min(left_rect[0], right_rect[0]) + FLOOR_CELL
            y = left_rect[1] + (FLOOR_CELL - DOOR_GAP) // 2
            self.assets.draw(
                surface,
                TILE_CORRIDOR_SPRITE,
                (x, y, FLOOR_TILE - FLOOR_CELL, DOOR_GAP),
            )
            self.assets.draw(surface, DOOR_OPEN_SPRITE, (x - 5, left_rect[1] + 3, 12, 10))
            return
        x = left_rect[0] + (FLOOR_CELL - DOOR_GAP) // 2
        y = min(left_rect[1], right_rect[1]) + FLOOR_CELL
        self.assets.draw(
            surface,
            TILE_CORRIDOR_SPRITE,
            (x, y, DOOR_GAP, FLOOR_TILE - FLOOR_CELL),
        )
        self.assets.draw(surface, DOOR_OPEN_SPRITE, (left_rect[0] + 3, y - 5, 10, 12))

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
                    self.pygame,
                    self.fonts,
                    self.runner,
                    self.assets,
                    self.audio,
                    self.settings,
                    self.settings_store,
                    self.settings_error,
                    self.apply_display_mode,
                )
            )
        if current.kind.value == "event":
            from git_dungeon.ui_pixel.screens.event import EventScreen

            return ScreenAction.replace(
                EventScreen(
                    self.pygame,
                    self.fonts,
                    self.runner,
                    self.assets,
                    self.audio,
                    self.settings,
                    self.settings_store,
                    self.settings_error,
                    self.apply_display_mode,
                )
            )
        if current.kind.value == "rest":
            from git_dungeon.ui_pixel.screens.rest import RestScreen

            return ScreenAction.replace(
                RestScreen(
                    self.pygame,
                    self.fonts,
                    self.runner,
                    self.assets,
                    self.audio,
                    self.settings,
                    self.settings_store,
                    self.settings_error,
                    self.apply_display_mode,
                )
            )
        if current.kind.value == "shop":
            from git_dungeon.ui_pixel.screens.shop import ShopScreen

            return ScreenAction.replace(
                ShopScreen(
                    self.pygame,
                    self.fonts,
                    self.runner,
                    self.assets,
                    self.audio,
                    self.settings,
                    self.settings_store,
                    self.settings_error,
                    self.apply_display_mode,
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

    def _chapter_index(self) -> int:
        current_chapter = getattr(self.runner, "current_chapter", None)
        if not callable(current_chapter):
            return 0
        chapter = current_chapter()
        return int(getattr(chapter, "chapter_index", 0) or 0)

    def _chapter_accent(self) -> tuple[int, int, int]:
        if getattr(self.settings, "high_contrast", False):
            return TEXT
        return CHAPTER_ACCENTS[self._chapter_index() % len(CHAPTER_ACCENTS)]

    def _draw_key_status(self, surface: Any) -> None:
        if not any(reward.grants_key or reward.requires_key for reward in self.floor.reward_rooms):
            return
        has_key = getattr(self.runner, "has_dungeon_key", lambda key_id: False)
        color = ACCENT if has_key("iron_key") else MUTED
        self.pygame.draw.rect(surface, (43, 39, 52), (282, 36, 14, 14))
        self.pygame.draw.circle(surface, color, (286, 43), 3, 1)
        self.pygame.draw.line(surface, color, (289, 43), (294, 43), 1)
        self.pygame.draw.line(surface, color, (292, 43), (292, 46), 1)

    def _reward_sprite(self, reward: DungeonRewardRoom) -> str:
        claimed = self._reward_claimed(reward.reward_id)
        if reward.grants_key:
            return CHEST_OPEN_SPRITE if claimed else KEY_IRON_SPRITE
        if reward.requires_key:
            return VAULT_OPEN_SPRITE if claimed else VAULT_LOCKED_SPRITE
        return CHEST_OPEN_SPRITE if claimed else CHEST_CLOSED_SPRITE

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
        hovered = self._coord_at(self.hover_pos)
        if hovered is not None:
            trap = self.floor.trap_at(hovered)
            if trap is not None:
                if self._trap_consumed(trap.trap_id):
                    return tr("Trap already spent", lang)
                return f"{tr('Trap', lang)}: {stat_delta('hp', -trap.damage, lang)}"
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
