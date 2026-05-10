"""Battle and boss combat screen."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from git_dungeon.engine.auto_policy import ACTION_ATTACK, ACTION_DEFEND, ACTION_ESCAPE, ACTION_SKILL
from git_dungeon.ui_pixel.screens.base import Screen, ScreenAction
from git_dungeon.ui_pixel.screens.game_over import GameOverScreen
from git_dungeon.ui_pixel.screens.dungeon import DungeonScreen
from git_dungeon.ui_pixel.text import (
    audio_label,
    battle_reward_feedback,
    battle_reward_float,
    boss_phase_label,
    enemy_name_label,
    skill_cost_text,
    stat_value,
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
    draw_location_stage,
    draw_panel,
    draw_stat_bar,
    draw_tooltip,
)

BATTLE_PLAYER_NAME_POS = (28, 44)
BATTLE_PLAYER_BAR_RECT = (28, 64, 92, 8)
BATTLE_PLAYER_SPRITE_RECT = (42, 76, 32, 32)
BATTLE_PLAYER_HIT_RECT = (40, 74, 36, 36)
BATTLE_PLAYER_SHIELD_RECT = (36, 70, 44, 44)
BATTLE_PLAYER_HP_POS = (82, 82)
BATTLE_PLAYER_MP_POS = (82, 94)
BATTLE_ENEMY_NAME_POS = (184, 44)
BATTLE_ENEMY_BAR_RECT = (184, 64, 92, 8)
BATTLE_ENEMY_SPRITE_RECT = (256, 78, 32, 32)
BATTLE_ENEMY_HIT_RECT = (254, 76, 36, 36)
BATTLE_ENEMY_HP_POS = (184, 82)
BATTLE_ENEMY_ATTACK_POS = (184, 94)
BATTLE_ENEMY_PHASE_POS = (184, 106)
BATTLE_ENEMY_STAT_WIDTH = 66
BATTLE_BUTTON_TOP = 134
BATTLE_BUTTON_HEIGHT = 14
BATTLE_ACTION_BAR_RECT = (18, 151, 274, 15)
BATTLE_SCENE_RECT = (18, 38, 284, 88)
BATTLE_GROUND_TOP = 112

PLAYER_IDLE_SPRITE = "player_idle"
PLAYER_ATTACK_SPRITE = "player_attack"
PLAYER_DEFEND_SPRITE = "player_defend"
ENEMY_DEFAULT_SPRITE = "enemy_default_git_goblin"
FX_SLASH_SPRITE = "fx_slash"
FX_SHIELD_SPRITE = "fx_shield"
FX_REWARD_SPRITE = "fx_reward_drop"
BOSS_SPRITES = (
    "boss_fix",
    "boss_refactor",
    "boss_merge_conflict",
    "boss_ci_sentinel",
    "boss_secret_leak",
    "boss_release_gate",
)

BOSS_NAME_SPRITES = {
    "production": "boss_fix",
    "bug": "boss_fix",
    "legacy": "boss_refactor",
    "refactor": "boss_refactor",
    "merge": "boss_merge_conflict",
    "conflict": "boss_merge_conflict",
    "ci": "boss_ci_sentinel",
    "loop": "boss_ci_sentinel",
    "sentinel": "boss_ci_sentinel",
    "secret": "boss_secret_leak",
    "leak": "boss_secret_leak",
    "release": "boss_release_gate",
    "gate": "boss_release_gate",
    "tag": "boss_release_gate",
}


@dataclass
class FloatingText:
    text: str
    x: int
    y: float
    color: tuple[int, int, int]
    ttl: float = 0.7


class BattleScreen(Screen):
    def __init__(
        self,
        pygame_module: Any,
        fonts: Any,
        runner: Any,
        assets: Any,
        audio: Any | None = None,
        settings: Any | None = None,
        settings_store: Any | None = None,
        settings_error: str = "",
    ) -> None:
        self.pygame = pygame_module
        self.fonts = fonts
        self.runner = runner
        self.assets = assets
        self.audio = audio
        self.settings = settings
        self.settings_store = settings_store
        self.settings_error = settings_error
        self.hover_pos: tuple[int, int] | None = None
        self.snapshot = runner.start_current_battle()
        self.message = tr(self.snapshot.message, self._lang())
        self.enemy_flash_timer = 0.0
        self.player_flash_timer = 0.0
        self.shield_timer = 0.0
        self.critical_timer = 0.0
        self.enemy_fade_timer = 0.0
        self.player_attack_timer = 0.0
        self.floating_texts: list[FloatingText] = []
        self.pending_action: ScreenAction | None = None
        self.finish_timer = 0.0

    def enter(self) -> None:
        if self.audio is not None:
            self.audio.play_bgm("boss" if self.snapshot.enemy.is_boss else "chapter")

    def handle(self, event: Any) -> ScreenAction | None:
        if self.pending_action is not None:
            return None
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
                    )
                )
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
        self.enemy_flash_timer = max(0.0, self.enemy_flash_timer - dt)
        self.player_flash_timer = max(0.0, self.player_flash_timer - dt)
        self.shield_timer = max(0.0, self.shield_timer - dt)
        self.critical_timer = max(0.0, self.critical_timer - dt)
        self.enemy_fade_timer = max(0.0, self.enemy_fade_timer - dt)
        self.player_attack_timer = max(0.0, self.player_attack_timer - dt)
        for item in self.floating_texts:
            item.ttl -= dt
            item.y -= 18 * dt
        self.floating_texts = [item for item in self.floating_texts if item.ttl > 0]
        if self.pending_action is not None:
            self.finish_timer = max(0.0, self.finish_timer - dt)
            if self.finish_timer <= 0:
                action = self.pending_action
                self.pending_action = None
                return action
        return None

    def draw(self, surface: Any) -> None:
        surface.fill(BG)
        lang = self._lang()
        snap = self.snapshot
        title = "BOSS" if snap.enemy.is_boss else "ELITE" if snap.enemy.is_elite else "BATTLE"
        draw_panel(
            self.pygame, surface, (10, 10, 300, 158), border=BAD if snap.enemy.is_boss else ACCENT
        )
        self.fonts.draw(
            surface, tr(title, lang), (22, 20), BAD if snap.enemy.is_boss else ACCENT, 22
        )
        self.fonts.draw(surface, f"{tr('Turn', lang)} {snap.turn}", (244, 24), MUTED, 14)

        self._draw_scene(surface, snap.enemy.is_boss)
        self.assets.draw(surface, self._player_sprite_id(), BATTLE_PLAYER_SPRITE_RECT)
        enemy_alpha = 255
        if self.enemy_fade_timer > 0:
            enemy_alpha = max(70, int(255 * self.enemy_fade_timer / 0.55))
        shake = 2 if self.critical_timer > 0 and int(self.critical_timer * 30) % 2 == 0 else 0
        enemy_rect = (
            BATTLE_ENEMY_SPRITE_RECT[0] + shake,
            BATTLE_ENEMY_SPRITE_RECT[1],
            BATTLE_ENEMY_SPRITE_RECT[2],
            BATTLE_ENEMY_SPRITE_RECT[3],
        )
        self._draw_sprite(surface, self._enemy_sprite_id(snap.enemy), enemy_rect, alpha=enemy_alpha)
        self._draw_combat_fx(surface)
        if self.enemy_flash_timer > 0:
            self.pygame.draw.rect(surface, BAD, BATTLE_ENEMY_HIT_RECT, 1)
        if self.player_flash_timer > 0:
            self.pygame.draw.rect(surface, BAD, BATTLE_PLAYER_HIT_RECT, 1)
        if self.shield_timer > 0:
            self.pygame.draw.rect(surface, GOOD, BATTLE_PLAYER_SHIELD_RECT, 1)

        self.fonts.draw_fit(surface, tr("Developer", lang), BATTLE_PLAYER_NAME_POS, 94, TEXT, 13)
        draw_stat_bar(
            self.pygame, surface, BATTLE_PLAYER_BAR_RECT, snap.player.hp, snap.player.max_hp, GOOD
        )
        self.fonts.draw_fit(
            surface,
            stat_value("hp", snap.player.hp, lang, snap.player.max_hp),
            BATTLE_PLAYER_HP_POS,
            66,
            TEXT,
            10,
        )
        self.fonts.draw_fit(
            surface,
            stat_value("mp", snap.player.mp, lang, snap.player.max_mp),
            BATTLE_PLAYER_MP_POS,
            66,
            ACCENT,
            10,
        )

        enemy_name = enemy_name_label(str(snap.enemy.name), lang)[:24]
        self.fonts.draw_fit(surface, enemy_name, BATTLE_ENEMY_NAME_POS, 94, TEXT, 13)
        draw_stat_bar(
            self.pygame, surface, BATTLE_ENEMY_BAR_RECT, snap.enemy.hp, snap.enemy.max_hp, BAD
        )
        self.fonts.draw_fit(
            surface,
            stat_value("hp", snap.enemy.hp, lang, snap.enemy.max_hp),
            BATTLE_ENEMY_HP_POS,
            BATTLE_ENEMY_STAT_WIDTH,
            TEXT,
            10,
        )
        self.fonts.draw_fit(
            surface,
            stat_value("attack", snap.enemy.attack, lang),
            BATTLE_ENEMY_ATTACK_POS,
            BATTLE_ENEMY_STAT_WIDTH,
            MUTED,
            10,
        )
        if snap.enemy.phase:
            self.fonts.draw_fit(
                surface,
                boss_phase_label(str(snap.enemy.phase), lang),
                BATTLE_ENEMY_PHASE_POS,
                BATTLE_ENEMY_STAT_WIDTH,
                BAD,
                10,
            )

        for item in self.floating_texts:
            alpha_color = item.color if item.ttl > 0.2 else MUTED
            self.fonts.draw(surface, item.text, (item.x, int(item.y)), alpha_color, 15)

        for button in self._buttons().values():
            button.draw(self.pygame, surface, self.fonts, button.contains(self.hover_pos))
        label = ""
        if self.audio is not None:
            label = audio_label(self.audio.status().label(), lang)
        draw_action_bar(
            self.pygame,
            surface,
            self.fonts,
            self.message,
            rect=BATTLE_ACTION_BAR_RECT,
            right_text=label,
            alert=self.message.startswith(tr("Need", lang)),
        )
        self._draw_tooltip(surface)

    def _buttons(self) -> dict[str, Button]:
        snap = self.snapshot
        can_skill = snap.player.mp >= snap.skill_cost
        return {
            ACTION_ATTACK: Button(
                (18, BATTLE_BUTTON_TOP, 54, BATTLE_BUTTON_HEIGHT), tr("Attack", self._lang())
            ),
            ACTION_DEFEND: Button(
                (78, BATTLE_BUTTON_TOP, 54, BATTLE_BUTTON_HEIGHT), tr("Defend", self._lang())
            ),
            ACTION_SKILL: Button(
                (138, BATTLE_BUTTON_TOP, 54, BATTLE_BUTTON_HEIGHT),
                tr("Skill", self._lang()),
                enabled=can_skill,
                tooltip=skill_cost_text(snap.skill_cost, self._lang()),
            ),
            ACTION_ESCAPE: Button(
                (198, BATTLE_BUTTON_TOP, 54, BATTLE_BUTTON_HEIGHT),
                tr("Escape", self._lang()),
                enabled=snap.can_escape,
            ),
        }

    def _draw_tooltip(self, surface: Any) -> None:
        for button in self._buttons().values():
            if button.tooltip and button.contains(self.hover_pos) and not button.enabled:
                draw_tooltip(self.pygame, surface, self.fonts, button.tooltip, (118, 112))
                return

    def _act(self, action: str) -> ScreenAction | None:
        if action == ACTION_ESCAPE and not self.snapshot.can_escape:
            self.message = tr("Cannot escape from Boss battle", self._lang())
            if self.audio is not None:
                self.audio.play_sfx("ui_denied")
            return None
        if action == ACTION_SKILL and self.snapshot.player.mp < self.snapshot.skill_cost:
            self.message = skill_cost_text(self.snapshot.skill_cost, self._lang())
            if self.audio is not None:
                self.audio.play_sfx("ui_denied")
            return None
        result, snapshot = self.runner.resolve_battle_action(action)
        self.snapshot = snapshot
        self.message = _message_for_result(result, snapshot, self._lang())
        if result.accepted and action in {ACTION_ATTACK, ACTION_SKILL}:
            self.player_attack_timer = 0.25
        self._queue_feedback(result)
        if result.player_damage > 0 or result.critical:
            self.enemy_flash_timer = 0.18
        if result.battle_over:
            reward = self.runner.last_reward_snapshot()
            if result.player_defeated:
                self.pending_action = ScreenAction.replace(
                    GameOverScreen(
                        self.pygame,
                        self.fonts,
                        self.runner,
                        self.assets,
                        won=False,
                        audio=self.audio,
                        settings=self.settings,
                    )
                )
                self.finish_timer = 0.55
                return None
            if result.won:
                if reward is not None:
                    reward_text = battle_reward_feedback(
                        reward.exp,
                        reward.gold,
                        self._lang(),
                        level_up=reward.level_up,
                    )
                    self._float(
                        battle_reward_float(reward.exp, reward.gold, self._lang()),
                        116,
                        86,
                        GOOD,
                        ttl=0.9,
                    )
                else:
                    reward_text = tr("Won battle.", self._lang())
                self.enemy_fade_timer = 0.55
                self.pending_action = ScreenAction.replace(
                    DungeonScreen(
                        self.pygame,
                        self.fonts,
                        self.runner,
                        self.assets,
                        message=reward_text,
                        audio=self.audio,
                        settings=self.settings,
                        settings_store=self.settings_store,
                        settings_error=self.settings_error,
                    )
                )
                self.finish_timer = 0.65
                return None
            if result.escaped:
                self.pending_action = ScreenAction.replace(
                    DungeonScreen(
                        self.pygame,
                        self.fonts,
                        self.runner,
                        self.assets,
                        message="Escaped battle",
                        audio=self.audio,
                        settings=self.settings,
                        settings_store=self.settings_store,
                        settings_error=self.settings_error,
                    )
                )
                self.finish_timer = 0.25
                return None
        return None

    def _queue_feedback(self, result: Any) -> None:
        if result.player_damage:
            self._float(f"-{result.player_damage}", 238, 58, BAD)
            self.enemy_flash_timer = 0.18
            if self.audio is not None:
                self.audio.play_sfx("combat_crit" if result.critical else "combat_hit")
        if result.critical:
            self._float(tr("Critical", self._lang()).upper(), 216, 38, BAD, ttl=0.9)
            self.critical_timer = 0.3
        if result.enemy_damage:
            self._float(f"-{result.enemy_damage}", 44, 68, BAD)
            self.player_flash_timer = 0.18
            if self.audio is not None:
                self.audio.play_sfx("combat_hurt")
        if result.defended:
            self._float(tr("Defended", self._lang()).upper(), 36, 56, GOOD)
            self.shield_timer = 0.35
            if self.audio is not None:
                self.audio.play_sfx("combat_defend")
        if result.won and self.audio is not None:
            self.audio.play_sfx("combat_kill")
        if result.escaped and self.audio is not None:
            self.audio.play_sfx("ui_cancel")

    def _float(
        self,
        text: str,
        x: int,
        y: int,
        color: tuple[int, int, int],
        *,
        ttl: float = 0.7,
    ) -> None:
        self.floating_texts.append(FloatingText(text=text, x=x, y=y, color=color, ttl=ttl))

    def _draw_scene(self, surface: Any, boss: bool) -> None:
        draw_location_stage(
            self.pygame,
            surface,
            self.assets,
            BATTLE_SCENE_RECT,
            ground_y=BATTLE_GROUND_TOP,
            border=BAD if boss else ACCENT,
        )
        if boss:
            self.pygame.draw.rect(surface, (82, 35, 46), (238, 52, 52, 64), 1)

    def _draw_combat_fx(self, surface: Any) -> None:
        if self.player_attack_timer > 0 or self.critical_timer > 0:
            self.assets.draw(surface, FX_SLASH_SPRITE, (226, 72, 36, 36))
        if self.shield_timer > 0:
            self.assets.draw(surface, FX_SHIELD_SPRITE, BATTLE_PLAYER_SHIELD_RECT)
        if self.enemy_fade_timer > 0:
            self.assets.draw(surface, FX_REWARD_SPRITE, (134, 78, 32, 32))

    def _player_sprite_id(self) -> str:
        if self.shield_timer > 0:
            return PLAYER_DEFEND_SPRITE
        if self.player_attack_timer > 0:
            return PLAYER_ATTACK_SPRITE
        return PLAYER_IDLE_SPRITE

    def _enemy_sprite_id(self, enemy: Any) -> str:
        if not enemy.is_boss:
            return ENEMY_DEFAULT_SPRITE
        name = str(enemy.name).lower()
        for token, sprite_id in BOSS_NAME_SPRITES.items():
            if token in name:
                return sprite_id
        return BOSS_SPRITES[sum(ord(char) for char in name) % len(BOSS_SPRITES)]

    def _draw_sprite(
        self,
        surface: Any,
        sprite_id: str,
        rect: tuple[int, int, int, int],
        *,
        alpha: int = 255,
    ) -> None:
        sprite = self.assets.get(sprite_id)
        scaled = self.pygame.transform.scale(sprite, (rect[2], rect[3]))
        if alpha < 255:
            scaled.set_alpha(alpha)
        surface.blit(scaled, (rect[0], rect[1]))

    def _lang(self) -> str:
        return getattr(self.settings, "lang", "en")


def _message_for_result(result: Any, snapshot: Any, lang: str) -> str:
    if not result.accepted:
        return str(result.message)
    parts: list[str] = []
    if result.player_damage:
        parts.append(f"{tr('Dealt', lang)} {result.player_damage}")
    if result.enemy_damage:
        parts.append(f"{tr('Took', lang)} {result.enemy_damage}")
    if result.critical:
        parts.append(tr("Critical", lang))
    if result.defended:
        parts.append(tr("Defended", lang))
    if result.escaped:
        parts.append(tr("Escaped", lang))
    if not parts:
        parts.append(snapshot.message)
    return " / ".join(parts)
