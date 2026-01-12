"""
ODA PAI Algorithm - Universal Algorithm
========================================

THE ALGORITHM: Current State → Ideal State through iteration.

This is the core orchestration engine that drives task execution
from Current State to Ideal State using registered capabilities
and ISC (Ideal State Contract) validation.

Phases (7-Phase Algorithm):
    1. OBSERVE: Analyze current state and context
    2. INTERPRET: Understand task, set effort level
    3. THINK: Cognitive analysis and capability routing
    4. PLAN: Build ISC with success criteria
    5. BUILD: Infrastructure and agent setup
    6. EXECUTE: Run capabilities to complete ISC rows
    7. VERIFY: Validate all success criteria met
    8. LEARN: Feedback loop and pattern extraction (iterative)

Migrated from: PAI TypeScript Universal Algorithm patterns
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field

from lib.oda.ontology.ontology_types import OntologyObject, utc_now
from lib.oda.ontology.registry import register_object_type

from .effort_levels import EffortLevel
from .isc_manager import ISCTable, ISCRow, ISCPhase, ISCRowStatus


class AlgorithmPhase(str, Enum):
    """
    Phases of THE ALGORITHM execution (7-Phase Algorithm).

    The algorithm progresses through these phases sequentially,
    with iteration possible between EXECUTE, VERIFY, and LEARN.
    """

    OBSERVE = "observe"       # Analyze current state
    INTERPRET = "interpret"   # Understand task, classify effort
    THINK = "think"          # Cognitive analysis and capability routing
    PLAN = "plan"            # Build ISC with success criteria
    BUILD = "build"          # Infrastructure and agent setup
    EXECUTE = "execute"      # Run capabilities to fulfill ISC
    VERIFY = "verify"        # Validate success criteria
    LEARN = "learn"          # Feedback loop and pattern extraction
    COMPLETE = "complete"    # All criteria met, task done


@dataclass
class AlgorithmContext:
    """
    Runtime context for algorithm execution.

    Contains all state needed during algorithm run:
    - Original request and classified effort
    - Current ISC state
    - Execution history
    - Available capabilities (filtered by effort)
    """

    request: str
    effort: EffortLevel
    isc: Optional[ISCTable] = None
    current_phase: AlgorithmPhase = AlgorithmPhase.OBSERVE
    iteration: int = 0
    max_iterations: int = 10
    execution_log: List[Dict[str, Any]] = field(default_factory=list)
    capabilities_used: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=utc_now)
    completed_at: Optional[datetime] = None
    # 7-Phase Algorithm additions
    observed_state: Dict[str, Any] = field(default_factory=dict)    # OBSERVE results
    thinking_results: Dict[str, Any] = field(default_factory=dict)  # THINK results
    build_config: Dict[str, Any] = field(default_factory=dict)      # BUILD configuration
    learning_insights: List[Dict[str, Any]] = field(default_factory=list)  # LEARN results

    def log_action(self, action: str, details: Dict[str, Any]) -> None:
        """Log an action to the execution log."""
        self.execution_log.append({
            "timestamp": utc_now().isoformat(),
            "iteration": self.iteration,
            "phase": self.current_phase.value,
            "action": action,
            "details": details,
        })

    def can_iterate(self) -> bool:
        """Check if more iterations are allowed."""
        return self.iteration < self.max_iterations


@dataclass
class AlgorithmResult:
    """
    Result of algorithm execution.

    Contains final state and metadata about the execution:
    - Success/failure status
    - Final ISC state
    - Execution statistics
    - Any error information
    """

    success: bool
    isc: Optional[ISCTable]
    final_phase: AlgorithmPhase
    iterations: int
    capabilities_used: List[str]
    duration_ms: float
    error: Optional[str] = None
    execution_log: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def summary(self) -> str:
        """Generate human-readable summary of execution."""
        status = "SUCCESS" if self.success else "FAILED"
        return (
            f"Algorithm {status}: {self.iterations} iterations, "
            f"{len(self.capabilities_used)} capabilities used, "
            f"{self.duration_ms:.2f}ms"
        )


class UniversalAlgorithm:
    """
    THE ALGORITHM: Universal task execution engine.

    Drives tasks from Current State to Ideal State through
    iterative capability execution guided by ISC validation.

    Usage:
        ```python
        algorithm = UniversalAlgorithm(effort=EffortLevel.STANDARD)

        # Simple execution
        result = algorithm.execute(
            request="Implement user authentication",
            isc=my_isc_table,
        )

        # With custom callbacks
        result = algorithm.execute(
            request="Complex refactoring task",
            isc=my_isc_table,
            on_phase_change=my_phase_callback,
            on_capability_used=my_capability_callback,
        )
        ```
    """

    def __init__(
        self,
        effort: EffortLevel = EffortLevel.STANDARD,
        max_iterations: Optional[int] = None,
    ):
        """
        Initialize the algorithm.

        Args:
            effort: Effort level (determines available capabilities)
            max_iterations: Override default max iterations
        """
        self.effort = effort
        self.max_iterations = max_iterations or self._default_max_iterations()
        self._capability_registry: Optional[Any] = None  # Lazy load

    def _default_max_iterations(self) -> int:
        """Get default max iterations based on effort level."""
        defaults = {
            EffortLevel.TRIVIAL: 1,
            EffortLevel.QUICK: 3,
            EffortLevel.STANDARD: 10,
            EffortLevel.THOROUGH: 25,
            EffortLevel.DETERMINED: 100,
        }
        return defaults.get(self.effort, 10)

    def execute(
        self,
        request: str,
        isc: Optional[ISCTable] = None,
        on_phase_change: Optional[Callable[[AlgorithmPhase], None]] = None,
        on_capability_used: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> AlgorithmResult:
        """
        Execute the algorithm for a given request.

        Args:
            request: The user's request/task
            isc: Pre-built ISC table (optional, will be created if not provided)
            on_phase_change: Callback when phase changes
            on_capability_used: Callback when a capability is used

        Returns:
            AlgorithmResult with execution details
        """
        start_time = utc_now()

        # Initialize context
        context = AlgorithmContext(
            request=request,
            effort=self.effort,
            isc=isc,
            max_iterations=self.max_iterations,
        )

        try:
            # Phase 1: OBSERVE (NEW)
            context = self._observe_phase(context, on_phase_change)

            # Phase 2: INTERPRET
            context = self._interpret_phase(context, on_phase_change)

            # Phase 3: THINK (NEW)
            context = self._think_phase(context, on_phase_change)

            # Phase 4: PLAN
            context = self._plan_phase(context, on_phase_change)

            # Phase 5: BUILD (NEW)
            context = self._build_phase(context, on_phase_change)

            # Phases 6, 7, 8: EXECUTE, VERIFY, LEARN (iterative)
            while context.can_iterate() and context.current_phase != AlgorithmPhase.COMPLETE:
                context.iteration += 1

                # Execute
                context = self._execute_phase(context, on_phase_change, on_capability_used)

                # Verify
                context = self._verify_phase(context, on_phase_change)

                # Learn (NEW - after each verify)
                if context.current_phase != AlgorithmPhase.COMPLETE:
                    context = self._learn_phase(context, on_phase_change)

            context.completed_at = utc_now()

            return AlgorithmResult(
                success=context.current_phase == AlgorithmPhase.COMPLETE,
                isc=context.isc,
                final_phase=context.current_phase,
                iterations=context.iteration,
                capabilities_used=context.capabilities_used,
                duration_ms=(context.completed_at - start_time).total_seconds() * 1000,
                execution_log=context.execution_log,
            )

        except Exception as e:
            return AlgorithmResult(
                success=False,
                isc=context.isc,
                final_phase=context.current_phase,
                iterations=context.iteration,
                capabilities_used=context.capabilities_used,
                duration_ms=(utc_now() - start_time).total_seconds() * 1000,
                error=str(e),
                execution_log=context.execution_log,
            )

    def _interpret_phase(
        self,
        context: AlgorithmContext,
        on_phase_change: Optional[Callable[[AlgorithmPhase], None]] = None,
    ) -> AlgorithmContext:
        """
        INTERPRET Phase: Understand the task and validate effort level.

        Actions:
        - Parse and understand the request
        - Validate effort level is appropriate
        - Identify key requirements
        """
        context.current_phase = AlgorithmPhase.INTERPRET
        if on_phase_change:
            on_phase_change(AlgorithmPhase.INTERPRET)

        context.log_action("interpret_start", {
            "request": context.request,
            "effort": context.effort.value,
        })

        # In production, this would analyze the request
        # For now, we validate and proceed
        context.log_action("interpret_complete", {
            "understood": True,
            "effort_appropriate": True,
        })

        return context

    def _plan_phase(
        self,
        context: AlgorithmContext,
        on_phase_change: Optional[Callable[[AlgorithmPhase], None]] = None,
    ) -> AlgorithmContext:
        """
        PLAN Phase: Build or validate ISC with success criteria.

        Actions:
        - If ISC not provided, generate one from request
        - Validate ISC structure
        - Set ISC phase to PLAN
        """
        context.current_phase = AlgorithmPhase.PLAN
        if on_phase_change:
            on_phase_change(AlgorithmPhase.PLAN)

        context.log_action("plan_start", {
            "has_existing_isc": context.isc is not None,
        })

        # If no ISC provided, we would generate one
        # For now, validate existing ISC
        if context.isc:
            context.log_action("plan_isc_validated", {
                "row_count": len(context.isc.rows) if hasattr(context.isc, 'rows') else 0,
            })
        else:
            context.log_action("plan_isc_generated", {
                "auto_generated": True,
            })

        return context

    def _execute_phase(
        self,
        context: AlgorithmContext,
        on_phase_change: Optional[Callable[[AlgorithmPhase], None]] = None,
        on_capability_used: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> AlgorithmContext:
        """
        EXECUTE Phase: Run capabilities to fulfill ISC rows.

        Actions:
        - Identify pending ISC rows
        - Select appropriate capabilities
        - Execute capabilities (potentially in parallel)
        - Update ISC row statuses
        """
        context.current_phase = AlgorithmPhase.EXECUTE
        if on_phase_change:
            on_phase_change(AlgorithmPhase.EXECUTE)

        context.log_action("execute_start", {
            "iteration": context.iteration,
        })

        # In production, this would:
        # 1. Get pending ISC rows
        # 2. Select capabilities based on effort level
        # 3. Execute capabilities
        # 4. Update row statuses

        context.log_action("execute_complete", {
            "capabilities_run": 0,  # Would be actual count
            "rows_updated": 0,      # Would be actual count
        })

        return context

    def _verify_phase(
        self,
        context: AlgorithmContext,
        on_phase_change: Optional[Callable[[AlgorithmPhase], None]] = None,
    ) -> AlgorithmContext:
        """
        VERIFY Phase: Validate all success criteria are met.

        Actions:
        - Check each ISC row status
        - If all COMPLETED, transition to COMPLETE
        - If not all done and iterations remain, return to EXECUTE
        - If iterations exhausted, report incomplete
        """
        context.current_phase = AlgorithmPhase.VERIFY
        if on_phase_change:
            on_phase_change(AlgorithmPhase.VERIFY)

        context.log_action("verify_start", {
            "iteration": context.iteration,
        })

        # In production, check actual ISC row statuses
        # For now, simulate completion check
        all_complete = True  # Would check actual rows

        if all_complete:
            context.current_phase = AlgorithmPhase.COMPLETE
            context.log_action("verify_complete", {
                "all_criteria_met": True,
            })
        else:
            context.log_action("verify_incomplete", {
                "all_criteria_met": False,
                "remaining_iterations": context.max_iterations - context.iteration,
            })

        return context

    def _observe_phase(
        self,
        context: AlgorithmContext,
        on_phase_change: Optional[Callable[[AlgorithmPhase], None]] = None,
    ) -> AlgorithmContext:
        """
        OBSERVE Phase: Analyze current state before task interpretation.

        Actions:
        - Collect baseline metrics
        - Analyze context and environment
        - Identify available resources and constraints
        - Prepare observation data for INTERPRET phase
        """
        context.current_phase = AlgorithmPhase.OBSERVE
        if on_phase_change:
            on_phase_change(AlgorithmPhase.OBSERVE)

        context.log_action("observe_start", {
            "request_length": len(context.request),
            "effort": context.effort.value,
        })

        # Collect observed state
        context.observed_state = {
            "request_analyzed": True,
            "effort_level": context.effort.value,
            "has_existing_isc": context.isc is not None,
            "max_iterations": context.max_iterations,
            "available_capabilities": self.get_available_capabilities(),
        }

        context.log_action("observe_complete", {
            "observed_state_keys": list(context.observed_state.keys()),
        })

        return context

    def _think_phase(
        self,
        context: AlgorithmContext,
        on_phase_change: Optional[Callable[[AlgorithmPhase], None]] = None,
    ) -> AlgorithmContext:
        """
        THINK Phase: Cognitive analysis and capability routing.

        Actions:
        - Analyze task complexity
        - Route to appropriate thinking capabilities (ultrathink, tree_of_thought)
        - Enhance ISC rows with analysis
        - Determine optimal execution strategy
        """
        context.current_phase = AlgorithmPhase.THINK
        if on_phase_change:
            on_phase_change(AlgorithmPhase.THINK)

        context.log_action("think_start", {
            "isc_rows": len(context.isc.rows) if context.isc and hasattr(context.isc, 'rows') else 0,
        })

        # Determine complexity and thinking strategy
        isc_row_count = len(context.isc.rows) if context.isc and hasattr(context.isc, 'rows') else 0
        use_deep_thinking = (
            context.effort.value in ("thorough", "determined") or
            isc_row_count > 5
        )

        context.thinking_results = {
            "complexity_assessed": True,
            "use_deep_thinking": use_deep_thinking,
            "thinking_capability": "tree_of_thought" if use_deep_thinking else "standard",
            "strategy": "parallel" if context.effort.value in ("standard", "thorough", "determined") else "sequential",
        }

        context.log_action("think_complete", {
            "thinking_strategy": context.thinking_results.get("strategy"),
            "use_deep_thinking": use_deep_thinking,
        })

        return context

    def _build_phase(
        self,
        context: AlgorithmContext,
        on_phase_change: Optional[Callable[[AlgorithmPhase], None]] = None,
    ) -> AlgorithmContext:
        """
        BUILD Phase: Infrastructure and agent setup.

        Actions:
        - Configure parallel execution based on effort level
        - Setup capability execution contexts
        - Prepare agent composition if needed
        - Configure execution parameters
        """
        context.current_phase = AlgorithmPhase.BUILD
        if on_phase_change:
            on_phase_change(AlgorithmPhase.BUILD)

        context.log_action("build_start", {
            "thinking_strategy": context.thinking_results.get("strategy"),
        })

        # Get max concurrent from effort level
        max_concurrent_map = {
            "trivial": 1,
            "quick": 1,
            "standard": 3,
            "thorough": 5,
            "determined": 10,
        }
        max_concurrent = max_concurrent_map.get(context.effort.value, 1)

        context.build_config = {
            "max_concurrent": max_concurrent,
            "parallel_enabled": max_concurrent > 1,
            "execution_mode": context.thinking_results.get("strategy", "sequential"),
            "capabilities_prepared": self.get_available_capabilities(),
        }

        context.log_action("build_complete", {
            "max_concurrent": max_concurrent,
            "parallel_enabled": context.build_config["parallel_enabled"],
        })

        return context

    def _learn_phase(
        self,
        context: AlgorithmContext,
        on_phase_change: Optional[Callable[[AlgorithmPhase], None]] = None,
    ) -> AlgorithmContext:
        """
        LEARN Phase: Feedback loop and pattern extraction.

        Actions:
        - Analyze execution log for patterns
        - Extract insights from verify results
        - Record metrics for optimization
        - Update learning insights for future iterations
        """
        context.current_phase = AlgorithmPhase.LEARN
        if on_phase_change:
            on_phase_change(AlgorithmPhase.LEARN)

        context.log_action("learn_start", {
            "iteration": context.iteration,
            "execution_log_entries": len(context.execution_log),
        })

        # Analyze execution patterns
        verify_entries = [
            e for e in context.execution_log
            if e.get("action", "").startswith("verify_")
        ]
        execute_entries = [
            e for e in context.execution_log
            if e.get("action", "").startswith("execute_")
        ]

        insight = {
            "iteration": context.iteration,
            "verify_count": len(verify_entries),
            "execute_count": len(execute_entries),
            "capabilities_used": len(context.capabilities_used),
            "pattern": "iterative" if context.iteration > 1 else "single_pass",
        }
        context.learning_insights.append(insight)

        context.log_action("learn_complete", {
            "insight_count": len(context.learning_insights),
            "latest_pattern": insight.get("pattern"),
        })

        return context

    def get_available_capabilities(self) -> List[str]:
        """
        Get list of capabilities available at current effort level.

        Returns:
            List of capability names unlocked at this effort level
        """
        # Would query CapabilityRegistry
        # For now, return representative list based on effort
        effort_capabilities = {
            EffortLevel.TRIVIAL: [],
            EffortLevel.QUICK: ["haiku", "intern"],
            EffortLevel.STANDARD: ["haiku", "sonnet", "intern", "researcher", "engineer"],
            EffortLevel.THOROUGH: [
                "haiku", "sonnet", "opus", "intern", "researcher",
                "engineer", "architect", "council", "plan_mode"
            ],
            EffortLevel.DETERMINED: [
                "haiku", "sonnet", "opus", "intern", "researcher",
                "engineer", "architect", "council", "plan_mode",
                "redteam", "ultrathink", "tree_of_thought"
            ],
        }
        return effort_capabilities.get(self.effort, [])
