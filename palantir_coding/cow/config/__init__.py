# cow/config/__init__.py
"""COW Pipeline v2.0 — Configuration and model management."""

from cow.config.models import ModelConfig, ModelUnavailableError
from cow.config.profiles import UserProfile

__all__ = ["ModelConfig", "ModelUnavailableError", "UserProfile"]
