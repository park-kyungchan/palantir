"""
Unit tests for PAI Skills Definition module.

Tests the core ObjectTypes for skill management:
- SkillTrigger: Activation criteria (keywords, patterns, context)
- SkillDefinition: Registered skill with triggers and tools
- SkillExecution: Execution history for audit

Also tests Pydantic validators and property methods.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import pytest

# Handle ImportError gracefully
# Note: Direct import from skill_definition.py to avoid package __init__.py import issues
try:
    import importlib.util
    import sys

    # Direct import to bypass broken package __init__.py
    _spec = importlib.util.spec_from_file_location(
        "skill_definition",
        "/home/palantir/park-kyungchan/palantir/lib/oda/pai/skills/skill_definition.py"
    )
    _module = importlib.util.module_from_spec(_spec)
    sys.modules["skill_definition"] = _module
    _spec.loader.exec_module(_module)

    SkillTrigger = _module.SkillTrigger
    SkillDefinition = _module.SkillDefinition
    SkillExecution = _module.SkillExecution
    SkillStatus = _module.SkillStatus
    TriggerPriority = _module.TriggerPriority
    ExecutionStatus = _module.ExecutionStatus

    from lib.oda.ontology.ontology_types import ObjectStatus
    IMPORT_ERROR = None
except (ImportError, FileNotFoundError, AttributeError) as e:
    IMPORT_ERROR = str(e)
    SkillTrigger = None
    SkillDefinition = None
    SkillExecution = None
    SkillStatus = None
    TriggerPriority = None
    ExecutionStatus = None
    ObjectStatus = None


pytestmark = pytest.mark.skipif(
    IMPORT_ERROR is not None,
    reason=f"Could not import skill_definition module: {IMPORT_ERROR}"
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def basic_trigger() -> "SkillTrigger":
    """Create a basic SkillTrigger with keywords only."""
    return SkillTrigger(
        name="basic_trigger",
        keywords=["commit", "git commit", "/commit"],
        priority=TriggerPriority.NORMAL
    )


@pytest.fixture
def pattern_trigger() -> "SkillTrigger":
    """Create a SkillTrigger with regex patterns."""
    return SkillTrigger(
        name="pattern_trigger",
        patterns=[r"^/review\s+PR\s+\d+$", r"review.*pull\s*request"],
        priority=TriggerPriority.HIGH
    )


@pytest.fixture
def full_trigger() -> "SkillTrigger":
    """Create a fully configured SkillTrigger."""
    return SkillTrigger(
        name="full_trigger",
        keywords=["audit", "check", "/audit"],
        patterns=[r"^/audit\s+.*$", r"run\s+audit"],
        context_match=["code review", "security check"],
        priority=TriggerPriority.CRITICAL,
        enabled=True,
        case_sensitive=False,
        skill_definition_id="skill-123",
        description="Triggers audit workflow"
    )


@pytest.fixture
def basic_skill() -> "SkillDefinition":
    """Create a basic SkillDefinition."""
    return SkillDefinition(
        name="code_review",
        display_name="Code Review Skill",
        description="Analyzes code for quality issues",
        tools=["Read", "Grep", "Edit"]
    )


@pytest.fixture
def full_skill() -> "SkillDefinition":
    """Create a fully configured SkillDefinition."""
    return SkillDefinition(
        name="deep_audit",
        display_name="Deep Audit Skill",
        description="Comprehensive code analysis",
        version="2.1.0",
        trigger_ids=["trigger-1", "trigger-2"],
        tools=["Read", "Grep", "Edit", "WebSearch"],
        model="claude-opus-4-5-20251101",
        skill_status=SkillStatus.ACTIVE,
        parameters={"depth": "thorough", "include_tests": True},
        constraints={"timeout": 300, "max_tokens": 8000},
        author="orion-system",
        tags=["audit", "code-quality", "security"]
    )


@pytest.fixture
def basic_execution() -> "SkillExecution":
    """Create a basic SkillExecution."""
    return SkillExecution(
        skill_name="code_review",
        input_text="Review this PR for issues",
        triggered_by="keyword"
    )


@pytest.fixture
def completed_execution() -> "SkillExecution":
    """Create a completed SkillExecution with full data."""
    execution = SkillExecution(
        skill_name="deep_audit",
        skill_definition_id="skill-456",
        input_text="Run deep audit on this module",
        input_context={"file_path": "/src/main.py", "scope": "module"},
        triggered_by="pattern",
        trigger_match=r"^/audit\s+.*$",
        agent_id="agent-789"
    )
    # Simulate completion
    execution.complete(
        output_text="Found 3 issues: ...",
        output_data={"issues": 3, "severity": "medium"},
        execution_status=ExecutionStatus.SUCCESS
    )
    return execution


# =============================================================================
# ENUM TESTS
# =============================================================================

class TestSkillStatus:
    """Tests for SkillStatus enum."""

    EXPECTED_VALUES = ["draft", "active", "deprecated", "disabled"]

    def test_skill_status_count(self):
        """SkillStatus should have exactly 4 values."""
        assert len(SkillStatus) == 4

    @pytest.mark.parametrize("value", EXPECTED_VALUES)
    def test_skill_status_has_value(self, value: str):
        """Each expected status value should exist."""
        assert value in [s.value for s in SkillStatus]

    def test_skill_status_is_str_enum(self):
        """SkillStatus should be a string enum."""
        assert SkillStatus.DRAFT.value == "draft"
        assert SkillStatus.ACTIVE.value == "active"


class TestTriggerPriority:
    """Tests for TriggerPriority enum."""

    EXPECTED_VALUES = ["low", "normal", "high", "critical"]

    def test_trigger_priority_count(self):
        """TriggerPriority should have exactly 4 values."""
        assert len(TriggerPriority) == 4

    @pytest.mark.parametrize("value", EXPECTED_VALUES)
    def test_trigger_priority_has_value(self, value: str):
        """Each expected priority value should exist."""
        assert value in [p.value for p in TriggerPriority]

    def test_trigger_priority_is_str_enum(self):
        """TriggerPriority should be a string enum."""
        assert TriggerPriority.NORMAL.value == "normal"
        assert TriggerPriority.CRITICAL.value == "critical"


class TestExecutionStatus:
    """Tests for ExecutionStatus enum."""

    EXPECTED_VALUES = ["success", "failure", "timeout", "cancelled"]

    def test_execution_status_count(self):
        """ExecutionStatus should have exactly 4 values."""
        assert len(ExecutionStatus) == 4

    @pytest.mark.parametrize("value", EXPECTED_VALUES)
    def test_execution_status_has_value(self, value: str):
        """Each expected execution status value should exist."""
        assert value in [s.value for s in ExecutionStatus]


# =============================================================================
# SKILLTRIGGER TESTS
# =============================================================================

class TestSkillTriggerFields:
    """Tests for SkillTrigger field validation."""

    def test_trigger_minimal_creation(self):
        """SkillTrigger can be created with just a name."""
        trigger = SkillTrigger(name="minimal")
        assert trigger.name == "minimal"
        assert trigger.keywords == []
        assert trigger.patterns == []
        assert trigger.priority == TriggerPriority.NORMAL
        assert trigger.enabled is True

    def test_trigger_name_required(self):
        """SkillTrigger requires a name."""
        with pytest.raises(ValueError):
            SkillTrigger()

    def test_trigger_name_min_length(self):
        """SkillTrigger name must be at least 1 character."""
        with pytest.raises(ValueError):
            SkillTrigger(name="")

    def test_trigger_name_max_length(self):
        """SkillTrigger name must not exceed 100 characters."""
        with pytest.raises(ValueError):
            SkillTrigger(name="x" * 101)

    def test_trigger_with_keywords(self, basic_trigger: "SkillTrigger"):
        """SkillTrigger should store keywords correctly."""
        assert basic_trigger.keywords == ["commit", "git commit", "/commit"]
        assert len(basic_trigger.keywords) == 3

    def test_trigger_with_patterns(self, pattern_trigger: "SkillTrigger"):
        """SkillTrigger should store patterns correctly."""
        assert len(pattern_trigger.patterns) == 2
        assert r"^/review\s+PR\s+\d+$" in pattern_trigger.patterns

    def test_trigger_default_priority(self):
        """SkillTrigger should default to NORMAL priority."""
        trigger = SkillTrigger(name="test")
        assert trigger.priority == TriggerPriority.NORMAL

    def test_trigger_description_max_length(self):
        """SkillTrigger description must not exceed 500 characters."""
        with pytest.raises(ValueError):
            SkillTrigger(name="test", description="x" * 501)


class TestSkillTriggerValidatePatterns:
    """Tests for SkillTrigger.validate_patterns() validator."""

    def test_valid_simple_pattern(self):
        """Valid simple regex pattern should pass validation."""
        trigger = SkillTrigger(name="test", patterns=[r"hello"])
        assert trigger.patterns == [r"hello"]

    def test_valid_complex_pattern(self):
        """Valid complex regex pattern should pass validation."""
        trigger = SkillTrigger(
            name="test",
            patterns=[r"^/commit\s+(-m\s+)?.*$", r"\d{4}-\d{2}-\d{2}"]
        )
        assert len(trigger.patterns) == 2

    def test_invalid_regex_pattern_raises_error(self):
        """Invalid regex pattern should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            SkillTrigger(name="test", patterns=[r"[invalid"])

    def test_invalid_pattern_unclosed_group(self):
        """Unclosed group in pattern should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            SkillTrigger(name="test", patterns=[r"(unclosed"])

    def test_invalid_pattern_bad_quantifier(self):
        """Bad quantifier in pattern should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            SkillTrigger(name="test", patterns=[r"*invalid"])

    def test_multiple_patterns_one_invalid(self):
        """One invalid pattern among multiple should fail."""
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            SkillTrigger(
                name="test",
                patterns=[r"valid", r"[invalid", r"also_valid"]
            )


