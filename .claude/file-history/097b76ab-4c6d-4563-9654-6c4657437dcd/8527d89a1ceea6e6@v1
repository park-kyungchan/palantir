"""
Unit tests for core types: ObjectType, PropertyDefinition, DataTypeSpec, PrimaryKeyDefinition.

Tests cover:
- Basic construction and validation
- Validation error cases (edge cases)
- Serialization (to_foundry_dict / from_foundry_dict roundtrip)
- Model validators (primary key exists, unique properties, mandatory control rules)
"""

import pytest
from pydantic import ValidationError

from ontology_definition import (
    ObjectType,
    PropertyDefinition,
    DataTypeSpec,
    DataType,
    PrimaryKeyDefinition,
    PropertyConstraints,
    ObjectStatus,
)


class TestDataTypeSpec:
    """Tests for DataTypeSpec - data type specification."""

    def test_simple_string_type(self):
        """Simple STRING type should work."""
        spec = DataTypeSpec(type=DataType.STRING)
        assert spec.type == DataType.STRING
        assert spec.array_item_type is None

    def test_simple_integer_type(self):
        """Simple INTEGER type should work."""
        spec = DataTypeSpec(type=DataType.INTEGER)
        assert spec.type == DataType.INTEGER

    def test_array_type_requires_item_type(self):
        """ARRAY type must have array_item_type."""
        with pytest.raises(ValidationError) as exc_info:
            DataTypeSpec(type=DataType.ARRAY)
        assert "ARRAY type requires array_item_type" in str(exc_info.value)

    def test_array_type_with_item_type(self):
        """ARRAY type with item type should work."""
        spec = DataTypeSpec(
            type=DataType.ARRAY,
            array_item_type=DataTypeSpec(type=DataType.STRING)
        )
        assert spec.type == DataType.ARRAY
        assert spec.array_item_type.type == DataType.STRING

    def test_vector_type_requires_dimension(self):
        """VECTOR type must have vector_dimension."""
        with pytest.raises(ValidationError) as exc_info:
            DataTypeSpec(type=DataType.VECTOR)
        assert "VECTOR type requires vector_dimension" in str(exc_info.value)

    def test_vector_type_with_dimension(self):
        """VECTOR type with dimension should work."""
        spec = DataTypeSpec(type=DataType.VECTOR, vector_dimension=128)
        assert spec.type == DataType.VECTOR
        assert spec.vector_dimension == 128

    def test_decimal_type_with_precision_scale(self):
        """DECIMAL type with precision and scale."""
        spec = DataTypeSpec(type=DataType.DECIMAL, precision=10, scale=2)
        assert spec.type == DataType.DECIMAL
        assert spec.precision == 10
        assert spec.scale == 2

    def test_to_foundry_dict_simple(self):
        """Export simple type to Foundry dict."""
        spec = DataTypeSpec(type=DataType.STRING)
        result = spec.to_foundry_dict()
        assert result == {"type": "STRING"}

    def test_to_foundry_dict_array(self):
        """Export ARRAY type to Foundry dict."""
        spec = DataTypeSpec(
            type=DataType.ARRAY,
            array_item_type=DataTypeSpec(type=DataType.INTEGER)
        )
        result = spec.to_foundry_dict()
        assert result == {
            "type": "ARRAY",
            "arrayItemType": {"type": "INTEGER"}
        }

    def test_from_foundry_dict_roundtrip(self):
        """from_foundry_dict should be inverse of to_foundry_dict."""
        original = DataTypeSpec(
            type=DataType.ARRAY,
            array_item_type=DataTypeSpec(type=DataType.STRING)
        )
        dict_form = original.to_foundry_dict()
        restored = DataTypeSpec.from_foundry_dict(dict_form)
        assert restored.type == original.type
        assert restored.array_item_type.type == original.array_item_type.type


