"""
Unit tests for constraints module: MandatoryControlConfig, PropertyConstraints, and related types.

Tests cover:
- GAP-002 P1-CRITICAL: MandatoryControlConfig for row-level security
- ControlType validation (MARKINGS, ORGANIZATIONS, CLASSIFICATIONS)
- Enforcement levels and type-specific requirements
- PropertyConstraints with all constraint types
- Validation error cases
- Serialization (to_foundry_dict / from_foundry_dict roundtrip)
"""

import pytest
from pydantic import ValidationError

from ontology_definition import (
    MandatoryControlConfig,
    PropertyConstraints,
)
from ontology_definition.constraints.mandatory_control import (
    MandatoryControlPropertyRequirements,
    SecurityMarkingReference,
)
from ontology_definition.constraints.property_constraints import (
    ArrayConstraints,
    DecimalConstraints,
    NumericConstraints,
    StringConstraints,
    VectorConstraints,
)
from ontology_definition.core.enums import ClassificationLevel, ControlType


class TestControlType:
    """Tests for ControlType enumeration."""

    def test_all_control_types_exist(self):
        """Verify all expected control types are available."""
        assert ControlType.MARKINGS.value == "MARKINGS"
        assert ControlType.ORGANIZATIONS.value == "ORGANIZATIONS"
        assert ControlType.CLASSIFICATIONS.value == "CLASSIFICATIONS"


class TestClassificationLevel:
    """Tests for ClassificationLevel enumeration."""

    def test_all_classification_levels_exist(self):
        """Verify all expected classification levels are available."""
        assert ClassificationLevel.UNCLASSIFIED.value == "UNCLASSIFIED"
        assert ClassificationLevel.CONFIDENTIAL.value == "CONFIDENTIAL"
        assert ClassificationLevel.SECRET.value == "SECRET"
        assert ClassificationLevel.TOP_SECRET.value == "TOP_SECRET"


