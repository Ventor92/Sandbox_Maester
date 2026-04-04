"""Textual TUI application for dice roller client."""

import asyncio
import logging
from typing import Any

from textual.app import ComposeResult, RenderableType
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Input, RichLog, Static
from textual.binding import Binding
from textual.app import App

from client.ws_client import DiceRollerClient
from client.parser import CommandParser
from client.renderer import EventRenderer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiceRollerApp(App):
    """Textual TUI application for the dice roller."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #log-view {
        border: solid $primary;
        height: 1fr;
    }

    #input-field {
        border: solid $accent;
        height: 3;
    }

    #status {
        dock: bottom;
        height: 1;
        background: $panel;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
    ]

    def __init__(self, server_url: str, room_id: str, player_name: str):
        super().__init__()
        self.server_url = server_url
        self.room_id = room_id
        self.player_name = player_name
        self.client = None
        self.connected = False

    def compose(self) -> ComposeResult:
        """Create the TUI layout."""
        yield Header()
        yield Container(
            Vertical(
                RichLog(id="log-view"),
                Input(id="input-field", placeholder="/r d20 [intent]"),
            ),
        )
        yield Static(id="status")
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the app when mounted."""
        log_view = self.query_one("#log-view", RichLog)
        input_field = self.query_one("#input-field", Input)
        status = self.query_one("#status", Static)

        log_view.write("[bold blue]ttRPG Dice Roller[/bold blue]")
        log_view.write(f"[dim]Room: {self.room_id}[/dim]")
        log_view.write(f"[dim]Player: {self.player_name}[/dim]")
        log_view.write("")
        log_view.write("[yellow]Connecting...[/yellow]")

        # Create WebSocket client
        self.client = DiceRollerClient(
            self.server_url, self._on_server_message
        )

        # Connect to server
        connected = await self.client.connect(self.room_id, self.player_name)

        if connected:
            self.connected = True
            status.update("[green]Connected[/green]")
            log_view.write("[green]Connected to server[/green]")
            log_view.write("")
            log_view.write("[dim]Commands:[/dim]")
            log_view.write("[dim]/r d20 - Roll a d20[/dim]")
            log_view.write("[dim]/r 2d6+1 attack goblin - Roll 2d6+1 with intent[/dim]")
        else:
            self.connected = False
            status.update("[red]Connection failed[/red]")
            log_view.write("[red]Failed to connect to server[/red]")

        input_field.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        if not self.connected:
            return

        text = event.value
        input_field = self.query_one("#input-field", Input)
        log_view = self.query_one("#log-view", RichLog)

        if not CommandParser.is_roll_command(text):
            log_view.write("[dim]Use /r <expr> [intent][/dim]")
            input_field.clear()
            return

        expr, intent = CommandParser.parse_roll_command(text)

        if not expr:
            log_view.write("[red]Invalid command. Use /r d20 [intent][/red]")
            input_field.clear()
            return

        # Send roll request
        asyncio.create_task(self.client.roll(expr, intent))

        input_field.clear()

    def _on_server_message(self, message: dict[str, Any]) -> None:
        """Handle incoming server message."""
        log_view = self.query_one("#log-view", RichLog)

        msg_type = message.get("type")

        if msg_type == "event":
            event = message.get("event", {})
            rendered = EventRenderer.render_event(event)
            log_view.write(rendered)

        elif msg_type == "error":
            error_msg = message.get("message", "Unknown error")
            log_view.write(f"[red][ERROR] {error_msg}[/red]")

    async def action_quit(self) -> None:
        """Quit the application."""
        if self.client:
            await self.client.disconnect()
        self.exit()