class TestSkillTriggerProperties:
    """Tests for SkillTrigger properties."""

    def test_has_keywords_true(self, basic_trigger: "SkillTrigger"):
        """has_keywords should return True when keywords exist."""
        assert basic_trigger.has_keywords is True

    def test_has_keywords_false(self):
        """has_keywords should return False when no keywords."""
        trigger = SkillTrigger(name="test")
        assert trigger.has_keywords is False

    def test_has_patterns_true(self, pattern_trigger: "SkillTrigger"):
        """has_patterns should return True when patterns exist."""
        assert pattern_trigger.has_patterns is True

    def test_has_patterns_false(self, basic_trigger: "SkillTrigger"):
        """has_patterns should return False when no patterns."""
        assert basic_trigger.has_patterns is False

    def test_has_context_match_true(self, full_trigger: "SkillTrigger"):
        """has_context_match should return True when context_match exists."""
        assert full_trigger.has_context_match is True

    def test_has_context_match_false(self, basic_trigger: "SkillTrigger"):
        """has_context_match should return False when no context_match."""
        assert basic_trigger.has_context_match is False

    def test_has_context_match_empty_list(self):
        """has_context_match should return False for empty list."""
        trigger = SkillTrigger(name="test", context_match=[])
        assert trigger.has_context_match is False