class TestPropertyDefinition:
    """Tests for PropertyDefinition - property schema definition."""

    def test_basic_property(self):
        """Basic property definition should work."""
        prop = PropertyDefinition(
            api_name="employeeId",
            display_name="Employee ID",
            data_type=DataTypeSpec(type=DataType.STRING),
        )
        assert prop.api_name == "employeeId"
        assert prop.display_name == "Employee ID"
        assert prop.data_type.type == DataType.STRING

    def test_property_with_constraints(self):
        """Property with constraints should work."""
        prop = PropertyDefinition(
            api_name="age",
            display_name="Age",
            data_type=DataTypeSpec(type=DataType.INTEGER),
            constraints=PropertyConstraints(required=True),
        )
        assert prop.constraints.required is True

    def test_api_name_pattern_validation(self):
        """apiName must start with letter."""
        with pytest.raises(ValidationError) as exc_info:
            PropertyDefinition(
                api_name="123invalid",  # starts with number
                display_name="Invalid",
                data_type=DataTypeSpec(type=DataType.STRING),
            )
        assert "api_name" in str(exc_info.value).lower() or "pattern" in str(exc_info.value).lower()

    def test_mandatory_control_requires_required_constraint(self):
        """Mandatory control property must be required."""
        with pytest.raises(ValidationError) as exc_info:
            PropertyDefinition(
                api_name="securityMarking",
                display_name="Security Marking",
                data_type=DataTypeSpec(type=DataType.STRING),
                is_mandatory_control=True,
                # Missing constraints with required=True
            )
        assert "Mandatory control property must have required=True" in str(exc_info.value)

    def test_mandatory_control_cannot_have_default(self):
        """Mandatory control property cannot have default value."""
        with pytest.raises(ValidationError) as exc_info:
            PropertyDefinition(
                api_name="securityMarking",
                display_name="Security Marking",
                data_type=DataTypeSpec(type=DataType.STRING),
                is_mandatory_control=True,
                constraints=PropertyConstraints(required=True, default_value="PUBLIC"),
            )
        assert "cannot have a default value" in str(exc_info.value)

    def test_mandatory_control_must_be_string_type(self):
        """Mandatory control property must be STRING or ARRAY[STRING]."""
        with pytest.raises(ValidationError) as exc_info:
            PropertyDefinition(
                api_name="securityMarking",
                display_name="Security Marking",
                data_type=DataTypeSpec(type=DataType.INTEGER),  # Invalid type
                is_mandatory_control=True,
                constraints=PropertyConstraints(required=True),
            )
        assert "must be STRING or ARRAY[STRING]" in str(exc_info.value)

    def test_mandatory_control_valid_string(self):
        """Valid mandatory control property with STRING type."""
        prop = PropertyDefinition(
            api_name="securityMarking",
            display_name="Security Marking",
            data_type=DataTypeSpec(type=DataType.STRING),
            is_mandatory_control=True,
            constraints=PropertyConstraints(required=True),
        )
        assert prop.is_mandatory_control is True

    def test_mandatory_control_valid_array_string(self):
        """Valid mandatory control property with ARRAY[STRING] type."""
        prop = PropertyDefinition(
            api_name="securityMarkings",
            display_name="Security Markings",
            data_type=DataTypeSpec(
                type=DataType.ARRAY,
                array_item_type=DataTypeSpec(type=DataType.STRING)
            ),
            is_mandatory_control=True,
            constraints=PropertyConstraints(required=True),
        )
        assert prop.is_mandatory_control is True

    def test_derived_property_requires_expression(self):
        """Derived property must have derived_expression."""
        with pytest.raises(ValidationError) as exc_info:
            PropertyDefinition(
                api_name="fullName",
                display_name="Full Name",
                data_type=DataTypeSpec(type=DataType.STRING),
                is_derived=True,
                # Missing derived_expression
            )
        assert "Derived property must have derived_expression" in str(exc_info.value)

    def test_derived_property_with_expression(self):
        """Valid derived property with expression."""
        prop = PropertyDefinition(
            api_name="fullName",
            display_name="Full Name",
            data_type=DataTypeSpec(type=DataType.STRING),
            is_derived=True,
            derived_expression="concat(firstName, ' ', lastName)",
        )
        assert prop.is_derived is True
        assert prop.derived_expression == "concat(firstName, ' ', lastName)"

    def test_edit_only_cannot_have_backing_column(self):
        """Edit-only property should not have backing column."""
        with pytest.raises(ValidationError) as exc_info:
            PropertyDefinition(
                api_name="notes",
                display_name="Notes",
                data_type=DataTypeSpec(type=DataType.STRING),
                is_edit_only=True,
                backing_column="notes_col",  # Invalid for edit-only
            )
        assert "Edit-only property should not have backing_column" in str(exc_info.value)

    def test_to_foundry_dict_roundtrip(self):
        """to_foundry_dict / from_foundry_dict should roundtrip."""
        original = PropertyDefinition(
            api_name="employeeId",
            display_name="Employee ID",
            description="Unique employee identifier",
            data_type=DataTypeSpec(type=DataType.STRING),
            constraints=PropertyConstraints(required=True, unique=True),
            backing_column="employee_id",
        )
        dict_form = original.to_foundry_dict()
        restored = PropertyDefinition.from_foundry_dict(dict_form)

        assert restored.api_name == original.api_name
        assert restored.display_name == original.display_name
        assert restored.description == original.description
        assert restored.data_type.type == original.data_type.type
        assert restored.constraints.required == original.constraints.required
        assert restored.backing_column == original.backing_column


