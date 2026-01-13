"""
Orion ODA v4.0 - Gemini Intent Adapter

Google Gemini intent classification adapter.
Supports both direct Gemini API and OpenAI-compatible endpoints.
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


GEMINI_INTENT_PROMPT = """You are an intent classifier for a development assistant.

## Available Commands
{commands}

## User Request
"{user_input}"

## Task
Classify this request into ONE of the available commands.
Consider both Korean and English inputs.

## Output (JSON only)
{{"command": "/ask", "confidence": 0.95, "reasoning": "Brief explanation"}}

Return only JSON, no markdown or explanation:"""


class GeminiIntentAdapter(BaseIntentAdapter):
    """
    Google Gemini Intent Adapter.

    Supports:
    - Direct Gemini API (google-generativeai package)
    - OpenAI-compatible endpoint (Antigravity backend)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-1.5-flash",
        use_openai_compat: bool = False,
        openai_compat_base_url: Optional[str] = None
    ):
        """
        Initialize Gemini Intent Adapter.

        Args:
            api_key: Google AI API key (reads from env if not provided)
            model: Model to use (default: gemini-1.5-flash)
            use_openai_compat: Use OpenAI-compatible endpoint
            openai_compat_base_url: Base URL for OpenAI-compatible endpoint
        """
        super().__init__()
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.model = model
        self.use_openai_compat = use_openai_compat
        self.openai_compat_base_url = openai_compat_base_url
        self._client = None

        self._init_client()

    def _init_client(self):
        """Initialize the appropriate client."""
        if self.use_openai_compat:
            try:
                import openai
                self._client = openai.OpenAI(
                    api_key=self.api_key or "dummy",
                    base_url=self.openai_compat_base_url
                )
            except ImportError:
                logger.warning("openai package not installed for compat mode")
        elif self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(self.model)
            except ImportError:
                logger.warning("google-generativeai package not installed")

    @property
    def name(self) -> str:
        return "gemini-intent-adapter"

    def is_available(self) -> bool:
        return self._client is not None

    async def _classify_impl(
        self,
        user_input: str,
        available_commands: List[CommandDescription]
    ) -> IntentResult:
        """Classify intent using Gemini."""
        if not self._client:
            return IntentResult(
                command="none",
                confidence=0.0,
                reasoning="Gemini client not available",
                match_type=IntentMatchType.FALLBACK,
                raw_input=user_input
            )

        prompt = GEMINI_INTENT_PROMPT.format(
            commands=format_commands_for_prompt(available_commands),
            user_input=user_input
        )

        try:
            if self.use_openai_compat:
                return await self._classify_openai_compat(prompt, user_input)
            else:
                return await self._classify_native(prompt, user_input)

        except Exception as e:
            logger.error(f"Gemini classification error: {e}")
            return IntentResult(
                command="none",
                confidence=0.0,
                reasoning=f"API error: {str(e)}",
                match_type=IntentMatchType.FALLBACK,
                raw_input=user_input
            )

    async def _classify_native(
        self,
        prompt: str,
        user_input: str
    ) -> IntentResult:
        """Classify using native Gemini API."""
        response = self._client.generate_content(prompt)
        return self._parse_response(response.text, user_input)

    async def _classify_openai_compat(
        self,
        prompt: str,
        user_input: str
    ) -> IntentResult:
        """Classify using OpenAI-compatible endpoint."""
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256
        )
        return self._parse_response(response.choices[0].message.content, user_input)

    def _parse_response(self, response: str, user_input: str) -> IntentResult:
        """Parse Gemini response into IntentResult."""
        try:
            # Extract JSON from response
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
            logger.warning(f"Failed to parse Gemini response: {e}")

        return IntentResult(
            command="none",
            confidence=0.3,
            reasoning=f"Parse error from: {response[:100]}",
            match_type=IntentMatchType.FALLBACK,
            raw_input=user_input
        )


def create_gemini_intent_adapter(
    api_key: Optional[str] = None,
    model: str = "gemini-1.5-flash"
) -> GeminiIntentAdapter:
    """Factory function for Gemini Intent Adapter."""
    return GeminiIntentAdapter(api_key=api_key, model=model)
