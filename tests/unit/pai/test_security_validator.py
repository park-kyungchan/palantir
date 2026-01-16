"""
Unit Tests for PAI Security Validator Module
=============================================

Comprehensive tests for the security validation hook system.

Tests cover:
    - SecurityLevel enum
    - RuleCategory enum
    - SecurityRule ObjectType
    - SecurityCheckResult ObjectType
    - SecurityValidator class
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

import pytest

# Handle import errors gracefully
# Note: We import directly from the module file to avoid __init__.py issues
try:
    # First attempt: standard import
    from lib.oda.pai.hooks.security_validator import (
        SecurityLevel,
        RuleCategory,
        SecurityRule,
        SecurityCheckResult,
        SecurityValidator,
        ValidateSecurityAction,
    )
    SECURITY_VALIDATOR_AVAILABLE = True
except ImportError:
    try:
        # Second attempt: direct module import (bypasses __init__.py)
        import importlib.util
        import sys
        from pathlib import Path

        # Find the module file
        _module_path = Path(__file__).parents[3] / "lib/oda/pai/hooks/security_validator.py"
        if _module_path.exists():
            _spec = importlib.util.spec_from_file_location(
                "security_validator_direct",
                str(_module_path)
            )
            _mod = importlib.util.module_from_spec(_spec)
            sys.modules["security_validator_direct"] = _mod
            _spec.loader.exec_module(_mod)

            # Extract the classes
            SecurityLevel = _mod.SecurityLevel
            RuleCategory = _mod.RuleCategory
            SecurityRule = _mod.SecurityRule
            SecurityCheckResult = _mod.SecurityCheckResult
            SecurityValidator = _mod.SecurityValidator
            ValidateSecurityAction = _mod.ValidateSecurityAction
            SECURITY_VALIDATOR_AVAILABLE = True
        else:
            raise ImportError(f"Module not found at {_module_path}")
    except Exception:
        SECURITY_VALIDATOR_AVAILABLE = False
        # Create placeholder classes to avoid NameError during collection
        # These will never be used because tests are skipped
        class SecurityLevel:  # type: ignore[no-redef]
            INFO = "info"
            WARNING = "warning"
            CRITICAL = "critical"
            BLOCKED = "blocked"

        class RuleCategory:  # type: ignore[no-redef]
            COMMAND_INJECTION = "command_injection"
            PATH_TRAVERSAL = "path_traversal"
            CREDENTIAL_EXPOSURE = "credential_exposure"
            DESTRUCTIVE_OPERATION = "destructive_operation"
            PRIVILEGE_ESCALATION = "privilege_escalation"
            DATA_EXFILTRATION = "data_exfiltration"
            CUSTOM = "custom"

        class SecurityRule:  # type: ignore[no-redef]
            pass

        class SecurityCheckResult:  # type: ignore[no-redef]
            pass

        class SecurityValidator:  # type: ignore[no-redef]
            pass

        class ValidateSecurityAction:  # type: ignore[no-redef]
            pass

# Skip all tests if module not available
pytestmark = pytest.mark.skipif(
    not SECURITY_VALIDATOR_AVAILABLE,
    reason="Security validator module requires Pydantic to be installed"
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def validator() -> SecurityValidator:
    """Security validator with default rules."""
    return SecurityValidator(load_defaults=True)


@pytest.fixture
def empty_validator() -> SecurityValidator:
    """Security validator without default rules."""
    return SecurityValidator(load_defaults=False)


@pytest.fixture
def sample_rule() -> SecurityRule:
    """Sample security rule for testing."""
    return SecurityRule(
        rule_id="TEST-001",
        name="Test Rule",
        category=RuleCategory.CUSTOM,
        pattern=r"test_pattern",
        level=SecurityLevel.WARNING,
        description="A test security rule",
        remediation="Remove test_pattern from input",
    )


@pytest.fixture
def blocked_rule() -> SecurityRule:
    """A rule with BLOCKED severity."""
    return SecurityRule(
        rule_id="BLOCK-001",
        name="Blocked Pattern",
        category=RuleCategory.DESTRUCTIVE_OPERATION,
        pattern=r"dangerous_action",
        level=SecurityLevel.BLOCKED,
        description="This pattern is always blocked",
    )


# =============================================================================
# SECURITY LEVEL ENUM TESTS
# =============================================================================


class TestSecurityLevelEnum:
    """Tests for SecurityLevel enum."""

    def test_info_level_exists(self):
        """INFO level should exist."""
        assert SecurityLevel.INFO.value == "info"

    def test_warning_level_exists(self):
        """WARNING level should exist."""
        assert SecurityLevel.WARNING.value == "warning"

    def test_critical_level_exists(self):
        """CRITICAL level should exist."""
        assert SecurityLevel.CRITICAL.value == "critical"

    def test_blocked_level_exists(self):
        """BLOCKED level should exist."""
        assert SecurityLevel.BLOCKED.value == "blocked"

    def test_all_levels_are_string_enum(self):
        """All levels should be string enum members."""
        for level in SecurityLevel:
            assert isinstance(level.value, str)
            assert isinstance(level, str)


# =============================================================================
# RULE CATEGORY ENUM TESTS
# =============================================================================


class TestRuleCategoryEnum:
    """Tests for RuleCategory enum."""

    @pytest.mark.parametrize("category,expected_value", [
        (RuleCategory.COMMAND_INJECTION, "command_injection"),
        (RuleCategory.PATH_TRAVERSAL, "path_traversal"),
        (RuleCategory.CREDENTIAL_EXPOSURE, "credential_exposure"),
        (RuleCategory.DESTRUCTIVE_OPERATION, "destructive_operation"),
        (RuleCategory.PRIVILEGE_ESCALATION, "privilege_escalation"),
        (RuleCategory.DATA_EXFILTRATION, "data_exfiltration"),
        (RuleCategory.CUSTOM, "custom"),
    ])
    def test_category_values(self, category: RuleCategory, expected_value: str):
        """Each category should have correct value."""
        assert category.value == expected_value

    def test_category_count(self):
        """Should have exactly 7 categories."""
        assert len(RuleCategory) == 7


# =============================================================================
# SECURITY RULE TESTS
# =============================================================================


class TestSecurityRule:
    """Tests for SecurityRule ObjectType."""

    def test_required_fields(self):
        """Rule requires rule_id, name, and pattern."""
        rule = SecurityRule(
            rule_id="RULE-001",
            name="Minimal Rule",
            pattern=r"some_pattern",
        )
        assert rule.rule_id == "RULE-001"
        assert rule.name == "Minimal Rule"
        assert rule.pattern == r"some_pattern"

    def test_default_values(self):
        """Rule should have sensible defaults."""
        rule = SecurityRule(
            rule_id="RULE-001",
            name="Test",
            pattern=r"test",
        )
        assert rule.category == RuleCategory.CUSTOM
        assert rule.level == SecurityLevel.WARNING
        assert rule.description == ""
        assert rule.remediation == ""
        assert rule.enabled is True
        assert rule.applies_to == ["*"]

    def test_validate_pattern_valid_regex(self):
        """Valid regex patterns should be accepted."""
        rule = SecurityRule(
            rule_id="RULE-001",
            name="Test",
            pattern=r"rm\s+-rf\s+/",
        )
        assert rule.pattern == r"rm\s+-rf\s+/"

    def test_validate_pattern_invalid_regex(self):
        """Invalid regex patterns should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            SecurityRule(
                rule_id="RULE-001",
                name="Test",
                pattern=r"[invalid(",
            )

    def test_matches_positive(self, sample_rule: SecurityRule):
        """matches() should return True for matching content."""
        assert sample_rule.matches("contains test_pattern here")

    def test_matches_negative(self, sample_rule: SecurityRule):
        """matches() should return False for non-matching content."""
        assert not sample_rule.matches("no match here")

    def test_matches_case_insensitive(self):
        """matches() should be case-insensitive."""
        rule = SecurityRule(
            rule_id="RULE-001",
            name="Test",
            pattern=r"dangerous",
        )
        assert rule.matches("DANGEROUS command")
        assert rule.matches("DaNgErOuS command")

    def test_matches_disabled_rule(self, sample_rule: SecurityRule):
        """Disabled rules should never match."""
        sample_rule.enabled = False
        assert not sample_rule.matches("contains test_pattern here")


