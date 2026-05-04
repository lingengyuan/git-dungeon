"""Shared screen contracts for the pixel UI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class ScreenAction:
    """A requested screen stack transition."""

    kind: Literal["push", "pop", "replace", "quit"]
    screen: "Screen | None" = None

    @classmethod
    def push(cls, screen: "Screen") -> "ScreenAction":
        return cls("push", screen)

    @classmethod
    def pop(cls) -> "ScreenAction":
        return cls("pop")

    @classmethod
    def replace(cls, screen: "Screen") -> "ScreenAction":
        return cls("replace", screen)

    @classmethod
    def quit(cls) -> "ScreenAction":
        return cls("quit")


class Screen:
    """Base class for pygame-backed screens.

    Pygame types stay as Any here so importing this module does not require
    pygame in CLI-only installs.
    """

    def enter(self) -> None:
        pass

    def exit(self) -> None:
        pass

    def handle(self, event: Any) -> ScreenAction | None:
        return None

    def update(self, dt: float) -> ScreenAction | None:
        return None

    def draw(self, surface: Any) -> None:
        raise NotImplementedError
