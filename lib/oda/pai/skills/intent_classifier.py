"""
Orion ODA v4.0 - LLM-Native Intent Classifier

Main entry point for intent classification.
Replaces TriggerDetector with LLM-based semantic understanding.

User Requirements (2026-01-13):
- "복잡한 과정 필요없이 LLM에게만 맡기려고 함"
- "완전 제거" (TriggerDetector)
- "커스텀 커맨드 고도화" (/ask, /plan, /audit)
- "실제 코드 수정 전까지는 LLM의 최대성능과 기능을 최대로 활용"

Design:
- No keywords, no regex, no Jaccard
- Direct LLM classification
- Simple, focused interface
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from lib.oda.llm.intent_adapter import (
    BaseIntentAdapter,
    CommandDescription,
    IntentAdapter,
    IntentMatchType,
    IntentResult,
)

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class IntentClassifierConfig:
    """
    Configuration for IntentClassifier.

    Simplified configuration focused on LLM-first approach.
    """
    # Confidence thresholds
    clarification_threshold: float = 0.7  # Below this, ask user
    min_confidence: float = 0.3  # Below this, fallback to /ask

    # Adapter settings
    adapter_type: str = "claude"  # claude, openai, gemini, local
    enable_telemetry: bool = True

    # Default commands if none provided
    use_default_commands: bool = True


# =============================================================================
# DEFAULT COMMANDS
# =============================================================================

DEFAULT_COMMANDS: List[CommandDescription] = [
    CommandDescription(
        name="/ask",
        description="요구사항 분석 및 명확화, 프롬프트 엔지니어링, 사용자 의도 파악",
        examples=["도와줘", "이해 안돼", "어떻게 해야해?", "모르겠어"]
    ),
    CommandDescription(
        name="/plan",
        description="구현 계획 수립, 아키텍처 설계, 작업 분해",
        examples=["계획 세워줘", "어떻게 구현할지", "설계해줘", "구현"]
    ),
    CommandDescription(
        name="/audit",
        description="코드 품질 검사, 3-Stage Protocol, 코드 리뷰",
        examples=["코드 리뷰해줘", "검사해줘", "품질 확인", "리뷰"]
    ),
    CommandDescription(
        name="/deep-audit",
        description="심층 분석, RSIL 방법론, 집중 검토",
        examples=["깊이 분석해줘", "심층 검토", "자세히 봐줘", "분석"]
    ),
    CommandDescription(
        name="/governance",
        description="거버넌스 준수 확인, 제안 검토, 정책 확인",
        examples=["거버넌스 확인", "정책 검토", "규칙 확인"]
    ),
    CommandDescription(
        name="/memory",
        description="시맨틱 메모리 관리, 인사이트/패턴 저장",
        examples=["기억해", "저장해", "메모리 관리"]
    ),
    CommandDescription(
        name="/quality-check",
        description="품질 게이트 실행, E2E 테스트, 설정 검사",
        examples=["품질 검사", "테스트 실행", "검증"]
    ),
]


# =============================================================================
# INTENT CLASSIFIER
# =============================================================================

class IntentClassifier:
    """
    LLM-Native Intent Classifier.

    Simple, focused classifier that delegates to LLM for intent understanding.
    No complex fallback layers - just LLM classification.

    Usage:
        classifier = IntentClassifier()
        result = await classifier.classify("코드 리뷰해줘")
        print(result.command)  # "/audit"
        print(result.confidence)  # 0.92
    """

    def __init__(
        self,
        adapter: Optional[IntentAdapter] = None,
        config: Optional[IntentClassifierConfig] = None,
        commands: Optional[List[CommandDescription]] = None
    ):
        """
        Initialize IntentClassifier.

        Args:
            adapter: LLM adapter for classification (auto-created if None)
            config: Configuration options
            commands: Available commands (uses defaults if None)
        """
        self.config = config or IntentClassifierConfig()
        self._commands = commands or (DEFAULT_COMMANDS if self.config.use_default_commands else [])
        self._adapter = adapter or self._create_default_adapter()
        self._logger = logging.getLogger(f"{__name__}.IntentClassifier")

    def _create_default_adapter(self) -> IntentAdapter:
        """Create default adapter based on config."""
        adapter_type = self.config.adapter_type.lower()

        if adapter_type == "claude":
            from lib.oda.llm.adapters.claude_intent_adapter import ClaudeIntentAdapter
            return ClaudeIntentAdapter(mode="embedded")

        elif adapter_type == "openai":
            from lib.oda.llm.adapters.openai_intent_adapter import OpenAIIntentAdapter
            return OpenAIIntentAdapter()

        elif adapter_type == "gemini":
            from lib.oda.llm.adapters.gemini_intent_adapter import GeminiIntentAdapter
            return GeminiIntentAdapter()

        elif adapter_type == "local":
            from lib.oda.llm.adapters.local_intent_adapter import LocalIntentAdapter
            return LocalIntentAdapter()

        else:
            self._logger.warning(f"Unknown adapter type: {adapter_type}, using Claude")
            from lib.oda.llm.adapters.claude_intent_adapter import ClaudeIntentAdapter
            return ClaudeIntentAdapter(mode="embedded")

    @property
    def commands(self) -> List[CommandDescription]:
        """Get available commands."""
        return self._commands

    @commands.setter
    def commands(self, value: List[CommandDescription]):
        """Set available commands."""
        self._commands = value

    def add_command(self, command: CommandDescription):
        """Add a new command."""
        self._commands.append(command)

    def remove_command(self, name: str):
        """Remove a command by name."""
        self._commands = [c for c in self._commands if c.name != name]

    async def classify(
        self,
        user_input: str,
        commands: Optional[List[CommandDescription]] = None
    ) -> IntentResult:
        """
        Classify user intent.

        This is the main entry point for intent classification.
        Simple flow:
        1. Check explicit command (/xxx)
        2. Delegate to LLM for natural language

        Args:
            user_input: User's input to classify
            commands: Optional override for available commands

        Returns:
            IntentResult with command, confidence, reasoning
        """
        start_time = time.time()
        cmds = commands or self._commands

        self._logger.debug(f"Classifying: {user_input[:50]}...")

        try:
            result = await self._adapter.classify(user_input, cmds)

            # Apply confidence threshold
            if result.confidence < self.config.min_confidence:
                self._logger.info(
                    f"Low confidence ({result.confidence:.2f}), "
                    f"defaulting to /ask"
                )
                result = IntentResult(
                    command="/ask",
                    confidence=self.config.min_confidence,
                    reasoning=f"Low confidence classification, using /ask for clarification. "
                              f"Original: {result.reasoning}",
                    match_type=IntentMatchType.FALLBACK,
                    raw_input=user_input
                )

            # Log telemetry
            if self.config.enable_telemetry:
                latency_ms = (time.time() - start_time) * 1000
                self._log_telemetry(result, latency_ms)

            return result

        except Exception as e:
            self._logger.error(f"Classification error: {e}")
            return IntentResult(
                command="/ask",
                confidence=0.0,
                reasoning=f"Classification failed: {str(e)}",
                match_type=IntentMatchType.FALLBACK,
                raw_input=user_input
            )

    def classify_sync(
        self,
        user_input: str,
        commands: Optional[List[CommandDescription]] = None
    ) -> IntentResult:
        """
        Synchronous wrapper for classify().

        Useful for non-async contexts.
        """
        return asyncio.run(self.classify(user_input, commands))

    def needs_clarification(self, result: IntentResult) -> bool:
        """
        Check if result needs user clarification.

        Args:
            result: Classification result to check

        Returns:
            True if clarification needed
        """
        return (
            result.confidence < self.config.clarification_threshold and
            result.match_type != IntentMatchType.EXPLICIT
        )

    def _log_telemetry(self, result: IntentResult, latency_ms: float):
        """Log classification telemetry."""
        self._logger.info(
            f"Intent: {result.command} | "
            f"Confidence: {result.confidence:.2f} | "
            f"Type: {result.match_type.value} | "
            f"Latency: {latency_ms:.1f}ms"
        )


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_intent_classifier(
    adapter_type: str = "claude",
    commands: Optional[List[CommandDescription]] = None
) -> IntentClassifier:
    """
    Factory function for IntentClassifier.

    Args:
        adapter_type: Type of LLM adapter (claude, openai, gemini, local)
        commands: Available commands

    Returns:
        Configured IntentClassifier
    """
    config = IntentClassifierConfig(adapter_type=adapter_type)
    return IntentClassifier(config=config, commands=commands)


def get_default_commands() -> List[CommandDescription]:
    """Get the default command list."""
    return DEFAULT_COMMANDS.copy()


# =============================================================================
# BACKWARD COMPATIBILITY (TriggerDetector interface)
# =============================================================================

class LegacyTriggerMatch:
    """
    Legacy TriggerMatch interface for backward compatibility.

    Maps IntentResult to the old TriggerMatch format.
    """

    def __init__(self, intent_result: IntentResult):
        self._result = intent_result

    @property
    def skill_name(self) -> str:
        """Map command to skill name."""
        # Remove leading slash for skill name
        cmd = self._result.command
        return cmd[1:] if cmd.startswith('/') else cmd

    @property
    def confidence(self) -> float:
        return self._result.confidence

    @property
    def matched_keyword(self) -> Optional[str]:
        """Legacy field - always None for LLM classification."""
        return None

    @property
    def context_similarity(self) -> float:
        """Legacy field - map to confidence."""
        return self._result.confidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_name": self.skill_name,
            "confidence": self.confidence,
            "matched_keyword": self.matched_keyword,
            "context_similarity": self.context_similarity,
            "reasoning": self._result.reasoning,
        }


def convert_to_trigger_match(intent_result: IntentResult) -> LegacyTriggerMatch:
    """Convert IntentResult to legacy TriggerMatch format."""
    return LegacyTriggerMatch(intent_result)


# =============================================================================
# LOW-CONFIDENCE CLARIFICATION FLOW
# =============================================================================

@dataclass
class ClarificationRequest:
    """
    Request for user clarification when classification confidence is low.

    Generated when IntentResult.confidence < clarification_threshold.
    """
    original_input: str
    top_match: IntentResult
    alternatives: List[IntentResult] = field(default_factory=list)
    clarification_prompt: str = ""
    suggested_options: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Auto-generate clarification prompt if not provided."""
        if not self.clarification_prompt:
            self.clarification_prompt = self._generate_prompt()
        if not self.suggested_options:
            self.suggested_options = self._generate_options()

    def _generate_prompt(self) -> str:
        """Generate a clarification prompt for the user."""
        confidence_pct = int(self.top_match.confidence * 100)

        # Korean/English bilingual prompt
        return (
            f"입력하신 내용을 분석했습니다: \"{self.original_input}\"\n\n"
            f"가장 유력한 명령어: {self.top_match.command} ({confidence_pct}% 확신)\n"
            f"분석 근거: {self.top_match.reasoning}\n\n"
            f"원하시는 작업이 맞나요? 아니라면 아래에서 선택하거나 더 구체적으로 말씀해주세요."
        )

    def _generate_options(self) -> List[str]:
        """Generate suggested options for AskUserQuestion."""
        options = [self.top_match.command]
        for alt in self.alternatives[:3]:  # Max 3 alternatives
            if alt.command not in options:
                options.append(alt.command)
        return options

    def to_ask_user_format(self) -> Dict[str, Any]:
        """
        Convert to AskUserQuestion tool format.

        Returns dict compatible with Claude Code's AskUserQuestion tool.
        """
        option_items = []
        for cmd in self.suggested_options:
            # Find description for this command
            desc = f"Execute {cmd} command"
            for alt in [self.top_match] + self.alternatives:
                if alt.command == cmd:
                    desc = alt.reasoning
                    break
            option_items.append({
                "label": cmd,
                "description": desc
            })

        return {
            "questions": [{
                "question": self.clarification_prompt,
                "header": "Command",
                "options": option_items[:4],  # Max 4 options
                "multiSelect": False
            }]
        }


