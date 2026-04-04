"""Dice rolling logic and expression parser."""

import re
from typing import NamedTuple
import random


class DiceRoll(NamedTuple):
    """Result of a dice roll."""

    expr: str
    rolls: list[int]
    modifier: int
    total: int


class DiceParser:
    """Parse and validate dice expressions like 'd20', '2d6+1', '3d8-2'."""

    # Pattern: [count]d<sides>[+/-modifier]
    PATTERN = r"^(\d+)?d(\d+)([\+\-])?((\d+))?$"
    MAX_DICE = 100

    @staticmethod
    def parse(expr: str) -> tuple[int, int, int] | None:
        """
        Parse a dice expression.

        Returns: (num_dice, sides, modifier) or None if invalid.
        """
        expr = expr.strip().lower()
        match = re.match(DiceParser.PATTERN, expr)

        if not match:
            return None

        num_dice = int(match.group(1) or 1)
        sides = int(match.group(2))
        op = match.group(3) or "+"
        modifier = int(match.group(5) or 0)

        if op == "-":
            modifier = -modifier

        if num_dice < 1 or num_dice > DiceParser.MAX_DICE:
            return None

        if sides < 1:
            return None

        return (num_dice, sides, modifier)

    @staticmethod
    def roll(expr: str) -> DiceRoll | None:
        """
        Roll dice according to expression.

        Returns: DiceRoll or None if expression is invalid.
        """
        parsed = DiceParser.parse(expr)
        if not parsed:
            return None

        num_dice, sides, modifier = parsed
        rolls = [random.randint(1, sides) for _ in range(num_dice)]
        base_total = sum(rolls)
        total = base_total + modifier

        return DiceRoll(
            expr=expr,
            rolls=rolls,
            modifier=modifier,
            total=total,
        )