class TestMandatoryControlConfig:
    """Tests for MandatoryControlConfig - row-level security configuration."""

    def test_markings_type_valid(self, sample_mandatory_control):
        """Valid MARKINGS control config using fixture."""
        assert sample_mandatory_control.control_type == ControlType.MARKINGS
        assert sample_mandatory_control.property_api_name == "securityMarking"
        assert sample_mandatory_control.marking_column_mapping == "security_markings"

    def test_markings_type_requires_column_mapping(self):
        """MARKINGS control_type requires marking_column_mapping."""
        with pytest.raises(ValidationError) as exc_info:
            MandatoryControlConfig(
                property_api_name="securityMarking",
                control_type=ControlType.MARKINGS,
                # Missing: marking_column_mapping
            )
        assert "marking_column_mapping is required for MARKINGS control type" in str(exc_info.value)

    def test_organizations_type_valid(self, organizations_mandatory_control):
        """Valid ORGANIZATIONS control config using fixture."""
        assert organizations_mandatory_control.control_type == ControlType.ORGANIZATIONS
        assert organizations_mandatory_control.property_api_name == "organizationId"
        assert organizations_mandatory_control.allowed_organizations is not None

    def test_organizations_type_requires_allowed_organizations(self):
        """ORGANIZATIONS control_type requires allowed_organizations."""
        with pytest.raises(ValidationError) as exc_info:
            MandatoryControlConfig(
                property_api_name="organizationId",
                control_type=ControlType.ORGANIZATIONS,
                # Missing: allowed_organizations
            )
        assert "allowed_organizations is required for ORGANIZATIONS control type" in str(exc_info.value)

    def test_classifications_type_valid(self, classifications_mandatory_control):
        """Valid CLASSIFICATIONS control config using fixture."""
        assert classifications_mandatory_control.control_type == ControlType.CLASSIFICATIONS
        assert classifications_mandatory_control.property_api_name == "classificationLevel"
        assert classifications_mandatory_control.max_classification_level == ClassificationLevel.SECRET

    def test_classifications_type_requires_max_level(self):
        """CLASSIFICATIONS control_type requires max_classification_level."""
        with pytest.raises(ValidationError) as exc_info:
            MandatoryControlConfig(
                property_api_name="classificationLevel",
                control_type=ControlType.CLASSIFICATIONS,
                # Missing: max_classification_level
            )
        assert "max_classification_level is required for CLASSIFICATIONS control type" in str(exc_info.value)

    def test_invalid_uuid_in_allowed_markings(self):
        """Invalid UUID format in allowed_markings should fail."""
        with pytest.raises(ValidationError) as exc_info:
            MandatoryControlConfig(
                property_api_name="securityMarking",
                control_type=ControlType.MARKINGS,
                marking_column_mapping="security_markings",
                allowed_markings=["not-a-valid-uuid"],
            )
        assert "Invalid UUID format" in str(exc_info.value)

    def test_invalid_uuid_in_allowed_organizations(self):
        """Invalid UUID format in allowed_organizations should fail."""
        with pytest.raises(ValidationError) as exc_info:
            MandatoryControlConfig(
                property_api_name="organizationId",
                control_type=ControlType.ORGANIZATIONS,
                allowed_organizations=["invalid-uuid-format"],
            )
        assert "Invalid UUID format" in str(exc_info.value)

    def test_valid_uuid_formats(self):
        """Valid UUID formats should pass."""
        config = MandatoryControlConfig(
            property_api_name="securityMarking",
            control_type=ControlType.MARKINGS,
            marking_column_mapping="security_markings",
            allowed_markings=[
                "550e8400-e29b-41d4-a716-446655440000",
                "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
            ],
        )
        assert len(config.allowed_markings) == 2

    def test_property_api_name_pattern(self):
        """property_api_name must match pattern (start with letter)."""
        with pytest.raises(ValidationError):
            MandatoryControlConfig(
                property_api_name="123invalid",  # Invalid: starts with number
                control_type=ControlType.MARKINGS,
                marking_column_mapping="security_markings",
            )

    def test_property_api_name_valid_patterns(self):
        """Valid property_api_name patterns."""
        config = MandatoryControlConfig(
            property_api_name="securityMarking",
            control_type=ControlType.MARKINGS,
            marking_column_mapping="security_markings",
        )
        assert config.property_api_name == "securityMarking"

        config2 = MandatoryControlConfig(
            property_api_name="security_marking_2",
            control_type=ControlType.MARKINGS,
            marking_column_mapping="security_markings",
        )
        assert config2.property_api_name == "security_marking_2"

    def test_to_foundry_dict_markings(self, sample_mandatory_control):
        """Export MARKINGS config to Foundry dict."""
        result = sample_mandatory_control.to_foundry_dict()
        assert result["propertyApiName"] == "securityMarking"
        assert result["controlType"] == "MARKINGS"
        assert result["markingColumnMapping"] == "security_markings"
        assert "allowedMarkings" in result

    def test_to_foundry_dict_organizations(self, organizations_mandatory_control):
        """Export ORGANIZATIONS config to Foundry dict."""
        result = organizations_mandatory_control.to_foundry_dict()
        assert result["controlType"] == "ORGANIZATIONS"
        assert "allowedOrganizations" in result

    def test_to_foundry_dict_classifications(self, classifications_mandatory_control):
        """Export CLASSIFICATIONS config to Foundry dict."""
        result = classifications_mandatory_control.to_foundry_dict()
        assert result["controlType"] == "CLASSIFICATIONS"
        assert result["maxClassificationLevel"] == "SECRET"

    def test_from_foundry_dict_roundtrip_markings(self, sample_mandatory_control):
        """from_foundry_dict should be inverse of to_foundry_dict for MARKINGS."""
        dict_form = sample_mandatory_control.to_foundry_dict()
        restored = MandatoryControlConfig.from_foundry_dict(dict_form)
        assert restored.control_type == sample_mandatory_control.control_type
        assert restored.property_api_name == sample_mandatory_control.property_api_name
        assert restored.marking_column_mapping == sample_mandatory_control.marking_column_mapping

    def test_from_foundry_dict_roundtrip_classifications(self, classifications_mandatory_control):
        """from_foundry_dict should be inverse of to_foundry_dict for CLASSIFICATIONS."""
        dict_form = classifications_mandatory_control.to_foundry_dict()
        restored = MandatoryControlConfig.from_foundry_dict(dict_form)
        assert restored.control_type == classifications_mandatory_control.control_type
        assert restored.max_classification_level == classifications_mandatory_control.max_classification_level


