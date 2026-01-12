"""
Orion ODA v4.0 - Agent Planning Loop (Phase 7.3.1)
===================================================

ReAct-style agent planning loop implementing:
- Observation -> Thought -> Action cycle
- Maximum iteration limit with backoff
- State management between iterations
- Integration with GovernanceEngine for action validation

Architecture:
    AgentPlanner orchestrates the planning cycle:
    1. Observe: Gather context from ontology
    2. Think: Reason about next action via LLM
    3. Act: Execute action through GovernanceEngine
    4. Reflect: Update state based on results
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol, TypeVar, Union

from pydantic import BaseModel, Field

from lib.oda.ontology.actions import ActionContext, ActionResult, GovernanceEngine, action_registry
from lib.oda.ontology.ontology_types import utc_now

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND TYPES
# =============================================================================

class PlannerState(str, Enum):
    """Agent planner lifecycle states."""
    IDLE = "idle"
    OBSERVING = "observing"
    THINKING = "thinking"
    ACTING = "acting"
    REFLECTING = "reflecting"
    COMPLETED = "completed"
    FAILED = "failed"
    MAX_ITERATIONS = "max_iterations"


class ThoughtType(str, Enum):
    """Types of agent thoughts in ReAct cycle."""
    OBSERVATION = "observation"
    REASONING = "reasoning"
    ACTION_SELECTION = "action_selection"
    REFLECTION = "reflection"
    ERROR = "error"


# =============================================================================
# DATA MODELS
# =============================================================================

class Observation(BaseModel):
    """Represents an observation from the environment/ontology."""
    source: str = Field(..., description="Source of observation (e.g., 'ontology', 'action_result')")
    content: Dict[str, Any] = Field(default_factory=dict, description="Observation data")
    timestamp: datetime = Field(default_factory=utc_now)

    class Config:
        arbitrary_types_allowed = True


class Thought(BaseModel):
    """Represents a reasoning step in the planning cycle."""
    thought_type: ThoughtType
    content: str = Field(..., description="The thought content")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=utc_now)

    class Config:
        arbitrary_types_allowed = True


class PlannedAction(BaseModel):
    """Represents a planned action to execute."""
    action_type: str = Field(..., description="Action API name")
    params: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    rationale: str = Field(default="", description="Why this action was selected")
    priority: int = Field(default=0, description="Execution priority (higher = first)")

    class Config:
        arbitrary_types_allowed = True


class PlannerIteration(BaseModel):
    """Represents a single iteration of the planning loop."""
    iteration: int
    state: PlannerState
    observations: List[Observation] = Field(default_factory=list)
    thoughts: List[Thought] = Field(default_factory=list)
    planned_action: Optional[PlannedAction] = None
    action_result: Optional[Dict[str, Any]] = None
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


@dataclass
class PlannerConfig:
    """Configuration for the agent planner."""
    max_iterations: int = 10
    iteration_timeout_seconds: float = 60.0
    backoff_base_seconds: float = 1.0
    backoff_max_seconds: float = 30.0
    enable_reflection: bool = True
    require_action_rationale: bool = True
    actor_id: str = "agent-planner"


# =============================================================================
# PROTOCOLS
# =============================================================================

class ThinkingFunction(Protocol):
    """Protocol for LLM thinking function."""

    async def __call__(
        self,
        observations: List[Observation],
        history: List[PlannerIteration],
        goal: str,
    ) -> tuple[List[Thought], Optional[PlannedAction]]:
        """
        Process observations and history to produce thoughts and an action.

        Args:
            observations: Current observations
            history: Previous iterations
            goal: The goal to achieve

        Returns:
            Tuple of (thoughts, planned_action or None if done)
        """
        ...


# =============================================================================
# AGENT PLANNER
# =============================================================================

class AgentPlanner:
    """
    ReAct-style agent planning loop.

    Implements the Observe -> Think -> Act -> Reflect cycle for
    autonomous agent operation within ODA governance constraints.

    Usage:
        ```python
        planner = AgentPlanner(
            goal="Create and configure a new service",
            think_fn=my_llm_think_function,
            observe_fn=my_observation_function,
        )

        async for iteration in planner.run():
            print(f"Iteration {iteration.iteration}: {iteration.state}")
            if iteration.planned_action:
                print(f"  Action: {iteration.planned_action.action_type}")

        print(f"Final state: {planner.state}")
        print(f"History: {len(planner.history)} iterations")
        ```
    """

    def __init__(
        self,
        goal: str,
        think_fn: ThinkingFunction,
        observe_fn: Optional[Callable[[], List[Observation]]] = None,
        config: Optional[PlannerConfig] = None,
        governance: Optional[GovernanceEngine] = None,
    ):
        """
        Initialize the agent planner.

        Args:
            goal: The goal to achieve
            think_fn: Async function for LLM reasoning
            observe_fn: Optional function to gather observations
            config: Planner configuration
            governance: Governance engine for action validation
        """
        self.goal = goal
        self.think_fn = think_fn
        self.observe_fn = observe_fn or (lambda: [])
        self.config = config or PlannerConfig()
        self.governance = governance or GovernanceEngine(action_registry)

        # State management
        self._state = PlannerState.IDLE
        self._history: List[PlannerIteration] = []
        self._current_iteration: int = 0
        self._started_at: Optional[datetime] = None
        self._completed_at: Optional[datetime] = None
        self._final_result: Optional[Any] = None

    @property
    def state(self) -> PlannerState:
        """Current planner state."""
        return self._state

    @property
    def history(self) -> List[PlannerIteration]:
        """History of all iterations."""
        return self._history.copy()

    @property
    def is_complete(self) -> bool:
        """Check if planning is complete."""
        return self._state in (
            PlannerState.COMPLETED,
            PlannerState.FAILED,
            PlannerState.MAX_ITERATIONS,
        )

    async def run(self):
        """
        Run the planning loop, yielding each iteration.

        This is an async generator that yields PlannerIteration objects
        as they complete. Use async for to iterate:

            async for iteration in planner.run():
                process(iteration)
        """
        self._started_at = utc_now()
        self._state = PlannerState.OBSERVING

        logger.info(f"Starting planner for goal: {self.goal[:100]}...")

        while not self.is_complete:
            self._current_iteration += 1

            if self._current_iteration > self.config.max_iterations:
                self._state = PlannerState.MAX_ITERATIONS
                logger.warning(f"Max iterations ({self.config.max_iterations}) reached")
                break

            iteration = await self._run_iteration()
            self._history.append(iteration)

            yield iteration

            # Check for completion
            if iteration.state == PlannerState.COMPLETED:
                self._state = PlannerState.COMPLETED
            elif iteration.state == PlannerState.FAILED:
                self._state = PlannerState.FAILED
            elif iteration.planned_action is None:
                # No more actions to take - goal achieved
                self._state = PlannerState.COMPLETED

        self._completed_at = utc_now()
        logger.info(f"Planner completed in state: {self._state}")

    async def _run_iteration(self) -> PlannerIteration:
        """Run a single iteration of the planning loop."""
        iteration = PlannerIteration(
            iteration=self._current_iteration,
            state=PlannerState.OBSERVING,
        )

        try:
            # 1. OBSERVE
            self._state = PlannerState.OBSERVING
            iteration.state = PlannerState.OBSERVING
            observations = await self._observe()
            iteration.observations = observations

            # 2. THINK
            self._state = PlannerState.THINKING
            iteration.state = PlannerState.THINKING
            thoughts, planned_action = await self._think(observations)
            iteration.thoughts = thoughts
            iteration.planned_action = planned_action

            # 3. ACT (if action was planned)
            if planned_action:
                self._state = PlannerState.ACTING
                iteration.state = PlannerState.ACTING
                result = await self._act(planned_action)
                iteration.action_result = result

                # 4. REFLECT
                if self.config.enable_reflection:
                    self._state = PlannerState.REFLECTING
                    iteration.state = PlannerState.REFLECTING
                    reflection = await self._reflect(planned_action, result)
                    iteration.thoughts.append(reflection)
            else:
                # No action means goal achieved
                iteration.state = PlannerState.COMPLETED

            iteration.completed_at = utc_now()

        except asyncio.TimeoutError:
            iteration.state = PlannerState.FAILED
            iteration.error = f"Iteration timed out after {self.config.iteration_timeout_seconds}s"
            logger.error(iteration.error)

        except Exception as e:
            iteration.state = PlannerState.FAILED
            iteration.error = str(e)
            logger.exception(f"Iteration {self._current_iteration} failed")

        return iteration

    async def _observe(self) -> List[Observation]:
        """Gather observations from the environment."""
        observations = []

        # Get user-provided observations
        if callable(self.observe_fn):
            if asyncio.iscoroutinefunction(self.observe_fn):
                user_obs = await self.observe_fn()
            else:
                user_obs = self.observe_fn()
            observations.extend(user_obs)

        # Add iteration context as observation
        if self._history:
            last_iteration = self._history[-1]
            observations.append(Observation(
                source="iteration_history",
                content={
                    "last_iteration": last_iteration.iteration,
                    "last_action": last_iteration.planned_action.action_type if last_iteration.planned_action else None,
                    "last_result": last_iteration.action_result,
                }
            ))

        return observations

    async def _think(
        self,
        observations: List[Observation]
    ) -> tuple[List[Thought], Optional[PlannedAction]]:
        """Execute the thinking/reasoning step via LLM."""
        try:
            async with asyncio.timeout(self.config.iteration_timeout_seconds):
                thoughts, planned_action = await self.think_fn(
                    observations=observations,
                    history=self._history,
                    goal=self.goal,
                )

            # Validate action rationale if required
            if planned_action and self.config.require_action_rationale:
                if not planned_action.rationale:
                    logger.warning("Action planned without rationale")

            return thoughts, planned_action

        except asyncio.TimeoutError:
            error_thought = Thought(
                thought_type=ThoughtType.ERROR,
                content="Thinking timed out",
                confidence=0.0,
            )
            return [error_thought], None

    async def _act(self, planned_action: PlannedAction) -> Dict[str, Any]:
        """Execute the planned action through governance."""
        action_type = planned_action.action_type
        params = planned_action.params

        # Check governance policy
        policy = self.governance.check_execution_policy(action_type, params)

        if policy.is_blocked():
            return {
                "success": False,
                "error": "GOVERNANCE_BLOCKED",
                "reason": policy.reason,
            }

        if not policy.is_allowed():
            return {
                "success": False,
                "error": "GOVERNANCE_REQUIRES_PROPOSAL",
                "reason": policy.reason,
            }

        # Execute the action
        action_cls = action_registry.get(action_type)
        if not action_cls:
            return {
                "success": False,
                "error": "ACTION_NOT_FOUND",
                "action_type": action_type,
            }

        try:
            action = action_cls()
            context = ActionContext(actor_id=self.config.actor_id)
            result: ActionResult = await action.execute(params, context)

            return result.to_dict()

        except Exception as e:
            logger.exception(f"Action execution failed: {action_type}")
            return {
                "success": False,
                "error": str(e),
                "exception_type": type(e).__name__,
            }

    async def _reflect(
        self,
        planned_action: PlannedAction,
        result: Dict[str, Any]
    ) -> Thought:
        """Generate a reflection thought based on action result."""
        success = result.get("success", False)

        if success:
            content = (
                f"Action '{planned_action.action_type}' succeeded. "
                f"Result: {str(result)[:200]}"
            )
            confidence = 1.0
        else:
            error = result.get("error", "Unknown error")
            content = (
                f"Action '{planned_action.action_type}' failed. "
                f"Error: {error}. "
                f"Consider alternative approach."
            )
            confidence = 0.3

        return Thought(
            thought_type=ThoughtType.REFLECTION,
            content=content,
            confidence=confidence,
            metadata={
                "action_type": planned_action.action_type,
                "success": success,
            }
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the planning session."""
        return {
            "goal": self.goal,
            "state": self._state.value,
            "total_iterations": len(self._history),
            "max_iterations": self.config.max_iterations,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "completed_at": self._completed_at.isoformat() if self._completed_at else None,
            "actions_executed": sum(
                1 for i in self._history if i.planned_action and i.action_result
            ),
            "successful_actions": sum(
                1 for i in self._history
                if i.action_result and i.action_result.get("success", False)
            ),
        }


