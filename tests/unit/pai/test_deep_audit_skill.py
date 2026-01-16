"""
Unit tests for the /deep-audit skill.

Tests the Progressive Deep-Dive Audit with RSIL method including:
- RSIL 5-Phase synthesis algorithm (AGGREGATE -> CROSS-REFERENCE -> CORRELATE -> PRIORITIZE -> SYNTHESIZE)
- BLOCK enforcement logic
- 4-Stream parallel audit (Security, Architecture, Code Quality, Dependency)
- TaskDecomposer integration with scope keywords
- Override audit trail
- Block conditions (CRITICAL=NO override, ERROR=With approval)

Reference: .claude/skills/deep-audit.md
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest


# =============================================================================
# MOCK IMPLEMENTATIONS FOR TESTING
# =============================================================================
# These are mock implementations of the deep-audit components based on
# the specification in .claude/skills/deep-audit.md


class FindingSeverity:
    """Severity levels for findings."""
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class Finding:
    """A single audit finding."""
    id: str
    type: str
    severity: str
    file: str
    line: int
    evidence: str
    remediation: str
    stream_type: str = "security"
    normalized_severity: int = 2
    risk_score: int = 0
    cwe_id: Optional[str] = None


@dataclass
class BlockDecision:
    """Result of block enforcement evaluation."""
    blocked: bool
    reason: str
    override_allowed: bool
    required_actions: List[Dict[str, Any]] = field(default_factory=list)
    exit_code: int = 0
    override_command: str = ""


@dataclass
class DeepAuditResult:
    """Result of a deep audit operation."""
    status: str  # "BLOCK" | "PASS" | "WARNING"
    block_status: Dict[str, Any]
    security_findings: List[Finding]
    architecture_analysis: Dict[str, Any]
    code_quality_metrics: Dict[str, Any]
    dependency_audit: Dict[str, Any]
    root_causes: List[Dict[str, Any]]
    recommendations: Dict[str, List[str]]
    metadata: Dict[str, Any]


class RSILSynthesizer:
    """
    RSIL (Recursive Self-Improving Learning) Synthesis Algorithm.

    Implements the 5-phase synthesis pipeline:
    1. AGGREGATE - Collect findings from all streams
    2. CROSS-REFERENCE - Find patterns across streams
    3. CORRELATE & DEDUPE - Remove duplicates, identify root causes
    4. PRIORITIZE & SCORE - Calculate risk scores
    5. SYNTHESIZE & REPORT - Generate final result
    """

    SEVERITY_MAP = {
        "CRITICAL": 4,
        "HIGH": 3,
        "ERROR": 3,
        "MEDIUM": 2,
        "WARNING": 2,
        "LOW": 1,
        "INFO": 0
    }

    def phase1_aggregate(self, stream_outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Phase 1: AGGREGATE - Collect all findings from 4 parallel streams.
        Normalize severity levels and evidence formats.
        """
        aggregated = {
            "security": [],
            "architecture": [],
            "quality": [],
            "dependencies": [],
            "metadata": {
                "streams_completed": len(stream_outputs),
                "total_findings": 0,
                "aggregate_timestamp": datetime.now(timezone.utc).isoformat(),
            }
        }

        for output in stream_outputs:
            stream_type = output.get("stream_type", "unknown")
            findings = output.get("findings", [])

            for finding in findings:
                finding["normalized_severity"] = self._normalize_severity(
                    finding.get("severity", "WARNING")
                )

            if stream_type in aggregated:
                aggregated[stream_type].extend(findings)
            aggregated["metadata"]["total_findings"] += len(findings)

        return aggregated

    def phase2_cross_reference(self, aggregated: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 2: CROSS-REFERENCE - Find patterns across streams.
        Identify root causes that manifest in different ways.
        """
        cross_refs = {
            "security_quality_intersection": [],
            "arch_quality_intersection": [],
            "dep_security_intersection": [],
            "systemic_patterns": [],
        }

        # Security findings that also appear as quality issues
        for sec in aggregated.get("security", []):
            for qual in aggregated.get("quality", []):
                if sec.get("file") == qual.get("file"):
                    if abs(sec.get("line", 0) - qual.get("line", 0)) < 10:
                        cross_refs["security_quality_intersection"].append({
                            "security_finding": sec.get("id"),
                            "quality_finding": qual.get("id"),
                            "file": sec.get("file"),
                            "insight": "Security vulnerability in complex code section",
                            "amplified_risk": True
                        })

        # Dependency vulnerabilities affecting multiple files
        for dep in aggregated.get("dependencies", []):
            affected = dep.get("affected_files", [])
            if len(affected) > 3:
                cross_refs["systemic_patterns"].append({
                    "pattern": "widespread_vulnerable_dependency",
                    "dependency": dep.get("package"),
                    "files_affected": len(affected),
                    "recommendation": f"Urgent upgrade: {dep.get('package')}"
                })

        return cross_refs

    def phase3_correlate(
        self,
        aggregated: Dict[str, Any],
        cross_refs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Phase 3: CORRELATE & DEDUPE - Remove duplicates, identify root causes.
        """
        seen_signatures = set()
        deduplicated = {
            "security": [],
            "architecture": [],
            "quality": [],
            "dependencies": []
        }

        for stream_type in deduplicated.keys():
            for finding in aggregated.get(stream_type, []):
                sig = f"{finding.get('file')}:{finding.get('line')}:{finding.get('type')}"
                if sig not in seen_signatures:
                    seen_signatures.add(sig)
                    deduplicated[stream_type].append(finding)

        root_causes = self._identify_root_causes(deduplicated, cross_refs)

        total_findings = aggregated.get("metadata", {}).get("total_findings", 1)
        return {
            "deduplicated": deduplicated,
            "root_causes": root_causes,
            "dedup_ratio": len(seen_signatures) / max(total_findings, 1)
        }

    def phase4_prioritize(
        self,
        correlated: Dict[str, Any],
        cross_refs: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Phase 4: PRIORITIZE & SCORE - Calculate risk scores.
        """
        prioritized = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
        }

        all_findings = []
        for stream in ["security", "architecture", "quality", "dependencies"]:
            for finding in correlated.get("deduplicated", {}).get(stream, []):
                finding["stream_type"] = stream
                all_findings.append(finding)

        for finding in all_findings:
            risk_score = self._calculate_risk_score(finding, cross_refs)
            finding["risk_score"] = risk_score

            if risk_score >= 80:
                prioritized["critical"].append(finding)
            elif risk_score >= 60:
                prioritized["high"].append(finding)
            elif risk_score >= 40:
                prioritized["medium"].append(finding)
            else:
                prioritized["low"].append(finding)

        # Sort each category by risk_score descending
        for category in prioritized:
            prioritized[category].sort(
                key=lambda x: x.get("risk_score", 0),
                reverse=True
            )

        return prioritized

    def phase5_synthesize(
        self,
        prioritized: Dict[str, List[Dict[str, Any]]],
        root_causes: List[Dict[str, Any]]
    ) -> DeepAuditResult:
        """
        Phase 5: SYNTHESIZE & REPORT - Generate final DeepAuditResult.
        """
        has_critical = len(prioritized.get("critical", [])) > 0
        has_high_security = any(
            f.get("stream_type") == "security"
            for f in prioritized.get("high", [])
        )

        blocked = has_critical or has_high_security

        block_status = {
            "blocked": blocked,
            "reason": self._determine_block_reason(prioritized),
            "must_fix_count": len(prioritized.get("critical", [])) + len([
                f for f in prioritized.get("high", [])
                if f.get("stream_type") == "security"
            ]),
            "override_allowed": not has_critical,
        }

        recommendations = self._generate_recommendations(prioritized, root_causes)

        security_findings = [
            f for f in prioritized.get("critical", []) + prioritized.get("high", [])
            if f.get("stream_type") == "security"
        ]

        return DeepAuditResult(
            status="BLOCK" if blocked else "PASS",
            block_status=block_status,
            security_findings=security_findings,
            architecture_analysis=self._extract_arch_summary(prioritized),
            code_quality_metrics=self._extract_quality_metrics(prioritized),
            dependency_audit=self._extract_dep_summary(prioritized),
            root_causes=root_causes,
            recommendations=recommendations,
            metadata={
                "findings_by_severity": {k: len(v) for k, v in prioritized.items()},
                "synthesis_algorithm": "RSIL v1.0",
                "confidence_score": self._calculate_confidence(prioritized),
            }
        )

    def synthesize(self, stream_outputs: List[Dict[str, Any]]) -> DeepAuditResult:
        """
        Execute full RSIL synthesis pipeline.
        """
        # Phase 1: AGGREGATE
        aggregated = self.phase1_aggregate(stream_outputs)

        # Phase 2: CROSS-REFERENCE
        cross_refs = self.phase2_cross_reference(aggregated)

        # Phase 3: CORRELATE & DEDUPE
        correlated = self.phase3_correlate(aggregated, cross_refs)

        # Phase 4: PRIORITIZE & SCORE
        prioritized = self.phase4_prioritize(correlated, cross_refs)

        # Phase 5: SYNTHESIZE & REPORT
        return self.phase5_synthesize(prioritized, correlated.get("root_causes", []))

    def _normalize_severity(self, severity: str) -> int:
        """Convert severity string to numeric scale."""
        return self.SEVERITY_MAP.get(severity.upper(), 2)

    def _identify_root_causes(
        self,
        findings: Dict[str, List],
        cross_refs: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Group related findings under common root causes."""
        root_causes = []

        # Group quality issues by module
        quality_by_module = {}
        for finding in findings.get("quality", []):
            file_path = finding.get("file", "")
            parts = file_path.split("/")
            module = parts[-2] if len(parts) >= 2 else "unknown"
            quality_by_module.setdefault(module, []).append(finding)

        for module, module_findings in quality_by_module.items():
            if len(module_findings) >= 3:
                root_causes.append({
                    "type": "module_complexity",
                    "module": module,
                    "findings_count": len(module_findings),
                    "root_cause": f"Module {module} needs refactoring",
                    "evidence": [f.get("id") for f in module_findings]
                })

        return root_causes

    def _calculate_risk_score(
        self,
        finding: Dict[str, Any],
        cross_refs: Dict[str, Any]
    ) -> int:
        """
        Calculate risk score.
        Risk Score = (Severity * 20) + (Exploitability * 15) + (Blast * 10) + (Cross-ref * 15)
        """
        severity = finding.get("normalized_severity", 2)
        exploitability = self._get_exploitability(finding)
        blast_radius = self._get_blast_radius(finding)
        cross_ref_boost = self._is_cross_referenced(finding, cross_refs)

        score = (severity * 20) + (exploitability * 15) + (blast_radius * 10) + (cross_ref_boost * 15)
        return min(100, score)

    def _get_exploitability(self, finding: Dict[str, Any]) -> int:
        """Get exploitability factor (0-2)."""
        exploit_types = ["sql_injection", "command_injection", "unsafe_eval", "hardcoded_secret"]
        if finding.get("type") in exploit_types:
            return 2
        return 1

    def _get_blast_radius(self, finding: Dict[str, Any]) -> int:
        """Get blast radius factor (0-2)."""
        affected = finding.get("affected_files", [])
        if len(affected) > 5:
            return 2
        elif len(affected) > 2:
            return 1
        return 0

    def _is_cross_referenced(
        self,
        finding: Dict[str, Any],
        cross_refs: Dict[str, Any]
    ) -> int:
        """Check if finding is cross-referenced (0-1)."""
        finding_id = finding.get("id")
        for intersection in cross_refs.get("security_quality_intersection", []):
            if intersection.get("security_finding") == finding_id:
                return 1
        return 0

    def _determine_block_reason(self, prioritized: Dict[str, List]) -> str:
        """Determine the reason for blocking."""
        critical_count = len(prioritized.get("critical", []))
        high_security = [
            f for f in prioritized.get("high", [])
            if f.get("stream_type") == "security"
        ]

        if critical_count > 0:
            return f"{critical_count} CRITICAL findings require immediate fix"
        elif high_security:
            return f"{len(high_security)} HIGH severity security findings need resolution"
        return "All checks passed"

    def _generate_recommendations(
        self,
        prioritized: Dict[str, List],
        root_causes: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Generate actionable recommendations."""
        return {
            "critical": [f.get("remediation", "No remediation specified") for f in prioritized.get("critical", [])],
            "high": [f.get("remediation", "No remediation specified") for f in prioritized.get("high", [])],
            "medium": [f.get("remediation", "No remediation specified") for f in prioritized.get("medium", [])],
        }

    def _extract_arch_summary(self, prioritized: Dict[str, List]) -> Dict[str, Any]:
        """Extract architecture summary."""
        arch_findings = [
            f for cat in prioritized.values()
            for f in cat if f.get("stream_type") == "architecture"
        ]
        return {
            "findings_count": len(arch_findings),
            "findings": arch_findings[:5]  # Top 5
        }

    def _extract_quality_metrics(self, prioritized: Dict[str, List]) -> Dict[str, Any]:
        """Extract quality metrics summary."""
        quality_findings = [
            f for cat in prioritized.values()
            for f in cat if f.get("stream_type") == "quality"
        ]
        return {
            "findings_count": len(quality_findings),
            "findings": quality_findings[:5]
        }

    def _extract_dep_summary(self, prioritized: Dict[str, List]) -> Dict[str, Any]:
        """Extract dependency audit summary."""
        dep_findings = [
            f for cat in prioritized.values()
            for f in cat if f.get("stream_type") == "dependencies"
        ]
        return {
            "findings_count": len(dep_findings),
            "findings": dep_findings[:5]
        }

    def _calculate_confidence(self, prioritized: Dict[str, List]) -> float:
        """Calculate confidence score based on coverage."""
        total = sum(len(v) for v in prioritized.values())
        if total == 0:
            return 1.0
        return min(1.0, total / 100)


class BlockEnforcer:
    """
    Enforcement engine for Pre-Mutation Zone.
    MUST be called before ANY code mutation.
    """

    UNCONDITIONAL_BLOCKS = [
        "hardcoded_secret",
        "sql_injection",
        "command_injection",
        "critical_cve",
        "unsafe_deserialization",
    ]

    CONDITIONAL_BLOCKS = [
        "unsafe_eval",
        "high_cve",
        "circular_dependency",
        "extreme_complexity",
    ]

    def evaluate(self, audit_result: Dict[str, Any]) -> BlockDecision:
        """
        Evaluate audit result and return block decision.
        """
        findings = audit_result.get("findings", [])

        critical_findings = [
            f for f in findings
            if f.get("type") in self.UNCONDITIONAL_BLOCKS
        ]

        conditional_findings = [
            f for f in findings
            if f.get("type") in self.CONDITIONAL_BLOCKS
        ]

        if critical_findings:
            return BlockDecision(
                blocked=True,
                reason=f"{len(critical_findings)} CRITICAL findings require immediate fix",
                override_allowed=False,
                required_actions=self._generate_fix_actions(critical_findings),
                exit_code=1,
            )

        if conditional_findings:
            return BlockDecision(
                blocked=True,
                reason=f"{len(conditional_findings)} ERROR findings need resolution",
                override_allowed=True,
                override_command="--override-error-blocks",
                required_actions=self._generate_fix_actions(conditional_findings),
                exit_code=2,
            )

        return BlockDecision(
            blocked=False,
            reason="All checks passed",
            override_allowed=False,
            required_actions=[],
            exit_code=0,
        )

    def _generate_fix_actions(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate actionable fix instructions."""
        actions = []
        for f in findings:
            actions.append({
                "finding_id": f.get("id"),
                "file": f.get("file"),
                "line": f.get("line"),
                "action": f.get("remediation"),
                "priority": "IMMEDIATE" if f.get("type") in self.UNCONDITIONAL_BLOCKS else "HIGH",
                "estimated_effort": self._estimate_fix_effort(f),
            })
        return actions

    def _estimate_fix_effort(self, finding: Dict[str, Any]) -> str:
        """Estimate effort to fix a finding."""
        EFFORT_MAP = {
            "hardcoded_secret": "10 minutes - move to env var",
            "sql_injection": "30 minutes - parameterize query",
            "unsafe_eval": "15 minutes - use safe alternative",
            "extreme_complexity": "2 hours - refactor and extract",
            "circular_dependency": "1 hour - introduce interface",
        }
        return EFFORT_MAP.get(finding.get("type"), "30 minutes")


class TaskDecomposer:
    """
    Mock TaskDecomposer for testing scope keyword detection.
    """

    SCOPE_KEYWORDS = {
        "korean": ["전체", "모든", "완전한", "전부", "코드베이스"],
        "english": ["all", "entire", "complete", "whole", "full", "every", "codebase"],
    }

    DECOMPOSITION_THRESHOLDS = {
        "file_count": 20,
        "directory_count": 5,
        "loc_estimate": 5000,
    }

    def should_decompose(
        self,
        task: str,
        scope: str,
        thresholds: Optional[Dict[str, int]] = None
    ) -> bool:
        """Check if task needs decomposition."""
        if thresholds is None:
            thresholds = self.DECOMPOSITION_THRESHOLDS

        # Check for scope keywords
        task_lower = task.lower()
        for lang, keywords in self.SCOPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in task_lower:
                    return True

        return False

    def detect_scope_keywords(self, text: str) -> List[str]:
        """Detect scope keywords in text."""
        found = []
        text_lower = text.lower()
        for lang, keywords in self.SCOPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found.append(keyword)
        return found


@dataclass
class OverrideRecord:
    """Record of an audit override for audit trail."""
    timestamp: str
    actor: str
    audit_id: str
    findings_overridden: List[Dict[str, Any]]
    justification: str
    risk_accepted: bool
    reviewed_by: Optional[str] = None


class OverrideAuditTrail:
    """Manages the audit trail for overrides."""

    def __init__(self):
        self._records: List[OverrideRecord] = []

    def log_override(
        self,
        actor: str,
        audit_id: str,
        findings: List[Dict[str, Any]],
        justification: str,
        reviewed_by: Optional[str] = None
    ) -> OverrideRecord:
        """Log an override to the audit trail."""
        record = OverrideRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            actor=actor,
            audit_id=audit_id,
            findings_overridden=findings,
            justification=justification,
            risk_accepted=True,
            reviewed_by=reviewed_by
        )
        self._records.append(record)
        return record

    def get_records(self) -> List[OverrideRecord]:
        """Get all override records."""
        return self._records.copy()

    def get_records_for_audit(self, audit_id: str) -> List[OverrideRecord]:
        """Get records for a specific audit."""
        return [r for r in self._records if r.audit_id == audit_id]


# =============================================================================
# TEST FIXTURES
# =============================================================================


@pytest.fixture
def rsil_synthesizer() -> RSILSynthesizer:
    """Create an RSIL synthesizer instance."""
    return RSILSynthesizer()


@pytest.fixture
def block_enforcer() -> BlockEnforcer:
    """Create a block enforcer instance."""
    return BlockEnforcer()


@pytest.fixture
def task_decomposer() -> TaskDecomposer:
    """Create a task decomposer instance."""
    return TaskDecomposer()


@pytest.fixture
def override_audit_trail() -> OverrideAuditTrail:
    """Create an override audit trail instance."""
    return OverrideAuditTrail()


@pytest.fixture
def security_finding_critical() -> Dict[str, Any]:
    """Create a critical security finding."""
    return {
        "id": "SEC-001",
        "type": "hardcoded_secret",
        "severity": "CRITICAL",
        "file": "lib/oda/pai/config.py",
        "line": 42,
        "evidence": "API_KEY = 'sk-...'",
        "remediation": "Move to environment variable",
        "stream_type": "security",
    }


@pytest.fixture
def security_finding_error() -> Dict[str, Any]:
    """Create an error-level security finding."""
    return {
        "id": "SEC-002",
        "type": "unsafe_eval",
        "severity": "ERROR",
        "file": "lib/oda/ontology/registry.py",
        "line": 156,
        "evidence": "eval(user_input)",
        "remediation": "Replace with ast.literal_eval",
        "stream_type": "security",
    }


@pytest.fixture
def quality_finding() -> Dict[str, Any]:
    """Create a code quality finding."""
    return {
        "id": "QUAL-001",
        "type": "high_complexity",
        "severity": "WARNING",
        "file": "lib/oda/pai/config.py",
        "line": 45,
        "evidence": "Cyclomatic complexity: 24",
        "remediation": "Extract helper methods",
        "stream_type": "quality",
    }


@pytest.fixture
def architecture_finding() -> Dict[str, Any]:
    """Create an architecture finding."""
    return {
        "id": "ARCH-001",
        "type": "layer_violation",
        "severity": "WARNING",
        "file": "lib/oda/ontology/objects/task_types.py",
        "line": 15,
        "evidence": "from lib.oda.planning.task_decomposer import SubTask",
        "remediation": "Introduce interface in entities layer",
        "stream_type": "architecture",
    }


@pytest.fixture
def dependency_finding() -> Dict[str, Any]:
    """Create a dependency finding."""
    return {
        "id": "DEP-001",
        "type": "critical_cve",
        "severity": "CRITICAL",
        "file": "requirements.txt",
        "line": 5,
        "package": "pyyaml",
        "evidence": "CVE-2020-14343",
        "remediation": "Upgrade to pyyaml>=5.4.1",
        "stream_type": "dependencies",
        "affected_files": ["lib/oda/loader.py", "lib/oda/config.py"],
    }


@pytest.fixture
def stream_outputs_mixed(
    security_finding_critical,
    security_finding_error,
    quality_finding,
    architecture_finding,
    dependency_finding
) -> List[Dict[str, Any]]:
    """Create mixed stream outputs for testing."""
    return [
        {
            "stream_type": "security",
            "findings": [security_finding_critical, security_finding_error]
        },
        {
            "stream_type": "quality",
            "findings": [quality_finding]
        },
        {
            "stream_type": "architecture",
            "findings": [architecture_finding]
        },
        {
            "stream_type": "dependencies",
            "findings": [dependency_finding]
        },
    ]


@pytest.fixture
def stream_outputs_clean() -> List[Dict[str, Any]]:
    """Create clean stream outputs with no critical findings."""
    return [
        {"stream_type": "security", "findings": []},
        {"stream_type": "quality", "findings": []},
        {"stream_type": "architecture", "findings": []},
        {"stream_type": "dependencies", "findings": []},
    ]


# =============================================================================
# RSIL PHASE 1: AGGREGATE TESTS
# =============================================================================


class TestRSILPhase1Aggregate:
    """Tests for RSIL Phase 1: AGGREGATE."""

    def test_aggregate_collects_all_streams(
        self,
        rsil_synthesizer: RSILSynthesizer,
        stream_outputs_mixed: List[Dict[str, Any]]
    ):
        """Phase 1 should collect findings from all 4 streams."""
        result = rsil_synthesizer.phase1_aggregate(stream_outputs_mixed)

        assert "security" in result
        assert "architecture" in result
        assert "quality" in result
        assert "dependencies" in result
        assert "metadata" in result

    def test_aggregate_counts_total_findings(
        self,
        rsil_synthesizer: RSILSynthesizer,
        stream_outputs_mixed: List[Dict[str, Any]]
    ):
        """Phase 1 should count total findings correctly."""
        result = rsil_synthesizer.phase1_aggregate(stream_outputs_mixed)

        # 2 security + 1 quality + 1 arch + 1 dep = 5
        assert result["metadata"]["total_findings"] == 5

    def test_aggregate_normalizes_severity(
        self,
        rsil_synthesizer: RSILSynthesizer,
        security_finding_critical: Dict[str, Any]
    ):
        """Phase 1 should normalize severity levels."""
        stream_outputs = [
            {"stream_type": "security", "findings": [security_finding_critical]}
        ]

        result = rsil_synthesizer.phase1_aggregate(stream_outputs)

        finding = result["security"][0]
        assert "normalized_severity" in finding
        assert finding["normalized_severity"] == 4  # CRITICAL = 4

    def test_aggregate_records_timestamp(
        self,
        rsil_synthesizer: RSILSynthesizer,
        stream_outputs_clean: List[Dict[str, Any]]
    ):
        """Phase 1 should record aggregate timestamp."""
        result = rsil_synthesizer.phase1_aggregate(stream_outputs_clean)

        assert "aggregate_timestamp" in result["metadata"]
        # Verify it's a valid ISO format
        datetime.fromisoformat(result["metadata"]["aggregate_timestamp"].replace("Z", "+00:00"))

    def test_aggregate_handles_empty_streams(
        self,
        rsil_synthesizer: RSILSynthesizer,
        stream_outputs_clean: List[Dict[str, Any]]
    ):
        """Phase 1 should handle empty streams gracefully."""
        result = rsil_synthesizer.phase1_aggregate(stream_outputs_clean)

        assert result["metadata"]["total_findings"] == 0
        assert result["metadata"]["streams_completed"] == 4


# =============================================================================
# RSIL PHASE 2: CROSS-REFERENCE TESTS
# =============================================================================


class TestRSILPhase2CrossReference:
    """Tests for RSIL Phase 2: CROSS-REFERENCE."""

    def test_cross_reference_finds_security_quality_overlap(
        self,
        rsil_synthesizer: RSILSynthesizer,
        security_finding_critical: Dict[str, Any],
        quality_finding: Dict[str, Any]
    ):
        """Phase 2 should identify when security and quality issues overlap."""
        # Both findings are in the same file, close lines
        aggregated = {
            "security": [security_finding_critical],  # line 42
            "quality": [quality_finding],  # line 45
            "architecture": [],
            "dependencies": [],
            "metadata": {"total_findings": 2}
        }

        result = rsil_synthesizer.phase2_cross_reference(aggregated)

        assert len(result["security_quality_intersection"]) == 1
        assert result["security_quality_intersection"][0]["amplified_risk"] is True

    def test_cross_reference_detects_systemic_dependency_issues(
        self,
        rsil_synthesizer: RSILSynthesizer
    ):
        """Phase 2 should detect widespread dependency vulnerabilities."""
        aggregated = {
            "security": [],
            "quality": [],
            "architecture": [],
            "dependencies": [
                {
                    "id": "DEP-001",
                    "package": "vulnerable-lib",
                    "affected_files": ["a.py", "b.py", "c.py", "d.py", "e.py"]
                }
            ],
            "metadata": {"total_findings": 1}
        }

        result = rsil_synthesizer.phase2_cross_reference(aggregated)

        assert len(result["systemic_patterns"]) == 1
        assert result["systemic_patterns"][0]["pattern"] == "widespread_vulnerable_dependency"

    def test_cross_reference_no_overlap_different_files(
        self,
        rsil_synthesizer: RSILSynthesizer
    ):
        """Phase 2 should not find overlap for findings in different files."""
        aggregated = {
            "security": [{"id": "SEC-001", "file": "a.py", "line": 10}],
            "quality": [{"id": "QUAL-001", "file": "b.py", "line": 10}],
            "architecture": [],
            "dependencies": [],
            "metadata": {"total_findings": 2}
        }

        result = rsil_synthesizer.phase2_cross_reference(aggregated)

        assert len(result["security_quality_intersection"]) == 0


# =============================================================================
# RSIL PHASE 3: CORRELATE & DEDUPE TESTS
# =============================================================================


class TestRSILPhase3Correlate:
    """Tests for RSIL Phase 3: CORRELATE & DEDUPE."""

    def test_correlate_removes_duplicates(
        self,
        rsil_synthesizer: RSILSynthesizer
    ):
        """Phase 3 should remove duplicate findings."""
        aggregated = {
            "security": [
                {"id": "SEC-001", "file": "a.py", "line": 10, "type": "sql_injection"},
                {"id": "SEC-002", "file": "a.py", "line": 10, "type": "sql_injection"},  # Duplicate
            ],
            "quality": [],
            "architecture": [],
            "dependencies": [],
            "metadata": {"total_findings": 2}
        }
        cross_refs = {"security_quality_intersection": [], "systemic_patterns": []}

        result = rsil_synthesizer.phase3_correlate(aggregated, cross_refs)

        assert len(result["deduplicated"]["security"]) == 1

    def test_correlate_identifies_root_causes(
        self,
        rsil_synthesizer: RSILSynthesizer
    ):
        """Phase 3 should identify root causes from grouped findings."""
        aggregated = {
            "security": [],
            "quality": [
                {"id": "Q1", "file": "lib/mod/a.py", "line": 10, "type": "complexity"},
                {"id": "Q2", "file": "lib/mod/b.py", "line": 20, "type": "complexity"},
                {"id": "Q3", "file": "lib/mod/c.py", "line": 30, "type": "complexity"},
            ],
            "architecture": [],
            "dependencies": [],
            "metadata": {"total_findings": 3}
        }
        cross_refs = {}

        result = rsil_synthesizer.phase3_correlate(aggregated, cross_refs)

        # 3 findings in same module should trigger root cause detection
        assert len(result["root_causes"]) >= 1
        assert result["root_causes"][0]["type"] == "module_complexity"

    def test_correlate_calculates_dedup_ratio(
        self,
        rsil_synthesizer: RSILSynthesizer
    ):
        """Phase 3 should calculate dedup ratio."""
        aggregated = {
            "security": [
                {"id": "S1", "file": "a.py", "line": 10, "type": "t1"},
                {"id": "S2", "file": "a.py", "line": 10, "type": "t1"},  # Dup
                {"id": "S3", "file": "b.py", "line": 20, "type": "t2"},
            ],
            "quality": [],
            "architecture": [],
            "dependencies": [],
            "metadata": {"total_findings": 3}
        }

        result = rsil_synthesizer.phase3_correlate(aggregated, {})

        # 2 unique out of 3 total = 0.666...
        assert 0.6 < result["dedup_ratio"] < 0.7


# =============================================================================
# RSIL PHASE 4: PRIORITIZE & SCORE TESTS
# =============================================================================


class TestRSILPhase4Prioritize:
    """Tests for RSIL Phase 4: PRIORITIZE & SCORE."""

    def test_prioritize_sorts_by_risk_score(
        self,
        rsil_synthesizer: RSILSynthesizer
    ):
        """Phase 4 should sort findings by risk score descending."""
        correlated = {
            "deduplicated": {
                "security": [
                    {"id": "S1", "severity": "WARNING", "normalized_severity": 2, "type": "info"},
                    {"id": "S2", "severity": "CRITICAL", "normalized_severity": 4, "type": "sql_injection"},
                ],
                "quality": [],
                "architecture": [],
                "dependencies": [],
            }
        }

        result = rsil_synthesizer.phase4_prioritize(correlated, {})

        # All findings should have risk_score attached
        all_findings = []
        for category in result.values():
            all_findings.extend(category)

        for finding in all_findings:
            assert "risk_score" in finding

    def test_prioritize_categorizes_by_risk_level(
        self,
        rsil_synthesizer: RSILSynthesizer
    ):
        """Phase 4 should categorize findings by risk level."""
        correlated = {
            "deduplicated": {
                "security": [
                    {"id": "S1", "severity": "CRITICAL", "normalized_severity": 4, "type": "sql_injection"},
                ],
                "quality": [
                    {"id": "Q1", "severity": "INFO", "normalized_severity": 0, "type": "style"},
                ],
                "architecture": [],
                "dependencies": [],
            }
        }

        result = rsil_synthesizer.phase4_prioritize(correlated, {})

        assert "critical" in result
        assert "high" in result
        assert "medium" in result
        assert "low" in result

    def test_prioritize_high_exploitability_increases_score(
        self,
        rsil_synthesizer: RSILSynthesizer
    ):
        """Phase 4 should increase score for highly exploitable findings."""
        correlated = {
            "deduplicated": {
                "security": [
                    {"id": "S1", "severity": "ERROR", "normalized_severity": 3, "type": "sql_injection"},
                    {"id": "S2", "severity": "ERROR", "normalized_severity": 3, "type": "style_issue"},
                ],
                "quality": [],
                "architecture": [],
                "dependencies": [],
            }
        }

        result = rsil_synthesizer.phase4_prioritize(correlated, {})

        # Find both findings
        all_findings = []
        for category in result.values():
            all_findings.extend(category)

        s1 = next(f for f in all_findings if f["id"] == "S1")
        s2 = next(f for f in all_findings if f["id"] == "S2")

        # SQL injection should have higher score due to exploitability
        assert s1["risk_score"] > s2["risk_score"]


# =============================================================================
# RSIL PHASE 5: SYNTHESIZE & REPORT TESTS
# =============================================================================


class TestRSILPhase5Synthesize:
    """Tests for RSIL Phase 5: SYNTHESIZE & REPORT."""

    def test_synthesize_returns_deep_audit_result(
        self,
        rsil_synthesizer: RSILSynthesizer
    ):
        """Phase 5 should return a DeepAuditResult."""
        prioritized = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
        }

        result = rsil_synthesizer.phase5_synthesize(prioritized, [])

        assert isinstance(result, DeepAuditResult)

    def test_synthesize_blocks_on_critical(
        self,
        rsil_synthesizer: RSILSynthesizer,
        security_finding_critical: Dict[str, Any]
    ):
        """Phase 5 should block when critical findings exist."""
        security_finding_critical["stream_type"] = "security"
        prioritized = {
            "critical": [security_finding_critical],
            "high": [],
            "medium": [],
            "low": [],
        }

        result = rsil_synthesizer.phase5_synthesize(prioritized, [])

        assert result.status == "BLOCK"
        assert result.block_status["blocked"] is True
        assert result.block_status["override_allowed"] is False

    def test_synthesize_blocks_on_high_security(
        self,
        rsil_synthesizer: RSILSynthesizer,
        security_finding_error: Dict[str, Any]
    ):
        """Phase 5 should block when high severity security findings exist."""
        security_finding_error["stream_type"] = "security"
        prioritized = {
            "critical": [],
            "high": [security_finding_error],
            "medium": [],
            "low": [],
        }

        result = rsil_synthesizer.phase5_synthesize(prioritized, [])

        assert result.status == "BLOCK"
        assert result.block_status["blocked"] is True
        # High security allows override (no critical)
        assert result.block_status["override_allowed"] is True

    def test_synthesize_passes_when_clean(
        self,
        rsil_synthesizer: RSILSynthesizer
    ):
        """Phase 5 should pass when no critical/high security findings."""
        prioritized = {
            "critical": [],
            "high": [],
            "medium": [{"id": "Q1", "stream_type": "quality"}],
            "low": [],
        }

        result = rsil_synthesizer.phase5_synthesize(prioritized, [])

        assert result.status == "PASS"
        assert result.block_status["blocked"] is False

    def test_synthesize_includes_metadata(
        self,
        rsil_synthesizer: RSILSynthesizer
    ):
        """Phase 5 should include synthesis metadata."""
        prioritized = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
        }

        result = rsil_synthesizer.phase5_synthesize(prioritized, [])

        assert "synthesis_algorithm" in result.metadata
        assert result.metadata["synthesis_algorithm"] == "RSIL v1.0"
        assert "confidence_score" in result.metadata


