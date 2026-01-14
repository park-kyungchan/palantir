"""
Orion ODA v4.0 - OpenAI Intent Adapter

OpenAI/GPT-4 intent classification adapter.
Uses function calling for structured output.
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


OPENAI_INTENT_PROMPT = """You are an intent classifier for a development assistant.

## Available Commands
{commands}

## User Request
"{user_input}"

## Task
Classify this request into ONE of the available commands.
Return a JSON object with command, confidence (0.0-1.0), and reasoning.

If the request doesn't match any command, use "none".
"""


class OpenAIIntentAdapter(BaseIntentAdapter):
    """
    OpenAI/GPT-4 Intent Adapter.

    Uses OpenAI API with function calling for structured output.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        base_url: Optional[str] = None
    ):
        """
        Initialize OpenAI Intent Adapter.

        Args:
            api_key: OpenAI API key (reads from env if not provided)
            model: Model to use (default: gpt-4o)
            base_url: Custom base URL for API-compatible endpoints
        """
        super().__init__()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.base_url = base_url
        self._client = None

        if self.api_key:
            try:
                import openai
                kwargs = {"api_key": self.api_key}
                if base_url:
                    kwargs["base_url"] = base_url
                self._client = openai.OpenAI(**kwargs)
            except ImportError:
                logger.warning("openai package not installed")

    @property
    def name(self) -> str:
        return "openai-intent-adapter"

    def is_available(self) -> bool:
        return self._client is not None

    async def _classify_impl(
        self,
        user_input: str,
        available_commands: List[CommandDescription]
    ) -> IntentResult:
        """Classify intent using OpenAI."""
        if not self._client:
            return IntentResult(
                command="none",
                confidence=0.0,
                reasoning="OpenAI client not available",
                match_type=IntentMatchType.FALLBACK,
                raw_input=user_input
            )

        try:
            # Build function schema for structured output
            function_schema = {
                "name": "classify_intent",
                "description": "Classify user intent into a command",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The matched command (e.g., /ask, /plan, /audit, none)"
                        },
                        "confidence": {
                            "type": "number",
                            "description": "Confidence score between 0.0 and 1.0"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Brief explanation for the classification"
                        }
                    },
                    "required": ["command", "confidence", "reasoning"]
                }
            }

            prompt = OPENAI_INTENT_PROMPT.format(
                commands=format_commands_for_prompt(available_commands),
                user_input=user_input
            )

            response = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                tools=[{"type": "function", "function": function_schema}],
                tool_choice={"type": "function", "function": {"name": "classify_intent"}}
            )

            # Extract function call result
            tool_call = response.choices[0].message.tool_calls[0]
            result_data = json.loads(tool_call.function.arguments)

            return IntentResult(
                command=result_data.get("command", "none"),
                confidence=float(result_data.get("confidence", 0.5)),
                reasoning=result_data.get("reasoning", ""),
                match_type=IntentMatchType.SEMANTIC,
                raw_input=user_input
            )

        except Exception as e:
            logger.error(f"OpenAI classification error: {e}")
            return IntentResult(
                command="none",
                confidence=0.0,
                reasoning=f"API error: {str(e)}",
                match_type=IntentMatchType.FALLBACK,
                raw_input=user_input
            )


def create_openai_intent_adapter(
    api_key: Optional[str] = None,
    model: str = "gpt-4o"
) -> OpenAIIntentAdapter:
    """Factory function for OpenAI Intent Adapter."""
    return OpenAIIntentAdapter(api_key=api_key, model=model)
