"""Game engine - main state and loop management."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

from .git_parser import GitParser, CommitInfo
from .entity import Entity
from .character import CharacterComponent, CharacterType, CharacterStats
from .combat import CombatSystem, CombatEncounter
from .inventory import InventoryComponent
from .save_system import SaveSystem
from .resource_manager import ResourceManager
from git_dungeon.config import GameConfig, Difficulty
from git_dungeon.utils.logger import setup_logger

if TYPE_CHECKING:
    from .system import System

logger = setup_logger(__name__)


@dataclass
class GameState:
    """Complete game state."""

    # Core components
    parser: Optional[GitParser] = None
    player: Optional[Entity] = None
    combat_system: Optional[CombatSystem] = None
    save_system: Optional[SaveSystem] = None
    resource_manager: Optional[ResourceManager] = None

    # Game progress
    commits: list[CommitInfo] = field(default_factory=list)
    current_commit_index: int = 0
    defeated_commits: list[str] = field(default_factory=list)
    current_commit: Optional[CommitInfo] = None
    current_combat: Optional[CombatEncounter] = None

    # Game state
    game_time: float = 0
    is_paused: bool = False
    is_game_over: bool = False
    turn_number: int = 0

    # Configuration
    config: GameConfig = field(default_factory=GameConfig)

    # Systems
    systems: list[System] = field(default_factory=list)

    def __post_init__(self):
        """Initialize game state."""
        # Initialize systems
        self.resource_manager = ResourceManager(self.config)
        self.combat_system = CombatSystem(self.config)
        self.save_system = SaveSystem()

        # Create player if not exists
        if self.player is None:
            self._create_player()

    def _create_player(self) -> Entity:
        """Create player entity."""
        player = Entity(
            id="player",
            name="Developer",
        )

        # Add character component
        char_comp = CharacterComponent(
            char_type=CharacterType.PLAYER,
            name="Developer",
            level=1,
            experience=0,
        )
        char_comp.initialize_stats(
            hp=100,  # Base HP from code lines
            mp=50,   # Base MP from commits
            attack=10,  # Base attack
            defense=5,  # Base defense
            speed=10,
            critical=10,
            evasion=5,
            luck=5,
        )
        player.add_component(char_comp)

        # Add inventory component
        inventory = InventoryComponent(max_slots=50)
        player.add_component(inventory)

        self.player = player
        return player

    def add_system(self, system: "System") -> None:
        """Add a system to the game.

        Args:
            system: System to add
        """
        self.systems.append(system)

    def remove_system(self, system_type: type) -> None:
        """Remove a system by type.

        Args:
            system_type: Type of system to remove
        """
        self.systems = [s for s in self.systems if not isinstance(s, system_type)]

    def get_system(self, system_type: type) -> Optional["System"]:
        """Get a system by type.

        Args:
            system_type: Type of system to get

        Returns:
            System or None
        """
        for system in self.systems:
            if isinstance(system, system_type):
                return system
        return None

    def load_repository(self, path: str) -> bool:
        """Load a Git repository.

        Args:
            path: Path to repository

        Returns:
            True if successful
        """
        try:
            self.parser = GitParser(self.config)
            self.parser.load_repository(path)
            self.commits = self.parser.get_commit_history(limit=self.config.max_commits)

            # Update config with the actual repo path (for save/load)
            self.config.repo_path = path

            # Set first commit (oldest) as current
            if self.commits:
                self.current_commit = self.commits[0]
                self.current_commit_index = 0

            logger.info(f"Loaded {len(self.commits)} commits from {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load repository: {e}")
            return False

    def start_combat(self) -> bool:
        """Start combat with current commit.

        Returns:
            True if combat started, False if already in combat or no commit
        """
        # Don't start if already in combat
        if self.current_combat is not None:
            logger.debug("Combat already in progress, cannot start new combat")
            return False

        if not self.player or not self.current_commit:
            return False

        # Create enemy entity from commit
        enemy = self._create_enemy_from_commit(self.current_commit)

        # Start combat
        self.current_combat = self.combat_system.start_combat(self.player, enemy)
        self.turn_number += 1

        return True

    def _create_enemy_from_commit(self, commit: CommitInfo) -> Entity:
        """Create an enemy entity from a commit.

        Args:
            commit: Commit information

        Returns:
            Enemy entity
        """
        enemy = Entity(
            id=f"commit_{commit.short_hash}",
            name=commit.get_creature_name(),
        )

        # Calculate stats based on commit
        base_hp = max(20, commit.total_changes)
        base_attack = max(5, commit.additions)
        base_defense = max(1, commit.deletions)

        char_comp = CharacterComponent(
            char_type=CharacterType.MONSTER,
            name=commit.get_creature_name(),
            level=1,
            experience=commit.total_changes // 10,
        )
        char_comp.initialize_stats(
            hp=base_hp,
            mp=0,
            attack=base_attack,
            defense=base_defense,
            speed=5,
            critical=5,
            evasion=2,
            luck=2,
        )

        enemy.add_component(char_comp)

        return enemy

    def player_action(self, action: str, **kwargs) -> bool:
        """Execute a player action in combat.

        Args:
            action: Action type
            **kwargs: Action parameters

        Returns:
            True if action was executed
        """
        if not self.current_combat:
            return False

        result = self.current_combat.player_action(action, **kwargs)

        # Check if combat ended
        if self.current_combat:
            if self.current_combat.ended:
                if result.value == "player_win":
                    self._on_enemy_defeated()
                self.current_combat = None

        return True

    def enemy_turn(self) -> bool:
        """Execute enemy turn.

        Returns:
            True if turn was executed
        """
        if not self.current_combat:
            return False

        result = self.current_combat.enemy_turn()

        # Check if combat ended
        if self.current_combat.ended:
            if result.value == "enemy_win":
                self._on_player_defeated()
            self.current_combat = None

        return True

    def _on_enemy_defeated(self) -> None:
        """Handle enemy defeat."""
        if not self.current_commit:
            return

        # Mark commit as defeated
        self.defeated_commits.append(self.current_commit.hash)

        # Grant experience
        char = self.player.get_component(CharacterComponent) if self.player else None
        if char:
            char.gain_experience(self.current_commit.total_changes)

        # Clear current combat
        self.current_combat = None

        # Move to next commit
        self._advance_to_next_commit()

    def _on_player_defeated(self) -> None:
        """Handle player defeat."""
        self.is_game_over = True

    def _advance_to_next_commit(self) -> bool:
        """Advance to the next commit.

        Returns:
            True if there are more commits
        """
        self.current_commit_index += 1

        if self.current_commit_index < len(self.commits):
            self.current_commit = self.commits[self.current_commit_index]
            logger.info(
                f"Advanced to commit {self.current_commit.short_hash}: "
                f"{self.current_commit.message[:50]}"
            )
            return True
        else:
            # All commits defeated!
            logger.info("All commits defeated! Victory!")
            self.is_game_over = True
            # 不设置为 None，让测试可以检查状态
            # self.current_commit = None
            return False

    def use_item(self, slot_index: int) -> bool:
        """Use an item from inventory.

        Args:
            slot_index: Inventory slot index

        Returns:
            True if item was used
        """
        if not self.player:
            return False

        inventory = self.player.get_component(InventoryComponent)
        if not inventory:
            return False

        return inventory.use_item(slot_index, self.player)

    def update(self, delta_time: float) -> None:
        """Update game state.

        Args:
            delta_time: Time since last update in seconds
        """
        if self.is_paused or self.is_game_over:
            return

        self.game_time += delta_time

        # Update all systems
        for system in self.systems:
            system.update(delta_time)

        # Update player
        if self.player:
            char = self.player.get_component(CharacterComponent)
            if char:
                char.update(delta_time)

    def pause(self) -> None:
        """Pause the game."""
        self.is_paused = True

    def resume(self) -> None:
        """Resume the game."""
        self.is_paused = False

    def save_game(self, slot: int = 0) -> bool:
        """Save the game.

        Args:
            slot: Save slot

        Returns:
            True if saved successfully
        """
        if not self.save_system:
            return False
        return self.save_system.save(self, slot)

    def load_game(self, slot: int = 0) -> bool:
        """Load the game.

        Args:
            slot: Save slot

        Returns:
            True if loaded successfully
        """
        if not self.save_system:
            return False
        return self.save_system.load(self, slot)

    def get_progress(self) -> dict:
        """Get current game progress.

        Returns:
            Progress dictionary
        """
        return {
            "commits_total": len(self.commits),
            "commits_defeated": len(self.defeated_commits),
            "current_commit_index": self.current_commit_index,
            "player_level": (
                self.player.get_component(CharacterComponent).level
                if self.player else 0
            ),
            "player_hp": (
                self.player.get_component(CharacterComponent).current_hp
                if self.player else 0
            ),
            "turn_number": self.turn_number,
            "game_time": self.game_time,
            "is_in_combat": self.current_combat is not None,
        }
