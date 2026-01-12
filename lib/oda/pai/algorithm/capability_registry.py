"""
ODA PAI Algorithm - Capability Registry
========================================

Defines the capability model for THE ALGORITHM.

Capabilities are the building blocks of task execution. Each capability
has a minimum effort level required to unlock it, a category, and
optional constraints like model requirements and concurrent limits.

ObjectTypes:
    - Capability: A single orchestratable capability
    - CapabilityConfig: Runtime configuration for a capability

Enums:
    - CapabilityCategory: Categories of capabilities

Migrated from: PAI/Packs/pai-algorithm-skill/src/skills/THEALGORITHM/Data/Capabilities.yaml
"""

from __future__ import annotations

from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional, Type

from pydantic import Field, field_validator

from lib.oda.ontology.ontology_types import OntologyObject
from lib.oda.ontology.registry import register_object_type

from .effort_levels import EffortLevel


# =============================================================================
# ENUMS
# =============================================================================


class CapabilityCategory(str, Enum):
    """
    Categories of capabilities in THE ALGORITHM.

    Each category represents a different aspect of task execution:
    - MODELS: LLM compute resources (haiku, sonnet, opus)
    - THINKING: Cognitive enhancement modes (ultrathink, tree_of_thought)
    - DEBATE: Multi-agent deliberation systems (council, redteam)
    - ANALYSIS: Problem decomposition modes (first_principles, science)
    - RESEARCH: Information gathering agents (perplexity, gemini, etc.)
    - EXECUTION: Task execution agents (intern, architect, engineer)
    - VERIFICATION: Quality assurance mechanisms (browser, skeptical_verifier)
    - COMPOSITION: Agent factory and composition tools
    - PARALLEL: Parallel execution infrastructure
    """

    MODELS = "models"
    THINKING = "thinking"
    DEBATE = "debate"
    ANALYSIS = "analysis"
    RESEARCH = "research"
    EXECUTION = "execution"
    VERIFICATION = "verification"
    COMPOSITION = "composition"
    PARALLEL = "parallel"

    @property
    def description(self) -> str:
        """Human-readable description of this category."""
        descriptions = {
            CapabilityCategory.MODELS: "LLM compute resources",
            CapabilityCategory.THINKING: "Cognitive enhancement modes",
            CapabilityCategory.DEBATE: "Multi-agent deliberation systems",
            CapabilityCategory.ANALYSIS: "Problem decomposition modes",
            CapabilityCategory.RESEARCH: "Information gathering agents",
            CapabilityCategory.EXECUTION: "Task execution agents",
            CapabilityCategory.VERIFICATION: "Quality assurance mechanisms",
            CapabilityCategory.COMPOSITION: "Agent factory and composition tools",
            CapabilityCategory.PARALLEL: "Parallel execution infrastructure",
        }
        return descriptions.get(self, "Unknown category")


class ModelType(str, Enum):
    """Supported LLM model types."""

    HAIKU = "haiku"
    SONNET = "sonnet"
    OPUS = "opus"

    @property
    def min_effort(self) -> EffortLevel:
        """Minimum effort level to use this model."""
        levels = {
            ModelType.HAIKU: EffortLevel.QUICK,
            ModelType.SONNET: EffortLevel.STANDARD,
            ModelType.OPUS: EffortLevel.DETERMINED,
        }
        return levels[self]


# =============================================================================
# OBJECT TYPES
# =============================================================================


