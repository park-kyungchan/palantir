"""
Orion ODA PAI Skills - /audit Skill Unit Tests

Tests for the /audit skill (Stage C Quality Verification) including:
- 4-Stream parallel quality checks (Build, Lint, Security, Documentation)
- Severity level classification (CRITICAL->INFO hierarchy)
- Filtering logic
- Pre-Mutation Zone boundary enforcement
- Stage C Quality Gate enforcement
- Boris Cherny parallel execution pattern
- TodoWrite integration

Reference: .claude/skills/audit.md

Version: 1.0.0
"""
from __future__ import annotations

import pytest
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import time


# =============================================================================
# AUDIT SKILL CORE ENUMS AND CONSTANTS (Extracted from audit.md)
# =============================================================================

class Severity(str, Enum):
    """Severity levels from audit.md Section 7."""
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    WARNING = "WARNING"
    LOW = "LOW"
    INFO = "INFO"


class GateStatus(str, Enum):
    """Quality Gate statuses."""
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARNING"


class StreamPriority(str, Enum):
    """Stream priority levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class OperationType(str, Enum):
    """Pre-Mutation Zone operation types."""
    READ = "read"
    EXECUTE_VERIFY = "execute_verify"
    ANALYZE = "analyze"
    REPORT = "report"
    TODO_WRITE = "todo_write"
    EDIT = "edit"
    WRITE = "write"
    CREATE_PROPOSAL = "create_proposal"


# Severity Action Matrix (from audit.md Section 7)
SEVERITY_ACTION_MATRIX = {
    Severity.CRITICAL: {"action": "BLOCK", "auto_fix": False, "requires_review": True},
    Severity.ERROR: {"action": "BLOCK", "auto_fix": False, "requires_review": True},
    Severity.HIGH: {"action": "WARN", "auto_fix": False, "requires_review": True},
    Severity.MEDIUM: {"action": "PASS", "auto_fix": True, "requires_review": False},
    Severity.WARNING: {"action": "PASS", "auto_fix": True, "requires_review": False},
    Severity.LOW: {"action": "PASS", "auto_fix": True, "requires_review": False},
    Severity.INFO: {"action": "PASS", "auto_fix": True, "requires_review": False},
}

# Severity Priority Order (highest to lowest)
SEVERITY_PRIORITY = [
    Severity.CRITICAL,
    Severity.ERROR,
    Severity.HIGH,
    Severity.MEDIUM,
    Severity.WARNING,
    Severity.LOW,
    Severity.INFO,
]

# Pre-Mutation Zone Rules (from audit.md Section 1)
PRE_MUTATION_ZONE_RULES = {
    "allowed": [
        OperationType.READ,
        OperationType.EXECUTE_VERIFY,
        OperationType.ANALYZE,
        OperationType.REPORT,
        OperationType.TODO_WRITE,
    ],
    "forbidden": [
        OperationType.EDIT,
        OperationType.WRITE,
        OperationType.CREATE_PROPOSAL,
    ],
}


# =============================================================================
# STREAM DEFINITIONS (from audit.md Section 4)
# =============================================================================

BUILD_STREAM = {
    "name": "build",
    "priority": StreamPriority.HIGH,
    "blocking": True,
    "checks": [
        {"name": "compile", "command": "python -m py_compile {files}"},
        {"name": "tests", "command": "pytest {path} -v --tb=short"},
        {"name": "typecheck", "command": "mypy {path} --ignore-missing-imports"},
    ],
    "severity_map": {
        "error": Severity.CRITICAL,
        "failure": Severity.CRITICAL,
    }
}

LINT_STREAM = {
    "name": "lint",
    "priority": StreamPriority.MEDIUM,
    "blocking": True,  # Only for ERROR severity
    "checks": [
        {"name": "ruff", "command": "ruff check {path}"},
        {"name": "format", "command": "ruff format --check {path}"},
    ],
    "severity_map": {
        "E": Severity.ERROR,      # ruff error codes
        "F": Severity.ERROR,      # pyflakes error
        "W": Severity.WARNING,    # warnings
        "I": Severity.INFO,       # import sorting
    }
}

SECURITY_STREAM = {
    "name": "security",
    "priority": StreamPriority.HIGH,
    "blocking": True,
    "checks": [
        {"name": "eval_exec", "pattern": r"eval\(|exec\(", "severity": Severity.CRITICAL},
        {"name": "credentials", "pattern": r"password\s*=\s*['\"]", "severity": Severity.CRITICAL},
        {"name": "sql_injection", "pattern": r"execute\(.*%s.*%", "severity": Severity.CRITICAL},
        {"name": "env_exposure", "pattern": r"\.env|credentials\.json", "severity": Severity.HIGH},
    ],
    "severity_map": {
        "match": Severity.CRITICAL,
    }
}

DOCUMENTATION_STREAM = {
    "name": "documentation",
    "priority": StreamPriority.LOW,
    "blocking": False,
    "checks": [
        {"name": "docstrings", "check": "docstring_coverage"},
        {"name": "type_hints", "check": "type_annotation_coverage"},
        {"name": "module_docs", "check": "module_docstring_present"},
    ],
    "severity_map": {
        "missing": Severity.INFO,
        "incomplete": Severity.LOW,
    }
}

ALL_STREAMS = [BUILD_STREAM, LINT_STREAM, SECURITY_STREAM, DOCUMENTATION_STREAM]


# =============================================================================
# QUALITY GATE RULES (from audit.md Section 11)
# =============================================================================

QUALITY_GATE_RULES = {
    "QG-001": {
        "condition": "CRITICAL > 0",
        "action": "BLOCK",
        "override": None,
        "message": "CRITICAL findings: {count}",
    },
    "QG-002": {
        "condition": "ERROR > 0",
        "action": "BLOCK",
        "override": None,
        "message": "ERROR findings: {count}",
    },
    "QG-003": {
        "condition": "build_failed",
        "action": "BLOCK",
        "override": None,
        "message": "Build stream failed",
    },
    "QG-004": {
        "condition": "tests_failed",
        "action": "BLOCK",
        "override": "--skip-tests",
        "message": "Tests failed",
    },
    "QG-005": {
        "condition": "HIGH > 5",
        "action": "WARN",
        "override": "--ignore-high",
        "message": "HIGH findings exceed threshold: {count}",
    },
    "QG-006": {
        "condition": "security_finding",
        "action": "BLOCK",
        "override": "--allow-security-risk",
        "message": "Security findings: {count}",
    },
}


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class Finding:
    """Represents a single audit finding."""
    severity: Severity
    category: str
    message: str
    file: str
    line: int
    code: Optional[str] = None
    auto_fixable: bool = False


@dataclass
class QualityCheck:
    """Represents a quality check result."""
    name: str
    status: str  # passed, failed, skipped
    command: str
    output: str = ""
    duration_ms: int = 0
    exit_code: int = 0


@dataclass
class StreamResult:
    """Represents results from a single stream."""
    name: str
    status: str  # passed, failed
    priority: StreamPriority
    blocking: bool
    quality_checks: List[QualityCheck] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)


@dataclass
class AuditResult:
    """Complete audit result."""
    status: GateStatus
    target: str
    quality_checks: List[QualityCheck] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)
    severity_counts: Dict[str, int] = field(default_factory=dict)
    stream_status: Dict[str, str] = field(default_factory=dict)
    recommendation: str = ""


@dataclass
class QualityGateResult:
    """Quality gate enforcement result."""
    gate_status: GateStatus
    blocking_rules: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    can_proceed: bool = True
    required_actions: List[str] = field(default_factory=list)


@dataclass
class TodoItem:
    """Represents a TodoWrite item."""
    content: str
    status: str  # pending, in_progress, completed
    activeForm: str


# =============================================================================
# IMPLEMENTATION FUNCTIONS
# =============================================================================

def is_operation_allowed(operation: OperationType) -> bool:
    """
    Check if operation is allowed in Pre-Mutation Zone.

    From audit.md Section 1: Pre-Mutation Zone Definition

    Args:
        operation: The operation type to check

    Returns:
        True if operation is allowed, False otherwise
    """
    return operation in PRE_MUTATION_ZONE_RULES["allowed"]


def is_operation_forbidden(operation: OperationType) -> bool:
    """
    Check if operation is forbidden in Pre-Mutation Zone.

    Args:
        operation: The operation type to check

    Returns:
        True if operation is forbidden, False otherwise
    """
    return operation in PRE_MUTATION_ZONE_RULES["forbidden"]


def get_severity_action(severity: Severity) -> Dict[str, Any]:
    """
    Get the action for a severity level.

    From audit.md Section 7: Severity Action Matrix

    Args:
        severity: The severity level

    Returns:
        Action configuration dictionary
    """
    return SEVERITY_ACTION_MATRIX.get(severity, SEVERITY_ACTION_MATRIX[Severity.INFO])


def is_severity_blocking(severity: Severity) -> bool:
    """
    Check if a severity level is blocking.

    Args:
        severity: The severity level

    Returns:
        True if severity is blocking (CRITICAL or ERROR)
    """
    return severity in [Severity.CRITICAL, Severity.ERROR]


def compare_severity(a: Severity, b: Severity) -> int:
    """
    Compare two severity levels.

    Args:
        a: First severity
        b: Second severity

    Returns:
        -1 if a < b, 0 if a == b, 1 if a > b (higher severity is "greater")
    """
    idx_a = SEVERITY_PRIORITY.index(a)
    idx_b = SEVERITY_PRIORITY.index(b)
    if idx_a < idx_b:
        return 1  # a is higher severity
    elif idx_a > idx_b:
        return -1  # b is higher severity
    return 0


def filter_findings(findings: List[Finding], config: Optional[Dict] = None) -> Dict[str, List[Finding]]:
    """
    Filter findings based on severity and blocking rules.

    From audit.md Section 8: Filtering Logic Section

    Args:
        findings: List of findings to filter
        config: Optional configuration with exclusions and overrides

    Returns:
        Dictionary with categorized findings
    """
    if config is None:
        config = {}

    filtered = {
        "blocking": [],
        "warning": [],
        "informational": [],
        "auto_fixable": [],
    }

    exclusions = config.get("exclusions", [])
    severity_overrides = config.get("severity_overrides", {})

    for finding in findings:
        # Skip excluded codes
        if finding.code and finding.code in exclusions:
            continue

        # Apply severity overrides
        severity = finding.severity
        if finding.code and finding.code in severity_overrides:
            severity = Severity(severity_overrides[finding.code])

        # Classify finding
        if severity in [Severity.CRITICAL, Severity.ERROR]:
            filtered["blocking"].append(finding)
        elif severity in [Severity.HIGH, Severity.MEDIUM, Severity.WARNING]:
            filtered["warning"].append(finding)
            if finding.auto_fixable:
                filtered["auto_fixable"].append(finding)
        else:
            filtered["informational"].append(finding)
            if finding.auto_fixable:
                filtered["auto_fixable"].append(finding)

    # Sort each category by severity priority
    for category in filtered:
        filtered[category].sort(
            key=lambda f: SEVERITY_PRIORITY.index(f.severity)
        )

    return filtered


def determine_blocking_status(filtered: Dict[str, List[Finding]]) -> Tuple[bool, str]:
    """
    Determine if audit should block based on filtered findings.

    From audit.md Section 8: Blocking Determination Logic

    Args:
        filtered: Filtered findings dictionary

    Returns:
        Tuple of (is_blocking, reason)
    """
    blocking = filtered.get("blocking", [])

    if not blocking:
        return (False, "No blocking findings")

    critical_count = sum(1 for f in blocking if f.severity == Severity.CRITICAL)
    error_count = sum(1 for f in blocking if f.severity == Severity.ERROR)

    if critical_count > 0:
        return (True, f"CRITICAL findings: {critical_count}")

    if error_count > 0:
        return (True, f"ERROR findings: {error_count}")

    return (False, "No blocking findings")


def count_severities(findings: List[Finding]) -> Dict[str, int]:
    """
    Count findings by severity.

    Args:
        findings: List of findings

    Returns:
        Dictionary mapping severity to count
    """
    counts = {s.value: 0 for s in Severity}
    for finding in findings:
        counts[finding.severity.value] += 1
    return counts


def aggregate_stream_results(stream_results: List[StreamResult]) -> AuditResult:
    """
    Aggregate results from multiple streams.

    From audit.md Section 6: Stream Synthesis Section

    Args:
        stream_results: List of stream results

    Returns:
        Aggregated AuditResult
    """
    all_checks = []
    all_findings = []
    stream_status = {}

    for result in stream_results:
        all_checks.extend(result.quality_checks)
        all_findings.extend(result.findings)
        stream_status[result.name] = result.status

    severity_counts = count_severities(all_findings)

    # Determine overall status
    if severity_counts.get(Severity.CRITICAL.value, 0) > 0:
        status = GateStatus.FAIL
        recommendation = "BLOCK: Fix CRITICAL issues before proceeding"
    elif severity_counts.get(Severity.ERROR.value, 0) > 0:
        status = GateStatus.FAIL
        recommendation = "BLOCK: Fix ERROR issues before proceeding"
    elif severity_counts.get(Severity.HIGH.value, 0) > 0:
        status = GateStatus.WARN
        recommendation = "Review HIGH severity findings"
    else:
        status = GateStatus.PASS
        recommendation = "Ready for implementation"

    return AuditResult(
        status=status,
        target="",
        quality_checks=all_checks,
        findings=all_findings,
        severity_counts=severity_counts,
        stream_status=stream_status,
        recommendation=recommendation,
    )


def enforce_quality_gate(audit_result: AuditResult) -> QualityGateResult:
    """
    Enforce Stage C Quality Gate based on audit results.

    From audit.md Section 11: Stage C Quality Gate Enforcement

    Args:
        audit_result: The audit result to evaluate

    Returns:
        QualityGateResult with gate status and required actions
    """
    severity_counts = audit_result.severity_counts
    stream_status = audit_result.stream_status

    blocking_rules = []
    warnings = []

    # QG-001: CRITICAL check
    critical_count = severity_counts.get(Severity.CRITICAL.value, 0)
    if critical_count > 0:
        blocking_rules.append({
            "rule": "QG-001",
            "message": f"CRITICAL findings: {critical_count}",
            "action": "Fix all CRITICAL issues",
        })

    # QG-002: ERROR check
    error_count = severity_counts.get(Severity.ERROR.value, 0)
    if error_count > 0:
        blocking_rules.append({
            "rule": "QG-002",
            "message": f"ERROR findings: {error_count}",
            "action": "Fix all ERROR issues",
        })

    # QG-003: Build stream
    if stream_status.get("build") == "failed":
        blocking_rules.append({
            "rule": "QG-003",
            "message": "Build stream failed",
            "action": "Fix build errors",
        })

    # QG-004: Test failures
    if stream_status.get("tests") == "failed":
        blocking_rules.append({
            "rule": "QG-004",
            "message": "Tests failed",
            "action": "Fix failing tests",
        })

    # QG-005: HIGH count threshold
    high_count = severity_counts.get(Severity.HIGH.value, 0)
    if high_count > 5:
        warnings.append({
            "rule": "QG-005",
            "message": f"HIGH findings exceed threshold: {high_count}",
            "action": "Review HIGH severity findings",
        })

    # QG-006: Security findings
    security_findings = [
        f for f in audit_result.findings
        if f.category == "security" and f.severity in [Severity.CRITICAL, Severity.HIGH]
    ]
    if security_findings:
        blocking_rules.append({
            "rule": "QG-006",
            "message": f"Security findings: {len(security_findings)}",
            "action": "Address security vulnerabilities",
        })

    # Determine gate status
    if blocking_rules:
        gate_status = GateStatus.FAIL
        can_proceed = False
    elif warnings:
        gate_status = GateStatus.WARN
        can_proceed = True
    else:
        gate_status = GateStatus.PASS
        can_proceed = True

    return QualityGateResult(
        gate_status=gate_status,
        blocking_rules=blocking_rules,
        warnings=warnings,
        can_proceed=can_proceed,
        required_actions=[r["action"] for r in blocking_rules],
    )


def get_stream_by_name(name: str) -> Optional[Dict]:
    """
    Get stream configuration by name.

    Args:
        name: Stream name

    Returns:
        Stream configuration or None
    """
    for stream in ALL_STREAMS:
        if stream["name"] == name:
            return stream
    return None


def is_stream_blocking(stream: Dict) -> bool:
    """
    Check if a stream is blocking.

    Args:
        stream: Stream configuration

    Returns:
        True if stream is blocking
    """
    return stream.get("blocking", False)


def validate_parallel_execution(tasks: List[str], max_parallel: int = 4) -> bool:
    """
    Validate that tasks can be executed in parallel.

    From audit.md Section 5: Boris Cherny Parallel Execution Pattern

    Args:
        tasks: List of task names to execute
        max_parallel: Maximum parallel tasks (default 4 for 4-stream)

    Returns:
        True if parallel execution is valid
    """
    # All 4 streams are independent and can run in parallel
    valid_streams = {"build", "lint", "security", "documentation"}
    return all(task in valid_streams for task in tasks) and len(tasks) <= max_parallel


def should_use_parallel_execution(num_checks: int) -> bool:
    """
    Determine if parallel execution should be used.

    From audit.md Section 5: Background Execution Rules

    Args:
        num_checks: Number of quality checks

    Returns:
        True if parallel execution should be used (3+ checks)
    """
    return num_checks >= 3


def create_todo_progress(stage: str) -> List[TodoItem]:
    """
    Create TodoWrite progress items for audit.

    From audit.md Section 9: TodoWrite Integration

    Args:
        stage: Current stage identifier

    Returns:
        List of TodoItem objects
    """
    items = [
        TodoItem("Initialize audit target", "pending", "Initializing audit target"),
        TodoItem("Deploy Build Stream", "pending", "Deploying Build Stream"),
        TodoItem("Deploy Lint Stream", "pending", "Deploying Lint Stream"),
        TodoItem("Deploy Security Stream", "pending", "Deploying Security Stream"),
        TodoItem("Deploy Documentation Stream", "pending", "Deploying Documentation Stream"),
        TodoItem("Synthesize stream results", "pending", "Synthesizing stream results"),
        TodoItem("Generate audit report", "pending", "Generating audit report"),
    ]

    if stage == "initialized":
        items[0] = TodoItem("Initialize audit target", "completed", "Initializing audit target")
    elif stage == "streams_deployed":
        items[0] = TodoItem("Initialize audit target", "completed", "Initializing audit target")
        items[1] = TodoItem("Deploy Build Stream", "completed", "Deploying Build Stream")
        items[2] = TodoItem("Deploy Lint Stream", "completed", "Deploying Lint Stream")
        items[3] = TodoItem("Deploy Security Stream", "completed", "Deploying Security Stream")
        items[4] = TodoItem("Deploy Documentation Stream", "completed", "Deploying Documentation Stream")
        items[5] = TodoItem("Synthesize stream results", "in_progress", "Synthesizing stream results")
    elif stage == "completed":
        items = [
            TodoItem("Initialize audit target", "completed", "Initializing audit target"),
            TodoItem("Deploy Build Stream", "completed", "Deploying Build Stream"),
            TodoItem("Deploy Lint Stream", "completed", "Deploying Lint Stream"),
            TodoItem("Deploy Security Stream", "completed", "Deploying Security Stream"),
            TodoItem("Deploy Documentation Stream", "completed", "Deploying Documentation Stream"),
            TodoItem("Synthesize stream results", "completed", "Synthesizing stream results"),
            TodoItem("Generate audit report", "completed", "Generating audit report"),
        ]

    return items


def map_ruff_code_to_severity(code: str) -> Severity:
    """
    Map ruff error code to severity level.

    From audit.md Section 4: Lint Stream severity_map

    Args:
        code: Ruff error code (e.g., "E501", "F401", "W503")

    Returns:
        Severity level
    """
    if not code:
        return Severity.INFO

    prefix = code[0].upper()
    severity_map = LINT_STREAM["severity_map"]
    return severity_map.get(prefix, Severity.INFO)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def sample_findings() -> List[Finding]:
    """Sample findings for testing."""
    return [
        Finding(Severity.CRITICAL, "security", "eval() usage detected", "lib/utils.py", 15),
        Finding(Severity.ERROR, "lint", "Undefined variable", "lib/module.py", 42, "F821"),
        Finding(Severity.HIGH, "security", "Potential credential exposure", "config.py", 10),
        Finding(Severity.WARNING, "lint", "Unused import", "lib/main.py", 5, "F401", True),
        Finding(Severity.INFO, "documentation", "Missing docstring", "lib/module.py", 1),
    ]


@pytest.fixture
def sample_quality_checks() -> List[QualityCheck]:
    """Sample quality checks for testing."""
    return [
        QualityCheck("compile", "passed", "python -m py_compile *.py", "", 500, 0),
        QualityCheck("tests", "passed", "pytest tests/ -v", "5 passed", 12500, 0),
        QualityCheck("lint", "passed", "ruff check .", "", 2000, 0),
        QualityCheck("typecheck", "passed", "mypy .", "", 8000, 0),
    ]


@pytest.fixture
def sample_stream_results() -> List[StreamResult]:
    """Sample stream results for aggregation testing."""
    return [
        StreamResult(
            name="build",
            status="passed",
            priority=StreamPriority.HIGH,
            blocking=True,
            quality_checks=[QualityCheck("compile", "passed", "python -m py_compile", "", 500, 0)],
            findings=[],
        ),
        StreamResult(
            name="lint",
            status="passed",
            priority=StreamPriority.MEDIUM,
            blocking=True,
            quality_checks=[QualityCheck("ruff", "passed", "ruff check .", "", 2000, 0)],
            findings=[Finding(Severity.WARNING, "lint", "Unused import", "lib/main.py", 5, "F401", True)],
        ),
        StreamResult(
            name="security",
            status="passed",
            priority=StreamPriority.HIGH,
            blocking=True,
            quality_checks=[],
            findings=[],
        ),
        StreamResult(
            name="documentation",
            status="passed",
            priority=StreamPriority.LOW,
            blocking=False,
            quality_checks=[],
            findings=[Finding(Severity.INFO, "documentation", "Missing docstring", "lib/module.py", 1)],
        ),
    ]


@pytest.fixture
def failing_audit_result() -> AuditResult:
    """Audit result with CRITICAL findings."""
    return AuditResult(
        status=GateStatus.FAIL,
        target="/lib/oda/",
        quality_checks=[],
        findings=[
            Finding(Severity.CRITICAL, "security", "eval() usage", "lib/utils.py", 15),
            Finding(Severity.ERROR, "lint", "Syntax error", "lib/module.py", 42),
        ],
        severity_counts={
            Severity.CRITICAL.value: 1,
            Severity.ERROR.value: 1,
            Severity.HIGH.value: 0,
            Severity.MEDIUM.value: 0,
            Severity.WARNING.value: 0,
            Severity.LOW.value: 0,
            Severity.INFO.value: 0,
        },
        stream_status={"build": "failed", "lint": "failed", "security": "failed"},
        recommendation="BLOCK: Fix CRITICAL issues",
    )


@pytest.fixture
def passing_audit_result() -> AuditResult:
    """Audit result with no blocking findings."""
    return AuditResult(
        status=GateStatus.PASS,
        target="/lib/oda/",
        quality_checks=[],
        findings=[
            Finding(Severity.WARNING, "lint", "Unused import", "lib/main.py", 5),
            Finding(Severity.INFO, "documentation", "Missing docstring", "lib/module.py", 1),
        ],
        severity_counts={
            Severity.CRITICAL.value: 0,
            Severity.ERROR.value: 0,
            Severity.HIGH.value: 0,
            Severity.MEDIUM.value: 0,
            Severity.WARNING.value: 1,
            Severity.LOW.value: 0,
            Severity.INFO.value: 1,
        },
        stream_status={"build": "passed", "lint": "passed", "security": "passed", "documentation": "passed"},
        recommendation="Ready for implementation",
    )


# =============================================================================
# TEST CASES: Pre-Mutation Zone Boundary Enforcement
# =============================================================================

class TestPreMutationZone:
    """Tests for Pre-Mutation Zone boundary enforcement (audit.md Section 1)."""

    def test_read_operation_allowed(self):
        """Test that read operations are allowed."""
        assert is_operation_allowed(OperationType.READ) is True

    def test_execute_verify_allowed(self):
        """Test that verification commands are allowed."""
        assert is_operation_allowed(OperationType.EXECUTE_VERIFY) is True

    def test_analyze_allowed(self):
        """Test that analysis operations are allowed."""
        assert is_operation_allowed(OperationType.ANALYZE) is True

    def test_report_allowed(self):
        """Test that report generation is allowed."""
        assert is_operation_allowed(OperationType.REPORT) is True

    def test_todo_write_allowed(self):
        """Test that TodoWrite updates are allowed."""
        assert is_operation_allowed(OperationType.TODO_WRITE) is True

    def test_edit_forbidden(self):
        """Test that edit operations are forbidden."""
        assert is_operation_forbidden(OperationType.EDIT) is True
        assert is_operation_allowed(OperationType.EDIT) is False

    def test_write_forbidden(self):
        """Test that write operations are forbidden."""
        assert is_operation_forbidden(OperationType.WRITE) is True
        assert is_operation_allowed(OperationType.WRITE) is False

    def test_create_proposal_forbidden(self):
        """Test that proposal creation is forbidden."""
        assert is_operation_forbidden(OperationType.CREATE_PROPOSAL) is True
        assert is_operation_allowed(OperationType.CREATE_PROPOSAL) is False

    def test_all_allowed_operations_not_forbidden(self):
        """Test that all allowed operations are not forbidden."""
        for op in PRE_MUTATION_ZONE_RULES["allowed"]:
            assert is_operation_forbidden(op) is False

    def test_all_forbidden_operations_not_allowed(self):
        """Test that all forbidden operations are not allowed."""
        for op in PRE_MUTATION_ZONE_RULES["forbidden"]:
            assert is_operation_allowed(op) is False


# =============================================================================
# TEST CASES: 4-Stream Parallel Quality Checks
# =============================================================================

class TestFourStreamArchitecture:
    """Tests for 4-Stream parallel quality checks (audit.md Section 4)."""

    def test_build_stream_configuration(self):
        """Test Build Stream configuration."""
        assert BUILD_STREAM["name"] == "build"
        assert BUILD_STREAM["priority"] == StreamPriority.HIGH
        assert BUILD_STREAM["blocking"] is True
        assert len(BUILD_STREAM["checks"]) == 3

    def test_lint_stream_configuration(self):
        """Test Lint Stream configuration."""
        assert LINT_STREAM["name"] == "lint"
        assert LINT_STREAM["priority"] == StreamPriority.MEDIUM
        assert LINT_STREAM["blocking"] is True
        assert len(LINT_STREAM["checks"]) == 2

    def test_security_stream_configuration(self):
        """Test Security Stream configuration."""
        assert SECURITY_STREAM["name"] == "security"
        assert SECURITY_STREAM["priority"] == StreamPriority.HIGH
        assert SECURITY_STREAM["blocking"] is True
        assert len(SECURITY_STREAM["checks"]) == 4

    def test_documentation_stream_configuration(self):
        """Test Documentation Stream configuration."""
        assert DOCUMENTATION_STREAM["name"] == "documentation"
        assert DOCUMENTATION_STREAM["priority"] == StreamPriority.LOW
        assert DOCUMENTATION_STREAM["blocking"] is False
        assert len(DOCUMENTATION_STREAM["checks"]) == 3

    def test_all_streams_count(self):
        """Test that all 4 streams are defined."""
        assert len(ALL_STREAMS) == 4

    def test_get_stream_by_name(self):
        """Test stream retrieval by name."""
        build = get_stream_by_name("build")
        assert build is not None
        assert build["name"] == "build"

        unknown = get_stream_by_name("unknown")
        assert unknown is None

    def test_high_priority_streams_are_blocking(self):
        """Test that HIGH priority streams are blocking."""
        for stream in ALL_STREAMS:
            if stream["priority"] == StreamPriority.HIGH:
                assert stream["blocking"] is True

    def test_low_priority_streams_not_blocking(self):
        """Test that LOW priority streams are not blocking."""
        for stream in ALL_STREAMS:
            if stream["priority"] == StreamPriority.LOW:
                assert stream["blocking"] is False

    def test_security_checks_have_patterns(self):
        """Test that security checks have pattern definitions."""
        for check in SECURITY_STREAM["checks"]:
            assert "pattern" in check or "check" in check

    def test_build_checks_have_commands(self):
        """Test that build checks have command definitions."""
        for check in BUILD_STREAM["checks"]:
            assert "command" in check


# =============================================================================
# TEST CASES: Severity Level Classification
# =============================================================================

class TestSeverityClassification:
    """Tests for severity level classification (audit.md Section 7)."""

    def test_severity_priority_order(self):
        """Test severity priority order (CRITICAL highest)."""
        assert SEVERITY_PRIORITY.index(Severity.CRITICAL) < SEVERITY_PRIORITY.index(Severity.ERROR)
        assert SEVERITY_PRIORITY.index(Severity.ERROR) < SEVERITY_PRIORITY.index(Severity.HIGH)
        assert SEVERITY_PRIORITY.index(Severity.HIGH) < SEVERITY_PRIORITY.index(Severity.MEDIUM)
        assert SEVERITY_PRIORITY.index(Severity.MEDIUM) < SEVERITY_PRIORITY.index(Severity.WARNING)
        assert SEVERITY_PRIORITY.index(Severity.WARNING) < SEVERITY_PRIORITY.index(Severity.LOW)
        assert SEVERITY_PRIORITY.index(Severity.LOW) < SEVERITY_PRIORITY.index(Severity.INFO)

    def test_critical_action_block(self):
        """Test CRITICAL severity action is BLOCK."""
        action = get_severity_action(Severity.CRITICAL)
        assert action["action"] == "BLOCK"
        assert action["auto_fix"] is False
        assert action["requires_review"] is True

    def test_error_action_block(self):
        """Test ERROR severity action is BLOCK."""
        action = get_severity_action(Severity.ERROR)
        assert action["action"] == "BLOCK"
        assert action["auto_fix"] is False
        assert action["requires_review"] is True

    def test_high_action_warn(self):
        """Test HIGH severity action is WARN."""
        action = get_severity_action(Severity.HIGH)
        assert action["action"] == "WARN"
        assert action["auto_fix"] is False
        assert action["requires_review"] is True

    def test_medium_to_info_action_pass(self):
        """Test MEDIUM to INFO severity actions are PASS."""
        for severity in [Severity.MEDIUM, Severity.WARNING, Severity.LOW, Severity.INFO]:
            action = get_severity_action(severity)
            assert action["action"] == "PASS"
            assert action["auto_fix"] is True

    def test_is_severity_blocking(self):
        """Test severity blocking determination."""
        assert is_severity_blocking(Severity.CRITICAL) is True
        assert is_severity_blocking(Severity.ERROR) is True
        assert is_severity_blocking(Severity.HIGH) is False
        assert is_severity_blocking(Severity.WARNING) is False
        assert is_severity_blocking(Severity.INFO) is False

    def test_compare_severity(self):
        """Test severity comparison."""
        assert compare_severity(Severity.CRITICAL, Severity.ERROR) == 1
        assert compare_severity(Severity.ERROR, Severity.CRITICAL) == -1
        assert compare_severity(Severity.CRITICAL, Severity.CRITICAL) == 0
        assert compare_severity(Severity.INFO, Severity.CRITICAL) == -1

    def test_ruff_code_severity_mapping(self):
        """Test ruff code to severity mapping."""
        assert map_ruff_code_to_severity("E501") == Severity.ERROR
        assert map_ruff_code_to_severity("F401") == Severity.ERROR
        assert map_ruff_code_to_severity("W503") == Severity.WARNING
        assert map_ruff_code_to_severity("I001") == Severity.INFO
        assert map_ruff_code_to_severity("") == Severity.INFO
        assert map_ruff_code_to_severity("X999") == Severity.INFO  # Unknown


# =============================================================================
# TEST CASES: Filtering Logic
# =============================================================================

class TestFilteringLogic:
    """Tests for filtering logic (audit.md Section 8)."""

    def test_filter_empty_findings(self):
        """Test filtering empty findings list."""
        filtered = filter_findings([])
        assert filtered["blocking"] == []
        assert filtered["warning"] == []
        assert filtered["informational"] == []
        assert filtered["auto_fixable"] == []

    def test_filter_critical_to_blocking(self, sample_findings):
        """Test that CRITICAL findings go to blocking."""
        filtered = filter_findings(sample_findings)
        blocking_severities = [f.severity for f in filtered["blocking"]]
        assert Severity.CRITICAL in blocking_severities

    def test_filter_error_to_blocking(self, sample_findings):
        """Test that ERROR findings go to blocking."""
        filtered = filter_findings(sample_findings)
        blocking_severities = [f.severity for f in filtered["blocking"]]
        assert Severity.ERROR in blocking_severities

    def test_filter_warning_to_warning_category(self, sample_findings):
        """Test that WARNING findings go to warning category."""
        filtered = filter_findings(sample_findings)
        warning_severities = [f.severity for f in filtered["warning"]]
        assert Severity.WARNING in warning_severities

    def test_filter_info_to_informational(self, sample_findings):
        """Test that INFO findings go to informational."""
        filtered = filter_findings(sample_findings)
        info_severities = [f.severity for f in filtered["informational"]]
        assert Severity.INFO in info_severities

    def test_filter_auto_fixable(self, sample_findings):
        """Test auto-fixable findings collection."""
        filtered = filter_findings(sample_findings)
        assert len(filtered["auto_fixable"]) >= 1
        assert all(f.auto_fixable for f in filtered["auto_fixable"])

    def test_filter_with_exclusions(self, sample_findings):
        """Test filtering with code exclusions."""
        config = {"exclusions": ["F401"]}  # Exclude unused import
        filtered = filter_findings(sample_findings, config)
        codes = [f.code for f in filtered["warning"] if f.code]
        assert "F401" not in codes

    def test_filter_with_severity_override(self, sample_findings):
        """Test filtering with severity overrides."""
        config = {"severity_overrides": {"F401": "INFO"}}
        filtered = filter_findings(sample_findings, config)
        # F401 should now be in informational
        info_codes = [f.code for f in filtered["informational"] if f.code]
        assert "F401" in info_codes

    def test_filter_sorted_by_priority(self, sample_findings):
        """Test that filtered results are sorted by severity priority."""
        filtered = filter_findings(sample_findings)
        blocking = filtered["blocking"]
        if len(blocking) >= 2:
            # CRITICAL should come before ERROR
            severities = [f.severity for f in blocking]
            assert severities.index(Severity.CRITICAL) < severities.index(Severity.ERROR)

    def test_determine_blocking_status_with_critical(self):
        """Test blocking status determination with CRITICAL findings."""
        findings = [Finding(Severity.CRITICAL, "security", "test", "file.py", 1)]
        filtered = filter_findings(findings)
        is_blocking, reason = determine_blocking_status(filtered)
        assert is_blocking is True
        assert "CRITICAL" in reason

    def test_determine_blocking_status_with_error(self):
        """Test blocking status determination with ERROR findings."""
        findings = [Finding(Severity.ERROR, "lint", "test", "file.py", 1)]
        filtered = filter_findings(findings)
        is_blocking, reason = determine_blocking_status(filtered)
        assert is_blocking is True
        assert "ERROR" in reason

    def test_determine_blocking_status_no_blocking(self):
        """Test blocking status with no blocking findings."""
        findings = [Finding(Severity.WARNING, "lint", "test", "file.py", 1)]
        filtered = filter_findings(findings)
        is_blocking, reason = determine_blocking_status(filtered)
        assert is_blocking is False
        assert "No blocking" in reason


# =============================================================================
# TEST CASES: Stage C Quality Gate Enforcement
# =============================================================================

class TestQualityGateEnforcement:
    """Tests for Stage C Quality Gate enforcement (audit.md Section 11)."""

    def test_quality_gate_pass_no_issues(self, passing_audit_result):
        """Test quality gate passes with no blocking issues."""
        result = enforce_quality_gate(passing_audit_result)
        assert result.gate_status == GateStatus.PASS
        assert result.can_proceed is True
        assert len(result.blocking_rules) == 0

    def test_quality_gate_fail_critical(self, failing_audit_result):
        """Test quality gate fails with CRITICAL findings."""
        result = enforce_quality_gate(failing_audit_result)
        assert result.gate_status == GateStatus.FAIL
        assert result.can_proceed is False
        assert any(r["rule"] == "QG-001" for r in result.blocking_rules)

    def test_quality_gate_fail_error(self, failing_audit_result):
        """Test quality gate fails with ERROR findings."""
        result = enforce_quality_gate(failing_audit_result)
        assert any(r["rule"] == "QG-002" for r in result.blocking_rules)

    def test_quality_gate_fail_build(self, failing_audit_result):
        """Test quality gate fails with build failure."""
        result = enforce_quality_gate(failing_audit_result)
        assert any(r["rule"] == "QG-003" for r in result.blocking_rules)

    def test_quality_gate_warn_high_threshold(self):
        """Test quality gate warns when HIGH threshold exceeded."""
        audit_result = AuditResult(
            status=GateStatus.WARN,
            target="/lib/",
            findings=[Finding(Severity.HIGH, "lint", f"Issue {i}", "file.py", i) for i in range(6)],
            severity_counts={
                Severity.CRITICAL.value: 0,
                Severity.ERROR.value: 0,
                Severity.HIGH.value: 6,
                Severity.MEDIUM.value: 0,
                Severity.WARNING.value: 0,
                Severity.LOW.value: 0,
                Severity.INFO.value: 0,
            },
            stream_status={},
        )
        result = enforce_quality_gate(audit_result)
        assert any(w["rule"] == "QG-005" for w in result.warnings)
        assert result.can_proceed is True  # Warnings don't block

    def test_quality_gate_fail_security(self):
        """Test quality gate fails with security findings."""
        audit_result = AuditResult(
            status=GateStatus.FAIL,
            target="/lib/",
            findings=[Finding(Severity.CRITICAL, "security", "eval() usage", "file.py", 1)],
            severity_counts={
                Severity.CRITICAL.value: 1,
                Severity.ERROR.value: 0,
                Severity.HIGH.value: 0,
                Severity.MEDIUM.value: 0,
                Severity.WARNING.value: 0,
                Severity.LOW.value: 0,
                Severity.INFO.value: 0,
            },
            stream_status={},
        )
        result = enforce_quality_gate(audit_result)
        assert any(r["rule"] == "QG-006" for r in result.blocking_rules)

    def test_quality_gate_required_actions(self, failing_audit_result):
        """Test that required actions are populated."""
        result = enforce_quality_gate(failing_audit_result)
        assert len(result.required_actions) > 0
        assert all(isinstance(action, str) for action in result.required_actions)

    def test_quality_gate_rules_exist(self):
        """Test that all quality gate rules are defined."""
        expected_rules = ["QG-001", "QG-002", "QG-003", "QG-004", "QG-005", "QG-006"]
        for rule in expected_rules:
            assert rule in QUALITY_GATE_RULES


# =============================================================================
# TEST CASES: Boris Cherny Parallel Execution Pattern
# =============================================================================

class TestParallelExecutionPattern:
    """Tests for Boris Cherny parallel execution pattern (audit.md Section 5)."""

    def test_should_use_parallel_for_3_checks(self):
        """Test parallel execution enabled for 3+ checks."""
        assert should_use_parallel_execution(3) is True
        assert should_use_parallel_execution(4) is True
        assert should_use_parallel_execution(10) is True

    def test_should_not_use_parallel_for_2_checks(self):
        """Test parallel execution disabled for < 3 checks."""
        assert should_use_parallel_execution(2) is False
        assert should_use_parallel_execution(1) is False
        assert should_use_parallel_execution(0) is False

    def test_validate_parallel_execution_valid(self):
        """Test valid parallel execution configuration."""
        tasks = ["build", "lint", "security", "documentation"]
        assert validate_parallel_execution(tasks) is True

    def test_validate_parallel_execution_partial(self):
        """Test partial parallel execution (subset of streams)."""
        tasks = ["build", "lint"]
        assert validate_parallel_execution(tasks) is True

    def test_validate_parallel_execution_invalid_stream(self):
        """Test invalid stream name in parallel execution."""
        tasks = ["build", "lint", "unknown_stream"]
        assert validate_parallel_execution(tasks) is False

    def test_validate_parallel_max_exceeded(self):
        """Test max parallel tasks exceeded."""
        tasks = ["build", "lint", "security", "documentation", "extra"]
        assert validate_parallel_execution(tasks, max_parallel=4) is False

    def test_all_streams_independent(self):
        """Test that all 4 streams are independent (can run in parallel)."""
        stream_names = [s["name"] for s in ALL_STREAMS]
        assert validate_parallel_execution(stream_names) is True

    def test_stream_independence_no_dependencies(self):
        """Test streams have no inter-dependencies."""
        # Each stream should not reference other streams
        for stream in ALL_STREAMS:
            checks = stream.get("checks", [])
            for check in checks:
                command = check.get("command", "")
                # Streams should not depend on each other
                other_streams = [s["name"] for s in ALL_STREAMS if s["name"] != stream["name"]]
                for other in other_streams:
                    assert other not in command.lower()


# =============================================================================
# TEST CASES: Stream Aggregation and Synthesis
# =============================================================================

class TestStreamSynthesis:
    """Tests for stream result synthesis (audit.md Section 6)."""

    def test_aggregate_empty_results(self):
        """Test aggregation of empty stream results."""
        result = aggregate_stream_results([])
        assert result.status == GateStatus.PASS
        assert len(result.quality_checks) == 0
        assert len(result.findings) == 0

    def test_aggregate_all_passing(self, sample_stream_results):
        """Test aggregation when all streams pass."""
        result = aggregate_stream_results(sample_stream_results)
        assert result.status == GateStatus.PASS
        assert "build" in result.stream_status
        assert result.stream_status["build"] == "passed"

    def test_aggregate_collects_all_findings(self, sample_stream_results):
        """Test that aggregation collects all findings."""
        result = aggregate_stream_results(sample_stream_results)
        assert len(result.findings) == 2  # WARNING + INFO from fixtures

    def test_aggregate_collects_all_checks(self, sample_stream_results):
        """Test that aggregation collects all quality checks."""
        result = aggregate_stream_results(sample_stream_results)
        assert len(result.quality_checks) >= 2

    def test_aggregate_counts_severities(self, sample_stream_results):
        """Test severity counting in aggregation."""
        result = aggregate_stream_results(sample_stream_results)
        assert result.severity_counts[Severity.WARNING.value] == 1
        assert result.severity_counts[Severity.INFO.value] == 1

    def test_aggregate_fail_on_critical(self):
        """Test aggregation fails on CRITICAL finding."""
        streams = [
            StreamResult(
                name="security",
                status="failed",
                priority=StreamPriority.HIGH,
                blocking=True,
                findings=[Finding(Severity.CRITICAL, "security", "eval() found", "file.py", 1)],
            )
        ]
        result = aggregate_stream_results(streams)
        assert result.status == GateStatus.FAIL
        assert "CRITICAL" in result.recommendation

    def test_aggregate_fail_on_error(self):
        """Test aggregation fails on ERROR finding."""
        streams = [
            StreamResult(
                name="lint",
                status="failed",
                priority=StreamPriority.MEDIUM,
                blocking=True,
                findings=[Finding(Severity.ERROR, "lint", "Syntax error", "file.py", 1)],
            )
        ]
        result = aggregate_stream_results(streams)
        assert result.status == GateStatus.FAIL

    def test_aggregate_warn_on_high(self):
        """Test aggregation warns on HIGH finding."""
        streams = [
            StreamResult(
                name="security",
                status="passed",
                priority=StreamPriority.HIGH,
                blocking=True,
                findings=[Finding(Severity.HIGH, "security", "Potential issue", "file.py", 1)],
            )
        ]
        result = aggregate_stream_results(streams)
        assert result.status == GateStatus.WARN
        assert "HIGH" in result.recommendation


# =============================================================================
# TEST CASES: TodoWrite Integration
# =============================================================================

class TestTodoWriteIntegration:
    """Tests for TodoWrite integration (audit.md Section 9)."""

    def test_create_initial_todo_progress(self):
        """Test initial TodoWrite progress creation."""
        items = create_todo_progress("initial")
        assert len(items) == 7
        assert all(item.status == "pending" for item in items)

    def test_create_initialized_todo_progress(self):
        """Test TodoWrite progress after initialization."""
        items = create_todo_progress("initialized")
        assert items[0].status == "completed"
        assert items[1].status == "pending"

    def test_create_streams_deployed_progress(self):
        """Test TodoWrite progress after streams deployed."""
        items = create_todo_progress("streams_deployed")
        # First 5 items should be completed
        assert items[0].status == "completed"  # Initialize
        assert items[1].status == "completed"  # Build Stream
        assert items[2].status == "completed"  # Lint Stream
        assert items[3].status == "completed"  # Security Stream
        assert items[4].status == "completed"  # Documentation Stream
        assert items[5].status == "in_progress"  # Synthesize
        assert items[6].status == "pending"  # Generate report

    def test_create_completed_todo_progress(self):
        """Test TodoWrite progress when completed."""
        items = create_todo_progress("completed")
        assert all(item.status == "completed" for item in items)

    def test_todo_item_has_active_form(self):
        """Test that TodoItems have activeForm."""
        items = create_todo_progress("initial")
        for item in items:
            assert item.activeForm
            assert len(item.activeForm) > 0

    def test_todo_item_content_matches_active_form(self):
        """Test content and activeForm consistency."""
        items = create_todo_progress("initial")
        for item in items:
            # activeForm should be a present continuous form of content
            assert "ing" in item.activeForm or item.activeForm.startswith("Deploy") or "Generat" in item.activeForm


# =============================================================================
# TEST CASES: Edge Cases and Integration
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_audit_result(self):
        """Test handling of empty audit result."""
        result = AuditResult(
            status=GateStatus.PASS,
            target="/lib/",
            severity_counts={s.value: 0 for s in Severity},
        )
        gate_result = enforce_quality_gate(result)
        assert gate_result.gate_status == GateStatus.PASS
        assert gate_result.can_proceed is True

    def test_findings_with_null_code(self):
        """Test filtering findings with null code."""
        findings = [
            Finding(Severity.WARNING, "lint", "Test", "file.py", 1, None),
        ]
        filtered = filter_findings(findings)
        assert len(filtered["warning"]) == 1

    def test_severity_count_all_zero(self):
        """Test severity counts with all zeros."""
        counts = count_severities([])
        for severity in Severity:
            assert counts[severity.value] == 0

    def test_multiple_findings_same_severity(self):
        """Test counting multiple findings of same severity."""
        findings = [
            Finding(Severity.WARNING, "lint", f"Test {i}", "file.py", i)
            for i in range(5)
        ]
        counts = count_severities(findings)
        assert counts[Severity.WARNING.value] == 5

    def test_finding_without_auto_fixable(self):
        """Test finding without auto_fixable flag."""
        finding = Finding(Severity.ERROR, "lint", "Test", "file.py", 1)
        assert finding.auto_fixable is False

    def test_stream_with_no_checks(self):
        """Test stream result with no quality checks."""
        result = StreamResult(
            name="custom",
            status="passed",
            priority=StreamPriority.LOW,
            blocking=False,
        )
        assert len(result.quality_checks) == 0

    def test_quality_check_default_values(self):
        """Test QualityCheck default values."""
        check = QualityCheck("test", "passed", "echo test")
        assert check.output == ""
        assert check.duration_ms == 0
        assert check.exit_code == 0


class TestIntegrationScenarios:
    """Integration tests for realistic audit scenarios."""

    def test_full_audit_flow_passing(self, sample_stream_results):
        """Test complete audit flow with passing results."""
        # Step 1: Create progress
        todo_items = create_todo_progress("initial")
        assert len(todo_items) == 7

        # Step 2: Aggregate results
        audit_result = aggregate_stream_results(sample_stream_results)
        assert audit_result.status == GateStatus.PASS

        # Step 3: Enforce quality gate
        gate_result = enforce_quality_gate(audit_result)
        assert gate_result.gate_status == GateStatus.PASS
        assert gate_result.can_proceed is True

        # Step 4: Update progress
        final_items = create_todo_progress("completed")
        assert all(item.status == "completed" for item in final_items)

    def test_full_audit_flow_failing(self, failing_audit_result):
        """Test complete audit flow with failing results."""
        # Enforce quality gate
        gate_result = enforce_quality_gate(failing_audit_result)

        # Should fail with blocking rules
        assert gate_result.gate_status == GateStatus.FAIL
        assert gate_result.can_proceed is False
        assert len(gate_result.blocking_rules) > 0
        assert len(gate_result.required_actions) > 0

    def test_security_audit_with_eval_detection(self):
        """Test security audit detecting eval() usage."""
        security_finding = Finding(
            severity=Severity.CRITICAL,
            category="security",
            message="eval() usage detected - potential code injection",
            file="lib/utils.py",
            line=42,
            code="S307",
        )

        stream = StreamResult(
            name="security",
            status="failed",
            priority=StreamPriority.HIGH,
            blocking=True,
            findings=[security_finding],
        )

        result = aggregate_stream_results([stream])
        assert result.status == GateStatus.FAIL

        gate_result = enforce_quality_gate(result)
        assert gate_result.gate_status == GateStatus.FAIL
        assert any(r["rule"] == "QG-006" for r in gate_result.blocking_rules)

    def test_lint_audit_with_multiple_issues(self):
        """Test lint audit with multiple severity levels."""
        findings = [
            Finding(Severity.ERROR, "lint", "Undefined name 'foo'", "module.py", 10, "F821"),
            Finding(Severity.WARNING, "lint", "Unused import", "module.py", 1, "F401", True),
            Finding(Severity.INFO, "lint", "Import sorting", "module.py", 2, "I001", True),
        ]

        stream = StreamResult(
            name="lint",
            status="failed",
            priority=StreamPriority.MEDIUM,
            blocking=True,
            findings=findings,
        )

        result = aggregate_stream_results([stream])
        assert result.status == GateStatus.FAIL  # ERROR is blocking

        filtered = filter_findings(result.findings)
        assert len(filtered["blocking"]) == 1
        assert len(filtered["warning"]) == 1
        assert len(filtered["informational"]) == 1
        assert len(filtered["auto_fixable"]) == 2

    def test_parallel_execution_all_streams(self):
        """Test parallel execution of all 4 streams."""
        # Verify all streams can be executed in parallel
        stream_names = [s["name"] for s in ALL_STREAMS]
        assert validate_parallel_execution(stream_names) is True

        # Simulate parallel execution results
        results = []
        for stream in ALL_STREAMS:
            results.append(StreamResult(
                name=stream["name"],
                status="passed",
                priority=stream["priority"],
                blocking=stream["blocking"],
            ))

        # Aggregate parallel results
        final_result = aggregate_stream_results(results)
        assert final_result.status == GateStatus.PASS
        assert len(final_result.stream_status) == 4


# =============================================================================
# TEST CASES: Benchmark Tests for Performance
# =============================================================================

class TestBenchmarkPerformance:
    """Benchmark tests for audit performance (audit.md compliance)."""

    def test_filter_performance_large_dataset(self):
        """Test filtering performance with large number of findings."""
        # Generate 1000 findings
        findings = [
            Finding(
                severity=Severity(list(Severity)[i % 7].value),
                category="test",
                message=f"Finding {i}",
                file=f"file_{i % 100}.py",
                line=i,
                code=f"T{i:04d}",
                auto_fixable=i % 2 == 0,
            )
            for i in range(1000)
        ]

        import time
        start = time.time()
        filtered = filter_findings(findings)
        elapsed = time.time() - start

        # Should complete in under 100ms
        assert elapsed < 0.1

        # Verify correctness
        total = (
            len(filtered["blocking"]) +
            len(filtered["warning"]) +
            len(filtered["informational"])
        )
        assert total == 1000

    def test_severity_counting_performance(self):
        """Test severity counting performance."""
        findings = [
            Finding(Severity.WARNING, "test", f"Test {i}", "file.py", i)
            for i in range(10000)
        ]

        start = time.time()
        counts = count_severities(findings)
        elapsed = time.time() - start

        assert elapsed < 0.1
        assert counts[Severity.WARNING.value] == 10000

    def test_aggregation_performance(self):
        """Test stream aggregation performance."""
        # Create 100 stream results
        streams = [
            StreamResult(
                name=f"stream_{i}",
                status="passed",
                priority=StreamPriority.MEDIUM,
                blocking=False,
                quality_checks=[QualityCheck(f"check_{i}", "passed", "cmd", "", 100, 0)],
                findings=[Finding(Severity.INFO, "test", f"Finding {i}", "file.py", i)],
            )
            for i in range(100)
        ]

        start = time.time()
        result = aggregate_stream_results(streams)
        elapsed = time.time() - start

        assert elapsed < 0.1
        assert len(result.quality_checks) == 100
        assert len(result.findings) == 100


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
