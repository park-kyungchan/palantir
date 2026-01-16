"""
Claude Code Protocol Runner

Executes 3-Stage Protocols using Claude Code native tools (TodoWrite, Subagents).
Bridges ODA protocol framework with Claude Code CLI capabilities.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type

from scripts.claude.evidence_tracker import EvidenceTracker, AntiHallucinationError
from scripts.claude.todo_sync import TodoTaskSync, TodoStatus


logger = logging.getLogger(__name__)


class ProtocolStage(str, Enum):
    """3-Stage Protocol stages."""
    A_SCAN = "A_SCAN"
    B_TRACE = "B_TRACE"
    C_VERIFY = "C_VERIFY"


@dataclass
class StageConfig:
    """Configuration for a protocol stage."""
    name: str
    description: str
    min_files: int
    min_line_refs: int
    min_snippets: int
    todo_content: str
    todo_active_form: str


# Default stage configurations
STAGE_CONFIGS: Dict[ProtocolStage, StageConfig] = {
    ProtocolStage.A_SCAN: StageConfig(
        name="SCAN",
        description="Surface analysis - map the landscape",
        min_files=3,
        min_line_refs=0,
        min_snippets=0,
        todo_content="Stage A: SCAN (Surface Analysis)",
        todo_active_form="Stage A: SCAN 진행 중",
    ),
    ProtocolStage.B_TRACE: StageConfig(
        name="TRACE",
        description="Logic analysis - trace data flow and dependencies",
        min_files=5,
        min_line_refs=10,
        min_snippets=0,
        todo_content="Stage B: TRACE (Logic Analysis)",
        todo_active_form="Stage B: TRACE 진행 중",
    ),
    ProtocolStage.C_VERIFY: StageConfig(
        name="VERIFY",
        description="Quality gate - validate and approve",
        min_files=5,
        min_line_refs=15,
        min_snippets=3,
        todo_content="Stage C: VERIFY (Quality Gate)",
        todo_active_form="Stage C: VERIFY 진행 중",
    ),
}


@dataclass
class StageResult:
    """Result of executing a protocol stage."""
    stage: ProtocolStage
    passed: bool
    timestamp: str
    evidence: Dict[str, Any]
    findings: List[Dict[str, Any]] = field(default_factory=list)
    message: str = ""
    error: Optional[str] = None


@dataclass
class ProtocolResult:
    """Result of executing the full protocol."""
    protocol_name: str
    stages: List[StageResult]
    passed: bool
    started_at: str
    completed_at: str
    evidence: Dict[str, Any]

    @property
    def duration_seconds(self) -> float:
        """Calculate duration in seconds."""
        start = datetime.fromisoformat(self.started_at)
        end = datetime.fromisoformat(self.completed_at)
        return (end - start).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Export as dictionary."""
        return {
            "protocol_name": self.protocol_name,
            "passed": self.passed,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_seconds": self.duration_seconds,
            "stages": [
                {
                    "stage": s.stage.value,
                    "passed": s.passed,
                    "message": s.message,
                    "findings_count": len(s.findings),
                }
                for s in self.stages
            ],
            "evidence": self.evidence,
        }


