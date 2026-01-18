"""
Identifier types and utilities for Ontology Definition.

Provides:
    - RID: Resource ID type and validation (Palantir global identifier)
    - ApiName: API name type and validation
    - UUID generation utilities
    - Identifier validation functions

RID Format:
    ri.{service}.{instance}.{type}.{unique-id}
    Example: ri.ontology.main.object-type.Employee

ApiName Format:
    - Must start with a letter
    - Only alphanumeric and underscore allowed
    - PascalCase recommended for types
    - camelCase recommended for properties
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, Field

# =============================================================================
# RID (Resource ID)
# =============================================================================

# RID pattern for Palantir Foundry resources
RID_PATTERN = re.compile(
    r"^ri\.(?P<service>[a-z]+)\.(?P<instance>[a-z]+)\.(?P<type>[a-z-]+)\.(?P<id>[a-zA-Z0-9-]+)$"
)

# Supported RID types
RID_TYPES = frozenset({
    "object-type",
    "link-type",
    "action-type",
    "interface",
    "value-type",
    "struct-type",
    "shared-property",
    "dataset",
    "restricted-view",
    "entity",
})


def validate_rid(value: str) -> str:
    """
    Validate that a string is a valid RID format.

    Args:
        value: String to validate

    Returns:
        The validated RID string

    Raises:
        ValueError: If the string is not a valid RID
    """
    if not RID_PATTERN.match(value):
        raise ValueError(
            f"Invalid RID format: {value}. "
            "Expected: ri.{{service}}.{{instance}}.{{type}}.{{id}}"
        )
    return value


def parse_rid(rid: str) -> dict[str, str]:
    """
    Parse a RID into its components.

    Args:
        rid: Resource ID string

    Returns:
        Dictionary with keys: service, instance, type, id

    Raises:
        ValueError: If the RID is invalid
    """
    match = RID_PATTERN.match(rid)
    if not match:
        raise ValueError(f"Invalid RID format: {rid}")
    return match.groupdict()


def generate_rid(
    service: str = "ontology",
    resource_type: str = "entity",
    instance: str = "main",
    unique_id: str | None = None,
) -> str:
    """
    Generate a new RID.

    Args:
        service: Service name (default: "ontology")
        resource_type: Resource type (e.g., "object-type", "link-type")
        instance: Instance name (default: "main")
        unique_id: Unique identifier (default: auto-generated UUID)

    Returns:
        New RID string

    Example:
        >>> generate_rid("ontology", "object-type", unique_id="Employee")
        'ri.ontology.main.object-type.Employee'
    """
    if unique_id is None:
        unique_id = str(uuid.uuid4())
    return f"ri.{service}.{instance}.{resource_type}.{unique_id}"


# Type alias for RID with validation
RID = Annotated[str, AfterValidator(validate_rid)]


# =============================================================================
# API NAME
# =============================================================================

# ApiName pattern - must start with letter, alphanumeric and underscore only
API_NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")

# Reserved words that cannot be used as apiNames
RESERVED_API_NAMES = frozenset({
    # Python keywords
    "class", "def", "return", "import", "from", "if", "else", "for", "while",
    "try", "except", "finally", "with", "as", "is", "in", "not", "and", "or",
    "True", "False", "None", "lambda", "yield", "global", "nonlocal", "pass",
    "break", "continue", "raise", "assert", "del",
    # SQL keywords
    "select", "from", "where", "join", "insert", "update", "delete", "create",
    "drop", "alter", "table", "index", "view", "constraint", "primary", "foreign",
    "key", "references", "unique", "null", "default", "order", "by", "group",
    "having", "union", "intersect", "except", "limit", "offset",
    # Ontology reserved
    "rid", "id", "type", "status", "version", "metadata", "properties", "links",
})


def validate_api_name(value: str) -> str:
    """
    Validate that a string is a valid apiName.

    Args:
        value: String to validate

    Returns:
        The validated apiName string

    Raises:
        ValueError: If the string is not a valid apiName
    """
    if not value:
        raise ValueError("apiName cannot be empty")

    if not API_NAME_PATTERN.match(value):
        raise ValueError(
            f"Invalid apiName: {value}. "
            "Must start with a letter and contain only alphanumeric characters and underscores."
        )

    if len(value) > 255:
        raise ValueError(f"apiName too long: {len(value)} > 255 characters")

    if value.lower() in RESERVED_API_NAMES:
        raise ValueError(f"apiName '{value}' is reserved and cannot be used")

    return value


def is_pascal_case(value: str) -> bool:
    """Check if string is PascalCase (recommended for type names)."""
    return bool(value) and value[0].isupper() and "_" not in value


def is_camel_case(value: str) -> bool:
    """Check if string is camelCase (recommended for property names)."""
    return bool(value) and value[0].islower() and "_" not in value


def is_snake_case(value: str) -> bool:
    """Check if string is snake_case (allowed but not recommended)."""
    return bool(value) and value.islower() and value.replace("_", "").isalnum()


def to_pascal_case(value: str) -> str:
    """Convert string to PascalCase."""
    if not value:
        return value
    # Handle snake_case
    if "_" in value:
        return "".join(word.capitalize() for word in value.split("_"))
    # Already PascalCase or single word
    return value[0].upper() + value[1:]


def to_camel_case(value: str) -> str:
    """Convert string to camelCase."""
    pascal = to_pascal_case(value)
    if not pascal:
        return pascal
    return pascal[0].lower() + pascal[1:]


def to_snake_case(value: str) -> str:
    """Convert string to snake_case."""
    if not value:
        return value
    # Insert underscore before uppercase letters
    result = re.sub(r"([A-Z])", r"_\1", value)
    return result.lower().lstrip("_")


# Type alias for ApiName with validation
ApiName = Annotated[str, AfterValidator(validate_api_name)]


# =============================================================================
# UUID UTILITIES
# =============================================================================

def generate_uuid() -> str:
    """
    Generate a new UUID v4 string.

    Returns:
        UUID string (lowercase, hyphenated format)

    Note:
        Palantir recommends String-based primary keys over Long
        to avoid JavaScript precision issues in Workshop/Slate.
    """
    return str(uuid.uuid4())


def is_valid_uuid(value: str) -> bool:
    """
    Check if a string is a valid UUID.

    Args:
        value: String to check

    Returns:
        True if valid UUID format
    """
    try:
        uuid.UUID(value)
        return True
    except (ValueError, TypeError):
        return False


def validate_uuid(value: str) -> str:
    """
    Validate that a string is a valid UUID format.

    Args:
        value: String to validate

    Returns:
        Normalized UUID string (lowercase)

    Raises:
        ValueError: If not a valid UUID
    """
    try:
        return str(uuid.UUID(value))
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid UUID format: {value}") from e


# =============================================================================
# TIMESTAMP UTILITIES
# =============================================================================

def generate_timestamp_id() -> str:
    """
    Generate a timestamp-based unique ID.

    Format: {timestamp}_{short-uuid}
    Example: 20260117T120000_a1b2c3d4

    Useful for human-readable IDs with natural ordering.
    """
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    short_uuid = uuid.uuid4().hex[:8]
    return f"{timestamp}_{short_uuid}"


# =============================================================================
# FIELD DEFINITIONS
# =============================================================================

# Pre-configured Field definitions for common identifier patterns

RIDField = Field(
    default_factory=lambda: generate_rid("ontology", "entity"),
    description="Resource ID - globally unique identifier",
    json_schema_extra={"readOnly": True, "immutable": True},
)

ApiNameField = Field(
    ...,
    description="Programmatic identifier. Must be unique within scope.",
    min_length=1,
    max_length=255,
    pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$",
)

UUIDField = Field(
    default_factory=generate_uuid,
    description="Primary key (UUID v4)",
    json_schema_extra={"immutable": True},
)
