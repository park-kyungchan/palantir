"""
Test fixtures for ontology-definition package tests.

Provides reusable test data for:
- ObjectType creation and validation
- LinkType creation and validation
- MandatoryControlConfig for row-level security
- RestrictedViewPolicy for access control
"""

import pytest

from ontology_definition import (
    Cardinality,
    ComparisonOperator,
    DataType,
    DataTypeSpec,
    LinkType,
    LogicalOperator,
    MandatoryControlConfig,
    ObjectStatus,
    ObjectType,
    PolicyTerm,
    PolicyTermType,
    PrimaryKeyDefinition,
    PropertyConstraints,
    PropertyDefinition,
    RestrictedViewPolicy,
)
from ontology_definition.core.enums import (
    ClassificationLevel,
    ControlType,
    ForeignKeyLocation,
    LinkImplementationType,
)
from ontology_definition.security.restricted_view import (
    IdentifierType,
    UserAttributeMapping,
)
from ontology_definition.types.link_type import (
    BackingTableConfig,
    CardinalityConfig,
    ForeignKeyConfig,
    LinkImplementation,
    ObjectTypeReference,
)

# =============================================================================
# ObjectType Fixtures
# =============================================================================

@pytest.fixture
def sample_object_type():
    """Create a valid ObjectType for testing."""
    return ObjectType(
        api_name="Employee",
        display_name="Employee",
        description="Company employee entity",
        primary_key=PrimaryKeyDefinition(property_api_name="employeeId"),
        properties=[
            PropertyDefinition(
                api_name="employeeId",
                display_name="Employee ID",
                data_type=DataTypeSpec(type=DataType.STRING),
                constraints=PropertyConstraints(required=True, unique=True),
            ),
            PropertyDefinition(
                api_name="name",
                display_name="Employee Name",
                data_type=DataTypeSpec(type=DataType.STRING),
                constraints=PropertyConstraints(required=True),
            ),
            PropertyDefinition(
                api_name="age",
                display_name="Age",
                data_type=DataTypeSpec(type=DataType.INTEGER),
            ),
            PropertyDefinition(
                api_name="email",
                display_name="Email",
                data_type=DataTypeSpec(type=DataType.STRING),
            ),
        ],
        status=ObjectStatus.ACTIVE,
    )


@pytest.fixture
def minimal_object_type():
    """Create a minimal valid ObjectType with just one property."""
    return ObjectType(
        api_name="Simple",
        display_name="Simple",
        primary_key=PrimaryKeyDefinition(property_api_name="id"),
        properties=[
            PropertyDefinition(
                api_name="id",
                display_name="ID",
                data_type=DataTypeSpec(type=DataType.STRING),
            ),
        ],
    )


@pytest.fixture
def object_type_with_constraints():
    """Create an ObjectType with various property constraints."""
    from ontology_definition.constraints.property_constraints import (
        NumericConstraints,
        StringConstraints,
    )
    return ObjectType(
        api_name="Document",
        display_name="Document",
        primary_key=PrimaryKeyDefinition(property_api_name="documentId"),
        properties=[
            PropertyDefinition(
                api_name="documentId",
                display_name="Document ID",
                data_type=DataTypeSpec(type=DataType.STRING),
                constraints=PropertyConstraints(required=True, unique=True),
            ),
            PropertyDefinition(
                api_name="title",
                display_name="Title",
                data_type=DataTypeSpec(type=DataType.STRING),
                constraints=PropertyConstraints(
                    required=True,
                    string=StringConstraints(min_length=1, max_length=255),
                ),
            ),
            PropertyDefinition(
                api_name="status",
                display_name="Status",
                data_type=DataTypeSpec(type=DataType.STRING),
                constraints=PropertyConstraints(
                    enum=["DRAFT", "PUBLISHED", "ARCHIVED"],
                ),
            ),
            PropertyDefinition(
                api_name="priority",
                display_name="Priority",
                data_type=DataTypeSpec(type=DataType.INTEGER),
                constraints=PropertyConstraints(
                    numeric=NumericConstraints(min_value=1, max_value=10),
                ),
            ),
        ],
    )


# =============================================================================
# LinkType Fixtures
# =============================================================================

@pytest.fixture
def sample_link_type():
    """Create a valid LinkType (MANY_TO_ONE with foreign key)."""
    return LinkType(
        api_name="EmployeeToDepartment",
        display_name="Employee to Department",
        description="Links employee to their department",
        source_object_type=ObjectTypeReference(api_name="Employee"),
        target_object_type=ObjectTypeReference(api_name="Department"),
        cardinality=CardinalityConfig(type=Cardinality.MANY_TO_ONE),
        implementation=LinkImplementation(
            type=LinkImplementationType.FOREIGN_KEY,
            foreign_key=ForeignKeyConfig(
                foreign_key_property="departmentId",
                foreign_key_location=ForeignKeyLocation.SOURCE,
            ),
        ),
    )


@pytest.fixture
def many_to_many_link_type():
    """Create a valid MANY_TO_MANY LinkType with backing table."""
    return LinkType(
        api_name="ProjectToMember",
        display_name="Project to Member",
        description="Links projects to team members",
        source_object_type=ObjectTypeReference(api_name="Project"),
        target_object_type=ObjectTypeReference(api_name="Member"),
        cardinality=CardinalityConfig(type=Cardinality.MANY_TO_MANY),
        implementation=LinkImplementation(
            type=LinkImplementationType.BACKING_TABLE,
            backing_table=BackingTableConfig(
                source_key_column="project_id",
                target_key_column="member_id",
            ),
        ),
    )


# =============================================================================
# MandatoryControl Fixtures
# =============================================================================

