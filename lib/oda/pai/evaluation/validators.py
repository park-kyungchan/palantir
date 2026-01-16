"""
ODA PAI Evaluation - Block Validators
=====================================

Defines validation protocols and concrete validators for AIP Logic blocks.

This module provides:
- ValidationResult: Result of a validation check
- BlockValidator: Protocol for validators
- Concrete validators for common checks
- ValidatorRegistry: Registry for managing validators

Validators:
    - ContentLengthValidator: Validates content length bounds
    - SyntaxValidator: Validates syntax for a language
    - FormatValidator: Validates expected format (markdown, json, etc.)
    - EncodingValidator: Validates text encoding

Usage:
    ```python
    from lib.oda.pai.evaluation import (
        BlockValidator,
        ContentLengthValidator,
        SyntaxValidator,
        ValidatorRegistry,
    )

    # Create registry
    registry = ValidatorRegistry()

    # Register validators
    registry.register(ContentLengthValidator(min_length=10, max_length=10000))
    registry.register(SyntaxValidator(language="python"))

    # Validate a block
    results = registry.validate_all("block-123")
    for result in results:
        print(f"{result.validator_name}: {'PASS' if result.valid else 'FAIL'}")
    ```

Version: 1.0.0
"""

from __future__ import annotations

import ast
import json
import re
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from lib.oda.ontology.ontology_types import utc_now


# =============================================================================
# VALIDATION RESULT
# =============================================================================


class ValidationResult(BaseModel):
    """
    Result of a validation check.

    Attributes:
        valid: Whether the validation passed
        validator_name: Name of the validator that produced this result
        errors: List of error messages (empty if valid)
        warnings: List of warning messages (non-blocking issues)
        checked_at: Timestamp of validation
        metadata: Additional metadata from validation
    """

    valid: bool = Field(
        ...,
        description="Whether the validation passed"
    )
    validator_name: str = Field(
        ...,
        description="Name of the validator that produced this result"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="List of error messages"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="List of warning messages"
    )
    checked_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp of validation"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata from validation"
    )

    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0

    def to_summary(self) -> str:
        """Generate a human-readable summary."""
        status = "PASS" if self.valid else "FAIL"
        parts = [f"[{status}] {self.validator_name}"]

        if self.errors:
            parts.append(f"  Errors: {', '.join(self.errors)}")
        if self.warnings:
            parts.append(f"  Warnings: {', '.join(self.warnings)}")

        return "\n".join(parts)

    @classmethod
    def passed(cls, validator_name: str, **metadata: Any) -> "ValidationResult":
        """Create a passing validation result."""
        return cls(
            valid=True,
            validator_name=validator_name,
            metadata=metadata,
        )

    @classmethod
    def failed(
        cls,
        validator_name: str,
        errors: List[str],
        warnings: Optional[List[str]] = None,
        **metadata: Any
    ) -> "ValidationResult":
        """Create a failing validation result."""
        return cls(
            valid=False,
            validator_name=validator_name,
            errors=errors,
            warnings=warnings or [],
            metadata=metadata,
        )


# =============================================================================
# BLOCK VALIDATOR PROTOCOL
# =============================================================================


@runtime_checkable
class BlockValidator(Protocol):
    """
    Protocol for block validators.

    Validators implement this protocol to provide custom validation logic.
    The protocol is runtime_checkable, allowing isinstance() checks.

    Properties:
        name: Human-readable name of the validator

    Methods:
        validate(block_id: str) -> ValidationResult
    """

    @property
    def name(self) -> str:
        """Human-readable name of the validator."""
        ...

    def validate(self, block_id: str) -> ValidationResult:
        """
        Validate a block.

        Args:
            block_id: The ID of the block to validate

        Returns:
            ValidationResult with pass/fail status and any messages
        """
        ...


# =============================================================================
# CONTENT VALIDATORS
# =============================================================================


