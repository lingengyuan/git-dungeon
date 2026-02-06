"""
Mock AI Client

Generates deterministic pseudo-text for testing without network calls.
"""

import hashlib
import json
from typing import List
from .types import TextRequest, TextResponse, TextKind
from .client_base import AIClient


class MockAIClient(AIClient):
    """
    Mock client for testing and CI.
    
    Generates stable pseudo-random text based on request content.
    Does not require network or API keys.
    """
    
    @property
    def name(self) -> str:
        return "mock"
    
    def generate_batch(self, requests: List[TextRequest]) -> List[TextResponse]:
        """Generate pseudo-text for each request."""
        return [self._generate_one(req) for req in requests]
    
    def health_check(self) -> bool:
        """Mock client is always available."""
        return True
    
    def _generate_one(self, request: TextRequest) -> TextResponse:
        """Generate pseudo-text for a single request."""
        # Create deterministic hash from request + context
        context_blob = self._context_fingerprint(request)
        key = f"{request.kind.value}:{request.repo_id}:{request.seed}:{request.lang}:{context_blob}"
        hash_val = hashlib.md5(key.encode()).hexdigest()[:8]
        
        # Generate pseudo-text based on text kind
        if request.kind == TextKind.ENEMY_INTRO:
            templates = [
                "A {commit_type} approaches, its aura pulsing with {adjective} energy.",
                "The {commit_type} looms, radiating an {adjective} presence.",
                "{commit_type}: {adjective} code converges before you.",
            ]
            adjective = self._adjective(hash_val)
            commit_type = request.extra_context.get("commit_type", "commit")
            text = templates[int(hash_val[0], 16) % len(templates)].format(
                commit_type=commit_type,
                adjective=adjective
            )
            
        elif request.kind == TextKind.BATTLE_START:
            templates = [
                "The battle begins! {commit_type} prepares its {attack}...",
                "Your blade meets {commit_type}'s {defense}. The clash echoes!",
                "{commit_type} activates {ability}. Brace yourself!",
            ]
            commit_type = request.extra_context.get("commit_type", "enemy")
            ability = self._ability(hash_val)
            text = templates[int(hash_val[1], 16) % len(templates)].format(
                commit_type=commit_type,
                attack=ability,
                defense=ability,
                ability=ability
            )
            
        elif request.kind == TextKind.BATTLE_END:
            victory = request.extra_context.get("victory", True)
            if victory:
                templates = [
                    "Victory! The {commit_type} falls, leaving behind {loot}.",
                    "You triumph! {loot} added to your collection.",
                    "The {commit_type} is defeated. {bonus}!",
                ]
            else:
                templates = [
                    "Defeat... The {commit_type} stands victorious.",
                    "You retreat, wounded but wiser.",
                    "The {commit_type} laughs as you fall back.",
                ]
            commit_type = request.extra_context.get("commit_type", "enemy")
            loot = self._loot(hash_val)
            bonus = self._bonus(hash_val)
            text = templates[int(hash_val[2], 16) % len(templates)].format(
                commit_type=commit_type,
                loot=loot,
                bonus=bonus
            )
            
        elif request.kind == TextKind.EVENT_FLAVOR:
            templates = [
                "You enter a {place}, {atmosphere}.",
                "The {place} glows with {atmosphere} energy.",
                "Ancient {place}: {atmosphere} whispers echo around you.",
            ]
            place = self._place(hash_val)
            atmosphere = self._atmosphere(hash_val)
            text = templates[int(hash_val[3], 16) % len(templates)].format(
                place=place,
                atmosphere=atmosphere
            )
            
        elif request.kind == TextKind.BOSS_PHASE:
            templates = [
                "{boss_name} shifts to phase {phase}! {ability} activates.",
                "The {boss_name} roars! Phase {phase} begins with {effect}.",
                "{boss_name}'s eyes glow {color}. Phase {phase} unleashed!",
            ]
            boss_name = request.extra_context.get("boss_name", "entity")
            phase = request.extra_context.get("phase", "2")
            ability = self._ability(hash_val)
            effect = self._effect(hash_val)
            color = self._color(hash_val)
            text = templates[int(hash_val[4], 16) % len(templates)].format(
                boss_name=boss_name,
                phase=phase,
                ability=ability,
                effect=effect,
                color=color
            )
        else:
            text = ""
        
        # Trim to length limits
        text = self._trim_to_limit(text, request.kind)
        
        return TextResponse(
            text=text,
            provider="mock",
            cached=False,
            meta={"mock": True}
        )

    def _context_fingerprint(self, request: TextRequest) -> str:
        """Stable context fingerprint to diversify fallback text by scenario."""
        payload = {
            "commit_sha": request.commit_sha,
            "enemy_id": request.enemy_id,
            "event_id": request.event_id,
            "extra_context": request.extra_context,
        }
        try:
            raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        except Exception:
            raw = str(payload)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    
    def _adjective(self, hash_val: str) -> str:
        adjectives = ["mysterious", "ancient", "dark", "brilliant", "chaotic", 
                      "serene", "volatile", "ethereal", "fierce", "shadowy"]
        return adjectives[int(hash_val[0], 16) % len(adjectives)]
    
    def _ability(self, hash_val: str) -> str:
        abilities = ["void ray", "shadow strike", "power surge", "time warp", 
                     "quantum shield", "plasma blade", "nebula blast"]
        return abilities[int(hash_val[1], 16) % len(abilities)]
    
    def _loot(self, hash_val: str) -> str:
        loots = ["a rare relic", "ancient knowledge", "encoded wisdom", 
                 "powerful artifacts", "forgotten scripts"]
        return loots[int(hash_val[2], 16) % len(loots)]
    
    def _bonus(self, hash_val: str) -> str:
        bonuses = ["Experience gained", "New paths revealed", "Strength increased",
                   "Your deck grows stronger", "Victory echoes through time"]
        return bonuses[int(hash_val[2], 16) % len(bonuses)]
    
    def _place(self, hash_val: str) -> str:
        places = ["ancient library", "floating citadel", "crystal cavern", 
                  "quantum realm", "digital void", "nebula chamber"]
        return places[int(hash_val[3], 16) % len(places)]
    
    def _atmosphere(self, hash_val: str) -> str:
        atmospheres = ["pulsating", "humming", "ethereal", "vibrating", "resonating"]
        return atmospheres[int(hash_val[3], 16) % len(atmospheres)]
    
    def _effect(self, hash_val: str) -> str:
        effects = ["devastating power", "reality warping", "cosmic energy", 
                   "dark matter swirls", "light explodes"]
        return effects[int(hash_val[4], 16) % len(effects)]
    
    def _color(self, hash_val: str) -> str:
        colors = ["crimson", "azure", "violet", "golden", "silver"]
        return colors[int(hash_val[4], 16) % len(colors)]
    
    def _trim_to_limit(self, text: str, kind: TextKind) -> str:
        """Trim text to meet kind-specific length limits."""
        limits = {
            TextKind.ENEMY_INTRO: 60,
            TextKind.BATTLE_START: 80,
            TextKind.BATTLE_END: 80,
            TextKind.EVENT_FLAVOR: 80,
            TextKind.BOSS_PHASE: 80,
        }
        limit = limits.get(kind, 80)
        if len(text) > limit:
            return text[:limit - 3].rstrip() + "..."
        return text