class TestMandatoryControlPropertyRequirements:
    """Tests for static validation rules for mandatory control properties."""

    def test_validate_required_property(self):
        """Property must be required for mandatory control."""
        errors = MandatoryControlPropertyRequirements.validate_property_for_mandatory_control(
            is_required=False,  # Invalid
            has_default=False,
            data_type="STRING",
        )
        assert len(errors) == 1
        assert "must be required" in errors[0]

    def test_validate_no_default_value(self):
        """Property cannot have default value for mandatory control."""
        errors = MandatoryControlPropertyRequirements.validate_property_for_mandatory_control(
            is_required=True,
            has_default=True,  # Invalid
            data_type="STRING",
        )
        assert len(errors) == 1
        assert "cannot have a default value" in errors[0]

    def test_validate_string_type(self):
        """Property must be STRING or ARRAY[STRING] for mandatory control."""
        errors = MandatoryControlPropertyRequirements.validate_property_for_mandatory_control(
            is_required=True,
            has_default=False,
            data_type="INTEGER",  # Invalid
        )
        assert len(errors) == 1
        assert "must be STRING or ARRAY[STRING]" in errors[0]

    def test_validate_array_string_type(self):
        """Property with ARRAY[STRING] should be valid."""
        errors = MandatoryControlPropertyRequirements.validate_property_for_mandatory_control(
            is_required=True,
            has_default=False,
            data_type="STRING",
            is_array=True,
        )
        assert len(errors) == 0

    def test_validate_valid_property(self):
        """Valid mandatory control property should have no errors."""
        errors = MandatoryControlPropertyRequirements.validate_property_for_mandatory_control(
            is_required=True,
            has_default=False,
            data_type="STRING",
        )
        assert len(errors) == 0

    def test_multiple_errors(self):
        """Multiple validation errors should be collected."""
        errors = MandatoryControlPropertyRequirements.validate_property_for_mandatory_control(
            is_required=False,  # Error 1
            has_default=True,   # Error 2
            data_type="BOOLEAN",  # Error 3
        )
        assert len(errors) == 3


class TestSecurityMarkingReference:
    """Tests for SecurityMarkingReference - reference to marking definition."""

    def test_valid_marking_reference(self):
        """Valid marking reference creation."""
        ref = SecurityMarkingReference(
            marking_id="550e8400-e29b-41d4-a716-446655440000",
            display_name="Public Data",
            description="Marking for public data",
        )
        assert ref.marking_id == "550e8400-e29b-41d4-a716-446655440000"
        assert ref.display_name == "Public Data"
        assert ref.description == "Marking for public data"

    def test_invalid_marking_uuid(self):
        """Invalid UUID format in marking_id should fail."""
        with pytest.raises(ValidationError) as exc_info:
            SecurityMarkingReference(
                marking_id="invalid-uuid",
            )
        assert "Invalid marking UUID" in str(exc_info.value)

    def test_minimal_marking_reference(self):
        """Minimal marking reference with just marking_id."""
        ref = SecurityMarkingReference(
            marking_id="6ba7b810-9dad-11d1-80b4-00c04fd430c8",
        )
        assert ref.marking_id == "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
        assert ref.display_name is None
        assert ref.description is None


