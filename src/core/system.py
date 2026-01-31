"""Game system base class."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game_engine import GameEngine


class System:
    """Base system class for ECS architecture."""

    def __init__(self, engine: "GameEngine"):
        """Initialize the system.

        Args:
            engine: Reference to the game engine
        """
        self.engine = engine

    def update(self, delta_time: float) -> None:
        """Update the system.

        Args:
            delta_time: Time since last update in seconds
        """
        pass

    def render(self) -> None:
        """Render the system."""
        pass