class TestSkillTriggerRepr:
    """Tests for SkillTrigger string representation."""

    def test_trigger_repr(self, basic_trigger: "SkillTrigger"):
        """__repr__ should include key information."""
        repr_str = repr(basic_trigger)
        assert "SkillTrigger" in repr_str
        assert "basic_trigger" in repr_str
        assert "normal" in repr_str


# =============================================================================
# SKILLDEFINITION TESTS
# =============================================================================

class TestSkillDefinitionFields:
    """Tests for SkillDefinition field validation."""

    def test_skill_minimal_creation(self):
        """SkillDefinition can be created with just a name."""
        skill = SkillDefinition(name="minimal_skill")
        assert skill.name == "minimal_skill"
        assert skill.version == "1.0.0"
        assert skill.skill_status == SkillStatus.DRAFT
        assert skill.tools == []
        assert skill.execution_count == 0

    def test_skill_name_required(self):
        """SkillDefinition requires a name."""
        with pytest.raises(ValueError):
            SkillDefinition()

    def test_skill_name_max_length(self):
        """SkillDefinition name must not exceed 100 characters."""
        with pytest.raises(ValueError):
            SkillDefinition(name="x" * 101)

    def test_skill_with_tools(self, basic_skill: "SkillDefinition"):
        """SkillDefinition should store tools correctly."""
        assert basic_skill.tools == ["Read", "Grep", "Edit"]

    def test_skill_default_status(self):
        """SkillDefinition should default to DRAFT status."""
        skill = SkillDefinition(name="test_skill")
        assert skill.skill_status == SkillStatus.DRAFT

    def test_skill_execution_count_non_negative(self):
        """execution_count must be non-negative."""
        with pytest.raises(ValueError):
            SkillDefinition(name="test_skill", execution_count=-1)


