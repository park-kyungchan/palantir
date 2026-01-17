"""
StructType Definition for Ontology.

A StructType is a user-defined complex data type with multiple fields,
enabling reusable nested structures for properties:
    - Address (street, city, state, postalCode, country)
    - ContactInfo (email, phone, fax)
    - GeoCoordinate (latitude, longitude, altitude)
    - MonetaryAmount (amount, currency)

StructTypes are referenced by properties via structTypeRef, enabling
consistent nested object schemas across multiple ObjectTypes.

Example:
    address = StructType(
        api_name="Address",
        display_name="Address",
        description="Physical or mailing address",
        fields=[
            StructTypeField(
                api_name="street",
                display_name="Street",
                data_type=DataTypeSpec(type=DataType.STRING),
                required=True,
            ),
            StructTypeField(
                api_name="city",
                display_name="City",
                data_type=DataTypeSpec(type=DataType.STRING),
                required=True,
            ),
            StructTypeField(
                api_name="postalCode",
                display_name="Postal Code",
                data_type=DataTypeSpec(type=DataType.STRING),
                required=True,
            ),
        ],
    )
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ontology_definition.core.base import OntologyEntity
from ontology_definition.core.identifiers import generate_rid
from ontology_definition.types.property_def import DataTypeSpec


class StructTypeStatus(str, Enum):
    """Lifecycle status for StructTypes."""

    DRAFT = "DRAFT"
    EXPERIMENTAL = "EXPERIMENTAL"
    ALPHA = "ALPHA"
    BETA = "BETA"
    ACTIVE = "ACTIVE"
    STABLE = "STABLE"
    DEPRECATED = "DEPRECATED"
    SUNSET = "SUNSET"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class StructFieldConstraints(BaseModel):
    """
    Constraints for a field within a StructType.

    Similar to PropertyConstraints but scoped to struct fields.
    """

    min_value: Optional[float] = Field(
        default=None,
        description="Minimum numeric value.",
        alias="minValue",
    )

    max_value: Optional[float] = Field(
        default=None,
        description="Maximum numeric value.",
        alias="maxValue",
    )

    min_length: Optional[int] = Field(
        default=None,
        description="Minimum string length.",
        ge=0,
        alias="minLength",
    )

    max_length: Optional[int] = Field(
        default=None,
        description="Maximum string length.",
        ge=0,
        alias="maxLength",
    )

    pattern: Optional[str] = Field(
        default=None,
        description="Regex pattern for string validation.",
    )

    enum: Optional[list[Any]] = Field(
        default=None,
        description="Allowed values for this field.",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {}
        if self.min_value is not None:
            result["minValue"] = self.min_value
        if self.max_value is not None:
            result["maxValue"] = self.max_value
        if self.min_length is not None:
            result["minLength"] = self.min_length
        if self.max_length is not None:
            result["maxLength"] = self.max_length
        if self.pattern is not None:
            result["pattern"] = self.pattern
        if self.enum is not None:
            result["enum"] = self.enum
        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "StructFieldConstraints":
        """Create from Foundry JSON format."""
        return cls(
            min_value=data.get("minValue"),
            max_value=data.get("maxValue"),
            min_length=data.get("minLength"),
            max_length=data.get("maxLength"),
            pattern=data.get("pattern"),
            enum=data.get("enum"),
        )


class StructTypeField(BaseModel):
    """
    Field definition within a StructType.

    Defines one field of a nested structure, including its type,
    whether it's required, and optional constraints.

    Example:
        street_field = StructTypeField(
            api_name="street",
            display_name="Street Address",
            data_type=DataTypeSpec(type=DataType.STRING),
            required=True,
            constraints=StructFieldConstraints(max_length=255),
        )
    """

    api_name: str = Field(
        ...,
        description="Field name within the struct (camelCase).",
        min_length=1,
        max_length=255,
        pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$",
        alias="apiName",
    )

    display_name: str = Field(
        ...,
        description="Human-friendly field name.",
        min_length=1,
        max_length=255,
        alias="displayName",
    )

    description: Optional[str] = Field(
        default=None,
        description="Documentation for this field.",
        max_length=4096,
    )

    data_type: DataTypeSpec = Field(
        ...,
        description="Data type for this field.",
        alias="dataType",
    )

    required: bool = Field(
        default=False,
        description="If true, field must have a value.",
    )

    default_value: Optional[Any] = Field(
        default=None,
        description="Default value if not provided.",
        alias="defaultValue",
    )

    constraints: Optional[StructFieldConstraints] = Field(
        default=None,
        description="Validation constraints for this field.",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "apiName": self.api_name,
            "displayName": self.display_name,
            "dataType": self.data_type.to_foundry_dict(),
        }
        if self.description:
            result["description"] = self.description
        if self.required:
            result["required"] = True
        if self.default_value is not None:
            result["defaultValue"] = self.default_value
        if self.constraints:
            result["constraints"] = self.constraints.to_foundry_dict()
        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "StructTypeField":
        """Create from Foundry JSON format."""
        constraints = None
        if data.get("constraints"):
            constraints = StructFieldConstraints.from_foundry_dict(data["constraints"])

        return cls(
            api_name=data["apiName"],
            display_name=data["displayName"],
            description=data.get("description"),
            data_type=DataTypeSpec.from_foundry_dict(data["dataType"]),
            required=data.get("required", False),
            default_value=data.get("defaultValue"),
            constraints=constraints,
        )


class StructType(OntologyEntity):
    """
    StructType schema definition - reusable nested structure.

    A StructType defines a complex data type with multiple fields,
    enabling consistent nested object schemas across properties.

    Key Features:
    - Multiple typed fields with individual constraints
    - Required/optional field designation
    - Default values for fields
    - Reusable via structTypeRef in properties

    Common StructTypes:
    - Address: street, city, state, postalCode, country
    - ContactInfo: email, phone, fax
    - MonetaryAmount: amount, currency
    - GeoCoordinate: latitude, longitude, altitude

    Example:
        >>> address = StructType(
        ...     api_name="Address",
        ...     display_name="Address",
        ...     description="Physical or mailing address",
        ...     fields=[
        ...         StructTypeField(
        ...             api_name="street",
        ...             display_name="Street",
        ...             data_type=DataTypeSpec(type=DataType.STRING),
        ...             required=True,
        ...         ),
        ...         StructTypeField(
        ...             api_name="city",
        ...             display_name="City",
        ...             data_type=DataTypeSpec(type=DataType.STRING),
        ...             required=True,
        ...         ),
        ...     ],
        ... )
    """

    # Override RID to use struct-type specific format
    rid: str = Field(
        default_factory=lambda: generate_rid("ontology", "struct-type"),
        description="Resource ID - globally unique identifier for this StructType.",
        pattern=r"^ri\.ontology\.[a-z]+\.struct-type\.[a-zA-Z0-9-]+$",
        json_schema_extra={"readOnly": True, "immutable": True},
    )

    # Fields (REQUIRED - at least one)
    fields: list[StructTypeField] = Field(
        ...,
        description="Field definitions within this struct.",
        min_length=1,
    )

    # Lifecycle Status
    status: StructTypeStatus = Field(
        default=StructTypeStatus.EXPERIMENTAL,
        description="Lifecycle status of the StructType.",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "x-palantir-entity-type": "struct-type",
            "x-palantir-indexing": ["api_name", "rid", "status"],
        },
    )

    @model_validator(mode="after")
    def validate_unique_field_names(self) -> "StructType":
        """Validate that all field apiNames are unique."""
        names = [f.api_name for f in self.fields]
        duplicates = [n for n in names if names.count(n) > 1]
        if duplicates:
            raise ValueError(
                f"Duplicate field apiNames found: {set(duplicates)}"
            )
        return self

    def get_field(self, api_name: str) -> Optional[StructTypeField]:
        """Get a field by its apiName."""
        for field in self.fields:
            if field.api_name == api_name:
                return field
        return None

    def get_required_fields(self) -> list[StructTypeField]:
        """Get all required fields."""
        return [f for f in self.fields if f.required]

    def get_optional_fields(self) -> list[StructTypeField]:
        """Get all optional fields."""
        return [f for f in self.fields if not f.required]

    def get_field_names(self) -> list[str]:
        """Get all field apiNames."""
        return [f.api_name for f in self.fields]

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Palantir Foundry-compatible dictionary format."""
        result = super().to_foundry_dict()

        result["$type"] = "StructType"
        result["fields"] = [f.to_foundry_dict() for f in self.fields]
        result["status"] = self.status.value

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "StructType":
        """Create StructType from Palantir Foundry JSON format."""
        fields = [
            StructTypeField.from_foundry_dict(f)
            for f in data["fields"]
        ]

        return cls(
            rid=data.get("rid", generate_rid("ontology", "struct-type")),
            api_name=data["apiName"],
            display_name=data["displayName"],
            description=data.get("description"),
            fields=fields,
            status=StructTypeStatus(data.get("status", "EXPERIMENTAL")),
        )


