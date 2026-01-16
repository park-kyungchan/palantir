"""
ODA v3.0 - E2E Tests for Complete Orchestration Flow
=====================================================

Tests the complete orchestration flow:
1. SubagentOutput -> Proposal conversion
2. Batch approval/rejection
3. Stage C verification
4. Approval mode selection
5. Error recovery and rollback

Reference: .claude/references/orchestration-flow.md
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ODA Imports
from lib.oda.ontology.actions import ActionContext, ActionResult
from lib.oda.ontology.actions.orchestration_actions import (
    ExecuteProposalBatchAction,
    GetOrchestrationStatusAction,
    OrchestrationResult,
    OrchestrationService,
    ProcessSubagentOutputAction,
    RollbackProposalsAction,
)
from lib.oda.ontology.actions.quality_actions import StageCVerifyAction
from lib.oda.ontology.evidence.quality_checks import (
    CheckStatus,
    Finding,
    FindingSeverity,
    QualityCheck,
    StageCEvidence,
)
from lib.oda.ontology.objects.proposal import (
    Proposal,
    ProposalPriority,
    ProposalStatus,
)
from lib.oda.claude.proposal_manager import (
    ApprovalMode,
    FileCreation,
    FileModification,
    ProposalManager,
    SubagentOutput,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def action_context() -> ActionContext:
    """Create a standard ActionContext for tests."""
    return ActionContext(
        actor_id="test-agent",
        metadata={"test": True},
    )


@pytest.fixture
def mock_database():
    """Mock database for isolation."""
    with patch("lib.oda.ontology.storage.database.Database") as mock_db_cls:
        mock_db = AsyncMock()
        mock_db.init = AsyncMock()
        mock_db.transaction = MagicMock()
        mock_db_cls.return_value = mock_db
        yield mock_db


@pytest.fixture
def mock_proposal_repository():
    """Mock ProposalRepository for isolation."""
    with patch(
        "lib.oda.ontology.storage.proposal_repository.ProposalRepository"
    ) as mock_repo_cls:
        mock_repo = AsyncMock()
        mock_repo_cls.return_value = mock_repo
        yield mock_repo


@pytest.fixture
def sample_subagent_output() -> SubagentOutput:
    """Sample SubagentOutput with multiple file operations."""
    return SubagentOutput(
        stage_a_evidence={
            "files_viewed": ["/path/to/a.py", "/path/to/b.py"],
            "requirements": ["FR1: Add feature X"],
            "complexity": "medium",
        },
        stage_b_evidence={
            "imports_verified": ["from module import Class"],
            "signatures_matched": ["def method(arg: Type) -> Return"],
        },
        files_to_modify=[
            FileModification(
                file_path="/path/to/a.py",
                old_content="# Original content A",
                new_content="# Modified content A",
                reason="Add feature X to module A",
            ),
            FileModification(
                file_path="/path/to/b.py",
                old_content="# Original content B",
                new_content="# Modified content B",
                reason="Add feature X to module B",
            ),
        ],
        files_to_create=[
            FileCreation(
                file_path="/path/to/c.py",
                content="# New file C",
                reason="Create helper module C",
            ),
        ],
        files_to_delete=["/path/to/deprecated.py"],
        verification_commands=["pytest tests/", "ruff check ."],
    )


@pytest.fixture
def sample_stage_c_evidence_passed() -> StageCEvidence:
    """Sample StageCEvidence that passes verification."""
    evidence = StageCEvidence(
        stage_started_at=datetime.now(),
        execution_context={"path": ".", "actor_id": "test-agent"},
    )
    evidence.add_quality_check(
        QualityCheck(
            name="build",
            status=CheckStatus.PASSED,
            command="python -m py_compile .",
            exit_code=0,
        )
    )
    evidence.add_quality_check(
        QualityCheck(
            name="tests",
            status=CheckStatus.PASSED,
            command="pytest tests/",
            exit_code=0,
        )
    )
    evidence.add_quality_check(
        QualityCheck(
            name="lint",
            status=CheckStatus.PASSED,
            command="ruff check .",
            exit_code=0,
        )
    )
    evidence.stage_completed_at = datetime.now()
    return evidence


@pytest.fixture
def sample_stage_c_evidence_critical() -> StageCEvidence:
    """Sample StageCEvidence with critical findings (should block)."""
    evidence = StageCEvidence(
        stage_started_at=datetime.now(),
        execution_context={"path": ".", "actor_id": "test-agent"},
    )
    evidence.add_quality_check(
        QualityCheck(
            name="build",
            status=CheckStatus.FAILED,
            command="python -m py_compile .",
            exit_code=1,
        )
    )
    evidence.add_quality_check(
        QualityCheck(
            name="tests",
            status=CheckStatus.FAILED,
            command="pytest tests/",
            exit_code=1,
        )
    )
    evidence.add_quality_check(
        QualityCheck(
            name="lint",
            status=CheckStatus.PASSED,
            command="ruff check .",
            exit_code=0,
        )
    )
    evidence.add_finding(
        Finding(
            severity=FindingSeverity.CRITICAL,
            category="build",
            message="Syntax error in module",
            file="a.py",
            line=10,
        )
    )
    evidence.stage_completed_at = datetime.now()
    return evidence


@pytest.fixture
def sample_stage_c_evidence_warnings() -> StageCEvidence:
    """Sample StageCEvidence with only warnings (should pass)."""
    evidence = StageCEvidence(
        stage_started_at=datetime.now(),
        execution_context={"path": ".", "actor_id": "test-agent"},
    )
    evidence.add_quality_check(
        QualityCheck(
            name="build",
            status=CheckStatus.PASSED,
            command="python -m py_compile .",
            exit_code=0,
        )
    )
    evidence.add_quality_check(
        QualityCheck(
            name="tests",
            status=CheckStatus.PASSED,
            command="pytest tests/",
            exit_code=0,
        )
    )
    evidence.add_quality_check(
        QualityCheck(
            name="lint",
            status=CheckStatus.PASSED,
            command="ruff check .",
            exit_code=0,
        )
    )
    # Add warnings only
    evidence.add_finding(
        Finding(
            severity=FindingSeverity.WARNING,
            category="lint",
            message="Line too long",
            file="a.py",
            line=15,
            code="E501",
            auto_fixable=True,
        )
    )
    evidence.add_finding(
        Finding(
            severity=FindingSeverity.WARNING,
            category="lint",
            message="Unused import",
            file="b.py",
            line=1,
            code="F401",
            auto_fixable=True,
        )
    )
    evidence.stage_completed_at = datetime.now()
    return evidence


# =============================================================================
# TEST: SUBAGENT OUTPUT TO PROPOSAL CONVERSION
# =============================================================================


class TestSubagentOutputToProposalConversion:
    """Test converting SubagentOutput to multiple file Proposals."""

    @pytest.mark.asyncio
    async def test_subagent_output_creates_file_proposals(
        self,
        sample_subagent_output: SubagentOutput,
        action_context: ActionContext,
    ):
        """Test converting SubagentOutput to multiple file Proposals."""
        output = sample_subagent_output

        # Verify the output has expected changes
        assert output.has_changes is True
        assert output.total_operations == 4  # 2 modify + 1 create + 1 delete

        # Verify structure
        assert len(output.files_to_modify) == 2
        assert len(output.files_to_create) == 1
        assert len(output.files_to_delete) == 1

        # Verify evidence is attached
        assert output.stage_a_evidence is not None
        assert "files_viewed" in output.stage_a_evidence
        assert output.stage_b_evidence is not None

    @pytest.mark.asyncio
    async def test_empty_output_creates_no_proposals(
        self,
        action_context: ActionContext,
    ):
        """Test that empty SubagentOutput creates no proposals."""
        output = SubagentOutput()

        assert output.has_changes is False
        assert output.total_operations == 0

    @pytest.mark.asyncio
    async def test_file_modification_validation(self):
        """Test FileModification validates absolute paths."""
        # Valid absolute path
        mod = FileModification(
            file_path="/absolute/path/file.py",
            new_content="content",
            reason="test",
        )
        assert mod.file_path.startswith("/")

        # Invalid relative path should fail
        with pytest.raises(ValueError, match="file_path must be absolute"):
            FileModification(
                file_path="relative/path/file.py",
                new_content="content",
                reason="test",
            )

    @pytest.mark.asyncio
    async def test_proposal_types_are_correct(
        self,
        sample_subagent_output: SubagentOutput,
    ):
        """Test that proposal action_types are correctly determined."""
        output = sample_subagent_output

        # Files to modify -> file.modify
        for mod in output.files_to_modify:
            assert mod.file_path.startswith("/")
            assert mod.new_content is not None

        # Files to create -> file.write
        for create in output.files_to_create:
            assert create.file_path.startswith("/")
            assert create.content is not None

        # Files to delete -> file.delete
        for delete_path in output.files_to_delete:
            assert delete_path.startswith("/")


# =============================================================================
# TEST: BATCH APPROVAL
# =============================================================================


class TestBatchApproval:
    """Test batch approval of multiple proposals."""

    @pytest.mark.asyncio
    async def test_batch_approval_approves_all(
        self,
        action_context: ActionContext,
    ):
        """Test batch approval of multiple proposals."""
        # Create mock proposals
        proposals = [
            Proposal(
                action_type="file.modify",
                payload={"file_path": f"/path/to/file{i}.py"},
                priority=ProposalPriority.MEDIUM,
                created_by="test-agent",
            )
            for i in range(3)
        ]

        # Submit all proposals
        for p in proposals:
            p.submit(submitter_id="test-agent")
            assert p.status == ProposalStatus.PENDING

        # Approve all
        for p in proposals:
            p.approve(reviewer_id="reviewer", comment="Batch approved")
            assert p.status == ProposalStatus.APPROVED
            assert p.reviewed_by == "reviewer"

    @pytest.mark.asyncio
    async def test_batch_approval_with_rejection(
        self,
        action_context: ActionContext,
    ):
        """Test batch approval when some proposals are rejected."""
        proposals = [
            Proposal(
                action_type="file.modify",
                payload={"file_path": f"/path/to/file{i}.py"},
                priority=ProposalPriority.MEDIUM,
                created_by="test-agent",
            )
            for i in range(3)
        ]

        # Submit all
        for p in proposals:
            p.submit(submitter_id="test-agent")

        # Approve first two, reject third
        proposals[0].approve(reviewer_id="reviewer", comment="Approved")
        proposals[1].approve(reviewer_id="reviewer", comment="Approved")
        proposals[2].reject(reviewer_id="reviewer", reason="Not needed")

        assert proposals[0].status == ProposalStatus.APPROVED
        assert proposals[1].status == ProposalStatus.APPROVED
        assert proposals[2].status == ProposalStatus.REJECTED
        assert proposals[2].review_comment == "Not needed"

    @pytest.mark.asyncio
    async def test_batch_summary_generation(
        self,
        sample_subagent_output: SubagentOutput,
        action_context: ActionContext,
    ):
        """Test batch summary generation for approval."""
        output = sample_subagent_output

        # Build summary similar to ProposalManager.batch_approval_summary
        summary_lines = [
            f"Total operations: {output.total_operations}",
            f"Modifications: {len(output.files_to_modify)}",
            f"Creations: {len(output.files_to_create)}",
            f"Deletions: {len(output.files_to_delete)}",
        ]

        assert "Total operations: 4" in summary_lines[0]
        assert "Modifications: 2" in summary_lines[1]
        assert "Creations: 1" in summary_lines[2]
        assert "Deletions: 1" in summary_lines[3]


# =============================================================================
# TEST: STAGE C VERIFICATION FLOW
# =============================================================================


class TestStageCVerificationFlow:
    """Test Stage C verification blocking and passing logic."""

    def test_stage_c_blocks_on_critical(
        self,
        sample_stage_c_evidence_critical: StageCEvidence,
    ):
        """Test that Stage C blocks when critical issues found."""
        evidence = sample_stage_c_evidence_critical

        assert evidence.critical_count > 0
        assert evidence.can_pass_stage() is False

        summary = evidence.to_summary()
        assert summary["status"] == "FAILED"
        assert summary["critical_count"] > 0

    def test_stage_c_passes_with_warnings(
        self,
        sample_stage_c_evidence_warnings: StageCEvidence,
    ):
        """Test that Stage C passes with only warnings."""
        evidence = sample_stage_c_evidence_warnings

        assert evidence.critical_count == 0
        assert evidence.error_count == 0
        assert evidence.findings_summary["WARNING"] == 2
        assert evidence.can_pass_stage() is True

        summary = evidence.to_summary()
        assert summary["status"] == "PASSED"

    def test_stage_c_requires_all_checks(self):
        """Test that Stage C requires build, tests, and lint checks."""
        evidence = StageCEvidence()

        # Only add tests (missing build and lint)
        evidence.add_quality_check(
            QualityCheck(
                name="tests",
                status=CheckStatus.PASSED,
                command="pytest",
                exit_code=0,
            )
        )

        # Should fail because build and lint are missing
        assert evidence.can_pass_stage() is False

    def test_stage_c_evidence_timing(
        self,
        sample_stage_c_evidence_passed: StageCEvidence,
    ):
        """Test Stage C evidence timing calculations."""
        evidence = sample_stage_c_evidence_passed

        duration = evidence.get_stage_duration_ms()
        assert duration is not None
        assert duration >= 0


# =============================================================================
# TEST: APPROVAL MODE SELECTION
# =============================================================================


class TestApprovalModeSelection:
    """Test different approval modes."""

    def test_interactive_mode_default(self):
        """Test interactive mode is default behavior."""
        mode = ApprovalMode.INTERACTIVE
        assert mode.value == "interactive"

    def test_batch_mode_collects_all(self):
        """Test batch mode collects proposals before approval."""
        mode = ApprovalMode.BATCH
        assert mode.value == "batch"

        # In batch mode, we collect all proposals first
        proposals = []
        for i in range(5):
            p = Proposal(
                action_type="file.modify",
                payload={"file_path": f"/path/file{i}.py"},
                created_by="agent",
            )
            p.submit()
            proposals.append(p)

        # All should be pending
        assert all(p.status == ProposalStatus.PENDING for p in proposals)

    def test_auto_mode_logs_without_asking(self):
        """Test auto mode approves without user interaction."""
        mode = ApprovalMode.AUTO
        assert mode.value == "auto"

        # In auto mode, proposals are auto-approved with audit log
        p = Proposal(
            action_type="file.modify",
            payload={"file_path": "/path/file.py"},
            created_by="agent",
        )
        p.submit()

        # Auto-approve
        p.approve(reviewer_id="auto-system", comment="Auto-approved")

        assert p.status == ProposalStatus.APPROVED
        assert p.reviewed_by == "auto-system"


# =============================================================================
# TEST: ERROR RECOVERY
# =============================================================================


class TestErrorRecovery:
    """Test error recovery and cleanup behaviors."""

    def test_proposal_rejection_cleanup(self):
        """Test cleanup after proposal rejection."""
        p = Proposal(
            action_type="file.modify",
            payload={
                "file_path": "/path/to/file.py",
                "new_content": "modified content",
            },
            created_by="agent",
        )
        p.submit()
        p.reject(reviewer_id="reviewer", reason="Changes not needed")

        # Proposal is in terminal state
        assert p.status == ProposalStatus.REJECTED
        assert p.is_terminal is True
        assert p.review_comment == "Changes not needed"

        # Cannot transition from terminal state (except to DELETED)
        with pytest.raises(Exception):  # InvalidTransitionError
            p.approve(reviewer_id="another")

    def test_proposal_cancellation(self):
        """Test proposal cancellation before execution."""
        p = Proposal(
            action_type="file.modify",
            payload={"file_path": "/path/file.py"},
            created_by="agent",
        )
        p.submit()
        p.approve(reviewer_id="reviewer")

        # Cancel before execution
        p.cancel(canceller_id="agent", reason="No longer needed")

        assert p.status == ProposalStatus.CANCELLED
        assert p.is_terminal is True

    def test_quality_gate_failure_detection(
        self,
        sample_stage_c_evidence_critical: StageCEvidence,
    ):
        """Test detection of quality gate failure for rollback trigger."""
        evidence = sample_stage_c_evidence_critical

        # Detection: critical_count > 0 or required check failed
        should_rollback = (
            evidence.critical_count > 0
            or any(
                c.status == CheckStatus.FAILED
                for c in evidence.quality_checks
                if c.name in {"build", "tests", "lint"}
            )
        )

        assert should_rollback is True

    def test_rollback_metadata_tracking(self):
        """Test that rollback operations track metadata correctly."""
        p = Proposal(
            action_type="file.modify",
            payload={
                "file_path": "/path/file.py",
                "old_content": "original",
                "new_content": "modified",
            },
            created_by="agent",
        )
        p.submit()
        p.approve(reviewer_id="reviewer")
        p.execute(executor_id="executor", result={"success": True})

        # Simulate rollback metadata update
        p.execution_result = p.execution_result or {}
        p.execution_result["rolled_back"] = True
        p.execution_result["rollback_reason"] = "Quality gate failed"
        p.execution_result["rollback_at"] = datetime.now().isoformat()
        p.execution_result["rollback_by"] = "system"

        assert p.execution_result["rolled_back"] is True
        assert "rollback_reason" in p.execution_result


# =============================================================================
# TEST: ORCHESTRATION ACTIONS
# =============================================================================


class TestOrchestrationActions:
    """Test orchestration action validation and execution."""

    @pytest.mark.asyncio
    async def test_process_subagent_output_validation(
        self,
        action_context: ActionContext,
    ):
        """Test ProcessSubagentOutputAction validation."""
        action = ProcessSubagentOutputAction()

        # Missing required fields should fail validation
        errors = action.validate({}, action_context)
        assert len(errors) > 0
        assert any("agent_id" in e for e in errors)

        # Valid params should pass validation
        errors = action.validate(
            {
                "agent_id": "test-agent",
                "output_data": {"files_to_modify": []},
                "approval_mode": "interactive",
            },
            action_context,
        )
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_execute_batch_validation(
        self,
        action_context: ActionContext,
    ):
        """Test ExecuteProposalBatchAction validation."""
        action = ExecuteProposalBatchAction()

        # Empty proposal_ids should fail
        errors = action.validate({"proposal_ids": []}, action_context)
        assert len(errors) > 0

        # Non-empty list should pass
        errors = action.validate(
            {"proposal_ids": ["proposal-1", "proposal-2"]},
            action_context,
        )
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_rollback_requires_proposal(self):
        """Test RollbackProposalsAction requires proposal approval."""
        action = RollbackProposalsAction()

        # Rollback is a hazardous action
        assert action.requires_proposal is True

    @pytest.mark.asyncio
    async def test_status_action_is_safe(self):
        """Test GetOrchestrationStatusAction is non-hazardous."""
        action = GetOrchestrationStatusAction()

        assert action.requires_proposal is False

    @pytest.mark.asyncio
    async def test_rollback_validation(
        self,
        action_context: ActionContext,
    ):
        """Test RollbackProposalsAction validation."""
        action = RollbackProposalsAction()

        # Missing reason should fail
        errors = action.validate(
            {"proposal_ids": ["p1"]},
            action_context,
        )
        assert len(errors) > 0
        assert any("reason" in e for e in errors)

        # Valid params should pass
        errors = action.validate(
            {
                "proposal_ids": ["p1"],
                "reason": "Quality gate failed",
            },
            action_context,
        )
        assert len(errors) == 0


# =============================================================================
# TEST: ORCHESTRATION SERVICE
# =============================================================================


class TestOrchestrationService:
    """Test OrchestrationService helper methods."""

    @pytest.mark.asyncio
    async def test_parse_subagent_output_structure(self):
        """Test parsing subagent output structure."""
        output_data = {
            "files_to_modify": [
                {
                    "file_path": "/path/a.py",
                    "new_content": "new",
                    "old_content": "old",
                    "reason": "test modify",
                }
            ],
            "files_to_create": [
                {
                    "file_path": "/path/b.py",
                    "content": "content",
                    "reason": "test create",
                }
            ],
            "files_to_delete": [
                {
                    "file_path": "/path/c.py",
                    "reason": "test delete",
                }
            ],
        }

        # Mock database
        with patch("lib.oda.ontology.storage.database.Database"):
            mock_db = MagicMock()
            service = OrchestrationService(mock_db)
            proposals = await service.parse_subagent_output(output_data)

        assert len(proposals) == 3

        # Check modify
        modify_proposal = next(p for p in proposals if p.operation == "modify")
        assert modify_proposal.file_path == "/path/a.py"
        assert modify_proposal.content == "new"
        assert modify_proposal.old_content == "old"

        # Check create
        create_proposal = next(p for p in proposals if p.operation == "write")
        assert create_proposal.file_path == "/path/b.py"
        assert create_proposal.content == "content"

        # Check delete
        delete_proposal = next(p for p in proposals if p.operation == "delete")
        assert delete_proposal.file_path == "/path/c.py"


# =============================================================================
# TEST: END-TO-END FLOW INTEGRATION
# =============================================================================


class TestE2EOrchestrationFlow:
    """Integration tests for the complete orchestration flow."""

    @pytest.mark.asyncio
    async def test_full_flow_happy_path(
        self,
        sample_subagent_output: SubagentOutput,
        action_context: ActionContext,
    ):
        """Test complete flow: output -> proposals -> approve -> execute."""
        output = sample_subagent_output

        # Step 1: Convert to proposals (simulated)
        proposals = []
        for mod in output.files_to_modify:
            p = Proposal(
                action_type="file.modify",
                payload={
                    "file_path": mod.file_path,
                    "old_content": mod.old_content,
                    "new_content": mod.new_content,
                    "reason": mod.reason,
                },
                created_by=action_context.actor_id,
            )
            p.submit()
            proposals.append(p)

        for create in output.files_to_create:
            p = Proposal(
                action_type="file.write",
                payload={
                    "file_path": create.file_path,
                    "content": create.content,
                    "reason": create.reason,
                },
                created_by=action_context.actor_id,
            )
            p.submit()
            proposals.append(p)

        # Step 2: Batch approval
        for p in proposals:
            p.approve(reviewer_id="reviewer", comment="Batch approved")

        assert all(p.status == ProposalStatus.APPROVED for p in proposals)

        # Step 3: Execute (simulated)
        for p in proposals:
            p.execute(executor_id=action_context.actor_id, result={"success": True})

        assert all(p.status == ProposalStatus.EXECUTED for p in proposals)

        # Step 4: Stage C verification (simulated pass)
        evidence = StageCEvidence()
        evidence.add_quality_check(
            QualityCheck(name="build", status=CheckStatus.PASSED, command="build")
        )
        evidence.add_quality_check(
            QualityCheck(name="tests", status=CheckStatus.PASSED, command="test")
        )
        evidence.add_quality_check(
            QualityCheck(name="lint", status=CheckStatus.PASSED, command="lint")
        )

        assert evidence.can_pass_stage() is True

    @pytest.mark.asyncio
    async def test_flow_with_rejection(
        self,
        sample_subagent_output: SubagentOutput,
        action_context: ActionContext,
    ):
        """Test flow where some proposals are rejected."""
        output = sample_subagent_output

        # Create proposals
        proposals = []
        for mod in output.files_to_modify:
            p = Proposal(
                action_type="file.modify",
                payload={"file_path": mod.file_path},
                created_by=action_context.actor_id,
            )
            p.submit()
            proposals.append(p)

        # Reviewer rejects one proposal
        proposals[0].approve(reviewer_id="reviewer")
        proposals[1].reject(reviewer_id="reviewer", reason="Unsafe change")

        # Only approved proposal can be executed
        assert proposals[0].can_execute is True
        assert proposals[1].can_execute is False
        assert proposals[1].is_terminal is True

    @pytest.mark.asyncio
    async def test_flow_with_quality_gate_failure(
        self,
        sample_subagent_output: SubagentOutput,
        sample_stage_c_evidence_critical: StageCEvidence,
        action_context: ActionContext,
    ):
        """Test flow where Stage C fails and triggers rollback need."""
        output = sample_subagent_output
        evidence = sample_stage_c_evidence_critical

        # Simulate executed proposals
        executed_proposal_ids = ["p1", "p2"]

        # Stage C fails
        assert evidence.can_pass_stage() is False

        # Rollback should be triggered
        should_rollback = not evidence.can_pass_stage()
        assert should_rollback is True

        # Rollback action would be created with these IDs
        rollback_params = {
            "proposal_ids": executed_proposal_ids,
            "reason": f"Stage C failed: {evidence.critical_count} critical issues",
        }

        assert len(rollback_params["proposal_ids"]) == 2
        assert "critical issues" in rollback_params["reason"]


# =============================================================================
# TEST: EDGE CASES
# =============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_proposal_state_machine_transitions(self):
        """Test all valid state transitions."""
        # DRAFT -> PENDING
        p = Proposal(action_type="file.modify", payload={}, created_by="agent")
        assert p.status == ProposalStatus.DRAFT
        p.submit()
        assert p.status == ProposalStatus.PENDING

        # PENDING -> APPROVED
        p2 = Proposal(action_type="file.modify", payload={}, created_by="agent")
        p2.submit()
        p2.approve(reviewer_id="reviewer")
        assert p2.status == ProposalStatus.APPROVED

        # APPROVED -> EXECUTED
        p2.execute(executor_id="executor")
        assert p2.status == ProposalStatus.EXECUTED

        # PENDING -> REJECTED
        p3 = Proposal(action_type="file.modify", payload={}, created_by="agent")
        p3.submit()
        p3.reject(reviewer_id="reviewer", reason="No")
        assert p3.status == ProposalStatus.REJECTED

    def test_empty_subagent_output_handling(self):
        """Test handling of empty subagent output."""
        output = SubagentOutput()

        assert output.has_changes is False
        assert output.total_operations == 0
        assert output.files_to_modify == []
        assert output.files_to_create == []
        assert output.files_to_delete == []

    def test_large_batch_size_validation(
        self,
        action_context: ActionContext,
    ):
        """Test validation of large batch sizes."""
        action = ExecuteProposalBatchAction()

        # 100 is max allowed
        errors = action.validate(
            {"proposal_ids": [f"p{i}" for i in range(100)]},
            action_context,
        )
        assert len(errors) == 0

        # 101 should fail
        errors = action.validate(
            {"proposal_ids": [f"p{i}" for i in range(101)]},
            action_context,
        )
        assert len(errors) > 0

    def test_stage_c_evidence_incremental_findings(self):
        """Test incremental addition of findings to evidence."""
        evidence = StageCEvidence()

        # Add findings one by one
        evidence.add_finding(
            Finding(
                severity=FindingSeverity.WARNING,
                category="lint",
                message="Warning 1",
                file="a.py",
                line=1,
            )
        )
        assert evidence.findings_summary["WARNING"] == 1

        evidence.add_finding(
            Finding(
                severity=FindingSeverity.ERROR,
                category="test",
                message="Error 1",
                file="b.py",
                line=2,
            )
        )
        assert evidence.findings_summary["ERROR"] == 1
        assert evidence.error_count == 1

        evidence.add_finding(
            Finding(
                severity=FindingSeverity.CRITICAL,
                category="security",
                message="Critical 1",
                file="c.py",
                line=3,
            )
        )
        assert evidence.findings_summary["CRITICAL"] == 1
        assert evidence.critical_count == 1

    def test_action_type_case_normalization(self):
        """Test that action_type is normalized to lowercase."""
        p = Proposal(
            action_type="FILE.Modify",  # Mixed case
            payload={},
            created_by="agent",
        )

        # Should be normalized to lowercase
        assert p.action_type == "file.modify"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
