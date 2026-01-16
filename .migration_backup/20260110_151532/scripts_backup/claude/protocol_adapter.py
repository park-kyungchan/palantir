"""
ODA Protocol Adapter

Bridges existing ODA ThreeStageProtocol implementations with Claude Code execution model.
Enables automatic TodoWrite state management, evidence validation, and rollback support.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type

# ODA Protocol imports
from scripts.ontology.protocols.base import (
    ThreeStageProtocol,
    ProtocolContext as ODAProtocolContext,
    StageResult as ODAStageResult,
    Stage,
    Finding,
    Severity,
)

# Claude integration imports
from scripts.claude.evidence_tracker import EvidenceTracker, EvidenceContext
from scripts.claude.todo_sync import TodoTaskSync, TodoStatus
from scripts.claude.protocol_runner import ProtocolStage, StageResult, STAGE_CONFIGS


# Protocol Registry - maps protocol names to implementations
PROTOCOL_REGISTRY: Dict[str, Type[ThreeStageProtocol]] = {}

def register_protocol(name: str):
    """Decorator to register a protocol implementation."""
    def decorator(cls: Type[ThreeStageProtocol]) -> Type[ThreeStageProtocol]:
        PROTOCOL_REGISTRY[name] = cls
        return cls
    return decorator


@dataclass
class ProtocolCheckpoint:
    """Snapshot of protocol state for rollback."""
    stage: ProtocolStage
    timestamp: str
    evidence_snapshot: Dict[str, Any]
    todo_ids: Dict[ProtocolStage, str]
    findings: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def capture(
        cls,
        stage: ProtocolStage,
        evidence: EvidenceTracker,
        todo_ids: Dict[ProtocolStage, str],
        findings: List[Dict[str, Any]] = None,
    ) -> "ProtocolCheckpoint":
        return cls(
            stage=stage,
            timestamp=datetime.utcnow().isoformat(),
            evidence_snapshot=evidence.export(),
            todo_ids=todo_ids.copy(),
            findings=findings or [],
        )


class TodoWriteManager:
    """Manages TodoWrite state through protocol execution."""

    def __init__(self, todo_sync: Optional[TodoTaskSync] = None):
        self.todo_sync = todo_sync or TodoTaskSync()
        self._stage_todos: Dict[ProtocolStage, str] = {}

    async def initialize_stages(
        self,
        trace_id: str,
        actor_id: str = "claude_code_agent",
    ) -> List[Dict[str, Any]]:
        """Create pending todos for all stages."""
        todos = []
        for stage in ProtocolStage:
            config = STAGE_CONFIGS[stage]
            try:
                task = await self.todo_sync.create_task_from_todo(
                    content=config.todo_content,
                    status=TodoStatus.PENDING,
                    trace_id=trace_id,
                    actor_id=actor_id,
                )
                self._stage_todos[stage] = task.id
            except Exception:
                # Database may not be available - continue without persistence
                self._stage_todos[stage] = f"local_{stage.value}"

            todos.append({
                "content": config.todo_content,
                "status": "pending",
                "activeForm": config.todo_active_form,
            })
        return todos

    async def mark_stage_in_progress(self, stage: ProtocolStage) -> None:
        """Update TodoWrite when stage begins."""
        if stage in self._stage_todos:
            try:
                await self.todo_sync.update_task_status(
                    self._stage_todos[stage],
                    TodoStatus.IN_PROGRESS,
                )
            except Exception:
                pass  # Continue without persistence

    async def mark_stage_completed(self, stage: ProtocolStage, passed: bool) -> None:
        """Update TodoWrite when stage completes."""
        if stage in self._stage_todos:
            status = TodoStatus.COMPLETED if passed else TodoStatus.PENDING
            try:
                await self.todo_sync.update_task_status(
                    self._stage_todos[stage],
                    status,
                )
            except Exception:
                pass

    def get_stage_todos(self) -> Dict[ProtocolStage, str]:
        return self._stage_todos.copy()


class StageBoundaryValidator:
    """Validates evidence requirements at stage transitions."""

    MINIMUM_EVIDENCE: Dict[ProtocolStage, Dict[str, int]] = {
        ProtocolStage.A_SCAN: {"files": 1, "lines": 0, "snippets": 0},
        ProtocolStage.B_TRACE: {"files": 3, "lines": 5, "snippets": 0},
        ProtocolStage.C_VERIFY: {"files": 3, "lines": 10, "snippets": 1},
    }

    def validate_transition(
        self,
        from_stage: Optional[ProtocolStage],
        to_stage: ProtocolStage,
        evidence: EvidenceTracker,
    ) -> Dict[str, Any]:
        """Validate evidence is sufficient to proceed to next stage."""
        result = {"valid": True, "errors": [], "warnings": []}

        if from_stage is None:
            return result

        validation = evidence.validate(stage=from_stage.value, strict=False)

        if not validation["valid"]:
            result["valid"] = False
            result["errors"] = validation.get("errors", [])

        return result


class ODAProtocolAdapter:
    """
    Adapts ODA ThreeStageProtocol to Claude Code execution model.

    Features:
    - Automatic evidence bridging between ODA and Claude Code
    - TodoWrite state management
    - Checkpoint/rollback support
    - Stage boundary validation
    """

    def __init__(
        self,
        protocol: ThreeStageProtocol,
        target_path: str,
        session_id: str,
        actor_id: str = "claude_code_agent",
    ):
        self.protocol = protocol
        self.target_path = Path(target_path)
        self.session_id = session_id
        self.actor_id = actor_id

        # ODA context
        self.oda_context = ODAProtocolContext(
            target_path=str(target_path),
            actor_id=actor_id,
        )

        # Claude Code integration
        self.evidence_tracker = EvidenceTracker(
            session_id=session_id,
            actor_id=actor_id,
        )
        self.todo_manager = TodoWriteManager()
        self.boundary_validator = StageBoundaryValidator()

        # State
        self._checkpoints: List[ProtocolCheckpoint] = []
        self._stage_results: Dict[ProtocolStage, ODAStageResult] = {}

    def _sync_evidence_to_oda(self) -> None:
        """Sync Claude Code evidence to ODA ProtocolContext."""
        evidence = self.evidence_tracker.export()

        for file_path in evidence.get("files_viewed", []):
            self.oda_context.add_file_evidence(file_path)

        for file_path, lines in evidence.get("lines_referenced", {}).items():
            self.oda_context.add_file_evidence(file_path, lines)

    def _sync_evidence_from_oda(self, stage_result: ODAStageResult) -> None:
        """Sync ODA StageResult evidence to Claude Code tracker."""
        evidence = stage_result.evidence

        for file_path in evidence.get("files_viewed", []):
            self.evidence_tracker.track_file_read(file_path)

        for file_path, lines in evidence.get("lines_referenced", {}).items():
            for line in lines:
                self.evidence_tracker.track_line_reference(
                    file_path, line, "", claim=None
                )

    def _convert_stage(self, protocol_stage: ProtocolStage) -> Stage:
        """Convert Claude ProtocolStage to ODA Stage."""
        mapping = {
            ProtocolStage.A_SCAN: Stage.A_SCAN,
            ProtocolStage.B_TRACE: Stage.B_TRACE,
            ProtocolStage.C_VERIFY: Stage.C_VERIFY,
        }
        return mapping[protocol_stage]

    async def execute_stage_a(self) -> StageResult:
        """Execute Stage A: SCAN through ODA protocol."""
        await self.todo_manager.mark_stage_in_progress(ProtocolStage.A_SCAN)

        # Checkpoint before execution
        self._checkpoints.append(ProtocolCheckpoint.capture(
            stage=ProtocolStage.A_SCAN,
            evidence=self.evidence_tracker,
            todo_ids=self.todo_manager.get_stage_todos(),
        ))

        try:
            # Sync evidence to ODA context
            self._sync_evidence_to_oda()

            # Execute ODA stage
            oda_result = await self.protocol.stage_a(self.oda_context)
            self._stage_results[ProtocolStage.A_SCAN] = oda_result

            # Sync evidence back
            self._sync_evidence_from_oda(oda_result)

            # Convert to Claude StageResult
            result = StageResult(
                stage=ProtocolStage.A_SCAN,
                passed=oda_result.passed,
                timestamp=datetime.utcnow().isoformat(),
                evidence=self.evidence_tracker.export(),
                findings=[self._convert_finding(f) for f in oda_result.findings],
                message=oda_result.message,
            )

            await self.todo_manager.mark_stage_completed(
                ProtocolStage.A_SCAN, oda_result.passed
            )

            return result

        except Exception as e:
            await self.todo_manager.mark_stage_completed(ProtocolStage.A_SCAN, False)
            return StageResult(
                stage=ProtocolStage.A_SCAN,
                passed=False,
                timestamp=datetime.utcnow().isoformat(),
                evidence=self.evidence_tracker.export(),
                message=f"Stage A failed: {str(e)}",
                error=type(e).__name__,
            )

    async def execute_stage_b(self) -> StageResult:
        """Execute Stage B: TRACE through ODA protocol."""
        # Validate boundary
        validation = self.boundary_validator.validate_transition(
            from_stage=ProtocolStage.A_SCAN,
            to_stage=ProtocolStage.B_TRACE,
            evidence=self.evidence_tracker,
        )

        if not validation["valid"]:
            return StageResult(
                stage=ProtocolStage.B_TRACE,
                passed=False,
                timestamp=datetime.utcnow().isoformat(),
                evidence=self.evidence_tracker.export(),
                message=f"Boundary validation failed: {validation['errors']}",
                error="BoundaryValidationError",
            )

        await self.todo_manager.mark_stage_in_progress(ProtocolStage.B_TRACE)

        self._checkpoints.append(ProtocolCheckpoint.capture(
            stage=ProtocolStage.B_TRACE,
            evidence=self.evidence_tracker,
            todo_ids=self.todo_manager.get_stage_todos(),
        ))

        try:
            self._sync_evidence_to_oda()

            stage_a_result = self._stage_results.get(ProtocolStage.A_SCAN)
            if not stage_a_result:
                raise ValueError("Stage A must be executed before Stage B")

            oda_result = await self.protocol.stage_b(self.oda_context, stage_a_result)
            self._stage_results[ProtocolStage.B_TRACE] = oda_result

            self._sync_evidence_from_oda(oda_result)

            result = StageResult(
                stage=ProtocolStage.B_TRACE,
                passed=oda_result.passed,
                timestamp=datetime.utcnow().isoformat(),
                evidence=self.evidence_tracker.export(),
                findings=[self._convert_finding(f) for f in oda_result.findings],
                message=oda_result.message,
            )

            await self.todo_manager.mark_stage_completed(
                ProtocolStage.B_TRACE, oda_result.passed
            )

            return result

        except Exception as e:
            await self.todo_manager.mark_stage_completed(ProtocolStage.B_TRACE, False)
            return StageResult(
                stage=ProtocolStage.B_TRACE,
                passed=False,
                timestamp=datetime.utcnow().isoformat(),
                evidence=self.evidence_tracker.export(),
                message=f"Stage B failed: {str(e)}",
                error=type(e).__name__,
            )

    async def execute_stage_c(self) -> StageResult:
        """Execute Stage C: VERIFY through ODA protocol."""
        validation = self.boundary_validator.validate_transition(
            from_stage=ProtocolStage.B_TRACE,
            to_stage=ProtocolStage.C_VERIFY,
            evidence=self.evidence_tracker,
        )

        if not validation["valid"]:
            return StageResult(
                stage=ProtocolStage.C_VERIFY,
                passed=False,
                timestamp=datetime.utcnow().isoformat(),
                evidence=self.evidence_tracker.export(),
                message=f"Boundary validation failed: {validation['errors']}",
                error="BoundaryValidationError",
            )

        await self.todo_manager.mark_stage_in_progress(ProtocolStage.C_VERIFY)

        self._checkpoints.append(ProtocolCheckpoint.capture(
            stage=ProtocolStage.C_VERIFY,
            evidence=self.evidence_tracker,
            todo_ids=self.todo_manager.get_stage_todos(),
        ))

        try:
            self._sync_evidence_to_oda()

            stage_b_result = self._stage_results.get(ProtocolStage.B_TRACE)
            if not stage_b_result:
                raise ValueError("Stage B must be executed before Stage C")

            oda_result = await self.protocol.stage_c(self.oda_context, stage_b_result)
            self._stage_results[ProtocolStage.C_VERIFY] = oda_result

            self._sync_evidence_from_oda(oda_result)

            result = StageResult(
                stage=ProtocolStage.C_VERIFY,
                passed=oda_result.passed,
                timestamp=datetime.utcnow().isoformat(),
                evidence=self.evidence_tracker.export(),
                findings=[self._convert_finding(f) for f in oda_result.findings],
                message=oda_result.message,
            )

            await self.todo_manager.mark_stage_completed(
                ProtocolStage.C_VERIFY, oda_result.passed
            )

            return result

        except Exception as e:
            await self.todo_manager.mark_stage_completed(ProtocolStage.C_VERIFY, False)
            return StageResult(
                stage=ProtocolStage.C_VERIFY,
                passed=False,
                timestamp=datetime.utcnow().isoformat(),
                evidence=self.evidence_tracker.export(),
                message=f"Stage C failed: {str(e)}",
                error=type(e).__name__,
            )

    async def execute_all(self) -> List[StageResult]:
        """Execute all stages in sequence."""
        results = []

        # Stage A
        result_a = await self.execute_stage_a()
        results.append(result_a)
        if not result_a.passed:
            return results

        # Stage B
        result_b = await self.execute_stage_b()
        results.append(result_b)
        if not result_b.passed:
            return results

        # Stage C
        result_c = await self.execute_stage_c()
        results.append(result_c)

        return results

    def _convert_finding(self, finding: Finding) -> Dict[str, Any]:
        """Convert ODA Finding to dict."""
        return {
            "file_path": finding.file_path,
            "severity": finding.severity.value if hasattr(finding.severity, 'value') else str(finding.severity),
            "description": finding.description,
            "line_number": finding.line_number,
            "code_snippet": finding.code_snippet,
        }

    def get_last_checkpoint(self) -> Optional[ProtocolCheckpoint]:
        """Get the most recent checkpoint for rollback."""
        return self._checkpoints[-1] if self._checkpoints else None

    def get_all_checkpoints(self) -> List[ProtocolCheckpoint]:
        """Get all checkpoints."""
        return self._checkpoints.copy()

    def rollback_to_checkpoint(self, checkpoint: ProtocolCheckpoint) -> None:
        """
        Rollback state to a previous checkpoint.

        Note: This resets evidence and todo state but does not undo
        any file system changes made during execution.
        """
        # Restore evidence tracker state
        self.evidence_tracker = EvidenceTracker(
            session_id=self.session_id,
            actor_id=self.actor_id,
        )

        # Re-track files from snapshot
        for file_path in checkpoint.evidence_snapshot.get("files_viewed", []):
            self.evidence_tracker.track_file_read(file_path)

        # Clear ODA context
        self.oda_context.files_viewed.clear()
        self.oda_context.lines_referenced.clear()

        # Remove checkpoints after the rollback point
        while self._checkpoints and self._checkpoints[-1] != checkpoint:
            self._checkpoints.pop()


# Load default protocols
def load_protocols():
    """Load and register default ODA protocols."""
    try:
        from scripts.ontology.protocols.audit_protocol import AuditProtocol
        PROTOCOL_REGISTRY["audit"] = AuditProtocol
    except ImportError:
        pass

    try:
        from scripts.ontology.protocols.planning_protocol import PlanningProtocol
        PROTOCOL_REGISTRY["planning"] = PlanningProtocol
    except ImportError:
        pass

    try:
        from scripts.ontology.protocols.execution_protocol import ExecutionProtocol
        PROTOCOL_REGISTRY["execution"] = ExecutionProtocol
    except ImportError:
        pass


def get_protocol(name: str) -> Optional[Type[ThreeStageProtocol]]:
    """Get a registered protocol by name."""
    if not PROTOCOL_REGISTRY:
        load_protocols()
    return PROTOCOL_REGISTRY.get(name)


def list_protocols() -> List[str]:
    """List all registered protocol names."""
    if not PROTOCOL_REGISTRY:
        load_protocols()
    return list(PROTOCOL_REGISTRY.keys())


# Auto-load on import
load_protocols()
