"""Event rendering for TUI display."""

from typing import Any


class EventRenderer:
    """Format events for display in the TUI."""

    @staticmethod
    def render_event(event: dict[str, Any]) -> str:
        """Render an event as a human-readable string."""
        event_type = event.get("type")

        if event_type == "roll":
            return EventRenderer._render_roll(event)
        elif event_type == "error":
            return EventRenderer._render_error(event)
        else:
            return f"[{event_type}] {event}"

    @staticmethod
    def _render_roll(event: dict[str, Any]) -> str:
        """Render a roll event."""
        payload = event.get("payload", {})
        player = payload.get("player", {})
        dice = payload.get("dice", {})
        fiction = payload.get("fiction", {})

        player_name = player.get("name", "Unknown")
        expr = dice.get("expr", "?")
        rolls = dice.get("rolls", [])
        modifier = dice.get("modifier", 0)
        total = dice.get("total", 0)
        intent = fiction.get("intent", "")

        # Format rolls list
        rolls_str = ", ".join(str(r) for r in rolls)

        # Build the message
        msg = f"{player_name} rolled {expr} [{rolls_str}]"

        if modifier != 0:
            op = "+" if modifier > 0 else ""
            msg += f" {op}{modifier}"

        msg += f" = {total}"

        if intent:
            msg += f" ({intent})"

        return msg

    @staticmethod
    def _render_error(event: dict[str, Any]) -> str:
        """Render an error event."""
        message = event.get("message", "Unknown error")
        return f"[ERROR] {message}"