class ContentLengthValidator:
    """
    Validates content length is within specified bounds.

    Attributes:
        min_length: Minimum required length (default: 0)
        max_length: Maximum allowed length (default: 100000)
        _content_provider: Optional function to get content for a block_id
    """

    def __init__(
        self,
        min_length: int = 0,
        max_length: int = 100000,
        content_provider: Optional[Callable[[str], str]] = None
    ) -> None:
        """
        Initialize ContentLengthValidator.

        Args:
            min_length: Minimum required length
            max_length: Maximum allowed length
            content_provider: Optional function to get content for a block_id
        """
        if min_length < 0:
            raise ValueError("min_length must be >= 0")
        if max_length < min_length:
            raise ValueError("max_length must be >= min_length")

        self.min_length = min_length
        self.max_length = max_length
        self._content_provider = content_provider

    @property
    def name(self) -> str:
        return "ContentLengthValidator"

    def validate(self, block_id: str) -> ValidationResult:
        """
        Validate content length for a block.

        Args:
            block_id: The ID of the block to validate

        Returns:
            ValidationResult indicating pass/fail
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Get content
        if self._content_provider:
            try:
                content = self._content_provider(block_id)
            except Exception as e:
                return ValidationResult.failed(
                    self.name,
                    [f"Failed to get content: {e}"]
                )
        else:
            # Default: use block_id as placeholder content
            content = block_id

        length = len(content)

        # Check bounds
        if length < self.min_length:
            errors.append(
                f"Content too short: {length} chars (min: {self.min_length})"
            )
        if length > self.max_length:
            errors.append(
                f"Content too long: {length} chars (max: {self.max_length})"
            )

        # Warnings for edge cases
        if length == 0:
            warnings.append("Content is empty")
        elif length < 10:
            warnings.append("Content is very short")

        if errors:
            return ValidationResult.failed(
                self.name,
                errors,
                warnings,
                length=length,
                min_length=self.min_length,
                max_length=self.max_length,
            )

        return ValidationResult.passed(
            self.name,
            length=length,
            min_length=self.min_length,
            max_length=self.max_length,
        )


class SyntaxValidator:
    """
    Validates syntax for a specific programming language.

    Currently supports:
    - python: Python syntax validation using ast.parse
    - json: JSON syntax validation using json.loads

    Attributes:
        language: The language to validate (python, json)
        _content_provider: Optional function to get content for a block_id
    """

    SUPPORTED_LANGUAGES = {"python", "json"}

    def __init__(
        self,
        language: str = "python",
        content_provider: Optional[Callable[[str], str]] = None
    ) -> None:
        """
        Initialize SyntaxValidator.

        Args:
            language: The language to validate
            content_provider: Optional function to get content for a block_id
        """
        language = language.lower()
        if language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language: {language}. "
                f"Supported: {self.SUPPORTED_LANGUAGES}"
            )

        self.language = language
        self._content_provider = content_provider

    @property
    def name(self) -> str:
        return f"SyntaxValidator({self.language})"

    def validate(self, block_id: str) -> ValidationResult:
        """
        Validate syntax for a block.

        Args:
            block_id: The ID of the block to validate

        Returns:
            ValidationResult indicating pass/fail
        """
        # Get content
        if self._content_provider:
            try:
                content = self._content_provider(block_id)
            except Exception as e:
                return ValidationResult.failed(
                    self.name,
                    [f"Failed to get content: {e}"]
                )
        else:
            # Default: empty content (passes syntax check)
            content = ""

        # Validate based on language
        if self.language == "python":
            return self._validate_python(content)
        elif self.language == "json":
            return self._validate_json(content)
        else:
            return ValidationResult.failed(
                self.name,
                [f"Unsupported language: {self.language}"]
            )

    def _validate_python(self, content: str) -> ValidationResult:
        """Validate Python syntax."""
        if not content.strip():
            return ValidationResult.passed(
                self.name,
                language="python",
                note="Empty content is valid"
            )

        try:
            ast.parse(content)
            return ValidationResult.passed(
                self.name,
                language="python"
            )
        except SyntaxError as e:
            return ValidationResult.failed(
                self.name,
                [f"Python syntax error at line {e.lineno}: {e.msg}"],
                language="python",
                line=e.lineno,
                offset=e.offset,
            )

    def _validate_json(self, content: str) -> ValidationResult:
        """Validate JSON syntax."""
        if not content.strip():
            return ValidationResult.passed(
                self.name,
                language="json",
                note="Empty content is valid"
            )

        try:
            json.loads(content)
            return ValidationResult.passed(
                self.name,
                language="json"
            )
        except json.JSONDecodeError as e:
            return ValidationResult.failed(
                self.name,
                [f"JSON syntax error at line {e.lineno}: {e.msg}"],
                language="json",
                line=e.lineno,
                column=e.colno,
            )


class FormatValidator:
    """
    Validates content matches an expected format.

    Supported formats:
    - markdown: Basic markdown structure validation
    - json: JSON format validation
    - yaml: YAML format validation (basic)
    - text: Plain text (always passes)

    Attributes:
        expected_format: The format to validate against
        _content_provider: Optional function to get content for a block_id
    """

    SUPPORTED_FORMATS = {"markdown", "json", "yaml", "text"}

    def __init__(
        self,
        expected_format: str = "markdown",
        content_provider: Optional[Callable[[str], str]] = None
    ) -> None:
        """
        Initialize FormatValidator.

        Args:
            expected_format: The format to validate against
            content_provider: Optional function to get content for a block_id
        """
        expected_format = expected_format.lower()
        if expected_format not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format: {expected_format}. "
                f"Supported: {self.SUPPORTED_FORMATS}"
            )

        self.expected_format = expected_format
        self._content_provider = content_provider

    @property
    def name(self) -> str:
        return f"FormatValidator({self.expected_format})"

    def validate(self, block_id: str) -> ValidationResult:
        """
        Validate format for a block.

        Args:
            block_id: The ID of the block to validate

        Returns:
            ValidationResult indicating pass/fail
        """
        # Get content
        if self._content_provider:
            try:
                content = self._content_provider(block_id)
            except Exception as e:
                return ValidationResult.failed(
                    self.name,
                    [f"Failed to get content: {e}"]
                )
        else:
            content = ""

        # Validate based on format
        if self.expected_format == "markdown":
            return self._validate_markdown(content)
        elif self.expected_format == "json":
            return self._validate_json(content)
        elif self.expected_format == "yaml":
            return self._validate_yaml(content)
        elif self.expected_format == "text":
            return ValidationResult.passed(
                self.name,
                format="text",
                note="Plain text always passes"
            )
        else:
            return ValidationResult.failed(
                self.name,
                [f"Unsupported format: {self.expected_format}"]
            )

    def _validate_markdown(self, content: str) -> ValidationResult:
        """Validate basic markdown structure."""
        warnings: List[str] = []

        if not content.strip():
            return ValidationResult.passed(
                self.name,
                format="markdown",
                note="Empty content is valid"
            )

        # Check for common markdown elements
        has_headers = bool(re.search(r'^#+\s', content, re.MULTILINE))
        has_lists = bool(re.search(r'^[\*\-\d\.]\s', content, re.MULTILINE))
        has_code_blocks = "```" in content
        has_inline_code = bool(re.search(r'`[^`]+`', content))

        # Check for potential issues
        unclosed_code_blocks = content.count("```") % 2 != 0
        if unclosed_code_blocks:
            warnings.append("Possible unclosed code block")

        # Check for broken links
        broken_links = re.findall(r'\[([^\]]*)\]\(\s*\)', content)
        if broken_links:
            warnings.append(f"Found {len(broken_links)} links with empty URLs")

        return ValidationResult.passed(
            self.name,
            format="markdown",
            has_headers=has_headers,
            has_lists=has_lists,
            has_code_blocks=has_code_blocks,
            has_inline_code=has_inline_code,
        ) if not warnings else ValidationResult(
            valid=True,
            validator_name=self.name,
            warnings=warnings,
            metadata={
                "format": "markdown",
                "has_headers": has_headers,
                "has_lists": has_lists,
            }
        )

    def _validate_json(self, content: str) -> ValidationResult:
        """Validate JSON format."""
        if not content.strip():
            return ValidationResult.passed(
                self.name,
                format="json",
                note="Empty content is valid"
            )

        try:
            parsed = json.loads(content)
            return ValidationResult.passed(
                self.name,
                format="json",
                type=type(parsed).__name__,
            )
        except json.JSONDecodeError as e:
            return ValidationResult.failed(
                self.name,
                [f"Invalid JSON at line {e.lineno}: {e.msg}"],
                format="json",
            )

    def _validate_yaml(self, content: str) -> ValidationResult:
        """Validate YAML format (basic check)."""
        if not content.strip():
            return ValidationResult.passed(
                self.name,
                format="yaml",
                note="Empty content is valid"
            )

        # Basic YAML validation without importing yaml library
        # Check for common YAML patterns
        lines = content.split("\n")
        errors: List[str] = []
        warnings: List[str] = []

        for i, line in enumerate(lines, 1):
            # Check for tabs (YAML should use spaces)
            if "\t" in line and not line.strip().startswith("#"):
                errors.append(f"Line {i}: YAML should use spaces, not tabs")
                break

            # Check for misaligned keys (basic)
            stripped = line.lstrip()
            if stripped and not stripped.startswith("#"):
                indent = len(line) - len(stripped)
                if indent % 2 != 0 and stripped.endswith(":"):
                    warnings.append(
                        f"Line {i}: Unusual indentation ({indent} spaces)"
                    )

        if errors:
            return ValidationResult.failed(
                self.name,
                errors,
                warnings,
                format="yaml",
            )

        return ValidationResult.passed(
            self.name,
            format="yaml",
        ) if not warnings else ValidationResult(
            valid=True,
            validator_name=self.name,
            warnings=warnings,
            metadata={"format": "yaml"}
        )


class EncodingValidator:
    """
    Validates text encoding.

    Attributes:
        expected_encoding: The expected encoding (default: utf-8)
        _content_provider: Optional function to get bytes for a block_id
    """

    def __init__(
        self,
        expected_encoding: str = "utf-8",
        content_provider: Optional[Callable[[str], bytes]] = None
    ) -> None:
        """
        Initialize EncodingValidator.

        Args:
            expected_encoding: The expected encoding
            content_provider: Optional function to get bytes for a block_id
        """
        self.expected_encoding = expected_encoding.lower()
        self._content_provider = content_provider

    @property
    def name(self) -> str:
        return f"EncodingValidator({self.expected_encoding})"

    def validate(self, block_id: str) -> ValidationResult:
        """
        Validate encoding for a block.

        Args:
            block_id: The ID of the block to validate

        Returns:
            ValidationResult indicating pass/fail
        """
        # Get content as bytes
        if self._content_provider:
            try:
                content_bytes = self._content_provider(block_id)
            except Exception as e:
                return ValidationResult.failed(
                    self.name,
                    [f"Failed to get content: {e}"]
                )
        else:
            # Default: encode block_id as sample
            content_bytes = block_id.encode(self.expected_encoding)

        # Try to decode with expected encoding
        try:
            content_bytes.decode(self.expected_encoding)
            return ValidationResult.passed(
                self.name,
                encoding=self.expected_encoding,
                byte_length=len(content_bytes),
            )
        except UnicodeDecodeError as e:
            return ValidationResult.failed(
                self.name,
                [
                    f"Invalid {self.expected_encoding} encoding: "
                    f"{e.reason} at position {e.start}"
                ],
                encoding=self.expected_encoding,
                error_start=e.start,
                error_end=e.end,
            )


# =============================================================================
# VALIDATOR REGISTRY
# =============================================================================


class ValidatorRegistry:
    """
    Registry for managing BlockValidator instances.

    The registry allows registering validators by name and validating
    blocks against all or specific validators.

    Attributes:
        _validators: Dictionary of registered validators by name
    """

    def __init__(self) -> None:
        """Initialize an empty ValidatorRegistry."""
        self._validators: Dict[str, BlockValidator] = {}

    def register(self, validator: BlockValidator) -> None:
        """
        Register a validator.

        Args:
            validator: The BlockValidator to register

        Raises:
            ValueError: If a validator with the same name is already registered
            TypeError: If the validator doesn't implement BlockValidator protocol
        """
        if not isinstance(validator, BlockValidator):
            raise TypeError(
                f"Expected BlockValidator, got {type(validator).__name__}"
            )

        name = validator.name
        if name in self._validators:
            raise ValueError(f"Validator already registered: {name}")

        self._validators[name] = validator

    def unregister(self, name: str) -> bool:
        """
        Unregister a validator by name.

        Args:
            name: The validator name to unregister

        Returns:
            True if the validator was removed, False if not found
        """
        if name in self._validators:
            del self._validators[name]
            return True
        return False

    def get(self, name: str) -> Optional[BlockValidator]:
        """
        Get a registered validator by name.

        Args:
            name: The validator name to look up

        Returns:
            The BlockValidator if found, None otherwise
        """
        return self._validators.get(name)

    def list_validators(self) -> List[str]:
        """
        List all registered validator names.

        Returns:
            List of validator names
        """
        return list(self._validators.keys())

    def validate_all(self, block_id: str) -> List[ValidationResult]:
        """
        Validate a block against all registered validators.

        Args:
            block_id: The ID of the block to validate

        Returns:
            List of ValidationResult from all validators
        """
        results: List[ValidationResult] = []

        for validator in self._validators.values():
            try:
                result = validator.validate(block_id)
                results.append(result)
            except Exception as e:
                # Catch any unexpected errors
                results.append(
                    ValidationResult.failed(
                        validator.name,
                        [f"Validation error: {e}"]
                    )
                )

        return results

    def validate_with(
        self,
        block_id: str,
        validator_names: List[str]
    ) -> List[ValidationResult]:
        """
        Validate a block against specific validators.

        Args:
            block_id: The ID of the block to validate
            validator_names: List of validator names to use

        Returns:
            List of ValidationResult from specified validators
        """
        results: List[ValidationResult] = []

        for name in validator_names:
            validator = self._validators.get(name)
            if validator:
                try:
                    result = validator.validate(block_id)
                    results.append(result)
                except Exception as e:
                    results.append(
                        ValidationResult.failed(
                            name,
                            [f"Validation error: {e}"]
                        )
                    )
            else:
                results.append(
                    ValidationResult.failed(
                        name,
                        [f"Validator not found: {name}"]
                    )
                )

        return results

    def all_pass(self, block_id: str) -> bool:
        """
        Check if a block passes all validators.

        Args:
            block_id: The ID of the block to validate

        Returns:
            True if all validators pass, False otherwise
        """
        results = self.validate_all(block_id)
        return all(r.valid for r in results)

    def get_failures(self, block_id: str) -> List[ValidationResult]:
        """
        Get only the failing validation results.

        Args:
            block_id: The ID of the block to validate

        Returns:
            List of failed ValidationResult objects
        """
        results = self.validate_all(block_id)
        return [r for r in results if not r.valid]

    @staticmethod
    def default_validators() -> List[BlockValidator]:
        """
        Get a list of default validators.

        Returns:
            List of commonly used BlockValidator instances
        """
        return [
            ContentLengthValidator(min_length=0, max_length=100000),
            SyntaxValidator(language="python"),
            FormatValidator(expected_format="markdown"),
            EncodingValidator(expected_encoding="utf-8"),
        ]
