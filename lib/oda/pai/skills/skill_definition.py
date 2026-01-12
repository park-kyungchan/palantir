"""
Orion ODA v3.0 - Skill Definition ObjectTypes
PAI Prompting Skill Migration - Phase 4

This module defines the core ObjectTypes for skill management:
- SkillDefinition: Represents a registered skill with triggers and tools
- SkillTrigger: Defines how a skill is activated (keywords, patterns, context)
- SkillExecution: Records skill execution history for audit

Aligned with Palantir AIP/Foundry ontology patterns.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from lib.oda.ontology.ontology_types import OntologyObject, utc_now
from lib.oda.ontology.registry import register_object_type


# =============================================================================
# ENUMS
# =============================================================================

class SkillStatus(str, Enum):
    """Skill lifecycle status."""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    DISABLED = "disabled"


class TriggerPriority(str, Enum):
    """
    Priority for trigger matching.
    Higher priority triggers are evaluated first.
    """
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class ExecutionStatus(str, Enum):
    """Skill execution outcome status."""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


# =============================================================================
# SKILL TRIGGER OBJECTTYPE
# =============================================================================

@register_object_type
class SkillTrigger(OntologyObject):
    """
    Defines activation criteria for a skill.

    A SkillTrigger specifies how user input is matched to a skill:
    - keywords: Exact word matches (case-insensitive)
    - patterns: Regex patterns for flexible matching
    - context_match: Optional context similarity requirements

    The trigger detection algorithm uses priority order:
    1. Exact keyword match
    2. Pattern regex match
    3. Context similarity (if context_match defined)

    Attributes:
        name: Human-readable trigger name
        keywords: List of exact keywords to match
        patterns: List of regex patterns to match
        context_match: Optional context keywords for semantic matching
        priority: Trigger evaluation priority
        enabled: Whether this trigger is active
        skill_definition_id: FK to parent SkillDefinition

    Example:
        ```python
        trigger = SkillTrigger(
            name="commit_trigger",
            keywords=["commit", "git commit", "/commit"],
            patterns=[r"^/commit\\s*$", r"make a commit"],
            priority=TriggerPriority.HIGH
        )
        ```
    """

    # Trigger identification
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Human-readable trigger name"
    )

    # Matching criteria
    keywords: List[str] = Field(
        default_factory=list,
        description="Exact keywords to match (case-insensitive)"
    )
    patterns: List[str] = Field(
        default_factory=list,
        description="Regex patterns for flexible matching"
    )
    context_match: Optional[List[str]] = Field(
        default=None,
        description="Context keywords for semantic similarity matching"
    )

    # Configuration
    priority: TriggerPriority = Field(
        default=TriggerPriority.NORMAL,
        description="Trigger evaluation priority"
    )
    enabled: bool = Field(
        default=True,
        description="Whether this trigger is active"
    )
    case_sensitive: bool = Field(
        default=False,
        description="Whether keyword matching is case-sensitive"
    )

    # Relationship
    skill_definition_id: Optional[str] = Field(
        default=None,
        description="FK to parent SkillDefinition"
    )

    # Metadata
    description: str = Field(
        default="",
        max_length=500,
        description="Human-readable description of what this trigger matches"
    )

    @field_validator("patterns")
    @classmethod
    def validate_patterns(cls, v: List[str]) -> List[str]:
        """Validate that patterns are valid regex."""
        import re
        for pattern in v:
            try:
                re.compile(pattern)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern '{pattern}': {e}")
        return v

    @property
    def has_keywords(self) -> bool:
        """Check if trigger has keyword matchers."""
        return len(self.keywords) > 0

    @property
    def has_patterns(self) -> bool:
        """Check if trigger has pattern matchers."""
        return len(self.patterns) > 0

    @property
    def has_context_match(self) -> bool:
        """Check if trigger has context matching."""
        return self.context_match is not None and len(self.context_match) > 0

    def __repr__(self) -> str:
        return (
            f"SkillTrigger(name='{self.name}', "
            f"keywords={len(self.keywords)}, "
            f"patterns={len(self.patterns)}, "
            f"priority={self.priority.value})"
        )


# =============================================================================
# SKILL DEFINITION OBJECTTYPE
# =============================================================================

@register_object_type
class SkillDefinition(OntologyObject):
    """
    Represents a registered skill in the ODA system.

    A SkillDefinition encapsulates:
    - Identity: name, description, version
    - Activation: triggers that activate this skill
    - Execution: tools required, model preferences
    - Configuration: parameters, constraints

    Skills are the primary unit of capability in the PAI/ODA system.
    They can be triggered by user input and execute workflows.

    Attributes:
        name: Unique skill identifier (snake_case)
        display_name: Human-readable skill name
        description: Detailed description of skill purpose
        version: Semantic version string
        triggers: List of SkillTrigger IDs
        tools: List of tool names this skill uses
        model: Preferred model for execution
        skill_status: Lifecycle status
        parameters: Default parameters for execution
        constraints: Execution constraints
        author: Skill author identifier
        tags: Categorization tags

    Example:
        ```python
        skill = SkillDefinition(
            name="code_review",
            display_name="Code Review Skill",
            description="Analyzes code for quality and suggests improvements",
            tools=["Read", "Grep", "Edit"],
            model="claude-opus-4-5-20251101"
        )
        ```
    """

    # Identity
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique skill identifier (snake_case)"
    )
    display_name: str = Field(
        default="",
        max_length=200,
        description="Human-readable skill name"
    )
    description: str = Field(
        default="",
        max_length=2000,
        description="Detailed description of skill purpose"
    )
    version: str = Field(
        default="1.0.0",
        max_length=20,
        description="Semantic version string"
    )

    # Activation
    trigger_ids: List[str] = Field(
        default_factory=list,
        description="List of SkillTrigger IDs that activate this skill"
    )

    # Execution Configuration
    tools: List[str] = Field(
        default_factory=list,
        description="List of tool names this skill uses"
    )
    model: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Preferred model for execution (e.g., 'claude-opus-4-5-20251101')"
    )

    # Lifecycle
    skill_status: SkillStatus = Field(
        default=SkillStatus.DRAFT,
        description="Skill lifecycle status"
    )

    # Configuration
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Default parameters for execution"
    )
    constraints: Dict[str, Any] = Field(
        default_factory=dict,
        description="Execution constraints (timeout, max_tokens, etc.)"
    )

    # Metadata
    author: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Skill author identifier"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Categorization tags"
    )
    documentation_url: Optional[str] = Field(
        default=None,
        max_length=500,
        description="URL to skill documentation"
    )

    # Runtime state
    execution_count: int = Field(
        default=0,
        ge=0,
        description="Total number of executions"
    )
    last_executed_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp of last execution"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name follows snake_case convention."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                f"name must be alphanumeric with underscores/hyphens: {v}"
            )
        return v.lower()

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate semantic version format."""
        import re
        if not re.match(r"^\d+\.\d+\.\d+(-[\w.]+)?$", v):
            raise ValueError(
                f"version must be semantic version format (e.g., '1.0.0'): {v}"
            )
        return v

    @property
    def is_enabled(self) -> bool:
        """Check if skill is enabled for execution."""
        return self.skill_status == SkillStatus.ACTIVE

    @property
    def has_triggers(self) -> bool:
        """Check if skill has any triggers defined."""
        return len(self.trigger_ids) > 0

    def record_execution(self) -> None:
        """Record a skill execution."""
        self.execution_count += 1
        self.last_executed_at = utc_now()
        self.touch()

    def activate(self) -> "SkillDefinition":
        """Activate the skill for use."""
        self.skill_status = SkillStatus.ACTIVE
        self.touch()
        return self

    def deprecate(self) -> "SkillDefinition":
        """Mark skill as deprecated."""
        self.skill_status = SkillStatus.DEPRECATED
        self.touch()
        return self

    def disable(self) -> "SkillDefinition":
        """Disable the skill."""
        self.skill_status = SkillStatus.DISABLED
        self.touch()
        return self

    def __repr__(self) -> str:
        return (
            f"SkillDefinition(name='{self.name}', "
            f"version='{self.version}', "
            f"status={self.skill_status.value}, "
            f"tools={len(self.tools)})"
        )


