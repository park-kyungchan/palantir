"""
Orion ODA v3.0 - 3-Stage Protocol Base Classes
================================================
Core abstractions for the enforced protocol framework.

Architecture:
    ThreeStageProtocol (ABC)
        │
        ├── stage_a() → StageResult (SCAN)
        ├── stage_b() → StageResult (TRACE)  
        └── stage_c() → StageResult (VERIFY)
                │
                ▼
        ProtocolResult (PASS/FAIL with evidence)
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class Stage(str, Enum):
    """
    Protocol execution stages.
    
    Aligned with ANTIGRAVITY_ARCHITECT_V5.0:
    - Stage A: Surface Scan (Landscape)
    - Stage B: Logic Trace (Deep-Dive)
    - Stage C: Quality Gate (Verification)
    """
    A_SCAN = "stage_a_scan"
    B_TRACE = "stage_b_trace"
    C_VERIFY = "stage_c_verify"


class Severity(str, Enum):
    """Finding severity levels."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProtocolPolicy(str, Enum):
    """
    Enforcement policy for protocol compliance.
    
    - BLOCK: Cannot proceed without passing protocol
    - WARN: Logs warning but allows proceeding
    - SKIP: Protocol not required for this action
    """
    BLOCK = "block"
    WARN = "warn"
    SKIP = "skip"


class AntiHallucinationError(Exception):
    """
    Raised when a protocol stage passes without proper evidence.
    
    V6.0 Enhancement: Aligned with Palantir submissionCriteria pattern.
    Ensures all analysis is grounded in actual file system reads.
    
    Attributes:
        stage: The stage that failed evidence validation
        message: Human-readable error description
    """
    def __init__(self, stage: str, message: str = "Stage passed without evidence"):
        self.stage = stage
        self.message = message
        super().__init__(f"[{stage}] {message}")


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class Finding:
    """
    A single finding from a protocol stage.
    
    Attributes:
        file_path: Path to the file where finding was discovered
        line_number: Optional line number
        severity: Impact level
        description: Human-readable description
        code_snippet: Optional code evidence
    """
    file_path: str
    severity: Severity
    description: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "severity": self.severity.value,
            "description": self.description,
            "code_snippet": self.code_snippet,
        }


@dataclass
class StageResult:
    """
    Result of a single protocol stage execution.
    
    Anti-Hallucination Design:
        The `evidence` field MUST contain proof of actual analysis:
        - files_viewed: List of file paths actually read
        - lines_referenced: Dict mapping file to line numbers
        - code_snippets: Dict mapping file:line to code
    
    If evidence is empty, the stage should be considered invalid.
    """
    stage: Stage
    passed: bool
    findings: List[Finding] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    message: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self):
        # Enforce evidence requirement
        if self.passed and not self.evidence:
            logger.warning(
                f"Stage {self.stage.value} passed without evidence. "
                "This may indicate incomplete analysis."
            )
    
    @property
    def has_evidence(self) -> bool:
        """Check if stage has proper evidence."""
        return bool(self.evidence.get("files_viewed"))
    
    @property
    def finding_count_by_severity(self) -> Dict[str, int]:
        """Count findings by severity."""
        counts: Dict[str, int] = {}
        for f in self.findings:
            counts[f.severity.value] = counts.get(f.severity.value, 0) + 1
        return counts
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage.value,
            "passed": self.passed,
            "findings": [f.to_dict() for f in self.findings],
            "evidence": self.evidence,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "has_evidence": self.has_evidence,
        }
    
    def validate_evidence(self, strict: bool = False) -> bool:
        """
        Validate that stage has proper evidence.
        
        V6.0 Enhancement: Anti-Hallucination enforcement.
        Aligned with Palantir submissionCriteria pattern.
        
        Args:
            strict: If True, raise AntiHallucinationError on failure
        
        Returns:
            True if evidence is valid
        
        Raises:
            AntiHallucinationError: If strict=True and no evidence
        """
        if self.passed and not self.has_evidence:
            if strict:
                raise AntiHallucinationError(
                    stage=self.stage.value,
                    message="Stage passed without files_viewed evidence"
                )
            return False
        return True