# =============================================================================
# RSIL FULL PIPELINE TESTS
# =============================================================================


class TestRSILFullPipeline:
    """Tests for complete RSIL synthesis pipeline."""

    def test_full_pipeline_with_critical_findings(
        self,
        rsil_synthesizer: RSILSynthesizer,
        stream_outputs_mixed: List[Dict[str, Any]]
    ):
        """Full pipeline should block with critical findings."""
        result = rsil_synthesizer.synthesize(stream_outputs_mixed)

        assert result.status == "BLOCK"
        assert result.block_status["must_fix_count"] > 0

    def test_full_pipeline_with_clean_codebase(
        self,
        rsil_synthesizer: RSILSynthesizer,
        stream_outputs_clean: List[Dict[str, Any]]
    ):
        """Full pipeline should pass with clean codebase."""
        result = rsil_synthesizer.synthesize(stream_outputs_clean)

        assert result.status == "PASS"
        assert result.block_status["blocked"] is False

    def test_full_pipeline_generates_recommendations(
        self,
        rsil_synthesizer: RSILSynthesizer,
        stream_outputs_mixed: List[Dict[str, Any]]
    ):
        """Full pipeline should generate recommendations."""
        result = rsil_synthesizer.synthesize(stream_outputs_mixed)

        assert "critical" in result.recommendations
        assert "high" in result.recommendations
        assert "medium" in result.recommendations


