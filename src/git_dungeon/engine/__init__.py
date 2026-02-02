# __init__.py - Engine package (M1: Rewards & Archetype)

from .events import (
    EventType,
    GameEvent,
    battle_started,
    battle_ended,
    damage_dealt,
    exp_gained,
    level_up,
    enemy_defeated,
    chapter_completed,
    item_dropped,
    game_saved,
    error,
    player_action,
    gold_gained,
    status_applied,
    chapter_started,
    game_ended,
)

from .rng import RNG, DefaultRNG, RNGContext, create_rng

from .model import (
    # M1 Enums
    CardType,
    StatusType,
    IntentType,
    # Original Enums
    EntityType,
    CombatActionType,
    ItemRarity,
    # M1 Data Classes
    CardInstance,
    DeckState,
    EnergyState,
    EnemyIntent,
    StatusStack,
    # Original Data Classes
    Stat,
    Stats,
    CharacterState,
    PlayerState,
    EnemyState,
    ChapterState,
    GameState,
    Action,
)

from .engine import Engine

# M1: Rewards & Archetype
from .rules.rewards import (
    RewardType,
    RewardOption,
    RewardBundle,
    ArchetypeBias,
    RewardsEngine,
    ArchetypeEngine,
    create_rewards_engine,
    create_archetype_engine,
)

from .rules.archetype import (
    Archetype,
    ArchetypeDefinition,
    ARCHETYPE_CONFIGS,
    ArchetypeManager,
    BiasTracker,
    create_archetype_manager,
    create_bias_tracker,
)

__all__ = [
    # Events
    "EventType",
    "GameEvent",
    "battle_started",
    "battle_ended",
    "damage_dealt",
    "exp_gained",
    "level_up",
    "enemy_defeated",
    "chapter_completed",
    "item_dropped",
    "game_saved",
    "error",
    "player_action",
    "gold_gained",
    "status_applied",
    "chapter_started",
    "game_ended",
    
    # RNG
    "RNG",
    "DefaultRNG",
    "RNGContext",
    "create_rng",
    
    # M1 Enums
    "CardType",
    "StatusType",
    "IntentType",
    
    # M1 Data Classes
    "CardInstance",
    "DeckState",
    "EnergyState",
    "EnemyIntent",
    "StatusStack",
    
    # Original Data Classes
    "EntityType",
    "CombatActionType",
    "ItemRarity",
    "Stat",
    "Stats",
    "CharacterState",
    "PlayerState",
    "EnemyState",
    "ChapterState",
    "GameState",
    "Action",
    
    # Engine
    "Engine",
    
    # M1: Rewards & Archetype
    "RewardType",
    "RewardOption",
    "RewardBundle",
    "ArchetypeBias",
    "RewardsEngine",
    "ArchetypeEngine",
    "create_rewards_engine",
    "create_archetype_engine",
    
    "Archetype",
    "ArchetypeDefinition",
    "ARCHETYPE_CONFIGS",
    "ArchetypeManager",
    "BiasTracker",
    "create_archetype_manager",
    "create_bias_tracker",
]
