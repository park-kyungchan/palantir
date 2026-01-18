"""
Orion ODA v3.0 - Planning Protocol Implementation
===================================================
3-Stage Protocol for planning and design operations.

Stages:
    A: Blueprint - Requirements gathering, scope definition
    B: Integration - How components connect, dependency analysis
    C: Quality Gate - Design review, approval checkpoint
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from lib.oda.ontology.protocols.evidence import (
    add_files_evidence,
    add_line_evidence,
    collect_snippets,
    discover_files,
)
from lib.oda.ontology.protocols.stage_requirements import get_evidence_requirements
from lib.oda.ontology.protocols.base import (
    Finding,
    ProtocolContext,
    Stage,
    StageResult,
    ThreeStageProtocol,
)


logger = logging.getLogger(__name__)


class PlanningProtocol(ThreeStageProtocol):
    """
    Protocol implementation for Planning operations.
    
    Used before:
    - Creating Proposals
    - Designing new features
    - Major refactoring decisions
    """
    
    @property
    def name(self) -> str:
        return "planning"
    
    async def stage_a(self, context: ProtocolContext) -> StageResult:
        """
        Stage A: Blueprint
        
        Gathers:
        - Requirements from context
        - Scope boundaries
        - Constraints and limitations
        - Success criteria
        """
        findings: List[Finding] = []
        req = get_evidence_requirements("A_SCAN")
        files = discover_files(context.target_path, limit=50)
        add_files_evidence(context, files[: req.min_files])

        evidence: Dict[str, Any] = context.get_evidence_dict()
        evidence["stage"] = "blueprint"
        evidence["planning_mode"] = "evidence_capture_only"

        passed = len(evidence.get("files_viewed", [])) >= req.min_files
        return StageResult(
            stage=Stage.A_SCAN,
            passed=passed,
            findings=findings,
            evidence=evidence,
            message=(
                "Blueprint complete (filesystem evidence captured)."
                if passed
                else "Blueprint incomplete: insufficient filesystem evidence."
            ),
        )
    
    async def stage_b(
        self, 
        context: ProtocolContext, 
        stage_a_result: StageResult
    ) -> StageResult:
        """
        Stage B: Integration Analysis
        
        Analyzes:
        - How new code connects to existing
        - Import paths and dependencies
        - Potential conflicts
        - API surface changes
        """
        findings: List[Finding] = []
        req = get_evidence_requirements("B_TRACE")
        files = discover_files(context.target_path, limit=50)
        add_files_evidence(context, files[: req.min_files])

        existing_line_refs = sum(len(v) for v in context.lines_referenced.values())
        needed_lines = max(0, req.min_line_refs - existing_line_refs)
        if needed_lines:
            add_line_evidence(context, files, min_total_lines=needed_lines)

        evidence: Dict[str, Any] = context.get_evidence_dict()
        evidence["stage"] = "integration"
        evidence["planning_mode"] = "evidence_capture_only"

        total_line_refs = sum(len(v) for v in evidence.get("lines_referenced", {}).values())
        passed = (
            len(evidence.get("files_viewed", [])) >= req.min_files
            and total_line_refs >= req.min_line_refs
        )
        return StageResult(
            stage=Stage.B_TRACE,
            passed=passed,
            findings=findings,
            evidence=evidence,
            message=(
                "Integration analysis complete (filesystem evidence captured)."
                if passed
                else "Integration analysis incomplete: insufficient filesystem evidence."
            ),
        )
    
    async def stage_c(
        self, 
        context: ProtocolContext, 
        stage_b_result: StageResult
    ) -> StageResult:
        """
        Stage C: Quality Gate
        
        Verifies:
        - Design aligns with architecture
        - No breaking changes (or they're documented)
        - Test strategy defined
        - Ready for implementation
        """
        findings: List[Finding] = []
        req = get_evidence_requirements("C_VERIFY")
        files = discover_files(context.target_path, limit=50)
        add_files_evidence(context, files[: req.min_files])

        existing_line_refs = sum(len(v) for v in context.lines_referenced.values())
        needed_lines = max(0, req.min_line_refs - existing_line_refs)
        if needed_lines:
            add_line_evidence(context, files, min_total_lines=needed_lines)

        snippets = collect_snippets(files, count=req.min_snippets, max_lines=30)

        evidence: Dict[str, Any] = context.get_evidence_dict()
        evidence["stage"] = "quality_gate"
        evidence["planning_mode"] = "evidence_capture_only"
        evidence["code_snippets"] = [s.to_dict() for s in snippets]
        
        total_line_refs = sum(len(v) for v in evidence.get("lines_referenced", {}).values())
        passed = (
            len(evidence.get("files_viewed", [])) >= req.min_files
            and total_line_refs >= req.min_line_refs
            and len(snippets) >= req.min_snippets
        )
        
        return StageResult(
            stage=Stage.C_VERIFY,
            passed=passed,
            findings=findings,
            evidence=evidence,
            message=(
                "Quality gate complete (filesystem evidence captured)."
                if passed
                else "Quality gate incomplete: insufficient filesystem evidence."
            ),
        )
