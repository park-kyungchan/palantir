"""
Orion ODA v3.0 - LLM Provider Abstraction Layer

LLM-Agnostic provider system supporting:
- Claude Code (native CLI integration - no API needed, AIP-Free)
- Antigravity (Gemini backend via OpenAI-compatible API)
- OpenAI (direct OpenAI API, also used for Codex)

This module ensures that the ODA system works identically regardless
of which LLM backend is used. All providers implement the same Protocol.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

import instructor
from openai import OpenAI

from lib.oda.llm.config import LLMBackendConfig, LLMProviderType, load_llm_config

logger = logging.getLogger(__name__)


@runtime_checkable
class LLMProvider(Protocol):
    """
    Protocol for LLM providers.

    All LLM providers must implement this protocol to ensure
    consistent behavior across different backends.
    """
    name: str

    def build_client(self) -> Optional[OpenAI]:
        """Build and return an OpenAI-compatible client, or None for CLI-native."""
        ...

    def default_model(self) -> str:
        """Return the default model for this provider."""
        ...

    def is_available(self) -> bool:
        """Check if this provider is currently available."""
        ...

    def provider_type(self) -> LLMProviderType:
        """Return the provider type enum."""
        ...


@dataclass(frozen=True)
class OpenAICompatibleProvider:
    """
    Provider for OpenAI-compatible APIs.

    Works with:
    - OpenAI API directly
    - Codex (OpenAI-compatible)
    - Any other OpenAI-compatible endpoint
    """
    config: LLMBackendConfig
    name: str = "openai-compatible"

    def build_client(self) -> OpenAI:
        return OpenAI(base_url=self.config.base_url, api_key=self.config.api_key)

    def default_model(self) -> str:
        return self.config.model

    def is_available(self) -> bool:
        """Check if the API endpoint is reachable."""
        try:
            client = self.build_client()
            client.models.list()
            return True
        except Exception as e:
            logger.debug(f"Provider {self.name} not available: {e}")
            return False

    def provider_type(self) -> LLMProviderType:
        return LLMProviderType.OPENAI


@dataclass(frozen=True)
class AntigravityProvider(OpenAICompatibleProvider):
    """Provider for Antigravity (Gemini) backend."""
    name: str = "antigravity"

    def provider_type(self) -> LLMProviderType:
        return LLMProviderType.ANTIGRAVITY


@dataclass(frozen=True)
class ClaudeCodeProvider:
    """
    Provider for Claude Code CLI-native integration.

    This provider does NOT use an API - it leverages the fact that
    we're already running inside Claude Code CLI. Operations are
    performed through Claude Code's native capabilities.

    No API key or base_url needed.
    """
    config: LLMBackendConfig
    name: str = "claude-code"

    def build_client(self) -> None:
        """
        Claude Code doesn't use a client - operations are CLI-native.

        Returns None to indicate CLI-native operation.
        """
        return None

    def default_model(self) -> str:
        return self.config.model or "claude-opus-4-5-20251101"

    def is_available(self) -> bool:
        """
        Check if running in Claude Code environment.

        Claude Code is always available when running inside the CLI.
        """
        import os
        # Check for Claude Code environment indicators
        return bool(
            os.environ.get("CLAUDE_CODE") or
            os.environ.get("CLAUDE_CODE_SESSION") or
            os.environ.get("CLAUDE_SESSION_ID")
        )

    def provider_type(self) -> LLMProviderType:
        return LLMProviderType.CLAUDE_CODE

    def is_cli_native(self) -> bool:
        """Indicate this provider uses CLI-native operations."""
        return True


# =============================================================================
# PROVIDER REGISTRY
# =============================================================================

class ProviderRegistry:
    """
    Registry for managing LLM providers with runtime switching.

    Provides:
    - Provider registration and lookup
    - Health checks
    - Fallback chain support
    """

    _providers: Dict[LLMProviderType, LLMProvider] = {}
    _default_provider: Optional[LLMProviderType] = None

    @classmethod
    def register(cls, provider: LLMProvider) -> None:
        """Register a provider instance."""
        cls._providers[provider.provider_type()] = provider

    @classmethod
    def get(cls, provider_type: LLMProviderType) -> Optional[LLMProvider]:
        """Get a registered provider by type."""
        return cls._providers.get(provider_type)

    @classmethod
    def get_default(cls) -> Optional[LLMProvider]:
        """Get the default provider."""
        if cls._default_provider:
            return cls._providers.get(cls._default_provider)
        # Return first available provider
        for provider in cls._providers.values():
            if provider.is_available():
                return provider
        return None

    @classmethod
    def set_default(cls, provider_type: LLMProviderType) -> None:
        """Set the default provider type."""
        cls._default_provider = provider_type

    @classmethod
    def list_available(cls) -> List[LLMProviderType]:
        """List all available providers."""
        return [
            pt for pt, p in cls._providers.items()
            if p.is_available()
        ]

    @classmethod
    def health_check(cls) -> Dict[LLMProviderType, bool]:
        """Check health of all registered providers."""
        return {
            pt: p.is_available()
            for pt, p in cls._providers.items()
        }


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def build_provider(config: LLMBackendConfig | None = None) -> LLMProvider:
    """
    Build and return the appropriate LLM provider.

    Args:
        config: Optional configuration. If not provided, loads from environment.

    Returns:
        LLMProvider instance based on configuration.

    Provider Selection:
    - CLAUDE_CODE: CLI-native (AIP-Free, default)
    - ANTIGRAVITY: Gemini backend
    - OPENAI: OpenAI-compatible (includes Codex)
    """
    resolved = config or load_llm_config()
    provider_type = resolved.provider_type

    if provider_type == LLMProviderType.CLAUDE_CODE:
        provider = ClaudeCodeProvider(resolved)
    elif provider_type == LLMProviderType.ANTIGRAVITY:
        provider = AntigravityProvider(resolved)
    else:  # OpenAI-compatible (includes Codex)
        provider = OpenAICompatibleProvider(resolved)

    # Register the provider
    ProviderRegistry.register(provider)

    return provider


def build_instructor_client(provider: LLMProvider) -> Optional[OpenAI]:
    """
    Build an Instructor-patched client for structured output.

    Args:
        provider: LLM provider instance

    Returns:
        Instructor-patched OpenAI client, or None for CLI-native providers
    """
    client = provider.build_client()
    if client is None:
        # CLI-native provider (Claude Code)
        logger.info(f"Provider {provider.name} is CLI-native, no Instructor client needed")
        return None

    return instructor.patch(
        client,
        mode=instructor.Mode.JSON,
    )


def get_current_provider() -> LLMProvider:
    """
    Get the current LLM provider based on environment.

    Convenience function that builds and returns the configured provider.
    """
    return build_provider()
