"""
Orion ODA v4.0 - LLM Intent Adapter Base Protocol

LLM-Native Intent Classification adapter interface.
Replaces keyword-based TriggerDetector with direct LLM classification.

Design Principles:
1. LLM-Direct: No keywords, no regex, no Jaccard - just LLM
2. Simple Interface: classify() method only
3. Multi-LLM Support: Claude, OpenAI, Gemini, Local
4. Structured Output: Always returns IntentResult

User Requirements (2026-01-13):
- "복잡한 과정 필요없이 LLM에게만 맡기려고 함"
- "완전 제거" (TriggerDetector)
- "커스텀 커맨드 고도화" (/ask, /plan, /audit)
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# INTENT TYPES
# =============================================================================

class IntentMatchType(str, Enum):
    """How the intent was matched."""
    EXPLICIT = "explicit"    # User used /command directly
    SEMANTIC = "semantic"    # LLM inferred from natural language
    FALLBACK = "fallback"    # Low confidence, needs clarification


class IntentResult(BaseModel):
    """
    Result of LLM intent classification.

    This is the core output type for all intent adapters.
    Simple and focused - no complex alternatives or embeddings.
    """
    command: str = Field(
        description="Matched command (e.g., '/ask', '/plan', '/audit', 'none')"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Classification confidence (0.0-1.0)"
    )
    reasoning: str = Field(
        description="LLM's explanation for the classification"
    )
    match_type: IntentMatchType = Field(
        default=IntentMatchType.SEMANTIC,
        description="How the intent was matched"
    )
    raw_input: str = Field(
        default="",
        description="Original user input"
    )

    class Config:
        frozen = True

    def needs_clarification(self, threshold: float = 0.7) -> bool:
        """Check if confidence is too low and needs user clarification."""
        return self.confidence < threshold and self.match_type != IntentMatchType.EXPLICIT


@dataclass
class CommandDescription:
    """
    Description of an available command for LLM context.
    """
    name: str           # e.g., "/ask"
    description: str    # Semantic description for LLM
    examples: List[str] = field(default_factory=list)  # Example triggers

    def to_prompt_format(self) -> str:
        """Format for inclusion in LLM prompt."""
        examples_str = ""
        if self.examples:
            examples_str = f" (examples: {', '.join(self.examples[:3])})"
        return f"- {self.name}: {self.description}{examples_str}"


# =============================================================================
# INTENT ADAPTER PROTOCOL
# =============================================================================

@runtime_checkable
class IntentAdapter(Protocol):
    """
    Protocol for LLM Intent Classification Adapters.

    All intent adapters must implement this protocol to ensure
    consistent classification behavior across different LLM backends.

    This is the core abstraction for LLM-Native Intent Classification.
    """

    @property
    def name(self) -> str:
        """Human-readable name of this adapter."""
        ...

    def is_available(self) -> bool:
        """Check if this adapter is ready for use."""
        ...

    async def classify(
        self,
        user_input: str,
        available_commands: List[CommandDescription],
    ) -> IntentResult:
        """
        Classify user intent using the LLM.

        This is the primary method for intent classification.
        LLM receives the user input and available commands,
        returns structured classification result.

        Args:
            user_input: Raw user input (natural language or /command)
            available_commands: List of commands with descriptions

        Returns:
            IntentResult with command, confidence, and reasoning
        """
        ...


# =============================================================================
# BASE ADAPTER IMPLEMENTATION
# =============================================================================

class BaseIntentAdapter(ABC):
    """
    Abstract base class for Intent Adapters.

    Provides common functionality:
    - Explicit command detection (/command syntax)
    - Logging and error handling
    - Default available commands

    Subclasses must implement:
    - _classify_impl(): Provider-specific LLM classification
    """

    # Default commands (can be overridden)
    DEFAULT_COMMANDS: List[CommandDescription] = [
        CommandDescription(
            name="/ask",
            description="요구사항 분석 및 명확화, 프롬프트 엔지니어링, 사용자 의도 파악",
            examples=["도와줘", "이해 안돼", "어떻게 해야해?"]
        ),
        CommandDescription(
            name="/plan",
            description="구현 계획 수립, 아키텍처 설계, 작업 분해",
            examples=["계획 세워줘", "어떻게 구현할지", "설계해줘"]
        ),
        CommandDescription(
            name="/audit",
            description="코드 품질 검사, 3-Stage Protocol, 코드 리뷰",
            examples=["코드 리뷰해줘", "검사해줘", "품질 확인"]
        ),
        CommandDescription(
            name="/deep-audit",
            description="심층 분석, RSIL 방법론, 집중 검토",
            examples=["깊이 분석해줘", "심층 검토", "자세히 봐줘"]
        ),
        CommandDescription(
            name="/governance",
            description="거버넌스 준수 확인, 제안 검토, 정책 확인",
            examples=["거버넌스 확인", "정책 검토"]
        ),
    ]

    def __init__(self):
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable adapter name."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check adapter availability."""
        ...

    @abstractmethod
    async def _classify_impl(
        self,
        user_input: str,
        available_commands: List[CommandDescription],
    ) -> IntentResult:
        """
        Provider-specific classification implementation.

        Called after explicit command check fails.
        Subclasses implement their LLM-specific logic here.
        """
        ...

    def _check_explicit_command(
        self,
        user_input: str,
        available_commands: List[CommandDescription]
    ) -> Optional[IntentResult]:
        """
        Check if input starts with an explicit /command.

        If user types "/ask something", we skip LLM and route directly.
        """
        stripped = user_input.strip()
        if not stripped.startswith('/'):
            return None

        # Extract command part
        parts = stripped.split(maxsplit=1)
        cmd = parts[0].lower()

        # Check against available commands
        for command in available_commands:
            if cmd == command.name.lower():
                self._logger.debug(f"Explicit command detected: {cmd}")
                return IntentResult(
                    command=command.name,
                    confidence=1.0,
                    reasoning="User explicitly invoked this command",
                    match_type=IntentMatchType.EXPLICIT,
                    raw_input=user_input
                )

        # Unknown command
        return IntentResult(
            command="none",
            confidence=0.5,
            reasoning=f"Unknown command '{cmd}' - not in available commands",
            match_type=IntentMatchType.FALLBACK,
            raw_input=user_input
        )

    async def classify(
        self,
        user_input: str,
        available_commands: Optional[List[CommandDescription]] = None,
    ) -> IntentResult:
        """
        Classify user intent.

        Flow:
        1. Check explicit command (/ask, /plan, etc.)
        2. If natural language, call LLM for classification
        """
        commands = available_commands or self.DEFAULT_COMMANDS

        self._logger.info(f"Classifying intent for: {user_input[:50]}...")

        # Step 1: Check explicit command
        explicit_result = self._check_explicit_command(user_input, commands)
        if explicit_result:
            return explicit_result

        # Step 2: LLM classification for natural language
        try:
            result = await self._classify_impl(user_input, commands)
            result = IntentResult(
                command=result.command,
                confidence=result.confidence,
                reasoning=result.reasoning,
                match_type=IntentMatchType.SEMANTIC,
                raw_input=user_input
            )

            self._logger.info(
                f"Intent classified: {result.command} "
                f"(confidence={result.confidence:.2f})"
            )
            return result

        except Exception as e:
            self._logger.error(f"Classification failed: {e}")
            return IntentResult(
                command="none",
                confidence=0.0,
                reasoning=f"Classification error: {str(e)}",
                match_type=IntentMatchType.FALLBACK,
                raw_input=user_input
            )


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def format_commands_for_prompt(commands: List[CommandDescription]) -> str:
    """Format command list for LLM prompt inclusion."""
    return "\n".join(cmd.to_prompt_format() for cmd in commands)


def parse_command_from_response(response: str, available_commands: List[CommandDescription]) -> str:
    """
    Extract command name from LLM response.

    Handles various formats:
    - Direct: "/ask"
    - JSON: {"command": "/ask"}
    - Sentence: "I think the user wants /ask"
    """
    response_lower = response.lower()

    for cmd in available_commands:
        if cmd.name.lower() in response_lower:
            return cmd.name

    return "none"
