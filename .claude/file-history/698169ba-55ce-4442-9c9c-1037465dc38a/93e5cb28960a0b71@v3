"""
ODA Structured Output Schemas
=============================

Pydantic models for enforcing structured JSON output from subagents.
Used by PromptTemplateBuilder to inject schema into prompts.

V2.1.10 Feature: L2 Synthesizer + Structured Prompts

This module provides:
1. Pydantic models defining output structure for each subagent type
2. Schema registry for type-safe lookup
3. JSON Schema generation for prompt injection
4. Validation utilities for subagent responses

Usage:
    from lib.oda.planning.output_schemas import (
        get_schema,
        get_json_schema,
        ExploreOutput,
        PlanOutput,
        validate_output,
    )

    # Get Pydantic model
    schema = get_schema("explore")

    # Get JSON Schema for prompt injection
    json_schema = get_json_schema("explore")

    # Validate subagent output
    result = validate_output("explore", raw_output_dict)
"""

from enum import Enum
from typing import Any, Dict, List, Optional, TypeVar, Union

from pydantic import BaseModel, Field, ValidationError


class Severity(str, Enum):
    """Finding severity levels for analysis results."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class Finding(BaseModel):
    """A single finding from analysis.

    Represents an issue, pattern, or observation discovered during
    codebase analysis by Explore or other subagents.
    """

    file: str = Field(..., description="File path where finding occurred")
    line: Optional[int] = Field(
        default=None, ge=1, description="Line number (optional for file-level findings)"
    )
    severity: Severity = Field(..., description="Finding severity level")
    description: str = Field(
        ..., max_length=200, description="Brief description of the finding"
    )
    category: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Finding category (e.g., 'security', 'performance', 'style')",
    )


class DependencyInfo(BaseModel):
    """Information about a code dependency."""

    name: str = Field(..., description="Dependency name or import path")
    type: str = Field(
        default="import",
        description="Dependency type: 'import', 'file', 'external', 'internal'",
    )
    location: Optional[str] = Field(
        default=None, description="Where this dependency is used"
    )


class ExploreOutput(BaseModel):
    """Structured output schema for Explore subagent.

    Used when Explore subagent analyzes codebase structure,
    discovers patterns, and identifies files for further analysis.

    Token Budget: ~5K tokens
    Max Files: 50
    Max Findings: 20
    """

    summary: str = Field(
        ..., max_length=200, description="One-sentence summary of analysis results"
    )
    files_analyzed: List[str] = Field(
        ...,
        max_length=50,
        description="List of analyzed file paths (absolute or relative)",
    )
    patterns_found: List[str] = Field(
        default_factory=list,
        max_length=20,
        description="Code patterns or architectural patterns discovered",
    )
    findings: List[Finding] = Field(
        ...,
        max_length=20,
        description="Analysis findings sorted by severity",
    )
    dependencies: List[Union[str, DependencyInfo]] = Field(
        default_factory=list,
        max_length=30,
        description="Identified dependencies (imports, file refs, externals)",
    )
    metrics: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metrics (file count, line count, complexity)",
    )
    next_action_hint: str = Field(
        ..., max_length=150, description="Suggested next action for orchestrator"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "summary": "Found 8 Python files with 3 security issues",
                "files_analyzed": ["lib/auth.py", "lib/api.py", "lib/utils.py"],
                "patterns_found": ["singleton", "factory"],
                "findings": [
                    {
                        "file": "lib/auth.py",
                        "line": 42,
                        "severity": "HIGH",
                        "description": "Hardcoded credentials detected",
                        "category": "security",
                    }
                ],
                "dependencies": ["requests", "pydantic"],
                "next_action_hint": "Review lib/auth.py for credential handling",
            }
        }


class PlanPhase(BaseModel):
    """A single phase in an implementation plan.

    Represents a logical grouping of tasks that should be
    completed together, with dependencies on other phases.
    """

    phase_number: int = Field(..., ge=1, le=20, description="Phase sequence number")
    name: str = Field(..., max_length=80, description="Phase name (e.g., 'Setup', 'Core Implementation')")
    description: Optional[str] = Field(
        default=None, max_length=200, description="Brief phase description"
    )
    tasks: List[str] = Field(
        ..., max_length=15, description="Tasks to complete in this phase"
    )
    dependencies: List[int] = Field(
        default_factory=list,
        description="Phase numbers this phase depends on",
    )
    estimated_effort: str = Field(
        ..., description="Effort estimate: 'trivial', 'small', 'medium', 'large', 'xlarge'"
    )
    files_affected: List[str] = Field(
        default_factory=list,
        max_length=10,
        description="Files that will be modified in this phase",
    )


class RiskItem(BaseModel):
    """A risk identified during planning."""

    description: str = Field(..., max_length=200, description="Risk description")
    severity: Severity = Field(default=Severity.MEDIUM, description="Risk severity")
    mitigation: Optional[str] = Field(
        default=None, max_length=200, description="Suggested mitigation"
    )


class PlanOutput(BaseModel):
    """Structured output schema for Plan subagent.

    Used when Plan subagent designs implementation strategy,
    breaks down work into phases, and identifies risks.

    Token Budget: ~10K tokens
    Max Phases: 10
    Max Risks: 5
    """

    summary: str = Field(
        ..., max_length=200, description="One-sentence plan summary"
    )
    objective: Optional[str] = Field(
        default=None, max_length=300, description="Clear statement of what this plan achieves"
    )
    total_phases: int = Field(..., ge=1, le=20, description="Total number of phases")
    phases: List[PlanPhase] = Field(
        ..., max_length=10, description="Implementation phases in order"
    )
    critical_files: List[str] = Field(
        default_factory=list,
        max_length=30,
        description="All files that will be created or modified",
    )
    risks: List[Union[str, RiskItem]] = Field(
        default_factory=list,
        max_length=10,
        description="Identified risks and concerns",
    )
    prerequisites: List[str] = Field(
        default_factory=list,
        max_length=10,
        description="Prerequisites that must be met before starting",
    )
    success_criteria: List[str] = Field(
        default_factory=list,
        max_length=5,
        description="How to verify the plan succeeded",
    )
    next_action_hint: str = Field(
        ..., max_length=150, description="Suggested next action for orchestrator"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "summary": "3-phase implementation plan for authentication module",
                "objective": "Add JWT-based authentication to the API",
                "total_phases": 3,
                "phases": [
                    {
                        "phase_number": 1,
                        "name": "Setup",
                        "tasks": ["Install dependencies", "Create config"],
                        "dependencies": [],
                        "estimated_effort": "small",
                        "files_affected": ["requirements.txt", "config.py"],
                    }
                ],
                "critical_files": ["lib/auth.py", "lib/api.py"],
                "risks": ["Breaking change to existing API"],
                "next_action_hint": "Start with Phase 1: Setup dependencies",
            }
        }


class AgentSummary(BaseModel):
    """Summary of a single agent's L2 output for synthesis."""

    agent_id: str = Field(..., description="Agent identifier")
    agent_type: str = Field(..., description="Subagent type (Explore, Plan, etc.)")
    status: str = Field(..., description="completed, failed, partial")
    key_findings: List[str] = Field(
        default_factory=list,
        max_length=10,
        description="Most important findings from this agent",
    )
    files_referenced: List[str] = Field(
        default_factory=list,
        max_length=20,
        description="Files this agent analyzed or referenced",
    )
    l2_path: Optional[str] = Field(
        default=None, description="Path to full L2 report"
    )


