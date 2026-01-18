"""
ODA V3.1 - Hallucination Filter
================================

LLM-Agnostic Governance Layer Phase 2.
Validates evidence and parameters to prevent hallucinated operations.

Core Principles:
- ZERO-TRUST: All evidence must be verified
- AUDIT-FIRST: Operations without files_viewed are invalid
- ANTI-HALLUCINATION: Code snippets must match file contents

Usage:
    from lib.oda.ontology.governance import HallucinationFilter

    result = HallucinationFilter.validate_action_params(
        action_api_name="file_edit",
        params={"file_path": "/path/to/file.py", "content": "..."},
        evidence={"files_viewed": ["/path/to/file.py"]}
    )
    if not result.is_valid:
        raise GovernanceError(result.report)
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from lib.oda.ontology.governance.violations import (
    GovernanceError,
    Violation,
    ViolationReport,
    ViolationSeverity,
    ViolationType,
)

logger = logging.getLogger(__name__)


# Extended violation types for hallucination detection
class HallucinationViolationType:
    """Extended violation types specific to hallucination detection."""
    MISSING_EVIDENCE = "missing_evidence"
    INSUFFICIENT_FILES_VIEWED = "insufficient_files_viewed"
    NONEXISTENT_FILE_REFERENCE = "nonexistent_file_reference"
    CONTENT_MISMATCH = "content_mismatch"
    INVALID_PARAMETER_TYPE = "invalid_parameter_type"
    PARAMETER_OUT_OF_RANGE = "parameter_out_of_range"
    UNVERIFIED_CODE_SNIPPET = "unverified_code_snippet"


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    report: ViolationReport
    verified_files: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.is_valid

    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """Merge another validation result into this one."""
        self.is_valid = self.is_valid and other.is_valid
        self.report.merge(other.report)
        self.verified_files.extend(other.verified_files)
        self.errors.extend(other.errors)
        return self


@dataclass
class ParameterSpec:
    """Specification for parameter validation."""
    name: str
    expected_type: type
    required: bool = True
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[List[Any]] = None
    pattern: Optional[str] = None  # Regex pattern for string validation
    validator: Optional[Callable[[Any], bool]] = None


class EvidenceValidator:
    """
    Validates evidence provided with action requests.

    Ensures:
    1. files_viewed is present and non-empty
    2. Referenced files actually exist
    3. Code snippets match actual file contents
    """

    # Minimum required files_viewed per action type
    MIN_FILES_VIEWED: Dict[str, int] = {
        "file_edit": 1,
        "file_create": 0,
        "file_delete": 1,
        "code_refactor": 2,
        "schema_modify": 3,
        "default": 1,
    }

    @classmethod
    def validate_files_viewed(
        cls,
        evidence: Dict[str, Any],
        action_api_name: str,
        strict: bool = True
    ) -> ValidationResult:
        """
        Validate that files_viewed evidence meets requirements.

        Args:
            evidence: Evidence dictionary containing files_viewed
            action_api_name: The action being validated
            strict: If True, missing evidence is ERROR; else WARNING

        Returns:
            ValidationResult with validation status
        """
        report = ViolationReport(target=f"evidence:{action_api_name}")
        verified_files: List[str] = []
        errors: List[str] = []
        is_valid = True

        files_viewed = evidence.get("files_viewed", [])

        # Check if files_viewed exists
        if "files_viewed" not in evidence:
            report.add(Violation(
                type=ViolationType.MISSING_TYPE_HINTS,  # Using existing type
                severity=ViolationSeverity.ERROR if strict else ViolationSeverity.WARNING,
                location=f"{action_api_name}.evidence",
                message=f"Missing 'files_viewed' in evidence. Stage cannot pass without evidence.",
                suggestion="Ensure agent reads files before performing actions",
                metadata={"violation_subtype": HallucinationViolationType.MISSING_EVIDENCE}
            ))
            if strict:
                is_valid = False
            errors.append("files_viewed missing from evidence")
            return ValidationResult(is_valid=is_valid, report=report, errors=errors)

        # Check minimum count
        min_required = cls.MIN_FILES_VIEWED.get(
            action_api_name,
            cls.MIN_FILES_VIEWED["default"]
        )

        if len(files_viewed) < min_required:
            report.add(Violation(
                type=ViolationType.MISSING_TYPE_HINTS,
                severity=ViolationSeverity.ERROR,
                location=f"{action_api_name}.files_viewed",
                message=f"Insufficient files_viewed: {len(files_viewed)} < {min_required} required",
                suggestion=f"Read at least {min_required} file(s) before performing {action_api_name}",
                metadata={
                    "violation_subtype": HallucinationViolationType.INSUFFICIENT_FILES_VIEWED,
                    "count": len(files_viewed),
                    "required": min_required
                }
            ))
            is_valid = False
            errors.append(f"Insufficient files_viewed: {len(files_viewed)} < {min_required}")

        # Verify each file exists
        for file_path in files_viewed:
            if cls._file_exists(file_path):
                verified_files.append(file_path)
            else:
                report.add(Violation(
                    type=ViolationType.FORBIDDEN_IMPORT,  # Reusing for missing file
                    severity=ViolationSeverity.ERROR,
                    location=f"{action_api_name}.files_viewed",
                    message=f"Nonexistent file in evidence: {file_path}",
                    suggestion="Verify file paths before adding to evidence",
                    metadata={
                        "violation_subtype": HallucinationViolationType.NONEXISTENT_FILE_REFERENCE,
                        "file_path": file_path
                    }
                ))
                is_valid = False
                errors.append(f"Nonexistent file: {file_path}")

        return ValidationResult(
            is_valid=is_valid,
            report=report,
            verified_files=verified_files,
            errors=errors
        )

    @classmethod
    def validate_code_snippet(
        cls,
        file_path: str,
        snippet: str,
        evidence: Dict[str, Any],
        fuzzy_match: bool = True
    ) -> ValidationResult:
        """
        Validate that a code snippet matches actual file contents.

        Args:
            file_path: Path to the file containing the snippet
            snippet: Code snippet to verify
            evidence: Evidence dictionary
            fuzzy_match: If True, allows whitespace differences

        Returns:
            ValidationResult with validation status
        """
        report = ViolationReport(target=f"snippet:{file_path}")
        is_valid = True
        errors: List[str] = []

        # Check file was viewed
        files_viewed = evidence.get("files_viewed", [])
        if file_path not in files_viewed:
            report.add(Violation(
                type=ViolationType.FORBIDDEN_IMPORT,
                severity=ViolationSeverity.ERROR,
                location=f"snippet.{file_path}",
                message=f"Code snippet references file not in files_viewed: {file_path}",
                suggestion="Read the file before referencing its contents",
                metadata={
                    "violation_subtype": HallucinationViolationType.UNVERIFIED_CODE_SNIPPET,
                    "file_path": file_path
                }
            ))
            return ValidationResult(is_valid=False, report=report, errors=["File not in evidence"])

        # Read actual file contents
        if not cls._file_exists(file_path):
            report.add(Violation(
                type=ViolationType.FORBIDDEN_IMPORT,
                severity=ViolationSeverity.ERROR,
                location=f"snippet.{file_path}",
                message=f"Cannot verify snippet - file does not exist: {file_path}",
                suggestion="Verify file exists before referencing",
                metadata={
                    "violation_subtype": HallucinationViolationType.NONEXISTENT_FILE_REFERENCE,
                    "file_path": file_path
                }
            ))
            return ValidationResult(is_valid=False, report=report, errors=["File does not exist"])

        try:
            actual_content = Path(file_path).read_text()

            # Normalize for comparison
            if fuzzy_match:
                normalized_snippet = cls._normalize_code(snippet)
                normalized_content = cls._normalize_code(actual_content)
                match = normalized_snippet in normalized_content
            else:
                match = snippet in actual_content

            if not match:
                report.add(Violation(
                    type=ViolationType.INCONSISTENT_RETURN,  # Reusing for mismatch
                    severity=ViolationSeverity.ERROR,
                    location=f"snippet.{file_path}",
                    message="Code snippet does not match actual file contents",
                    suggestion="Re-read the file to get accurate contents",
                    metadata={
                        "violation_subtype": HallucinationViolationType.CONTENT_MISMATCH,
                        "file_path": file_path,
                        "snippet_preview": snippet[:100] + "..." if len(snippet) > 100 else snippet
                    }
                ))
                is_valid = False
                errors.append("Snippet content mismatch")

        except Exception as e:
            logger.warning(f"Could not read file for snippet validation: {e}")
            errors.append(f"Could not read file: {e}")

        return ValidationResult(
            is_valid=is_valid,
            report=report,
            verified_files=[file_path] if is_valid else [],
            errors=errors
        )

    @staticmethod
    def _file_exists(file_path: str) -> bool:
        """Check if a file exists."""
        try:
            return Path(file_path).exists()
        except Exception:
            return False

    @staticmethod
    def _normalize_code(code: str) -> str:
        """Normalize code for fuzzy comparison."""
        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in code.split('\n')]
        # Remove empty lines
        lines = [line for line in lines if line]
        # Join with single space
        return ' '.join(lines)


class ParameterValidator:
    """
    Validates action parameters against type and range constraints.

    Ensures:
    1. Required parameters are present
    2. Parameter types match expected types
    3. Numeric parameters are within valid ranges
    4. String parameters match patterns (if specified)
    """

    # Common parameter specs by action type
    PARAMETER_SPECS: Dict[str, List[ParameterSpec]] = {
        "file_edit": [
            ParameterSpec("file_path", str, required=True, pattern=r'^[\w\-./\\]+$'),
            ParameterSpec("old_string", str, required=True),
            ParameterSpec("new_string", str, required=True),
        ],
        "file_create": [
            ParameterSpec("file_path", str, required=True, pattern=r'^[\w\-./\\]+$'),
            ParameterSpec("content", str, required=True),
        ],
        "file_delete": [
            ParameterSpec("file_path", str, required=True, pattern=r'^[\w\-./\\]+$'),
        ],
    }

    @classmethod
    def validate_params(
        cls,
        action_api_name: str,
        params: Dict[str, Any],
        custom_specs: Optional[List[ParameterSpec]] = None
    ) -> ValidationResult:
        """
        Validate action parameters against specifications.

        Args:
            action_api_name: The action being validated
            params: Parameters to validate
            custom_specs: Custom parameter specifications (override defaults)

        Returns:
            ValidationResult with validation status
        """
        report = ViolationReport(target=f"params:{action_api_name}")
        is_valid = True
        errors: List[str] = []

        # Get specs for this action
        specs = custom_specs or cls.PARAMETER_SPECS.get(action_api_name, [])

        if not specs:
            # No specs defined, skip validation
            logger.debug(f"No parameter specs for {action_api_name}, skipping validation")
            return ValidationResult(is_valid=True, report=report)

        for spec in specs:
            result = cls._validate_single_param(spec, params, action_api_name)
            if not result.is_valid:
                is_valid = False
                report.merge(result.report)
                errors.extend(result.errors)

        return ValidationResult(is_valid=is_valid, report=report, errors=errors)

    @classmethod
    def _validate_single_param(
        cls,
        spec: ParameterSpec,
        params: Dict[str, Any],
        action_api_name: str
    ) -> ValidationResult:
        """Validate a single parameter against its spec."""
        report = ViolationReport(target=f"param:{spec.name}")
        errors: List[str] = []
        is_valid = True

        value = params.get(spec.name)

        # Check required
        if spec.required and value is None:
            report.add(Violation(
                type=ViolationType.MISSING_TYPE_HINTS,
                severity=ViolationSeverity.ERROR,
                location=f"{action_api_name}.params.{spec.name}",
                message=f"Required parameter '{spec.name}' is missing",
                suggestion=f"Provide value for required parameter '{spec.name}'",
                metadata={
                    "violation_subtype": HallucinationViolationType.INVALID_PARAMETER_TYPE,
                    "param_name": spec.name
                }
            ))
            return ValidationResult(is_valid=False, report=report, errors=["Missing required param"])

        if value is None:
            return ValidationResult(is_valid=True, report=report)

        # Check type
        if not isinstance(value, spec.expected_type):
            report.add(Violation(
                type=ViolationType.MISSING_TYPE_HINTS,
                severity=ViolationSeverity.ERROR,
                location=f"{action_api_name}.params.{spec.name}",
                message=f"Parameter '{spec.name}' has wrong type: expected {spec.expected_type.__name__}, got {type(value).__name__}",
                suggestion=f"Provide {spec.expected_type.__name__} value for '{spec.name}'",
                metadata={
                    "violation_subtype": HallucinationViolationType.INVALID_PARAMETER_TYPE,
                    "param_name": spec.name,
                    "expected": spec.expected_type.__name__,
                    "actual": type(value).__name__
                }
            ))
            is_valid = False
            errors.append(f"Type mismatch for {spec.name}")

        # Check range (for numeric types)
        if isinstance(value, (int, float)):
            if spec.min_value is not None and value < spec.min_value:
                report.add(Violation(
                    type=ViolationType.TOO_MANY_PARAMETERS,
                    severity=ViolationSeverity.ERROR,
                    location=f"{action_api_name}.params.{spec.name}",
                    message=f"Parameter '{spec.name}' below minimum: {value} < {spec.min_value}",
                    suggestion=f"Value must be >= {spec.min_value}",
                    metadata={
                        "violation_subtype": HallucinationViolationType.PARAMETER_OUT_OF_RANGE,
                        "param_name": spec.name,
                        "value": value,
                        "min": spec.min_value
                    }
                ))
                is_valid = False
                errors.append(f"Value below minimum for {spec.name}")

            if spec.max_value is not None and value > spec.max_value:
                report.add(Violation(
                    type=ViolationType.TOO_MANY_PARAMETERS,
                    severity=ViolationSeverity.ERROR,
                    location=f"{action_api_name}.params.{spec.name}",
                    message=f"Parameter '{spec.name}' above maximum: {value} > {spec.max_value}",
                    suggestion=f"Value must be <= {spec.max_value}",
                    metadata={
                        "violation_subtype": HallucinationViolationType.PARAMETER_OUT_OF_RANGE,
                        "param_name": spec.name,
                        "value": value,
                        "max": spec.max_value
                    }
                ))
                is_valid = False
                errors.append(f"Value above maximum for {spec.name}")

        # Check allowed values
        if spec.allowed_values is not None and value not in spec.allowed_values:
            report.add(Violation(
                type=ViolationType.MISSING_TYPE_HINTS,
                severity=ViolationSeverity.ERROR,
                location=f"{action_api_name}.params.{spec.name}",
                message=f"Parameter '{spec.name}' has invalid value: {value}",
                suggestion=f"Allowed values: {spec.allowed_values}",
                metadata={
                    "violation_subtype": HallucinationViolationType.INVALID_PARAMETER_TYPE,
                    "param_name": spec.name,
                    "value": value,
                    "allowed": spec.allowed_values
                }
            ))
            is_valid = False
            errors.append(f"Invalid value for {spec.name}")

        # Check pattern (for strings)
        if spec.pattern is not None and isinstance(value, str):
            if not re.match(spec.pattern, value):
                report.add(Violation(
                    type=ViolationType.INVALID_API_NAME,
                    severity=ViolationSeverity.ERROR,
                    location=f"{action_api_name}.params.{spec.name}",
                    message=f"Parameter '{spec.name}' does not match pattern: {spec.pattern}",
                    suggestion=f"Value must match pattern: {spec.pattern}",
                    metadata={
                        "violation_subtype": HallucinationViolationType.INVALID_PARAMETER_TYPE,
                        "param_name": spec.name,
                        "value": value,
                        "pattern": spec.pattern
                    }
                ))
                is_valid = False
                errors.append(f"Pattern mismatch for {spec.name}")

        # Custom validator
        if spec.validator is not None:
            try:
                if not spec.validator(value):
                    report.add(Violation(
                        type=ViolationType.MISSING_TYPE_HINTS,
                        severity=ViolationSeverity.ERROR,
                        location=f"{action_api_name}.params.{spec.name}",
                        message=f"Parameter '{spec.name}' failed custom validation",
                        suggestion="Check parameter value meets custom requirements",
                        metadata={
                            "violation_subtype": HallucinationViolationType.INVALID_PARAMETER_TYPE,
                            "param_name": spec.name
                        }
                    ))
                    is_valid = False
                    errors.append(f"Custom validation failed for {spec.name}")
            except Exception as e:
                logger.warning(f"Custom validator error for {spec.name}: {e}")

        return ValidationResult(is_valid=is_valid, report=report, errors=errors)


class HallucinationFilter:
    """
    Main hallucination filter that combines evidence and parameter validation.

    Enforces:
    1. files_viewed minimum count per action type
    2. All referenced files must exist
    3. Code snippets must match actual file contents
    4. Parameters must match expected types and ranges

    Usage:
        result = HallucinationFilter.validate_action_params(
            action_api_name="file_edit",
            params={"file_path": "/path/to/file.py", ...},
            evidence={"files_viewed": ["/path/to/file.py"]}
        )
        if not result.is_valid:
            raise GovernanceError(result.report)
    """

    # Actions that require evidence validation
    EVIDENCE_REQUIRED_ACTIONS: Set[str] = {
        "file_edit",
        "file_delete",
        "code_refactor",
        "schema_modify",
        "database_migrate",
    }

    # Actions exempt from evidence validation
    EVIDENCE_EXEMPT_ACTIONS: Set[str] = {
        "file_create",
        "echo",
        "list_files",
        "search_code",
    }

    @classmethod
    def validate_action_params(
        cls,
        action_api_name: str,
        params: Dict[str, Any],
        evidence: Dict[str, Any],
        strict: bool = True,
        custom_param_specs: Optional[List[ParameterSpec]] = None
    ) -> ValidationResult:
        """
        Validate action parameters and evidence for hallucination prevention.

        Args:
            action_api_name: The action API name
            params: Action parameters to validate
            evidence: Evidence dictionary (must include files_viewed)
            strict: If True, missing evidence blocks the action
            custom_param_specs: Custom parameter specifications

        Returns:
            ValidationResult with combined validation status
        """
        report = ViolationReport(target=f"hallucination:{action_api_name}")
        combined_result = ValidationResult(is_valid=True, report=report)

        # Step 1: Validate evidence (files_viewed)
        if action_api_name not in cls.EVIDENCE_EXEMPT_ACTIONS:
            evidence_result = EvidenceValidator.validate_files_viewed(
                evidence=evidence,
                action_api_name=action_api_name,
                strict=strict
            )
            combined_result.merge(evidence_result)

        # Step 2: Validate parameters
        param_result = ParameterValidator.validate_params(
            action_api_name=action_api_name,
            params=params,
            custom_specs=custom_param_specs
        )
        combined_result.merge(param_result)

        # Step 3: Cross-validate file references in params
        if combined_result.is_valid:
            cross_result = cls._cross_validate_file_references(
                action_api_name=action_api_name,
                params=params,
                evidence=evidence
            )
            combined_result.merge(cross_result)

        # Log validation result
        if combined_result.is_valid:
            logger.debug(f"Hallucination filter passed for {action_api_name}")
        else:
            logger.warning(
                f"Hallucination filter BLOCKED {action_api_name}: "
                f"{len(combined_result.errors)} violations"
            )

        return combined_result

    @classmethod
    def _cross_validate_file_references(
        cls,
        action_api_name: str,
        params: Dict[str, Any],
        evidence: Dict[str, Any]
    ) -> ValidationResult:
        """
        Cross-validate that file paths in params were in files_viewed.

        Ensures agent read the file before trying to modify it.
        """
        report = ViolationReport(target=f"cross:{action_api_name}")
        is_valid = True
        errors: List[str] = []

        files_viewed = set(evidence.get("files_viewed", []))

        # Check common file path parameters
        file_path_params = ["file_path", "source_file", "target_file", "path"]

        for param_name in file_path_params:
            if param_name in params:
                file_path = params[param_name]
                if isinstance(file_path, str) and file_path not in files_viewed:
                    # Allow file_create to reference new files
                    if action_api_name == "file_create":
                        continue

                    report.add(Violation(
                        type=ViolationType.FORBIDDEN_IMPORT,
                        severity=ViolationSeverity.ERROR,
                        location=f"{action_api_name}.params.{param_name}",
                        message=f"File '{file_path}' not in files_viewed evidence",
                        suggestion="Read the file before performing modifications",
                        metadata={
                            "violation_subtype": HallucinationViolationType.UNVERIFIED_CODE_SNIPPET,
                            "param_name": param_name,
                            "file_path": file_path,
                            "files_viewed": list(files_viewed)
                        }
                    ))
                    is_valid = False
                    errors.append(f"Unverified file reference: {file_path}")

        return ValidationResult(is_valid=is_valid, report=report, errors=errors)

    @classmethod
    def validate_code_snippet_match(
        cls,
        file_path: str,
        snippet: str,
        evidence: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate that a code snippet matches the actual file contents.

        Use this when an agent provides code that should exist in a file.
        """
        return EvidenceValidator.validate_code_snippet(
            file_path=file_path,
            snippet=snippet,
            evidence=evidence
        )

    @classmethod
    def require_files_viewed(
        cls,
        evidence: Dict[str, Any],
        min_count: int = 1
    ) -> ValidationResult:
        """
        Simple check that files_viewed has at least min_count entries.

        Use this as a Stage gate.
        """
        report = ViolationReport(target="stage_gate")
        files_viewed = evidence.get("files_viewed", [])

        if len(files_viewed) < min_count:
            report.add(Violation(
                type=ViolationType.MISSING_TYPE_HINTS,
                severity=ViolationSeverity.CRITICAL,
                location="stage.files_viewed",
                message=f"Stage cannot pass: files_viewed ({len(files_viewed)}) < required ({min_count})",
                suggestion=f"Read at least {min_count} file(s) before completing this stage",
                metadata={
                    "violation_subtype": HallucinationViolationType.INSUFFICIENT_FILES_VIEWED,
                    "count": len(files_viewed),
                    "required": min_count
                }
            ))
            return ValidationResult(
                is_valid=False,
                report=report,
                errors=[f"Insufficient files_viewed: {len(files_viewed)} < {min_count}"]
            )

        return ValidationResult(
            is_valid=True,
            report=report,
            verified_files=files_viewed
        )


# Convenience functions for direct use
def validate_action(
    action_api_name: str,
    params: Dict[str, Any],
    evidence: Dict[str, Any]
) -> ValidationResult:
    """Convenience function for HallucinationFilter.validate_action_params."""
    return HallucinationFilter.validate_action_params(
        action_api_name=action_api_name,
        params=params,
        evidence=evidence
    )


def require_evidence(evidence: Dict[str, Any], min_files: int = 1) -> bool:
    """
    Simple check that can be used as a Stage gate.

    Raises GovernanceError if insufficient evidence.
    """
    result = HallucinationFilter.require_files_viewed(evidence, min_files)
    if not result.is_valid:
        raise GovernanceError(result.report)
    return True
