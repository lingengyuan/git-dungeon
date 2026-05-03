"""Schema-contract regression tests for the base ContentLoader."""

from __future__ import annotations

from git_dungeon.content.loader import ContentLoader
from git_dungeon.content.schema import EventChoice, EventDef, EventEffect


def test_loader_normalizes_event_effects_to_eventeffect_instances() -> None:
    """`loader._load_events` once stored raw dicts, breaking the schema's
    `effects: List[EventEffect]` contract. main_cli's auto-mode then crashed
    on the first event node with `'dict' object has no attribute 'opcode'`.

    This test pins the contract: every effect produced by the default loader
    must be an EventEffect instance, mirroring `packs.py:_parse_event`.
    """
    loader = ContentLoader(content_dir="src/git_dungeon/content")
    registry = loader.load()

    assert registry.events, "expected default events to load"

    for event_id, event in registry.events.items():
        assert isinstance(event, EventDef)
        for choice in event.choices:
            assert isinstance(choice, EventChoice)
            for effect in choice.effects:
                assert isinstance(effect, EventEffect), (
                    f"event {event_id} choice {choice.id} produced {type(effect).__name__}, "
                    "expected EventEffect — see content/loader.py:_load_events"
                )
                assert effect.opcode, f"effect under {event_id}/{choice.id} missing opcode"