class TestNumericConstraints:
    """Tests for NumericConstraints - constraints for numeric types."""

    def test_min_max_value(self):
        """Numeric constraints with min and max."""
        constraints = NumericConstraints(
            min_value=0,
            max_value=100,
        )
        assert constraints.min_value == 0
        assert constraints.max_value == 100

    def test_exclusive_bounds(self):
        """Numeric constraints with exclusive bounds."""
        constraints = NumericConstraints(
            min_value=0,
            max_value=100,
            exclusive_min=True,
            exclusive_max=True,
        )
        assert constraints.exclusive_min is True
        assert constraints.exclusive_max is True

    def test_multiple_of(self):
        """Numeric constraints with multiple_of."""
        constraints = NumericConstraints(
            multiple_of=5,
        )
        assert constraints.multiple_of == 5

    def test_min_greater_than_max_fails(self):
        """min_value > max_value should fail."""
        with pytest.raises(ValidationError) as exc_info:
            NumericConstraints(
                min_value=100,
                max_value=0,  # Invalid: min > max
            )
        assert "min_value" in str(exc_info.value) and "max_value" in str(exc_info.value)

    def test_float_values(self):
        """Numeric constraints with float values."""
        constraints = NumericConstraints(
            min_value=0.0,
            max_value=1.0,
            multiple_of=0.1,
        )
        assert constraints.min_value == 0.0
        assert constraints.max_value == 1.0


class TestStringConstraints:
    """Tests for StringConstraints - constraints for STRING type."""

    def test_min_max_length(self):
        """String constraints with min and max length."""
        constraints = StringConstraints(
            min_length=1,
            max_length=255,
        )
        assert constraints.min_length == 1
        assert constraints.max_length == 255

    def test_pattern(self):
        """String constraints with pattern."""
        constraints = StringConstraints(
            pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$",
        )
        assert constraints.pattern == r"^[a-zA-Z][a-zA-Z0-9_]*$"

    def test_format_flags(self):
        """String constraints with format flags."""
        constraints = StringConstraints(
            rid_format=True,
            uuid_format=False,
            email_format=False,
            url_format=False,
        )
        assert constraints.rid_format is True

    def test_min_greater_than_max_fails(self):
        """min_length > max_length should fail."""
        with pytest.raises(ValidationError) as exc_info:
            StringConstraints(
                min_length=100,
                max_length=10,  # Invalid: min > max
            )
        assert "min_length" in str(exc_info.value) and "max_length" in str(exc_info.value)

    def test_email_format(self):
        """String constraints for email format."""
        constraints = StringConstraints(
            email_format=True,
        )
        assert constraints.email_format is True


class TestArrayConstraints:
    """Tests for ArrayConstraints - constraints for ARRAY type."""

    def test_min_max_items(self):
        """Array constraints with min and max items."""
        constraints = ArrayConstraints(
            min_items=1,
            max_items=10,
        )
        assert constraints.min_items == 1
        assert constraints.max_items == 10

    def test_unique_items(self):
        """Array constraints with unique items flag."""
        constraints = ArrayConstraints(
            unique_items=True,
        )
        assert constraints.unique_items is True

    def test_min_greater_than_max_fails(self):
        """min_items > max_items should fail."""
        with pytest.raises(ValidationError) as exc_info:
            ArrayConstraints(
                min_items=10,
                max_items=1,  # Invalid: min > max
            )
        assert "min_items" in str(exc_info.value) and "max_items" in str(exc_info.value)


