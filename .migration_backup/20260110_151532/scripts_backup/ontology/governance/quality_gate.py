"""
ODA V3.0 - Code Quality Gate
=============================

Registration-time validation for ActionType implementations.
Enforces code quality standards at ODA level.

Usage:
    from scripts.ontology.governance import CodeQualityGate
    
    violations = CodeQualityGate.validate_action_class(MyAction)
    if violations.has_errors:
        raise GovernanceError(violations)
"""

from __future__ import annotations

import ast
import inspect
import logging
import re
from typing import Any, Callable, ClassVar, Dict, List, Optional, Type, get_type_hints

from scripts.ontology.governance.violations import (
    GovernanceError,
    Violation,
    ViolationReport,
    ViolationSeverity,
    ViolationType,
)

logger = logging.getLogger(__name__)


class CodeQualityGate:
    """
    Validates ActionType implementations at registration time.
    
    Rules:
    1. Must have docstring
    2. Must have return type hints
    3. No bare exception catching (unless retry pattern)
    4. Consistent return patterns
    5. Valid api_name format
    """
    
    # Allowed patterns in exception handling (for retry logic)
    ALLOWED_EXCEPTION_PATTERNS = [
        "ConcurrencyError",
        "StaleObjectError",
        "ConnectionError",
        "TimeoutError",
    ]
    
    @classmethod
    def validate_action_class(
        cls,
        action_cls: Type,
        strict: bool = False
    ) -> ViolationReport:
        """
        Validate an ActionType class against quality standards.
        
        Args:
            action_cls: The ActionType subclass to validate
            strict: If True, warnings become errors
            
        Returns:
            ViolationReport with all found violations
        """
        report = ViolationReport(target=getattr(action_cls, 'api_name', action_cls.__name__))
        
        # Rule 1: Docstring check
        cls._check_docstring(action_cls, report, strict)
        
        # Rule 2: Type hints check
        cls._check_type_hints(action_cls, report, strict)
        
        # Rule 3: Exception handling check
        cls._check_exception_handling(action_cls, report, strict)
        
        # Rule 4: api_name format check
        cls._check_api_name(action_cls, report, strict)
        
        # Rule 5: submission_criteria presence
        cls._check_submission_criteria(action_cls, report, strict)
        
        return report
    
    @classmethod
    def _check_docstring(
        cls,
        action_cls: Type,
        report: ViolationReport,
        strict: bool
    ) -> None:
        """Check that class and apply_edits have docstrings."""
        # Class docstring
        if not action_cls.__doc__ or len(action_cls.__doc__.strip()) < 10:
            report.add(Violation(
                type=ViolationType.MISSING_DOCSTRING,
                severity=ViolationSeverity.ERROR if strict else ViolationSeverity.WARNING,
                location=f"{action_cls.__name__}",
                message="ActionType must have a descriptive docstring",
                suggestion="Add a docstring describing the action's purpose and parameters",
            ))
        
        # apply_edits docstring
        if hasattr(action_cls, 'apply_edits'):
            method = getattr(action_cls, 'apply_edits')
            if not method.__doc__:
                report.add(Violation(
                    type=ViolationType.MISSING_DOCSTRING,
                    severity=ViolationSeverity.WARNING,
                    location=f"{action_cls.__name__}.apply_edits",
                    message="apply_edits should have a docstring",
                    suggestion="Add a docstring describing the mutation logic",
                ))
    
    @classmethod
    def _check_type_hints(
        cls,
        action_cls: Type,
        report: ViolationReport,
        strict: bool
    ) -> None:
        """Check that apply_edits has proper type hints."""
        if not hasattr(action_cls, 'apply_edits'):
            return
        
        try:
            hints = get_type_hints(action_cls.apply_edits)
            if 'return' not in hints:
                report.add(Violation(
                    type=ViolationType.UNTYPED_RETURN,
                    severity=ViolationSeverity.ERROR if strict else ViolationSeverity.WARNING,
                    location=f"{action_cls.__name__}.apply_edits",
                    message="apply_edits must have return type annotation",
                    suggestion="Add -> tuple[Optional[T], List[EditOperation]] return type",
                ))
        except Exception:
            # Type hints may fail to resolve in some cases
            pass
    
    @classmethod
    def _check_exception_handling(
        cls,
        action_cls: Type,
        report: ViolationReport,
        strict: bool
    ) -> None:
        """Check for bare exception catching."""
        if not hasattr(action_cls, 'apply_edits'):
            return
        
        try:
            source = inspect.getsource(action_cls.apply_edits)
            
            # Parse to AST for accurate analysis
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler):
                    # Check for bare 'except:' or 'except Exception:'
                    if node.type is None:
                        report.add(Violation(
                            type=ViolationType.BARE_EXCEPTION,
                            severity=ViolationSeverity.ERROR,
                            location=f"{action_cls.__name__}.apply_edits",
                            message="Bare 'except:' catches all errors including SystemExit",
                            suggestion="Use specific exception types",
                        ))
                    elif isinstance(node.type, ast.Name) and node.type.id == 'Exception':
                        # Check if it's handling specific errors inside
                        handler_source = ast.get_source_segment(source, node)
                        if handler_source:
                            has_allowed = any(
                                pattern in handler_source 
                                for pattern in cls.ALLOWED_EXCEPTION_PATTERNS
                            )
                            if not has_allowed:
                                report.add(Violation(
                                    type=ViolationType.BARE_EXCEPTION,
                                    severity=ViolationSeverity.WARNING,
                                    location=f"{action_cls.__name__}.apply_edits",
                                    message="Catching generic Exception may hide errors",
                                    suggestion="Catch specific exceptions or re-raise after logging",
                                ))
        except Exception as e:
            logger.debug(f"Could not analyze exception handling: {e}")
    
    @classmethod
    def _check_api_name(
        cls,
        action_cls: Type,
        report: ViolationReport,
        strict: bool
    ) -> None:
        """Check api_name follows snake_case convention."""
        api_name = getattr(action_cls, 'api_name', None)
        
        if not api_name:
            report.add(Violation(
                type=ViolationType.INVALID_API_NAME,
                severity=ViolationSeverity.ERROR,
                location=f"{action_cls.__name__}",
                message="ActionType must have api_name class variable",
                suggestion="Add: api_name: ClassVar[str] = 'my_action'",
            ))
            return
        
        # Check snake_case
        if not re.match(r'^[a-z][a-z0-9_]*$', api_name):
            report.add(Violation(
                type=ViolationType.NON_SNAKE_CASE,
                severity=ViolationSeverity.WARNING,
                location=f"{action_cls.__name__}.api_name",
                message=f"api_name '{api_name}' should be snake_case",
                suggestion="Use lowercase with underscores: my_action_name",
            ))
    
    @classmethod
    def _check_submission_criteria(
        cls,
        action_cls: Type,
        report: ViolationReport,
        strict: bool
    ) -> None:
        """Check that submission_criteria is defined."""
        criteria = getattr(action_cls, 'submission_criteria', None)
        
        if criteria is None:
            report.add(Violation(
                type=ViolationType.MISSING_TYPE_HINTS,
                severity=ViolationSeverity.INFO,
                location=f"{action_cls.__name__}",
                message="No submission_criteria defined (default: no validation)",
                suggestion="Consider adding validation criteria for this action",
            ))