class ClaudeProtocolRunner:
    """
    Runs 3-Stage Protocols with Claude Code integration.

    Features:
    - TodoWrite integration for stage tracking
    - Evidence collection with anti-hallucination validation
    - Subagent delegation support
    - Task synchronization with ODA
    - ODA Protocol adapter integration (optional)
    - Rollback support with checkpoints

    Usage:
        runner = ClaudeProtocolRunner(
            protocol_name="audit",
            target_path="scripts/ontology/",
        )

        # Register stage handlers
        runner.register_stage_handler(ProtocolStage.A_SCAN, scan_handler)
        runner.register_stage_handler(ProtocolStage.B_TRACE, trace_handler)
        runner.register_stage_handler(ProtocolStage.C_VERIFY, verify_handler)

        # Execute protocol
        result = await runner.execute()

        # Or use ODA protocol directly:
        runner = ClaudeProtocolRunner(
            protocol_name="audit",
            target_path="scripts/ontology/",
            use_oda_protocol=True,  # Uses registered ODA protocol
        )
        result = await runner.execute()

        # With rollback support:
        result = await runner.execute_with_rollback(max_retries=3)
    """

    def __init__(
        self,
        protocol_name: str,
        target_path: str,
        session_id: Optional[str] = None,
        actor_id: str = "claude_code_agent",
        use_oda_protocol: bool = True,
    ):
        self.protocol_name = protocol_name
        self.target_path = Path(target_path)
        self.session_id = session_id or f"{protocol_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.actor_id = actor_id
        self.use_oda_protocol = use_oda_protocol

        # Components
        self.evidence_tracker = EvidenceTracker(
            session_id=self.session_id,
            actor_id=actor_id,
        )
        self.todo_sync = TodoTaskSync()

        # ODA Protocol Adapter (lazy initialization)
        self._oda_adapter: Optional["ODAProtocolAdapter"] = None

        # Stage handlers
        self._stage_handlers: Dict[ProtocolStage, Callable] = {}

        # Results
        self._stage_results: List[StageResult] = []
        self._started_at: Optional[str] = None

    def _get_oda_adapter(self) -> Optional["ODAProtocolAdapter"]:
        """Get or initialize ODA protocol adapter."""
        if self._oda_adapter is not None:
            return self._oda_adapter

        if not self.use_oda_protocol:
            return None

        # Lazy import to avoid circular dependency
        from scripts.claude.protocol_adapter import (
            ODAProtocolAdapter,
            PROTOCOL_REGISTRY,
            load_protocols,
        )

        # Ensure protocols are loaded
        if not PROTOCOL_REGISTRY:
            load_protocols()

        # Check if protocol exists in registry
        protocol_cls = PROTOCOL_REGISTRY.get(self.protocol_name)
        if not protocol_cls:
            logger.debug(
                f"Protocol '{self.protocol_name}' not found in registry, "
                "falling back to handler-based execution"
            )
            return None

        # Create adapter
        protocol = protocol_cls()
        self._oda_adapter = ODAProtocolAdapter(
            protocol=protocol,
            target_path=str(self.target_path),
            session_id=self.session_id,
            actor_id=self.actor_id,
        )

        # Share evidence tracker
        self._oda_adapter.evidence_tracker = self.evidence_tracker

        return self._oda_adapter

    def register_stage_handler(
        self,
        stage: ProtocolStage,
        handler: Callable,
    ) -> None:
        """
        Register a handler function for a protocol stage.

        Args:
            stage: Protocol stage
            handler: Async function that executes the stage
                     Signature: async def handler(context: Dict) -> Dict[str, Any]
        """
        self._stage_handlers[stage] = handler

    async def execute(self) -> ProtocolResult:
        """
        Execute the full 3-Stage Protocol.

        When use_oda_protocol=True and the protocol exists in PROTOCOL_REGISTRY,
        uses ODAProtocolAdapter for execution. Otherwise falls back to
        handler-based execution.

        Returns:
            ProtocolResult with all stage results
        """
        self._started_at = datetime.utcnow().isoformat()

        # Try ODA adapter first
        adapter = self._get_oda_adapter()
        if adapter:
            return await self._execute_with_oda_adapter(adapter)

        # Fall back to handler-based execution
        return await self._execute_with_handlers()

    async def _execute_with_oda_adapter(
        self,
        adapter: "ODAProtocolAdapter",
    ) -> ProtocolResult:
        """Execute protocol using ODA adapter."""
        logger.info(
            f"Executing protocol '{self.protocol_name}' via ODA adapter"
        )

        # Execute all stages through adapter
        stage_results = await adapter.execute_all()
        self._stage_results = stage_results

        all_passed = all(r.passed for r in stage_results)
        completed_at = datetime.utcnow().isoformat()

        return ProtocolResult(
            protocol_name=self.protocol_name,
            stages=stage_results,
            passed=all_passed,
            started_at=self._started_at,
            completed_at=completed_at,
            evidence=self.evidence_tracker.export(),
        )

    async def _execute_with_handlers(self) -> ProtocolResult:
        """Execute protocol using registered handlers."""
        logger.info(
            f"Executing protocol '{self.protocol_name}' via handlers"
        )

        # Create initial todos for all stages
        todos = [
            {
                "content": config.todo_content,
                "status": "pending",
                "activeForm": config.todo_active_form,
            }
            for config in STAGE_CONFIGS.values()
        ]

        # Execute stages sequentially
        all_passed = True
        for stage in ProtocolStage:
            result = await self._execute_stage(stage)
            self._stage_results.append(result)

            if not result.passed:
                all_passed = False
                break  # Stop on first failure

        completed_at = datetime.utcnow().isoformat()

        return ProtocolResult(
            protocol_name=self.protocol_name,
            stages=self._stage_results,
            passed=all_passed,
            started_at=self._started_at,
            completed_at=completed_at,
            evidence=self.evidence_tracker.export(),
        )

    async def execute_with_rollback(
        self,
        max_retries: int = 3,
        strict_evidence: bool = True,
    ) -> ProtocolResult:
        """
        Execute protocol with rollback support on failure.

        Uses checkpoints to restore state between retries. When a stage fails,
        the adapter state is rolled back to the previous checkpoint and the
        stage is re-executed.

        Args:
            max_retries: Maximum retry attempts (default: 3)
            strict_evidence: If True, validate evidence at each stage

        Returns:
            ProtocolResult with final outcome

        Example:
            result = await runner.execute_with_rollback(max_retries=3)
            if not result.passed:
                print(f"Failed after {max_retries} attempts")
        """
        adapter = self._get_oda_adapter()

        for attempt in range(1, max_retries + 1):
            logger.info(
                f"[{self.protocol_name}] Rollback attempt {attempt}/{max_retries}"
            )

            # Reset state for new attempt
            self._stage_results = []
            self._started_at = datetime.utcnow().isoformat()

            if adapter:
                # Reset adapter state
                adapter._checkpoints.clear()
                adapter._stage_results.clear()
                adapter.evidence_tracker = EvidenceTracker(
                    session_id=f"{self.session_id}_attempt{attempt}",
                    actor_id=self.actor_id,
                )
                self.evidence_tracker = adapter.evidence_tracker

                result = await self._execute_with_oda_adapter(adapter)
            else:
                # Reset evidence tracker for handler-based execution
                self.evidence_tracker = EvidenceTracker(
                    session_id=f"{self.session_id}_attempt{attempt}",
                    actor_id=self.actor_id,
                )

                result = await self._execute_with_handlers()

            # Validate evidence if strict mode
            if strict_evidence and not result.passed:
                for stage_result in result.stages:
                    if stage_result.error:
                        logger.warning(
                            f"[{self.protocol_name}] Stage {stage_result.stage.value} "
                            f"failed: {stage_result.message}"
                        )

            if result.passed:
                logger.info(
                    f"[{self.protocol_name}] Completed on attempt {attempt}: PASSED"
                )
                return result

            if attempt < max_retries:
                logger.warning(
                    f"[{self.protocol_name}] Attempt {attempt} failed, "
                    f"rolling back and retrying..."
                )

                # Rollback to last successful checkpoint if using adapter
                if adapter:
                    checkpoint = adapter.get_last_checkpoint()
                    if checkpoint:
                        adapter.rollback_to_checkpoint(checkpoint)
            else:
                logger.error(
                    f"[{self.protocol_name}] Exhausted {max_retries} attempts"
                )

        return result

    async def _execute_stage(self, stage: ProtocolStage) -> StageResult:
        """Execute a single protocol stage."""
        config = STAGE_CONFIGS[stage]
        timestamp = datetime.utcnow().isoformat()

        try:
            # Get handler
            handler = self._stage_handlers.get(stage)

            if handler:
                # Execute custom handler
                context = {
                    "stage": stage,
                    "target_path": str(self.target_path),
                    "evidence_tracker": self.evidence_tracker,
                    "session_id": self.session_id,
                }
                handler_result = await handler(context)
                findings = handler_result.get("findings", [])
                message = handler_result.get("message", f"Stage {config.name} completed")
            else:
                # Default: just validate evidence
                findings = []
                message = f"Stage {config.name} completed (no handler)"

            # Validate evidence
            validation = self.evidence_tracker.validate(
                stage=stage.value,
                strict=False,
            )

            if not validation["valid"]:
                return StageResult(
                    stage=stage,
                    passed=False,
                    timestamp=timestamp,
                    evidence=self.evidence_tracker.export(),
                    findings=findings,
                    message=f"Evidence validation failed: {validation['errors']}",
                    error="AntiHallucinationError",
                )

            return StageResult(
                stage=stage,
                passed=True,
                timestamp=timestamp,
                evidence=self.evidence_tracker.export(),
                findings=findings,
                message=message,
            )

        except AntiHallucinationError as e:
            return StageResult(
                stage=stage,
                passed=False,
                timestamp=timestamp,
                evidence=self.evidence_tracker.export(),
                message=str(e),
                error="AntiHallucinationError",
            )
        except Exception as e:
            return StageResult(
                stage=stage,
                passed=False,
                timestamp=timestamp,
                evidence=self.evidence_tracker.export(),
                message=f"Stage failed: {str(e)}",
                error=type(e).__name__,
            )

    def generate_todowrite_payload(self) -> List[Dict[str, Any]]:
        """
        Generate TodoWrite payload reflecting current protocol state.

        Returns:
            List of todo items for TodoWrite tool
        """
        todos = []

        for stage in ProtocolStage:
            config = STAGE_CONFIGS[stage]

            # Find result for this stage
            stage_result = next(
                (r for r in self._stage_results if r.stage == stage),
                None
            )

            if stage_result:
                if stage_result.passed:
                    status = "completed"
                else:
                    status = "in_progress"  # Failed but attempted
            else:
                # Check if previous stage passed
                prev_stages = list(ProtocolStage)[:list(ProtocolStage).index(stage)]
                prev_passed = all(
                    any(r.stage == ps and r.passed for r in self._stage_results)
                    for ps in prev_stages
                )

                if prev_passed or not prev_stages:
                    status = "pending"
                else:
                    status = "pending"  # Blocked by previous

            todos.append({
                "content": config.todo_content,
                "status": status,
                "activeForm": config.todo_active_form,
            })

        return todos