class TestDecimalConstraints:
    """Tests for DecimalConstraints - constraints for DECIMAL type."""

    def test_precision_scale(self):
        """Decimal constraints with precision and scale."""
        constraints = DecimalConstraints(
            precision=10,
            scale=2,
        )
        assert constraints.precision == 10
        assert constraints.scale == 2

    def test_default_values(self):
        """Decimal constraints with default values."""
        constraints = DecimalConstraints()
        assert constraints.precision == 18
        assert constraints.scale == 2

    def test_scale_greater_than_precision_fails(self):
        """scale > precision should fail."""
        with pytest.raises(ValidationError) as exc_info:
            DecimalConstraints(
                precision=5,
                scale=10,  # Invalid: scale > precision
            )
        assert "scale" in str(exc_info.value) and "precision" in str(exc_info.value)

    def test_precision_bounds(self):
        """precision must be 1-38."""
        with pytest.raises(ValidationError):
            DecimalConstraints(precision=0)  # Too low
        with pytest.raises(ValidationError):
            DecimalConstraints(precision=39)  # Too high


class TestVectorConstraints:
    """Tests for VectorConstraints - constraints for VECTOR type."""

    def test_dimension_required(self):
        """dimension is required for VectorConstraints."""
        constraints = VectorConstraints(dimension=128)
        assert constraints.dimension == 128

    def test_dimension_must_be_positive(self):
        """dimension must be >= 1."""
        with pytest.raises(ValidationError):
            VectorConstraints(dimension=0)


class TestPropertyConstraints:
    """Tests for PropertyConstraints - complete validation constraints."""

    def test_basic_flags(self):
        """Basic constraint flags."""
        constraints = PropertyConstraints(
            required=True,
            unique=True,
            immutable=False,
        )
        assert constraints.required is True
        assert constraints.unique is True
        assert constraints.immutable is False

    def test_enum_constraint(self):
        """Enum constraint with allowed values."""
        constraints = PropertyConstraints(
            enum=["ACTIVE", "INACTIVE", "PENDING"],
        )
        assert constraints.enum == ["ACTIVE", "INACTIVE", "PENDING"]

    def test_empty_enum_fails(self):
        """Empty enum list should fail."""
        with pytest.raises(ValidationError) as exc_info:
            PropertyConstraints(enum=[])
        assert "enum list cannot be empty" in str(exc_info.value)

    def test_default_value(self):
        """Default value constraint."""
        constraints = PropertyConstraints(
            default_value="PENDING",
        )
        assert constraints.default_value == "PENDING"

    def test_nested_numeric_constraints(self):
        """PropertyConstraints with nested NumericConstraints."""
        constraints = PropertyConstraints(
            required=True,
            numeric=NumericConstraints(
                min_value=0,
                max_value=100,
            ),
        )
        assert constraints.numeric is not None
        assert constraints.numeric.min_value == 0
        assert constraints.numeric.max_value == 100

    def test_nested_string_constraints(self):
        """PropertyConstraints with nested StringConstraints."""
        constraints = PropertyConstraints(
            required=True,
            string=StringConstraints(
                min_length=1,
                max_length=100,
                pattern=r"^[A-Z].*$",
            ),
        )
        assert constraints.string is not None
        assert constraints.string.pattern == r"^[A-Z].*$"

    def test_nested_array_constraints(self):
        """PropertyConstraints with nested ArrayConstraints."""
        constraints = PropertyConstraints(
            array=ArrayConstraints(
                min_items=1,
                unique_items=True,
            ),
        )
        assert constraints.array is not None
        assert constraints.array.unique_items is True

    def test_nested_decimal_constraints(self):
        """PropertyConstraints with nested DecimalConstraints."""
        constraints = PropertyConstraints(
            decimal=DecimalConstraints(
                precision=10,
                scale=2,
            ),
        )
        assert constraints.decimal is not None
        assert constraints.decimal.precision == 10

    def test_to_foundry_dict(self):
        """Export PropertyConstraints to Foundry dict."""
        constraints = PropertyConstraints(
            required=True,
            unique=True,
            numeric=NumericConstraints(
                min_value=0,
                max_value=100,
            ),
        )
        result = constraints.to_foundry_dict()
        assert result["required"] is True
        assert result["unique"] is True
        assert result["minValue"] == 0
        assert result["maxValue"] == 100

    def test_to_foundry_dict_string(self):
        """Export PropertyConstraints with string to Foundry dict."""
        constraints = PropertyConstraints(
            string=StringConstraints(
                min_length=1,
                max_length=255,
                pattern=r"^test.*$",
            ),
        )
        result = constraints.to_foundry_dict()
        assert result["minLength"] == 1
        assert result["maxLength"] == 255
        assert result["pattern"] == r"^test.*$"

    def test_to_foundry_dict_array(self):
        """Export PropertyConstraints with array to Foundry dict."""
        constraints = PropertyConstraints(
            array=ArrayConstraints(
                min_items=1,
                max_items=10,
                unique_items=True,
            ),
        )
        result = constraints.to_foundry_dict()
        assert result["arrayMinItems"] == 1
        assert result["arrayMaxItems"] == 10
        assert result["arrayUnique"] is True

    def test_from_foundry_dict_roundtrip(self):
        """from_foundry_dict should be inverse of to_foundry_dict."""
        original = PropertyConstraints(
            required=True,
            unique=True,
            enum=["A", "B", "C"],
            numeric=NumericConstraints(min_value=0, max_value=100),
        )
        dict_form = original.to_foundry_dict()
        restored = PropertyConstraints.from_foundry_dict(dict_form)
        assert restored.required == original.required
        assert restored.unique == original.unique
        assert restored.enum == original.enum
        assert restored.numeric.min_value == original.numeric.min_value

    def test_from_foundry_dict_string(self):
        """from_foundry_dict with string constraints."""
        data = {
            "minLength": 1,
            "maxLength": 100,
            "pattern": r"^test.*$",
        }
        constraints = PropertyConstraints.from_foundry_dict(data)
        assert constraints.string is not None
        assert constraints.string.min_length == 1
        assert constraints.string.max_length == 100
        assert constraints.string.pattern == r"^test.*$"

    def test_custom_validator(self):
        """PropertyConstraints with custom validator reference."""
        constraints = PropertyConstraints(
            custom_validator="validate_employee_id",
        )
        assert constraints.custom_validator == "validate_employee_id"

    def test_mixed_type_enum(self):
        """Enum with mixed types (string, int)."""
        constraints = PropertyConstraints(
            enum=["ACTIVE", 1, 2.5, True],
        )
        assert constraints.enum == ["ACTIVE", 1, 2.5, True]