# Predefined common StructTypes for convenience
class CommonStructTypes:
    """
    Factory for commonly used StructTypes.

    Usage:
        address_type = CommonStructTypes.address()
        money_type = CommonStructTypes.monetary_amount()
    """

    @staticmethod
    def address() -> StructType:
        """Create an Address StructType."""
        from ontology_definition.core.enums import DataType

        return StructType(
            api_name="Address",
            display_name="Address",
            description="Physical or mailing address.",
            fields=[
                StructTypeField(
                    api_name="street",
                    display_name="Street",
                    data_type=DataTypeSpec(type=DataType.STRING),
                    required=True,
                    constraints=StructFieldConstraints(max_length=255),
                ),
                StructTypeField(
                    api_name="city",
                    display_name="City",
                    data_type=DataTypeSpec(type=DataType.STRING),
                    required=True,
                    constraints=StructFieldConstraints(max_length=100),
                ),
                StructTypeField(
                    api_name="state",
                    display_name="State/Province",
                    data_type=DataTypeSpec(type=DataType.STRING),
                    required=False,
                    constraints=StructFieldConstraints(max_length=100),
                ),
                StructTypeField(
                    api_name="postalCode",
                    display_name="Postal Code",
                    data_type=DataTypeSpec(type=DataType.STRING),
                    required=True,
                    constraints=StructFieldConstraints(
                        pattern=r"^[A-Z0-9\- ]{3,10}$"
                    ),
                ),
                StructTypeField(
                    api_name="country",
                    display_name="Country",
                    data_type=DataTypeSpec(type=DataType.STRING),
                    required=True,
                    constraints=StructFieldConstraints(max_length=100),
                ),
            ],
            status=StructTypeStatus.ACTIVE,
        )

    @staticmethod
    def monetary_amount(
        currencies: Optional[list[str]] = None
    ) -> StructType:
        """Create a MonetaryAmount StructType."""
        from ontology_definition.core.enums import DataType

        if currencies is None:
            currencies = ["USD", "EUR", "GBP", "JPY", "KRW", "CNY"]

        return StructType(
            api_name="MonetaryAmount",
            display_name="Monetary Amount",
            description="Amount with currency.",
            fields=[
                StructTypeField(
                    api_name="amount",
                    display_name="Amount",
                    data_type=DataTypeSpec(
                        type=DataType.DECIMAL,
                        precision=18,
                        scale=2,
                    ),
                    required=True,
                ),
                StructTypeField(
                    api_name="currency",
                    display_name="Currency",
                    data_type=DataTypeSpec(type=DataType.STRING),
                    required=True,
                    constraints=StructFieldConstraints(
                        pattern=r"^[A-Z]{3}$",
                        enum=currencies,
                    ),
                ),
            ],
            status=StructTypeStatus.ACTIVE,
        )

    @staticmethod
    def geo_coordinate() -> StructType:
        """Create a GeoCoordinate StructType."""
        from ontology_definition.core.enums import DataType

        return StructType(
            api_name="GeoCoordinate",
            display_name="Geographic Coordinate",
            description="Latitude/longitude coordinate with optional altitude.",
            fields=[
                StructTypeField(
                    api_name="latitude",
                    display_name="Latitude",
                    data_type=DataTypeSpec(type=DataType.DOUBLE),
                    required=True,
                    constraints=StructFieldConstraints(
                        min_value=-90.0,
                        max_value=90.0,
                    ),
                ),
                StructTypeField(
                    api_name="longitude",
                    display_name="Longitude",
                    data_type=DataTypeSpec(type=DataType.DOUBLE),
                    required=True,
                    constraints=StructFieldConstraints(
                        min_value=-180.0,
                        max_value=180.0,
                    ),
                ),
                StructTypeField(
                    api_name="altitude",
                    display_name="Altitude (meters)",
                    data_type=DataTypeSpec(type=DataType.DOUBLE),
                    required=False,
                ),
            ],
            status=StructTypeStatus.ACTIVE,
        )

    @staticmethod
    def contact_info() -> StructType:
        """Create a ContactInfo StructType."""
        from ontology_definition.core.enums import DataType

        return StructType(
            api_name="ContactInfo",
            display_name="Contact Information",
            description="Contact details including email and phone.",
            fields=[
                StructTypeField(
                    api_name="email",
                    display_name="Email",
                    data_type=DataTypeSpec(type=DataType.STRING),
                    required=False,
                    constraints=StructFieldConstraints(
                        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                        max_length=255,
                    ),
                ),
                StructTypeField(
                    api_name="phone",
                    display_name="Phone",
                    data_type=DataTypeSpec(type=DataType.STRING),
                    required=False,
                    constraints=StructFieldConstraints(
                        pattern=r"^\+?[0-9\-\s\(\)]{7,20}$",
                    ),
                ),
                StructTypeField(
                    api_name="fax",
                    display_name="Fax",
                    data_type=DataTypeSpec(type=DataType.STRING),
                    required=False,
                ),
            ],
            status=StructTypeStatus.ACTIVE,
        )
