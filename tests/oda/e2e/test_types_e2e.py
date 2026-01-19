from __future__ import annotations

from datetime import datetime

import pytest

from lib.oda.ontology.types import (
    CascadePolicy,
    ConstraintSeverity,
    ConstraintType,
    InterfaceDefinition,
    LinkConstraint,
    LinkDirection,
    LinkTypeConstraints,
    LinkTypeMetadata,
    MethodSpec,
    PropertyConstraint,
    PropertyDataType,
    PropertyDefinition,
    PropertySpec,
    ReferentialIntegrityChecker,
    ResourceLifecycleStatus,
    SharedPropertyDefinition,
    SharedPropertyRegistry,
    get_allowed_transitions,
    get_builtin_property,
    get_property_validator,
    is_valid_transition,
    list_builtin_properties,
)


def test_status_lifecycle_helpers_and_transitions() -> None:
    assert ResourceLifecycleStatus.DRAFT.get_stage() == "development"
    assert ResourceLifecycleStatus.ACTIVE.get_stage() == "production"
    assert ResourceLifecycleStatus.DEPRECATED.get_stage() == "deprecation"
    assert ResourceLifecycleStatus.ARCHIVED.get_stage() == "end_of_life"

    assert ResourceLifecycleStatus.ACTIVE.is_usable() is True
    assert ResourceLifecycleStatus.BETA.is_usable() is True
    assert ResourceLifecycleStatus.DRAFT.is_usable() is False

    assert ResourceLifecycleStatus.ARCHIVED.is_modifiable() is False
    assert ResourceLifecycleStatus.ACTIVE.is_modifiable() is True

    assert set(get_allowed_transitions(ResourceLifecycleStatus.DRAFT)) == {
        ResourceLifecycleStatus.EXPERIMENTAL,
        ResourceLifecycleStatus.ACTIVE,
        ResourceLifecycleStatus.DELETED,
    }
    assert is_valid_transition(ResourceLifecycleStatus.DRAFT, ResourceLifecycleStatus.EXPERIMENTAL) is True
    assert is_valid_transition(ResourceLifecycleStatus.DRAFT, ResourceLifecycleStatus.BETA) is False


def test_property_constraint_validates_pattern_and_ranges() -> None:
    with pytest.raises(ValueError, match="Invalid regex pattern"):
        PropertyConstraint(pattern="(")

    with pytest.raises(ValueError, match="min_value"):
        PropertyConstraint(min_value=10, max_value=1)

    with pytest.raises(ValueError, match="min_length"):
        PropertyConstraint(min_length=10, max_length=1)


def test_property_definition_validation_and_json_schema() -> None:
    with pytest.raises(ValueError, match="snake_case"):
        PropertyDefinition(
            name="NotSnakeCase",
            property_type=PropertyDataType.STRING,
        )

    array_prop = PropertyDefinition(
        name="tags",
        property_type=PropertyDataType.ARRAY,
        constraints=PropertyConstraint(),
    )
    assert array_prop.element_type == PropertyDataType.STRING

    with pytest.raises(ValueError, match="compute_dependencies"):
        PropertyDefinition(
            name="computed_value",
            property_type=PropertyDataType.INTEGER,
            is_computed=True,
            compute_function="compute_value",
        )

    prop = PropertyDefinition(
        name="age",
        property_type=PropertyDataType.INTEGER,
        constraints=PropertyConstraint(min_value=0, max_value=120),
        description="Age in years",
    )
    schema = prop.to_json_schema()
    assert schema["type"] == "integer"
    assert schema["minimum"] == 0
    assert schema["maximum"] == 120


def test_property_validator_builtin_and_missing_custom_validator() -> None:
    validator = get_property_validator()

    email_def = PropertyDefinition(
        name="email",
        property_type=PropertyDataType.EMAIL,
        constraints=PropertyConstraint(required=True, custom_validator="email"),
    )
    assert validator.validate(email_def, "user@example.com") == []

    violations = validator.validate(email_def, "not-an-email")
    assert any(v.constraint_type == ConstraintType.CUSTOM for v in violations)

    missing_validator_def = PropertyDefinition(
        name="slug",
        property_type=PropertyDataType.STRING,
        constraints=PropertyConstraint(custom_validator="does_not_exist"),
    )
    violations = validator.validate(missing_validator_def, "anything")
    assert any(v.constraint_type == ConstraintType.CUSTOM for v in violations)
    assert any(v.severity == ConstraintSeverity.WARNING for v in violations)


def test_link_constraint_validates_max_gte_min() -> None:
    with pytest.raises(ValueError, match="max_links"):
        LinkConstraint(min_links=2, max_links=1)


