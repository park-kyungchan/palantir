from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import instructor
from openai import OpenAI

from scripts.llm.config import LLMBackendConfig, load_llm_config


class LLMProvider(Protocol):
    name: str

    def build_client(self) -> OpenAI:
        ...

    def default_model(self) -> str:
        ...


@dataclass(frozen=True)
class OpenAICompatibleProvider:
    config: LLMBackendConfig
    name: str = "openai-compatible"

    def build_client(self) -> OpenAI:
        return OpenAI(base_url=self.config.base_url, api_key=self.config.api_key)

    def default_model(self) -> str:
        return self.config.model


@dataclass(frozen=True)
class AntigravityProvider(OpenAICompatibleProvider):
    name: str = "antigravity"


def build_provider(config: LLMBackendConfig | None = None) -> LLMProvider:
    resolved = config or load_llm_config()
    if resolved.provider == "antigravity":
        return AntigravityProvider(resolved)
    return OpenAICompatibleProvider(resolved)


def build_instructor_client(provider: LLMProvider) -> OpenAI:
    return instructor.patch(
        provider.build_client(),
        mode=instructor.Mode.JSON,
    )
