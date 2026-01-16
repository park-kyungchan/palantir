from __future__ import annotations

from enum import Enum
from typing import Any, Annotated, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from lib.oda.ontology.ontology_types import Cardinality, PropertyType


_SNAKE_ID_RE = r"^[a-z][a-z0-9_]*$"
_DISPLAY_RE = r"^.{1,200}$"


class FunctionLanguage(str, Enum):
    """
    Foundry docs (Functions overview) state supported languages are TypeScript and Python.
    https://www.palantir.com/docs/foundry/functions/overview/
    """

    TYPESCRIPT = "typescript"
    PYTHON = "python"


class DatasourceMode(str, Enum):
    """
    Permission checks in Foundry differ for single- vs multi-datasource objects.
    This is modeled as metadata because ODA does not (yet) have a true datasource layer.
    https://www.palantir.com/docs/foundry/object-edits/permission-checks/
    """

    SINGLE = "single"
    MULTI = "multi"


class LogicalOperator(str, Enum):
    """Submission criteria logical operators: all, any, no."""

    ALL = "all"
    ANY = "any"
    NO = "no"


class ComparisonOperator(str, Enum):
    """A minimal operator set for submission criteria conditions."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IN = "in"
    NOT_IN = "not_in"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class ValueRef(BaseModel):
    """
    Reference used by submission criteria and edits.

    - parameter: references an action parameter (by id)
    - property: references a property of a target object type
    - literal: embeds a literal value
    """

    model_config = ConfigDict(extra="forbid")

    source: Literal["parameter", "property", "literal"]
    name: Optional[str] = None
    object_type_id: Optional[str] = None
    value: Optional[Any] = None

    @model_validator(mode="after")
    def _validate_shape(self) -> "ValueRef":
        if self.source == "literal":
            if self.value is None:
                raise ValueError("literal ValueRef requires 'value'")
            return self

        if not self.name or not self.name.strip():
            raise ValueError(f"{self.source} ValueRef requires 'name'")

        if self.source == "property" and (not self.object_type_id or not self.object_type_id.strip()):
            raise ValueError("property ValueRef requires 'object_type_id'")

        return self


class PropertySpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    property_id: str = Field(..., pattern=_SNAKE_ID_RE)
    property_type: PropertyType
    required: bool = False
    description: str = ""


class ObjectTypeSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    object_type_id: str = Field(..., pattern=_SNAKE_ID_RE)
    display_name: str = Field(default="", pattern=_DISPLAY_RE)
    description: str = ""
    primary_key: str = Field(default="id", pattern=_SNAKE_ID_RE)
    datasource_mode: DatasourceMode = DatasourceMode.SINGLE
    properties: List[PropertySpec] = Field(default_factory=list)
    implements: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _normalize_display_name(self) -> "ObjectTypeSpec":
        if not self.display_name:
            self.display_name = self.object_type_id
        return self

    @model_validator(mode="after")
    def _validate_properties_unique(self) -> "ObjectTypeSpec":
        seen: set[str] = set()
        for prop in self.properties:
            if prop.property_id in seen:
                raise ValueError(f"Duplicate property_id in '{self.object_type_id}': {prop.property_id}")
            seen.add(prop.property_id)

        if self.primary_key not in seen:
            raise ValueError(
                f"primary_key '{self.primary_key}' not found in properties of '{self.object_type_id}'"
            )

        return self


class LinkTypeSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    link_type_id: str = Field(..., pattern=_SNAKE_ID_RE)
    display_name: str = Field(default="", pattern=_DISPLAY_RE)
    description: str = ""

    from_object_type_id: str = Field(..., pattern=_SNAKE_ID_RE)
    to_object_type_id: str = Field(..., pattern=_SNAKE_ID_RE)
    cardinality: Cardinality = Cardinality.ONE_TO_MANY

    reverse_link_type_id: Optional[str] = Field(default=None, pattern=_SNAKE_ID_RE)

    @model_validator(mode="after")
    def _normalize_display_name(self) -> "LinkTypeSpec":
        if not self.display_name:
            self.display_name = self.link_type_id
        return self


class InterfaceTypeSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    interface_id: str = Field(..., min_length=1, max_length=120)
    display_name: str = Field(default="", pattern=_DISPLAY_RE)
    description: str = ""
    extends: List[str] = Field(default_factory=list)
    required_properties: List[PropertySpec] = Field(default_factory=list)

    @model_validator(mode="after")
    def _normalize_display_name(self) -> "InterfaceTypeSpec":
        if not self.display_name:
            self.display_name = self.interface_id
        return self

    @model_validator(mode="after")
    def _validate_properties_unique(self) -> "InterfaceTypeSpec":
        seen: set[str] = set()
        for prop in self.required_properties:
            if prop.property_id in seen:
                raise ValueError(f"Duplicate required property_id in '{self.interface_id}': {prop.property_id}")
            seen.add(prop.property_id)
        return self


class ActionParameterSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    parameter_id: str = Field(..., pattern=_SNAKE_ID_RE)
    parameter_type: PropertyType = PropertyType.STRING
    required: bool = False
    description: str = ""


class ActionObjectEditSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    edit_type: Literal["create_object", "update_object", "delete_object"]
    object_type_id: str = Field(..., pattern=_SNAKE_ID_RE)
    object_id: Optional[ValueRef] = None
    properties: Dict[str, ValueRef] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_object_edit_shape(self) -> "ActionObjectEditSpec":
        if self.edit_type in {"update_object", "delete_object"} and self.object_id is None:
            raise ValueError(f"{self.edit_type} requires object_id ValueRef")
        return self


class ActionLinkEditSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    edit_type: Literal["create_link", "delete_link"]
    link_type_id: str = Field(..., pattern=_SNAKE_ID_RE)
    from_object_id: ValueRef
    to_object_id: ValueRef


ActionEditSpec = Annotated[
    Union[ActionObjectEditSpec, ActionLinkEditSpec],
    Field(discriminator="edit_type"),
]


class SubmissionConditionNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_type: Literal["condition"]
    left: ValueRef
    operator: ComparisonOperator
    right: Optional[ValueRef] = None
    failure_message: Optional[str] = None

    @model_validator(mode="after")
    def _validate_condition(self) -> "SubmissionConditionNode":
        if self.operator in {ComparisonOperator.IS_NULL, ComparisonOperator.IS_NOT_NULL}:
            return self
        if self.right is None:
            raise ValueError(f"operator '{self.operator}' requires 'right'")
        return self


class SubmissionLogicalNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_type: Literal["logical"]
    operator: LogicalOperator
    children: List["SubmissionCriteriaNode"]
    failure_message: Optional[str] = None

    @field_validator("children")
    @classmethod
    def _validate_children(cls, v: List["SubmissionCriteriaNode"]) -> List["SubmissionCriteriaNode"]:
        if not v:
            raise ValueError("logical operator must have at least 1 child node")
        return v


SubmissionCriteriaNode = Annotated[
    Union[SubmissionConditionNode, SubmissionLogicalNode],
    Field(discriminator="node_type"),
]


class SubmissionCriteriaSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    roots: List[SubmissionCriteriaNode] = Field(default_factory=list)

    @field_validator("roots")
    @classmethod
    def _validate_roots(cls, v: List[SubmissionCriteriaNode]) -> List[SubmissionCriteriaNode]:
        for node in v:
            msg = getattr(node, "failure_message", None)
            if not msg or not str(msg).strip():
                raise ValueError("Each root submission criteria node must define a non-empty failure_message")
        return v


class SideEffectSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    side_effect_type: str = Field(..., min_length=1, max_length=80)
    description: str = ""
    config: Dict[str, Any] = Field(default_factory=dict)


class ActionTypeSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_type_id: str = Field(..., pattern=_SNAKE_ID_RE)
    display_name: str = Field(default="", pattern=_DISPLAY_RE)
    description: str = ""

    parameters: List[ActionParameterSpec] = Field(default_factory=list)
    target_object_type_ids: List[str] = Field(default_factory=list)

    edits: List[ActionEditSpec] = Field(default_factory=list)
    submission_criteria: Optional[SubmissionCriteriaSpec] = None
    side_effects: List[SideEffectSpec] = Field(default_factory=list)

    @model_validator(mode="after")
    def _normalize_display_name(self) -> "ActionTypeSpec":
        if not self.display_name:
            self.display_name = self.action_type_id
        return self

    @model_validator(mode="after")
    def _validate_parameters_unique(self) -> "ActionTypeSpec":
        seen: set[str] = set()
        for p in self.parameters:
            if p.parameter_id in seen:
                raise ValueError(f"Duplicate parameter_id in '{self.action_type_id}': {p.parameter_id}")
            seen.add(p.parameter_id)
        return self


class FunctionTypeSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    function_type_id: str = Field(..., pattern=_SNAKE_ID_RE)
    display_name: str = Field(default="", pattern=_DISPLAY_RE)
    description: str = ""
    language: FunctionLanguage

    @model_validator(mode="after")
    def _normalize_display_name(self) -> "FunctionTypeSpec":
        if not self.display_name:
            self.display_name = self.function_type_id
        return self


class DynamicSecuritySpec(BaseModel):
    """
    Placeholder policy container for Foundry's 'dynamic security' kinetic element.
    https://www.palantir.com/docs/foundry/ontology/overview/
    """

    model_config = ConfigDict(extra="forbid")

    model: str = Field(default="unspecified", min_length=1, max_length=80)
    policies: List[Dict[str, Any]] = Field(default_factory=list)
    notes: str = ""


class SchemaMigrationInstruction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    op: Literal[
        "rename_property",
        "change_property_type",
        "delete_property",
        "add_property",
    ]
    object_type_id: str = Field(..., pattern=_SNAKE_ID_RE)
    property_id: str = Field(..., pattern=_SNAKE_ID_RE)
    new_property_id: Optional[str] = Field(default=None, pattern=_SNAKE_ID_RE)
    new_property_type: Optional[PropertyType] = None
    notes: str = ""


class SchemaMigrationPlan(BaseModel):
    """
    Foundry OSv2 constraint:
    - up to 500 schema migrations applied at a single time
    - does not support applying migration instructions on the primary key property
    https://www.palantir.com/docs/foundry/object-edits/schema-migrations/
    """

    model_config = ConfigDict(extra="forbid")

    instructions: List[SchemaMigrationInstruction] = Field(default_factory=list)

    @field_validator("instructions")
    @classmethod
    def _validate_batch_limit(cls, v: List[SchemaMigrationInstruction]) -> List[SchemaMigrationInstruction]:
        if len(v) > 500:
            raise ValueError("SchemaMigrationPlan supports up to 500 instructions per batch")
        return v


class OntologySpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spec_version: str = Field(default="foundry_mimic.v1")
    ontology_id: str = Field(..., pattern=_SNAKE_ID_RE)
    display_name: str = Field(default="", pattern=_DISPLAY_RE)
    description: str = ""

    object_types: List[ObjectTypeSpec] = Field(default_factory=list)
    link_types: List[LinkTypeSpec] = Field(default_factory=list)
    interface_types: List[InterfaceTypeSpec] = Field(default_factory=list)
    action_types: List[ActionTypeSpec] = Field(default_factory=list)
    function_types: List[FunctionTypeSpec] = Field(default_factory=list)

    dynamic_security: Optional[DynamicSecuritySpec] = None
    schema_migration_policy: Optional[SchemaMigrationPlan] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _normalize_display_name(self) -> "OntologySpec":
        if not self.display_name:
            self.display_name = self.ontology_id
        return self

    @model_validator(mode="after")
    def _validate_unique_ids(self) -> "OntologySpec":
        def uniq(kind: str, ids: List[str]) -> None:
            seen: set[str] = set()
            for i in ids:
                if i in seen:
                    raise ValueError(f"Duplicate {kind} id: {i}")
                seen.add(i)

        uniq("object_type", [o.object_type_id for o in self.object_types])
        uniq("link_type", [l.link_type_id for l in self.link_types])
        uniq("interface_type", [i.interface_id for i in self.interface_types])
        uniq("action_type", [a.action_type_id for a in self.action_types])
        uniq("function_type", [f.function_type_id for f in self.function_types])
        return self


class ObjectTypePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: Optional[str] = None
    datasource_mode: Optional[DatasourceMode] = None
    primary_key: Optional[str] = Field(default=None, pattern=_SNAKE_ID_RE)
    add_properties: List[PropertySpec] = Field(default_factory=list)
    remove_property_ids: List[str] = Field(default_factory=list)
    add_implements: List[str] = Field(default_factory=list)
    remove_implements: List[str] = Field(default_factory=list)


class AddObjectTypeOp(BaseModel):
    model_config = ConfigDict(extra="forbid")
    op: Literal["add_object_type"]
    object_type: ObjectTypeSpec


class UpdateObjectTypeOp(BaseModel):
    model_config = ConfigDict(extra="forbid")
    op: Literal["update_object_type"]
    object_type_id: str = Field(..., pattern=_SNAKE_ID_RE)
    patch: ObjectTypePatch


class DeleteObjectTypeOp(BaseModel):
    model_config = ConfigDict(extra="forbid")
    op: Literal["delete_object_type"]
    object_type_id: str = Field(..., pattern=_SNAKE_ID_RE)


class AddLinkTypeOp(BaseModel):
    model_config = ConfigDict(extra="forbid")
    op: Literal["add_link_type"]
    link_type: LinkTypeSpec


class DeleteLinkTypeOp(BaseModel):
    model_config = ConfigDict(extra="forbid")
    op: Literal["delete_link_type"]
    link_type_id: str = Field(..., pattern=_SNAKE_ID_RE)


class AddInterfaceTypeOp(BaseModel):
    model_config = ConfigDict(extra="forbid")
    op: Literal["add_interface_type"]
    interface_type: InterfaceTypeSpec


class DeleteInterfaceTypeOp(BaseModel):
    model_config = ConfigDict(extra="forbid")
    op: Literal["delete_interface_type"]
    interface_id: str = Field(..., min_length=1, max_length=120)


class AddActionTypeOp(BaseModel):
    model_config = ConfigDict(extra="forbid")
    op: Literal["add_action_type"]
    action_type: ActionTypeSpec


class DeleteActionTypeOp(BaseModel):
    model_config = ConfigDict(extra="forbid")
    op: Literal["delete_action_type"]
    action_type_id: str = Field(..., pattern=_SNAKE_ID_RE)


class AddFunctionTypeOp(BaseModel):
    model_config = ConfigDict(extra="forbid")
    op: Literal["add_function_type"]
    function_type: FunctionTypeSpec


class DeleteFunctionTypeOp(BaseModel):
    model_config = ConfigDict(extra="forbid")
    op: Literal["delete_function_type"]
    function_type_id: str = Field(..., pattern=_SNAKE_ID_RE)


class SetDynamicSecurityOp(BaseModel):
    model_config = ConfigDict(extra="forbid")
    op: Literal["set_dynamic_security"]
    dynamic_security: Optional[DynamicSecuritySpec] = None


ChangeOperation = Annotated[
    Union[
        AddObjectTypeOp,
        UpdateObjectTypeOp,
        DeleteObjectTypeOp,
        AddLinkTypeOp,
        DeleteLinkTypeOp,
        AddInterfaceTypeOp,
        DeleteInterfaceTypeOp,
        AddActionTypeOp,
        DeleteActionTypeOp,
        AddFunctionTypeOp,
        DeleteFunctionTypeOp,
        SetDynamicSecurityOp,
    ],
    Field(discriminator="op"),
]


class OntologyChangeSet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    change_set_id: str = Field(..., min_length=1, max_length=120)
    ontology_id: str = Field(..., pattern=_SNAKE_ID_RE)
    notes: str = ""

    operations: List[ChangeOperation] = Field(default_factory=list)
    schema_migration_plan: Optional[SchemaMigrationPlan] = None

