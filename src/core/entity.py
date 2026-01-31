"""Game entity system (ECS-like architecture)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .component import Component


@dataclass
class Entity:
    """Base entity class."""

    id: str
    name: str = ""
    components: dict[type, "Component"] = field(default_factory=dict)

    def add_component(self, component: "Component") -> None:
        """Add a component to the entity."""
        self.components[type(component)] = component
        component.entity = self

    def remove_component(self, component_type: type) -> None:
        """Remove a component from the entity."""
        if component_type in self.components:
            del self.components[component_type]

    def get_component(self, component_type: type) -> "Component | None":
        """Get a component by type."""
        return self.components.get(component_type)

    def has_component(self, component_type: type) -> bool:
        """Check if entity has a component."""
        return component_type in self.components

    def __getitem__(self, key: type) -> "Component":
        """Get component using bracket syntax."""
        result = self.get_component(key)
        if result is None:
            raise KeyError(f"Component {key} not found")
        return result

    def __contains__(self, key: type) -> bool:
        """Check for component using 'in' operator."""
        return self.has_component(key)