def test_link_type_metadata_validates_backing_table_and_bidirectional_reverse() -> None:
    with pytest.raises(ValueError, match="backing_table_name"):
        LinkTypeMetadata(
            link_type_id="task_depends_on_task",
            source_type="Task",
            target_type="Task",
            cardinality="N:N",
            # missing backing_table_name
        )

    link = LinkTypeMetadata(
        link_type_id="task_assigned_to_agent",
        source_type="Task",
        target_type="Agent",
        cardinality="1:N",
        direction=LinkDirection.BIDIRECTIONAL,
        # reverse_link_id omitted on purpose
        on_source_delete=CascadePolicy.RESTRICT,
        on_target_delete=CascadePolicy.SET_NULL,
        description="Assignment relationship",
    )
    assert link.reverse_link_id == "task_assigned_to_agent_reverse"

    data = link.to_json()
    assert data["link_type_id"] == "task_assigned_to_agent"
    assert data["on_delete"] == CascadePolicy.RESTRICT.value
    assert data["on_update"] == CascadePolicy.CASCADE.value


def test_referential_integrity_checker_rules() -> None:
    metadata = LinkTypeMetadata(
        link_type_id="task_assigned_to_agent",
        source_type="Task",
        target_type="Agent",
        cardinality="1:N",
        constraints=LinkTypeConstraints(
            min_cardinality=1,
            max_cardinality=2,
            unique_target=True,
            required=True,
            allowed_source_statuses=["active"],
            allowed_target_statuses=["active"],
        ),
    )

    checker = ReferentialIntegrityChecker()

    # Exceed max_cardinality
    violation = checker.validate_cardinality(metadata, current_link_count=2, adding=True)
    assert violation is not None
    assert violation.violation_type.value == "cardinality_violation"

    # Remove below required minimum
    violation = checker.validate_cardinality(metadata, current_link_count=1, adding=False)
    assert violation is not None

    # Unique constraint
    violation = checker.validate_unique_constraint(
        metadata,
        target_id="agent-123",
        existing_target_ids={"agent-123"},
    )
    assert violation is not None

    # Status constraints
    violation = checker.validate_target_status(metadata, target_status="archived")
    assert violation is not None

    violations = checker.validate_all(
        metadata=metadata,
        source_id="task-1",
        target_id="agent-123",
        source_status="active",
        target_status="archived",
        current_link_count=0,
        existing_target_ids=set(),
        adding=True,
    )
    assert violations


@pytest.mark.asyncio
async def test_referential_integrity_checker_custom_validator() -> None:
    metadata = LinkTypeMetadata(
        link_type_id="task_links_to_task",
        source_type="Task",
        target_type="Task",
        cardinality="1:N",
        constraints=LinkTypeConstraints(custom_validator="no_self_link"),
    )

    checker = ReferentialIntegrityChecker()
    checker.register_validator("no_self_link", lambda source_id, target_id, ctx: source_id != target_id)

    violation = await checker.run_custom_validator(
        metadata=metadata,
        source_id="task-1",
        target_id="task-1",
        context={},
    )
    assert violation is not None
    assert violation.violation_type.value == "custom_validation_failed"


def test_interface_type_models_validate_and_helpers_work() -> None:
    with pytest.raises(ValueError, match="double underscore"):
        PropertySpec(name="__bad", type_hint="str")

    with pytest.raises(ValueError, match="return type"):
        MethodSpec(name="do_thing", signature="(self)")

    with pytest.raises(ValueError, match="cannot extend itself"):
        InterfaceDefinition(
            interface_id="IVersionable",
            description="Test interface",
            extends=["IVersionable"],
        )

    iface = InterfaceDefinition(
        interface_id="IVersionable",
        description="Objects that support versioning",
        required_properties=[PropertySpec(name="version", type_hint="int")],
        required_methods=[MethodSpec(name="bump_version", signature="(self) -> int")],
    )
    assert iface.get_all_property_names() == ["version"]
    assert iface.get_all_method_names() == ["bump_version"]
    assert iface.get_property_spec("version") is not None
    assert iface.get_method_spec("bump_version") is not None


def test_shared_property_registry_registers_and_tracks_usage() -> None:
    registry = SharedPropertyRegistry()

    definition = SharedPropertyDefinition(
        property_id="created_at",
        description="Creation time",
        type_hint="datetime",
        default_factory="datetime.now",
        category="audit",
        is_indexed=True,
    )
    registry.register_property(definition)
    assert registry.has_property("created_at") is True

    usage = registry.register_usage(property_id="created_at", object_type="Task")
    assert usage.property_id == "created_at"
    assert usage.object_type == "Task"
    datetime.fromisoformat(usage.registered_at)

    with pytest.raises(ValueError, match="already registered"):
        registry.register_property(definition)

    with pytest.raises(ValueError, match="already uses"):
        registry.register_usage(property_id="created_at", object_type="Task")

    assert registry.get_usages_for_property("created_at") == ["Task"]
    assert registry.get_properties_for_object("Task") == ["created_at"]

    exported = registry.export_dict()
    assert exported["statistics"]["total_properties"] == 1
    assert exported["statistics"]["total_usages"] == 1


def test_builtin_shared_properties_are_available() -> None:
    assert "created_at" in list_builtin_properties()
    created_at = get_builtin_property("created_at")
    assert created_at is not None
    assert created_at.property_id == "created_at"