@register_object_type
class Capability(OntologyObject):
    """
    A single orchestratable capability in THE ALGORITHM.

    Capabilities define what actions/tools/agents can be invoked
    at different effort levels. Each capability has:
    - A unique name and category
    - Minimum effort level to unlock
    - Optional model and agent requirements
    - Usage guidance (when to use)

    Attributes:
        name: Unique identifier for this capability (e.g., "council")
        category: Category this capability belongs to
        description: Human-readable description
        min_effort: Minimum effort level required (maps from effort_min)
        use_when: Guidance on when to use this capability
        model: Required model type (if any)
        subagent_type: Subagent type to spawn (if any)
        skill: Skill identifier (if any)
        workflow: Workflow name (if any)
        tool: Tool name (if any)
        agents_count: Number of agents (for debate systems)
        rounds_count: Number of rounds (for debate systems)
        max_iterations: Max iterations (for iterative loops)
        keywords: Trigger keywords for this capability
        traits: Required agent traits (if any)
        config: Additional configuration dict
        is_enabled: Whether this capability is currently enabled
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique identifier for this capability"
    )
    category: CapabilityCategory = Field(
        ...,
        description="Category this capability belongs to"
    )
    description: str = Field(
        default="",
        max_length=500,
        description="Human-readable description"
    )
    min_effort: EffortLevel = Field(
        default=EffortLevel.STANDARD,
        description="Minimum effort level required"
    )
    use_when: str = Field(
        default="",
        max_length=1000,
        description="Guidance on when to use this capability"
    )
    model: Optional[ModelType] = Field(
        default=None,
        description="Required model type (if any)"
    )
    subagent_type: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Subagent type to spawn (if any)"
    )
    skill: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Skill identifier (if any)"
    )
    workflow: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Workflow name (if any)"
    )
    tool: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Tool name (if any)"
    )
    agents_count: Optional[int] = Field(
        default=None,
        ge=1,
        le=100,
        description="Number of agents (for debate systems)"
    )
    rounds_count: Optional[int] = Field(
        default=None,
        ge=1,
        le=10,
        description="Number of rounds (for debate systems)"
    )
    max_iterations: Optional[int] = Field(
        default=None,
        ge=1,
        description="Max iterations (for iterative loops)"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Trigger keywords for this capability"
    )
    traits: List[str] = Field(
        default_factory=list,
        description="Required agent traits (if any)"
    )
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional configuration dict"
    )
    is_enabled: bool = Field(
        default=True,
        description="Whether this capability is currently enabled"
    )

    @field_validator("name")
    @classmethod
    def validate_name_format(cls, v: str) -> str:
        """Validate name is lowercase with underscores."""
        if not v.replace("_", "").isalnum():
            raise ValueError(
                "Capability name must be alphanumeric with underscores"
            )
        return v.lower()

    def is_available_at(self, effort: EffortLevel) -> bool:
        """Check if this capability is available at the given effort level."""
        return self.is_enabled and effort.can_use(self.min_effort)

    def to_summary(self) -> Dict[str, Any]:
        """Generate a summary dict for display."""
        return {
            "name": self.name,
            "category": self.category.value,
            "min_effort": self.min_effort.value,
            "model": self.model.value if self.model else None,
            "enabled": self.is_enabled,
        }


# =============================================================================
# CAPABILITY REGISTRY (In-Memory)
# =============================================================================


class CapabilityRegistryService:
    """
    In-memory registry for capabilities.

    Provides lookup and filtering of capabilities by category,
    effort level, and other criteria.
    """

    def __init__(self):
        self._capabilities: Dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        """Register a capability."""
        self._capabilities[capability.name] = capability

    def get(self, name: str) -> Optional[Capability]:
        """Get a capability by name."""
        return self._capabilities.get(name)

    def list_all(self) -> List[Capability]:
        """List all registered capabilities."""
        return list(self._capabilities.values())

    def list_by_category(self, category: CapabilityCategory) -> List[Capability]:
        """List capabilities in a category."""
        return [c for c in self._capabilities.values() if c.category == category]

    def list_available_at(self, effort: EffortLevel) -> List[Capability]:
        """List capabilities available at an effort level."""
        return [
            c for c in self._capabilities.values()
            if c.is_available_at(effort)
        ]

    def list_by_model(self, model: ModelType) -> List[Capability]:
        """List capabilities requiring a specific model."""
        return [c for c in self._capabilities.values() if c.model == model]

    def find_by_keyword(self, keyword: str) -> List[Capability]:
        """Find capabilities matching a keyword."""
        keyword_lower = keyword.lower()
        return [
            c for c in self._capabilities.values()
            if keyword_lower in c.keywords or keyword_lower in c.name
        ]

    def get_effort_unlocks(self, effort: EffortLevel) -> Dict[str, List[str]]:
        """
        Get capabilities unlocked at exactly this effort level.

        Returns a dict mapping category to list of capability names.
        """
        unlocks: Dict[str, List[str]] = {}
        for cap in self._capabilities.values():
            if cap.min_effort == effort:
                cat = cap.category.value
                if cat not in unlocks:
                    unlocks[cat] = []
                unlocks[cat].append(cap.name)
        return unlocks


# Global registry instance
_capability_registry = CapabilityRegistryService()


def get_capability_registry() -> CapabilityRegistryService:
    """Get the global capability registry."""
    return _capability_registry


def register_capability(cap: Capability) -> Capability:
    """Register a capability with the global registry."""
    _capability_registry.register(cap)
    return cap


# =============================================================================
# BUILT-IN CAPABILITIES (from Capabilities.yaml)
# =============================================================================


def _register_default_capabilities() -> None:
    """Register default capabilities from PAI Capabilities.yaml."""

    # Models
    register_capability(Capability(
        name="haiku",
        category=CapabilityCategory.MODELS,
        description="Fast, cheap execution",
        min_effort=EffortLevel.QUICK,
        use_when="Parallel grunt work, simple execution, spotchecks",
        model=ModelType.HAIKU,
    ))
    register_capability(Capability(
        name="sonnet",
        category=CapabilityCategory.MODELS,
        description="Balanced reasoning",
        min_effort=EffortLevel.STANDARD,
        use_when="Analysis, planning, research, standard work",
        model=ModelType.SONNET,
    ))
    register_capability(Capability(
        name="opus",
        category=CapabilityCategory.MODELS,
        description="Maximum intelligence",
        min_effort=EffortLevel.DETERMINED,
        use_when="Architecture, critical decisions, complex reasoning",
        model=ModelType.OPUS,
    ))

    # Thinking
    register_capability(Capability(
        name="ultrathink",
        category=CapabilityCategory.THINKING,
        description="Creative solution mode",
        min_effort=EffortLevel.STANDARD,
        use_when="Need creative solutions, novel approaches, quality thinking",
        skill="BeCreative",
        workflow="StandardCreativity",
    ))
    register_capability(Capability(
        name="tree_of_thought",
        category=CapabilityCategory.THINKING,
        description="Branching exploration",
        min_effort=EffortLevel.THOROUGH,
        use_when="Complex multi-factor decisions, branching exploration",
        skill="BeCreative",
        workflow="TreeOfThoughts",
    ))
    register_capability(Capability(
        name="plan_mode",
        category=CapabilityCategory.THINKING,
        description="Structured planning with approval",
        min_effort=EffortLevel.THOROUGH,
        use_when="Complex multi-step implementation needing user approval",
        tool="EnterPlanMode",
    ))

    # Debate
    register_capability(Capability(
        name="council",
        category=CapabilityCategory.DEBATE,
        description="Multi-perspective deliberation",
        min_effort=EffortLevel.THOROUGH,
        use_when="Need multiple perspectives, collaborative analysis, design decisions",
        skill="Council",
        workflow="DEBATE",
        agents_count=4,
        rounds_count=3,
    ))
    register_capability(Capability(
        name="redteam",
        category=CapabilityCategory.DEBATE,
        description="Adversarial validation",
        min_effort=EffortLevel.DETERMINED,
        use_when="Adversarial validation, stress-testing, find weaknesses",
        skill="RedTeam",
        workflow="ParallelAnalysis",
        agents_count=32,
    ))

    # Analysis
    register_capability(Capability(
        name="first_principles",
        category=CapabilityCategory.ANALYSIS,
        description="Root truth discovery",
        min_effort=EffortLevel.STANDARD,
        use_when="Challenge assumptions, find root truths, deconstruct problems",
        skill="FirstPrinciples",
    ))
    register_capability(Capability(
        name="science",
        category=CapabilityCategory.ANALYSIS,
        description="Hypothesis-driven exploration",
        min_effort=EffortLevel.STANDARD,
        use_when="Hypothesis-driven exploration, systematic experimentation",
        skill="Science",
    ))

    # Research Agents
    for name, use_when in [
        ("perplexity", "Web research, current events, citations needed"),
        ("gemini", "Multi-perspective research, parallel query decomposition"),
        ("grok", "Contrarian analysis, unbiased fact-checking"),
        ("claude", "Academic research, scholarly sources"),
        ("codex", "Technical archaeology, code pattern research"),
    ]:
        register_capability(Capability(
            name=name,
            category=CapabilityCategory.RESEARCH,
            description=f"{name.capitalize()} researcher",
            min_effort=EffortLevel.STANDARD,
            use_when=use_when,
            subagent_type=f"{name.capitalize()}Researcher",
            model=ModelType.SONNET,
        ))

    # Execution Agents
    register_capability(Capability(
        name="intern",
        category=CapabilityCategory.EXECUTION,
        description="Fast parallel worker",
        min_effort=EffortLevel.QUICK,
        use_when="Parallel grunt work, simple tasks, data gathering",
        subagent_type="Intern",
        model=ModelType.HAIKU,
    ))
    register_capability(Capability(
        name="architect",
        category=CapabilityCategory.EXECUTION,
        description="System design specialist",
        min_effort=EffortLevel.THOROUGH,
        use_when="System design, architectural decisions",
        subagent_type="Architect",
        model=ModelType.OPUS,
    ))
    register_capability(Capability(
        name="engineer",
        category=CapabilityCategory.EXECUTION,
        description="Implementation specialist",
        min_effort=EffortLevel.STANDARD,
        use_when="Implementation, coding tasks",
        subagent_type="Engineer",
        model=ModelType.SONNET,
    ))
    register_capability(Capability(
        name="qa_tester",
        category=CapabilityCategory.EXECUTION,
        description="Quality assurance",
        min_effort=EffortLevel.STANDARD,
        use_when="Testing, validation, quality assurance",
        subagent_type="QATester",
        model=ModelType.SONNET,
    ))
    register_capability(Capability(
        name="designer",
        category=CapabilityCategory.EXECUTION,
        description="UX/UI specialist",
        min_effort=EffortLevel.STANDARD,
        use_when="UX/UI design, user-centered solutions",
        subagent_type="Designer",
        model=ModelType.SONNET,
    ))
    register_capability(Capability(
        name="pentester",
        category=CapabilityCategory.EXECUTION,
        description="Security testing",
        min_effort=EffortLevel.THOROUGH,
        use_when="Security testing, vulnerability assessment",
        subagent_type="Pentester",
        model=ModelType.SONNET,
    ))
    register_capability(Capability(
        name="ralph_loop",
        category=CapabilityCategory.EXECUTION,
        description="Persistent iteration loop",
        min_effort=EffortLevel.QUICK,
        use_when="Need persistent iteration until success criteria met",
        model=ModelType.SONNET,
        max_iterations=10,
        keywords=[
            "iterate until", "keep trying", "until tests pass",
            "until it works", "persistent", "retry until",
            "loop until", "ralph", "keep iterating", "don't stop until"
        ],
        config={"completion_detection": "promise_tags"},
    ))

    # Verification
    register_capability(Capability(
        name="browser",
        category=CapabilityCategory.VERIFICATION,
        description="Web application validation",
        min_effort=EffortLevel.STANDARD,
        use_when="Web application validation, visual verification",
        skill="Browser",
    ))
    register_capability(Capability(
        name="skeptical_verifier",
        category=CapabilityCategory.VERIFICATION,
        description="Independent validation",
        min_effort=EffortLevel.STANDARD,
        use_when="Validate work against ISC criteria",
        model=ModelType.SONNET,
        traits=["skeptical", "meticulous", "adversarial"],
        config={"rule": "Must be different agent than executor"},
    ))


# Register defaults on module load
_register_default_capabilities()
