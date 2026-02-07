"""
Function Type Definition for Ontology.

Functions are executable logic units in the Ontology that enable custom computations,
data transformations, and Ontology modifications through code.

Aligned with Ontology.md Section 6 - Function specification.

Key components:
    - FunctionType: Main schema for function definitions
    - FunctionSignature: Input/output type definitions
    - FunctionParameter: Individual parameter specifications
    - FunctionMetadata: Metadata (className, methodName, version, apiName)

Function decorator types:
    - @Function(): General computation, derived values, data transformation
    - @OntologyEditFunction(): Write operations to Ontology (requires @Edits)
    - @Query(): Read-only queries exposed via API Gateway

Example:
    get_employees_by_dept = FunctionType(
        api_name="getEmployeesByDepartment",
        display_name="Get Employees By Department",
        decorator_type=FunctionDecoratorType.QUERY,
        metadata=FunctionMetadata(
            class_name="EmployeeService",
            method_name="findByDepartment",
            version="1.0.0",
            query_api_name="getEmployeesByDepartment",
        ),
        signature=FunctionSignature(
            inputs=[
                FunctionParameter(
                    name="dept",
                    param_type=FunctionParameterTypeSpec(type=FunctionParameterType.STRING),
                ),
            ],
            return_type=FunctionParameterTypeSpec(
                type=FunctionParameterType.OBJECT_SET,
                type_parameter="Employee",
            ),
        ),
    )
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ontology_definition.core.enums import (
    FunctionDecoratorType,
    FunctionParameterType,
    FunctionStatus,
)


class FunctionParameterTypeSpec(BaseModel):
    """
    Type specification for function parameters and return values.

    Supports:
    - Primitives: STRING, INTEGER, LONG, DOUBLE, FLOAT, BOOLEAN, TIMESTAMP, DATE, LOCAL_DATE
    - Ontology: OBJECT_TYPE, OBJECT_SET<T>, SINGLE_LINK<T>, MULTI_LINK<T>
    - Collections: ARRAY<T>, MAP<K,V>, SET<T>
    - Custom: STRUCT (with struct_type_ref)
    - Void: For return type only

    Examples:
        # Simple string type
        FunctionParameterTypeSpec(type=FunctionParameterType.STRING)

        # ObjectSet<Employee>
        FunctionParameterTypeSpec(
            type=FunctionParameterType.OBJECT_SET,
            type_parameter="Employee"
        )

        # Array<String>
        FunctionParameterTypeSpec(
            type=FunctionParameterType.ARRAY,
            item_type=FunctionParameterTypeSpec(type=FunctionParameterType.STRING)
        )

        # Map<String, Integer>
        FunctionParameterTypeSpec(
            type=FunctionParameterType.MAP,
            key_type=FunctionParameterTypeSpec(type=FunctionParameterType.STRING),
            value_type=FunctionParameterTypeSpec(type=FunctionParameterType.INTEGER)
        )
    """

    type: FunctionParameterType = Field(
        ...,
        description="Base parameter type.",
    )

    # For OBJECT_TYPE, OBJECT_SET, SINGLE_LINK, MULTI_LINK
    type_parameter: Optional[str] = Field(
        default=None,
        description="For ontology types, the ObjectType apiName (e.g., 'Employee').",
        alias="typeParameter",
    )

    # For ARRAY, SET
    item_type: Optional["FunctionParameterTypeSpec"] = Field(
        default=None,
        description="For ARRAY and SET, the element type.",
        alias="itemType",
    )

    # For MAP
    key_type: Optional["FunctionParameterTypeSpec"] = Field(
        default=None,
        description="For MAP, the key type.",
        alias="keyType",
    )

    value_type: Optional["FunctionParameterTypeSpec"] = Field(
        default=None,
        description="For MAP, the value type.",
        alias="valueType",
    )

    # For STRUCT
    struct_type_ref: Optional[str] = Field(
        default=None,
        description="For STRUCT, reference to a StructType definition.",
        alias="structTypeRef",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_type_config(self) -> "FunctionParameterTypeSpec":
        """Validate that required configuration is present for each type."""
        # Ontology types require type_parameter
        if self.type in (
            FunctionParameterType.OBJECT_TYPE,
            FunctionParameterType.OBJECT_SET,
            FunctionParameterType.SINGLE_LINK,
            FunctionParameterType.MULTI_LINK,
        ):
            if not self.type_parameter:
                raise ValueError(f"{self.type.value} requires type_parameter (ObjectType apiName)")

        # ARRAY and SET require item_type
        if self.type in (FunctionParameterType.ARRAY, FunctionParameterType.SET):
            if not self.item_type:
                raise ValueError(f"{self.type.value} requires item_type specification")

        # MAP requires key_type and value_type
        if self.type == FunctionParameterType.MAP:
            if not self.key_type or not self.value_type:
                raise ValueError("MAP requires both key_type and value_type")

        # STRUCT requires struct_type_ref
        if self.type == FunctionParameterType.STRUCT:
            if not self.struct_type_ref:
                raise ValueError("STRUCT requires struct_type_ref")

        return self

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {"type": self.type.value}

        if self.type_parameter:
            result["typeParameter"] = self.type_parameter

        if self.item_type:
            result["itemType"] = self.item_type.to_foundry_dict()

        if self.key_type:
            result["keyType"] = self.key_type.to_foundry_dict()

        if self.value_type:
            result["valueType"] = self.value_type.to_foundry_dict()

        if self.struct_type_ref:
            result["structTypeRef"] = self.struct_type_ref

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "FunctionParameterTypeSpec":
        """Create from Foundry JSON format."""
        item_type = None
        if data.get("itemType"):
            item_type = cls.from_foundry_dict(data["itemType"])

        key_type = None
        if data.get("keyType"):
            key_type = cls.from_foundry_dict(data["keyType"])

        value_type = None
        if data.get("valueType"):
            value_type = cls.from_foundry_dict(data["valueType"])

        return cls(
            type=FunctionParameterType(data["type"]),
            type_parameter=data.get("typeParameter"),
            item_type=item_type,
            key_type=key_type,
            value_type=value_type,
            struct_type_ref=data.get("structTypeRef"),
        )


class FunctionParameter(BaseModel):
    """
    Parameter definition for a function input.

    Each parameter specifies:
    - name: Parameter identifier
    - param_type: Type specification
    - optional: Whether the parameter can be omitted
    - description: Documentation
    - default_value: Default value if optional

    Example:
        FunctionParameter(
            name="departmentCode",
            param_type=FunctionParameterTypeSpec(type=FunctionParameterType.STRING),
            optional=False,
            description="Department code to filter employees"
        )
    """

    name: str = Field(
        ...,
        description="Parameter name (identifier).",
        min_length=1,
        max_length=255,
        pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$",
    )

    param_type: FunctionParameterTypeSpec = Field(
        ...,
        description="Type specification for this parameter.",
        alias="type",
    )

    optional: bool = Field(
        default=False,
        description="If true, this parameter can be omitted.",
    )

    description: Optional[str] = Field(
        default=None,
        description="Documentation for this parameter.",
        max_length=4096,
    )

    default_value: Optional[Any] = Field(
        default=None,
        description="Default value if parameter is optional and not provided.",
        alias="defaultValue",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_default_value(self) -> "FunctionParameter":
        """Validate that default value is only set for optional parameters."""
        if self.default_value is not None and not self.optional:
            raise ValueError("default_value can only be set for optional parameters")
        return self

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "name": self.name,
            "type": self.param_type.to_foundry_dict(),
        }

        if self.optional:
            result["optional"] = True

        if self.description:
            result["description"] = self.description

        if self.default_value is not None:
            result["defaultValue"] = self.default_value

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "FunctionParameter":
        """Create from Foundry JSON format."""
        return cls(
            name=data["name"],
            param_type=FunctionParameterTypeSpec.from_foundry_dict(data["type"]),
            optional=data.get("optional", False),
            description=data.get("description"),
            default_value=data.get("defaultValue"),
        )


class FunctionSignature(BaseModel):
    """
    Function signature defining inputs and return type.

    Specifies the complete type signature of a function:
    - inputs: List of input parameters
    - return_type: Return type (VOID for void functions)

    Example:
        # Function signature: (dept: string) -> ObjectSet<Employee>
        FunctionSignature(
            inputs=[
                FunctionParameter(
                    name="dept",
                    param_type=FunctionParameterTypeSpec(type=FunctionParameterType.STRING),
                )
            ],
            return_type=FunctionParameterTypeSpec(
                type=FunctionParameterType.OBJECT_SET,
                type_parameter="Employee"
            )
        )
    """

    inputs: list[FunctionParameter] = Field(
        default_factory=list,
        description="Input parameters for the function.",
    )

    return_type: FunctionParameterTypeSpec = Field(
        ...,
        description="Return type of the function. Use VOID for void functions.",
        alias="returnType",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_unique_param_names(self) -> "FunctionSignature":
        """Validate that parameter names are unique."""
        names = [p.name for p in self.inputs]
        duplicates = [n for n in names if names.count(n) > 1]
        if duplicates:
            raise ValueError(f"Duplicate parameter names: {set(duplicates)}")
        return self

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        return {
            "inputs": [p.to_foundry_dict() for p in self.inputs],
            "returnType": self.return_type.to_foundry_dict(),
        }

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "FunctionSignature":
        """Create from Foundry JSON format."""
        inputs = [FunctionParameter.from_foundry_dict(p) for p in data.get("inputs", [])]
        return cls(
            inputs=inputs,
            return_type=FunctionParameterTypeSpec.from_foundry_dict(data["returnType"]),
        )


class FunctionMetadata(BaseModel):
    """
    Metadata for a function definition.

    Contains implementation details:
    - class_name: TypeScript/Python class containing the function
    - method_name: Method name (unique identifier within class)
    - version: Semantic version (semver)
    - query_api_name: For @Query functions, the API name for Gateway exposure

    Example:
        FunctionMetadata(
            class_name="EmployeeService",
            method_name="findByDepartment",
            version="1.0.0",
            query_api_name="getEmployeesByDepartment"
        )
    """

    class_name: str = Field(
        ...,
        description="TypeScript/Python class name containing the function.",
        min_length=1,
        max_length=255,
        alias="className",
    )

    method_name: str = Field(
        ...,
        description="Method name (unique identifier within the class).",
        min_length=1,
        max_length=255,
        pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$",
        alias="methodName",
    )

    version: str = Field(
        default="1.0.0",
        description="Semantic version (semver format: MAJOR.MINOR.PATCH).",
        pattern=r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$",
    )

    query_api_name: Optional[str] = Field(
        default=None,
        description="For @Query functions, the API name exposed via Gateway.",
        alias="queryApiName",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "className": self.class_name,
            "methodName": self.method_name,
            "version": self.version,
        }

        if self.query_api_name:
            result["queryApiName"] = self.query_api_name

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "FunctionMetadata":
        """Create from Foundry JSON format."""
        return cls(
            class_name=data["className"],
            method_name=data["methodName"],
            version=data.get("version", "1.0.0"),
            query_api_name=data.get("queryApiName"),
        )


class EditsDeclaration(BaseModel):
    """
    Declaration of ObjectTypes that an @OntologyEditFunction can modify.

    Represents the @Edits(ObjectType1, ObjectType2) decorator.

    Example:
        EditsDeclaration(
            object_types=["Employee", "Ticket"]
        )
    """

    object_types: list[str] = Field(
        ...,
        description="List of ObjectType apiNames that this function can edit.",
        min_length=1,
        alias="objectTypes",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        return {"objectTypes": self.object_types}

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "EditsDeclaration":
        """Create from Foundry JSON format."""
        return cls(object_types=data["objectTypes"])


class FunctionType(BaseModel):
    """
    Function type definition - executable logic unit in the Ontology.

    Functions enable custom computations, data transformations, and Ontology
    modifications through code.

    Decorator types:
    - @Function(): General computation, derived values, data transformation
    - @OntologyEditFunction(): Write operations to Ontology (requires @Edits)
    - @Query(): Read-only queries exposed via API Gateway

    IMPORTANT:
    - @OntologyEditFunction MUST have edits declaration
    - @Query functions MUST NOT have side effects
    - @Query functions should specify query_api_name in metadata

    Example:
        # Query function
        get_employees = FunctionType(
            api_name="getEmployeesByDepartment",
            display_name="Get Employees By Department",
            decorator_type=FunctionDecoratorType.QUERY,
            metadata=FunctionMetadata(
                class_name="EmployeeService",
                method_name="findByDepartment",
                version="1.0.0",
                query_api_name="getEmployeesByDepartment",
            ),
            signature=FunctionSignature(
                inputs=[
                    FunctionParameter(
                        name="dept",
                        param_type=FunctionParameterTypeSpec(
                            type=FunctionParameterType.STRING
                        ),
                    )
                ],
                return_type=FunctionParameterTypeSpec(
                    type=FunctionParameterType.OBJECT_SET,
                    type_parameter="Employee"
                ),
            ),
        )

        # Ontology Edit Function
        create_ticket = FunctionType(
            api_name="createTicketAndAssign",
            display_name="Create Ticket and Assign",
            decorator_type=FunctionDecoratorType.ONTOLOGY_EDIT_FUNCTION,
            metadata=FunctionMetadata(
                class_name="TicketService",
                method_name="createTicketAndAssign",
                version="1.0.0",
            ),
            signature=FunctionSignature(
                inputs=[
                    FunctionParameter(
                        name="employee",
                        param_type=FunctionParameterTypeSpec(
                            type=FunctionParameterType.OBJECT_TYPE,
                            type_parameter="Employee"
                        ),
                    ),
                    FunctionParameter(
                        name="ticketId",
                        param_type=FunctionParameterTypeSpec(
                            type=FunctionParameterType.INTEGER
                        ),
                    ),
                ],
                return_type=FunctionParameterTypeSpec(type=FunctionParameterType.VOID),
            ),
            edits=EditsDeclaration(object_types=["Employee", "Ticket"]),
        )
    """

    # Identity
    api_name: str = Field(
        ...,
        description="Unique identifier for this function.",
        min_length=1,
        max_length=255,
        pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$",
        alias="apiName",
    )

    display_name: str = Field(
        ...,
        description="Human-friendly name for UI display.",
        min_length=1,
        max_length=255,
        alias="displayName",
    )

    description: Optional[str] = Field(
        default=None,
        description="Documentation for this function.",
        max_length=4096,
    )

    # Decorator type
    decorator_type: FunctionDecoratorType = Field(
        ...,
        description="Function decorator type (@Function, @OntologyEditFunction, @Query).",
        alias="decoratorType",
    )

    # Metadata
    metadata: FunctionMetadata = Field(
        ...,
        description="Function metadata (className, methodName, version, apiName).",
    )

    # Signature
    signature: FunctionSignature = Field(
        ...,
        description="Function signature (inputs and return type).",
    )

    # Edits declaration (required for @OntologyEditFunction)
    edits: Optional[EditsDeclaration] = Field(
        default=None,
        description="For @OntologyEditFunction, the ObjectTypes that can be edited.",
    )

    # Status
    status: FunctionStatus = Field(
        default=FunctionStatus.EXPERIMENTAL,
        description="Lifecycle status of this function.",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        use_enum_values=False,
    )

    @model_validator(mode="after")
    def validate_ontology_edit_function(self) -> "FunctionType":
        """
        Validate @OntologyEditFunction requirements:
        1. Must have edits declaration
        2. Return type should be VOID
        """
        if self.decorator_type == FunctionDecoratorType.ONTOLOGY_EDIT_FUNCTION:
            if not self.edits:
                raise ValueError(
                    "@OntologyEditFunction requires @Edits declaration "
                    "(specify which ObjectTypes can be edited)"
                )

            # Return type should be VOID for @OntologyEditFunction
            if self.signature.return_type.type != FunctionParameterType.VOID:
                raise ValueError(
                    "@OntologyEditFunction should return VOID (void | Promise<void>)"
                )

        return self

    @model_validator(mode="after")
    def validate_query_function(self) -> "FunctionType":
        """
        Validate @Query function requirements:
        1. Should have query_api_name in metadata
        """
        if self.decorator_type == FunctionDecoratorType.QUERY:
            if not self.metadata.query_api_name:
                raise ValueError(
                    "@Query function should have query_api_name in metadata "
                    "for API Gateway exposure"
                )

        return self

    @model_validator(mode="after")
    def validate_no_edits_for_non_edit_function(self) -> "FunctionType":
        """Validate that non-edit functions don't have edits declaration."""
        if self.decorator_type != FunctionDecoratorType.ONTOLOGY_EDIT_FUNCTION:
            if self.edits is not None:
                raise ValueError(
                    f"@Edits declaration is only valid for @OntologyEditFunction, "
                    f"not for {self.decorator_type.value}"
                )

        return self

    def get_input_parameter(self, name: str) -> Optional[FunctionParameter]:
        """Get an input parameter by name."""
        for param in self.signature.inputs:
            if param.name == name:
                return param
        return None

    def get_required_parameters(self) -> list[FunctionParameter]:
        """Get all required (non-optional) parameters."""
        return [p for p in self.signature.inputs if not p.optional]

    def get_optional_parameters(self) -> list[FunctionParameter]:
        """Get all optional parameters."""
        return [p for p in self.signature.inputs if p.optional]

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Palantir Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "apiName": self.api_name,
            "displayName": self.display_name,
            "decoratorType": self.decorator_type.value,
            "metadata": self.metadata.to_foundry_dict(),
            "signature": self.signature.to_foundry_dict(),
            "status": self.status.value,
        }

        if self.description:
            result["description"] = self.description

        if self.edits:
            result["edits"] = self.edits.to_foundry_dict()

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "FunctionType":
        """Create from Foundry JSON format."""
        edits = None
        if data.get("edits"):
            edits = EditsDeclaration.from_foundry_dict(data["edits"])

        return cls(
            api_name=data["apiName"],
            display_name=data["displayName"],
            description=data.get("description"),
            decorator_type=FunctionDecoratorType(data["decoratorType"]),
            metadata=FunctionMetadata.from_foundry_dict(data["metadata"]),
            signature=FunctionSignature.from_foundry_dict(data["signature"]),
            edits=edits,
            status=FunctionStatus(data.get("status", "EXPERIMENTAL")),
        )


# Update forward references
FunctionParameterTypeSpec.model_rebuild()
