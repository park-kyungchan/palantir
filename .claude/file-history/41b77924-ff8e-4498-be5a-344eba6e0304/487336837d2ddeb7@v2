"""
Orion ODA v3.0 - Security Validator
====================================

Security validation hook system for PAI.

Provides security checks that can be executed as pre-hooks
to validate commands, inputs, and actions before execution.

ObjectTypes:
    - SecurityRule: A single security validation rule
    - SecurityCheckResult: Result of a security check

ActionTypes:
    - ValidateSecurityAction: Execute security validation

Reference: PAI hook system security patterns
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional, Pattern
import re

from pydantic import Field, field_validator

from lib.oda.ontology.ontology_types import OntologyObject, utc_now
from lib.oda.ontology.registry import register_object_type


# =============================================================================
# ENUMS
# =============================================================================


class SecurityLevel(str, Enum):
    """Security severity level for rules and violations."""

    INFO = "info"           # Informational, no action required
    WARNING = "warning"     # Potential issue, proceed with caution
    CRITICAL = "critical"   # Must be blocked, security violation
    BLOCKED = "blocked"     # Always blocked, no override


class RuleCategory(str, Enum):
    """Categories of security rules."""

    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    CREDENTIAL_EXPOSURE = "credential_exposure"
    DESTRUCTIVE_OPERATION = "destructive_operation"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    CUSTOM = "custom"


# =============================================================================
# SECURITY RULE OBJECTTYPE
# =============================================================================


@register_object_type
class SecurityRule(OntologyObject):
    """
    A security validation rule.

    Defines a pattern to detect and the action to take when detected.

    Attributes:
        rule_id: Unique identifier for the rule
        name: Human-readable name
        category: Rule category
        pattern: Regex pattern to match
        level: Security severity level
        description: Detailed description
        remediation: Suggested fix
        enabled: Whether rule is active
    """

    rule_id: str = Field(
        ...,
        description="Unique rule identifier (e.g., 'CMD-001')"
    )

    name: str = Field(
        ...,
        description="Human-readable rule name"
    )

    category: RuleCategory = Field(
        default=RuleCategory.CUSTOM,
        description="Rule category for grouping"
    )

    pattern: str = Field(
        ...,
        description="Regex pattern to detect violations"
    )

    level: SecurityLevel = Field(
        default=SecurityLevel.WARNING,
        description="Severity level"
    )

    description: str = Field(
        default="",
        description="Detailed description of what this rule detects"
    )

    remediation: str = Field(
        default="",
        description="Suggested remediation steps"
    )

    enabled: bool = Field(
        default=True,
        description="Whether this rule is active"
    )

    applies_to: List[str] = Field(
        default_factory=lambda: ["*"],
        description="Tools/contexts this rule applies to"
    )

    @field_validator('pattern')
    @classmethod
    def validate_pattern(cls, v: str) -> str:
        """Validate that pattern is a valid regex."""
        try:
            re.compile(v)
            return v
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")

    def matches(self, content: str) -> bool:
        """Check if content matches this rule's pattern."""
        if not self.enabled:
            return False
        return bool(re.search(self.pattern, content, re.IGNORECASE))


# =============================================================================
# SECURITY CHECK RESULT
# =============================================================================


