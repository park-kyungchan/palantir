"""
ODA PAI Algorithm - Effort Levels
=================================

Defines the EffortLevel enum that controls algorithm behavior.
Effort levels determine which capabilities are unlocked for task execution.

Hierarchy (ascending):
    TRIVIAL < QUICK < STANDARD < THOROUGH < DETERMINED

Migrated from: PAI/Packs/pai-algorithm-skill/src/skills/THEALGORITHM/Data/Capabilities.yaml
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List


class EffortLevel(str, Enum):
    """
    Effort levels for THE ALGORITHM.

    Each level unlocks progressively more powerful capabilities:

    - TRIVIAL: Skip algorithm, direct response
    - QUICK: Single-step, fast execution (haiku, intern)
    - STANDARD: Multi-step bounded work (sonnet, researchers, engineer)
    - THOROUGH: Complex, multi-file work (council, plan_mode, architect)
    - DETERMINED: Mission-critical, unlimited iteration (opus, redteam)
    """

    TRIVIAL = "TRIVIAL"
    QUICK = "QUICK"
    STANDARD = "STANDARD"
    THOROUGH = "THOROUGH"
    DETERMINED = "DETERMINED"

    @property
    def rank(self) -> int:
        """
        Get the numeric rank of this effort level.

        Used for comparisons between effort levels.
        Higher rank means more effort/resources available.
        """
        ranks = {
            EffortLevel.TRIVIAL: 0,
            EffortLevel.QUICK: 1,
            EffortLevel.STANDARD: 2,
            EffortLevel.THOROUGH: 3,
            EffortLevel.DETERMINED: 4,
        }
        return ranks[self]

    def __lt__(self, other: "EffortLevel") -> bool:
        if not isinstance(other, EffortLevel):
            return NotImplemented
        return self.rank < other.rank

    def __le__(self, other: "EffortLevel") -> bool:
        if not isinstance(other, EffortLevel):
            return NotImplemented
        return self.rank <= other.rank

    def __gt__(self, other: "EffortLevel") -> bool:
        if not isinstance(other, EffortLevel):
            return NotImplemented
        return self.rank > other.rank

    def __ge__(self, other: "EffortLevel") -> bool:
        if not isinstance(other, EffortLevel):
            return NotImplemented
        return self.rank >= other.rank

    @property
    def description(self) -> str:
        """Human-readable description of this effort level."""
        descriptions = {
            EffortLevel.TRIVIAL: "Skip algorithm, direct response",
            EffortLevel.QUICK: "Single-step, fast execution",
            EffortLevel.STANDARD: "Multi-step bounded work",
            EffortLevel.THOROUGH: "Complex, multi-file work",
            EffortLevel.DETERMINED: "Mission-critical, unlimited iteration",
        }
        return descriptions[self]

    @property
    def max_concurrent(self) -> int:
        """
        Maximum concurrent parallel executions allowed at this effort level.

        Returns:
            Number of parallel tasks allowed (1-10)
        """
        concurrency = {
            EffortLevel.TRIVIAL: 1,
            EffortLevel.QUICK: 1,
            EffortLevel.STANDARD: 3,
            EffortLevel.THOROUGH: 5,
            EffortLevel.DETERMINED: 10,
        }
        return concurrency[self]

    @classmethod
    def from_string(cls, value: str) -> "EffortLevel":
        """
        Parse an effort level from a string.

        Args:
            value: String representation (case-insensitive)

        Returns:
            The corresponding EffortLevel

        Raises:
            ValueError: If the value is not a valid effort level
        """
        try:
            return cls(value.upper())
        except ValueError:
            valid_values = [e.value for e in cls]
            raise ValueError(
                f"Invalid effort level: '{value}'. "
                f"Valid values: {valid_values}"
            )

    @classmethod
    def default(cls) -> "EffortLevel":
        """Return the default effort level (STANDARD)."""
        return cls.STANDARD

    def can_use(self, required: "EffortLevel") -> bool:
        """
        Check if this effort level can use a capability requiring a minimum level.

        Args:
            required: The minimum effort level required by a capability

        Returns:
            True if this effort level meets or exceeds the requirement
        """
        return self >= required


# Type alias for effort level dictionaries
EffortUnlocks = Dict[EffortLevel, List[str]]
