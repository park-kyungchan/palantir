"""
Orion ODA v4.0 - Local LLM Intent Adapter

Local LLM intent classification adapter.
Supports Ollama, LM Studio, and other local inference servers.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from lib.oda.llm.intent_adapter import (
    BaseIntentAdapter,
    CommandDescription,
    IntentMatchType,
    IntentResult,
    format_commands_for_prompt,
)

logger = logging.getLogger(__name__)


LOCAL_INTENT_PROMPT = """You are an intent classifier. Classify the user request into one command.

Commands:
{commands}

User: "{user_input}"

Reply with JSON only: {{"command": "/ask", "confidence": 0.9, "reasoning": "why"}}
JSON:"""


class LocalIntentAdapter(BaseIntentAdapter):
    """
    Local LLM Intent Adapter.

    Supports:
    - Ollama (default)
    - LM Studio
    - Any OpenAI-compatible local server
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        model: str = "llama3.2",
        api_key: str = "ollama"  # Ollama doesn't require real key
    ):
        """
        Initialize Local LLM Intent Adapter.

        Args:
            base_url: Local server URL (default: Ollama)
            model: Model name (default: llama3.2)
            api_key: API key (default: "ollama" for Ollama)
        """
        super().__init__()
        self.base_url = base_url
        self.model = model
        self.api_key = api_key
        self._client = None

        try:
            import openai
            self._client = openai.OpenAI(
                api_key=api_key,
                base_url=base_url
            )
        except ImportError:
            logger.warning("openai package not installed")

    @property
    def name(self) -> str:
        return "local-intent-adapter"

    def is_available(self) -> bool:
        """Check if local server is available."""
        if not self._client:
            return False

        try:
            # Quick health check
            self._client.models.list()
            return True
        except Exception:
            return False

    async def _classify_impl(
        self,
        user_input: str,
        available_commands: List[CommandDescription]
    ) -> IntentResult:
        """Classify intent using local LLM."""
        if not self._client:
            return IntentResult(
                command="none",
                confidence=0.0,
                reasoning="Local LLM client not available",
                match_type=IntentMatchType.FALLBACK,
                raw_input=user_input
            )

        prompt = LOCAL_INTENT_PROMPT.format(
            commands=format_commands_for_prompt(available_commands),
            user_input=user_input
        )

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=128,
                temperature=0.1  # Low temperature for consistent classification
            )

            content = response.choices[0].message.content
            return self._parse_response(content, user_input)

        except Exception as e:
            logger.error(f"Local LLM error: {e}")
            return IntentResult(
                command="none",
                confidence=0.0,
                reasoning=f"Local LLM error: {str(e)}",
                match_type=IntentMatchType.FALLBACK,
                raw_input=user_input
            )

    def _parse_response(self, response: str, user_input: str) -> IntentResult:
        """Parse local LLM response into IntentResult."""
        try:
            json_match = re.search(r'\{[^{}]+\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return IntentResult(
                    command=data.get("command", "none"),
                    confidence=float(data.get("confidence", 0.5)),
                    reasoning=data.get("reasoning", ""),
                    match_type=IntentMatchType.SEMANTIC,
                    raw_input=user_input
                )
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse local LLM response: {e}")

        return IntentResult(
            command="none",
            confidence=0.3,
            reasoning=f"Parse error: {response[:100]}",
            match_type=IntentMatchType.FALLBACK,
            raw_input=user_input
        )


def create_local_intent_adapter(
    base_url: str = "http://localhost:11434/v1",
    model: str = "llama3.2"
) -> LocalIntentAdapter:
    """Factory function for Local LLM Intent Adapter."""
    return LocalIntentAdapter(base_url=base_url, model=model)


# Convenience aliases
OllamaIntentAdapter = LocalIntentAdapter
LMStudioIntentAdapter = LocalIntentAdapter
