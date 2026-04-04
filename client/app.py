"""Textual TUI application for dice roller client - with local state management."""

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
from client.service import LocalGameService

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
        Binding("up", "history_prev", "Previous", show=False),
        Binding("down", "history_next", "Next", show=False),
    ]

    def __init__(self, server_url: str, room_id: str, player_name: str):
        super().__init__()
        self.server_url = server_url
        self.room_id = room_id
        self.player_name = player_name
        self.client = None
        self.connected = False
        self.local_player_id = None
        self.game_service = LocalGameService()  # Local state management
        
        # Command history
        self.command_history: list[str] = []
        self.history_index: int = -1

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
            
            # Register local player
            player = self.game_service.register_player(self.room_id, self.player_name)
            if player:
                self.local_player_id = player.client_id
                self.game_service.set_local_player(player.client_id)
                logger.info(f"Local player registered: {player.client_id}")
            
            log_view.write("[dim]Commands:[/dim]")
            log_view.write("[dim]/r d20 - Roll a d20[/dim]")
            log_view.write("[dim]/r 2d6+1 attack goblin - Roll 2d6+1 with intent[/dim]")
            log_view.write("")
            log_view.write("[dim]Shortcuts:[/dim]")
            log_view.write("[dim]UP/DOWN - Navigate command history[/dim]")
            log_view.write("[dim]CTRL+C - Quit[/dim]")
        else:
            self.connected = False
            status.update("[red]Connection failed[/red]")
            log_view.write("[red]Failed to connect to server[/red]")

        input_field.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        if not self.connected or not self.local_player_id:
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

        # Add to history
        self.command_history.append(text)
        self.history_index = -1  # Reset to current (not in history)

        # Generate roll locally and send event to server
        roll_event = self.game_service.roll_dice(self.room_id, self.local_player_id, expr, intent)
        
        if roll_event:
            # Send event to server relay
            asyncio.create_task(self.client.send_event(roll_event.to_dict()))
            # Display locally
            rendered = EventRenderer.render_event(roll_event.to_dict())
            log_view.write(rendered)
        else:
            log_view.write("[red]Invalid dice expression[/red]")

        input_field.clear()

    def _on_server_message(self, message: dict[str, Any]) -> None:
        """Handle incoming server message."""
        log_view = self.query_one("#log-view", RichLog)

        msg_type = message.get("type")

        if msg_type == "event":
            event_dict = message.get("event", {})
            # Process in local service (updates local state)
            self.game_service.process_event(self.room_id, event_dict)
            # Display
            rendered = EventRenderer.render_event(event_dict)
            log_view.write(rendered)

        elif msg_type == "player_joined":
            player_name = message.get("player_name", "Unknown")
            log_view.write(f"[blue]{player_name} joined the game[/blue]")

        elif msg_type == "error":
            error_msg = message.get("message", "Unknown error")
            log_view.write(f"[red][ERROR] {error_msg}[/red]")

    def action_history_prev(self) -> None:
        """Navigate to previous command in history (UP arrow)."""
        if not self.command_history:
            return
        
        input_field = self.query_one("#input-field", Input)
        
        # Move to previous
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            cmd = self.command_history[-(self.history_index + 1)]
            input_field.value = cmd
            # Move cursor to end
            input_field.cursor_position = len(cmd)

    def action_history_next(self) -> None:
        """Navigate to next command in history (DOWN arrow)."""
        if not self.command_history or self.history_index <= 0:
            # Clear input
            input_field = self.query_one("#input-field", Input)
            input_field.value = ""
            self.history_index = -1
            return
        
        input_field = self.query_one("#input-field", Input)
        
        # Move to next (towards current)
        self.history_index -= 1
        if self.history_index >= 0:
            cmd = self.command_history[-(self.history_index + 1)]
            input_field.value = cmd
            input_field.cursor_position = len(cmd)
        else:
            input_field.value = ""

    async def action_quit(self) -> None:
        """Quit the application."""
        if self.client:
            await self.client.disconnect()
        self.exit()
