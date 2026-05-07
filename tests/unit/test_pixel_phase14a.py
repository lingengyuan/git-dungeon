"""Phase 14A tests for shared pixel UI text and widgets."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

from git_dungeon.ui_pixel.app import PixelFont
from git_dungeon.ui_pixel import widgets
from git_dungeon.ui_pixel.screens.battle import (
    BATTLE_ACTION_BAR_RECT,
    BATTLE_BUTTON_HEIGHT,
    BATTLE_BUTTON_TOP,
    BATTLE_ENEMY_BAR_RECT,
    BATTLE_ENEMY_HIT_RECT,
    BATTLE_ENEMY_SPRITE_RECT,
    BATTLE_PLAYER_BAR_RECT,
    BATTLE_PLAYER_HP_POS,
    BATTLE_PLAYER_MP_POS,
    BATTLE_PLAYER_NAME_POS,
    BATTLE_PLAYER_SPRITE_RECT,
)
from git_dungeon.ui_pixel.text import (
    battle_reward_feedback,
    rest_detail,
    rest_result_feedback,
    shop_offer_detail,
    shop_result_feedback,
    skill_cost_text,
    stat_value,
    trap_feedback,
)


SCREEN_DIR = Path("src/git_dungeon/ui_pixel/screens")


def test_stat_and_reward_formatters_use_player_language() -> None:
    assert stat_value("hp", 8, "en", 10) == "Health 8/10"
    assert stat_value("mp", 3, "en", 5) == "Energy 3/5"
    assert skill_cost_text(10, "en") == "Need 10 Energy"

    reward = battle_reward_feedback(12, 15, "zh_CN")

    assert "经验" in reward
    assert "金币" in reward
    assert "EXP" not in reward
    assert "Gold" not in reward


def test_rest_shop_and_trap_formatters_hide_raw_fields() -> None:
    offer = SimpleNamespace(cost=20, heal=5, attack=2, mp=1, max_hp=3)

    assert rest_detail("Restore 30 HP", "zh_CN") == "恢复 30 生命"
    assert rest_result_feedback("Restore 30 HP", "zh_CN") == "休息结果：恢复 30 生命"
    assert shop_offer_detail(offer, "en") == (
        "Cost 20 Gold / Health +5 / Attack +2 / Energy +1 / Max Health +3"
    )
    assert shop_offer_detail(offer, "zh_CN") == "20金币 / 生命+5 / 攻击+2 / 魔力+1 / 上限+3"
    assert shop_result_feedback("skip", "zh_CN") == "离开商店"
    assert trap_feedback(8, "zh_CN") == "触发陷阱: 生命 -8"


def test_running_screens_do_not_build_raw_player_stat_text() -> None:
    raw_terms = (
        '"HP"',
        "'HP'",
        '"MP"',
        "'MP'",
        '"EXP"',
        "'EXP'",
        "cost {offer.cost} hp",
        "atk {offer.attack}",
        "maxhp",
        'message=f"Rest:',
        'message=f"Shop:',
    )

    for path in SCREEN_DIR.glob("*.py"):
        source = path.read_text()
        for term in raw_terms:
            assert term not in source, f"{path} still contains raw UI term {term!r}"


def test_shared_widgets_expose_phase14a_ui_kit() -> None:
    assert hasattr(widgets, "draw_dialog")
    assert hasattr(widgets, "draw_toast")
    assert hasattr(widgets, "draw_tooltip")
    assert hasattr(widgets, "draw_action_bar")
    assert hasattr(widgets, "draw_choice_card")
    assert hasattr(widgets, "draw_item_card")


def test_choice_card_text_baselines_fit_inside_compact_card() -> None:
    calls: list[tuple[tuple[int, int], int]] = []

    class FakeDraw:
        @staticmethod
        def rect(*_args: Any, **_kwargs: Any) -> None:
            return None

    class FakeFonts:
        @staticmethod
        def draw_fit(
            _surface: Any,
            _text: str,
            pos: tuple[int, int],
            _max_width: int,
            _color: tuple[int, int, int],
            size: int,
        ) -> None:
            calls.append((pos, size))

    rect = (10, 20, 120, 22)

    widgets.draw_choice_card(
        SimpleNamespace(draw=FakeDraw()),
        object(),
        FakeFonts(),
        rect,
        "1. 冒险选择",
        "损失生命 / 获得金币",
    )

    assert calls
    for pos, size in calls:
        assert pos[1] + size <= rect[1] + rect[3]


def test_chinese_font_prefers_readable_system_font_when_available() -> None:
    pygame = __import__("pygame")
    pygame.init()
    try:
        font = PixelFont(pygame, "zh_CN")
        path = str(font._cjk_font).lower()
    finally:
        pygame.quit()

    assert "ark-pixel" not in path or not (
        Path("/System/Library/Fonts/Hiragino Sans GB.ttc").exists()
        or Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf").exists()
        or Path("/Library/Fonts/Arial Unicode.ttf").exists()
    )


def test_chinese_font_render_size_is_smaller_than_layout_size() -> None:
    pygame = __import__("pygame")
    pygame.init()
    try:
        font = PixelFont(pygame, "zh_CN")
        assert font._render_size(12) == 10
        assert font._render_size(9) == 8
    finally:
        pygame.quit()


def test_battle_text_layout_keeps_status_away_from_bars_and_buttons() -> None:
    assert BATTLE_PLAYER_NAME_POS[1] + 13 <= BATTLE_PLAYER_BAR_RECT[1] - 4
    assert BATTLE_PLAYER_MP_POS[1] + 10 <= BATTLE_BUTTON_TOP - 6
    assert BATTLE_BUTTON_TOP + BATTLE_BUTTON_HEIGHT <= BATTLE_ACTION_BAR_RECT[1] - 3
    sprite_right = BATTLE_PLAYER_SPRITE_RECT[0] + BATTLE_PLAYER_SPRITE_RECT[2]
    assert BATTLE_PLAYER_HP_POS[0] >= sprite_right + 6
    assert BATTLE_PLAYER_MP_POS[0] >= sprite_right + 6
    enemy_bar_bottom = BATTLE_ENEMY_BAR_RECT[1] + BATTLE_ENEMY_BAR_RECT[3]
    assert BATTLE_ENEMY_SPRITE_RECT[1] >= enemy_bar_bottom + 6
    assert BATTLE_ENEMY_HIT_RECT[1] >= enemy_bar_bottom + 4
