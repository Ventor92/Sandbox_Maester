"""Command parser for dice roller client."""

import re
import json
from typing import Any


class CommandParser:
    """Parse commands in the format: /r <expr> <intent> and /custom <subtype> <args|json>"""

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

    @staticmethod
    def parse_custom_command(text: str) -> tuple[str | None, dict[str, Any] | None]:
        """
        Parse a custom command.

        Format examples:
          /custom table_roll loot sword
          /custom table_roll {"table_id":"loot","choice":"sword"}

        Returns: (subtype, payload) or (None, None) if invalid
        """
        text = text.strip()
        if not text.startswith("/custom "):
            return None, None

        rest = text[len("/custom "):].strip()
        if not rest:
            return None, {}

        parts = rest.split(None, 1)
        subtype = parts[0]
        payload: dict[str, Any] = {}

        if len(parts) == 1:
            payload = {}
        else:
            remainder = parts[1].strip()
            # If remainder is JSON, parse it
            if remainder.startswith("{"):
                try:
                    payload = json.loads(remainder)
                except Exception:
                    return None, None
            else:
                # Simple space-separated args. Special-case common subtype 'table_roll'
                if subtype == "table_roll":
                    sp = remainder.split(None, 1)
                    payload = {"table_id": sp[0], "choice": sp[1] if len(sp) > 1 else ""}
                else:
                    payload = {"args": remainder}

        return subtype, payload

    @staticmethod
    def is_custom_command(text: str) -> bool:
        """Check if text is a custom command (starts with /custom)."""
        return text.strip().startswith("/custom")
