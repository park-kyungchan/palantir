"""
ODA V3.0 - Governance Violations
================================

Defines violation types for quality gates and architectural compliance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ViolationSeverity(str, Enum):
    """Severity levels for governance violations."""
    INFO = "info"       # Suggestion, not blocking
    WARNING = "warning"  # Should fix, logged
    ERROR = "error"     # Must fix, blocks in strict mode
    CRITICAL = "critical"  # Always blocks


class ViolationType(str, Enum):
    """Types of governance violations."""
    # Code Quality
    MISSING_DOCSTRING = "missing_docstring"
    UNTYPED_RETURN = "untyped_return"
    BARE_EXCEPTION = "bare_exception"
    INCONSISTENT_RETURN = "inconsistent_return"
    MISSING_TYPE_HINTS = "missing_type_hints"
    
    # Architecture
    LAYER_VIOLATION = "layer_violation"
    CIRCULAR_IMPORT = "circular_import"
    FORBIDDEN_IMPORT = "forbidden_import"
    
    # Naming
    INVALID_API_NAME = "invalid_api_name"
    NON_SNAKE_CASE = "non_snake_case"
    
    # Complexity
    CYCLOMATIC_COMPLEXITY = "cyclomatic_complexity"
    TOO_MANY_PARAMETERS = "too_many_parameters"


@dataclass
class Violation:
    """
    Represents a single governance violation.
    
    Attributes:
        type: The type of violation
        severity: How severe this violation is
        location: Where the violation occurred (file:line or class.method)
        message: Human-readable description
        suggestion: Optional fix suggestion
        metadata: Additional context
    """
    type: ViolationType
    severity: ViolationSeverity
    location: str
    message: str
    suggestion: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "severity": self.severity.value,
            "location": self.location,
            "message": self.message,
            "suggestion": self.suggestion,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }
    
    def __str__(self) -> str:
        return f"[{self.severity.value.upper()}] {self.location}: {self.message}"


@dataclass
class ViolationReport:
    """
    Aggregated report of all violations from a validation run.
    """
    violations: List[Violation] = field(default_factory=list)
    target: str = ""  # What was validated (action name, module path, etc.)
    
    @property
    def has_errors(self) -> bool:
        """Check if any blocking violations exist."""
        return any(
            v.severity in (ViolationSeverity.ERROR, ViolationSeverity.CRITICAL)
            for v in self.violations
        )
    
    @property
    def error_count(self) -> int:
        return sum(
            1 for v in self.violations
            if v.severity in (ViolationSeverity.ERROR, ViolationSeverity.CRITICAL)
        )
    
    @property
    def warning_count(self) -> int:
        return sum(
            1 for v in self.violations
            if v.severity == ViolationSeverity.WARNING
        )
    
    def add(self, violation: Violation) -> None:
        self.violations.append(violation)
    
    def merge(self, other: "ViolationReport") -> None:
        self.violations.extend(other.violations)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "total": len(self.violations),
            "errors": self.error_count,
            "warnings": self.warning_count,
            "violations": [v.to_dict() for v in self.violations],
        }
    
    def __str__(self) -> str:
        lines = [f"Violation Report for {self.target}:"]
        lines.append(f"  Errors: {self.error_count}, Warnings: {self.warning_count}")
        for v in self.violations:
            lines.append(f"  - {v}")
        return "\n".join(lines)


class GovernanceError(Exception):
    """Raised when governance validation fails in strict mode."""
    
    def __init__(self, report: ViolationReport):
        self.report = report
        super().__init__(str(report))
