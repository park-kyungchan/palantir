"""
Orion ODA v4.0 - LLM Action Adapter Layer

LLM-Agnostic Governance Layer for ODA Action execution.
All adapters implement the same LLMActionAdapter Protocol, ensuring
that action execution works identically regardless of LLM backend.

Supported Adapters:
- ClaudeActionAdapter: Claude Code CLI-native (no API needed)
- GeminiActionAdapter: Antigravity backend (Gemini via OpenAI-compatible API)
- OpenAIActionAdapter: Direct OpenAI API integration

Design Principles:
1. Single Interface: All adapters implement LLMActionAdapter Protocol
2. No LLM-Specific Branching: Caller code never checks LLM type
3. Action-Context Integration: Full ActionContext/ActionResult support
4. Type Safety: Complete type hints throughout
"""
from __future__ import annotations

from .base import (
    LLMActionAdapter,
    ActionExecutionError,
    ActionValidationError,
    AdapterCapabilities,
)
from .claude_adapter import ClaudeActionAdapter
from .factory import build_action_adapter
from .gemini_adapter import GeminiActionAdapter
from .openai_adapter import OpenAIActionAdapter

__all__ = [
    # Protocol and base types
    "LLMActionAdapter",
    "ActionExecutionError",
    "ActionValidationError",
    "AdapterCapabilities",
    "build_action_adapter",
    # Concrete adapters
    "ClaudeActionAdapter",
    "GeminiActionAdapter",
    "OpenAIActionAdapter",
]
