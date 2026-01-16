"""
Orion ODA v4.0 - LinkType Registry

Centralized registry for all LinkType definitions.
Palantir Foundry Pattern: LinkTypes are first-class citizens with their own registry.

This module provides:
- LinkTypeRegistry: Single source of truth for all link type definitions
- @register_link_type: Decorator for registering link types from ObjectType classes
- Bidirectional link resolution
- LinkType validation rules
- JSON schema export

Schema Version: 4.0.0
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Type,
    TypeVar,
    Union,
)

from lib.oda.ontology.ontology_types import Cardinality, Link
from lib.oda.ontology.types.link_types import (
    CascadePolicy,
    IntegrityViolation,
    IntegrityViolationType,
    LinkDirection,
    LinkTypeConstraints,
    LinkTypeMetadata,
    ReferentialIntegrityChecker,
)

if TYPE_CHECKING:
    from lib.oda.ontology.ontology_types import OntologyObject

# Schema version for export
LINK_SCHEMA_VERSION = "4.0.0"
LINK_SCHEMA_GENERATED_BY = "Orion ODA v4.0 LinkTypeRegistry"

T = TypeVar("T")


# =============================================================================
# VALIDATION ERROR
# =============================================================================


@dataclass(frozen=True)
class LinkTypeValidationError:
    """
    Represents a validation error during link type registration.

    Attributes:
        link_type_id: The link type that failed validation
        error_code: Error code for programmatic handling
        message: Human-readable error message
    """
    link_type_id: str
    error_code: str
    message: str


# =============================================================================
# LINK TYPE REGISTRY
# =============================================================================


class LinkTypeRegistry:
    """
    Centralized registry for all LinkType definitions.

    Palantir Foundry Pattern:
    - LinkTypes are first-class citizens in the Ontology
    - Each link type is registered with full metadata
    - Bidirectional links are resolved automatically
    - M:N links validate backing table configuration

    Example:
        ```python
        registry = LinkTypeRegistry()

        # Register a link type
        registry.register(LinkTypeMetadata(
            link_type_id="task_assigned_to_agent",
            source_type="Task",
            target_type="Agent",
            cardinality="N:1",
            direction=LinkDirection.BIDIRECTIONAL,
            reverse_link_id="agent_assigned_tasks",
        ))

        # Query link types
        task_links = registry.get_links_for_source("Task")
        agent_links = registry.get_links_for_target("Agent")

        # Resolve bidirectional navigation
        reverse = registry.get_reverse_link("task_assigned_to_agent")
        ```
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._links: Dict[str, LinkTypeMetadata] = {}
        self._source_index: Dict[str, Set[str]] = {}  # source_type -> link_type_ids
        self._target_index: Dict[str, Set[str]] = {}  # target_type -> link_type_ids
        self._reverse_map: Dict[str, str] = {}  # link_type_id -> reverse_link_type_id
        self._integrity_checker = ReferentialIntegrityChecker()
        self._validation_errors: List[LinkTypeValidationError] = []

    # -------------------------------------------------------------------------
    # Registration (Task 1.1.1)
    # -------------------------------------------------------------------------

    def register(
        self,
        metadata: LinkTypeMetadata,
        *,
        overwrite: bool = False,
    ) -> bool:
        """
        Register a link type with the registry.

        Args:
            metadata: Full LinkTypeMetadata definition
            overwrite: If True, allow overwriting existing registration

        Returns:
            True if registration succeeded, False if validation failed

        Raises:
            ValueError: If link_type_id already exists and overwrite=False
        """
        link_type_id = metadata.link_type_id

        # Check for duplicate
        if link_type_id in self._links and not overwrite:
            self._validation_errors.append(
                LinkTypeValidationError(
                    link_type_id=link_type_id,
                    error_code="DUPLICATE_LINK_TYPE",
                    message=f"LinkType '{link_type_id}' already registered",
                )
            )
            raise ValueError(f"LinkType '{link_type_id}' already registered")

        # Validate the link type (Task 1.1.3)
        validation_errors = self._validate_link_type(metadata)
        if validation_errors:
            self._validation_errors.extend(validation_errors)
            return False

        # Store in registry
        self._links[link_type_id] = metadata

        # Update source index
        source_type = metadata.source_type
        if source_type not in self._source_index:
            self._source_index[source_type] = set()
        self._source_index[source_type].add(link_type_id)

        # Update target index
        target_type = metadata.target_type
        if target_type not in self._target_index:
            self._target_index[target_type] = set()
        self._target_index[target_type].add(link_type_id)

        # Update reverse link map (Task 1.1.4)
        if metadata.reverse_link_id:
            self._reverse_map[link_type_id] = metadata.reverse_link_id
            # Also map the reverse direction
            self._reverse_map[metadata.reverse_link_id] = link_type_id

        return True

    def register_from_link(
        self,
        link: Link,
        source_type_name: str,
        *,
        on_source_delete: CascadePolicy = CascadePolicy.CASCADE,
        on_target_delete: CascadePolicy = CascadePolicy.SET_NULL,
    ) -> bool:
        """
        Register a link type from a Link[T] definition on an ObjectType.

        This is used internally by @register_link_type decorator.

        Args:
            link: The Link[T] instance from ObjectType
            source_type_name: Name of the source ObjectType
            on_source_delete: Cascade policy for source deletion
            on_target_delete: Cascade policy for target deletion

        Returns:
            True if registration succeeded
        """
        # Resolve target type name
        target = link.target
        if isinstance(target, str):
            target_type_name = target
        elif hasattr(target, "__name__"):
            target_type_name = target.__name__
        else:
            target_type_name = str(target)

        # Map Cardinality enum to string
        cardinality_map = {
            Cardinality.ONE_TO_ONE: "1:1",
            Cardinality.ONE_TO_MANY: "1:N",
            Cardinality.MANY_TO_ONE: "N:1",
            Cardinality.MANY_TO_MANY: "N:N",
        }
        cardinality = cardinality_map.get(link.cardinality, "1:N")

        # Determine direction
        direction = (
            LinkDirection.BIDIRECTIONAL
            if link.reverse_link_id
            else LinkDirection.DIRECTED
        )

        # Create metadata
        metadata = LinkTypeMetadata(
            link_type_id=link.link_type_id,
            source_type=source_type_name,
            target_type=target_type_name,
            cardinality=cardinality,
            direction=direction,
            reverse_link_id=link.reverse_link_id,
            backing_table_name=link.backing_table_name,
            is_materialized=link.is_materialized,
            description=link.description,
            on_source_delete=on_source_delete,
            on_target_delete=on_target_delete,
        )

        return self.register(metadata, overwrite=True)

    # -------------------------------------------------------------------------
    # Validation Rules (Task 1.1.3)
    # -------------------------------------------------------------------------

    def _validate_link_type(
        self, metadata: LinkTypeMetadata
    ) -> List[LinkTypeValidationError]:
        """
        Validate a link type before registration.

        Validation rules:
        1. link_type_id must be unique (checked in register())
        2. M:N cardinality requires backing_table_name (checked by Pydantic)
        3. Bidirectional links must have reverse_link_id (checked by Pydantic)
        4. Reverse link ID must not conflict with existing link IDs
        5. source_type and target_type should be valid ObjectType names

        Args:
            metadata: LinkType to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors: List[LinkTypeValidationError] = []

        # Rule 4: Check reverse link ID conflict
        if metadata.reverse_link_id:
            reverse_id = metadata.reverse_link_id

            # Cannot be same as forward link
            if reverse_id == metadata.link_type_id:
                errors.append(
                    LinkTypeValidationError(
                        link_type_id=metadata.link_type_id,
                        error_code="REVERSE_LINK_SELF_REFERENCE",
                        message=f"reverse_link_id cannot be the same as link_type_id",
                    )
                )

            # Check if reverse_link_id conflicts with existing link
            if reverse_id in self._links:
                existing = self._links[reverse_id]
                # It's valid if it's the actual reverse link
                if not (
                    existing.source_type == metadata.target_type
                    and existing.target_type == metadata.source_type
                    and existing.reverse_link_id == metadata.link_type_id
                ):
                    errors.append(
                        LinkTypeValidationError(
                            link_type_id=metadata.link_type_id,
                            error_code="REVERSE_LINK_CONFLICT",
                            message=f"reverse_link_id '{reverse_id}' conflicts with existing link",
                        )
                    )

        return errors

    # -------------------------------------------------------------------------
    # Query Methods
    # -------------------------------------------------------------------------

    def get(self, link_type_id: str) -> Optional[LinkTypeMetadata]:
        """
        Get a link type by ID.

        Args:
            link_type_id: The link type identifier

        Returns:
            LinkTypeMetadata or None if not found
        """
        return self._links.get(link_type_id)

    def get_links_for_source(self, source_type: str) -> List[LinkTypeMetadata]:
        """
        Get all link types where the given type is the source.

        Args:
            source_type: ObjectType name

        Returns:
            List of LinkTypeMetadata where source_type matches
        """
        link_ids = self._source_index.get(source_type, set())
        return [self._links[lid] for lid in link_ids if lid in self._links]

    def get_links_for_target(self, target_type: str) -> List[LinkTypeMetadata]:
        """
        Get all link types where the given type is the target.

        Args:
            target_type: ObjectType name

        Returns:
            List of LinkTypeMetadata where target_type matches
        """
        link_ids = self._target_index.get(target_type, set())
        return [self._links[lid] for lid in link_ids if lid in self._links]

    def get_links_between(
        self, source_type: str, target_type: str
    ) -> List[LinkTypeMetadata]:
        """
        Get all link types between two object types.

        Args:
            source_type: Source ObjectType name
            target_type: Target ObjectType name

        Returns:
            List of LinkTypeMetadata connecting the two types
        """
        source_links = set(self._source_index.get(source_type, set()))
        target_links = set(self._target_index.get(target_type, set()))
        intersection = source_links & target_links

        # Filter to only exact matches
        return [
            self._links[lid]
            for lid in intersection
            if self._links[lid].source_type == source_type
            and self._links[lid].target_type == target_type
        ]

    def list_all(self) -> List[LinkTypeMetadata]:
        """
        Get all registered link types.

        Returns:
            List of all LinkTypeMetadata in registry
        """
        return list(self._links.values())

    # -------------------------------------------------------------------------
    # Bidirectional Link Resolution (Task 1.1.4)
    # -------------------------------------------------------------------------

    def get_reverse_link(self, link_type_id: str) -> Optional[LinkTypeMetadata]:
        """
        Get the reverse link type for bidirectional navigation.

        Args:
            link_type_id: The forward link type ID

        Returns:
            Reverse LinkTypeMetadata or None if not bidirectional
        """
        reverse_id = self._reverse_map.get(link_type_id)
        if not reverse_id:
            return None

        # First check if reverse is registered
        if reverse_id in self._links:
            return self._links[reverse_id]

        # If not registered, synthesize reverse metadata from forward link
        forward = self._links.get(link_type_id)
        if not forward:
            return None

        # Synthesize reverse link metadata
        reverse_cardinality_map = {
            "1:1": "1:1",
            "1:N": "N:1",
            "N:1": "1:N",
            "N:N": "N:N",
        }

        return LinkTypeMetadata(
            link_type_id=reverse_id,
            source_type=forward.target_type,
            target_type=forward.source_type,
            cardinality=reverse_cardinality_map.get(forward.cardinality, "1:N"),
            direction=forward.direction,
            reverse_link_id=forward.link_type_id,
            backing_table_name=forward.backing_table_name,
            is_materialized=forward.is_materialized,
            description=f"Reverse of: {forward.description or forward.link_type_id}",
            on_source_delete=forward.on_target_delete,
            on_target_delete=forward.on_source_delete,
        )

    def resolve_bidirectional_path(
        self, start_type: str, end_type: str, max_depth: int = 3
    ) -> List[List[str]]:
        """
        Find all paths between two object types using bidirectional links.

        Args:
            start_type: Starting ObjectType name
            end_type: Ending ObjectType name
            max_depth: Maximum path length to search

        Returns:
            List of paths, where each path is a list of link_type_ids
        """
        if start_type == end_type:
            return [[]]

        paths: List[List[str]] = []
        visited: Set[str] = set()

        def dfs(current_type: str, path: List[str], depth: int) -> None:
            if depth > max_depth:
                return

            if current_type == end_type:
                paths.append(path.copy())
                return

            if current_type in visited:
                return

            visited.add(current_type)

            # Try outgoing links (forward direction)
            for link in self.get_links_for_source(current_type):
                path.append(link.link_type_id)
                dfs(link.target_type, path, depth + 1)
                path.pop()

            # Try incoming links (reverse direction via bidirectional)
            for link in self.get_links_for_target(current_type):
                if link.direction == LinkDirection.BIDIRECTIONAL:
                    reverse_id = link.reverse_link_id or f"{link.link_type_id}_reverse"
                    path.append(reverse_id)
                    dfs(link.source_type, path, depth + 1)
                    path.pop()

            visited.remove(current_type)

        dfs(start_type, [], 0)
        return paths

    # -------------------------------------------------------------------------
    # Integrity Checking
    # -------------------------------------------------------------------------

    def get_integrity_checker(self) -> ReferentialIntegrityChecker:
        """Get the registry's integrity checker instance."""
        return self._integrity_checker

    def validate_link(
        self,
        link_type_id: str,
        source_id: str,
        target_id: str,
        source_status: str = "active",
        target_status: str = "active",
        current_link_count: int = 0,
        existing_target_ids: Optional[Set[str]] = None,
    ) -> List[IntegrityViolation]:
        """
        Validate a link creation using all registered constraints.

        Args:
            link_type_id: Link type to validate against
            source_id: Source object ID
            target_id: Target object ID
            source_status: Source object status
            target_status: Target object status
            current_link_count: Current number of links from source
            existing_target_ids: Already linked target IDs

        Returns:
            List of violations (empty if valid)
        """
        metadata = self.get(link_type_id)
        if not metadata:
            return [
                IntegrityViolation(
                    violation_type=IntegrityViolationType.INVALID_OBJECT_TYPE,
                    link_type_id=link_type_id,
                    source_id=source_id,
                    target_id=target_id,
                    message=f"Unknown link type: {link_type_id}",
                )
            ]

        return self._integrity_checker.validate_all(
            metadata=metadata,
            source_id=source_id,
            target_id=target_id,
            source_status=source_status,
            target_status=target_status,
            current_link_count=current_link_count,
            existing_target_ids=existing_target_ids or set(),
            adding=True,
        )

    # -------------------------------------------------------------------------
    # Export Methods
    # -------------------------------------------------------------------------

    def export_json(self, path: Union[str, Path]) -> None:
        """
        Export all link types to JSON schema file.

        Args:
            path: Output file path
        """
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "version": LINK_SCHEMA_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by": LINK_SCHEMA_GENERATED_BY,
            "link_types": {
                link_id: metadata.to_json() for link_id, metadata in self._links.items()
            },
            "statistics": {
                "total_link_types": len(self._links),
                "bidirectional_links": sum(
                    1 for m in self._links.values() if m.direction == LinkDirection.BIDIRECTIONAL
                ),
                "many_to_many_links": sum(
                    1 for m in self._links.values() if m.is_many_to_many
                ),
            },
        }

        target.write_text(json.dumps(payload, indent=2))

    def get_validation_errors(self) -> List[LinkTypeValidationError]:
        """Get all validation errors from registration attempts."""
        return self._validation_errors.copy()

    def clear_validation_errors(self) -> None:
        """Clear accumulated validation errors."""
        self._validation_errors.clear()

    def __len__(self) -> int:
        """Return number of registered link types."""
        return len(self._links)

    def __contains__(self, link_type_id: str) -> bool:
        """Check if a link type is registered."""
        return link_type_id in self._links

    def __repr__(self) -> str:
        return f"LinkTypeRegistry(count={len(self._links)})"


