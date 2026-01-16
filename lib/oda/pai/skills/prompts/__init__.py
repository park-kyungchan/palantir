"""
Orion ODA v4.0 - Skill Prompts

Prompt templates for LLM-based skill operations.
"""
from .intent_prompts import (
    INTENT_CLASSIFICATION_PROMPT,
    CLARIFICATION_PROMPT,
    format_commands_for_classification,
)

__all__ = [
    "INTENT_CLASSIFICATION_PROMPT",
    "CLARIFICATION_PROMPT",
    "format_commands_for_classification",
]
