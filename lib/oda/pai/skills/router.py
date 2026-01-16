"""
Orion ODA v4.0 - Skill Router (LLM-Native)
==========================================

Skill routing system for PAI.

Routes user input to the appropriate skill using LLM-based intent classification.
Manages skill registration, priority resolution, and execution delegation.

V4.0 CHANGES (2026-01-13):
    - Replaced TriggerDetector with IntentClassifier
    - LLM-Native semantic understanding
    - No keywords, no regex, no Jaccard
    - User requirement: "복잡한 과정 필요없이 LLM에게만 맡기려고 함"

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
# V4.0: Replace TriggerDetector with IntentClassifier (LLM-Native)
from .intent_classifier import (
    IntentClassifier,
    IntentResult,
    IntentClassifierConfig,
    CommandDescription,
    convert_to_trigger_match,
)
from lib.oda.llm.intent_adapter import IntentMatchType

# V4.0: Context Injection System
from .context_injector import (
    ContextInjector,
    InjectedContext,
    inject_context,
)


# =============================================================================
# ROUTE RESULT
# =============================================================================


@dataclass
class RouteResult:
    """
    Result of skill routing.

    Contains the matched skill (if any) and routing metadata.

    V4.0: Enhanced with IntentResult for LLM-based classification.
    """

    matched: bool
    skill: Optional[SkillDefinition] = None
    trigger: Optional[SkillTrigger] = None
    match_score: float = 0.0
    alternatives: List[SkillDefinition] = field(default_factory=list)
    routing_time_ms: float = 0.0

    # V4.0: LLM classification result
    intent_result: Optional[IntentResult] = None
    needs_clarification: bool = False
    reasoning: str = ""

    # V4.0: Injected context for skill execution
    injected_context: Optional[InjectedContext] = None

    @property
    def skill_name(self) -> Optional[str]:
        """Get matched skill name if available."""
        return self.skill.name if self.skill else None

    @property
    def confidence(self) -> float:
        """Get classification confidence."""
        if self.intent_result:
            return self.intent_result.confidence
        return self.match_score

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

    def __init__(
        self,
        adapter_type: str = "claude",
        clarification_threshold: float = 0.7
    ):
        """
        Initialize skill router.

        V4.0: Uses IntentClassifier instead of TriggerDetector.

        Args:
            adapter_type: LLM adapter type (claude, openai, gemini, local)
            clarification_threshold: Confidence below which to ask for clarification
        """
        self._skills: Dict[str, SkillDefinition] = {}
        # V4.0: Replace TriggerDetector with IntentClassifier
        self._classifier = IntentClassifier(
            config=IntentClassifierConfig(
                adapter_type=adapter_type,
                clarification_threshold=clarification_threshold,
            )
        )
        self._execution_history: List[SkillExecution] = []
        self._command_map: Dict[str, str] = {}  # command -> skill_name mapping
        # V4.0: Context Injector for automatic reference loading
        self._context_injector = ContextInjector()

    def register(self, skill: SkillDefinition, command: Optional[str] = None) -> None:
        """
        Register a skill.

        V4.0: Also registers with IntentClassifier for LLM-based routing.

        Args:
            skill: SkillDefinition to register
            command: Optional command name (e.g., "/audit"). If not provided,
                    uses "/" + skill.name

        Raises:
            ValueError: If skill with same name already exists
        """
        if skill.name in self._skills:
            raise ValueError(f"Skill '{skill.name}' is already registered")

        self._skills[skill.name] = skill

        # V4.0: Register command for LLM-based routing
        cmd = command or f"/{skill.name}"
        self._command_map[cmd] = skill.name

        # Add to classifier's available commands
        self._classifier.add_command(CommandDescription(
            name=cmd,
            description=skill.description or f"Execute {skill.name} skill",
            examples=self._extract_examples(skill)
        ))

    def unregister(self, skill_name: str) -> bool:
        """
        Unregister a skill.

        Args:
            skill_name: Name of skill to unregister

        Returns:
            True if skill was unregistered, False if not found
        """
        if skill_name in self._skills:
            del self._skills[skill_name]
            # V4.0: Also unregister from classifier
            cmd = f"/{skill_name}"
            self._classifier.remove_command(cmd)
            if cmd in self._command_map:
                del self._command_map[cmd]
            return True
        return False

    def _extract_examples(self, skill: SkillDefinition) -> List[str]:
        """
        Extract example trigger phrases from skill.

        V4.0: Converts legacy trigger keywords to examples.
        """
        examples = []
        triggers = getattr(skill, 'triggers', [])
        for trigger in triggers:
            if hasattr(trigger, 'keywords'):
                examples.extend(trigger.keywords[:3])  # Take up to 3
            if hasattr(trigger, 'examples'):
                examples.extend(trigger.examples[:3])
        return examples[:5]  # Max 5 examples

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
        Route user input to appropriate skill using LLM-based classification.

        V4.0: Uses IntentClassifier instead of TriggerDetector.

        Args:
            user_input: User's input text
            context: Optional context for routing decisions (reserved for future use)

        Returns:
            RouteResult with matched skill (if any)
        """
        import asyncio
        start_time = utc_now()

        # V4.0: Use LLM-based intent classification
        try:
            # Run async classifier in sync context
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in async context, create new loop
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self._classifier.classify(user_input)
                    )
                    intent_result = future.result()
            else:
                intent_result = asyncio.run(self._classifier.classify(user_input))
        except Exception as e:
            # Fallback on error
            from lib.oda.llm.intent_adapter import IntentResult
            intent_result = IntentResult(
                command="none",
                confidence=0.0,
                reasoning=f"Classification error: {str(e)}",
                match_type=IntentMatchType.FALLBACK,
                raw_input=user_input
            )

        routing_time = (utc_now() - start_time).total_seconds() * 1000

        # Check if no match
        if intent_result.command == "none" or intent_result.confidence < 0.3:
            return RouteResult(
                matched=False,
                routing_time_ms=routing_time,
                intent_result=intent_result,
                reasoning=intent_result.reasoning,
            )

        # Map command to skill
        skill_name = self._command_map.get(intent_result.command)
        if not skill_name:
            # Try stripping leading slash
            skill_name = intent_result.command.lstrip('/')

        skill = self._skills.get(skill_name)
        if not skill or skill.skill_status != SkillStatus.ACTIVE:
            return RouteResult(
                matched=False,
                routing_time_ms=routing_time,
                intent_result=intent_result,
                reasoning=f"Skill '{skill_name}' not found or inactive",
            )

        # Check if clarification needed
        needs_clarification = self._classifier.needs_clarification(intent_result)

        # V4.0: Inject context before skill execution
        injected_context = self._context_injector.inject(
            skill_name=skill_name,
            user_input=user_input,
            include_plan=True,
        )

        return RouteResult(
            matched=True,
            skill=skill,
            match_score=intent_result.confidence,
            alternatives=[],
            routing_time_ms=routing_time,
            intent_result=intent_result,
            needs_clarification=needs_clarification,
            reasoning=intent_result.reasoning,
            injected_context=injected_context,
        )

    async def route_async(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> RouteResult:
        """
        Async version of route() for async contexts.

        V4.0: Native async routing.
        """
        start_time = utc_now()

        intent_result = await self._classifier.classify(user_input)

        routing_time = (utc_now() - start_time).total_seconds() * 1000

        if intent_result.command == "none" or intent_result.confidence < 0.3:
            return RouteResult(
                matched=False,
                routing_time_ms=routing_time,
                intent_result=intent_result,
                reasoning=intent_result.reasoning,
            )

        skill_name = self._command_map.get(intent_result.command)
        if not skill_name:
            skill_name = intent_result.command.lstrip('/')

        skill = self._skills.get(skill_name)
        if not skill or skill.skill_status != SkillStatus.ACTIVE:
            return RouteResult(
                matched=False,
                routing_time_ms=routing_time,
                intent_result=intent_result,
                reasoning=f"Skill '{skill_name}' not found or inactive",
            )

        needs_clarification = self._classifier.needs_clarification(intent_result)

        # V4.0: Inject context before skill execution
        injected_context = self._context_injector.inject(
            skill_name=skill_name,
            user_input=user_input,
            include_plan=True,
        )

        return RouteResult(
            matched=True,
            skill=skill,
            match_score=intent_result.confidence,
            alternatives=[],
            routing_time_ms=routing_time,
            intent_result=intent_result,
            needs_clarification=needs_clarification,
            reasoning=intent_result.reasoning,
            injected_context=injected_context,
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
