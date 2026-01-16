"""
Orion ODA v4.0 - Agent LLM Adapter (Phase 7.4.1)
=================================================

AgentLLMAdapter integrates the agent execution system with LLM providers:
- Support for OpenAI, Anthropic (Claude), and local models
- Streaming response support for long-running operations
- Tool/function calling integration
- Reasoning trace integration

Architecture:
    AgentLLMAdapter wraps the LLM provider and provides:
    1. Action planning via LLM reasoning
    2. Tool calling for ODA actions
    3. Streaming responses for UI integration
    4. Trace logging for debugging
"""

from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Protocol, Type, Union

from pydantic import BaseModel, Field

from lib.oda.agent.planner import (
    AgentPlanner,
    Observation,
    PlannedAction,
    PlannerConfig,
    PlannerIteration,
    Thought,
    ThoughtType,
)
from lib.oda.agent.trace import TraceLogger, TraceLevel
from lib.oda.llm.adapters.base import (
    AdapterCapabilities,
    BaseActionAdapter,
    ExecutionMode,
    LLMActionAdapter,
)
from lib.oda.llm.providers import (
    LLMProvider,
    LLMProviderType,
    ProviderRegistry,
    build_provider,
)
from lib.oda.ontology.actions import ActionContext, ActionResult, action_registry

logger = logging.getLogger(__name__)


# =============================================================================
# STREAMING TYPES
# =============================================================================

class StreamEventType(str, Enum):
    """Types of streaming events."""
    THINKING = "thinking"        # LLM is reasoning
    ACTION_START = "action_start"  # Action execution starting
    ACTION_END = "action_end"    # Action execution complete
    CONTENT = "content"          # Text content chunk
    TOOL_CALL = "tool_call"      # Tool/function call
    ERROR = "error"              # Error occurred
    DONE = "done"                # Stream complete


@dataclass
class StreamEvent:
    """A single streaming event."""
    event_type: StreamEventType
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.event_type.value,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


# =============================================================================
# TOOL DEFINITIONS
# =============================================================================

class AgentTool(BaseModel):
    """Definition of a tool available to the agent."""
    name: str = Field(..., description="Tool name")
    description: str = Field(default="", description="Tool description")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema for parameters")
    action_type: Optional[str] = Field(default=None, description="Linked ODA action type")

    class Config:
        arbitrary_types_allowed = True


class ToolCallRequest(BaseModel):
    """Request from LLM to call a tool."""
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    call_id: str = ""

    class Config:
        arbitrary_types_allowed = True


class ToolCallResult(BaseModel):
    """Result of a tool call."""
    call_id: str
    tool_name: str
    success: bool
    result: Any = None
    error: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


# =============================================================================
# AGENT LLM ADAPTER
# =============================================================================