class TestPropertyConstraintsIntegration:
    """Integration tests for PropertyConstraints with PropertyDefinition."""

    def test_constraints_with_mandatory_control_property(
        self, mandatory_control_property
    ):
        """Mandatory control property has proper constraints."""
        assert mandatory_control_property.constraints.required is True
        assert mandatory_control_property.is_mandatory_control is True

    def test_constraints_in_object_type(self, object_type_with_constraints):
        """ObjectType with various property constraints.

        Note: PropertyConstraints uses nested constraint objects:
        - string constraints: constraints.string.min_length, etc.
        - numeric constraints: constraints.numeric.min_value, etc.
        - enum values: constraints.enum (not allowed_values)
        """
        # Find title property
        title_prop = object_type_with_constraints.get_property("title")
        assert title_prop is not None
        assert title_prop.constraints.required is True
        # String constraints are nested
        assert title_prop.constraints.string is not None
        assert title_prop.constraints.string.min_length == 1
        assert title_prop.constraints.string.max_length == 255

        # Find status property with enum
        status_prop = object_type_with_constraints.get_property("status")
        assert status_prop is not None
        # Enum is directly on constraints, not allowed_values
        assert status_prop.constraints.enum == ["DRAFT", "PUBLISHED", "ARCHIVED"]

        # Find priority property with numeric constraints
        priority_prop = object_type_with_constraints.get_property("priority")
        assert priority_prop is not None
        # Numeric constraints are nested
        assert priority_prop.constraints.numeric is not None
        assert priority_prop.constraints.numeric.min_value == 1
        assert priority_prop.constraints.numeric.max_value == 10
