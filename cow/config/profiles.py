# cow/config/profiles.py
"""User presets for progressive automation (AD-13).

Level 1: Full interactive selection (no defaults).
Level 2: Type-based defaults — user approves batch.
Level 3: Auto-apply — user reviews final output only.

Profile data stored as JSON in ~/.cow/profiles.json.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("cow.config.profiles")

DEFAULT_PROFILE_PATH = Path.home() / ".cow" / "profiles.json"


@dataclass
class UserProfile:
    """User profile for progressive automation.

    Attributes:
        path: Path to profile JSON file.
        defaults: Per-problem-type default settings.
        automation_level: Current automation level (1, 2, or 3).
    """
    path: Path = DEFAULT_PROFILE_PATH
    defaults: dict = field(default_factory=dict)
    automation_level: int = 1

    def load(self) -> None:
        """Load profile from disk."""
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.defaults = data.get("defaults", {})
            self.automation_level = data.get("automation_level", 1)

    def save(self) -> None:
        """Save profile to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "defaults": self.defaults,
            "automation_level": self.automation_level,
        }
        self.path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def get_defaults(self, problem_type: str) -> dict:
        """Return stored defaults for a problem type.

        Args:
            problem_type: e.g., "text_only", "with_diagram", "multi_column".

        Returns:
            Dict of default settings, or empty dict if none stored.
        """
        return self.defaults.get(problem_type, {})

    def save_selection(self, problem_type: str, selection: dict) -> None:
        """Record user selection for future default inference.

        Args:
            problem_type: Problem category.
            selection: User's chosen settings (ocr_method, model params, etc.).
        """
        self.defaults[problem_type] = selection
        self.save()
        logger.info(f"Saved defaults for '{problem_type}': {selection}")