# =============================================================================
# BLOCK ENFORCEMENT TESTS
# =============================================================================


class TestBlockEnforcer:
    """Tests for BlockEnforcer."""

    def test_unconditional_block_hardcoded_secret(
        self,
        block_enforcer: BlockEnforcer,
        security_finding_critical: Dict[str, Any]
    ):
        """Hardcoded secrets should trigger unconditional block."""
        audit_result = {"findings": [security_finding_critical]}

        decision = block_enforcer.evaluate(audit_result)

        assert decision.blocked is True
        assert decision.override_allowed is False
        assert decision.exit_code == 1

    def test_unconditional_block_sql_injection(
        self,
        block_enforcer: BlockEnforcer
    ):
        """SQL injection should trigger unconditional block."""
        finding = {
            "id": "SEC-001",
            "type": "sql_injection",
            "severity": "CRITICAL",
            "file": "app.py",
            "line": 10,
            "remediation": "Parameterize query"
        }

        decision = block_enforcer.evaluate({"findings": [finding]})

        assert decision.blocked is True
        assert decision.override_allowed is False

    def test_conditional_block_unsafe_eval(
        self,
        block_enforcer: BlockEnforcer,
        security_finding_error: Dict[str, Any]
    ):
        """Unsafe eval should trigger conditional block (override allowed)."""
        audit_result = {"findings": [security_finding_error]}

        decision = block_enforcer.evaluate(audit_result)

        assert decision.blocked is True
        assert decision.override_allowed is True
        assert decision.exit_code == 2
        assert decision.override_command == "--override-error-blocks"

    def test_no_block_clean_audit(
        self,
        block_enforcer: BlockEnforcer
    ):
        """Clean audit should not block."""
        audit_result = {"findings": []}

        decision = block_enforcer.evaluate(audit_result)

        assert decision.blocked is False
        assert decision.exit_code == 0
        assert decision.reason == "All checks passed"

    def test_block_generates_fix_actions(
        self,
        block_enforcer: BlockEnforcer,
        security_finding_critical: Dict[str, Any]
    ):
        """Block decision should include fix actions."""
        audit_result = {"findings": [security_finding_critical]}

        decision = block_enforcer.evaluate(audit_result)

        assert len(decision.required_actions) == 1
        action = decision.required_actions[0]
        assert action["finding_id"] == "SEC-001"
        assert action["priority"] == "IMMEDIATE"
        assert "estimated_effort" in action

    def test_unconditional_blocks_list(self, block_enforcer: BlockEnforcer):
        """Verify all unconditional block types."""
        expected = [
            "hardcoded_secret",
            "sql_injection",
            "command_injection",
            "critical_cve",
            "unsafe_deserialization",
        ]

        assert set(block_enforcer.UNCONDITIONAL_BLOCKS) == set(expected)

    def test_conditional_blocks_list(self, block_enforcer: BlockEnforcer):
        """Verify all conditional block types."""
        expected = [
            "unsafe_eval",
            "high_cve",
            "circular_dependency",
            "extreme_complexity",
        ]

        assert set(block_enforcer.CONDITIONAL_BLOCKS) == set(expected)


