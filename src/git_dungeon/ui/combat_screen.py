"""Combat UI components for Git Dungeon."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static, Button
from typing import Any


def format_hp_bar(current: int, maximum: int, width: int = 20) -> str:
    """Create an ASCII HP bar."""
    ratio = max(0, min(1, current / maximum)) if maximum > 0 else 0
    filled = int(ratio * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {current}/{maximum}"


def format_mp_bar(current: int, maximum: int, width: int = 15) -> str:
    """Create an ASCII MP bar."""
    ratio = max(0, min(1, current / maximum)) if maximum > 0 else 0
    filled = int(ratio * width)
    bar = "▓" * filled + "░" * (width - filled)
    return f"[{bar}] {current}/{maximum}"


class CharacterPanel(Static):
    """Panel showing character stats."""

    def __init__(
        self,
        name: str,
        hp: int = 0,
        max_hp: int = 0,
        mp: int = 0,
        max_mp: int = 0,
        attack: int = 0,
        defense: int = 0,
        is_player: bool = True,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._name = name
        self._hp = hp
        self._max_hp = max_hp
        self._mp = mp
        self._max_mp = max_mp
        self._attack = attack
        self._defense = defense
        self._is_player = is_player

    def compose(self) -> ComposeResult:
        """Compose the panel."""
        icon = "⚔️" if self._is_player else "👾"
        hp_bar = format_hp_bar(self._hp, self._max_hp)
        mp_bar = format_mp_bar(self._mp, self._max_mp)

        yield Container(
            Static(f"{icon} {self._name}", classes="name"),
            Static(f"HP: {hp_bar}", classes="hp"),
            Static(f"MP: {mp_bar}", classes="mp"),
            Static(f"ATK: {self._attack}  DEF: {self._defense}", classes="stats"),
            classes=f"character-panel {'player' if self._is_player else 'enemy'}",
        )

    def update_stats(
        self,
        hp: int | None = None,
        mp: int | None = None,
        attack: int | None = None,
        defense: int | None = None,
    ) -> None:
        """Update character stats."""
        if hp is not None:
            self._hp = hp
        if mp is not None:
            self._mp = mp
        if attack is not None:
            self._attack = attack
        if defense is not None:
            self._defense = defense
        self.refresh()


class CombatLog(Static):
    """Combat action log."""

    def __init__(self, max_lines: int = 10, **kwargs: Any):
        super().__init__(**kwargs)
        self._max_lines = max_lines
        self._lines: list[str] = []

    def add_message(self, message: str) -> None:
        """Add a message to the log."""
        self._lines.append(message)
        if len(self._lines) > self._max_lines:
            self._lines = self._lines[-self._max_lines :]
        self.update("\n".join(self._lines))

    def clear(self) -> None:
        """Clear the log."""
        self._lines = []
        self.update("")


class CombatScreen(Static):
    """Main combat screen."""

    CSS = """
    CombatScreen {
        layout: vertical;
        height: 100%;
        width: 100%;
    }

    .combat-area {
        layout: horizontal;
        height: 15;
        margin: 1;
    }

    .character-panel {
        width: 50;
        height: 10;
        border: solid green;
        padding: 1;
    }

    .character-panel.enemy {
        border: solid red;
    }

    .character-panel .name {
        text-style: bold;
        color: $accent;
    }

    .character-panel .hp {
        color: $success;
    }

    .character-panel .mp {
        color: $info;
    }

    .character-panel .stats {
        color: $text-muted;
    }

    .skill-area {
        layout: vertical;
        height: 12;
        margin: 1;
        border: solid $accent;
        padding: 1;
    }

    .skill-title {
        text-style: bold;
        margin-bottom: 1;
    }

    .skill-button {
        width: 40;
        margin: 0 1;
    }

    .combat-log {
        height: 10;
        border: solid $text-muted;
        margin: 1;
        padding: 1;
    }

    .action-area {
        layout: horizontal;
        height: 3;
        margin: 1;
    }

    .action-button {
        width: 20;
        margin: 0 1;
    }
    """

    def __init__(self, **kwargs: Any):
        """Initialize combat screen."""
        super().__init__(**kwargs)
        self._combat_log = CombatLog(id="combat-log")

    def compose(self) -> ComposeResult:
        """Compose the combat screen."""
        # Character panels
        yield Container(
            CharacterPanel(
                "Developer (你)",
                hp=100,
                max_hp=100,
                mp=50,
                max_mp=50,
                attack=10,
                defense=5,
                is_player=True,
                id="player-panel",
            ),
            CharacterPanel(
                "Enemy",
                hp=20,
                max_hp=20,
                attack=5,
                defense=3,
                is_player=False,
                id="enemy-panel",
            ),
            classes="combat-area",
        )

        # Skill panel
        yield Container(
            Static("技能:", classes="skill-title"),
            Button("[1] Git Add (0 MP) 普通攻击", id="skill-git_add", classes="skill-button"),
            Button("[2] Git Commit (20 MP) 强力攻击", id="skill-git_commit", classes="skill-button"),
            Button("[3] Git Push (15 MP) 远程攻击", id="skill-git_push", classes="skill-button"),
            Button("[4] Git Pull (10 MP) 恢复HP", id="skill-git_pull", classes="skill-button"),
            Button("[5] Git Stash (10 MP) 护盾", id="skill-git_stash", classes="skill-button"),
            Button("[6] Git Reset (25 MP) 清除debuff", id="skill-git_reset", classes="skill-button"),
            classes="skill-area",
        )

        # Combat log
        yield self._combat_log

        # Action buttons
        yield Container(
            Button("物品 [i]", id="btn-inventory", classes="action-button"),
            Button("保存 [s]", id="btn-save", classes="action-button"),
            Button("暂停 [p]", id="btn-pause", classes="action-button"),
            Button("退出 [q]", id="btn-quit", classes="action-button"),
            classes="action-area",
        )

    def add_log_message(self, message: str) -> None:
        """Add a message to the combat log."""
        self._combat_log.add_message(message)

    def update_player_stats(
        self, hp: int, max_hp: int, mp: int, max_mp: int, attack: int, defense: int
    ) -> None:
        """Update player stats display."""
        panel = self.query_one("#player-panel", CharacterPanel)
        panel.update_stats(hp=hp, mp=mp, attack=attack, defense=defense)

    def update_enemy_stats(self, hp: int, max_hp: int, attack: int, defense: int) -> None:
        """Update enemy stats display."""
        panel = self.query_one("#enemy-panel", CharacterPanel)
        panel.update_stats(hp=hp, attack=attack, defense=defense)