@dataclass
class ProtocolResult:
    """
    Aggregated result of all protocol stages.
    
    Contains results from Stage A, B, and C with overall pass/fail status.
    """
    protocol_name: str
    stages: List[StageResult] = field(default_factory=list)
    passed: bool = False
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    
    @property
    def duration_seconds(self) -> float:
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0
    
    @property
    def total_findings(self) -> int:
        return sum(len(s.findings) for s in self.stages)
    
    @property
    def critical_findings(self) -> List[Finding]:
        findings = []
        for s in self.stages:
            findings.extend(f for f in s.findings if f.severity == Severity.CRITICAL)
        return findings
    
    def get_stage(self, stage: Stage) -> Optional[StageResult]:
        """Get result for a specific stage."""
        for s in self.stages:
            if s.stage == stage:
                return s
        return None
    
    @classmethod
    def failed(cls, protocol_name: str, failed_stage: StageResult) -> "ProtocolResult":
        """Create a failed result from a failed stage."""
        return cls(
            protocol_name=protocol_name,
            stages=[failed_stage],
            passed=False,
            completed_at=datetime.now(timezone.utc),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "protocol_name": self.protocol_name,
            "passed": self.passed,
            "stages": [s.to_dict() for s in self.stages],
            "total_findings": self.total_findings,
            "duration_seconds": self.duration_seconds,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class ProtocolContext(BaseModel):
    """
    Execution context for protocol stages.
    
    Carries shared state between stages:
    - target_path: Primary path being analyzed
    - actor_id: Who is running the protocol
    - metadata: Additional context data
    """
    target_path: str = Field(default="", description="Primary target for analysis")
    actor_id: str = Field(default="system", description="Who initiated the protocol")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Accumulated evidence across stages
    files_viewed: List[str] = Field(default_factory=list)
    lines_referenced: Dict[str, List[int]] = Field(default_factory=dict)
    
    def add_file_evidence(self, file_path: str, lines: Optional[List[int]] = None) -> None:
        """Track a file that was viewed during analysis."""
        if file_path not in self.files_viewed:
            self.files_viewed.append(file_path)
        if lines:
            existing = self.lines_referenced.get(file_path, [])
            self.lines_referenced[file_path] = list(set(existing + lines))
    
    def get_evidence_dict(self) -> Dict[str, Any]:
        """Get accumulated evidence for StageResult."""
        return {
            "files_viewed": self.files_viewed,
            "lines_referenced": self.lines_referenced,
            "target_path": self.target_path,
            "actor_id": self.actor_id,
        }


# =============================================================================
# ABSTRACT PROTOCOL
# =============================================================================

class ThreeStageProtocol(ABC):
    """
    Abstract Base Class for 3-Stage Protocol implementations.
    
    Usage:
        class AuditProtocol(ThreeStageProtocol):
            name = "audit"
            
            async def stage_a(self, context):
                # Surface scan logic
                return StageResult(stage=Stage.A_SCAN, passed=True, ...)
            
            async def stage_b(self, context, stage_a_result):
                # Logic trace
                return StageResult(stage=Stage.B_TRACE, passed=True, ...)
            
            async def stage_c(self, context, stage_b_result):
                # Quality audit
                return StageResult(stage=Stage.C_VERIFY, passed=True, ...)
    
    Enforcement:
        @require_protocol(AuditProtocol)
        class DeepAuditAction(ActionType):
            # Cannot execute without passing 3-stage protocol
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Protocol identifier (e.g., 'audit', 'planning', 'execution')."""
        pass
    
    @abstractmethod
    async def stage_a(self, context: ProtocolContext) -> StageResult:
        """
        Stage A: Surface Scan / Blueprint
        
        Purpose: High-level analysis of target
        - File structure
        - Key patterns
        - Requirements gathering
        
        Returns:
            StageResult with findings and evidence
        """
        pass
    
    @abstractmethod
    async def stage_b(
        self, 
        context: ProtocolContext, 
        stage_a_result: StageResult
    ) -> StageResult:
        """
        Stage B: Logic Trace / Integration Analysis
        
        Purpose: Deep-dive into specifics
        - Data flow analysis
        - Integration points
        - Dependency mapping
        
        Args:
            context: Shared protocol context
            stage_a_result: Results from Stage A to build upon
        
        Returns:
            StageResult with findings and evidence
        """
        pass
    
    @abstractmethod
    async def stage_c(
        self, 
        context: ProtocolContext, 
        stage_b_result: StageResult
    ) -> StageResult:
        """
        Stage C: Quality Gate / Verification
        
        Purpose: Final verification
        - Quality assessment
        - Validation checks
        - Approval gate
        
        Args:
            context: Shared protocol context
            stage_b_result: Results from Stage B to verify
        
        Returns:
            StageResult with pass/fail decision
        """
        pass
    
    async def execute(self, context: ProtocolContext) -> ProtocolResult:
        """
        Execute the full 3-stage protocol.
        
        Runs Stage A → B → C in sequence.
        Short-circuits on any stage failure.
        
        Args:
            context: Execution context with target and actor info
        
        Returns:
            ProtocolResult with all stage results and overall verdict
        """
        result = ProtocolResult(protocol_name=self.name)
        
        # Stage A: Surface Scan
        logger.info(f"[{self.name}] Starting Stage A: Surface Scan")
        stage_a_result = await self.stage_a(context)
        result.stages.append(stage_a_result)
        
        if not stage_a_result.passed:
            logger.warning(f"[{self.name}] Stage A failed: {stage_a_result.message}")
            result.completed_at = datetime.now(timezone.utc)
            return result
        
        # Stage B: Logic Trace
        logger.info(f"[{self.name}] Starting Stage B: Logic Trace")
        stage_b_result = await self.stage_b(context, stage_a_result)
        result.stages.append(stage_b_result)
        
        if not stage_b_result.passed:
            logger.warning(f"[{self.name}] Stage B failed: {stage_b_result.message}")
            result.completed_at = datetime.now(timezone.utc)
            return result
        
        # Stage C: Quality Gate
        logger.info(f"[{self.name}] Starting Stage C: Quality Gate")
        stage_c_result = await self.stage_c(context, stage_b_result)
        result.stages.append(stage_c_result)
        
        # Final verdict
        result.passed = stage_c_result.passed
        result.completed_at = datetime.now(timezone.utc)
        
        logger.info(
            f"[{self.name}] Protocol complete: "
            f"{'PASSED' if result.passed else 'FAILED'} "
            f"({result.total_findings} findings, {result.duration_seconds:.2f}s)"
        )
        
        return result
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