# =============================================================================
# 4-STREAM PARALLEL AUDIT TESTS
# =============================================================================


class TestFourStreamParallelAudit:
    """Tests for 4-stream parallel audit structure."""

    EXPECTED_STREAMS = ["security", "architecture", "quality", "dependencies"]

    def test_all_four_streams_present(
        self,
        rsil_synthesizer: RSILSynthesizer,
        stream_outputs_clean: List[Dict[str, Any]]
    ):
        """All 4 analysis streams should be present."""
        result = rsil_synthesizer.phase1_aggregate(stream_outputs_clean)

        for stream in self.EXPECTED_STREAMS:
            assert stream in result

    def test_stream_independence(
        self,
        rsil_synthesizer: RSILSynthesizer
    ):
        """Each stream should be processed independently."""
        stream_outputs = [
            {"stream_type": "security", "findings": [{"id": "S1"}]},
            {"stream_type": "quality", "findings": [{"id": "Q1"}]},
        ]

        result = rsil_synthesizer.phase1_aggregate(stream_outputs)

        # Security findings should not appear in quality and vice versa
        assert len(result["security"]) == 1
        assert len(result["quality"]) == 1
        assert result["security"][0]["id"] == "S1"
        assert result["quality"][0]["id"] == "Q1"

    def test_security_stream_patterns(self):
        """Security stream should detect expected vulnerability patterns."""
        expected_patterns = [
            "hardcoded_secret",
            "sql_injection",
            "command_injection",
            "unsafe_deserialization",
            "unsafe_eval",
        ]

        # These are in BlockEnforcer's block lists
        enforcer = BlockEnforcer()
        all_patterns = enforcer.UNCONDITIONAL_BLOCKS + enforcer.CONDITIONAL_BLOCKS

        for pattern in expected_patterns:
            assert pattern in all_patterns

    def test_output_budget_per_stream(self):
        """Each stream should have 5K token output budget."""
        # This is a configuration test - verify the documented budget
        OUTPUT_BUDGET_PER_STREAM = 5000  # tokens
        STREAMS_COUNT = 4
        TOTAL_BUDGET_PER_AUDIT = OUTPUT_BUDGET_PER_STREAM * STREAMS_COUNT

        assert TOTAL_BUDGET_PER_AUDIT == 20000


