"""Unit tests for strict runtime content-pack loading."""

from __future__ import annotations

from pathlib import Path
import textwrap

import pytest

from git_dungeon.content.runtime_loader import ContentPackLoadError, load_runtime_content


def _write_pack_file(pack_dir: Path, body: str) -> None:
    pack_dir.mkdir(parents=True, exist_ok=True)
    (pack_dir / "pack.yml").write_text(textwrap.dedent(body).strip() + "\n", encoding="utf-8")


def test_runtime_loader_can_load_builtin_pack_by_id() -> None:
    runtime = load_runtime_content(
        content_dir="src/git_dungeon/content",
        content_pack_args=["debug_pack"],
        env_content_dir="",
    )

    assert runtime.loaded_pack_ids == ["debug_pack"]
    assert "debug_pack" in runtime.registry.packs
    assert "debug_burst" in runtime.registry.cards


def test_runtime_loader_external_pack_can_override_and_append(tmp_path: Path) -> None:
    pack_dir = tmp_path / "example_pack"
    _write_pack_file(
        pack_dir,
        """
        pack_info:
          id: example_pack
          name_key: pack.example_pack.name
          desc_key: pack.example_pack.desc
          archetype: general
          rarity: uncommon
          points_cost: 120

        chapter_overrides:
          feature:
            name: "Feature Storm"
            gold_bonus: 1.25

        cards:
          - id: strike
            name_key: card.strike.name
            desc_key: card.strike.desc
            type: attack
            cost: 3
            rarity: common
            effects:
              - type: damage
                value: 9
            tags: ["starter", "override"]

          - id: pack_demo_card
            name_key: card.pack_demo_card.name
            desc_key: card.pack_demo_card.desc
            type: skill
            cost: 1
            rarity: uncommon
            effects:
              - type: block
                value: 8
            tags: ["pack", "demo"]

        relics:
          - id: pack_demo_relic
            name_key: relic.pack_demo_relic.name
            desc_key: relic.pack_demo_relic.desc
            tier: uncommon
            effects:
              bonus_block: 2

        events:
          - id: pack_demo_event
            name_key: event.pack_demo_event.name
            desc_key: event.pack_demo_event.desc
            choices:
              - id: gain_gold
                text_key: event.pack_demo_event.choice.gain_gold
                effects:
                  - opcode: gain_gold
                    value: 33
        """,
    )

    runtime = load_runtime_content(
        content_dir="src/git_dungeon/content",
        content_pack_args=[str(pack_dir)],
        env_content_dir="",
    )

    assert runtime.loaded_pack_ids == ["example_pack"]
    assert runtime.registry.cards["strike"].cost == 3
    assert "pack_demo_card" in runtime.registry.cards
    assert "pack_demo_relic" in runtime.registry.relics
    assert "pack_demo_event" in runtime.registry.events
    assert runtime.chapter_overrides["feature"]["name"] == "Feature Storm"
    assert runtime.chapter_overrides["feature"]["gold_bonus"] == 1.25


def test_runtime_loader_raises_clear_error_for_missing_required_fields(tmp_path: Path) -> None:
    pack_dir = tmp_path / "broken_pack"
    _write_pack_file(
        pack_dir,
        """
        pack_info:
          name_key: pack.broken.name
          desc_key: pack.broken.desc
        cards: []
        relics: []
        events: []
        """,
    )

    with pytest.raises(ContentPackLoadError, match="pack_info.id"):
        load_runtime_content(
            content_dir="src/git_dungeon/content",
            content_pack_args=[str(pack_dir)],
            env_content_dir="",
        )
