"""
Orion ODA v4.0 - Schema Conflict Detection
==========================================

Enhanced conflict detection specifically for schema-level conflicts.

This module provides:
- SchemaConflict: Schema-specific conflict representation
- SchemaConflictDetector: Detect schema incompatibilities between branches
- Auto-merge capability detection

Design Principles:
1. Schema changes are treated with higher severity
2. Type mismatches require manual resolution
3. Support for field-level granularity in schema conflicts

Schema Version: 4.0.0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import uuid

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from lib.oda.ontology.objects.branch import BranchCommit

logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMA CONFLICT TYPES (Enhanced from ConflictType)
# =============================================================================

class SchemaConflictType(str, Enum):
    """Types of schema-specific conflicts."""
    SCHEMA_CHANGE = "schema_change"              # Same field modified differently
    TYPE_MISMATCH = "type_mismatch"              # Field type changed incompatibly
    DELETION_CONFLICT = "deletion_conflict"      # One branch deleted, other modified
    CONSTRAINT_VIOLATION = "constraint_violation"  # Conflicting constraints
    FIELD_RENAME = "field_rename"                # Field renamed in both branches
    REQUIRED_CHANGE = "required_change"          # Required/optional changed differently
    DEFAULT_CHANGE = "default_change"            # Different default values set
    VALIDATION_CONFLICT = "validation_conflict"  # Conflicting validators


class SchemaConflictSeverity(str, Enum):
    """Severity levels for schema conflicts."""
    INFO = "info"           # Informational, no action needed
    WARNING = "warning"     # May need attention
    ERROR = "error"         # Must be resolved
    CRITICAL = "critical"   # Blocks operation


# =============================================================================
# SCHEMA CONFLICT MODELS (Pydantic v2)
# =============================================================================

class SchemaConflict(BaseModel):
    """
    Represents a schema-level conflict between branches.

    Captures detailed information about incompatible schema changes
    between two branches, including:
    - What type of conflict occurred
    - Which object type and field are affected
    - Values from both branches
    - Suggested resolutions
    """
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])

    # Conflict classification
    conflict_type: SchemaConflictType
    severity: SchemaConflictSeverity = SchemaConflictSeverity.ERROR

    # Location
    object_type: str
    field_name: Optional[str] = None

    # Values from both branches
    branch_a_value: Any = None
    branch_b_value: Any = None
    base_value: Any = None  # Value at common ancestor

    # Context
    branch_a_id: Optional[str] = None
    branch_b_id: Optional[str] = None
    branch_a_commit_id: Optional[str] = None
    branch_b_commit_id: Optional[str] = None

    # Resolution
    resolution_suggestions: List[str] = Field(default_factory=list)
    auto_resolvable: bool = False
    recommended_resolution: Optional[str] = None

    # Metadata
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}

    @property
    def key(self) -> str:
        """Unique key for this conflict."""
        if self.field_name:
            return f"{self.object_type}:{self.field_name}"
        return self.object_type

    @property
    def is_blocking(self) -> bool:
        """Check if this conflict blocks merge."""
        return self.severity in (SchemaConflictSeverity.ERROR, SchemaConflictSeverity.CRITICAL)


class SchemaConflictBatch(BaseModel):
    """Collection of schema conflicts from a comparison operation."""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    branch_a_id: str
    branch_b_id: str
    conflicts: List[SchemaConflict] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"extra": "forbid"}

    @property
    def total_count(self) -> int:
        return len(self.conflicts)

    @property
    def blocking_count(self) -> int:
        return len([c for c in self.conflicts if c.is_blocking])

    @property
    def auto_resolvable_count(self) -> int:
        return len([c for c in self.conflicts if c.auto_resolvable])

    @property
    def can_auto_merge(self) -> bool:
        """Check if all conflicts can be auto-resolved."""
        return all(c.auto_resolvable for c in self.conflicts)

    def get_by_type(self, conflict_type: SchemaConflictType) -> List[SchemaConflict]:
        return [c for c in self.conflicts if c.conflict_type == conflict_type]

    def get_blocking(self) -> List[SchemaConflict]:
        return [c for c in self.conflicts if c.is_blocking]


# =============================================================================
# SCHEMA CONFLICT DETECTOR
# =============================================================================

class SchemaConflictDetector:
    """
    Detect schema-level conflicts between branches.

    Analyzes schema definitions from two branches to identify
    incompatible changes that would prevent merge.

    Usage:
        ```python
        detector = SchemaConflictDetector()

        # Detect conflicts between two schema states
        conflicts = detector.detect_conflicts(
            branch_a="feature-branch",
            branch_b="main",
            schema_a=feature_schema,
            schema_b=main_schema
        )

        # Check if auto-merge is possible
        if detector.can_auto_merge(conflicts):
            print("Safe to auto-merge")
        ```
    """

    def __init__(
        self,
        strict_mode: bool = True,
        type_coercion_allowed: bool = False,
    ):
        """
        Initialize SchemaConflictDetector.

        Args:
            strict_mode: If True, more situations are flagged as conflicts
            type_coercion_allowed: If True, some type changes are auto-resolvable
        """
        self._strict_mode = strict_mode
        self._type_coercion_allowed = type_coercion_allowed

        # Compatible type transitions (for type_coercion_allowed mode)
        self._compatible_types = {
            ("int", "float"): True,
            ("str", "Optional[str]"): True,
            ("int", "Optional[int]"): True,
            ("float", "Optional[float]"): True,
            ("bool", "Optional[bool]"): True,
        }

    def detect_conflicts(
        self,
        branch_a: str,
        branch_b: str,
        schema_a: Optional[Dict[str, Any]] = None,
        schema_b: Optional[Dict[str, Any]] = None,
        base_schema: Optional[Dict[str, Any]] = None,
    ) -> List[SchemaConflict]:
        """
        Detect schema conflicts between two branches.

        Args:
            branch_a: First branch identifier
            branch_b: Second branch identifier
            schema_a: Schema from branch A
            schema_b: Schema from branch B
            base_schema: Schema from common ancestor (for three-way comparison)

        Returns:
            List of detected schema conflicts
        """
        conflicts = []

        if not schema_a or not schema_b:
            return conflicts

        # Compare object types
        types_a = set(schema_a.keys())
        types_b = set(schema_b.keys())

        # Check for type additions/deletions
        deleted_in_b = types_a - types_b
        added_in_b = types_b - types_a
        common_types = types_a & types_b

        # Deletion conflicts
        for type_name in deleted_in_b:
            # Check if base had this type (true deletion vs. not yet added)
            if base_schema and type_name in base_schema:
                conflicts.append(SchemaConflict(
                    conflict_type=SchemaConflictType.DELETION_CONFLICT,
                    severity=SchemaConflictSeverity.ERROR,
                    object_type=type_name,
                    branch_a_value=schema_a[type_name],
                    branch_b_value=None,
                    base_value=base_schema.get(type_name),
                    branch_a_id=branch_a,
                    branch_b_id=branch_b,
                    resolution_suggestions=[
                        f"Keep type '{type_name}' from branch A",
                        f"Accept deletion from branch B",
                        f"Mark type '{type_name}' as deprecated"
                    ],
                    auto_resolvable=False,
                ))

        # Compare common types for field-level conflicts
        for type_name in common_types:
            type_conflicts = self._compare_type_schemas(
                type_name=type_name,
                schema_a=schema_a[type_name],
                schema_b=schema_b[type_name],
                base_schema=base_schema.get(type_name) if base_schema else None,
                branch_a=branch_a,
                branch_b=branch_b,
            )
            conflicts.extend(type_conflicts)

        return conflicts

    def _compare_type_schemas(
        self,
        type_name: str,
        schema_a: Dict[str, Any],
        schema_b: Dict[str, Any],
        base_schema: Optional[Dict[str, Any]],
        branch_a: str,
        branch_b: str,
    ) -> List[SchemaConflict]:
        """Compare schemas for a single object type."""
        conflicts = []

        fields_a = schema_a.get("fields", schema_a.get("properties", {}))
        fields_b = schema_b.get("fields", schema_b.get("properties", {}))
        base_fields = base_schema.get("fields", base_schema.get("properties", {})) if base_schema else {}

        # Get all field names
        all_fields = set(fields_a.keys()) | set(fields_b.keys())

        for field_name in all_fields:
            field_a = fields_a.get(field_name)
            field_b = fields_b.get(field_name)
            field_base = base_fields.get(field_name)

            # Both have the field - check for conflicts
            if field_a and field_b:
                field_conflict = self._detect_field_conflict(
                    type_name=type_name,
                    field_name=field_name,
                    field_a=field_a,
                    field_b=field_b,
                    field_base=field_base,
                    branch_a=branch_a,
                    branch_b=branch_b,
                )
                if field_conflict:
                    conflicts.append(field_conflict)

            # Field deleted in one branch
            elif field_a and not field_b:
                if field_base:  # Was in base - true deletion
                    conflicts.append(SchemaConflict(
                        conflict_type=SchemaConflictType.DELETION_CONFLICT,
                        severity=SchemaConflictSeverity.WARNING if not self._strict_mode else SchemaConflictSeverity.ERROR,
                        object_type=type_name,
                        field_name=field_name,
                        branch_a_value=field_a,
                        branch_b_value=None,
                        base_value=field_base,
                        branch_a_id=branch_a,
                        branch_b_id=branch_b,
                        resolution_suggestions=[
                            f"Keep field '{field_name}'",
                            f"Accept field deletion",
                            f"Mark field as deprecated"
                        ],
                        auto_resolvable=False,
                    ))

        return conflicts

    def _detect_field_conflict(
        self,
        type_name: str,
        field_name: str,
        field_a: Dict[str, Any],
        field_b: Dict[str, Any],
        field_base: Optional[Dict[str, Any]],
        branch_a: str,
        branch_b: str,
    ) -> Optional[SchemaConflict]:
        """Detect conflict for a single field."""

        # Check type mismatch
        type_a = field_a.get("type", field_a.get("annotation"))
        type_b = field_b.get("type", field_b.get("annotation"))

        if type_a != type_b:
            # Check if it's a compatible type change
            is_compatible = self._is_compatible_type_change(type_a, type_b)

            return SchemaConflict(
                conflict_type=SchemaConflictType.TYPE_MISMATCH,
                severity=SchemaConflictSeverity.WARNING if is_compatible else SchemaConflictSeverity.ERROR,
                object_type=type_name,
                field_name=field_name,
                branch_a_value={"type": type_a, "full": field_a},
                branch_b_value={"type": type_b, "full": field_b},
                base_value=field_base,
                branch_a_id=branch_a,
                branch_b_id=branch_b,
                resolution_suggestions=[
                    f"Use type '{type_a}' from branch A",
                    f"Use type '{type_b}' from branch B",
                    "Create migration for type change"
                ] + ([f"Auto-coerce (compatible: {type_a} -> {type_b})"] if is_compatible else []),
                auto_resolvable=is_compatible and self._type_coercion_allowed,
                recommended_resolution=f"Use type '{type_b}'" if is_compatible else None,
            )

        # Check default value conflict
        default_a = field_a.get("default")
        default_b = field_b.get("default")
        base_default = field_base.get("default") if field_base else None

        if default_a != default_b:
            # If base matches one side, it's auto-resolvable
            auto_resolve = (base_default == default_a) or (base_default == default_b)

            if auto_resolve:
                # Use the changed value
                recommended = default_b if base_default == default_a else default_a
            else:
                recommended = None

            return SchemaConflict(
                conflict_type=SchemaConflictType.DEFAULT_CHANGE,
                severity=SchemaConflictSeverity.WARNING,
                object_type=type_name,
                field_name=field_name,
                branch_a_value=default_a,
                branch_b_value=default_b,
                base_value=base_default,
                branch_a_id=branch_a,
                branch_b_id=branch_b,
                resolution_suggestions=[
                    f"Use default '{default_a}' from branch A",
                    f"Use default '{default_b}' from branch B",
                ],
                auto_resolvable=auto_resolve,
                recommended_resolution=f"Use default '{recommended}'" if recommended else None,
            )

        # Check required/optional conflict
        required_a = field_a.get("required", True)
        required_b = field_b.get("required", True)

        if required_a != required_b:
            return SchemaConflict(
                conflict_type=SchemaConflictType.REQUIRED_CHANGE,
                severity=SchemaConflictSeverity.WARNING,
                object_type=type_name,
                field_name=field_name,
                branch_a_value=required_a,
                branch_b_value=required_b,
                base_value=field_base.get("required") if field_base else None,
                branch_a_id=branch_a,
                branch_b_id=branch_b,
                resolution_suggestions=[
                    "Make field required",
                    "Make field optional",
                ],
                auto_resolvable=not self._strict_mode,
            )

        return None

    def _is_compatible_type_change(self, type_a: Any, type_b: Any) -> bool:
        """Check if a type change is compatible (widening only)."""
        if not self._type_coercion_allowed:
            return False

        key = (str(type_a), str(type_b))
        reverse_key = (str(type_b), str(type_a))

        return key in self._compatible_types or reverse_key in self._compatible_types

    def can_auto_merge(self, conflicts: List[SchemaConflict]) -> bool:
        """
        Check if all conflicts can be auto-merged.

        Args:
            conflicts: List of schema conflicts

        Returns:
            True if safe to auto-merge
        """
        if not conflicts:
            return True

        return all(c.auto_resolvable for c in conflicts)

    def suggest_resolution(self, conflict: SchemaConflict) -> str:
        """
        Suggest the best resolution for a conflict.

        Args:
            conflict: The conflict to resolve

        Returns:
            Resolution suggestion string
        """
        if conflict.recommended_resolution:
            return conflict.recommended_resolution

        if conflict.resolution_suggestions:
            return conflict.resolution_suggestions[0]

        # Default suggestions by type
        suggestions = {
            SchemaConflictType.TYPE_MISMATCH: "Review type compatibility and choose appropriate type",
            SchemaConflictType.DELETION_CONFLICT: "Decide whether to keep or remove the item",
            SchemaConflictType.SCHEMA_CHANGE: "Review changes and select preferred schema",
            SchemaConflictType.CONSTRAINT_VIOLATION: "Reconcile conflicting constraints",
            SchemaConflictType.REQUIRED_CHANGE: "Make field optional if data exists without it",
            SchemaConflictType.DEFAULT_CHANGE: "Use newer default value",
        }

        return suggestions.get(conflict.conflict_type, "Manual resolution required")


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "SchemaConflictType",
    "SchemaConflictSeverity",
    "SchemaConflict",
    "SchemaConflictBatch",
    "SchemaConflictDetector",
]