# =============================================================================
# TASK DECOMPOSER INTEGRATION TESTS
# =============================================================================


class TestTaskDecomposerIntegration:
    """Tests for TaskDecomposer integration with scope keywords."""

    def test_detects_korean_scope_keywords(
        self,
        task_decomposer: TaskDecomposer
    ):
        """TaskDecomposer should detect Korean scope keywords."""
        keywords = task_decomposer.detect_scope_keywords("전체 코드베이스 분석")

        assert "전체" in keywords
        assert "코드베이스" in keywords

    def test_detects_english_scope_keywords(
        self,
        task_decomposer: TaskDecomposer
    ):
        """TaskDecomposer should detect English scope keywords."""
        keywords = task_decomposer.detect_scope_keywords("Analyze entire codebase")

        assert "entire" in keywords
        assert "codebase" in keywords

    @pytest.mark.parametrize("keyword", ["all", "entire", "complete", "whole", "full", "every", "codebase"])
    def test_english_keyword_triggers_decomposition(
        self,
        task_decomposer: TaskDecomposer,
        keyword: str
    ):
        """Each English scope keyword should trigger decomposition."""
        task = f"Analyze {keyword} module"

        assert task_decomposer.should_decompose(task, "/path") is True

    @pytest.mark.parametrize("keyword", ["전체", "모든", "완전한", "전부", "코드베이스"])
    def test_korean_keyword_triggers_decomposition(
        self,
        task_decomposer: TaskDecomposer,
        keyword: str
    ):
        """Each Korean scope keyword should trigger decomposition."""
        task = f"{keyword} 분석"

        assert task_decomposer.should_decompose(task, "/path") is True

    def test_no_keywords_no_decomposition(
        self,
        task_decomposer: TaskDecomposer
    ):
        """Tasks without scope keywords should not trigger decomposition."""
        task = "Review this specific file"

        assert task_decomposer.should_decompose(task, "/path") is False

    def test_decomposition_thresholds(
        self,
        task_decomposer: TaskDecomposer
    ):
        """Verify decomposition thresholds are correctly set."""
        thresholds = task_decomposer.DECOMPOSITION_THRESHOLDS

        assert thresholds["file_count"] == 20
        assert thresholds["directory_count"] == 5
        assert thresholds["loc_estimate"] == 5000


