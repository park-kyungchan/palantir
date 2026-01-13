"""
Orion ODA PAI - Skills Module (v4.0 LLM-Native)

Skill routing and execution system for PAI.

V4.0 CHANGES (2026-01-13):
- TriggerDetector REMOVED - replaced by IntentClassifier
- LLM-Native semantic understanding
- No keywords, no regex, no Jaccard
- User requirement: "복잡한 과정 필요없이 LLM에게만 맡기려고 함"

This module provides the infrastructure for skill management:
- SkillDefinition: Skill metadata and configuration
- IntentClassifier: LLM-based intent classification (NEW)
- Workflow: Multi-step workflow definitions
- Router: Skill routing orchestration

Key Components:
- SkillDefinition: name, description, triggers, tools, model
- IntentClassifier: LLM-based semantic understanding (V4.0)
- Workflow, WorkflowStep: Multi-step execution
- SkillExecution: Execution record for audit
- SkillRouter: Main routing orchestrator

Usage:
    ```python
    from lib.oda.pai.skills import (
        SkillDefinition,
        SkillRouter,
        IntentClassifier,
        IntentResult,
    )

    # Route user input using LLM-based classification
    router = SkillRouter()
    result = router.route("코드 리뷰해줘")
    # result.skill_name -> "audit"
    # result.confidence -> 0.92
    # result.reasoning -> "User requests code review"
    ```

Version: 4.0.0
"""

from lib.oda.pai.skills.skill_definition import (
    SkillDefinition,
    SkillTrigger,
    SkillExecution,
    SkillStatus,
    TriggerPriority,
    ExecutionStatus,
)

# V4.0: Replace TriggerDetector with IntentClassifier
from lib.oda.pai.skills.intent_classifier import (
    IntentClassifier,
    IntentClassifierConfig,
    IntentResult,
    CommandDescription,
    create_intent_classifier,
    get_default_commands,
    LegacyTriggerMatch,  # Backward compatibility
    convert_to_trigger_match,
    # V4.0: Low-Confidence Clarification Flow
    ClarificationRequest,
    ClarificationFlow,
)
from lib.oda.llm.intent_adapter import (
    IntentMatchType,
    IntentAdapter,
)

from lib.oda.pai.skills.workflow import (
    Workflow,
    WorkflowStep,
    StepStatus,
)

# Import workflow execution types from ontology actions
from lib.oda.ontology.actions.workflow_actions import (
    WorkflowExecution,
    ExecuteWorkflowAction,
)

from lib.oda.pai.skills.router import (
    SkillRouter,
    RouteResult,
    RouteToSkillAction,
    RegisterSkillAction,
)

# V4.0: Context Injection System
from lib.oda.pai.skills.context_injector import (
    ContextInjector,
    InjectedContext,
    InjectContextAction,
    inject_context,
    get_default_injector,
    get_reference_map,
    REFERENCE_MAP,
    AUTO_DETECT_KEYWORDS,
)


__all__ = [
    # Skill Definition
    "SkillDefinition",
    "SkillTrigger",
    "SkillExecution",
    "SkillStatus",
    "TriggerPriority",
    "ExecutionStatus",

    # V4.0: Intent Classification (replaces TriggerDetector)
    "IntentClassifier",
    "IntentClassifierConfig",
    "IntentResult",
    "CommandDescription",
    "IntentMatchType",
    "IntentAdapter",
    "create_intent_classifier",
    "get_default_commands",
    # Backward compatibility
    "LegacyTriggerMatch",
    "convert_to_trigger_match",
    # V4.0: Low-Confidence Clarification
    "ClarificationRequest",
    "ClarificationFlow",

    # Workflow
    "Workflow",
    "WorkflowStep",
    "WorkflowExecution",
    "StepStatus",
    "ExecuteWorkflowAction",

    # Router
    "SkillRouter",
    "RouteResult",
    "RouteToSkillAction",
    "RegisterSkillAction",

    # V4.0: Context Injection
    "ContextInjector",
    "InjectedContext",
    "InjectContextAction",
    "inject_context",
    "get_default_injector",
    "get_reference_map",
    "REFERENCE_MAP",
    "AUTO_DETECT_KEYWORDS",
]


__version__ = "4.0.0"