@register_object_type
class SecurityCheckResult(OntologyObject):
    """
    Result of a security validation check.

    Records the outcome of running security rules against input.

    Attributes:
        input_hash: Hash of checked input (for audit without storing sensitive data)
        rules_checked: Number of rules evaluated
        violations: List of triggered rule IDs
        highest_level: Most severe violation level
        blocked: Whether the input was blocked
        details: Detailed findings
        checked_at: Timestamp of check
    """

    input_hash: str = Field(
        ...,
        description="SHA-256 hash of the input (privacy-preserving audit)"
    )

    input_preview: str = Field(
        default="",
        description="First 100 chars of input (for debugging)",
        max_length=100
    )

    rules_checked: int = Field(
        default=0,
        description="Number of rules evaluated"
    )

    violations: List[str] = Field(
        default_factory=list,
        description="List of triggered rule IDs"
    )

    highest_level: SecurityLevel = Field(
        default=SecurityLevel.INFO,
        description="Most severe violation level found"
    )

    blocked: bool = Field(
        default=False,
        description="Whether input was blocked"
    )

    details: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Detailed findings for each violation"
    )

    checked_at: datetime = Field(
        default_factory=utc_now,
        description="When the check was performed"
    )

    duration_ms: float = Field(
        default=0.0,
        description="Check duration in milliseconds"
    )

    @property
    def is_clean(self) -> bool:
        """Check if no violations were found."""
        return len(self.violations) == 0

    @property
    def summary(self) -> str:
        """Generate human-readable summary."""
        if self.is_clean:
            return f"CLEAN: {self.rules_checked} rules checked, no violations"
        return (
            f"{self.highest_level.value.upper()}: "
            f"{len(self.violations)} violations in {self.rules_checked} rules"
        )


# =============================================================================
# SECURITY VALIDATOR
# =============================================================================


