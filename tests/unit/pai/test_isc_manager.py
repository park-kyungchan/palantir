"""
Unit tests for PAI Algorithm ISC Manager module.

Tests the Ideal State Contract (ISC) management system for THE ALGORITHM:
- ISCPhase: Execution phase enumeration
- ISCRowStatus: Row status enumeration
- ISCRow: Individual success criterion ObjectType
- ISCTable: Container for ISC rows ObjectType
- CreateISCAction: Create a new ISC table
- AddISCRowAction: Add a row to an ISC table
- UpdateISCStatusAction: Update status of an ISC row
- SetISCPhaseAction: Update the current phase of an ISC table
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import MagicMock, AsyncMock, patch

try:
    from lib.oda.pai.algorithm.isc_manager import (
        ISCPhase,
        ISCRowStatus,
        ISCRow,
        ISCTable,
        CreateISCAction,
        AddISCRowAction,
        UpdateISCStatusAction,
        SetISCPhaseAction,
    )
    from lib.oda.pai.algorithm.effort_levels import EffortLevel
    from lib.oda.ontology.actions import (
        ActionContext,
        EditType,
        ValidationError,
    )
    IMPORT_ERROR = None
except ImportError as e:
    IMPORT_ERROR = str(e)
    ISCPhase = None
    ISCRowStatus = None
    ISCRow = None
    ISCTable = None
    CreateISCAction = None
    AddISCRowAction = None
    UpdateISCStatusAction = None
    SetISCPhaseAction = None
    EffortLevel = None
    ActionContext = None
    EditType = None
    ValidationError = None


pytestmark = pytest.mark.skipif(
    IMPORT_ERROR is not None,
    reason=f"Could not import isc_manager module: {IMPORT_ERROR}"
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def action_context() -> ActionContext:
    """Default action context for tests."""
    return ActionContext(actor_id="test-user-001")


@pytest.fixture
def sample_isc_table() -> ISCTable:
    """Sample ISCTable instance."""
    return ISCTable(
        title="Test ISC Table",
        description="A test ISC for unit testing",
        created_by="test-user-001",
    )


@pytest.fixture
def sample_isc_row(sample_isc_table: ISCTable) -> ISCRow:
    """Sample ISCRow instance."""
    return ISCRow(
        isc_table_id=sample_isc_table.id,
        criterion="Implement feature X",
        current_state="Feature not implemented",
        ideal_state="Feature fully implemented and tested",
        created_by="test-user-001",
    )


@pytest.fixture
def completed_isc_table() -> ISCTable:
    """ISCTable with all rows completed."""
    return ISCTable(
        title="Completed ISC",
        total_rows=5,
        completed_rows=5,
        blocked_rows=0,
        current_phase=ISCPhase.COMPLETE,
        created_by="test-user-001",
    )


@pytest.fixture
def blocked_isc_table() -> ISCTable:
    """ISCTable with blocked rows."""
    return ISCTable(
        title="Blocked ISC",
        total_rows=5,
        completed_rows=2,
        blocked_rows=1,
        created_by="test-user-001",
    )


# =============================================================================
# ENUM TESTS: ISCPhase
# =============================================================================


class TestISCPhase:
    """Tests for ISCPhase enum."""

    EXPECTED_PHASES = [
        "definition",
        "analysis",
        "planning",
        "execution",
        "verification",
        "complete",
    ]

    def test_phase_count(self):
        """ISCPhase should have exactly 6 values."""
        assert len(ISCPhase) == 6

    @pytest.mark.parametrize("phase_value", EXPECTED_PHASES)
    def test_phase_has_value(self, phase_value: str):
        """Each expected phase value should exist in the enum."""
        phase_values = [p.value for p in ISCPhase]
        assert phase_value in phase_values

    def test_phase_is_str_enum(self):
        """ISCPhase should be a string enum for serialization."""
        assert ISCPhase.DEFINITION.value == "definition"
        assert isinstance(ISCPhase.DEFINITION.value, str)

    def test_phase_ordering(self):
        """Phases should be in logical execution order."""
        phases = list(ISCPhase)
        assert phases[0] == ISCPhase.DEFINITION
        assert phases[-1] == ISCPhase.COMPLETE

    def test_phase_definition(self):
        """DEFINITION phase is the initial contract creation phase."""
        assert ISCPhase.DEFINITION == ISCPhase.DEFINITION
        assert ISCPhase.DEFINITION.value == "definition"

    def test_phase_complete(self):
        """COMPLETE phase indicates all criteria met."""
        assert ISCPhase.COMPLETE.value == "complete"


# =============================================================================
# ENUM TESTS: ISCRowStatus
# =============================================================================


class TestISCRowStatus:
    """Tests for ISCRowStatus enum."""

    EXPECTED_STATUSES = [
        "pending",
        "in_progress",
        "completed",
        "blocked",
        "skipped",
    ]

    def test_status_count(self):
        """ISCRowStatus should have exactly 5 values."""
        assert len(ISCRowStatus) == 5

    @pytest.mark.parametrize("status_value", EXPECTED_STATUSES)
    def test_status_has_value(self, status_value: str):
        """Each expected status value should exist in the enum."""
        status_values = [s.value for s in ISCRowStatus]
        assert status_value in status_values

    def test_status_is_str_enum(self):
        """ISCRowStatus should be a string enum for serialization."""
        assert ISCRowStatus.PENDING.value == "pending"
        assert isinstance(ISCRowStatus.PENDING.value, str)

    def test_status_pending_default(self):
        """PENDING should be the natural starting state."""
        assert ISCRowStatus.PENDING.value == "pending"

    def test_status_completed(self):
        """COMPLETED indicates successful completion."""
        assert ISCRowStatus.COMPLETED.value == "completed"

    def test_status_blocked(self):
        """BLOCKED indicates a blocked criterion."""
        assert ISCRowStatus.BLOCKED.value == "blocked"

    def test_status_skipped(self):
        """SKIPPED indicates a skipped criterion."""
        assert ISCRowStatus.SKIPPED.value == "skipped"


# =============================================================================
# OBJECT TYPE TESTS: ISCRow
# =============================================================================


class TestISCRow:
    """Tests for ISCRow ObjectType."""

    def test_row_creation_minimal(self):
        """ISCRow can be created with minimal required fields."""
        row = ISCRow(
            isc_table_id="table-001",
            criterion="Test criterion",
        )
        assert row.isc_table_id == "table-001"
        assert row.criterion == "Test criterion"
        assert row.row_status == ISCRowStatus.PENDING
        assert row.can_parallel is True

    def test_row_creation_full(self):
        """ISCRow can be created with all fields."""
        row = ISCRow(
            isc_table_id="table-001",
            criterion="Test criterion",
            current_state="Current state description",
            ideal_state="Ideal state description",
            row_status=ISCRowStatus.IN_PROGRESS,
            can_parallel=False,
            dependencies=["row-001", "row-002"],
            assigned_capability="sonnet",
            notes="Important notes",
            created_by="test-user",
        )
        assert row.current_state == "Current state description"
        assert row.ideal_state == "Ideal state description"
        assert row.row_status == ISCRowStatus.IN_PROGRESS
        assert row.can_parallel is False
        assert row.dependencies == ["row-001", "row-002"]
        assert row.assigned_capability == "sonnet"
        assert row.notes == "Important notes"

    def test_row_has_auto_generated_id(self):
        """ISCRow should have an auto-generated UUID id."""
        row = ISCRow(isc_table_id="table-001", criterion="Test")
        assert row.id is not None
        assert len(row.id) > 0

    def test_row_is_ready_when_pending(self):
        """is_ready should return True when status is PENDING."""
        row = ISCRow(
            isc_table_id="table-001",
            criterion="Test",
            row_status=ISCRowStatus.PENDING,
        )
        assert row.is_ready is True

    def test_row_is_not_ready_when_in_progress(self):
        """is_ready should return False when status is IN_PROGRESS."""
        row = ISCRow(
            isc_table_id="table-001",
            criterion="Test",
            row_status=ISCRowStatus.IN_PROGRESS,
        )
        assert row.is_ready is False

    def test_row_is_complete_when_completed(self):
        """is_complete should return True when status is COMPLETED."""
        row = ISCRow(
            isc_table_id="table-001",
            criterion="Test",
            row_status=ISCRowStatus.COMPLETED,
        )
        assert row.is_complete is True

    def test_row_is_complete_when_skipped(self):
        """is_complete should return True when status is SKIPPED."""
        row = ISCRow(
            isc_table_id="table-001",
            criterion="Test",
            row_status=ISCRowStatus.SKIPPED,
        )
        assert row.is_complete is True

    def test_row_is_not_complete_when_blocked(self):
        """is_complete should return False when status is BLOCKED."""
        row = ISCRow(
            isc_table_id="table-001",
            criterion="Test",
            row_status=ISCRowStatus.BLOCKED,
        )
        assert row.is_complete is False

    def test_row_criterion_max_length_validation(self):
        """Criterion should enforce max length of 500 characters."""
        long_criterion = "x" * 501
        with pytest.raises(Exception):  # Pydantic validation error
            ISCRow(isc_table_id="table-001", criterion=long_criterion)

    def test_row_evidence_list(self):
        """Evidence should be stored as a list."""
        row = ISCRow(
            isc_table_id="table-001",
            criterion="Test",
            evidence=["evidence1", "evidence2"],
        )
        assert len(row.evidence) == 2
        assert "evidence1" in row.evidence

    def test_row_completed_at_initially_none(self):
        """completed_at should be None initially."""
        row = ISCRow(isc_table_id="table-001", criterion="Test")
        assert row.completed_at is None


# =============================================================================
# OBJECT TYPE TESTS: ISCTable
# =============================================================================


class TestISCTable:
    """Tests for ISCTable ObjectType."""

    def test_table_creation_minimal(self):
        """ISCTable can be created with minimal required fields."""
        table = ISCTable(title="Test Table")
        assert table.title == "Test Table"
        assert table.current_phase == ISCPhase.DEFINITION
        assert table.effort_level == EffortLevel.STANDARD
        assert table.total_rows == 0

    def test_table_creation_full(self):
        """ISCTable can be created with all fields."""
        table = ISCTable(
            title="Full Test Table",
            description="A comprehensive test table",
            current_phase=ISCPhase.EXECUTION,
            effort_level=EffortLevel.THOROUGH,
            row_ids=["row-001", "row-002"],
            total_rows=2,
            completed_rows=1,
            blocked_rows=0,
            task_id="task-001",
            parent_isc_id="parent-isc-001",
            metadata={"key": "value"},
            created_by="test-user",
        )
        assert table.description == "A comprehensive test table"
        assert table.current_phase == ISCPhase.EXECUTION
        assert table.effort_level == EffortLevel.THOROUGH
        assert len(table.row_ids) == 2
        assert table.task_id == "task-001"
        assert table.parent_isc_id == "parent-isc-001"

    def test_table_has_auto_generated_id(self):
        """ISCTable should have an auto-generated UUID id."""
        table = ISCTable(title="Test")
        assert table.id is not None
        assert len(table.id) > 0

    def test_table_completion_percentage_empty(self):
        """Completion percentage should be 0 for empty table."""
        table = ISCTable(title="Empty", total_rows=0)
        assert table.completion_percentage == 0.0

    def test_table_completion_percentage_partial(self):
        """Completion percentage should calculate correctly."""
        table = ISCTable(title="Partial", total_rows=10, completed_rows=5)
        assert table.completion_percentage == 50.0

    def test_table_completion_percentage_full(self):
        """Completion percentage should be 100 when all complete."""
        table = ISCTable(title="Complete", total_rows=5, completed_rows=5)
        assert table.completion_percentage == 100.0

    def test_table_is_complete_true(self, completed_isc_table: ISCTable):
        """is_complete should return True when all rows completed."""
        assert completed_isc_table.is_complete is True

    def test_table_is_complete_false_empty(self):
        """is_complete should return False when table is empty."""
        table = ISCTable(title="Empty", total_rows=0)
        assert table.is_complete is False

    def test_table_is_complete_false_partial(self):
        """is_complete should return False when partially completed."""
        table = ISCTable(title="Partial", total_rows=10, completed_rows=5)
        assert table.is_complete is False

    def test_table_is_blocked_true(self, blocked_isc_table: ISCTable):
        """is_blocked should return True when there are blocked rows."""
        assert blocked_isc_table.is_blocked is True

    def test_table_is_blocked_false(self):
        """is_blocked should return False when no rows are blocked."""
        table = ISCTable(title="Not Blocked", blocked_rows=0)
        assert table.is_blocked is False

    def test_table_to_summary(self, sample_isc_table: ISCTable):
        """to_summary should return a proper summary dict."""
        summary = sample_isc_table.to_summary()
        assert "id" in summary
        assert "title" in summary
        assert "phase" in summary
        assert "effort" in summary
        assert "progress" in summary
        assert "completion" in summary
        assert "blocked" in summary
        assert summary["title"] == "Test ISC Table"

    def test_table_title_max_length(self):
        """Title should enforce max length of 255 characters."""
        long_title = "x" * 256
        with pytest.raises(Exception):  # Pydantic validation error
            ISCTable(title=long_title)


# =============================================================================
# ACTION TESTS: CreateISCAction
# =============================================================================


class TestCreateISCAction:
    """Tests for CreateISCAction."""

    def test_action_has_api_name(self):
        """CreateISCAction should have correct api_name."""
        assert CreateISCAction.api_name == "pai.create_isc"

    def test_action_object_type(self):
        """CreateISCAction should target ISCTable."""
        assert CreateISCAction.object_type == ISCTable

    def test_action_does_not_require_proposal(self):
        """CreateISCAction should not require proposal."""
        assert CreateISCAction.requires_proposal is False

    @pytest.mark.asyncio
    async def test_apply_edits_creates_isc_table(self, action_context: ActionContext):
        """apply_edits should create an ISCTable."""
        action = CreateISCAction()
        params = {
            "title": "New ISC Table",
            "description": "Test description",
        }

        result, edits = await action.apply_edits(params, action_context)

        assert result is not None
        assert isinstance(result, ISCTable)
        assert result.title == "New ISC Table"
        assert result.description == "Test description"
        assert result.created_by == "test-user-001"

    @pytest.mark.asyncio
    async def test_apply_edits_creates_edit_operation(self, action_context: ActionContext):
        """apply_edits should create a CREATE EditOperation."""
        action = CreateISCAction()
        params = {"title": "New ISC Table"}

        result, edits = await action.apply_edits(params, action_context)

        assert len(edits) == 1
        assert edits[0].edit_type == EditType.CREATE
        assert edits[0].object_type == "ISCTable"

    @pytest.mark.asyncio
    async def test_apply_edits_with_effort_level(self, action_context: ActionContext):
        """apply_edits should handle effort_level parameter."""
        action = CreateISCAction()
        params = {
            "title": "New ISC Table",
            "effort_level": "THOROUGH",
        }

        result, edits = await action.apply_edits(params, action_context)

        assert result.effort_level == EffortLevel.THOROUGH

    def test_validation_requires_title(self, action_context: ActionContext):
        """Validation should fail without title."""
        action = CreateISCAction()
        params = {"description": "No title"}

        errors = action.validate(params, action_context)

        assert len(errors) > 0
        assert any("title" in error.lower() for error in errors)


# =============================================================================
# ACTION TESTS: AddISCRowAction
# =============================================================================


class TestAddISCRowAction:
    """Tests for AddISCRowAction."""

    def test_action_has_api_name(self):
        """AddISCRowAction should have correct api_name."""
        assert AddISCRowAction.api_name == "pai.add_isc_row"

    def test_action_object_type(self):
        """AddISCRowAction should target ISCRow."""
        assert AddISCRowAction.object_type == ISCRow

    def test_action_does_not_require_proposal(self):
        """AddISCRowAction should not require proposal."""
        assert AddISCRowAction.requires_proposal is False

    @pytest.mark.asyncio
    async def test_apply_edits_creates_isc_row(self, action_context: ActionContext):
        """apply_edits should create an ISCRow."""
        action = AddISCRowAction()
        params = {
            "isc_table_id": "table-001",
            "criterion": "Implement feature X",
            "current_state": "Not implemented",
            "ideal_state": "Fully implemented",
        }

        result, edits = await action.apply_edits(params, action_context)

        assert result is not None
        assert isinstance(result, ISCRow)
        assert result.criterion == "Implement feature X"
        assert result.isc_table_id == "table-001"

    @pytest.mark.asyncio
    async def test_apply_edits_creates_link_operation(self, action_context: ActionContext):
        """apply_edits should create both CREATE and LINK operations."""
        action = AddISCRowAction()
        params = {
            "isc_table_id": "table-001",
            "criterion": "Test criterion",
        }

        result, edits = await action.apply_edits(params, action_context)

        assert len(edits) == 2
        assert edits[0].edit_type == EditType.CREATE
        assert edits[1].edit_type == EditType.LINK
        assert edits[1].object_type == "ISCTable"

    def test_validation_requires_isc_table_id(self, action_context: ActionContext):
        """Validation should fail without isc_table_id."""
        action = AddISCRowAction()
        params = {"criterion": "Test"}

        errors = action.validate(params, action_context)

        assert len(errors) > 0
        assert any("isc_table_id" in error.lower() for error in errors)

    def test_validation_requires_criterion(self, action_context: ActionContext):
        """Validation should fail without criterion."""
        action = AddISCRowAction()
        params = {"isc_table_id": "table-001"}

        errors = action.validate(params, action_context)

        assert len(errors) > 0
        assert any("criterion" in error.lower() for error in errors)


# =============================================================================
# ACTION TESTS: UpdateISCStatusAction
# =============================================================================


class TestUpdateISCStatusAction:
    """Tests for UpdateISCStatusAction."""

    def test_action_has_api_name(self):
        """UpdateISCStatusAction should have correct api_name."""
        assert UpdateISCStatusAction.api_name == "pai.update_isc_status"

    def test_action_object_type(self):
        """UpdateISCStatusAction should target ISCRow."""
        assert UpdateISCStatusAction.object_type == ISCRow

    def test_action_does_not_require_proposal(self):
        """UpdateISCStatusAction should not require proposal."""
        assert UpdateISCStatusAction.requires_proposal is False

    @pytest.mark.asyncio
    async def test_apply_edits_updates_status(self, action_context: ActionContext):
        """apply_edits should update row status."""
        action = UpdateISCStatusAction()
        params = {
            "row_id": "row-001",
            "row_status": "in_progress",
        }

        result, edits = await action.apply_edits(params, action_context)

        assert len(edits) >= 1
        assert edits[0].edit_type == EditType.MODIFY
        assert edits[0].object_type == "ISCRow"
        assert edits[0].changes["row_status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_apply_edits_adds_completed_at_on_completion(
        self, action_context: ActionContext
    ):
        """apply_edits should add completed_at when marking complete."""
        action = UpdateISCStatusAction()
        params = {
            "row_id": "row-001",
            "row_status": "completed",
        }

        result, edits = await action.apply_edits(params, action_context)

        assert "completed_at" in edits[0].changes

    @pytest.mark.asyncio
    async def test_apply_edits_adds_evidence(self, action_context: ActionContext):
        """apply_edits should include evidence when provided."""
        action = UpdateISCStatusAction()
        params = {
            "row_id": "row-001",
            "row_status": "completed",
            "evidence": ["Test passed", "Code reviewed"],
        }

        result, edits = await action.apply_edits(params, action_context)

        assert edits[0].changes["evidence"] == ["Test passed", "Code reviewed"]

    def test_validation_requires_row_id(self, action_context: ActionContext):
        """Validation should fail without row_id."""
        action = UpdateISCStatusAction()
        params = {"row_status": "completed"}

        errors = action.validate(params, action_context)

        assert len(errors) > 0
        assert any("row_id" in error.lower() for error in errors)

    def test_validation_requires_row_status(self, action_context: ActionContext):
        """Validation should fail without row_status."""
        action = UpdateISCStatusAction()
        params = {"row_id": "row-001"}

        errors = action.validate(params, action_context)

        assert len(errors) > 0
        assert any("row_status" in error.lower() for error in errors)

    def test_validation_row_status_allowed_values(self, action_context: ActionContext):
        """Validation should fail with invalid row_status value."""
        action = UpdateISCStatusAction()
        params = {
            "row_id": "row-001",
            "row_status": "invalid_status",
        }

        errors = action.validate(params, action_context)

        assert len(errors) > 0


# =============================================================================
# ACTION TESTS: SetISCPhaseAction
# =============================================================================


class TestSetISCPhaseAction:
    """Tests for SetISCPhaseAction."""

    def test_action_has_api_name(self):
        """SetISCPhaseAction should have correct api_name."""
        assert SetISCPhaseAction.api_name == "pai.set_isc_phase"

    def test_action_object_type(self):
        """SetISCPhaseAction should target ISCTable."""
        assert SetISCPhaseAction.object_type == ISCTable

    def test_action_does_not_require_proposal(self):
        """SetISCPhaseAction should not require proposal."""
        assert SetISCPhaseAction.requires_proposal is False

    @pytest.mark.asyncio
    async def test_apply_edits_updates_phase(self, action_context: ActionContext):
        """apply_edits should update table phase."""
        action = SetISCPhaseAction()
        params = {
            "isc_table_id": "table-001",
            "phase": "execution",
        }

        result, edits = await action.apply_edits(params, action_context)

        assert len(edits) == 1
        assert edits[0].edit_type == EditType.MODIFY
        assert edits[0].object_type == "ISCTable"
        assert edits[0].changes["current_phase"] == "execution"

    @pytest.mark.asyncio
    async def test_apply_edits_adds_notes_to_metadata(self, action_context: ActionContext):
        """apply_edits should add notes to metadata when provided."""
        action = SetISCPhaseAction()
        params = {
            "isc_table_id": "table-001",
            "phase": "verification",
            "notes": "Moving to verification phase",
        }

        result, edits = await action.apply_edits(params, action_context)

        assert "metadata" in edits[0].changes
        assert "phase_verification_notes" in edits[0].changes["metadata"]

    def test_validation_requires_isc_table_id(self, action_context: ActionContext):
        """Validation should fail without isc_table_id."""
        action = SetISCPhaseAction()
        params = {"phase": "execution"}

        errors = action.validate(params, action_context)

        assert len(errors) > 0
        assert any("isc_table_id" in error.lower() for error in errors)

    def test_validation_requires_phase(self, action_context: ActionContext):
        """Validation should fail without phase."""
        action = SetISCPhaseAction()
        params = {"isc_table_id": "table-001"}

        errors = action.validate(params, action_context)

        assert len(errors) > 0
        assert any("phase" in error.lower() for error in errors)

    def test_validation_phase_allowed_values(self, action_context: ActionContext):
        """Validation should fail with invalid phase value."""
        action = SetISCPhaseAction()
        params = {
            "isc_table_id": "table-001",
            "phase": "invalid_phase",
        }

        errors = action.validate(params, action_context)

        assert len(errors) > 0


# =============================================================================
# STATE MACHINE TESTS
# =============================================================================


class TestISCStateMachine:
    """Tests for ISC state machine transitions."""

    @pytest.mark.parametrize(
        "from_status,to_status",
        [
            (ISCRowStatus.PENDING, ISCRowStatus.IN_PROGRESS),
            (ISCRowStatus.IN_PROGRESS, ISCRowStatus.COMPLETED),
            (ISCRowStatus.PENDING, ISCRowStatus.BLOCKED),
            (ISCRowStatus.BLOCKED, ISCRowStatus.PENDING),
            (ISCRowStatus.PENDING, ISCRowStatus.SKIPPED),
        ],
    )
    def test_valid_row_status_transitions(
        self, from_status: ISCRowStatus, to_status: ISCRowStatus
    ):
        """Test valid status transitions for ISCRow."""
        row = ISCRow(
            isc_table_id="table-001",
            criterion="Test",
            row_status=from_status,
        )
        # Status can be updated (no validation in object itself)
        row.row_status = to_status
        assert row.row_status == to_status

    @pytest.mark.parametrize(
        "from_phase,to_phase",
        [
            (ISCPhase.DEFINITION, ISCPhase.ANALYSIS),
            (ISCPhase.ANALYSIS, ISCPhase.PLANNING),
            (ISCPhase.PLANNING, ISCPhase.EXECUTION),
            (ISCPhase.EXECUTION, ISCPhase.VERIFICATION),
            (ISCPhase.VERIFICATION, ISCPhase.COMPLETE),
        ],
    )
    def test_valid_phase_transitions(
        self, from_phase: ISCPhase, to_phase: ISCPhase
    ):
        """Test valid phase transitions for ISCTable."""
        table = ISCTable(title="Test", current_phase=from_phase)
        table.current_phase = to_phase
        assert table.current_phase == to_phase


# =============================================================================
# INTEGRATION-LIKE TESTS
# =============================================================================


class TestISCTableRowInteraction:
    """Tests for ISCTable and ISCRow interaction patterns."""

    def test_table_tracks_row_ids(self):
        """ISCTable should track row IDs."""
        table = ISCTable(
            title="Test",
            row_ids=["row-001", "row-002", "row-003"],
            total_rows=3,
        )
        assert len(table.row_ids) == 3
        assert table.total_rows == 3

    def test_table_progress_calculation(self):
        """ISCTable should calculate progress correctly."""
        table = ISCTable(
            title="Test",
            total_rows=4,
            completed_rows=3,
        )
        assert table.completion_percentage == 75.0
        assert table.is_complete is False

    def test_table_blocked_state_affects_is_blocked(self):
        """ISCTable.is_blocked should reflect blocked_rows count."""
        table = ISCTable(title="Test", blocked_rows=0)
        assert table.is_blocked is False

        table.blocked_rows = 1
        assert table.is_blocked is True

    def test_row_dependencies_list(self):
        """ISCRow should track dependencies."""
        row = ISCRow(
            isc_table_id="table-001",
            criterion="Dependent task",
            dependencies=["row-001", "row-002"],
        )
        assert len(row.dependencies) == 2
        assert "row-001" in row.dependencies