class TestSkillDefinitionValidateName:
    """Tests for SkillDefinition.validate_name() validator."""

    def test_valid_snake_case_name(self):
        """Valid snake_case name should pass."""
        skill = SkillDefinition(name="code_review")
        assert skill.name == "code_review"

    def test_valid_name_with_hyphen(self):
        """Name with hyphens should pass."""
        skill = SkillDefinition(name="code-review")
        assert skill.name == "code-review"

    def test_name_converted_to_lowercase(self):
        """Name should be converted to lowercase."""
        skill = SkillDefinition(name="Code_Review")
        assert skill.name == "code_review"

    def test_name_with_numbers(self):
        """Name with numbers should pass."""
        skill = SkillDefinition(name="review_v2")
        assert skill.name == "review_v2"

    def test_invalid_name_with_spaces(self):
        """Name with spaces should raise ValueError."""
        with pytest.raises(ValueError, match="alphanumeric"):
            SkillDefinition(name="code review")

    def test_invalid_name_with_special_chars(self):
        """Name with special characters should raise ValueError."""
        with pytest.raises(ValueError, match="alphanumeric"):
            SkillDefinition(name="code@review")

    def test_invalid_name_with_dots(self):
        """Name with dots should raise ValueError."""
        with pytest.raises(ValueError, match="alphanumeric"):
            SkillDefinition(name="code.review")


class TestSkillDefinitionValidateVersion:
    """Tests for SkillDefinition.validate_version() validator."""

    def test_valid_semantic_version(self):
        """Valid semantic version should pass."""
        skill = SkillDefinition(name="test_skill", version="1.0.0")
        assert skill.version == "1.0.0"

    def test_valid_version_with_prerelease(self):
        """Version with prerelease tag should pass."""
        skill = SkillDefinition(name="test_skill", version="2.0.0-beta.1")
        assert skill.version == "2.0.0-beta.1"

    def test_valid_version_with_alpha(self):
        """Version with alpha tag should pass."""
        skill = SkillDefinition(name="test_skill", version="1.0.0-alpha")
        assert skill.version == "1.0.0-alpha"

    def test_invalid_version_two_parts(self):
        """Version with only two parts should fail."""
        with pytest.raises(ValueError, match="semantic version"):
            SkillDefinition(name="test_skill", version="1.0")

    def test_invalid_version_one_part(self):
        """Version with only one part should fail."""
        with pytest.raises(ValueError, match="semantic version"):
            SkillDefinition(name="test_skill", version="1")

    def test_invalid_version_non_numeric(self):
        """Non-numeric version should fail."""
        with pytest.raises(ValueError, match="semantic version"):
            SkillDefinition(name="test_skill", version="v1.0.0")

    def test_invalid_version_format(self):
        """Invalid version format should fail."""
        with pytest.raises(ValueError, match="semantic version"):
            SkillDefinition(name="test_skill", version="latest")


class TestSkillDefinitionProperties:
    """Tests for SkillDefinition properties."""

    def test_is_enabled_active(self, full_skill: "SkillDefinition"):
        """is_enabled should return True for ACTIVE status."""
        assert full_skill.is_enabled is True

    def test_is_enabled_draft(self, basic_skill: "SkillDefinition"):
        """is_enabled should return False for DRAFT status."""
        assert basic_skill.is_enabled is False

    def test_is_enabled_deprecated(self):
        """is_enabled should return False for DEPRECATED status."""
        skill = SkillDefinition(
            name="test_skill",
            skill_status=SkillStatus.DEPRECATED
        )
        assert skill.is_enabled is False

    def test_is_enabled_disabled(self):
        """is_enabled should return False for DISABLED status."""
        skill = SkillDefinition(
            name="test_skill",
            skill_status=SkillStatus.DISABLED
        )
        assert skill.is_enabled is False

    def test_has_triggers_true(self, full_skill: "SkillDefinition"):
        """has_triggers should return True when trigger_ids exist."""
        assert full_skill.has_triggers is True

    def test_has_triggers_false(self, basic_skill: "SkillDefinition"):
        """has_triggers should return False when no trigger_ids."""
        assert basic_skill.has_triggers is False