class AgentLLMAdapter(ABC):
    """
    Abstract adapter for integrating agent execution with LLM providers.

    Subclasses implement provider-specific logic for:
    - Generating reasoning/thoughts
    - Planning actions
    - Processing tool calls
    - Streaming responses
    """

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        trace_level: TraceLevel = TraceLevel.STANDARD,
    ):
        """
        Initialize the adapter.

        Args:
            provider: LLM provider (auto-detected if not specified)
            trace_level: Verbosity level for trace logging
        """
        self._provider = provider or build_provider()
        self._trace_level = trace_level
        self._tools: Dict[str, AgentTool] = {}
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Register default ODA action tools
        self._register_default_tools()

    @property
    def provider(self) -> LLMProvider:
        """Get the underlying LLM provider."""
        return self._provider

    @property
    def provider_type(self) -> LLMProviderType:
        """Get the provider type."""
        return self._provider.provider_type()

    def _register_default_tools(self) -> None:
        """Register ODA actions as tools."""
        for action_name in action_registry.list_actions():
            action_cls = action_registry.get(action_name)
            if action_cls:
                tool = AgentTool(
                    name=action_name,
                    description=action_cls.__doc__ or f"Execute {action_name} action",
                    parameters=action_cls.get_parameter_schema(),
                    action_type=action_name,
                )
                self._tools[action_name] = tool

    def register_tool(self, tool: AgentTool) -> None:
        """Register a custom tool."""
        self._tools[tool.name] = tool
        self._logger.info(f"Registered tool: {tool.name}")

    def get_tool(self, name: str) -> Optional[AgentTool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[AgentTool]:
        """List all registered tools."""
        return list(self._tools.values())

    @abstractmethod
    async def generate_plan(
        self,
        goal: str,
        context: Dict[str, Any],
        max_actions: int = 5,
    ) -> List[PlannedAction]:
        """
        Generate a plan of actions to achieve a goal.

        Args:
            goal: The goal to achieve
            context: Current context/state
            max_actions: Maximum number of actions to plan

        Returns:
            List of PlannedAction objects
        """
        ...

    @abstractmethod
    async def think(
        self,
        observations: List[Observation],
        history: List[PlannerIteration],
        goal: str,
    ) -> tuple[List[Thought], Optional[PlannedAction]]:
        """
        Process observations and produce thoughts/actions.

        This is the core reasoning function for the ReAct cycle.

        Args:
            observations: Current observations
            history: Previous iterations
            goal: The goal being pursued

        Returns:
            Tuple of (thoughts, next_action or None if done)
        """
        ...

    @abstractmethod
    async def process_tool_call(
        self,
        tool_call: ToolCallRequest,
        actor_id: str = "agent",
    ) -> ToolCallResult:
        """
        Process a tool call from the LLM.

        Args:
            tool_call: The tool call request
            actor_id: ID of the actor making the call

        Returns:
            ToolCallResult with success/error status
        """
        ...

    async def stream_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[StreamEvent]:
        """
        Generate a streaming response for a prompt.

        Override in subclasses for streaming support.

        Args:
            prompt: The input prompt
            context: Optional context

        Yields:
            StreamEvent objects
        """
        # Default non-streaming implementation
        yield StreamEvent(
            event_type=StreamEventType.CONTENT,
            content="Streaming not supported for this provider",
        )
        yield StreamEvent(event_type=StreamEventType.DONE)

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        actor_id: str = "agent",
    ) -> ToolCallResult:
        """
        Execute a tool by name.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            actor_id: ID of the actor

        Returns:
            ToolCallResult
        """
        tool = self._tools.get(tool_name)
        if not tool:
            return ToolCallResult(
                call_id="",
                tool_name=tool_name,
                success=False,
                error=f"Tool '{tool_name}' not found",
            )

        # Execute linked ODA action
        if tool.action_type:
            action_cls = action_registry.get(tool.action_type)
            if action_cls:
                try:
                    action = action_cls()
                    context = ActionContext(actor_id=actor_id)
                    result: ActionResult = await action.execute(arguments, context)

                    return ToolCallResult(
                        call_id="",
                        tool_name=tool_name,
                        success=result.success,
                        result=result.to_dict(),
                        error=result.error if not result.success else None,
                    )
                except Exception as e:
                    return ToolCallResult(
                        call_id="",
                        tool_name=tool_name,
                        success=False,
                        error=str(e),
                    )

        return ToolCallResult(
            call_id="",
            tool_name=tool_name,
            success=False,
            error="Tool has no linked action",
        )


# =============================================================================
# OPENAI COMPATIBLE ADAPTER
# =============================================================================