# =============================================================================
# GLOBAL REGISTRY INSTANCE
# =============================================================================

_LINK_REGISTRY = LinkTypeRegistry()


def get_link_registry() -> LinkTypeRegistry:
    """Get the global LinkTypeRegistry instance."""
    return _LINK_REGISTRY


# =============================================================================
# DECORATOR (Task 1.1.2)
# =============================================================================


def register_link_type(
    cls: Optional[Type["OntologyObject"]] = None,
    *,
    on_source_delete: CascadePolicy = CascadePolicy.CASCADE,
    on_target_delete: CascadePolicy = CascadePolicy.SET_NULL,
) -> Union[Type["OntologyObject"], Callable[[Type["OntologyObject"]], Type["OntologyObject"]]]:
    """
    Decorator to register all Link[T] definitions from an ObjectType class.

    This decorator scans the class for Link[T] attributes and registers
    them with the global LinkTypeRegistry.

    Args:
        cls: The ObjectType class to scan (when used without parentheses)
        on_source_delete: Default cascade policy for source deletion
        on_target_delete: Default cascade policy for target deletion

    Returns:
        The decorated class (unchanged)

    Example:
        ```python
        @register_link_type
        @register_object_type
        class Task(OntologyObject):
            title: str
            assigned_to: ClassVar[Link[Agent]] = Link(
                target=Agent,
                link_type_id="task_assigned_to_agent",
                cardinality=Cardinality.MANY_TO_ONE,
            )

        # Or with custom cascade policies:
        @register_link_type(on_source_delete=CascadePolicy.RESTRICT)
        @register_object_type
        class Project(OntologyObject):
            ...
        ```
    """

    def decorator(klass: Type["OntologyObject"]) -> Type["OntologyObject"]:
        registry = get_link_registry()

        # Scan class attributes for Link instances
        for attr_name in dir(klass):
            try:
                attr_value = getattr(klass, attr_name, None)
                if isinstance(attr_value, Link):
                    registry.register_from_link(
                        link=attr_value,
                        source_type_name=klass.__name__,
                        on_source_delete=on_source_delete,
                        on_target_delete=on_target_delete,
                    )
            except Exception:
                # Skip attributes that raise errors during access
                pass

        return klass

    # Handle both @register_link_type and @register_link_type()
    if cls is not None:
        return decorator(cls)
    return decorator