class SynthesisOutput(BaseModel):
    """Structured output schema for L2 Synthesizer.

    Used when Main Agent synthesizes results from multiple
    subagent L2 reports into a cohesive summary.

    Token Budget: Variable (depends on number of agents)
    """

    summary: str = Field(
        ..., max_length=300, description="Executive summary of all synthesized results"
    )
    total_agents: int = Field(..., ge=1, description="Number of L2 files synthesized")
    agent_summaries: List[AgentSummary] = Field(
        default_factory=list,
        max_length=20,
        description="Summary of each agent's contribution",
    )
    critical_findings: List[str] = Field(
        ...,
        max_length=15,
        description="Most critical findings across all L2s (deduplicated)",
    )
    cross_module_concerns: List[str] = Field(
        default_factory=list,
        max_length=10,
        description="Issues spanning multiple modules or requiring coordination",
    )
    consolidated_files: List[str] = Field(
        default_factory=list,
        max_length=50,
        description="All unique files referenced across agents",
    )
    recommended_next_action: str = Field(
        ..., max_length=150, description="Primary recommended next action"
    )
    additional_recommendations: List[str] = Field(
        default_factory=list,
        max_length=5,
        description="Secondary recommendations",
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "summary": "Synthesized 3 agent reports: found 5 critical issues",
                "total_agents": 3,
                "critical_findings": [
                    "SQL injection vulnerability in user input handler",
                    "Missing authentication on admin endpoints",
                ],
                "cross_module_concerns": [
                    "Auth module tightly coupled with database layer"
                ],
                "recommended_next_action": "Address SQL injection in lib/db.py first",
            }
        }