class ClarificationFlow:
    """
    Manages low-confidence clarification flow.

    When classification confidence is below threshold, this flow
    helps clarify user intent through structured questions.

    Usage:
        flow = ClarificationFlow(classifier)
        result = await classifier.classify("뭔가 해줘")

        if classifier.needs_clarification(result):
            request = await flow.create_clarification(result, "뭔가 해줘")
            # Use request.to_ask_user_format() with AskUserQuestion tool
    """

    def __init__(
        self,
        classifier: IntentClassifier,
        max_alternatives: int = 3
    ):
        """
        Initialize clarification flow.

        Args:
            classifier: IntentClassifier instance
            max_alternatives: Maximum alternative commands to suggest
        """
        self.classifier = classifier
        self.max_alternatives = max_alternatives
        self._logger = logging.getLogger(f"{__name__}.ClarificationFlow")

    async def create_clarification(
        self,
        top_result: IntentResult,
        original_input: str
    ) -> ClarificationRequest:
        """
        Create a clarification request for low-confidence classification.

        Args:
            top_result: The top classification result
            original_input: User's original input

        Returns:
            ClarificationRequest with prompt and options
        """
        # Get alternative classifications
        alternatives = await self._get_alternatives(original_input, top_result)

        return ClarificationRequest(
            original_input=original_input,
            top_match=top_result,
            alternatives=alternatives
        )

    async def _get_alternatives(
        self,
        user_input: str,
        top_result: IntentResult
    ) -> List[IntentResult]:
        """
        Get alternative command suggestions.

        Uses available commands list to suggest alternatives.
        """
        alternatives = []
        commands = self.classifier.commands

        # Find commands that might match
        for cmd in commands:
            if cmd.name == top_result.command:
                continue

            # Simple heuristic: check example overlap
            score = self._calculate_alternative_score(user_input, cmd)
            if score > 0.2:  # Minimum threshold
                alternatives.append(IntentResult(
                    command=cmd.name,
                    confidence=score,
                    reasoning=cmd.description,
                    match_type=IntentMatchType.SEMANTIC,
                    raw_input=user_input
                ))

        # Sort by confidence and limit
        alternatives.sort(key=lambda x: x.confidence, reverse=True)
        return alternatives[:self.max_alternatives]

    def _calculate_alternative_score(
        self,
        user_input: str,
        command: CommandDescription
    ) -> float:
        """
        Calculate a simple alternative score.

        Uses basic keyword overlap as a fallback heuristic.
        """
        user_lower = user_input.lower()
        score = 0.0

        # Check example overlap
        if hasattr(command, 'examples') and command.examples:
            for example in command.examples:
                if example.lower() in user_lower or user_lower in example.lower():
                    score += 0.3

        # Check description overlap
        if command.description:
            desc_words = set(command.description.lower().split())
            input_words = set(user_lower.split())
            overlap = len(desc_words & input_words)
            if overlap > 0:
                score += 0.1 * overlap

        return min(score, 0.8)  # Cap at 0.8

    def create_clarification_sync(
        self,
        top_result: IntentResult,
        original_input: str
    ) -> ClarificationRequest:
        """Synchronous wrapper for create_clarification()."""
        return asyncio.run(self.create_clarification(top_result, original_input))