class TestPrimaryKeyDefinition:
    """Tests for PrimaryKeyDefinition."""

    def test_basic_primary_key(self):
        """Basic primary key definition."""
        pk = PrimaryKeyDefinition(property_api_name="id")
        assert pk.property_api_name == "id"
        assert pk.backing_column is None

    def test_primary_key_with_backing_column(self):
        """Primary key with backing column."""
        pk = PrimaryKeyDefinition(
            property_api_name="employeeId",
            backing_column="employee_id"
        )
        assert pk.property_api_name == "employeeId"
        assert pk.backing_column == "employee_id"

    def test_to_foundry_dict(self):
        """Export to Foundry dict."""
        pk = PrimaryKeyDefinition(
            property_api_name="employeeId",
            backing_column="employee_id"
        )
        result = pk.to_foundry_dict()
        assert result == {
            "propertyApiName": "employeeId",
            "backingColumn": "employee_id"
        }


class TestObjectType:
    """Tests for ObjectType - the core entity type."""

    def test_basic_object_type(self):
        """Basic ObjectType creation."""
        obj = ObjectType(
            api_name="Employee",
            display_name="Employee",
            primary_key=PrimaryKeyDefinition(property_api_name="employeeId"),
            properties=[
                PropertyDefinition(
                    api_name="employeeId",
                    display_name="Employee ID",
                    data_type=DataTypeSpec(type=DataType.STRING),
                )
            ],
        )
        assert obj.api_name == "Employee"
        assert obj.display_name == "Employee"
        assert len(obj.properties) == 1

    def test_object_type_requires_properties(self):
        """ObjectType must have at least one property."""
        with pytest.raises(ValidationError) as exc_info:
            ObjectType(
                api_name="Empty",
                display_name="Empty",
                primary_key=PrimaryKeyDefinition(property_api_name="id"),
                properties=[],  # Empty - should fail
            )
        assert "min_length" in str(exc_info.value).lower() or "properties" in str(exc_info.value).lower()

    def test_primary_key_must_reference_existing_property(self):
        """Primary key must reference an existing property."""
        with pytest.raises(ValidationError) as exc_info:
            ObjectType(
                api_name="Employee",
                display_name="Employee",
                primary_key=PrimaryKeyDefinition(property_api_name="nonexistent"),
                properties=[
                    PropertyDefinition(
                        api_name="employeeId",
                        display_name="Employee ID",
                        data_type=DataTypeSpec(type=DataType.STRING),
                    )
                ],
            )
        assert "not found in properties" in str(exc_info.value)

    def test_unique_property_names(self):
        """Property names must be unique within ObjectType."""
        with pytest.raises(ValidationError) as exc_info:
            ObjectType(
                api_name="Employee",
                display_name="Employee",
                primary_key=PrimaryKeyDefinition(property_api_name="employeeId"),
                properties=[
                    PropertyDefinition(
                        api_name="employeeId",
                        display_name="Employee ID",
                        data_type=DataTypeSpec(type=DataType.STRING),
                    ),
                    PropertyDefinition(
                        api_name="employeeId",  # Duplicate!
                        display_name="Employee ID 2",
                        data_type=DataTypeSpec(type=DataType.STRING),
                    ),
                ],
            )
        assert "Duplicate property apiNames" in str(exc_info.value)

    def test_object_type_with_multiple_properties(self):
        """ObjectType with multiple properties."""
        obj = ObjectType(
            api_name="Employee",
            display_name="Employee",
            primary_key=PrimaryKeyDefinition(property_api_name="employeeId"),
            properties=[
                PropertyDefinition(
                    api_name="employeeId",
                    display_name="Employee ID",
                    data_type=DataTypeSpec(type=DataType.STRING),
                ),
                PropertyDefinition(
                    api_name="name",
                    display_name="Name",
                    data_type=DataTypeSpec(type=DataType.STRING),
                ),
                PropertyDefinition(
                    api_name="age",
                    display_name="Age",
                    data_type=DataTypeSpec(type=DataType.INTEGER),
                ),
            ],
        )
        assert len(obj.properties) == 3

    def test_get_property(self):
        """get_property method should find property by apiName."""
        obj = ObjectType(
            api_name="Employee",
            display_name="Employee",
            primary_key=PrimaryKeyDefinition(property_api_name="employeeId"),
            properties=[
                PropertyDefinition(
                    api_name="employeeId",
                    display_name="Employee ID",
                    data_type=DataTypeSpec(type=DataType.STRING),
                ),
                PropertyDefinition(
                    api_name="name",
                    display_name="Name",
                    data_type=DataTypeSpec(type=DataType.STRING),
                ),
            ],
        )

        prop = obj.get_property("name")
        assert prop is not None
        assert prop.api_name == "name"

        missing = obj.get_property("nonexistent")
        assert missing is None

    def test_get_primary_key_property(self):
        """get_primary_key_property should return the primary key property."""
        obj = ObjectType(
            api_name="Employee",
            display_name="Employee",
            primary_key=PrimaryKeyDefinition(property_api_name="employeeId"),
            properties=[
                PropertyDefinition(
                    api_name="employeeId",
                    display_name="Employee ID",
                    data_type=DataTypeSpec(type=DataType.STRING),
                ),
            ],
        )
        pk_prop = obj.get_primary_key_property()
        assert pk_prop.api_name == "employeeId"

    def test_implements_interface(self):
        """implements_interface should check interface list."""
        obj = ObjectType(
            api_name="Employee",
            display_name="Employee",
            primary_key=PrimaryKeyDefinition(property_api_name="employeeId"),
            properties=[
                PropertyDefinition(
                    api_name="employeeId",
                    display_name="Employee ID",
                    data_type=DataTypeSpec(type=DataType.STRING),
                ),
            ],
            interfaces=["Auditable", "Identifiable"],
        )
        assert obj.implements_interface("Auditable") is True
        assert obj.implements_interface("Identifiable") is True
        assert obj.implements_interface("Unknown") is False

    def test_status_default_experimental(self):
        """Default status should be EXPERIMENTAL."""
        obj = ObjectType(
            api_name="Employee",
            display_name="Employee",
            primary_key=PrimaryKeyDefinition(property_api_name="employeeId"),
            properties=[
                PropertyDefinition(
                    api_name="employeeId",
                    display_name="Employee ID",
                    data_type=DataTypeSpec(type=DataType.STRING),
                ),
            ],
        )
        assert obj.status == ObjectStatus.EXPERIMENTAL

    def test_endorsed_flag(self):
        """Endorsed flag should be settable."""
        obj = ObjectType(
            api_name="Employee",
            display_name="Employee",
            primary_key=PrimaryKeyDefinition(property_api_name="employeeId"),
            properties=[
                PropertyDefinition(
                    api_name="employeeId",
                    display_name="Employee ID",
                    data_type=DataTypeSpec(type=DataType.STRING),
                ),
            ],
            endorsed=True,
        )
        assert obj.endorsed is True

    def test_to_foundry_dict(self):
        """Export to Foundry dict format."""
        obj = ObjectType(
            api_name="Employee",
            display_name="Employee",
            description="Company employee",
            primary_key=PrimaryKeyDefinition(property_api_name="employeeId"),
            properties=[
                PropertyDefinition(
                    api_name="employeeId",
                    display_name="Employee ID",
                    data_type=DataTypeSpec(type=DataType.STRING),
                ),
            ],
            status=ObjectStatus.ACTIVE,
            endorsed=True,
        )
        result = obj.to_foundry_dict()

        assert result["apiName"] == "Employee"
        assert result["displayName"] == "Employee"
        assert result["description"] == "Company employee"
        assert result["primaryKey"]["propertyApiName"] == "employeeId"
        assert result["status"] == "ACTIVE"
        assert result["endorsed"] is True
        assert len(result["properties"]) == 1

    def test_from_foundry_dict_roundtrip(self):
        """from_foundry_dict should be inverse of to_foundry_dict."""
        original = ObjectType(
            api_name="Employee",
            display_name="Employee",
            description="Company employee",
            primary_key=PrimaryKeyDefinition(property_api_name="employeeId"),
            properties=[
                PropertyDefinition(
                    api_name="employeeId",
                    display_name="Employee ID",
                    data_type=DataTypeSpec(type=DataType.STRING),
                    constraints=PropertyConstraints(required=True),
                ),
                PropertyDefinition(
                    api_name="name",
                    display_name="Name",
                    data_type=DataTypeSpec(type=DataType.STRING),
                ),
            ],
            status=ObjectStatus.ACTIVE,
            endorsed=True,
            interfaces=["Identifiable"],
        )

        dict_form = original.to_foundry_dict()
        restored = ObjectType.from_foundry_dict(dict_form)

        assert restored.api_name == original.api_name
        assert restored.display_name == original.display_name
        assert restored.description == original.description
        assert restored.status == original.status
        assert restored.endorsed == original.endorsed
        assert len(restored.properties) == len(original.properties)
        assert restored.interfaces == original.interfaces

    def test_rid_is_auto_generated(self):
        """RID should be auto-generated with correct pattern."""
        obj = ObjectType(
            api_name="Employee",
            display_name="Employee",
            primary_key=PrimaryKeyDefinition(property_api_name="employeeId"),
            properties=[
                PropertyDefinition(
                    api_name="employeeId",
                    display_name="Employee ID",
                    data_type=DataTypeSpec(type=DataType.STRING),
                ),
            ],
        )
        assert obj.rid.startswith("ri.ontology.")
        assert "object-type" in obj.rid
