"""Shared deterministic actions for non-combat route nodes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from git_dungeon.engine.auto_policy import (
    AutoEventOptionContext,
    REST_ACTION_FOCUS,
    REST_ACTION_HEAL,
)
from git_dungeon.engine.events import apply_event_choice
from git_dungeon.engine.rng import DefaultRNG, RNG
from git_dungeon.engine.route import NodeKind, RouteNode


@dataclass(frozen=True)
class EventResolution:
    event_id: str
    choice_id: str
    hp_delta: int
    gold_delta: int
    messages: tuple[str, ...]
    effects_applied: tuple[str, ...]
    player_alive: bool


@dataclass(frozen=True)
class RestResolution:
    choice: str
    hp_delta: int
    max_hp_delta: int
    attack_delta: int
    message: str


@dataclass(frozen=True)
class ShopResolution:
    choice: str
    purchased: bool
    reason: str | None
    gold_delta: int
    hp_delta: int
    max_hp_delta: int
    attack_delta: int
    mp_delta: int
    message: str


def select_event_for_node(
    events: list[Any],
    *,
    seed: int,
    chapter: Any,
    node: RouteNode,
) -> Any:
    """Pick one deterministic event for a route node."""
    all_events = sorted(events, key=lambda item: item.id)
    if not all_events:
        return None

    preferred_tags: set[str] = {tag.value for tag in node.tags}
    if node.kind == NodeKind.SHOP:
        preferred_tags.update({"shop", "greed"})
    elif node.kind == NodeKind.REST:
        preferred_tags.update({"safe"})
    elif node.kind == NodeKind.ELITE:
        preferred_tags.update({"risk"})

    filtered = [
        event
        for event in all_events
        if (
            not event.route_tags
            or not preferred_tags
            or bool(preferred_tags.intersection(event.route_tags))
        )
    ]
    candidates = filtered or all_events

    chapter_type = getattr(getattr(chapter, "chapter_type", None), "value", "default")
    weights = [
        max(1, int(event.weights.get(chapter_type, event.weights.get("default", 1))))
        for event in candidates
    ]

    picker = DefaultRNG(seed=seed + chapter.chapter_index * 131 + node.position * 17)
    return picker.choices(candidates, weights=weights, k=1)[0]


def build_event_option_context(choice: Any) -> AutoEventOptionContext:
    """Build policy-scoring context for one event choice."""
    hp_delta = 0
    gold_delta = 0
    resource_delta = 0.0
    risk_level = 0
    for effect in choice.effects:
        opcode = str(effect.opcode)
        value = effect.value
        amount = int(value) if isinstance(value, (int, float)) else 0
        if opcode == "heal":
            hp_delta += amount
        elif opcode == "take_damage":
            hp_delta -= amount
            risk_level += 1
        elif opcode == "gain_gold":
            gold_delta += amount
        elif opcode == "lose_gold":
            gold_delta -= amount
        elif opcode in {"add_relic"}:
            resource_delta += 1.2
        elif opcode in {"add_card", "upgrade_card"}:
            resource_delta += 0.8
        elif opcode in {"apply_status", "trigger_battle"}:
            risk_level += 2
            resource_delta -= 0.4
    return AutoEventOptionContext(
        choice_id=choice.id,
        hp_delta=hp_delta,
        gold_delta=gold_delta,
        resource_delta=resource_delta,
        risk_level=risk_level,
    )


def apply_event_resolution(
    state: Any,
    event: Any,
    choice_index: int,
    rng: RNG,
) -> EventResolution:
    """Apply one event choice and return a display-friendly result."""
    if not event.choices:
        raise ValueError(f"Event has no choices: {event.id}")
    if choice_index < 0 or choice_index >= len(event.choices):
        raise ValueError(f"Invalid event choice index: {choice_index}")

    player = state.player.character
    before_hp = player.current_hp
    before_gold = state.player.gold
    choice = event.choices[choice_index]
    effect_payload = [
        {
            "opcode": effect.opcode,
            "value": effect.value,
            "target": effect.target,
            "condition": effect.condition,
        }
        for effect in choice.effects
    ]
    result = apply_event_choice(state, effect_payload, rng)
    return EventResolution(
        event_id=str(event.id),
        choice_id=str(choice.id),
        hp_delta=player.current_hp - before_hp,
        gold_delta=state.player.gold - before_gold,
        messages=tuple(str(message) for message in result.get("messages", [])),
        effects_applied=tuple(str(effect) for effect in result.get("effects_applied", [])),
        player_alive=player.current_hp > 0,
    )


def resolve_rest_action(state: Any, choice: str) -> RestResolution:
    """Apply a rest action using the CLI-equivalent rules."""
    player = state.player.character
    before_hp = player.current_hp
    before_max_hp = player.stats.hp.value
    before_attack = player.stats.attack.value

    if choice == REST_ACTION_HEAL:
        heal_amount = max(10, int(player.stats.hp.value * 0.3))
        actual = player.heal(heal_amount)
        return RestResolution(
            choice=REST_ACTION_HEAL,
            hp_delta=actual,
            max_hp_delta=0,
            attack_delta=0,
            message=f"heal={actual}",
        )
    if choice != REST_ACTION_FOCUS:
        raise ValueError(f"Unknown rest action: {choice}")

    player.stats.attack.base += 2
    player.stats.hp.base += 5
    player.current_hp = min(player.stats.hp.value, player.current_hp + 5)
    return RestResolution(
        choice=REST_ACTION_FOCUS,
        hp_delta=player.current_hp - before_hp,
        max_hp_delta=player.stats.hp.value - before_max_hp,
        attack_delta=player.stats.attack.value - before_attack,
        message="focus=atk+2 hp_max+5",
    )


def shop_offers_for_node(seed: int, chapter: Any, node: RouteNode) -> list[dict[str, Any]]:
    """Build deterministic light-weight shop offers for one node."""
    picker = DefaultRNG(seed=seed + chapter.chapter_index * 211 + node.position * 41)
    tier = chapter.chapter_index
    templates = [
        {
            "id": "patch_kit",
            "label": "Patch Kit",
            "cost": 30 + tier * 5,
            "heal": 18,
            "atk": 0,
            "mp": 0,
        },
        {
            "id": "compiler_blade",
            "label": "Compiler Blade",
            "cost": 55 + tier * 8,
            "heal": 0,
            "atk": 2,
            "mp": 0,
        },
        {
            "id": "cache_tonic",
            "label": "Cache Tonic",
            "cost": 42 + tier * 6,
            "heal": 8,
            "atk": 0,
            "mp": 12,
        },
        {
            "id": "max_hp_patch",
            "label": "MaxHP Patch",
            "cost": 75 + tier * 10,
            "heal": 10,
            "atk": 1,
            "mp": 0,
            "hp_max": 10,
        },
    ]
    picked_ids = picker.sample(list(range(len(templates))), k=min(3, len(templates)))
    return [templates[index] for index in picked_ids]


def apply_shop_offer_to_state(state: Any, offer: dict[str, Any]) -> tuple[int, int, int, int]:
    """Apply one shop offer and return hp/max-hp/attack/mp deltas."""
    player = state.player.character
    before_hp = player.current_hp
    before_max_hp = player.stats.hp.value
    before_attack = player.stats.attack.value
    before_mp = player.current_mp

    hp_max_gain = int(offer.get("hp_max", 0))
    if hp_max_gain:
        player.stats.hp.base += hp_max_gain
        player.current_hp += hp_max_gain
    atk_gain = int(offer.get("atk", 0))
    if atk_gain:
        player.stats.attack.base += atk_gain
    mp_gain = int(offer.get("mp", 0))
    if mp_gain:
        player.current_mp = min(player.stats.mp.value, player.current_mp + mp_gain)
    heal_gain = int(offer.get("heal", 0))
    if heal_gain:
        player.heal(heal_gain)

    return (
        player.current_hp - before_hp,
        player.stats.hp.value - before_max_hp,
        player.stats.attack.value - before_attack,
        player.current_mp - before_mp,
    )


def resolve_shop_purchase(
    state: Any,
    inventory: Any,
    offers: list[dict[str, Any]],
    selected_idx: int | None,
) -> ShopResolution:
    """Apply or skip a shop choice using the CLI-equivalent rules."""
    if selected_idx is None or selected_idx < 0 or selected_idx >= len(offers):
        return ShopResolution(
            choice="skip",
            purchased=False,
            reason=None,
            gold_delta=0,
            hp_delta=0,
            max_hp_delta=0,
            attack_delta=0,
            mp_delta=0,
            message="Shop skipped.",
        )

    offer = offers[selected_idx]
    cost = int(offer["cost"])
    if cost > state.player.gold:
        return ShopResolution(
            choice="insufficient_gold",
            purchased=False,
            reason="insufficient_gold",
            gold_delta=0,
            hp_delta=0,
            max_hp_delta=0,
            attack_delta=0,
            mp_delta=0,
            message="Not enough gold.",
        )

    before_gold = state.player.gold
    state.player.gold -= cost
    if inventory is not None:
        inventory.gold = state.player.gold
    hp_delta, max_hp_delta, attack_delta, mp_delta = apply_shop_offer_to_state(state, offer)
    return ShopResolution(
        choice=str(offer["id"]),
        purchased=True,
        reason=None,
        gold_delta=state.player.gold - before_gold,
        hp_delta=hp_delta,
        max_hp_delta=max_hp_delta,
        attack_delta=attack_delta,
        mp_delta=mp_delta,
        message=f"Purchased {offer['label']} for {cost} gold.",
    )
