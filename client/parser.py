"""Command parser for dice roller client."""

import re


class CommandParser:
    """Parse commands in the format: /r <expr> <intent>"""

    @staticmethod
    def parse_roll_command(text: str) -> tuple[str | None, str]:
        """
        Parse a roll command.

        Format: /r d20 [intent text...]

        Returns: (expr, intent) or (None, "") if invalid
        """
        text = text.strip()

        if not text.startswith("/r "):
            return None, ""

        # Remove /r prefix and split on first space
        rest = text[3:].strip()

        parts = rest.split(None, 1)
        if not parts:
            return None, ""

        expr = parts[0]
        intent = parts[1] if len(parts) > 1 else ""

        return expr, intent

    @staticmethod
    def is_roll_command(text: str) -> bool:
        """Check if text is a roll command."""
        return text.strip().startswith("/r ")