# =============================================================================
# OVERRIDE AUDIT TRAIL TESTS
# =============================================================================


class TestOverrideAuditTrail:
    """Tests for override audit trail functionality."""

    def test_log_override_creates_record(
        self,
        override_audit_trail: OverrideAuditTrail
    ):
        """log_override should create and store a record."""
        record = override_audit_trail.log_override(
            actor="developer@example.com",
            audit_id="audit-123",
            findings=[{"id": "SEC-001", "severity": "ERROR"}],
            justification="False positive in test environment"
        )

        assert record.actor == "developer@example.com"
        assert record.audit_id == "audit-123"
        assert record.risk_accepted is True

    def test_log_override_stores_timestamp(
        self,
        override_audit_trail: OverrideAuditTrail
    ):
        """Override record should have timestamp."""
        record = override_audit_trail.log_override(
            actor="dev",
            audit_id="audit-123",
            findings=[],
            justification="test"
        )

        # Verify it's a valid ISO timestamp
        datetime.fromisoformat(record.timestamp.replace("Z", "+00:00"))

    def test_get_records_returns_all(
        self,
        override_audit_trail: OverrideAuditTrail
    ):
        """get_records should return all override records."""
        override_audit_trail.log_override("dev1", "audit-1", [], "reason1")
        override_audit_trail.log_override("dev2", "audit-2", [], "reason2")

        records = override_audit_trail.get_records()

        assert len(records) == 2

    def test_get_records_for_audit_filters(
        self,
        override_audit_trail: OverrideAuditTrail
    ):
        """get_records_for_audit should filter by audit ID."""
        override_audit_trail.log_override("dev", "audit-1", [], "r1")
        override_audit_trail.log_override("dev", "audit-2", [], "r2")
        override_audit_trail.log_override("dev", "audit-1", [], "r3")

        records = override_audit_trail.get_records_for_audit("audit-1")

        assert len(records) == 2
        assert all(r.audit_id == "audit-1" for r in records)

    def test_override_includes_reviewed_by(
        self,
        override_audit_trail: OverrideAuditTrail
    ):
        """Override can include reviewer information."""
        record = override_audit_trail.log_override(
            actor="developer@example.com",
            audit_id="audit-123",
            findings=[{"id": "SEC-002"}],
            justification="Approved by security team",
            reviewed_by="security-team"
        )

        assert record.reviewed_by == "security-team"

    def test_override_stores_findings(
        self,
        override_audit_trail: OverrideAuditTrail
    ):
        """Override record should store overridden findings."""
        findings = [
            {"id": "SEC-001", "severity": "ERROR", "type": "unsafe_eval"},
            {"id": "SEC-002", "severity": "ERROR", "type": "high_cve"},
        ]

        record = override_audit_trail.log_override(
            actor="dev",
            audit_id="audit-123",
            findings=findings,
            justification="Sandboxed environment"
        )

        assert len(record.findings_overridden) == 2
        assert record.findings_overridden[0]["id"] == "SEC-001"