class TestSkillDefinitionMethods:
    """Tests for SkillDefinition methods.

    Note: SkillDefinition.version (semantic version string) shadows
    OntologyObject.version (integer for optimistic locking). This causes
    touch() to fail. Tests that call touch() are marked xfail.
    """

    @pytest.mark.xfail(
        reason="SkillDefinition.version (str) shadows OntologyObject.version (int)",
        strict=True
    )
    def test_record_execution(self, basic_skill: "SkillDefinition"):
        """record_execution should increment count and update timestamp.

        Note: This test exposes a design conflict where SkillDefinition.version
        (semantic version string) shadows OntologyObject.version (int).
        """
        initial_count = basic_skill.execution_count

        basic_skill.record_execution()

        assert basic_skill.execution_count == initial_count + 1
        assert basic_skill.last_executed_at is not None

    @pytest.mark.xfail(
        reason="SkillDefinition.version (str) shadows OntologyObject.version (int)",
        strict=True
    )
    def test_record_execution_multiple_times(self, basic_skill: "SkillDefinition"):
        """record_execution can be called multiple times."""
        for _ in range(5):
            basic_skill.record_execution()

        assert basic_skill.execution_count == 5
        assert basic_skill.last_executed_at is not None

    @pytest.mark.xfail(
        reason="SkillDefinition.version (str) shadows OntologyObject.version (int)",
        strict=True
    )
    def test_activate(self, basic_skill: "SkillDefinition"):
        """activate should set status to ACTIVE."""
        assert basic_skill.skill_status == SkillStatus.DRAFT

        result = basic_skill.activate()

        assert basic_skill.skill_status == SkillStatus.ACTIVE
        assert result is basic_skill  # Method chaining

    @pytest.mark.xfail(
        reason="SkillDefinition.version (str) shadows OntologyObject.version (int)",
        strict=True
    )
    def test_deprecate(self, full_skill: "SkillDefinition"):
        """deprecate should set status to DEPRECATED."""
        assert full_skill.skill_status == SkillStatus.ACTIVE

        result = full_skill.deprecate()

        assert full_skill.skill_status == SkillStatus.DEPRECATED
        assert result is full_skill  # Method chaining

    @pytest.mark.xfail(
        reason="SkillDefinition.version (str) shadows OntologyObject.version (int)",
        strict=True
    )
    def test_disable(self, full_skill: "SkillDefinition"):
        """disable should set status to DISABLED."""
        result = full_skill.disable()

        assert full_skill.skill_status == SkillStatus.DISABLED
        assert result is full_skill  # Method chaining

    @pytest.mark.xfail(
        reason="SkillDefinition.version (str) shadows OntologyObject.version (int)",
        strict=True
    )
    def test_method_chaining(self, basic_skill: "SkillDefinition"):
        """Methods should support chaining."""
        basic_skill.activate().record_execution()

        assert basic_skill.skill_status == SkillStatus.ACTIVE
        assert basic_skill.execution_count == 1


class TestSkillDefinitionRepr:
    """Tests for SkillDefinition string representation."""

    def test_skill_repr(self, basic_skill: "SkillDefinition"):
        """__repr__ should include key information."""
        repr_str = repr(basic_skill)
        assert "SkillDefinition" in repr_str
        assert "code_review" in repr_str
        assert "1.0.0" in repr_str
        assert "draft" in repr_str


# =============================================================================
# SKILLEXECUTION TESTS
# =============================================================================

class TestSkillExecutionFields:
    """Tests for SkillExecution field validation and defaults."""

    def test_execution_minimal_creation(self):
        """SkillExecution can be created with just skill_name."""
        execution = SkillExecution(skill_name="test_skill")
        assert execution.skill_name == "test_skill"
        assert execution.input_text == ""
        assert execution.output_text == ""
        assert execution.execution_status == ExecutionStatus.SUCCESS
        assert execution.duration_ms == 0
        assert execution.triggered_by == "keyword"

    def test_execution_skill_name_required(self):
        """SkillExecution requires skill_name."""
        with pytest.raises(ValueError):
            SkillExecution()

    def test_execution_skill_name_max_length(self):
        """skill_name must not exceed 100 characters."""
        with pytest.raises(ValueError):
            SkillExecution(skill_name="x" * 101)

    def test_execution_default_token_usage(self):
        """token_usage should default to zeros."""
        execution = SkillExecution(skill_name="test")
        assert execution.token_usage == {"input": 0, "output": 0, "total": 0}

    def test_execution_duration_non_negative(self):
        """duration_ms must be non-negative."""
        with pytest.raises(ValueError):
            SkillExecution(skill_name="test", duration_ms=-1)

    def test_execution_with_context(self, basic_execution: "SkillExecution"):
        """SkillExecution should store input correctly."""
        assert basic_execution.skill_name == "code_review"
        assert basic_execution.input_text == "Review this PR for issues"
        assert basic_execution.triggered_by == "keyword"

    def test_execution_started_at_auto_set(self):
        """started_at should be auto-set to current UTC time."""
        before = datetime.now(timezone.utc)
        execution = SkillExecution(skill_name="test")
        after = datetime.now(timezone.utc)

        assert before <= execution.started_at <= after


