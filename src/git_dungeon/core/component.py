"""Game component system."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .entity import Entity


@dataclass
class Component:
    """Base component class."""

    entity: "Entity | None" = field(default=None, repr=False)

    def on_attach(self) -> None:
        """Called when component is attached to an entity."""
        pass

    def on_detach(self) -> None:
        """Called when component is detached from an entity."""
        pass

    def update(self, delta_time: float) -> None:
        """Update the component.

        Args:
            delta_time: Time since last update in seconds
        """
        pass