class SecurityValidator:
    """
    Security validation orchestrator.

    Manages security rules and executes validation checks.

    Usage:
        ```python
        validator = SecurityValidator()

        # Add rules
        validator.add_rule(SecurityRule(
            rule_id="CMD-001",
            name="Dangerous rm command",
            pattern=r"rm\\s+-rf\\s+/",
            level=SecurityLevel.BLOCKED,
        ))

        # Validate input
        result = validator.validate("rm -rf /home/user")
        if result.blocked:
            print(f"Blocked: {result.summary}")
        ```
    """

    # Default rules (commonly dangerous patterns)
    DEFAULT_RULES: ClassVar[List[Dict[str, Any]]] = [
        {
            "rule_id": "CMD-001",
            "name": "Root directory deletion",
            "category": RuleCategory.DESTRUCTIVE_OPERATION,
            "pattern": r"rm\s+(-[rf]+\s+)*(/|/\*)",
            "level": SecurityLevel.BLOCKED,
            "description": "Attempts to delete root directory",
        },
        {
            "rule_id": "CMD-002",
            "name": "Sudo rm",
            "category": RuleCategory.DESTRUCTIVE_OPERATION,
            "pattern": r"sudo\s+rm\s+-rf",
            "level": SecurityLevel.CRITICAL,
            "description": "Privileged recursive deletion",
        },
        {
            "rule_id": "CMD-003",
            "name": "Chmod 777",
            "category": RuleCategory.PRIVILEGE_ESCALATION,
            "pattern": r"chmod\s+777",
            "level": SecurityLevel.WARNING,
            "description": "World-writable permissions",
        },
        {
            "rule_id": "CRED-001",
            "name": "API key exposure",
            "category": RuleCategory.CREDENTIAL_EXPOSURE,
            "pattern": r"(api[_-]?key|secret|password)\s*[=:]\s*['\"][^'\"]+['\"]",
            "level": SecurityLevel.CRITICAL,
            "description": "Potential credential in command",
        },
        {
            "rule_id": "PATH-001",
            "name": "Path traversal",
            "category": RuleCategory.PATH_TRAVERSAL,
            "pattern": r"\.\./\.\./",
            "level": SecurityLevel.WARNING,
            "description": "Multiple directory traversals",
        },
        {
            "rule_id": "SQL-001",
            "name": "SQL DROP TABLE",
            "category": RuleCategory.DESTRUCTIVE_OPERATION,
            "pattern": r"DROP\s+TABLE",
            "level": SecurityLevel.BLOCKED,
            "description": "SQL table deletion",
        },
        {
            "rule_id": "EXEC-001",
            "name": "Python eval/exec",
            "category": RuleCategory.COMMAND_INJECTION,
            "pattern": r"(eval|exec)\s*\(",
            "level": SecurityLevel.CRITICAL,
            "description": "Dynamic code execution",
        },
    ]

    def __init__(self, load_defaults: bool = True):
        """
        Initialize security validator.

        Args:
            load_defaults: Whether to load default security rules
        """
        self._rules: Dict[str, SecurityRule] = {}

        if load_defaults:
            self._load_default_rules()

    def _load_default_rules(self) -> None:
        """Load default security rules."""
        for rule_data in self.DEFAULT_RULES:
            rule = SecurityRule(**rule_data)
            self._rules[rule.rule_id] = rule

    def add_rule(self, rule: SecurityRule) -> None:
        """
        Add a security rule.

        Args:
            rule: SecurityRule to add
        """
        self._rules[rule.rule_id] = rule

    def remove_rule(self, rule_id: str) -> bool:
        """
        Remove a security rule.

        Args:
            rule_id: ID of rule to remove

        Returns:
            True if rule was removed, False if not found
        """
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    def get_rule(self, rule_id: str) -> Optional[SecurityRule]:
        """Get a rule by ID."""
        return self._rules.get(rule_id)

    def list_rules(self) -> List[SecurityRule]:
        """List all registered rules."""
        return list(self._rules.values())

    def validate(
        self,
        content: str,
        context: Optional[str] = None,
    ) -> SecurityCheckResult:
        """
        Validate content against all security rules.

        Args:
            content: Content to validate
            context: Optional context (e.g., tool name) for filtering rules

        Returns:
            SecurityCheckResult with findings
        """
        import hashlib
        start_time = utc_now()

        # Create result
        result = SecurityCheckResult(
            input_hash=hashlib.sha256(content.encode()).hexdigest(),
            input_preview=content[:100] if content else "",
            rules_checked=0,
        )

        violations = []
        details = []
        highest_level = SecurityLevel.INFO

        # Check each rule
        for rule in self._rules.values():
            if not rule.enabled:
                continue

            # Check if rule applies to this context
            if context and rule.applies_to != ["*"]:
                if context not in rule.applies_to:
                    continue

            result.rules_checked += 1

            if rule.matches(content):
                violations.append(rule.rule_id)
                details.append({
                    "rule_id": rule.rule_id,
                    "name": rule.name,
                    "level": rule.level.value,
                    "description": rule.description,
                    "remediation": rule.remediation,
                })

                # Track highest severity
                if rule.level == SecurityLevel.BLOCKED:
                    highest_level = SecurityLevel.BLOCKED
                elif rule.level == SecurityLevel.CRITICAL and highest_level != SecurityLevel.BLOCKED:
                    highest_level = SecurityLevel.CRITICAL
                elif rule.level == SecurityLevel.WARNING and highest_level == SecurityLevel.INFO:
                    highest_level = SecurityLevel.WARNING

        # Update result
        result.violations = violations
        result.details = details
        result.highest_level = highest_level
        result.blocked = highest_level == SecurityLevel.BLOCKED
        result.duration_ms = (utc_now() - start_time).total_seconds() * 1000

        return result


# =============================================================================
# ACTION TYPE
# =============================================================================


class ValidateSecurityAction:
    """
    Action to execute security validation.

    Non-hazardous action that validates input against security rules.
    """

    api_name: ClassVar[str] = "validate_security"
    display_name: ClassVar[str] = "Validate Security"
    description: ClassVar[str] = "Run security validation on input content"
    is_hazardous: ClassVar[bool] = False

    def __init__(
        self,
        content: str,
        context: Optional[str] = None,
        validator: Optional[SecurityValidator] = None,
    ):
        """
        Initialize validation action.

        Args:
            content: Content to validate
            context: Optional context for rule filtering
            validator: Optional custom validator (uses default if not provided)
        """
        self.content = content
        self.context = context
        self.validator = validator or SecurityValidator()

    def execute(self) -> SecurityCheckResult:
        """Execute security validation."""
        return self.validator.validate(self.content, self.context)
