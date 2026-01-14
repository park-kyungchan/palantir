"""
Orion ODA v4.0 - Intent Classification Prompts

Prompt templates for LLM-Native Intent Classification.
Replaces keyword-based TriggerDetector with semantic understanding.

Design Principles:
1. Simple and direct prompts
2. Support both Korean and English
3. Structured JSON output
4. Explainable classification (reasoning)
"""
from __future__ import annotations

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from lib.oda.llm.intent_adapter import CommandDescription


# =============================================================================
# MAIN CLASSIFICATION PROMPT
# =============================================================================

INTENT_CLASSIFICATION_PROMPT = """You are an intent classifier for a development assistant.

## Available Commands
{commands}

## User Request
"{user_input}"

## Task
Classify this request into ONE of the available commands.
Return structured JSON with your classification.

## Rules
1. Consider semantic meaning, not just keywords
2. Korean and English requests are equally valid
3. Be confident - if it clearly matches a command, classify it
4. If truly ambiguous or unrelated, return "none"

## Output Format (JSON only, no markdown code blocks)
{{"command": "/ask", "confidence": 0.95, "reasoning": "Brief explanation"}}

JSON:"""


# =============================================================================
# CLARIFICATION PROMPT
# =============================================================================

CLARIFICATION_PROMPT = """The intent classification for the following request was uncertain.

User request: "{user_input}"
Top match: {top_command} (confidence: {confidence:.2f})
Reasoning: {reasoning}

Please confirm or provide more details about what you'd like to do.
"""


# =============================================================================
# FEW-SHOT EXAMPLES (Optional enhancement)
# =============================================================================

FEW_SHOT_EXAMPLES = """
## Examples

User: "코드 리뷰해줘"
Output: {{"command": "/audit", "confidence": 0.95, "reasoning": "User requests code review"}}

User: "어떻게 구현해야할지 계획 세워줘"
Output: {{"command": "/plan", "confidence": 0.92, "reasoning": "User wants implementation planning"}}

User: "이거 뭐야?"
Output: {{"command": "/ask", "confidence": 0.88, "reasoning": "User needs clarification"}}

User: "심층적으로 분석해줘"
Output: {{"command": "/deep-audit", "confidence": 0.90, "reasoning": "User wants deep analysis"}}

User: "안녕하세요"
Output: {{"command": "none", "confidence": 0.85, "reasoning": "Greeting, not a command request"}}
"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def format_commands_for_classification(commands: List["CommandDescription"]) -> str:
    """
    Format command list for LLM prompt.

    Args:
        commands: List of CommandDescription objects

    Returns:
        Formatted string for prompt inclusion
    """
    lines = []
    for cmd in commands:
        examples_str = ""
        if hasattr(cmd, 'examples') and cmd.examples:
            examples_str = f" (examples: {', '.join(cmd.examples[:3])})"
        lines.append(f"- {cmd.name}: {cmd.description}{examples_str}")
    return "\n".join(lines)


def build_classification_prompt(
    user_input: str,
    commands: List["CommandDescription"],
    include_few_shot: bool = False
) -> str:
    """
    Build the full classification prompt.

    Args:
        user_input: User's input to classify
        commands: Available commands
        include_few_shot: Whether to include few-shot examples

    Returns:
        Complete prompt string
    """
    commands_str = format_commands_for_classification(commands)

    prompt = INTENT_CLASSIFICATION_PROMPT.format(
        commands=commands_str,
        user_input=user_input
    )

    if include_few_shot:
        # Insert few-shot examples before the output format section
        prompt = prompt.replace(
            "## Output Format",
            FEW_SHOT_EXAMPLES + "\n## Output Format"
        )

    return prompt


def build_clarification_prompt(
    user_input: str,
    top_command: str,
    confidence: float,
    reasoning: str
) -> str:
    """
    Build a clarification prompt for low-confidence classifications.

    Args:
        user_input: Original user input
        top_command: Top matched command
        confidence: Classification confidence
        reasoning: Classification reasoning

    Returns:
        Clarification prompt string
    """
    return CLARIFICATION_PROMPT.format(
        user_input=user_input,
        top_command=top_command,
        confidence=confidence,
        reasoning=reasoning
    )