class ExecutionOutput(BaseModel):
    """Structured output schema for general-purpose execution subagent.

    Used when a subagent executes implementation tasks and
    reports on files modified and verification results.

    Token Budget: ~15K tokens
    """

    summary: str = Field(
        ..., max_length=200, description="One-sentence summary of execution results"
    )
    status: str = Field(
        ..., description="Execution status: 'success', 'partial', 'failed'"
    )
    files_created: List[str] = Field(
        default_factory=list,
        max_length=20,
        description="New files created",
    )
    files_modified: List[str] = Field(
        default_factory=list,
        max_length=30,
        description="Existing files modified",
    )
    files_deleted: List[str] = Field(
        default_factory=list,
        max_length=10,
        description="Files deleted",
    )
    verification_results: Dict[str, str] = Field(
        default_factory=dict,
        description="Results of verification steps (e.g., {'tests': 'passed', 'lint': 'passed'})",
    )
    errors: List[str] = Field(
        default_factory=list,
        max_length=10,
        description="Errors encountered during execution",
    )
    warnings: List[str] = Field(
        default_factory=list,
        max_length=10,
        description="Warnings (non-blocking issues)",
    )
    next_action_hint: str = Field(
        ..., max_length=150, description="Suggested next action"
    )


# Type variable for generic schema operations
T = TypeVar("T", bound=BaseModel)

# Schema registry for lookup by subagent type
SCHEMA_REGISTRY: Dict[str, type[BaseModel]] = {
    "explore": ExploreOutput,
    "plan": PlanOutput,
    "synthesis": SynthesisOutput,
    "execution": ExecutionOutput,
    "general_purpose": ExecutionOutput,  # Alias
    "general-purpose": ExecutionOutput,  # Alias with hyphen
}


def get_schema(subagent_type: str) -> type[BaseModel]:
    """Get Pydantic schema class for a subagent type.

    Args:
        subagent_type: Type of subagent (e.g., 'explore', 'plan', 'Explore')

    Returns:
        Pydantic BaseModel subclass for the specified type

    Raises:
        ValueError: If subagent_type is not registered

    Example:
        >>> schema = get_schema("explore")
        >>> schema.__name__
        'ExploreOutput'
    """
    normalized = subagent_type.lower().replace("-", "_").replace(" ", "_")
    if normalized not in SCHEMA_REGISTRY:
        available = ", ".join(sorted(set(SCHEMA_REGISTRY.keys())))
        raise ValueError(
            f"Unknown subagent type: '{subagent_type}'. "
            f"Available types: {available}"
        )
    return SCHEMA_REGISTRY[normalized]