# =============================================================================
# SECURITY CHECK RESULT TESTS
# =============================================================================


class TestSecurityCheckResult:
    """Tests for SecurityCheckResult ObjectType."""

    def test_required_fields(self):
        """Result requires input_hash."""
        result = SecurityCheckResult(
            input_hash="abc123def456"
        )
        assert result.input_hash == "abc123def456"

    def test_default_values(self):
        """Result should have sensible defaults."""
        result = SecurityCheckResult(input_hash="test_hash")
        assert result.input_preview == ""
        assert result.rules_checked == 0
        assert result.violations == []
        assert result.highest_level == SecurityLevel.INFO
        assert result.blocked is False
        assert result.details == []
        assert result.duration_ms == 0.0
        assert isinstance(result.checked_at, datetime)

    def test_is_clean_property_true(self):
        """is_clean should be True when no violations."""
        result = SecurityCheckResult(
            input_hash="hash",
            violations=[],
        )
        assert result.is_clean is True

    def test_is_clean_property_false(self):
        """is_clean should be False when violations exist."""
        result = SecurityCheckResult(
            input_hash="hash",
            violations=["RULE-001"],
        )
        assert result.is_clean is False

    def test_summary_clean(self):
        """summary should indicate clean status."""
        result = SecurityCheckResult(
            input_hash="hash",
            rules_checked=10,
            violations=[],
        )
        assert "CLEAN" in result.summary
        assert "10 rules checked" in result.summary

    def test_summary_with_violations(self):
        """summary should show violation count and level."""
        result = SecurityCheckResult(
            input_hash="hash",
            rules_checked=10,
            violations=["RULE-001", "RULE-002"],
            highest_level=SecurityLevel.CRITICAL,
        )
        assert "CRITICAL" in result.summary
        assert "2 violations" in result.summary