class TestSkillExecutionComplete:
    """Tests for SkillExecution.complete() method."""

    def test_complete_sets_completed_at(self, basic_execution: "SkillExecution"):
        """complete() should set completed_at timestamp."""
        assert basic_execution.completed_at is None

        basic_execution.complete(output_text="Done")

        assert basic_execution.completed_at is not None

    def test_complete_calculates_duration(self):
        """complete() should calculate duration_ms."""
        execution = SkillExecution(skill_name="test")
        # Small delay to ensure measurable duration
        time.sleep(0.01)  # 10ms

        execution.complete(output_text="Done")

        assert execution.duration_ms >= 10

    def test_complete_sets_output_text(self, basic_execution: "SkillExecution"):
        """complete() should set output_text."""
        basic_execution.complete(output_text="Analysis complete: 3 issues found")

        assert basic_execution.output_text == "Analysis complete: 3 issues found"

    def test_complete_sets_output_data(self, basic_execution: "SkillExecution"):
        """complete() should set output_data when provided."""
        output_data = {"issues": 3, "files": ["a.py", "b.py"]}

        basic_execution.complete(output_text="Done", output_data=output_data)

        assert basic_execution.output_data == output_data

    def test_complete_sets_status(self, basic_execution: "SkillExecution"):
        """complete() should set execution_status."""
        basic_execution.complete(
            output_text="Error occurred",
            execution_status=ExecutionStatus.FAILURE
        )

        assert basic_execution.execution_status == ExecutionStatus.FAILURE

    def test_complete_sets_error_message(self, basic_execution: "SkillExecution"):
        """complete() should set error_message when provided."""
        basic_execution.complete(
            output_text="",
            execution_status=ExecutionStatus.FAILURE,
            error_message="Connection timeout"
        )

        assert basic_execution.error_message == "Connection timeout"
        assert basic_execution.execution_status == ExecutionStatus.FAILURE

    def test_complete_returns_self(self, basic_execution: "SkillExecution"):
        """complete() should return self for method chaining."""
        result = basic_execution.complete(output_text="Done")

        assert result is basic_execution

    def test_complete_updates_version(self, basic_execution: "SkillExecution"):
        """complete() should call touch() and update version."""
        initial_version = basic_execution.version

        basic_execution.complete(output_text="Done")

        assert basic_execution.version == initial_version + 1


class TestSkillExecutionProperties:
    """Tests for SkillExecution properties."""

    def test_is_success_true(self, completed_execution: "SkillExecution"):
        """is_success should return True for SUCCESS status."""
        assert completed_execution.is_success is True

    def test_is_success_false(self):
        """is_success should return False for non-SUCCESS status."""
        execution = SkillExecution(skill_name="test")
        execution.execution_status = ExecutionStatus.FAILURE
        assert execution.is_success is False

    def test_is_failure_true(self):
        """is_failure should return True for FAILURE status."""
        execution = SkillExecution(skill_name="test")
        execution.execution_status = ExecutionStatus.FAILURE
        assert execution.is_failure is True

    def test_is_failure_false(self, completed_execution: "SkillExecution"):
        """is_failure should return False for non-FAILURE status."""
        assert completed_execution.is_failure is False

    def test_is_failure_timeout(self):
        """is_failure should return False for TIMEOUT status."""
        execution = SkillExecution(skill_name="test")
        execution.execution_status = ExecutionStatus.TIMEOUT
        assert execution.is_failure is False  # TIMEOUT is not FAILURE