class OpenAIAgentAdapter(AgentLLMAdapter):
    """
    Agent adapter for OpenAI-compatible LLM providers.

    Supports:
    - OpenAI API
    - Antigravity (Gemini via OpenAI API)
    - Local models via OpenAI-compatible endpoints
    """

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
        trace_level: TraceLevel = TraceLevel.STANDARD,
    ):
        super().__init__(provider, trace_level)
        self._model = model or self._provider.default_model()
        self._client = self._provider.build_client()

    async def generate_plan(
        self,
        goal: str,
        context: Dict[str, Any],
        max_actions: int = 5,
    ) -> List[PlannedAction]:
        """Generate a plan using OpenAI-compatible API."""
        if not self._client:
            self._logger.warning("No client available for planning")
            return []

        system_prompt = """You are an agent planner. Given a goal and context, generate a plan of actions.

Available actions:
{}

Respond with a JSON array of actions in this format:
[
    {{"action_type": "action.name", "params": {{}}, "rationale": "why this action"}}
]
"""
        action_list = "\n".join([
            f"- {t.name}: {t.description}"
            for t in self._tools.values()
        ][:20])  # Limit for prompt size

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt.format(action_list)},
                    {"role": "user", "content": f"Goal: {goal}\n\nContext: {json.dumps(context)}"},
                ],
                temperature=0.7,
                max_tokens=2000,
            )

            content = response.choices[0].message.content
            # Parse JSON from response
            # Handle markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            actions_data = json.loads(content.strip())

            return [
                PlannedAction(
                    action_type=a["action_type"],
                    params=a.get("params", {}),
                    rationale=a.get("rationale", ""),
                )
                for a in actions_data[:max_actions]
            ]

        except Exception as e:
            self._logger.exception("Failed to generate plan")
            return []

    async def think(
        self,
        observations: List[Observation],
        history: List[PlannerIteration],
        goal: str,
    ) -> tuple[List[Thought], Optional[PlannedAction]]:
        """Process observations using ReAct-style reasoning."""
        if not self._client:
            return [Thought(
                thought_type=ThoughtType.ERROR,
                content="No LLM client available",
                confidence=0.0,
            )], None

        # Build context from observations and history
        obs_text = "\n".join([
            f"- [{o.source}]: {json.dumps(o.content)[:200]}"
            for o in observations
        ])

        history_text = ""
        if history:
            last_iter = history[-1]
            if last_iter.planned_action:
                history_text = f"Last action: {last_iter.planned_action.action_type}"
                if last_iter.action_result:
                    history_text += f" -> {last_iter.action_result.get('success', 'unknown')}"

        system_prompt = """You are a reasoning agent using the ReAct framework.
Given observations and a goal, think step by step and decide on the next action.

Available actions: {}

Respond in this exact JSON format:
{{
    "thoughts": [
        {{"type": "observation", "content": "What I observe"}},
        {{"type": "reasoning", "content": "My reasoning"}},
        {{"type": "action_selection", "content": "Why I chose this action"}}
    ],
    "action": {{"action_type": "...", "params": {{}}, "rationale": "..."}} or null if goal achieved
}}
"""
        action_names = ", ".join(list(self._tools.keys())[:15])

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt.format(action_names)},
                    {"role": "user", "content": f"""Goal: {goal}

Observations:
{obs_text}

{history_text}

Think and decide on the next action (or null if goal is achieved):"""},
                ],
                temperature=0.5,
                max_tokens=1500,
            )

            content = response.choices[0].message.content

            # Parse JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            data = json.loads(content.strip())

            thoughts = [
                Thought(
                    thought_type=ThoughtType(t.get("type", "reasoning")),
                    content=t.get("content", ""),
                    confidence=t.get("confidence", 0.8),
                )
                for t in data.get("thoughts", [])
            ]

            action_data = data.get("action")
            planned_action = None
            if action_data:
                planned_action = PlannedAction(
                    action_type=action_data["action_type"],
                    params=action_data.get("params", {}),
                    rationale=action_data.get("rationale", ""),
                )

            return thoughts, planned_action

        except Exception as e:
            self._logger.exception("Thinking failed")
            return [Thought(
                thought_type=ThoughtType.ERROR,
                content=str(e),
                confidence=0.0,
            )], None

    async def process_tool_call(
        self,
        tool_call: ToolCallRequest,
        actor_id: str = "agent",
    ) -> ToolCallResult:
        """Process a tool call from the LLM."""
        return await self.execute_tool(
            tool_call.tool_name,
            tool_call.arguments,
            actor_id,
        )

    async def stream_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[StreamEvent]:
        """Stream a response from OpenAI-compatible API."""
        if not self._client:
            yield StreamEvent(
                event_type=StreamEventType.ERROR,
                content="No client available",
            )
            yield StreamEvent(event_type=StreamEventType.DONE)
            return

        try:
            stream = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "user", "content": prompt},
                ],
                stream=True,
            )

            yield StreamEvent(event_type=StreamEventType.THINKING)

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield StreamEvent(
                        event_type=StreamEventType.CONTENT,
                        content=chunk.choices[0].delta.content,
                    )

            yield StreamEvent(event_type=StreamEventType.DONE)

        except Exception as e:
            yield StreamEvent(
                event_type=StreamEventType.ERROR,
                content=str(e),
            )
            yield StreamEvent(event_type=StreamEventType.DONE)