# =============================================================================
# SKILL EXECUTION OBJECTTYPE
# =============================================================================

@register_object_type
class SkillExecution(OntologyObject):
    """
    Records a skill execution instance for audit and analysis.

    Every skill invocation creates a SkillExecution record that tracks:
    - Input: What triggered the execution
    - Output: What was produced
    - Performance: Duration, token usage
    - Status: Success or failure details

    Attributes:
        skill_name: Name of the executed skill
        skill_definition_id: FK to SkillDefinition
        input_text: User input that triggered execution
        input_context: Additional context provided
        output_text: Generated output
        output_data: Structured output data
        execution_status: Outcome status
        duration_ms: Execution time in milliseconds
        token_usage: Token consumption details
        error_message: Error details if failed
        triggered_by: What triggered the execution
        agent_id: ID of the executing agent

    Example:
        ```python
        execution = SkillExecution(
            skill_name="code_review",
            input_text="Review this PR",
            output_text="Found 3 issues...",
            execution_status=ExecutionStatus.SUCCESS,
            duration_ms=1523
        )
        ```
    """

    # Skill reference
    skill_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the executed skill"
    )
    skill_definition_id: Optional[str] = Field(
        default=None,
        description="FK to SkillDefinition"
    )

    # Input
    input_text: str = Field(
        default="",
        max_length=10000,
        description="User input that triggered execution"
    )
    input_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context provided"
    )

    # Output
    output_text: str = Field(
        default="",
        max_length=50000,
        description="Generated output"
    )
    output_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured output data"
    )

    # Execution status
    execution_status: ExecutionStatus = Field(
        default=ExecutionStatus.SUCCESS,
        description="Outcome status"
    )

    # Performance metrics
    duration_ms: int = Field(
        default=0,
        ge=0,
        description="Execution time in milliseconds"
    )
    token_usage: Dict[str, int] = Field(
        default_factory=lambda: {"input": 0, "output": 0, "total": 0},
        description="Token consumption details"
    )

    # Error handling
    error_message: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Error details if failed"
    )
    error_traceback: Optional[str] = Field(
        default=None,
        max_length=10000,
        description="Full traceback if available"
    )

    # Trigger information
    triggered_by: str = Field(
        default="keyword",
        max_length=50,
        description="What triggered the execution (keyword, pattern, context, direct)"
    )
    trigger_match: Optional[str] = Field(
        default=None,
        max_length=200,
        description="The specific match that triggered execution"
    )

    # Agent reference
    agent_id: Optional[str] = Field(
        default=None,
        description="ID of the executing agent"
    )

    # Timestamps
    started_at: datetime = Field(
        default_factory=utc_now,
        description="Execution start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Execution completion timestamp"
    )

    @property
    def is_success(self) -> bool:
        """Check if execution was successful."""
        return self.execution_status == ExecutionStatus.SUCCESS

    @property
    def is_failure(self) -> bool:
        """Check if execution failed."""
        return self.execution_status == ExecutionStatus.FAILURE

    def complete(
        self,
        output_text: str = "",
        output_data: Optional[Dict[str, Any]] = None,
        execution_status: ExecutionStatus = ExecutionStatus.SUCCESS,
        error_message: Optional[str] = None
    ) -> "SkillExecution":
        """
        Mark execution as complete.

        Args:
            output_text: Generated output text
            output_data: Structured output data
            execution_status: Outcome status
            error_message: Error details if failed

        Returns:
            self for method chaining
        """
        self.completed_at = utc_now()
        self.output_text = output_text
        if output_data:
            self.output_data = output_data
        self.execution_status = execution_status
        if error_message:
            self.error_message = error_message

        # Calculate duration
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)

        self.touch()
        return self

    def to_audit_log(self) -> Dict[str, Any]:
        """Generate an audit log entry."""
        return {
            "execution_id": self.id,
            "skill_name": self.skill_name,
            "status": self.execution_status.value,
            "duration_ms": self.duration_ms,
            "triggered_by": self.triggered_by,
            "trigger_match": self.trigger_match,
            "agent_id": self.agent_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
        }

    def __repr__(self) -> str:
        return (
            f"SkillExecution(skill='{self.skill_name}', "
            f"status={self.execution_status.value}, "
            f"duration={self.duration_ms}ms)"
        )
