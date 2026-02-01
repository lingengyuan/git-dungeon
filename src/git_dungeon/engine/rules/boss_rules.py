# boss_rules.py - Boss battle system

"""
Boss battle system for Git Dungeon.

Features:
- Multi-phase bosses
- Special boss abilities
- Boss AI behaviors
- Boss rewards
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from enum import Enum
from random import randint

from git_dungeon.engine.rng import RNG, roll_chance
from git_dungeon.engine.events import GameEvent, EventType


class BossPhase(Enum):
    """Boss fight phases."""
    PHASE_1 = "phase_1"
    PHASE_2 = "phase_2"
    PHASE_3 = "phase_3"
    ENRAGED = "enraged"


class BossAbilityType(Enum):
    """Types of boss abilities."""
    AOE = "aoe"              # Area of effect damage
    BUFF = "buff"            # Buff self
    DEBUFF = "debuff"        # Debuff player
    SUMMON = "summon"        # Summon minions
    HEAL = "heal"            # Heal self
    CHARGE = "charge"        # Charge up for big attack
    ESCAPE = "escape"        # Phase transition


class BossAIType(Enum):
    """Boss AI behavior types."""
    AGGRESSIVE = "aggressive"     # Always attack
    TACTICAL = "tactical"         # Use abilities strategically
    PHASE_BASED = "phase_based"   # Different behavior per phase
    PATTERN = "pattern"           # Fixed action pattern


@dataclass
class BossAbility:
    """A boss special ability."""
    ability_id: str
    name: str
    ability_type: BossAbilityType
    damage_multiplier: float = 1.0
    cooldown: int = 3
    current_cooldown: int = 0
    description: str = ""
    
    def use(self) -> bool:
        """Use ability (returns True if successful)."""
        if self.current_cooldown <= 0:
            self.current_cooldown = self.cooldown
            return True
        return False
    
    def tick(self):
        """Reduce cooldown."""
        if self.current_cooldown > 0:
            self.current_cooldown -= 1


@dataclass 
class BossPhaseData:
    """Data for a boss phase."""
    phase: BossPhase
    hp_multiplier: float = 1.0
    attack_multiplier: float = 1.0
    defense_multiplier: float = 1.0
    abilities: List[BossAbility] = field(default_factory=list)
    description: str = ""


@dataclass
class BossTemplate:
    """Template for creating boss enemies."""
    boss_id: str
    name: str
    description: str
    base_hp: int
    base_attack: int
    base_defense: int
    phases: List[BossPhaseData] = field(default_factory=list)
    ai_type: BossAIType = BossAIType.AGGRESSIVE
    abilities: List[BossAbility] = field(default_factory=list)
    drop_items: List[str] = field(default_factory=list)
    bonus_gold: int = 100
    bonus_exp: int = 200
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "boss_id": self.boss_id,
            "name": self.name,
            "description": self.description,
            "base_hp": self.base_hp,
            "base_attack": self.base_attack,
            "base_defense": self.base_defense,
            "phases": [p.phase.value for p in self.phases],
            "ai_type": self.ai_type.value,
            "abilities": [a.name for a in self.abilities],
        }


class BossState:
    """State of a boss in combat."""
    
    def __init__(self, template: BossTemplate):
        self.template = template
        self.name = template.name
        self.boss_id = template.boss_id
        
        # Current stats
        self.max_hp = template.base_hp
        self.current_hp = template.base_hp
        self.attack = template.base_attack
        self.defense = template.base_defense
        
        # Phase tracking
        self.current_phase_index = 0
        self.phase = BossPhase.PHASE_1
        
        # Ability tracking
        self.abilities = [BossAbility(
            ability_id=a.ability_id,
            name=a.name,
            ability_type=a.ability_type,
            damage_multiplier=a.damage_multiplier,
            cooldown=a.cooldown,
            description=a.description,
        ) for a in template.abilities]
        
        # AI state
        self.ai_type = template.ai_type
        self.action_history: List[str] = []
        self.turn_count = 0
        
        # Enrage threshold
        self.enrage_threshold = 0.25  # 25% HP
    
    @property
    def is_alive(self) -> bool:
        return self.current_hp > 0
    
    @property
    def is_enraged(self) -> bool:
        return self.current_hp <= self.max_hp * self.enrage_threshold
    
    @property
    def phase_name(self) -> str:
        return self.phase.value
    
    def take_damage(self, amount: int) -> int:
        """Take damage, return actual damage dealt."""
        actual = max(1, amount - self.defense)
        self.current_hp = max(0, self.current_hp - actual)
        
        # Check phase transition
        self._check_phase_transition()
        
        return actual
    
    def _check_phase_transition(self):
        """Check and handle phase transitions."""
        hp_percent = self.current_hp / self.max_hp if self.max_hp > 0 else 0
        
        if self.is_enraged and self.phase != BossPhase.ENRAGED:
            self._transition_to_phase(BossPhase.ENRAGED)
        elif hp_percent <= 0.5 and self.phase == BossPhase.PHASE_1:
            self._transition_to_phase(BossPhase.PHASE_2)
        elif hp_percent <= 0.75 and self.current_phase_index == 0:
            self._transition_to_phase(BossPhase.PHASE_2)
    
    def _transition_to_phase(self, new_phase: BossPhase):
        """Transition to a new phase."""
        old_phase = self.phase
        self.phase = new_phase
        self.current_phase_index += 1
        
        # Apply phase multipliers
        phase_data = self._get_phase_data(new_phase)
        if phase_data:
            self.attack = int(self.template.base_attack * phase_data.attack_multiplier)
            self.defense = int(self.template.base_defense * phase_data.defense_multiplier)
    
    def _get_phase_data(self, phase: BossPhase) -> Optional[BossPhaseData]:
        """Get phase data for a phase."""
        for p in self.template.phases:
            if p.phase == phase:
                return p
        return None
    
    def tick_abilities(self):
        """Tick all ability cooldowns."""
        for ability in self.abilities:
            ability.tick()
    
    def get_available_abilities(self) -> List[BossAbility]:
        """Get abilities that are off cooldown."""
        return [a for a in self.abilities if a.current_cooldown <= 0]
    
    def get_next_action(self, rng: RNG, player_hp_percent: float = 1.0) -> str:
        """
        Determine the next boss action.
        
        Returns:
            Action string: "attack", ability_id, or "defend"
        """
        self.turn_count += 1
        
        if self.ai_type == BossAIType.AGGRESSIVE:
            return self._aggressive_ai(rng)
        elif self.ai_type == BossAIType.TACTICAL:
            return self._tactical_ai(rng, player_hp_percent)
        elif self.ai_type == BossAIType.PHASE_BASED:
            return self._phase_based_ai(rng)
        else:
            return "attack"
    
    def _aggressive_ai(self, rng: RNG) -> str:
        """Aggressive AI - always attack, use abilities when available."""
        available = self.get_available_abilities()
        if available and roll_chance(rng, 0.3):  # 30% chance to use ability
            ability = rng.choice(available)
            return ability.ability_id
        return "attack"
    
    def _tactical_ai(self, rng: RNG, player_hp_percent: float) -> str:
        """Tactical AI - adapt to situation."""
        # If player is low, finish them
        if player_hp_percent < 0.3:
            available = self.get_available_abilities()
            for a in available:
                if a.ability_type == BossAbilityType.AOE:
                    return a.ability_id
        
        # If self is low, heal or buff
        if self.current_hp < self.max_hp * 0.4:
            available = self.get_available_abilities()
            for a in available:
                if a.ability_type in [BossAbilityType.HEAL, BossAbilityType.BUFF]:
                    return a.ability_id
        
        # Default to attack
        return "attack"
    
    def _phase_based_ai(self, rng: RNG) -> str:
        """Phase-based AI - different actions per phase."""
        available = self.get_available_abilities()
        
        if self.phase == BossPhase.ENRAGED:
            # Enraged: use abilities more often
            if available and roll_chance(rng, 0.6):
                return rng.choice(available).ability_id
        elif self.phase == BossPhase.PHASE_2:
            # Phase 2: tactical ability use
            if available and roll_chance(rng, 0.4):
                return rng.choice(available).ability_id
        else:
            # Phase 1: mostly attacks
            if available and roll_chance(rng, 0.2):
                return rng.choice(available).ability_id
        
        return "attack"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "boss_id": self.boss_id,
            "name": self.name,
            "current_hp": self.current_hp,
            "max_hp": self.max_hp,
            "phase": self.phase.value,
            "is_enraged": self.is_enraged,
            "is_alive": self.is_alive,
        }


class BossSystem:
    """
    Manages boss battles.
    
    Features:
    - Boss spawning
    - Boss AI
    - Phase transitions
    - Rewards
    """
    
    # Pre-defined boss templates
    BOSS_TEMPLATES = {
        "merge_conflict": BossTemplate(
            boss_id="merge_conflict",
            name="Merge Conflict",
            description="A tangled web of conflicting changes",
            base_hp=500,
            base_attack=25,
            base_defense=10,
            ai_type=BossAIType.PHASE_BASED,
            bonus_gold=200,
            bonus_exp=500,
            phases=[
                BossPhaseData(
                    phase=BossPhase.PHASE_1,
                    hp_multiplier=1.0,
                    attack_multiplier=1.0,
                    defense_multiplier=1.0,
                    description="Initial state",
                ),
                BossPhaseData(
                    phase=BossPhase.PHASE_2,
                    hp_multiplier=0.5,
                    attack_multiplier=1.3,
                    defense_multiplier=1.0,
                    description="Conflict intensifies",
                ),
                BossPhaseData(
                    phase=BossPhase.ENRAGED,
                    hp_multiplier=0.25,
                    attack_multiplier=1.5,
                    defense_multiplier=1.2,
                    description="FULL CONFLICT!",
                ),
            ],
            abilities=[
                BossAbility(
                    ability_id="conflict_resolution",
                    name="Conflict Resolution",
                    ability_type=BossAbilityType.AOE,
                    damage_multiplier=1.5,
                    cooldown=3,
                    description="Deals damage to all players",
                ),
                BossAbility(
                    ability_id="rebase",
                    name="Rebase",
                    ability_type=BossAbilityType.BUFF,
                    damage_multiplier=0,
                    cooldown=4,
                    description="Boosts attack",
                ),
            ],
            drop_items=["legendary_sword", "dragon_scale"],
        ),
        
        "legacy_code": BossTemplate(
            boss_id="legacy_code",
            name="Legacy Code",
            description="Ancient, undocumented, and terrifying",
            base_hp=800,
            base_attack=35,
            base_defense=15,
            ai_type=BossAIType.TACTICAL,
            bonus_gold=300,
            bonus_exp=800,
            abilities=[
                BossAbility(
                    ability_id="spaghetti",
                    name="Spaghetti Code",
                    ability_type=BossAbilityType.DEBUFF,
                    damage_multiplier=0,
                    cooldown=3,
                    description="Reduces player defense",
                ),
                BossAbility(
                    ability_id="refactor",
                    name="Refactor",
                    ability_type=BossAbilityType.HEAL,
                    damage_multiplier=0,
                    cooldown=5,
                    description="Heals boss HP",
                ),
                BossAbility(
                    ability_id="technical_debt",
                    name="Technical Debt",
                    ability_type=BossAbilityType.AOE,
                    damage_multiplier=2.0,
                    cooldown=6,
                    description="Massive damage",
                ),
            ],
            drop_items=["dragon_scale", "elixir"],
        ),
        
        "infinite_loop": BossTemplate(
            boss_id="infinite_loop",
            name="Infinite Loop",
            description="Caught in an endless cycle...",
            base_hp=1000,
            base_attack=20,
            base_defense=5,
            ai_type=BossAIType.AGGRESSIVE,
            bonus_gold=250,
            bonus_exp=600,
            abilities=[
                BossAbility(
                    ability_id="while_true",
                    name="While True",
                    ability_type=BossAbilityType.AOE,
                    damage_multiplier=1.2,
                    cooldown=2,
                    description="Rapid attacks",
                ),
                BossAbility(
                    ability_id="recursion",
                    name="Recursion",
                    ability_type=BossAbilityType.CHARGE,
                    damage_multiplier=2.5,
                    cooldown=4,
                    description="Charges up for massive hit",
                ),
            ],
            drop_items=["super_potion", "blade"],
        ),
        
        "production_bug": BossTemplate(
            boss_id="production_bug",
            name="Production Bug",
            description="It only happens in production...",
            base_hp=600,
            base_attack=40,
            base_defense=8,
            ai_type=BossAIType.TACTICAL,
            bonus_gold=400,
            bonus_exp=1000,
            abilities=[
                BossAbility(
                    ability_id="race_condition",
                    name="Race Condition",
                    ability_type=BossAbilityType.AOE,
                    damage_multiplier=1.8,
                    cooldown=3,
                    description="Unpredictable damage",
                ),
                BossAbility(
                    ability_id="null_pointer",
                    name="Null Pointer",
                    ability_type=BossAbilityType.DEBUFF,
                    damage_multiplier=0,
                    cooldown=4,
                    description="Disables player abilities",
                ),
                BossAbility(
                    ability_id="memory_leak",
                    name="Memory Leak",
                    ability_type=BossAbilityType.DEBUFF,
                    damage_multiplier=0,
                    cooldown=5,
                    description="Slowly drains HP over time",
                ),
            ],
            drop_items=["legendary_sword", "elixir"],
        ),
    }
    
    def __init__(self, rng: RNG):
        self.rng = rng
    
    def create_boss(self, boss_id: str, chapter_index: int = 0) -> Optional[BossState]:
        """
        Create a boss for a chapter.
        
        Args:
            boss_id: ID of the boss template
            chapter_index: Current chapter (for scaling)
            
        Returns:
            BossState or None if not found
        """
        template = self.BOSS_TEMPLATES.get(boss_id)
        if not template:
            return None
        
        # Scale boss by chapter
        scale_factor = 1.0 + (chapter_index * 0.15)
        
        scaled_template = BossTemplate(
            boss_id=template.boss_id,
            name=template.name,
            description=template.description,
            base_hp=int(template.base_hp * scale_factor),
            base_attack=int(template.base_attack * scale_factor),
            base_defense=int(template.base_defense * scale_factor),
            phases=template.phases,
            ai_type=template.ai_type,
            abilities=template.abilities,
            drop_items=template.drop_items,
            bonus_gold=int(template.bonus_gold * scale_factor),
            bonus_exp=int(template.bonus_exp * scale_factor),
        )
        
        return BossState(scaled_template)
    
    def get_random_boss(self, chapter_index: int) -> BossState:
        """Get a random boss for the chapter."""
        boss_ids = list(self.BOSS_TEMPLATES.keys())
        boss_id = self.rng.choice(boss_ids)
        return self.create_boss(boss_id, chapter_index)
    
    def get_boss_for_chapter_type(self, chapter_type: str, chapter_index: int) -> Optional[BossState]:
        """Get appropriate boss for chapter type."""
        boss_mapping = {
            "integration": "merge_conflict",
            "legacy": "legacy_code",
            "fix": "production_bug",
            "feature": "infinite_loop",
        }
        
        boss_id = boss_mapping.get(chapter_type, "infinite_loop")
        return self.create_boss(boss_id, chapter_index)
    
    def render_boss_intro(self, boss: BossState) -> str:
        """Render boss introduction."""
        lines = [
            "",
            "=" * 50,
            f"👹 BOSS BATTLE",
            "=" * 50,
            f"⚠️  WARNING: {boss.name}",
            f"📝 {boss.template.description}",
            "",
            f"❤️  HP: {boss.current_hp}/{boss.max_hp}",
            f"⚔️  ATK: {boss.attack}",
            f"🛡️  DEF: {boss.defense}",
        ]
        
        # Show abilities
        if boss.abilities:
            lines.extend([
                "",
                "💥 ABILITIES:",
            ])
            for ability in boss.abilities:
                lines.append(f"   • {ability.name}: {ability.description}")
        
        lines.extend([
            "",
            f"Phase: {boss.phase_name}",
            "=" * 50,
        ])
        
        return "\n".join(lines)
    
    def render_boss_status(self, boss: BossState) -> str:
        """Render boss status bar."""
        hp_percent = boss.current_hp / boss.max_hp if boss.max_hp > 0 else 0
        width = 20
        filled = int(hp_percent * width)
        
        # HP bar
        color = "🔴" if hp_percent < 0.3 else "🟡" if hp_percent < 0.6 else "🟢"
        bar = "█" * filled + "░" * (width - filled)
        
        lines = [
            f"👹 {boss.name}",
            f"{color} HP:{boss.current_hp:4}/{boss.max_hp:4}|{bar}|",
        ]
        
        # Phase indicator
        if boss.is_enraged:
            lines.append("🔥 ENRAGED! 🔥")
        
        # Cooldowns
        abilities_on_cd = [a for a in boss.abilities if a.current_cooldown > 0]
        if abilities_on_cd:
            cd_names = ", ".join(f"{a.name}({a.current_cooldown})" for a in abilities_on_cd[:3])
            lines.append(f"⏳ CD: {cd_names}")
        
        return "\n".join(lines)
    
    def calculate_boss_damage(self, boss: BossState, ability_id: str = "attack") -> int:
        """Calculate damage from boss attack or ability."""
        if ability_id == "attack":
            base_damage = boss.attack
        else:
            ability = None
            for a in boss.abilities:
                if a.ability_id == ability_id:
                    ability = a
                    break
            
            if ability:
                base_damage = int(boss.attack * ability.damage_multiplier)
            else:
                base_damage = boss.attack
        
        # Enrage bonus
        if boss.is_enraged:
            base_damage = int(base_damage * 1.3)
        
        return base_damage
    
    def get_boss_rewards(self, boss: BossState) -> Dict[str, int]:
        """Get rewards for defeating a boss."""
        return {
            "gold": boss.template.bonus_gold,
            "exp": boss.template.bonus_exp,
            "items": boss.template.drop_items,
        }
    
    def render_victory(self, boss: BossState) -> str:
        """Render boss defeat message."""
        rewards = self.get_boss_rewards(boss)
        
        lines = [
            "",
            "=" * 50,
            f"🎉 BOSS DEFEATED: {boss.name}",
            "=" * 50,
            "",
            f"💰 Gold: +{rewards['gold']}",
            f"⭐ EXP: +{rewards['exp']}",
        ]
        
        if rewards['items']:
            items_str = ", ".join(rewards['items'])
            lines.append(f"🎁 Items: {items_str}")
        
        lines.extend([
            "",
            "=" * 50,
        ])
        
        return "\n".join(lines)


# Export
__all__ = [
    "BossPhase",
    "BossAbilityType",
    "BossAIType",
    "BossAbility",
    "BossPhaseData",
    "BossTemplate",
    "BossState",
    "BossSystem",
]