class QualityGateEnforcement:
    """
    Singleton configuration for quality gate enforcement mode.

    ODA v3.0 Strict Compliance:
    - Default mode is now 'block' for strict ODA enforcement
    - Can be overridden via ORION_GOVERNANCE_MODE environment variable
    - Modes: 'block' (fail on violations), 'warn' (log only), 'off' (disabled)
    """

    _mode: Optional[str] = None  # Lazy initialization

    @classmethod
    def _get_default_mode(cls) -> str:
        """Get default mode from environment or use 'block' for strict ODA."""
        import os
        env_mode = os.environ.get("ORION_GOVERNANCE_MODE", "").lower()
        if env_mode in ("warn", "block", "off"):
            return env_mode
        # Default to 'block' for strict ODA compliance
        return "block"

    @classmethod
    def set_mode(cls, mode: str) -> None:
        """Set enforcement mode: 'warn', 'block', or 'off'."""
        if mode not in ("warn", "block", "off"):
            raise ValueError(f"Invalid mode: {mode}. Use 'warn', 'block', or 'off'")
        cls._mode = mode
        logger.info(f"Quality gate enforcement mode set to: {mode}")

    @classmethod
    def get_mode(cls) -> str:
        """Get current enforcement mode."""
        if cls._mode is None:
            cls._mode = cls._get_default_mode()
        return cls._mode

    @classmethod
    def should_block(cls) -> bool:
        """Check if violations should block execution."""
        return cls.get_mode() == "block"

    @classmethod
    def is_enabled(cls) -> bool:
        """Check if quality gate enforcement is enabled."""
        return cls.get_mode() != "off"

    @classmethod
    def reset(cls) -> None:
        """Reset mode to re-read from environment."""
        cls._mode = None