def get_json_schema(subagent_type: str) -> Dict[str, Any]:
    """Get JSON Schema for a subagent type.

    Generates a JSON Schema suitable for embedding in prompts
    to guide subagent output format.

    Args:
        subagent_type: Type of subagent (e.g., 'explore', 'plan')

    Returns:
        JSON Schema dictionary

    Example:
        >>> schema = get_json_schema("explore")
        >>> schema["title"]
        'ExploreOutput'
    """
    schema_class = get_schema(subagent_type)
    return schema_class.model_json_schema()


def get_schema_prompt_block(subagent_type: str) -> str:
    """Generate a prompt block containing the JSON Schema.

    Creates a formatted string suitable for injection into
    subagent prompts.

    Args:
        subagent_type: Type of subagent

    Returns:
        Formatted prompt block with JSON Schema

    Example:
        >>> block = get_schema_prompt_block("explore")
        >>> "ExploreOutput" in block
        True
    """
    import json

    schema = get_json_schema(subagent_type)
    schema_str = json.dumps(schema, indent=2)

    return f"""## Output Format (REQUIRED)

You MUST respond with valid JSON matching this schema:

```json
{schema_str}
```

IMPORTANT:
- Output ONLY the JSON object, no additional text
- All required fields must be present
- Respect maxLength constraints for strings
- Respect maxItems constraints for arrays
"""


def validate_output(
    subagent_type: str, data: Dict[str, Any]
) -> tuple[Optional[BaseModel], Optional[str]]:
    """Validate subagent output against its schema.

    Args:
        subagent_type: Type of subagent
        data: Raw output dictionary to validate

    Returns:
        Tuple of (validated_model, error_message)
        - If valid: (model_instance, None)
        - If invalid: (None, error_description)

    Example:
        >>> data = {"summary": "Test", "files_analyzed": [], ...}
        >>> result, error = validate_output("explore", data)
        >>> error is None
        True
    """
    try:
        schema_class = get_schema(subagent_type)
        validated = schema_class.model_validate(data)
        return validated, None
    except ValidationError as e:
        return None, str(e)
    except ValueError as e:
        return None, str(e)


def extract_structured_output(
    raw_text: str, subagent_type: str
) -> tuple[Optional[BaseModel], Optional[str]]:
    """Extract and validate JSON from raw subagent output text.

    Attempts to find and parse JSON from potentially mixed text output,
    then validates against the schema.

    Args:
        raw_text: Raw text output from subagent (may contain non-JSON text)
        subagent_type: Type of subagent for schema validation

    Returns:
        Tuple of (validated_model, error_message)

    Example:
        >>> text = 'Here is my analysis:\\n```json\\n{"summary": "..."}\\n```'
        >>> result, error = extract_structured_output(text, "explore")
    """
    import json
    import re

    # Try to extract JSON from code blocks first
    json_block_pattern = r"```(?:json)?\s*\n?([\s\S]*?)\n?```"
    matches = re.findall(json_block_pattern, raw_text)

    for match in matches:
        try:
            data = json.loads(match.strip())
            return validate_output(subagent_type, data)
        except json.JSONDecodeError:
            continue

    # Try parsing the entire text as JSON
    try:
        data = json.loads(raw_text.strip())
        return validate_output(subagent_type, data)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object pattern
    json_obj_pattern = r"\{[\s\S]*\}"
    obj_matches = re.findall(json_obj_pattern, raw_text)

    for match in obj_matches:
        try:
            data = json.loads(match)
            return validate_output(subagent_type, data)
        except json.JSONDecodeError:
            continue

    return None, "Could not extract valid JSON from output"


# Export all public symbols
__all__ = [
    # Enums
    "Severity",
    # Models
    "Finding",
    "DependencyInfo",
    "ExploreOutput",
    "PlanPhase",
    "RiskItem",
    "PlanOutput",
    "AgentSummary",
    "SynthesisOutput",
    "ExecutionOutput",
    # Registry
    "SCHEMA_REGISTRY",
    # Functions
    "get_schema",
    "get_json_schema",
    "get_schema_prompt_block",
    "validate_output",
    "extract_structured_output",
]