# =============================================================================
# CLAUDE CODE ADAPTER (CLI Native)
# =============================================================================

class ClaudeCodeAgentAdapter(AgentLLMAdapter):
    """
    Agent adapter for Claude Code CLI-native operation.

    This adapter works without API calls - it's designed for
    use when already running inside Claude Code CLI.
    """

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        trace_level: TraceLevel = TraceLevel.STANDARD,
    ):
        super().__init__(provider, trace_level)

    async def generate_plan(
        self,
        goal: str,
        context: Dict[str, Any],
        max_actions: int = 5,
    ) -> List[PlannedAction]:
        """Generate a simple plan based on goal parsing."""
        # CLI-native - return empty plan (Claude Code handles planning)
        self._logger.info("CLI-native mode - planning handled by Claude Code")
        return []

    async def think(
        self,
        observations: List[Observation],
        history: List[PlannerIteration],
        goal: str,
    ) -> tuple[List[Thought], Optional[PlannedAction]]:
        """CLI-native thinking - delegate to Claude Code."""
        # In CLI-native mode, we don't do LLM calls
        # Return observation summary as thought
        thought = Thought(
            thought_type=ThoughtType.OBSERVATION,
            content=f"CLI-native mode. Observations: {len(observations)}. Goal: {goal[:100]}",
            confidence=1.0,
        )
        return [thought], None

    async def process_tool_call(
        self,
        tool_call: ToolCallRequest,
        actor_id: str = "agent",
    ) -> ToolCallResult:
        """Process tool call in CLI-native mode."""
        return await self.execute_tool(
            tool_call.tool_name,
            tool_call.arguments,
            actor_id,
        )


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def build_agent_adapter(
    provider_type: Optional[LLMProviderType] = None,
    trace_level: TraceLevel = TraceLevel.STANDARD,
) -> AgentLLMAdapter:
    """
    Build the appropriate agent adapter based on provider type.

    Args:
        provider_type: Specific provider type (auto-detected if None)
        trace_level: Trace logging level

    Returns:
        Configured AgentLLMAdapter instance
    """
    if provider_type is None:
        provider = build_provider()
        provider_type = provider.provider_type()
    else:
        from lib.oda.llm.config import load_llm_config, LLMBackendConfig
        config = load_llm_config()
        config.provider_type = provider_type
        provider = build_provider(config)

    if provider_type == LLMProviderType.CLAUDE_CODE:
        return ClaudeCodeAgentAdapter(provider, trace_level)
    else:
        # OpenAI-compatible for all other providers
        return OpenAIAgentAdapter(provider, trace_level=trace_level)


__all__ = [
    "StreamEventType",
    "StreamEvent",
    "AgentTool",
    "ToolCallRequest",
    "ToolCallResult",
    "AgentLLMAdapter",
    "OpenAIAgentAdapter",
    "ClaudeCodeAgentAdapter",
    "build_agent_adapter",
]
