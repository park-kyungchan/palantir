import pytest

from lib.oda.llm.adapters.factory import build_action_adapter
from lib.oda.llm.config import LLMBackendConfig, LLMProviderType
from lib.oda.llm.providers import (
    AntigravityProvider,
    ClaudeCodeProvider,
    OpenAICompatibleProvider,
)


def test_build_action_adapter_claude_code() -> None:
    config = LLMBackendConfig(
        provider="claude-code",
        base_url="",
        api_key="",
        model="claude-opus-4-5-20251101",
    )
    provider = ClaudeCodeProvider(config)
    adapter = build_action_adapter(provider)
    assert adapter.provider_type == LLMProviderType.CLAUDE_CODE
    assert adapter.name == "claude-code-adapter"


def test_build_action_adapter_antigravity() -> None:
    config = LLMBackendConfig(
        provider="antigravity",
        base_url="http://localhost:1234/v1",
        api_key="test",
        model="gemini-3.0-pro",
    )
    provider = AntigravityProvider(config)
    adapter = build_action_adapter(provider)
    assert adapter.provider_type == LLMProviderType.ANTIGRAVITY
    assert adapter.name == "gemini-adapter"


def test_build_action_adapter_openai() -> None:
    config = LLMBackendConfig(
        provider="openai",
        base_url="http://localhost:1234/v1",
        api_key="test",
        model="gpt-4o",
    )
    provider = OpenAICompatibleProvider(config)
    adapter = build_action_adapter(provider)
    assert adapter.provider_type == LLMProviderType.OPENAI
    assert adapter.name == "openai-adapter"