# =============================================================================
# SIMPLE PLANNER (Non-LLM version for testing)
# =============================================================================

class SimplePlanner:
    """
    Simple planner that executes a predefined list of actions.

    Useful for testing and scripted workflows without LLM reasoning.

    Usage:
        ```python
        actions = [
            PlannedAction(action_type="file.read", params={"path": "/tmp/x"}),
            PlannedAction(action_type="file.write", params={"path": "/tmp/y", "content": "data"}),
        ]

        planner = SimplePlanner(actions)
        results = await planner.execute_all()
        ```
    """

    def __init__(
        self,
        actions: List[PlannedAction],
        config: Optional[PlannerConfig] = None,
        governance: Optional[GovernanceEngine] = None,
    ):
        self.actions = actions
        self.config = config or PlannerConfig()
        self.governance = governance or GovernanceEngine(action_registry)
        self._results: List[Dict[str, Any]] = []

    @property
    def results(self) -> List[Dict[str, Any]]:
        """Get execution results."""
        return self._results.copy()

    async def execute_all(self) -> List[Dict[str, Any]]:
        """Execute all planned actions in sequence."""
        self._results = []

        for action in self.actions:
            result = await self._execute_action(action)
            self._results.append({
                "action": action.model_dump(),
                "result": result,
            })

            # Stop on failure
            if not result.get("success", False):
                break

        return self._results

    async def _execute_action(self, planned_action: PlannedAction) -> Dict[str, Any]:
        """Execute a single action."""
        action_type = planned_action.action_type
        params = planned_action.params

        # Check governance
        policy = self.governance.check_execution_policy(action_type, params)
        if policy.is_blocked() or not policy.is_allowed():
            return {
                "success": False,
                "error": "GOVERNANCE_POLICY",
                "reason": policy.reason,
            }

        # Execute
        action_cls = action_registry.get(action_type)
        if not action_cls:
            return {"success": False, "error": "ACTION_NOT_FOUND"}

        try:
            action = action_cls()
            context = ActionContext(actor_id=self.config.actor_id)
            result = await action.execute(params, context)
            return result.to_dict()
        except Exception as e:
            return {"success": False, "error": str(e)}


__all__ = [
    "PlannerState",
    "ThoughtType",
    "Observation",
    "Thought",
    "PlannedAction",
    "PlannerIteration",
    "PlannerConfig",
    "ThinkingFunction",
    "AgentPlanner",
    "SimplePlanner",
]