@pytest.fixture
def sample_mandatory_control():
    """Create a valid MandatoryControlConfig for MARKINGS type."""
    return MandatoryControlConfig(
        property_api_name="securityMarking",
        control_type=ControlType.MARKINGS,
        marking_column_mapping="security_markings",
        allowed_markings=["550e8400-e29b-41d4-a716-446655440000"],
    )


@pytest.fixture
def organizations_mandatory_control():
    """Create a valid MandatoryControlConfig for ORGANIZATIONS type."""
    return MandatoryControlConfig(
        property_api_name="organizationId",
        control_type=ControlType.ORGANIZATIONS,
        allowed_organizations=["550e8400-e29b-41d4-a716-446655440001"],
    )


@pytest.fixture
def classifications_mandatory_control():
    """Create a valid MandatoryControlConfig for CLASSIFICATIONS type."""
    return MandatoryControlConfig(
        property_api_name="classificationLevel",
        control_type=ControlType.CLASSIFICATIONS,
        max_classification_level=ClassificationLevel.SECRET,
    )


# =============================================================================
# RestrictedViewPolicy Fixtures
# =============================================================================

@pytest.fixture
def sample_restricted_view():
    """Create a valid RestrictedViewPolicy with user attribute comparison."""
    return RestrictedViewPolicy(
        logical_operator=LogicalOperator.AND,
        terms=[
            PolicyTerm(
                term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
                column_name="tenantId",
                user_attribute="user.tenantId",
                comparison_operator=ComparisonOperator.EQUALS,
            ),
        ],
        enabled=True,
        description="Tenant isolation policy",
    )


@pytest.fixture
def marking_based_restricted_view():
    """Create a valid RestrictedViewPolicy with MARKING_CHECK term."""
    return RestrictedViewPolicy(
        logical_operator=LogicalOperator.AND,
        terms=[
            PolicyTerm(
                term_type=PolicyTermType.MARKING_CHECK,
                column_name="securityMarkings",
            ),
        ],
        user_attribute_mapping=UserAttributeMapping(
            identifier_type=IdentifierType.UUID,
            markings_attribute="user.markings",
        ),
        enabled=True,
        description="Marking-based access policy",
    )


@pytest.fixture
def multi_term_restricted_view():
    """Create a RestrictedViewPolicy with multiple terms (OR logic)."""
    return RestrictedViewPolicy(
        logical_operator=LogicalOperator.OR,
        terms=[
            PolicyTerm(
                term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
                column_name="ownerId",
                user_attribute="user.id",
                comparison_operator=ComparisonOperator.EQUALS,
                description="Owner access",
            ),
            PolicyTerm(
                term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
                column_name="departmentId",
                user_attribute="user.departmentIds",
                comparison_operator=ComparisonOperator.IN,
                description="Department access",
            ),
        ],
        enabled=True,
    )


@pytest.fixture
def column_value_match_restricted_view():
    """Create a RestrictedViewPolicy with COLUMN_VALUE_MATCH term."""
    return RestrictedViewPolicy(
        logical_operator=LogicalOperator.AND,
        terms=[
            PolicyTerm(
                term_type=PolicyTermType.COLUMN_VALUE_MATCH,
                column_name="status",
                comparison_operator=ComparisonOperator.IN,
                static_value=["PUBLISHED", "APPROVED"],
            ),
        ],
        enabled=True,
    )


# =============================================================================
# UserAttributeMapping Fixtures
# =============================================================================

@pytest.fixture
def sample_user_attribute_mapping():
    """Create a valid UserAttributeMapping."""
    return UserAttributeMapping(
        identifier_type=IdentifierType.UUID,
        markings_attribute="user.markings",
        organizations_attribute="user.organizationIds",
        groups_attribute="user.groups",
        roles_attribute="user.roles",
    )


# =============================================================================
# DataTypeSpec Fixtures
# =============================================================================

@pytest.fixture
def array_string_type():
    """Create an ARRAY[STRING] DataTypeSpec."""
    return DataTypeSpec(
        type=DataType.ARRAY,
        array_item_type=DataTypeSpec(type=DataType.STRING),
    )


@pytest.fixture
def vector_type():
    """Create a VECTOR DataTypeSpec with dimension."""
    return DataTypeSpec(
        type=DataType.VECTOR,
        vector_dimension=128,
    )


@pytest.fixture
def decimal_type():
    """Create a DECIMAL DataTypeSpec with precision and scale."""
    return DataTypeSpec(
        type=DataType.DECIMAL,
        precision=10,
        scale=2,
    )


# =============================================================================
# PropertyDefinition Fixtures
# =============================================================================

@pytest.fixture
def mandatory_control_property():
    """Create a valid mandatory control property."""
    return PropertyDefinition(
        api_name="securityMarking",
        display_name="Security Marking",
        data_type=DataTypeSpec(type=DataType.STRING),
        is_mandatory_control=True,
        constraints=PropertyConstraints(required=True),
    )


@pytest.fixture
def mandatory_control_array_property():
    """Create a valid mandatory control property with ARRAY[STRING] type."""
    return PropertyDefinition(
        api_name="securityMarkings",
        display_name="Security Markings",
        data_type=DataTypeSpec(
            type=DataType.ARRAY,
            array_item_type=DataTypeSpec(type=DataType.STRING),
        ),
        is_mandatory_control=True,
        constraints=PropertyConstraints(required=True),
    )


@pytest.fixture
def derived_property():
    """Create a derived property."""
    return PropertyDefinition(
        api_name="fullName",
        display_name="Full Name",
        data_type=DataTypeSpec(type=DataType.STRING),
        is_derived=True,
        derived_expression="concat(firstName, ' ', lastName)",
    )
