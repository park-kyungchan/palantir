"""
Orion ODA v3.0 - Tier Analyzer (V2.1.8)
=======================================

3-Tier Progressive Deep-Dive analysis engine for /deep-audit.
Executes Structure -> Function -> Logic analysis with layer reports.

This module implements:
- 3-Tier hierarchical analysis (Structure, Function, Logic)
- Progressive deep-dive execution (ALL tiers, then report by layer)
- Blocking gate evaluation for CRITICAL/ERROR findings
- Auto-Compact survival through JSON serialization

Tier Hierarchy:
    Tier 1 (Structure): Files, directories, module hierarchy
    Tier 2 (Function):  APIs, signatures, dependencies, imports
    Tier 3 (Logic):     Code lines, control flow, business logic

Usage:
    from lib.oda.planning import TierAnalyzer, TierLevel

    analyzer = TierAnalyzer()

    # Execute all tiers progressively
    result = analyzer.execute_progressive("lib/oda/")

    # Generate layer report
    report = analyzer.generate_layer_report(result.tier_results)

    # Check blocking status
    if result.blocked:
        print(f"BLOCKED: {result.block_reason}")
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple


class TierAnalyzerError(Exception):
    """Raised when tier analysis encounters an error."""
    pass


class TierLevel(str, Enum):
    """
    3-Tier analysis hierarchy.

    Each tier builds upon the previous tier's findings.
    """
    STRUCTURE = "tier_1"   # File/directory structure
    FUNCTION = "tier_2"    # API/signature/dependency
    LOGIC = "tier_3"       # Code line level


class FindingSeverity(str, Enum):
    """
    Finding severity levels.

    CRITICAL and ERROR trigger blocking gate.
    """
    CRITICAL = "critical"  # Must fix before proceeding
    ERROR = "error"        # Should fix, may block
    WARNING = "warning"    # Should address, non-blocking
    INFO = "info"          # Informational, non-blocking


class FindingCategory(str, Enum):
    """Categories for organizing findings."""
    SECURITY = "security"
    ARCHITECTURE = "architecture"
    QUALITY = "quality"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    DOCUMENTATION = "documentation"
    TESTING = "testing"


# Tier analysis state (for tracking progress)
TierState = Literal["pending", "analyzing", "completed", "failed"]


# Blocking thresholds
BLOCKING_THRESHOLDS = {
    FindingSeverity.CRITICAL: 1,  # Any CRITICAL blocks
    FindingSeverity.ERROR: 5,      # 5+ ERRORs blocks
}


@dataclass
class TierFinding:
    """
    A single finding from tier analysis.

    Attributes:
        tier: Which tier discovered this finding
        severity: CRITICAL, ERROR, WARNING, or INFO
        category: Finding category (security, quality, etc.)
        title: Short, descriptive title
        description: Detailed explanation
        file_path: File where finding was discovered
        line_number: Line number (if applicable)
        evidence: Code snippet or evidence
        suggestion: Recommended fix (if applicable)
    """
    tier: TierLevel
    severity: FindingSeverity
    category: FindingCategory
    title: str
    description: str
    file_path: str
    line_number: Optional[int] = None
    evidence: str = ""
    suggestion: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "tier": self.tier.value,
            "severity": self.severity.value,
            "category": self.category.value,
            "title": self.title,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "evidence": self.evidence,
            "suggestion": self.suggestion,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TierFinding":
        """Deserialize from dictionary."""
        return cls(
            tier=TierLevel(data["tier"]),
            severity=FindingSeverity(data["severity"]),
            category=FindingCategory(data["category"]),
            title=data["title"],
            description=data["description"],
            file_path=data["file_path"],
            line_number=data.get("line_number"),
            evidence=data.get("evidence", ""),
            suggestion=data.get("suggestion"),
            timestamp=(
                datetime.fromisoformat(data["timestamp"])
                if "timestamp" in data
                else datetime.now()
            ),
        )

    def format_for_display(self) -> str:
        """Format finding for human-readable display."""
        severity_markers = {
            FindingSeverity.CRITICAL: "[CRITICAL]",
            FindingSeverity.ERROR: "[ERROR]",
            FindingSeverity.WARNING: "[WARNING]",
            FindingSeverity.INFO: "[INFO]",
        }

        lines = [
            f"{severity_markers[self.severity]} {self.title}",
            f"  Category: {self.category.value}",
            f"  File: {self.file_path}" + (f":{self.line_number}" if self.line_number else ""),
            f"  Description: {self.description}",
        ]

        if self.evidence:
            lines.append(f"  Evidence: {self.evidence[:100]}...")

        if self.suggestion:
            lines.append(f"  Suggestion: {self.suggestion}")

        return "\n".join(lines)


@dataclass
class TierResult:
    """
    Result from a single tier analysis.

    Attributes:
        tier: Which tier this result is from
        target: Analysis target path
        state: Current state (pending, analyzing, completed, failed)
        findings: List of findings discovered
        files_analyzed: Files examined during analysis
        metrics: Tier-specific metrics
        execution_time_ms: Time taken for analysis
        timestamp: When analysis completed
    """
    tier: TierLevel
    target: str
    state: TierState = "pending"
    findings: List[TierFinding] = field(default_factory=list)
    files_analyzed: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "tier": self.tier.value,
            "target": self.target,
            "state": self.state,
            "findings": [f.to_dict() for f in self.findings],
            "files_analyzed": self.files_analyzed,
            "metrics": self.metrics,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp.isoformat(),
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TierResult":
        """Deserialize from dictionary."""
        return cls(
            tier=TierLevel(data["tier"]),
            target=data["target"],
            state=data.get("state", "pending"),
            findings=[TierFinding.from_dict(f) for f in data.get("findings", [])],
            files_analyzed=data.get("files_analyzed", []),
            metrics=data.get("metrics", {}),
            execution_time_ms=data.get("execution_time_ms", 0),
            timestamp=(
                datetime.fromisoformat(data["timestamp"])
                if "timestamp" in data
                else datetime.now()
            ),
            error_message=data.get("error_message"),
        )

    @property
    def critical_count(self) -> int:
        """Count of CRITICAL severity findings."""
        return sum(1 for f in self.findings if f.severity == FindingSeverity.CRITICAL)

    @property
    def error_count(self) -> int:
        """Count of ERROR severity findings."""
        return sum(1 for f in self.findings if f.severity == FindingSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        """Count of WARNING severity findings."""
        return sum(1 for f in self.findings if f.severity == FindingSeverity.WARNING)

    @property
    def info_count(self) -> int:
        """Count of INFO severity findings."""
        return sum(1 for f in self.findings if f.severity == FindingSeverity.INFO)


@dataclass
class ProgressiveResult:
    """
    Result from progressive (all-tier) analysis.

    Attributes:
        target: Analysis target path
        tier_results: Results from each tier
        total_findings: Total findings across all tiers
        critical_count: Total CRITICAL findings
        error_count: Total ERROR findings
        blocked: Whether execution should be blocked
        block_reason: Reason for blocking (if blocked)
        execution_time_total_ms: Total time for all tiers
        timestamp: When analysis completed
    """
    target: str
    tier_results: List[TierResult] = field(default_factory=list)
    total_findings: int = 0
    critical_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    blocked: bool = False
    block_reason: Optional[str] = None
    execution_time_total_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "target": self.target,
            "tier_results": [r.to_dict() for r in self.tier_results],
            "total_findings": self.total_findings,
            "critical_count": self.critical_count,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "blocked": self.blocked,
            "block_reason": self.block_reason,
            "execution_time_total_ms": self.execution_time_total_ms,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProgressiveResult":
        """Deserialize from dictionary."""
        return cls(
            target=data["target"],
            tier_results=[TierResult.from_dict(r) for r in data.get("tier_results", [])],
            total_findings=data.get("total_findings", 0),
            critical_count=data.get("critical_count", 0),
            error_count=data.get("error_count", 0),
            warning_count=data.get("warning_count", 0),
            info_count=data.get("info_count", 0),
            blocked=data.get("blocked", False),
            block_reason=data.get("block_reason"),
            execution_time_total_ms=data.get("execution_time_total_ms", 0),
            timestamp=(
                datetime.fromisoformat(data["timestamp"])
                if "timestamp" in data
                else datetime.now()
            ),
        )

    def get_tier_result(self, tier: TierLevel) -> Optional[TierResult]:
        """Get result for a specific tier."""
        for result in self.tier_results:
            if result.tier == tier:
                return result
        return None


@dataclass
class LayerReport:
    """
    Layer-separated report for progressive deep-dive.

    Attributes:
        target: Analysis target path
        tier_1_summary: Structure tier findings summary
        tier_2_summary: Function tier findings summary
        tier_3_summary: Logic tier findings summary
        overall_status: PASS, BLOCKED, or WARNING
        block_reason: Reason for blocking (if blocked)
        generated_at: Report generation timestamp
    """
    target: str
    tier_1_summary: Dict[str, Any] = field(default_factory=dict)
    tier_2_summary: Dict[str, Any] = field(default_factory=dict)
    tier_3_summary: Dict[str, Any] = field(default_factory=dict)
    overall_status: str = "PASS"  # PASS, BLOCKED, WARNING
    block_reason: Optional[str] = None
    generated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "target": self.target,
            "tier_1_summary": self.tier_1_summary,
            "tier_2_summary": self.tier_2_summary,
            "tier_3_summary": self.tier_3_summary,
            "overall_status": self.overall_status,
            "block_reason": self.block_reason,
            "generated_at": self.generated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LayerReport":
        """Deserialize from dictionary."""
        return cls(
            target=data["target"],
            tier_1_summary=data.get("tier_1_summary", {}),
            tier_2_summary=data.get("tier_2_summary", {}),
            tier_3_summary=data.get("tier_3_summary", {}),
            overall_status=data.get("overall_status", "PASS"),
            block_reason=data.get("block_reason"),
            generated_at=(
                datetime.fromisoformat(data["generated_at"])
                if "generated_at" in data
                else datetime.now()
            ),
        )

    def format_markdown(self) -> str:
        """Format report as markdown."""
        sections = [
            f"# Deep-Dive Analysis Report",
            f"**Target:** `{self.target}`",
            f"**Status:** {self.overall_status}",
            f"**Generated:** {self.generated_at.isoformat()}",
            "",
        ]

        if self.block_reason:
            sections.append(f"> **BLOCKED:** {self.block_reason}")
            sections.append("")

        # Tier 1 Summary
        sections.append("## Tier 1: Structure Analysis")
        sections.append(self._format_tier_summary(self.tier_1_summary))
        sections.append("")

        # Tier 2 Summary
        sections.append("## Tier 2: Function Analysis")
        sections.append(self._format_tier_summary(self.tier_2_summary))
        sections.append("")

        # Tier 3 Summary
        sections.append("## Tier 3: Logic Analysis")
        sections.append(self._format_tier_summary(self.tier_3_summary))

        return "\n".join(sections)

    def _format_tier_summary(self, summary: Dict[str, Any]) -> str:
        """Format a tier summary as markdown list."""
        if not summary:
            return "- No findings"

        lines = []

        # Metrics
        if "metrics" in summary:
            lines.append("### Metrics")
            for key, value in summary["metrics"].items():
                lines.append(f"- **{key}:** {value}")

        # Findings by severity
        if "findings_by_severity" in summary:
            lines.append("### Findings")
            for severity, count in summary["findings_by_severity"].items():
                if count > 0:
                    lines.append(f"- {severity.upper()}: {count}")

        # Key findings
        if "key_findings" in summary and summary["key_findings"]:
            lines.append("### Key Findings")
            for finding in summary["key_findings"][:5]:  # Top 5
                lines.append(f"- {finding}")

        return "\n".join(lines) if lines else "- Analysis complete, no issues"


class TierAnalyzer:
    """
    3-Tier Progressive Deep-Dive analyzer.

    Executes ALL tiers, then reports by layer.
    Implements blocking gate for CRITICAL/ERROR findings.

    Key features:
    - Progressive tier execution (Structure -> Function -> Logic)
    - Layer-separated reporting
    - Blocking gate evaluation
    - Auto-Compact survival through JSON serialization
    - ULTRATHINK mode budget allocation

    Example:
        analyzer = TierAnalyzer()

        # Full progressive analysis
        result = analyzer.execute_progressive("lib/oda/")

        if result.blocked:
            print(f"BLOCKED: {result.block_reason}")
        else:
            report = analyzer.generate_layer_report(result.tier_results)
            print(report.format_markdown())
    """

    # Analysis patterns for each tier
    SECURITY_PATTERNS = [
        (r"eval\s*\(", "eval() usage", FindingSeverity.CRITICAL),
        (r"exec\s*\(", "exec() usage", FindingSeverity.CRITICAL),
        (r"__import__\s*\(", "dynamic import", FindingSeverity.WARNING),
        (r"subprocess\.(call|run|Popen)\s*\(.*shell\s*=\s*True", "shell injection risk", FindingSeverity.CRITICAL),
        (r"os\.system\s*\(", "os.system() usage", FindingSeverity.ERROR),
        (r"pickle\.load", "pickle deserialization", FindingSeverity.WARNING),
        (r"yaml\.load\s*\([^)]*Loader\s*=\s*None", "unsafe YAML loading", FindingSeverity.ERROR),
        (r"password\s*=\s*['\"][^'\"]+['\"]", "hardcoded password", FindingSeverity.CRITICAL),
        (r"api_key\s*=\s*['\"][^'\"]+['\"]", "hardcoded API key", FindingSeverity.CRITICAL),
        (r"SQL.*\+.*input|f['\"].*SELECT.*\{", "SQL injection risk", FindingSeverity.CRITICAL),
    ]

    QUALITY_PATTERNS = [
        (r"# ?TODO", "TODO comment", FindingSeverity.INFO),
        (r"# ?FIXME", "FIXME comment", FindingSeverity.WARNING),
        (r"# ?HACK", "HACK comment", FindingSeverity.WARNING),
        (r"# ?XXX", "XXX comment", FindingSeverity.WARNING),
        (r"pass\s*$", "empty pass statement", FindingSeverity.INFO),
        (r"except\s*:", "bare except clause", FindingSeverity.WARNING),
        (r"except\s+Exception\s*:", "broad exception catch", FindingSeverity.INFO),
        (r"print\s*\(", "print statement in code", FindingSeverity.INFO),
    ]

    COMPLEXITY_PATTERNS = [
        (r"if.*if.*if.*if", "deeply nested conditionals", FindingSeverity.WARNING),
        (r"for.*for.*for", "deeply nested loops", FindingSeverity.WARNING),
        (r"lambda.*lambda", "nested lambda", FindingSeverity.INFO),
    ]

    def __init__(
        self,
        thinking_mode: str = "ULTRATHINK",
        base_path: Optional[str] = None,
    ):
        """
        Initialize TierAnalyzer.

        Args:
            thinking_mode: Context budget mode (STANDARD, EXTENDED, ULTRATHINK)
            base_path: Base path for relative path resolution
        """
        self.thinking_mode = thinking_mode
        self.base_path = base_path or os.getcwd()
        self._tier_results: List[TierResult] = []
        self._current_tier: Optional[TierLevel] = None
        self._created_at = datetime.now()
        self._updated_at = datetime.now()

    # ========== Single Tier Analysis ==========

    def analyze_tier(self, tier: TierLevel, target: str) -> TierResult:
        """
        Execute single tier analysis.

        Args:
            tier: Which tier to analyze
            target: Target path

        Returns:
            TierResult with findings
        """
        start_time = datetime.now()

        result = TierResult(
            tier=tier,
            target=target,
            state="analyzing",
        )

        try:
            if tier == TierLevel.STRUCTURE:
                result = self._analyze_structure(target)
            elif tier == TierLevel.FUNCTION:
                # Need structure tier results for context
                structure_result = self._get_cached_result(TierLevel.STRUCTURE)
                result = self._analyze_functions(target, structure_result)
            elif tier == TierLevel.LOGIC:
                # Need function tier results for context
                function_result = self._get_cached_result(TierLevel.FUNCTION)
                result = self._analyze_logic(target, function_result)

            result.state = "completed"

        except Exception as e:
            result.state = "failed"
            result.error_message = str(e)

        # Calculate execution time
        end_time = datetime.now()
        result.execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
        result.timestamp = end_time

        # Cache result
        self._tier_results.append(result)
        self._updated_at = datetime.now()

        return result

    def _get_cached_result(self, tier: TierLevel) -> Optional[TierResult]:
        """Get cached result for a tier."""
        for result in self._tier_results:
            if result.tier == tier:
                return result
        return None

    # ========== Progressive Analysis ==========

    def execute_progressive(self, target: str) -> ProgressiveResult:
        """
        Execute all 3 tiers sequentially, collect all results.

        This is the main entry point for full deep-dive analysis.

        Args:
            target: Target path for analysis

        Returns:
            ProgressiveResult with all tier findings
        """
        start_time = datetime.now()

        # Clear previous results
        self._tier_results = []

        # Execute tiers in order
        tier_order = [TierLevel.STRUCTURE, TierLevel.FUNCTION, TierLevel.LOGIC]

        for tier in tier_order:
            self._current_tier = tier
            self.analyze_tier(tier, target)

        self._current_tier = None

        # Aggregate results
        result = ProgressiveResult(
            target=target,
            tier_results=self._tier_results.copy(),
        )

        # Count findings
        for tier_result in self._tier_results:
            result.total_findings += len(tier_result.findings)
            result.critical_count += tier_result.critical_count
            result.error_count += tier_result.error_count
            result.warning_count += tier_result.warning_count
            result.info_count += tier_result.info_count

        # Evaluate blocking
        result.blocked, result.block_reason = self._evaluate_blocking(self._tier_results)

        # Calculate total execution time
        end_time = datetime.now()
        result.execution_time_total_ms = int((end_time - start_time).total_seconds() * 1000)
        result.timestamp = end_time

        self._updated_at = datetime.now()

        return result

    # ========== Layer Report Generation ==========

    def generate_layer_report(self, tier_results: List[TierResult]) -> LayerReport:
        """
        Generate tier-by-tier layer report.

        Args:
            tier_results: List of tier results

        Returns:
            LayerReport with tier summaries
        """
        report = LayerReport(
            target=tier_results[0].target if tier_results else "unknown",
        )

        for result in tier_results:
            summary = self._generate_tier_summary(result)

            if result.tier == TierLevel.STRUCTURE:
                report.tier_1_summary = summary
            elif result.tier == TierLevel.FUNCTION:
                report.tier_2_summary = summary
            elif result.tier == TierLevel.LOGIC:
                report.tier_3_summary = summary

        # Determine overall status
        blocked, block_reason = self._evaluate_blocking(tier_results)

        if blocked:
            report.overall_status = "BLOCKED"
            report.block_reason = block_reason
        elif any(r.warning_count > 0 for r in tier_results):
            report.overall_status = "WARNING"
        else:
            report.overall_status = "PASS"

        report.generated_at = datetime.now()

        return report

    def _generate_tier_summary(self, result: TierResult) -> Dict[str, Any]:
        """Generate summary for a single tier result."""
        summary = {
            "state": result.state,
            "files_analyzed": len(result.files_analyzed),
            "metrics": result.metrics,
            "findings_by_severity": {
                "critical": result.critical_count,
                "error": result.error_count,
                "warning": result.warning_count,
                "info": result.info_count,
            },
            "key_findings": [],
        }

        # Extract key findings (CRITICAL and ERROR)
        for finding in result.findings:
            if finding.severity in (FindingSeverity.CRITICAL, FindingSeverity.ERROR):
                summary["key_findings"].append(
                    f"[{finding.severity.value.upper()}] {finding.title}: {finding.file_path}"
                )

        return summary

    # ========== Tier-Specific Analysis ==========

    def _analyze_structure(self, target: str) -> TierResult:
        """
        Tier 1: File/directory structure analysis.

        Analyzes:
        - Directory tree
        - File count and sizes
        - Module hierarchy
        - Package structure
        """
        result = TierResult(
            tier=TierLevel.STRUCTURE,
            target=target,
            state="analyzing",
        )

        target_path = Path(self.base_path) / target if not os.path.isabs(target) else Path(target)

        if not target_path.exists():
            result.state = "failed"
            result.error_message = f"Target path does not exist: {target_path}"
            return result

        # Collect structure metrics
        files = []
        dirs = []
        total_size = 0
        python_files = []

        try:
            if target_path.is_file():
                files.append(str(target_path))
                total_size = target_path.stat().st_size
                if target_path.suffix == ".py":
                    python_files.append(str(target_path))
            else:
                for root, dirnames, filenames in os.walk(target_path):
                    # Skip __pycache__ and hidden directories
                    dirnames[:] = [d for d in dirnames if not d.startswith('.') and d != '__pycache__']

                    dirs.append(root)
                    for filename in filenames:
                        if filename.startswith('.'):
                            continue
                        filepath = os.path.join(root, filename)
                        files.append(filepath)
                        try:
                            total_size += os.path.getsize(filepath)
                        except OSError:
                            pass
                        if filename.endswith(".py"):
                            python_files.append(filepath)

            result.files_analyzed = files
            result.metrics = {
                "total_files": len(files),
                "total_directories": len(dirs),
                "total_size_bytes": total_size,
                "python_files": len(python_files),
            }

            # Structure-level findings

            # Check for missing __init__.py in directories with .py files
            if target_path.is_dir():
                for dir_path in dirs:
                    py_in_dir = [f for f in files if f.startswith(dir_path + os.sep) and f.endswith(".py")]
                    if py_in_dir:
                        init_file = os.path.join(dir_path, "__init__.py")
                        if init_file not in files and dir_path != str(target_path):
                            result.findings.append(TierFinding(
                                tier=TierLevel.STRUCTURE,
                                severity=FindingSeverity.WARNING,
                                category=FindingCategory.ARCHITECTURE,
                                title="Missing __init__.py",
                                description=f"Directory contains Python files but no __init__.py",
                                file_path=dir_path,
                                evidence=f"Found {len(py_in_dir)} Python files in directory",
                                suggestion="Add __init__.py to make this a proper Python package",
                            ))

            # Check for overly deep nesting
            max_depth = 0
            for f in files:
                depth = f.replace(str(target_path), "").count(os.sep)
                max_depth = max(max_depth, depth)

            if max_depth > 5:
                result.findings.append(TierFinding(
                    tier=TierLevel.STRUCTURE,
                    severity=FindingSeverity.INFO,
                    category=FindingCategory.ARCHITECTURE,
                    title="Deep directory nesting",
                    description=f"Directory structure has depth of {max_depth} levels",
                    file_path=str(target_path),
                    evidence=f"Maximum nesting depth: {max_depth}",
                    suggestion="Consider flattening the directory structure",
                ))

            result.metrics["max_depth"] = max_depth
            result.state = "completed"

        except Exception as e:
            result.state = "failed"
            result.error_message = str(e)

        return result

    def _analyze_functions(
        self,
        target: str,
        structure: Optional[TierResult],
    ) -> TierResult:
        """
        Tier 2: API/signature/dependency analysis.

        Analyzes:
        - Public APIs
        - Function signatures
        - Import graph
        - Dependency analysis
        - Interface contracts
        """
        result = TierResult(
            tier=TierLevel.FUNCTION,
            target=target,
            state="analyzing",
        )

        # Get files from structure result or discover them
        if structure and structure.files_analyzed:
            python_files = [f for f in structure.files_analyzed if f.endswith(".py")]
        else:
            target_path = Path(self.base_path) / target if not os.path.isabs(target) else Path(target)
            python_files = list(target_path.rglob("*.py")) if target_path.is_dir() else [target_path]
            python_files = [str(f) for f in python_files]

        result.files_analyzed = python_files

        # Metrics
        total_functions = 0
        total_classes = 0
        total_imports = 0
        imports_map: Dict[str, List[str]] = {}  # file -> list of imports

        # Function and class patterns
        func_pattern = re.compile(r"^\s*(?:async\s+)?def\s+(\w+)\s*\(", re.MULTILINE)
        class_pattern = re.compile(r"^\s*class\s+(\w+)\s*[:\(]", re.MULTILINE)
        import_pattern = re.compile(r"^\s*(?:from\s+[\w.]+\s+)?import\s+", re.MULTILINE)

        try:
            for filepath in python_files:
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except (IOError, OSError):
                    continue

                # Count functions
                functions = func_pattern.findall(content)
                total_functions += len(functions)

                # Count classes
                classes = class_pattern.findall(content)
                total_classes += len(classes)

                # Analyze imports
                import_lines = import_pattern.findall(content)
                total_imports += len(import_lines)
                imports_map[filepath] = import_lines

                # Check for missing type hints in public functions
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    # Check for public function without type hints
                    if re.match(r"^\s*def\s+[a-z]\w*\s*\([^)]*\)\s*:", line):
                        if "->" not in line and "self" not in line.split("(")[1].split(")")[0]:
                            result.findings.append(TierFinding(
                                tier=TierLevel.FUNCTION,
                                severity=FindingSeverity.INFO,
                                category=FindingCategory.QUALITY,
                                title="Missing return type hint",
                                description="Public function lacks return type annotation",
                                file_path=filepath,
                                line_number=i + 1,
                                evidence=line.strip()[:80],
                                suggestion="Add return type annotation (e.g., -> None, -> str)",
                            ))

                # Check for circular import risk (importing from same package)
                # This is a simplified check

            result.metrics = {
                "total_functions": total_functions,
                "total_classes": total_classes,
                "total_imports": total_imports,
                "files_with_imports": len([f for f in imports_map if imports_map[f]]),
            }

            result.state = "completed"

        except Exception as e:
            result.state = "failed"
            result.error_message = str(e)

        return result

    def _analyze_logic(
        self,
        target: str,
        functions: Optional[TierResult],
    ) -> TierResult:
        """
        Tier 3: Code line level logic analysis.

        Analyzes:
        - Code complexity (cyclomatic)
        - Security patterns (eval, exec, SQL injection)
        - Business logic flow
        - Error handling patterns
        - Performance anti-patterns
        """
        result = TierResult(
            tier=TierLevel.LOGIC,
            target=target,
            state="analyzing",
        )

        # Get files from previous tier or discover them
        if functions and functions.files_analyzed:
            python_files = functions.files_analyzed
        else:
            target_path = Path(self.base_path) / target if not os.path.isabs(target) else Path(target)
            python_files = list(target_path.rglob("*.py")) if target_path.is_dir() else [target_path]
            python_files = [str(f) for f in python_files]

        result.files_analyzed = python_files

        # Metrics
        total_lines = 0
        code_lines = 0
        comment_lines = 0

        try:
            for filepath in python_files:
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        lines = content.split('\n')
                except (IOError, OSError):
                    continue

                total_lines += len(lines)

                for i, line in enumerate(lines):
                    stripped = line.strip()

                    if not stripped:
                        continue
                    elif stripped.startswith('#'):
                        comment_lines += 1
                    else:
                        code_lines += 1

                    # Check security patterns
                    for pattern, title, severity in self.SECURITY_PATTERNS:
                        if re.search(pattern, line, re.IGNORECASE):
                            result.findings.append(TierFinding(
                                tier=TierLevel.LOGIC,
                                severity=severity,
                                category=FindingCategory.SECURITY,
                                title=title,
                                description=f"Potentially dangerous pattern detected",
                                file_path=filepath,
                                line_number=i + 1,
                                evidence=line.strip()[:100],
                                suggestion="Review and replace with safer alternative",
                            ))

                    # Check quality patterns
                    for pattern, title, severity in self.QUALITY_PATTERNS:
                        if re.search(pattern, line, re.IGNORECASE):
                            result.findings.append(TierFinding(
                                tier=TierLevel.LOGIC,
                                severity=severity,
                                category=FindingCategory.QUALITY,
                                title=title,
                                description=f"Code quality issue detected",
                                file_path=filepath,
                                line_number=i + 1,
                                evidence=line.strip()[:100],
                            ))

                    # Check complexity patterns
                    for pattern, title, severity in self.COMPLEXITY_PATTERNS:
                        if re.search(pattern, line, re.IGNORECASE):
                            result.findings.append(TierFinding(
                                tier=TierLevel.LOGIC,
                                severity=severity,
                                category=FindingCategory.MAINTAINABILITY,
                                title=title,
                                description=f"High complexity detected",
                                file_path=filepath,
                                line_number=i + 1,
                                evidence=line.strip()[:100],
                                suggestion="Consider refactoring to reduce complexity",
                            ))

            result.metrics = {
                "total_lines": total_lines,
                "code_lines": code_lines,
                "comment_lines": comment_lines,
                "comment_ratio": round(comment_lines / max(code_lines, 1), 2),
            }

            result.state = "completed"

        except Exception as e:
            result.state = "failed"
            result.error_message = str(e)

        return result

    # ========== Blocking Evaluation ==========

    def _evaluate_blocking(
        self,
        results: List[TierResult],
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if CRITICAL/ERROR findings require blocking.

        Args:
            results: List of tier results

        Returns:
            Tuple of (blocked, reason)
        """
        total_critical = sum(r.critical_count for r in results)
        total_error = sum(r.error_count for r in results)

        if total_critical >= BLOCKING_THRESHOLDS[FindingSeverity.CRITICAL]:
            return True, f"CRITICAL findings ({total_critical}) exceed threshold"

        if total_error >= BLOCKING_THRESHOLDS[FindingSeverity.ERROR]:
            return True, f"ERROR findings ({total_error}) exceed threshold ({BLOCKING_THRESHOLDS[FindingSeverity.ERROR]})"

        return False, None

    # ========== TodoWrite Integration ==========

    def to_todowrite_json(self) -> List[Dict[str, Any]]:
        """
        Generate TodoWrite-compatible JSON for UI display.

        Returns:
            List of todo items showing analysis progress
        """
        todos = []

        tier_names = {
            TierLevel.STRUCTURE: "Structure",
            TierLevel.FUNCTION: "Function",
            TierLevel.LOGIC: "Logic",
        }

        for tier in [TierLevel.STRUCTURE, TierLevel.FUNCTION, TierLevel.LOGIC]:
            result = self._get_cached_result(tier)

            if result is None:
                status = "pending"
                if self._current_tier and self._current_tier == tier:
                    status = "in_progress"
            elif result.state == "completed":
                status = "completed"
            elif result.state == "analyzing":
                status = "in_progress"
            else:
                status = "pending"

            content = f"[Tier {tier.value[-1]}] {tier_names[tier]} Analysis"

            if result and result.state == "completed":
                finding_count = len(result.findings)
                content += f" ({finding_count} findings)"

            todos.append({
                "content": content,
                "status": status,
                "activeForm": f"Analyzing {tier_names[tier].lower()}...",
            })

        return todos

    # ========== Persistence (Auto-Compact Survival) ==========

    def to_json(self) -> str:
        """
        Serialize to JSON for persistence.

        Returns:
            JSON string for storage
        """
        data = {
            "thinking_mode": self.thinking_mode,
            "base_path": self.base_path,
            "tier_results": [r.to_dict() for r in self._tier_results],
            "current_tier": self._current_tier.value if self._current_tier else None,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "TierAnalyzer":
        """
        Deserialize from JSON.

        Args:
            json_str: JSON string from to_json()

        Returns:
            Restored TierAnalyzer
        """
        data = json.loads(json_str)

        analyzer = cls(
            thinking_mode=data.get("thinking_mode", "ULTRATHINK"),
            base_path=data.get("base_path"),
        )

        analyzer._tier_results = [
            TierResult.from_dict(r) for r in data.get("tier_results", [])
        ]

        if data.get("current_tier"):
            analyzer._current_tier = TierLevel(data["current_tier"])

        analyzer._created_at = datetime.fromisoformat(data["created_at"])
        analyzer._updated_at = datetime.fromisoformat(data["updated_at"])

        return analyzer


# ========== Convenience Functions ==========

def create_tier_analyzer(
    thinking_mode: str = "ULTRATHINK",
    base_path: Optional[str] = None,
) -> TierAnalyzer:
    """
    Create a new TierAnalyzer instance.

    Args:
        thinking_mode: Context budget mode
        base_path: Base path for relative path resolution

    Returns:
        New TierAnalyzer instance
    """
    return TierAnalyzer(thinking_mode=thinking_mode, base_path=base_path)


def load_tier_analyzer(json_str: str) -> TierAnalyzer:
    """
    Load TierAnalyzer from JSON (for Auto-Compact recovery).

    Args:
        json_str: JSON string from to_json()

    Returns:
        Restored TierAnalyzer
    """
    return TierAnalyzer.from_json(json_str)


def analyze_target(
    target: str,
    thinking_mode: str = "ULTRATHINK",
) -> ProgressiveResult:
    """
    Quick analysis of a target path.

    Args:
        target: Target path to analyze
        thinking_mode: Context budget mode

    Returns:
        ProgressiveResult with all tier findings
    """
    analyzer = create_tier_analyzer(thinking_mode=thinking_mode)
    return analyzer.execute_progressive(target)


def get_blocking_status(result: ProgressiveResult) -> Tuple[bool, str]:
    """
    Get blocking status from a ProgressiveResult.

    Args:
        result: Progressive analysis result

    Returns:
        Tuple of (blocked, status_message)
    """
    if result.blocked:
        return True, f"BLOCKED: {result.block_reason}"

    if result.warning_count > 0:
        return False, f"WARNING: {result.warning_count} warnings found"

    return False, "PASS: No blocking issues found"