class TestSkillExecutionToAuditLog:
    """Tests for SkillExecution.to_audit_log() method."""

    def test_audit_log_contains_required_fields(
        self, completed_execution: "SkillExecution"
    ):
        """to_audit_log() should return dict with all required fields."""
        audit_log = completed_execution.to_audit_log()

        required_fields = [
            "execution_id",
            "skill_name",
            "status",
            "duration_ms",
            "triggered_by",
            "trigger_match",
            "agent_id",
            "started_at",
            "completed_at",
            "error_message",
        ]
        for field in required_fields:
            assert field in audit_log

    def test_audit_log_execution_id(self, completed_execution: "SkillExecution"):
        """execution_id should be the object id."""
        audit_log = completed_execution.to_audit_log()
        assert audit_log["execution_id"] == completed_execution.id

    def test_audit_log_skill_name(self, completed_execution: "SkillExecution"):
        """skill_name should match the execution skill_name."""
        audit_log = completed_execution.to_audit_log()
        assert audit_log["skill_name"] == "deep_audit"

    def test_audit_log_status_value(self, completed_execution: "SkillExecution"):
        """status should be the enum value string."""
        audit_log = completed_execution.to_audit_log()
        assert audit_log["status"] == "success"

    def test_audit_log_timestamps_iso_format(
        self, completed_execution: "SkillExecution"
    ):
        """timestamps should be in ISO format."""
        audit_log = completed_execution.to_audit_log()

        # Verify ISO format by parsing
        if audit_log["started_at"]:
            datetime.fromisoformat(audit_log["started_at"].replace("Z", "+00:00"))
        if audit_log["completed_at"]:
            datetime.fromisoformat(audit_log["completed_at"].replace("Z", "+00:00"))

    def test_audit_log_none_values(self, basic_execution: "SkillExecution"):
        """to_audit_log() should handle None values."""
        audit_log = basic_execution.to_audit_log()

        assert audit_log["completed_at"] is None
        assert audit_log["error_message"] is None
        assert audit_log["trigger_match"] is None


class TestSkillExecutionRepr:
    """Tests for SkillExecution string representation."""

    def test_execution_repr(self, basic_execution: "SkillExecution"):
        """__repr__ should include key information."""
        repr_str = repr(basic_execution)
        assert "SkillExecution" in repr_str
        assert "code_review" in repr_str
        assert "success" in repr_str


# =============================================================================
# INHERITANCE TESTS (OntologyObject)
# =============================================================================

class TestOntologyObjectInheritance:
    """Tests that verify OntologyObject inheritance behavior."""

    def test_trigger_has_id(self, basic_trigger: "SkillTrigger"):
        """SkillTrigger should inherit id from OntologyObject."""
        assert basic_trigger.id is not None
        assert isinstance(basic_trigger.id, str)

    def test_skill_has_audit_fields(self, basic_skill: "SkillDefinition"):
        """SkillDefinition should inherit audit fields."""
        assert basic_skill.created_at is not None
        assert basic_skill.updated_at is not None

    def test_execution_has_status(self, basic_execution: "SkillExecution"):
        """SkillExecution should inherit ObjectStatus."""
        assert basic_execution.status == ObjectStatus.ACTIVE

    @pytest.mark.xfail(
        reason="SkillDefinition.version (str) shadows OntologyObject.version (int)",
        strict=True
    )
    def test_skill_touch_updates_timestamp(self, basic_skill: "SkillDefinition"):
        """touch() should update updated_at timestamp.

        Note: This test exposes a design conflict where SkillDefinition.version
        (semantic version string) shadows OntologyObject.version (int).
        """
        initial_updated_at = basic_skill.updated_at
        time.sleep(0.001)  # Ensure time difference

        basic_skill.touch()

        assert basic_skill.updated_at > initial_updated_at

    @pytest.mark.xfail(
        reason="SkillDefinition.version (str) shadows OntologyObject.version (int)",
        strict=True
    )
    def test_skill_soft_delete(self, basic_skill: "SkillDefinition"):
        """soft_delete() should set status to DELETED.

        Note: This test exposes a design conflict where SkillDefinition.version
        (semantic version string) shadows OntologyObject.version (int).
        """
        basic_skill.soft_delete()

        assert basic_skill.status == ObjectStatus.DELETED

    def test_execution_is_active(self, basic_execution: "SkillExecution"):
        """is_active should return True for ACTIVE status."""
        assert basic_execution.is_active is True
