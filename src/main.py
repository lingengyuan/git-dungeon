"""Main entry point for Git Dungeon."""

import sys
from pathlib import Path
from typing import Optional, Callable

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Static, Input, Button
from textual.screen import Screen
from textual import events

from .config import load_config, GameConfig
from .core.game_engine import GameState
from .utils.logger import setup_logger

logger = setup_logger(__name__)


class GameScreen(Static):
    """Main game screen."""

    def compose(self) -> ComposeResult:
        """Compose the game UI."""
        yield Header(show_clock=True)
        yield Container(
            Static("Git Dungeon", id="title"),
            Static("Press 'l' to load a repository", id="instructions"),
            Static("", id="status"),  # 显示当前状态
            Static("", id="progress"),  # 显示进度
            id="game-container",
        )
        yield Footer()


class InputScreen(Screen):
    """Input screen for repository path."""

    def __init__(self, prompt: str = "Enter repository path:", on_submit: Optional[Callable] = None, on_cancel: Optional[Callable] = None):
        """Initialize the input screen.

        Args:
            prompt: Prompt text
            on_submit: Callback when submitted
            on_cancel: Callback when cancelled
        """
        super().__init__()
        self._prompt = prompt
        self._on_submit = on_submit
        self._on_cancel = on_cancel

    def compose(self) -> ComposeResult:
        """Compose the input screen."""
        yield Container(
            Static(self._prompt, id="prompt"),
            Input(placeholder="/path/to/repo", id="path_input"),
            Button("OK", id="ok", variant="primary"),
            Button("Cancel", id="cancel"),
            id="input-container",
        )

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        self.query_one("#path_input").focus()

    def on_button_clicked(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "ok":
            path = self.query_one("#path_input").value
            if path and self._on_submit:
                self._on_submit(path)
        elif event.button.id == "cancel":
            if self._on_cancel:
                self._on_cancel()
        self.pop()


class GitDungeonApp(App):
    """Main Textual application."""

    CSS = """
    Screen {
        background: $background;
    }
    #title {
        content-align: center middle;
        text-style: bold;
        color: $accent;
        height: 3;
    }
    #instructions {
        content-align: center middle;
        color: $text-muted;
    }
    #status {
        content-align: center middle;
        color: $success;
        height: 1;
    }
    #progress {
        content-align: center middle;
        color: $text-muted;
        height: 1;
    }
    #game-container {
        align: center middle;
    }
    #input-container {
        align: center middle;
        width: 60;
        height: 12;
    }
    #input-container #prompt {
        width: 100%;
        content-align: center middle;
        margin: 1 0;
    }
    #input-container Input {
        width: 100%;
        margin: 1 0;
    }
    #input-container Button {
        width: 20;
        margin: 0 1;
    }
    #input-container .buttons {
        align: center middle;
        height: 3;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("l", "load_repo", "Load Repository"),
        ("s", "save", "Save Game"),
        ("p", "pause", "Pause"),
    ]

    def __init__(self, config: Optional[GameConfig] = None):
        """Initialize the app.

        Args:
            config: Game configuration
        """
        super().__init__()
        self.config = config or load_config()
        self.game_state = GameState(config=self.config)
        self._repo_loaded = False

    def compose(self) -> ComposeResult:
        """Compose the app."""
        yield GameScreen()

    def _update_status(self) -> None:
        """Update status display."""
        status = self.query_one("#status")
        progress = self.query_one("#progress")

        if self._repo_loaded:
            commits = len(self.game_state.commits)
            defeated = len(self.game_state.defeated_commits)
            status.update(f"Loaded: {self.game_state.config.repo_path}")
            progress.update(f"Progress: {defeated}/{commits} commits defeated")
        else:
            status.update("")
            progress.update("")

    def action_load_repo(self) -> None:
        """Load a Git repository - show input screen."""
        def on_submit(path: str) -> None:
            """Handle path input submission."""
            if path:
                if self.game_state.load_repository(path):
                    self._repo_loaded = True
                    self.notify(f"Loaded {len(self.game_state.commits)} commits", severity="success")
                    self._update_status()
                else:
                    self.notify(f"Failed to load: {path}", severity="error")

        def on_cancel() -> None:
            """Handle cancel."""
            pass

        self.push_screen(
            InputScreen(
                prompt="Enter repository path:",
                on_submit=on_submit,
                on_cancel=on_cancel,
            )
        )

    def action_save(self) -> None:
        """Save the game."""
        from src.core.save_system import SaveSystem
        from pathlib import Path
        import tempfile

        save_dir = Path(tempfile.gettempdir()) / "git-dungeon-saves"
        save_system = SaveSystem(save_dir)

        if save_system.save(self.game_state, 0):
            self.notify(f"Game saved to {save_dir}", severity="success")
        else:
            self.notify("Failed to save game", severity="error")

    def action_pause(self) -> None:
        """Pause the game."""
        if self.game_state.is_paused:
            self.game_state.resume()
            self.notify("Game resumed")
        else:
            self.game_state.pause()
            self.notify("Game paused")


def main():
    """Main entry point."""
    app = GitDungeonApp()
    app.run()


if __name__ == "__main__":
    main()