# =============================================================================
# SECURITY VALIDATOR TESTS
# =============================================================================


class TestSecurityValidator:
    """Tests for SecurityValidator class."""

    def test_init_with_defaults(self, validator: SecurityValidator):
        """Validator should load default rules by default."""
        rules = validator.list_rules()
        assert len(rules) > 0
        # Check for known default rules
        rule_ids = [r.rule_id for r in rules]
        assert "CMD-001" in rule_ids
        assert "CMD-002" in rule_ids

    def test_init_without_defaults(self, empty_validator: SecurityValidator):
        """Validator can be initialized without default rules."""
        rules = empty_validator.list_rules()
        assert len(rules) == 0

    def test_add_rule(self, empty_validator: SecurityValidator, sample_rule: SecurityRule):
        """add_rule should add a rule to the validator."""
        empty_validator.add_rule(sample_rule)
        assert len(empty_validator.list_rules()) == 1
        assert empty_validator.get_rule("TEST-001") is sample_rule

    def test_add_rule_replaces_existing(self, empty_validator: SecurityValidator):
        """Adding rule with same ID should replace existing."""
        rule1 = SecurityRule(
            rule_id="RULE-001",
            name="Original",
            pattern=r"original",
        )
        rule2 = SecurityRule(
            rule_id="RULE-001",
            name="Replacement",
            pattern=r"replacement",
        )
        empty_validator.add_rule(rule1)
        empty_validator.add_rule(rule2)

        assert len(empty_validator.list_rules()) == 1
        assert empty_validator.get_rule("RULE-001").name == "Replacement"

    def test_remove_rule_existing(self, validator: SecurityValidator):
        """remove_rule should return True and remove existing rule."""
        assert validator.get_rule("CMD-001") is not None
        result = validator.remove_rule("CMD-001")
        assert result is True
        assert validator.get_rule("CMD-001") is None

    def test_remove_rule_nonexistent(self, validator: SecurityValidator):
        """remove_rule should return False for nonexistent rule."""
        result = validator.remove_rule("NONEXISTENT-999")
        assert result is False

    def test_validate_clean_content(self, empty_validator: SecurityValidator):
        """validate should return clean result for safe content."""
        result = empty_validator.validate("echo hello world")
        assert result.is_clean
        assert result.blocked is False

    def test_validate_returns_security_check_result(self, validator: SecurityValidator):
        """validate should return SecurityCheckResult instance."""
        result = validator.validate("safe content")
        assert isinstance(result, SecurityCheckResult)
        assert result.input_hash is not None
        assert result.rules_checked > 0

    def test_validate_input_hash_generated(self, validator: SecurityValidator):
        """validate should generate SHA-256 hash of input."""
        result = validator.validate("test content")
        # SHA-256 hashes are 64 characters
        assert len(result.input_hash) == 64

    def test_validate_input_preview_truncated(self, validator: SecurityValidator):
        """validate should truncate input_preview to 100 chars."""
        long_content = "x" * 200
        result = validator.validate(long_content)
        assert len(result.input_preview) == 100


# =============================================================================
# DANGEROUS PATTERN DETECTION TESTS
# =============================================================================