def load_links_from_object_types() -> None:
    """
    Load all Link[T] definitions from registered ObjectTypes.

    Call this after all ObjectTypes are registered to populate
    the LinkTypeRegistry from existing Link definitions.
    """
    from lib.oda.ontology.registry import get_registry

    obj_registry = get_registry()
    link_registry = get_link_registry()

    for obj_name, obj_def in obj_registry.list_objects().items():
        for link_id, link_def in obj_def.links.items():
            # Convert LinkDefinition to LinkTypeMetadata
            metadata = LinkTypeMetadata(
                link_type_id=link_def.link_type_id,
                source_type=obj_name,
                target_type=link_def.target,
                cardinality=link_def.cardinality,
                direction=(
                    LinkDirection.BIDIRECTIONAL
                    if link_def.reverse_link_id
                    else LinkDirection.DIRECTED
                ),
                reverse_link_id=link_def.reverse_link_id,
                backing_table_name=link_def.backing_table_name,
                is_materialized=link_def.is_materialized,
                description=link_def.description,
            )

            try:
                link_registry.register(metadata, overwrite=True)
            except ValueError:
                # Skip duplicates
                pass


def export_link_registry(path: Union[str, Path]) -> None:
    """
    Export the global LinkTypeRegistry to JSON.

    Ensures all ObjectTypes are loaded before export.

    Args:
        path: Output file path
    """
    load_links_from_object_types()
    get_link_registry().export_json(path)