# Convenience function for quick protocol execution
async def run_protocol(
    protocol_name: str,
    target_path: str,
    handlers: Optional[Dict[ProtocolStage, Callable]] = None,
    use_oda_protocol: bool = True,
    with_rollback: bool = False,
    max_retries: int = 3,
) -> ProtocolResult:
    """
    Quick way to run a protocol.

    Args:
        protocol_name: Name of the protocol (audit, plan, etc.)
        target_path: Path to analyze
        handlers: Optional stage handlers
        use_oda_protocol: If True, use ODA protocol adapter when available
        with_rollback: If True, use execute_with_rollback for retry support
        max_retries: Maximum retries when with_rollback=True

    Returns:
        ProtocolResult
    """
    runner = ClaudeProtocolRunner(
        protocol_name=protocol_name,
        target_path=target_path,
        use_oda_protocol=use_oda_protocol,
    )

    if handlers:
        for stage, handler in handlers.items():
            runner.register_stage_handler(stage, handler)

    if with_rollback:
        return await runner.execute_with_rollback(max_retries=max_retries)
    return await runner.execute()


# CLI interface
if __name__ == "__main__":
    import sys

    async def main():
        if len(sys.argv) < 3:
            print("Usage: python protocol_runner.py <protocol_name> <target_path>")
            print("Example: python protocol_runner.py audit scripts/ontology/")
            sys.exit(1)

        protocol_name = sys.argv[1]
        target_path = sys.argv[2]

        result = await run_protocol(protocol_name, target_path)
        print(json.dumps(result.to_dict(), indent=2))

    asyncio.run(main())