class TestDangerousPatternDetection:
    """Tests for detection of dangerous patterns."""

    @pytest.mark.parametrize("dangerous_input,expected_blocked", [
        ("rm -rf /", True),
        ("rm -rf /*", True),
        ("rm -r /", True),
        ("rm -f /", True),
    ])
    def test_root_deletion_blocked(
        self,
        validator: SecurityValidator,
        dangerous_input: str,
        expected_blocked: bool,
    ):
        """Root directory deletion attempts should be blocked."""
        result = validator.validate(dangerous_input)
        assert result.blocked == expected_blocked
        assert "CMD-001" in result.violations

    def test_sudo_rm_rf_detected(self, validator: SecurityValidator):
        """sudo rm -rf should trigger CRITICAL level."""
        result = validator.validate("sudo rm -rf /home/user")
        assert "CMD-002" in result.violations
        assert result.highest_level in [SecurityLevel.CRITICAL, SecurityLevel.BLOCKED]

    def test_chmod_777_detected(self, validator: SecurityValidator):
        """chmod 777 should trigger WARNING level."""
        result = validator.validate("chmod 777 /var/www")
        assert "CMD-003" in result.violations

    def test_api_key_exposure_detected(self, validator: SecurityValidator):
        """API key in content should be detected."""
        result = validator.validate("api_key = 'secret123'")
        assert "CRED-001" in result.violations
        assert result.highest_level == SecurityLevel.CRITICAL

    def test_path_traversal_detected(self, validator: SecurityValidator):
        """Path traversal patterns should be detected."""
        result = validator.validate("cat ../../etc/passwd")
        assert "PATH-001" in result.violations

    def test_sql_drop_table_blocked(self, validator: SecurityValidator):
        """DROP TABLE should be blocked."""
        result = validator.validate("DROP TABLE users")
        assert "SQL-001" in result.violations
        assert result.blocked is True

    def test_eval_exec_detected(self, validator: SecurityValidator):
        """Python eval/exec should trigger CRITICAL."""
        result = validator.validate("eval(user_input)")
        assert "EXEC-001" in result.violations

        result2 = validator.validate("exec(code)")
        assert "EXEC-001" in result2.violations

    def test_safe_content_passes(self, validator: SecurityValidator):
        """Safe content should pass validation."""
        safe_commands = [
            "ls -la",
            "git status",
            "python script.py",
            "cat README.md",
            "pip install package",
        ]
        for cmd in safe_commands:
            result = validator.validate(cmd)
            assert result.is_clean, f"'{cmd}' should be clean but got violations: {result.violations}"


# =============================================================================
# CONTEXT FILTERING TESTS
# =============================================================================


class TestContextFiltering:
    """Tests for rule context filtering."""

    def test_context_specific_rule(self, empty_validator: SecurityValidator):
        """Rules with specific applies_to should only match in that context."""
        rule = SecurityRule(
            rule_id="CONTEXT-001",
            name="Bash Only Rule",
            pattern=r"dangerous",
            applies_to=["bash"],
        )
        empty_validator.add_rule(rule)

        # Should match in bash context
        result_bash = empty_validator.validate("dangerous command", context="bash")
        assert "CONTEXT-001" in result_bash.violations

        # Should not match in other context
        result_other = empty_validator.validate("dangerous command", context="python")
        assert "CONTEXT-001" not in result_other.violations

    def test_wildcard_applies_to_all(self, empty_validator: SecurityValidator):
        """Rules with applies_to=['*'] should match in any context."""
        rule = SecurityRule(
            rule_id="WILD-001",
            name="Wildcard Rule",
            pattern=r"pattern",
            applies_to=["*"],
        )
        empty_validator.add_rule(rule)

        for ctx in ["bash", "python", "sql", None]:
            result = empty_validator.validate("pattern here", context=ctx)
            assert "WILD-001" in result.violations


# =============================================================================
# VALIDATE SECURITY ACTION TESTS
# =============================================================================


class TestValidateSecurityAction:
    """Tests for ValidateSecurityAction."""

    def test_action_with_default_validator(self):
        """Action should create default validator if none provided."""
        action = ValidateSecurityAction(content="rm -rf /")
        result = action.execute()
        assert isinstance(result, SecurityCheckResult)
        assert result.blocked is True

    def test_action_with_custom_validator(self, empty_validator: SecurityValidator):
        """Action should use provided validator."""
        action = ValidateSecurityAction(
            content="dangerous",
            validator=empty_validator,
        )
        result = action.execute()
        # Empty validator has no rules, so content should be clean
        assert result.is_clean

    def test_action_with_context(self, validator: SecurityValidator):
        """Action should pass context to validator."""
        action = ValidateSecurityAction(
            content="safe content",
            context="bash",
            validator=validator,
        )
        result = action.execute()
        assert isinstance(result, SecurityCheckResult)

    def test_action_class_attributes(self):
        """Action should have correct class attributes."""
        assert ValidateSecurityAction.api_name == "validate_security"
        assert ValidateSecurityAction.display_name == "Validate Security"
        assert ValidateSecurityAction.is_hazardous is False
