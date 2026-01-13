"""
Orion ODA v3.0 - Skill Router
==============================

Skill routing system for PAI.

Routes user input to the appropriate skill based on trigger matching.
Manages skill registration, priority resolution, and execution delegation.

ActionTypes:
    - RouteToSkillAction: Route input to matched skill
    - RegisterSkillAction: Register a new skill (hazardous)

Reference: PAI prompting skill routing patterns
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional, Callable

from pydantic import Field

from lib.oda.ontology.ontology_types import OntologyObject, utc_now
from lib.oda.ontology.registry import register_object_type

from .skill_definition import (
    SkillDefinition,
    SkillTrigger,
    SkillExecution,
    SkillStatus,
    TriggerPriority,
    ExecutionStatus,
)
from .trigger_detector import TriggerDetector, TriggerMatch


# =============================================================================
# ROUTE RESULT
# =============================================================================


@dataclass
class RouteResult:
    """
    Result of skill routing.

    Contains the matched skill (if any) and routing metadata.
    """

    matched: bool
    skill: Optional[SkillDefinition] = None
    trigger: Optional[SkillTrigger] = None
    match_score: float = 0.0
    alternatives: List[SkillDefinition] = field(default_factory=list)
    routing_time_ms: float = 0.0

    @property
    def skill_name(self) -> Optional[str]:
        """Get matched skill name if available."""
        return self.skill.name if self.skill else None

    def __bool__(self) -> bool:
        """RouteResult is truthy if a skill was matched."""
        return self.matched


# =============================================================================
# SKILL ROUTER
# =============================================================================


class SkillRouter:
    """
    Skill routing orchestrator.

    Manages skill registration and routes user input to appropriate skills.

    Usage:
        ```python
        router = SkillRouter()

        # Register skills
        router.register(commit_skill)
        router.register(review_skill)

        # Route input
        result = router.route("Please commit my changes")
        if result:
            print(f"Matched: {result.skill_name}")
        else:
            print("No skill matched")

        # Execute matched skill
        if result.matched:
            execution = router.execute(result.skill, user_input)
        ```
    """

    def __init__(self):
        """Initialize skill router."""
        self._skills: Dict[str, SkillDefinition] = {}
        self._detector = TriggerDetector()
        self._execution_history: List[SkillExecution] = []

    def register(self, skill: SkillDefinition) -> None:
        """
        Register a skill.

        Args:
            skill: SkillDefinition to register (with triggers attribute)

        Raises:
            ValueError: If skill with same name already exists
        """
        if skill.name in self._skills:
            raise ValueError(f"Skill '{skill.name}' is already registered")

        self._skills[skill.name] = skill

        # Register with detector if skill has triggers
        triggers = getattr(skill, 'triggers', [])
        if triggers:
            self._detector.register_skill(skill, triggers)

    def unregister(self, skill_name: str) -> bool:
        """
        Unregister a skill.

        Args:
            skill_name: Name of skill to unregister

        Returns:
            True if skill was unregistered, False if not found
        """
        if skill_name in self._skills:
            skill = self._skills[skill_name]
            del self._skills[skill_name]
            # Also unregister from detector
            self._detector.unregister_skill(skill.id)
            return True
        return False

    def get_skill(self, name: str) -> Optional[SkillDefinition]:
        """Get a skill by name."""
        return self._skills.get(name)

    def list_skills(self, active_only: bool = True) -> List[SkillDefinition]:
        """
        List registered skills.

        Args:
            active_only: If True, only return active skills

        Returns:
            List of SkillDefinition objects
        """
        skills = list(self._skills.values())
        if active_only:
            skills = [s for s in skills if s.skill_status == SkillStatus.ACTIVE]
        return skills

    def route(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> RouteResult:
        """
        Route user input to appropriate skill.

        Args:
            user_input: User's input text
            context: Optional context for routing decisions (reserved for future use)

        Returns:
            RouteResult with matched skill (if any)
        """
        start_time = utc_now()

        # Use the detector to find matches
        # The detector was populated during skill registration
        match = self._detector.detect(user_input)

        routing_time = (utc_now() - start_time).total_seconds() * 1000

        if not match.matched:
            return RouteResult(
                matched=False,
                routing_time_ms=routing_time,
            )

        # Look up the matched skill
        skill = self._skills.get(match.skill_name)
        if not skill or skill.skill_status != SkillStatus.ACTIVE:
            return RouteResult(
                matched=False,
                routing_time_ms=routing_time,
            )

        return RouteResult(
            matched=True,
            skill=skill,
            trigger=match.trigger,
            match_score=match.confidence,
            alternatives=[],  # Could be enhanced with detector.detect_all()
            routing_time_ms=routing_time,
        )

    def route_by_name(self, skill_name: str) -> RouteResult:
        """
        Route directly to a skill by name.

        Useful for explicit skill invocation (e.g., /commit).

        Args:
            skill_name: Name of skill to route to

        Returns:
            RouteResult with matched skill
        """
        skill = self._skills.get(skill_name)

        if skill and skill.skill_status == SkillStatus.ACTIVE:
            return RouteResult(
                matched=True,
                skill=skill,
                match_score=1.0,  # Exact match
            )

        return RouteResult(matched=False)

    def execute(
        self,
        skill: SkillDefinition,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        executor: Optional[Callable[[SkillDefinition, str, Dict], Any]] = None,
    ) -> SkillExecution:
        """
        Execute a skill.

        Args:
            skill: Skill to execute
            user_input: User input that triggered the skill
            context: Optional execution context
            executor: Optional custom executor function

        Returns:
            SkillExecution record
        """
        start_time = utc_now()
        execution = SkillExecution(
            skill_name=skill.name,
            input_text=user_input[:1000],  # Truncate for storage
            execution_status=ExecutionStatus.SUCCESS,
        )

        try:
            if executor:
                output = executor(skill, user_input, context or {})
                execution.output_text = str(output)[:5000]  # Truncate
            else:
                # Default execution: return skill prompt
                execution.output_text = skill.description

            execution.execution_status = ExecutionStatus.SUCCESS

        except TimeoutError:
            execution.execution_status = ExecutionStatus.TIMEOUT
            execution.output_text = "Execution timed out"

        except Exception as e:
            execution.execution_status = ExecutionStatus.FAILURE
            execution.output_text = f"Error: {str(e)}"

        finally:
            execution.duration_ms = int((utc_now() - start_time).total_seconds() * 1000)
            self._execution_history.append(execution)

        return execution

    def get_execution_history(
        self,
        skill_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[SkillExecution]:
        """
        Get execution history.

        Args:
            skill_name: Filter by skill name (optional)
            limit: Maximum records to return

        Returns:
            List of SkillExecution records
        """
        history = self._execution_history

        if skill_name:
            history = [e for e in history if e.skill_name == skill_name]

        return history[-limit:]


# =============================================================================
# ACTION TYPES
# =============================================================================


class RouteToSkillAction:
    """
    Action to route input to a skill.

    Non-hazardous action that performs skill routing.
    """

    api_name: ClassVar[str] = "route_to_skill"
    display_name: ClassVar[str] = "Route to Skill"
    description: ClassVar[str] = "Route user input to matching skill"
    is_hazardous: ClassVar[bool] = False

    def __init__(
        self,
        user_input: str,
        router: Optional[SkillRouter] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize routing action.

        Args:
            user_input: User input to route
            router: Optional SkillRouter (uses default if not provided)
            context: Optional routing context
        """
        self.user_input = user_input
        self.router = router or SkillRouter()
        self.context = context

    def execute(self) -> RouteResult:
        """Execute skill routing."""
        return self.router.route(self.user_input, self.context)


class RegisterSkillAction:
    """
    Action to register a new skill.

    HAZARDOUS: Modifies the skill registry (schema change).
    Requires approval via Proposal system.
    """

    api_name: ClassVar[str] = "register_skill"
    display_name: ClassVar[str] = "Register Skill"
    description: ClassVar[str] = "Register a new skill in the router"
    is_hazardous: ClassVar[bool] = True  # Schema change

    def __init__(
        self,
        skill: SkillDefinition,
        router: SkillRouter,
    ):
        """
        Initialize registration action.

        Args:
            skill: Skill to register
            router: SkillRouter to register in
        """
        self.skill = skill
        self.router = router

    def execute(self) -> Dict[str, Any]:
        """
        Execute skill registration.

        Returns:
            Registration result with skill details
        """
        self.router.register(self.skill)
        return {
            "registered": True,
            "skill_name": self.skill.name,
            "trigger_count": len(self.skill.triggers),
            "tool_count": len(self.skill.tools),
        }

    def get_proposal_description(self) -> str:
        """Get description for Proposal system."""
        return (
            f"Register new skill '{self.skill.name}' with "
            f"{len(self.skill.triggers)} triggers and "
            f"{len(self.skill.tools)} tools"
        )