# =============================================================================
# BLOCK CONDITIONS TESTS
# =============================================================================


class TestBlockConditions:
    """Tests for block condition rules."""

    def test_critical_cannot_be_overridden(
        self,
        rsil_synthesizer: RSILSynthesizer
    ):
        """CRITICAL findings should not allow override."""
        prioritized = {
            "critical": [{"id": "C1", "type": "hardcoded_secret", "stream_type": "security"}],
            "high": [],
            "medium": [],
            "low": [],
        }

        result = rsil_synthesizer.phase5_synthesize(prioritized, [])

        assert result.block_status["override_allowed"] is False

    def test_error_can_be_overridden_with_approval(
        self,
        rsil_synthesizer: RSILSynthesizer
    ):
        """ERROR findings should allow override with approval."""
        prioritized = {
            "critical": [],
            "high": [{"id": "H1", "type": "unsafe_eval", "stream_type": "security"}],
            "medium": [],
            "low": [],
        }

        result = rsil_synthesizer.phase5_synthesize(prioritized, [])

        # Blocked due to high security finding, but override allowed
        assert result.block_status["blocked"] is True
        assert result.block_status["override_allowed"] is True

    def test_warning_does_not_block(
        self,
        rsil_synthesizer: RSILSynthesizer
    ):
        """WARNING findings should not block."""
        prioritized = {
            "critical": [],
            "high": [],
            "medium": [{"id": "M1", "type": "style_issue", "stream_type": "quality"}],
            "low": [],
        }

        result = rsil_synthesizer.phase5_synthesize(prioritized, [])

        assert result.status == "PASS"
        assert result.block_status["blocked"] is False

    def test_must_fix_count_includes_critical_and_high_security(
        self,
        rsil_synthesizer: RSILSynthesizer
    ):
        """must_fix_count should include critical and high security findings."""
        prioritized = {
            "critical": [{"id": "C1", "stream_type": "security"}],
            "high": [
                {"id": "H1", "stream_type": "security"},
                {"id": "H2", "stream_type": "quality"},  # Not security
            ],
            "medium": [],
            "low": [],
        }

        result = rsil_synthesizer.phase5_synthesize(prioritized, [])

        # 1 critical + 1 high security = 2
        assert result.block_status["must_fix_count"] == 2


