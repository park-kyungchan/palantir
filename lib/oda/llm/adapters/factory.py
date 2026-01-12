"""
LLM Action Adapter Factory

Centralizes adapter selection so callers don't branch on provider type.
"""

from __future__ import annotations

from lib.oda.llm.adapters.base import LLMActionAdapter
from lib.oda.llm.config import LLMBackendConfig, LLMProviderType, load_llm_config
from lib.oda.llm.providers import (
    AntigravityProvider,
    ClaudeCodeProvider,
    LLMProvider,
    OpenAICompatibleProvider,
    build_provider,
)

from lib.oda.llm.adapters.claude_adapter import ClaudeActionAdapter
from lib.oda.llm.adapters.gemini_adapter import GeminiActionAdapter
from lib.oda.llm.adapters.openai_adapter import OpenAIActionAdapter


def build_action_adapter(
    provider: LLMProvider | None = None,
    *,
    config: LLMBackendConfig | None = None,
) -> LLMActionAdapter:
    resolved_provider = provider or build_provider(config or load_llm_config())

    provider_type = resolved_provider.provider_type()
    if provider_type == LLMProviderType.CLAUDE_CODE:
        if not isinstance(resolved_provider, ClaudeCodeProvider):
            raise ValueError(
                "Provider type mismatch: expected ClaudeCodeProvider, "
                f"got {type(resolved_provider).__name__}"
            )
        return ClaudeActionAdapter(resolved_provider)

    if provider_type == LLMProviderType.ANTIGRAVITY:
        if not isinstance(resolved_provider, AntigravityProvider):
            raise ValueError(
                "Provider type mismatch: expected AntigravityProvider, "
                f"got {type(resolved_provider).__name__}"
            )
        return GeminiActionAdapter(resolved_provider)

    if not isinstance(resolved_provider, OpenAICompatibleProvider):
        raise ValueError(
            "Provider type mismatch: expected OpenAICompatibleProvider, "
            f"got {type(resolved_provider).__name__}"
        )

    return OpenAIActionAdapter(resolved_provider)

