"""
Orion ODA v4.0 - Claude Intent Adapter

Claude-specific intent classification adapter.
In Claude Code environment, Main Agent IS Claude, so this adapter
focuses on structured output extraction via prompt engineering.

Key Features:
- Prompt engineering for intent classification
- JSON structured output
- V2.1.4 feature awareness (context:fork, run_in_background)
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from lib.oda.llm.intent_adapter import (
    BaseIntentAdapter,
    CommandDescription,
    IntentMatchType,
    IntentResult,
)

logger = logging.getLogger(__name__)


# =============================================================================
# INTENT CLASSIFICATION PROMPT
# =============================================================================

CLAUDE_INTENT_PROMPT = """You are an intent classifier for a development assistant.

## Available Commands
{commands}

## User Request
"{user_input}"

## Task
Classify this request into ONE of the available commands.
If the request doesn't match any command clearly, return "none".

## Rules
1. Consider semantic meaning, not just keywords
2. Korean and English requests are equally valid
3. Be confident - if it's clearly about code review, it's /audit
4. If truly ambiguous, return "none"

## Output Format (JSON only, no markdown)
{{"command": "/ask", "confidence": 0.95, "reasoning": "User needs clarification"}}

Respond with JSON only:"""


# =============================================================================
# CLAUDE INTENT ADAPTER
# =============================================================================

class ClaudeIntentAdapter(BaseIntentAdapter):
    """
    Claude Code Intent Adapter.

    In Claude Code environment, this adapter doesn't make API calls.
    Instead, it provides the prompt that Main Agent (Claude) will process.

    Two modes:
    1. Embedded mode: Returns prompt for Main Agent to process
    2. API mode: Makes actual API call (for testing/external use)
    """

    def __init__(
        self,
        mode: str = "embedded",
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize Claude Intent Adapter.

        Args:
            mode: "embedded" (Main Agent processes) or "api" (direct API call)
            api_key: Anthropic API key (required for api mode)
            model: Model to use for API mode
        """
        super().__init__()
        self.mode = mode
        self.api_key = api_key
        self.model = model
        self._client = None

        if mode == "api" and api_key:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=api_key)
            except ImportError:
                logger.warning("anthropic package not installed, API mode unavailable")

    @property
    def name(self) -> str:
        return "claude-intent-adapter"

    def is_available(self) -> bool:
        """Always available in embedded mode."""
        if self.mode == "embedded":
            return True
        return self._client is not None

    def build_classification_prompt(
        self,
        user_input: str,
        available_commands: List[CommandDescription]
    ) -> str:
        """
        Build the intent classification prompt.

        This method is public so Main Agent can access the prompt
        in embedded mode.
        """
        from lib.oda.llm.intent_adapter import format_commands_for_prompt

        commands_str = format_commands_for_prompt(available_commands)

        return CLAUDE_INTENT_PROMPT.format(
            commands=commands_str,
            user_input=user_input
        )

    async def _classify_impl(
        self,
        user_input: str,
        available_commands: List[CommandDescription]
    ) -> IntentResult:
        """
        Classify intent using Claude.

        In embedded mode, this returns a prompt for Main Agent.
        In API mode, makes actual API call.
        """
        prompt = self.build_classification_prompt(user_input, available_commands)

        if self.mode == "api" and self._client:
            return await self._classify_via_api(prompt, user_input, available_commands)

        # Embedded mode: Return instruction for Main Agent
        # Main Agent should process this prompt and return structured output
        # For now, we'll use a heuristic fallback
        return self._classify_heuristic(user_input, available_commands)

    async def _classify_via_api(
        self,
        prompt: str,
        user_input: str,
        available_commands: List[CommandDescription]
    ) -> IntentResult:
        """Make actual API call to Claude."""
        if not self._client:
            raise RuntimeError("API client not initialized")

        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            return self._parse_response(content, user_input, available_commands)

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return IntentResult(
                command="none",
                confidence=0.0,
                reasoning=f"API error: {str(e)}",
                match_type=IntentMatchType.FALLBACK,
                raw_input=user_input
            )

    def _parse_response(
        self,
        response: str,
        user_input: str,
        available_commands: List[CommandDescription]
    ) -> IntentResult:
        """Parse LLM JSON response into IntentResult."""
        try:
            # Try to extract JSON from response
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
            logger.warning(f"Failed to parse response: {e}")

        # Fallback: extract command from text
        from lib.oda.llm.intent_adapter import parse_command_from_response
        command = parse_command_from_response(response, available_commands)

        return IntentResult(
            command=command,
            confidence=0.6,
            reasoning=f"Extracted from response: {response[:100]}",
            match_type=IntentMatchType.SEMANTIC,
            raw_input=user_input
        )

    def _classify_heuristic(
        self,
        user_input: str,
        available_commands: List[CommandDescription]
    ) -> IntentResult:
        """
        Simple heuristic classification (fallback).

        This is used in embedded mode when we can't directly invoke LLM.
        Uses simple keyword matching as last resort.
        """
        input_lower = user_input.lower()

        # Simple keyword mapping for common patterns
        heuristics = [
            (["리뷰", "검사", "확인", "review", "check", "audit"], "/audit"),
            (["계획", "설계", "plan", "design", "구현"], "/plan"),
            (["분석", "깊이", "심층", "deep", "analyze"], "/deep-audit"),
            (["도움", "모르", "help", "how", "what", "뭐야", "어떻게"], "/ask"),
            (["거버넌스", "정책", "governance", "policy"], "/governance"),
        ]

        for keywords, command in heuristics:
            for kw in keywords:
                if kw in input_lower:
                    return IntentResult(
                        command=command,
                        confidence=0.7,
                        reasoning=f"Heuristic match: keyword '{kw}' found",
                        match_type=IntentMatchType.SEMANTIC,
                        raw_input=user_input
                    )

        # Default to /ask for general queries
        return IntentResult(
            command="/ask",
            confidence=0.5,
            reasoning="No clear match, defaulting to /ask for clarification",
            match_type=IntentMatchType.FALLBACK,
            raw_input=user_input
        )


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_claude_intent_adapter(
    mode: str = "embedded",
    api_key: Optional[str] = None
) -> ClaudeIntentAdapter:
    """
    Factory function for Claude Intent Adapter.

    Args:
        mode: "embedded" or "api"
        api_key: Anthropic API key (optional, reads from env if not provided)
    """
    import os

    if mode == "api" and not api_key:
        api_key = os.getenv("ANTHROPIC_API_KEY")

    return ClaudeIntentAdapter(mode=mode, api_key=api_key)