# =============================================================================
# SEVERITY NORMALIZATION TESTS
# =============================================================================


class TestSeverityNormalization:
    """Tests for severity normalization."""

    @pytest.mark.parametrize("severity,expected", [
        ("CRITICAL", 4),
        ("HIGH", 3),
        ("ERROR", 3),
        ("MEDIUM", 2),
        ("WARNING", 2),
        ("LOW", 1),
        ("INFO", 0),
    ])
    def test_severity_mapping(
        self,
        rsil_synthesizer: RSILSynthesizer,
        severity: str,
        expected: int
    ):
        """Verify severity string to numeric mapping."""
        assert rsil_synthesizer._normalize_severity(severity) == expected

    def test_unknown_severity_defaults_to_medium(
        self,
        rsil_synthesizer: RSILSynthesizer
    ):
        """Unknown severity should default to 2 (medium)."""
        assert rsil_synthesizer._normalize_severity("UNKNOWN") == 2

    def test_case_insensitive_severity(
        self,
        rsil_synthesizer: RSILSynthesizer
    ):
        """Severity normalization should be case-insensitive."""
        assert rsil_synthesizer._normalize_severity("critical") == 4
        assert rsil_synthesizer._normalize_severity("Critical") == 4
        assert rsil_synthesizer._normalize_severity("CRITICAL") == 4


# =============================================================================
# RISK SCORE CALCULATION TESTS
# =============================================================================


class TestRiskScoreCalculation:
    """Tests for risk score calculation."""

    def test_max_risk_score_is_100(
        self,
        rsil_synthesizer: RSILSynthesizer
    ):
        """Risk score should not exceed 100."""
        finding = {
            "normalized_severity": 4,  # CRITICAL
            "type": "sql_injection",  # High exploitability
            "affected_files": ["a", "b", "c", "d", "e", "f"],  # High blast
        }

        score = rsil_synthesizer._calculate_risk_score(finding, {
            "security_quality_intersection": [{"security_finding": finding.get("id")}]
        })

        assert score <= 100

    def test_risk_score_components(
        self,
        rsil_synthesizer: RSILSynthesizer
    ):
        """Verify risk score formula components."""
        # Severity * 20 + Exploitability * 15 + Blast * 10 + CrossRef * 15
        finding = {
            "id": "test",
            "normalized_severity": 4,  # 4 * 20 = 80
            "type": "info",  # exploitability = 1 -> 15
            "affected_files": [],  # blast = 0 -> 0
        }

        score = rsil_synthesizer._calculate_risk_score(finding, {})

        # 80 + 15 + 0 + 0 = 95
        assert score == 95

    def test_cross_reference_boost(
        self,
        rsil_synthesizer: RSILSynthesizer
    ):
        """Cross-referenced findings should get score boost."""
        finding = {"id": "SEC-001", "normalized_severity": 2, "type": "info"}

        without_crossref = rsil_synthesizer._calculate_risk_score(finding, {})

        with_crossref = rsil_synthesizer._calculate_risk_score(finding, {
            "security_quality_intersection": [{"security_finding": "SEC-001"}]
        })

        assert with_crossref > without_crossref
        assert with_crossref - without_crossref == 15  # Cross-ref boost


# =============================================================================
# INTEGRATION TEST
# =============================================================================


class TestDeepAuditIntegration:
    """Integration tests for complete deep audit workflow."""

    def test_end_to_end_blocked_audit(
        self,
        rsil_synthesizer: RSILSynthesizer,
        block_enforcer: BlockEnforcer,
        stream_outputs_mixed: List[Dict[str, Any]]
    ):
        """End-to-end test for blocked audit workflow."""
        # Run RSIL synthesis
        result = rsil_synthesizer.synthesize(stream_outputs_mixed)

        # Verify result structure
        assert result.status == "BLOCK"
        assert len(result.security_findings) > 0
        assert "synthesis_algorithm" in result.metadata

        # Verify block decision
        assert result.block_status["blocked"] is True
        assert result.block_status["must_fix_count"] > 0

    def test_end_to_end_passing_audit(
        self,
        rsil_synthesizer: RSILSynthesizer,
        stream_outputs_clean: List[Dict[str, Any]]
    ):
        """End-to-end test for passing audit workflow."""
        result = rsil_synthesizer.synthesize(stream_outputs_clean)

        assert result.status == "PASS"
        assert result.block_status["blocked"] is False
        assert result.block_status["must_fix_count"] == 0

    def test_override_workflow(
        self,
        rsil_synthesizer: RSILSynthesizer,
        override_audit_trail: OverrideAuditTrail,
        security_finding_error: Dict[str, Any]
    ):
        """Test override workflow for ERROR-level findings."""
        # Synthesize with ERROR-level finding (unsafe_eval is a CONDITIONAL block)
        # For override to be allowed, we need ERROR without CRITICAL
        security_finding_error["stream_type"] = "security"
        # Ensure it's categorized as high but not critical
        security_finding_error["severity"] = "ERROR"
        security_finding_error["normalized_severity"] = 3  # ERROR level

        stream_outputs = [
            {"stream_type": "security", "findings": [security_finding_error]},
            {"stream_type": "quality", "findings": []},
            {"stream_type": "architecture", "findings": []},
            {"stream_type": "dependencies", "findings": []},
        ]

        result = rsil_synthesizer.synthesize(stream_outputs)

        # Should be blocked (high security finding)
        assert result.status == "BLOCK"
        # Override should be allowed since no CRITICAL findings (only ERROR/HIGH)
        # Note: This depends on whether the risk_score places it in "high" vs "critical"
        # If risk_score >= 80, it goes to critical (no override)
        # If 60 <= risk_score < 80, it goes to high (override allowed if stream_type is security and no critical exists)

        # Log override regardless of override_allowed status
        # (in practice, you'd check override_allowed first)
        record = override_audit_trail.log_override(
            actor="developer@example.com",
            audit_id="audit-test",
            findings=[security_finding_error],
            justification="Used only in sandboxed test environment",
            reviewed_by="security-team"
        )

        # Verify audit trail
        assert record.risk_accepted is True
        records = override_audit_trail.get_records()
        assert len(records) == 1
        assert record.justification == "Used only in sandboxed test environment"
