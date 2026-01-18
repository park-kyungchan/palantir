"""
ActionType Definition for Ontology.

An ActionType defines the schema for a set of changes or edits to objects,
property values, and links that a user can take at once in Palantir Foundry.

Key components:
    - Parameters: User inputs required for the action
    - Affected ObjectTypes: ObjectTypes that can be created/modified/deleted
    - Edit Specifications: Declarative edit operations
    - Submission Criteria: Preconditions for execution
    - Side Effects: Post-execution effects (notifications, webhooks)
    - Implementation: How the action is implemented

IMPORTANT: Like LinkType, ActionType does NOT support 'endorsed' status.
Only ObjectTypes can be endorsed.

Example:
    modify_file_action = ActionType(
        api_name="file.modify",
        display_name="Modify File",
        description="Modifies an existing file in the repository.",
        category="file",
        hazardous=True,
        parameters=[
            ActionParameter(
                api_name="filePath",
                display_name="File Path",
                data_type=ParameterDataType(type=ParameterType.STRING),
                required=True,
            ),
        ],
        affected_object_types=[
            AffectedObjectType(
                object_type_api_name="File",
                operations=[ObjectOperation.MODIFY],
            ),
        ],
        implementation=ActionImplementation(
            type=ActionImplementationType.FUNCTION_BACKED,
            function_ref="lib.oda.actions.file.modify_file",
        ),
    )
"""

from __future__ import annotations

# ============================================================================
# Enums for ActionType
# ============================================================================
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ontology_definition.core.base import OntologyEntity
from ontology_definition.core.identifiers import generate_rid


class ParameterType(str, Enum):
    """
    Data types available for action parameters.

    Subset of DataType plus special action-specific types:
    - OBJECT_PICKER: Select an object instance
    - OBJECT_SET: Select multiple objects
    - ATTACHMENT: File attachment
    """

    STRING = "STRING"
    INTEGER = "INTEGER"
    LONG = "LONG"
    FLOAT = "FLOAT"
    DOUBLE = "DOUBLE"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"
    TIMESTAMP = "TIMESTAMP"
    ARRAY = "ARRAY"
    OBJECT_PICKER = "OBJECT_PICKER"
    OBJECT_SET = "OBJECT_SET"
    ATTACHMENT = "ATTACHMENT"
    STRUCT = "STRUCT"


class ObjectOperation(str, Enum):
    """Operations that an action can perform on ObjectTypes."""

    CREATE = "CREATE"
    MODIFY = "MODIFY"
    DELETE = "DELETE"


class EditOperationType(str, Enum):
    """Types of declarative edit operations."""

    CREATE_OBJECT = "CREATE_OBJECT"
    MODIFY_OBJECT = "MODIFY_OBJECT"
    DELETE_OBJECT = "DELETE_OBJECT"
    CREATE_LINK = "CREATE_LINK"
    DELETE_LINK = "DELETE_LINK"
    MODIFY_PROPERTY = "MODIFY_PROPERTY"


class ObjectSelectionType(str, Enum):
    """How to select object(s) for edit operations."""

    PARAMETER = "PARAMETER"
    QUERY = "QUERY"
    CURRENT = "CURRENT"


class EditConditionType(str, Enum):
    """Types of conditions for conditional edit execution."""

    PARAMETER_EQUALS = "PARAMETER_EQUALS"
    PARAMETER_NOT_NULL = "PARAMETER_NOT_NULL"
    OBJECT_STATE = "OBJECT_STATE"
    EXPRESSION = "EXPRESSION"


class SubmissionCriterionType(str, Enum):
    """Types of submission criteria (preconditions)."""

    PARAMETER_VALIDATION = "PARAMETER_VALIDATION"
    OBJECT_STATE_CHECK = "OBJECT_STATE_CHECK"
    PERMISSION_CHECK = "PERMISSION_CHECK"
    CARDINALITY_CHECK = "CARDINALITY_CHECK"
    CUSTOM_FUNCTION = "CUSTOM_FUNCTION"


class CriterionSeverity(str, Enum):
    """Severity level for submission criteria failures."""

    ERROR = "ERROR"
    WARNING = "WARNING"


class SideEffectType(str, Enum):
    """Types of post-execution side effects."""

    NOTIFICATION = "NOTIFICATION"
    WEBHOOK = "WEBHOOK"
    EMAIL = "EMAIL"
    AUDIT_LOG = "AUDIT_LOG"
    TRIGGER_ACTION = "TRIGGER_ACTION"
    CUSTOM_FUNCTION = "CUSTOM_FUNCTION"


class NotificationChannel(str, Enum):
    """Channels for notification side effects."""

    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    SLACK = "SLACK"
    TEAMS = "TEAMS"


class ActionImplementationType(str, Enum):
    """How the action logic is implemented."""

    DECLARATIVE = "DECLARATIVE"
    FUNCTION_BACKED = "FUNCTION_BACKED"
    INLINE_EDIT = "INLINE_EDIT"


class FunctionLanguage(str, Enum):
    """Programming languages for function-backed actions."""

    TYPESCRIPT = "TYPESCRIPT"
    PYTHON = "PYTHON"


class ObjectAccessLevel(str, Enum):
    """Required access levels on ObjectTypes."""

    READ = "READ"
    WRITE = "WRITE"
    DELETE = "DELETE"
    ADMIN = "ADMIN"


class ActionTypeStatus(str, Enum):
    """
    Lifecycle status for ActionTypes.

    Same as ObjectStatus but WITHOUT ENDORSED status.
    Only ObjectTypes can be endorsed.
    """

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


class AuditLogLevel(str, Enum):
    """Detail level for audit logs."""

    MINIMAL = "MINIMAL"
    STANDARD = "STANDARD"
    DETAILED = "DETAILED"


class UndoStrategy(str, Enum):
    """Strategies for undoing an action."""

    INVERSE_ACTION = "INVERSE_ACTION"
    RESTORE_SNAPSHOT = "RESTORE_SNAPSHOT"
    CUSTOM_FUNCTION = "CUSTOM_FUNCTION"


class ParameterInputType(str, Enum):
    """UI input types for parameter rendering."""

    TEXT = "text"
    TEXTAREA = "textarea"
    NUMBER = "number"
    SELECT = "select"
    MULTISELECT = "multiselect"
    DATEPICKER = "datepicker"
    FILEPICKER = "filepicker"
    OBJECTPICKER = "objectpicker"


# ============================================================================
# Parameter-related Models
# ============================================================================


class ParameterDataType(BaseModel):
    """
    Data type specification for action parameter.
    """

    type: ParameterType = Field(
        ...,
        description="Base parameter type.",
    )

    object_type_ref: str | None = Field(
        default=None,
        description="For OBJECT_PICKER/OBJECT_SET, the ObjectType apiName to pick from.",
        alias="objectTypeRef",
    )

    array_item_type: ParameterDataType | None = Field(
        default=None,
        description="For ARRAY type, the item type.",
        alias="arrayItemType",
    )

    struct_definition: dict[str, Any] | None = Field(
        default=None,
        description="For STRUCT type, the field definitions.",
        alias="structDefinition",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_type_config(self) -> ParameterDataType:
        """Validate required config based on type."""
        if self.type in (ParameterType.OBJECT_PICKER, ParameterType.OBJECT_SET):
            if not self.object_type_ref:
                raise ValueError(
                    f"{self.type.value} requires object_type_ref specification"
                )
        if self.type == ParameterType.ARRAY and self.array_item_type is None:
            raise ValueError("ARRAY type requires array_item_type specification")
        return self

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {"type": self.type.value}
        if self.object_type_ref:
            result["objectTypeRef"] = self.object_type_ref
        if self.array_item_type:
            result["arrayItemType"] = self.array_item_type.to_foundry_dict()
        if self.struct_definition:
            result["structDefinition"] = self.struct_definition
        return result


class ParameterConstraints(BaseModel):
    """
    Validation constraints for action parameter.
    """

    enum: list[Any] | None = Field(
        default=None,
        description="Allowed values.",
    )

    min_value: int | float | None = Field(
        default=None,
        description="Minimum numeric value.",
        alias="minValue",
    )

    max_value: int | float | None = Field(
        default=None,
        description="Maximum numeric value.",
        alias="maxValue",
    )

    min_length: int | None = Field(
        default=None,
        description="Minimum string length.",
        ge=0,
        alias="minLength",
    )

    max_length: int | None = Field(
        default=None,
        description="Maximum string length.",
        ge=0,
        alias="maxLength",
    )

    pattern: str | None = Field(
        default=None,
        description="Regular expression pattern for validation.",
    )

    object_filter: str | None = Field(
        default=None,
        description="For OBJECT_PICKER, filter expression to limit selectable objects.",
        alias="objectFilter",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {}
        if self.enum:
            result["enum"] = self.enum
        if self.min_value is not None:
            result["minValue"] = self.min_value
        if self.max_value is not None:
            result["maxValue"] = self.max_value
        if self.min_length is not None:
            result["minLength"] = self.min_length
        if self.max_length is not None:
            result["maxLength"] = self.max_length
        if self.pattern:
            result["pattern"] = self.pattern
        if self.object_filter:
            result["objectFilter"] = self.object_filter
        return result


class ParameterUIHints(BaseModel):
    """
    UI rendering hints for parameter input.
    """

    input_type: ParameterInputType | None = Field(
        default=None,
        description="Type of UI input control.",
        alias="inputType",
    )

    placeholder: str | None = Field(
        default=None,
        description="Placeholder text for input.",
    )

    helper_text: str | None = Field(
        default=None,
        description="Helper text displayed below input.",
        alias="helperText",
    )

    order: int | None = Field(
        default=None,
        description="Display order in form.",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {}
        if self.input_type:
            result["inputType"] = self.input_type.value
        if self.placeholder:
            result["placeholder"] = self.placeholder
        if self.helper_text:
            result["helperText"] = self.helper_text
        if self.order is not None:
            result["order"] = self.order
        return result


class ActionParameter(BaseModel):
    """
    Input parameter definition for an action.

    Parameters define what inputs users must provide when executing an action.
    """

    api_name: str = Field(
        ...,
        description="Unique parameter identifier.",
        min_length=1,
        max_length=255,
        pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$",
        alias="apiName",
    )

    display_name: str = Field(
        ...,
        description="Human-friendly parameter name.",
        min_length=1,
        max_length=255,
        alias="displayName",
    )

    description: str | None = Field(
        default=None,
        description="Parameter documentation.",
        max_length=4096,
    )

    data_type: ParameterDataType = Field(
        ...,
        description="Data type for this parameter.",
        alias="dataType",
    )

    required: bool = Field(
        default=False,
        description="If true, parameter must be provided.",
    )

    default_value: Any | None = Field(
        default=None,
        description="Default value if not provided.",
        alias="defaultValue",
    )

    constraints: ParameterConstraints | None = Field(
        default=None,
        description="Validation constraints for this parameter.",
    )

    ui_hints: ParameterUIHints | None = Field(
        default=None,
        description="UI rendering hints.",
        alias="uiHints",
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
        if self.ui_hints:
            result["uiHints"] = self.ui_hints.to_foundry_dict()
        return result


# ============================================================================
# Affected ObjectTypes and Edit Specifications
# ============================================================================


class AffectedObjectType(BaseModel):
    """
    ObjectType affected by this action.
    """

    object_type_api_name: str = Field(
        ...,
        description="apiName of the affected ObjectType.",
        alias="objectTypeApiName",
    )

    operations: list[ObjectOperation] = Field(
        ...,
        description="Operations this action can perform on this ObjectType.",
        min_length=1,
    )

    modifiable_properties: list[str] = Field(
        default_factory=list,
        description="For MODIFY, which properties can be changed. Empty = all.",
        alias="modifiableProperties",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "objectTypeApiName": self.object_type_api_name,
            "operations": [op.value for op in self.operations],
        }
        if self.modifiable_properties:
            result["modifiableProperties"] = self.modifiable_properties
        return result


class PropertyMapping(BaseModel):
    """
    Mapping from action parameter to object property.
    """

    target_property: str = Field(
        ...,
        description="apiName of the property to set.",
        alias="targetProperty",
    )

    source_parameter: str | None = Field(
        default=None,
        description="apiName of the parameter providing the value.",
        alias="sourceParameter",
    )

    static_value: Any | None = Field(
        default=None,
        description="Static value to set (instead of parameter).",
        alias="staticValue",
    )

    expression: str | None = Field(
        default=None,
        description="Expression to compute the value.",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_value_source(self) -> PropertyMapping:
        """Validate that at least one value source is provided."""
        if not any([self.source_parameter, self.static_value is not None, self.expression]):
            raise ValueError(
                "PropertyMapping must specify source_parameter, static_value, or expression"
            )
        return self

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {"targetProperty": self.target_property}
        if self.source_parameter:
            result["sourceParameter"] = self.source_parameter
        if self.static_value is not None:
            result["staticValue"] = self.static_value
        if self.expression:
            result["expression"] = self.expression
        return result


class ObjectSelection(BaseModel):
    """
    How to select object(s) for modification/deletion.
    """

    selection_type: ObjectSelectionType = Field(
        ...,
        description="Type of selection.",
        alias="selectionType",
    )

    parameter_ref: str | None = Field(
        default=None,
        description="For PARAMETER, the parameter containing the object reference.",
        alias="parameterRef",
    )

    query_expression: str | None = Field(
        default=None,
        description="For QUERY, expression to find objects.",
        alias="queryExpression",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {"selectionType": self.selection_type.value}
        if self.parameter_ref:
            result["parameterRef"] = self.parameter_ref
        if self.query_expression:
            result["queryExpression"] = self.query_expression
        return result


class LinkSelection(BaseModel):
    """
    How to select objects for link creation/deletion.
    """

    source_object_parameter: str | None = Field(
        default=None,
        description="Parameter containing source object reference.",
        alias="sourceObjectParameter",
    )

    target_object_parameter: str | None = Field(
        default=None,
        description="Parameter containing target object reference.",
        alias="targetObjectParameter",
    )

    source_object_query: str | None = Field(
        default=None,
        description="Query to find source object(s).",
        alias="sourceObjectQuery",
    )

    target_object_query: str | None = Field(
        default=None,
        description="Query to find target object(s).",
        alias="targetObjectQuery",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {}
        if self.source_object_parameter:
            result["sourceObjectParameter"] = self.source_object_parameter
        if self.target_object_parameter:
            result["targetObjectParameter"] = self.target_object_parameter
        if self.source_object_query:
            result["sourceObjectQuery"] = self.source_object_query
        if self.target_object_query:
            result["targetObjectQuery"] = self.target_object_query
        return result


class EditCondition(BaseModel):
    """
    Condition for conditional edit execution.
    """

    condition_type: EditConditionType = Field(
        ...,
        description="Type of condition.",
        alias="conditionType",
    )

    parameter_ref: str | None = Field(
        default=None,
        description="Parameter to check.",
        alias="parameterRef",
    )

    expected_value: Any | None = Field(
        default=None,
        description="Expected value for PARAMETER_EQUALS.",
        alias="expectedValue",
    )

    expression: str | None = Field(
        default=None,
        description="Boolean expression for EXPRESSION type.",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {"conditionType": self.condition_type.value}
        if self.parameter_ref:
            result["parameterRef"] = self.parameter_ref
        if self.expected_value is not None:
            result["expectedValue"] = self.expected_value
        if self.expression:
            result["expression"] = self.expression
        return result


class EditSpecification(BaseModel):
    """
    Declarative edit operation that defines a specific change.

    Edit specifications define what changes occur when an action is executed,
    using a declarative model rather than imperative code.
    """

    operation_type: EditOperationType = Field(
        ...,
        description="Type of edit operation.",
        alias="operationType",
    )

    target_object_type: str | None = Field(
        default=None,
        description="ObjectType being affected.",
        alias="targetObjectType",
    )

    target_link_type: str | None = Field(
        default=None,
        description="For link operations, the LinkType being affected.",
        alias="targetLinkType",
    )

    property_mappings: list[PropertyMapping] = Field(
        default_factory=list,
        description="How parameter values map to object properties.",
        alias="propertyMappings",
    )

    object_selection: ObjectSelection | None = Field(
        default=None,
        description="How to select which object(s) to modify/delete.",
        alias="objectSelection",
    )

    link_selection: LinkSelection | None = Field(
        default=None,
        description="For link operations, how to select the objects to link.",
        alias="linkSelection",
    )

    conditional: EditCondition | None = Field(
        default=None,
        description="Condition that must be true for this edit to apply.",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_edit_config(self) -> EditSpecification:
        """Validate edit specification has required config for operation type."""
        if self.operation_type in (
            EditOperationType.CREATE_OBJECT,
            EditOperationType.MODIFY_OBJECT,
            EditOperationType.DELETE_OBJECT,
            EditOperationType.MODIFY_PROPERTY,
        ):
            if not self.target_object_type:
                raise ValueError(
                    f"{self.operation_type.value} requires target_object_type"
                )
        if self.operation_type in (
            EditOperationType.CREATE_LINK,
            EditOperationType.DELETE_LINK,
        ):
            if not self.target_link_type:
                raise ValueError(
                    f"{self.operation_type.value} requires target_link_type"
                )
        return self

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {"operationType": self.operation_type.value}
        if self.target_object_type:
            result["targetObjectType"] = self.target_object_type
        if self.target_link_type:
            result["targetLinkType"] = self.target_link_type
        if self.property_mappings:
            result["propertyMappings"] = [pm.to_foundry_dict() for pm in self.property_mappings]
        if self.object_selection:
            result["objectSelection"] = self.object_selection.to_foundry_dict()
        if self.link_selection:
            result["linkSelection"] = self.link_selection.to_foundry_dict()
        if self.conditional:
            result["conditional"] = self.conditional.to_foundry_dict()
        return result


# ============================================================================
# Submission Criteria
# ============================================================================


class SubmissionCriterion(BaseModel):
    """
    Precondition that must be satisfied to execute the action.

    Submission criteria are evaluated before the action executes.
    If any ERROR-severity criterion fails, the action is blocked.
    """

    api_name: str = Field(
        ...,
        description="Unique identifier for this criterion.",
        alias="apiName",
    )

    display_name: str | None = Field(
        default=None,
        description="Human-readable criterion name.",
        alias="displayName",
    )

    description: str | None = Field(
        default=None,
        description="Explanation of what this criterion checks.",
    )

    criterion_type: SubmissionCriterionType = Field(
        ...,
        description="Type of criterion.",
        alias="criterionType",
    )

    expression: str | None = Field(
        default=None,
        description="Boolean expression that must evaluate to true.",
    )

    error_message: str | None = Field(
        default=None,
        description="Message to display if criterion fails.",
        alias="errorMessage",
    )

    severity: CriterionSeverity = Field(
        default=CriterionSeverity.ERROR,
        description="Severity level (ERROR blocks execution, WARNING allows).",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "apiName": self.api_name,
            "criterionType": self.criterion_type.value,
        }
        if self.display_name:
            result["displayName"] = self.display_name
        if self.description:
            result["description"] = self.description
        if self.expression:
            result["expression"] = self.expression
        if self.error_message:
            result["errorMessage"] = self.error_message
        if self.severity != CriterionSeverity.ERROR:
            result["severity"] = self.severity.value
        return result


# ============================================================================
# Side Effects
# ============================================================================


class NotificationConfig(BaseModel):
    """Configuration for NOTIFICATION side effect."""

    recipients: list[str] = Field(
        default_factory=list,
        description="User IDs or group IDs to notify.",
    )

    recipient_expression: str | None = Field(
        default=None,
        description="Expression to compute recipients dynamically.",
        alias="recipientExpression",
    )

    message_template: str | None = Field(
        default=None,
        description="Notification message template with parameter placeholders.",
        alias="messageTemplate",
    )

    channel: NotificationChannel = Field(
        default=NotificationChannel.IN_APP,
        description="Notification channel.",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )


class WebhookRetryPolicy(BaseModel):
    """Retry policy for webhook side effects."""

    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts.",
        alias="maxRetries",
    )

    retry_delay: int = Field(
        default=1000,
        description="Delay between retries in milliseconds.",
        alias="retryDelay",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )


class WebhookConfig(BaseModel):
    """Configuration for WEBHOOK side effect."""

    url: str = Field(
        ...,
        description="Webhook endpoint URL.",
    )

    method: str = Field(
        default="POST",
        description="HTTP method.",
    )

    headers: dict[str, str] = Field(
        default_factory=dict,
        description="HTTP headers.",
    )

    payload_template: str | None = Field(
        default=None,
        description="JSON template for request body.",
        alias="payloadTemplate",
    )

    retry_policy: WebhookRetryPolicy | None = Field(
        default=None,
        description="Retry configuration.",
        alias="retryPolicy",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )


class TriggerActionConfig(BaseModel):
    """Configuration for TRIGGER_ACTION side effect."""

    action_api_name: str = Field(
        ...,
        description="apiName of action to trigger.",
        alias="actionApiName",
    )

    parameter_mappings: dict[str, str] = Field(
        default_factory=dict,
        description="Map current action parameters to triggered action parameters.",
        alias="parameterMappings",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )


class SideEffectConfig(BaseModel):
    """Configuration for side effect execution."""

    notification_config: NotificationConfig | None = Field(
        default=None,
        description="For NOTIFICATION type.",
        alias="notificationConfig",
    )

    webhook_config: WebhookConfig | None = Field(
        default=None,
        description="For WEBHOOK type.",
        alias="webhookConfig",
    )

    trigger_action_config: TriggerActionConfig | None = Field(
        default=None,
        description="For TRIGGER_ACTION type.",
        alias="triggerActionConfig",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {}
        if self.notification_config:
            nc = self.notification_config
            result["notificationConfig"] = {
                "recipients": nc.recipients,
                "channel": nc.channel.value,
            }
            if nc.recipient_expression:
                result["notificationConfig"]["recipientExpression"] = nc.recipient_expression
            if nc.message_template:
                result["notificationConfig"]["messageTemplate"] = nc.message_template
        if self.webhook_config:
            wc = self.webhook_config
            result["webhookConfig"] = {
                "url": wc.url,
                "method": wc.method,
            }
            if wc.headers:
                result["webhookConfig"]["headers"] = wc.headers
            if wc.payload_template:
                result["webhookConfig"]["payloadTemplate"] = wc.payload_template
            if wc.retry_policy:
                result["webhookConfig"]["retryPolicy"] = {
                    "maxRetries": wc.retry_policy.max_retries,
                    "retryDelay": wc.retry_policy.retry_delay,
                }
        if self.trigger_action_config:
            tc = self.trigger_action_config
            result["triggerActionConfig"] = {
                "actionApiName": tc.action_api_name,
                "parameterMappings": tc.parameter_mappings,
            }
        return result


class SideEffect(BaseModel):
    """
    Post-execution effect that occurs after successful action completion.
    """

    api_name: str = Field(
        ...,
        description="Unique identifier for this side effect.",
        alias="apiName",
    )

    effect_type: SideEffectType = Field(
        ...,
        description="Type of side effect.",
        alias="effectType",
    )

    configuration: SideEffectConfig = Field(
        ...,
        description="Configuration specific to the effect type.",
    )

    conditional: EditCondition | None = Field(
        default=None,
        description="Condition for when this side effect should trigger.",
    )

    async_execution: bool = Field(
        default=True,
        description="If true, side effect runs asynchronously.",
        alias="async",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "apiName": self.api_name,
            "effectType": self.effect_type.value,
            "configuration": self.configuration.to_foundry_dict(),
        }
        if self.conditional:
            result["conditional"] = self.conditional.to_foundry_dict()
        result["async"] = self.async_execution
        return result


# ============================================================================
# Implementation, Permissions, Audit, Undo
# ============================================================================


class FunctionConfig(BaseModel):
    """Configuration for function-backed actions."""

    timeout: int = Field(
        default=30000,
        description="Timeout in milliseconds.",
    )

    retries: int = Field(
        default=0,
        description="Number of retry attempts.",
    )

    model_config = ConfigDict(extra="forbid")


class ActionImplementation(BaseModel):
    """
    How the action logic is implemented.

    Implementation types:
    - DECLARATIVE: Uses EditSpecifications to define changes
    - FUNCTION_BACKED: Calls a function (TypeScript or Python)
    - INLINE_EDIT: Simple property edits without logic
    """

    type: ActionImplementationType = Field(
        ...,
        description="Implementation type.",
    )

    function_ref: str | None = Field(
        default=None,
        description="For FUNCTION_BACKED, reference to the implementing function.",
        alias="functionRef",
    )

    function_language: FunctionLanguage | None = Field(
        default=None,
        description="For FUNCTION_BACKED, the implementation language.",
        alias="functionLanguage",
    )

    function_config: FunctionConfig | None = Field(
        default=None,
        description="Additional function configuration.",
        alias="functionConfig",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_function_config(self) -> ActionImplementation:
        """Validate function config for FUNCTION_BACKED type."""
        if self.type == ActionImplementationType.FUNCTION_BACKED:
            if not self.function_ref:
                raise ValueError("FUNCTION_BACKED requires function_ref")
        return self

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {"type": self.type.value}
        if self.function_ref:
            result["functionRef"] = self.function_ref
        if self.function_language:
            result["functionLanguage"] = self.function_language.value
        if self.function_config:
            result["functionConfig"] = {
                "timeout": self.function_config.timeout,
                "retries": self.function_config.retries,
            }
        return result


class ObjectTypePermission(BaseModel):
    """Required permission on an ObjectType."""

    object_type_api_name: str = Field(
        ...,
        description="apiName of the ObjectType.",
        alias="objectTypeApiName",
    )

    required_access: ObjectAccessLevel = Field(
        ...,
        description="Required access level.",
        alias="requiredAccess",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )


class ActionPermissions(BaseModel):
    """
    Permission requirements for action execution.
    """

    required_roles: list[str] = Field(
        default_factory=list,
        description="Roles that can execute this action.",
        alias="requiredRoles",
    )

    required_permissions: list[str] = Field(
        default_factory=list,
        description="Specific permissions required.",
        alias="requiredPermissions",
    )

    object_type_permissions: list[ObjectTypePermission] = Field(
        default_factory=list,
        description="Required permissions on affected ObjectTypes.",
        alias="objectTypePermissions",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {}
        if self.required_roles:
            result["requiredRoles"] = self.required_roles
        if self.required_permissions:
            result["requiredPermissions"] = self.required_permissions
        if self.object_type_permissions:
            result["objectTypePermissions"] = [
                {
                    "objectTypeApiName": p.object_type_api_name,
                    "requiredAccess": p.required_access.value,
                }
                for p in self.object_type_permissions
            ]
        return result


class AuditConfig(BaseModel):
    """
    Configuration for action execution audit trail.
    """

    enabled: bool = Field(
        default=True,
        description="If true, all executions are logged.",
    )

    log_level: AuditLogLevel = Field(
        default=AuditLogLevel.STANDARD,
        description="Detail level for audit logs.",
        alias="logLevel",
    )

    include_parameters: bool = Field(
        default=True,
        description="If true, parameter values are logged.",
        alias="includeParameters",
    )

    include_before_after: bool = Field(
        default=True,
        description="If true, before/after state snapshots are logged.",
        alias="includeBeforeAfter",
    )

    sensitive_parameters: list[str] = Field(
        default_factory=list,
        description="Parameter apiNames to mask in logs.",
        alias="sensitiveParameters",
    )

    retention_days: int = Field(
        default=365,
        description="Days to retain audit logs.",
        ge=1,
        alias="retentionDays",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "enabled": self.enabled,
            "logLevel": self.log_level.value,
            "includeParameters": self.include_parameters,
            "includeBeforeAfter": self.include_before_after,
            "retentionDays": self.retention_days,
        }
        if self.sensitive_parameters:
            result["sensitiveParameters"] = self.sensitive_parameters
        return result


class UndoConfig(BaseModel):
    """
    Configuration for undo/revert capability.
    """

    undoable: bool = Field(
        default=False,
        description="If true, action can be undone/reverted.",
    )

    undo_window_minutes: int = Field(
        default=60,
        description="Time window in minutes during which undo is allowed.",
        ge=0,
        alias="undoWindowMinutes",
    )

    undo_strategy: UndoStrategy = Field(
        default=UndoStrategy.RESTORE_SNAPSHOT,
        description="How undo is performed.",
        alias="undoStrategy",
    )

    inverse_action_ref: str | None = Field(
        default=None,
        description="For INVERSE_ACTION, the action to execute for undo.",
        alias="inverseActionRef",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_inverse_action(self) -> UndoConfig:
        """Validate inverse action ref for INVERSE_ACTION strategy."""
        if self.undo_strategy == UndoStrategy.INVERSE_ACTION and not self.inverse_action_ref:
            raise ValueError(
                "INVERSE_ACTION undo strategy requires inverse_action_ref"
            )
        return self

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "undoable": self.undoable,
            "undoWindowMinutes": self.undo_window_minutes,
            "undoStrategy": self.undo_strategy.value,
        }
        if self.inverse_action_ref:
            result["inverseActionRef"] = self.inverse_action_ref
        return result


# ============================================================================
# ActionType Main Class
# ============================================================================


class ActionType(OntologyEntity):
    """
    ActionType schema definition - operations users can perform on the ontology.

    An ActionType defines a set of changes to objects, property values, and links
    that a user can execute at once. It specifies:
    - Required input parameters
    - Affected ObjectTypes
    - Edit specifications (what changes occur)
    - Submission criteria (preconditions)
    - Side effects (post-execution effects)

    IMPORTANT: ActionType does NOT support 'endorsed' status.
    Only ObjectTypes can be endorsed.

    Example:
        >>> modify_file = ActionType(
        ...     api_name="file.modify",
        ...     display_name="Modify File",
        ...     hazardous=True,
        ...     parameters=[
        ...         ActionParameter(
        ...             api_name="filePath",
        ...             display_name="File Path",
        ...             data_type=ParameterDataType(type=ParameterType.STRING),
        ...             required=True,
        ...         ),
        ...     ],
        ...     affected_object_types=[
        ...         AffectedObjectType(
        ...             object_type_api_name="File",
        ...             operations=[ObjectOperation.MODIFY],
        ...         ),
        ...     ],
        ...     implementation=ActionImplementation(
        ...         type=ActionImplementationType.FUNCTION_BACKED,
        ...         function_ref="lib.oda.actions.file.modify_file",
        ...         function_language=FunctionLanguage.PYTHON,
        ...     ),
        ... )
    """

    # Override RID to use action-type specific format
    rid: str = Field(
        default_factory=lambda: generate_rid("ontology", "action-type"),
        description="Resource ID - globally unique identifier for this ActionType.",
        pattern=r"^ri\.ontology\.[a-z]+\.action-type\.[a-zA-Z0-9-]+$",
        json_schema_extra={"readOnly": True, "immutable": True},
    )

    # Override api_name to allow dots (for namespace.action format)
    api_name: str = Field(
        ...,
        description="Unique identifier. Supports dot notation for namespacing (e.g., file.modify).",
        min_length=1,
        max_length=255,
        pattern=r"^[a-zA-Z][a-zA-Z0-9_.]*$",
        alias="apiName",
    )

    # Category (optional, for organization)
    category: str | None = Field(
        default=None,
        description="Action category for organization and filtering.",
    )

    # Hazardous flag (triggers Proposal workflow)
    hazardous: bool = Field(
        default=False,
        description="If true, this action requires Proposal approval workflow before execution.",
    )

    # Parameters
    parameters: list[ActionParameter] = Field(
        default_factory=list,
        description="User inputs required for this action.",
    )

    # Affected ObjectTypes (REQUIRED)
    affected_object_types: list[AffectedObjectType] = Field(
        ...,
        description="ObjectTypes that this action can create, modify, or delete.",
        min_length=1,
        alias="affectedObjectTypes",
    )

    # Edit Specifications
    edit_specifications: list[EditSpecification] = Field(
        default_factory=list,
        description="Declarative edit operations (rules) that define what changes occur.",
        alias="editSpecifications",
    )

    # Submission Criteria
    submission_criteria: list[SubmissionCriterion] = Field(
        default_factory=list,
        description="Boolean conditions that must be true to submit/execute this action.",
        alias="submissionCriteria",
    )

    # Side Effects
    side_effects: list[SideEffect] = Field(
        default_factory=list,
        description="Post-execution effects (notifications, webhooks, etc.).",
        alias="sideEffects",
    )

    # Implementation (REQUIRED)
    implementation: ActionImplementation = Field(
        ...,
        description="How the action is implemented (declarative rules or function-backed).",
    )

    # Permissions
    permissions: ActionPermissions | None = Field(
        default=None,
        description="Permission requirements to execute this action.",
    )

    # Lifecycle Status
    status: ActionTypeStatus = Field(
        default=ActionTypeStatus.EXPERIMENTAL,
        description="Lifecycle status of the ActionType. Note: ENDORSED is NOT supported.",
    )

    # Audit Configuration
    audit_config: AuditConfig | None = Field(
        default=None,
        description="Configuration for action logging and tracking.",
        alias="auditConfig",
    )

    # Undo Configuration
    undo_config: UndoConfig | None = Field(
        default=None,
        description="Configuration for undo/revert capability.",
        alias="undoConfig",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        use_enum_values=False,
        json_schema_extra={
            "x-palantir-entity-type": "action-type",
            "x-palantir-indexing": ["api_name", "rid", "status", "category", "hazardous"],
            "x-palantir-no-endorsed": True,  # ActionType cannot be endorsed
        },
    )

    @model_validator(mode="after")
    def validate_unique_parameter_names(self) -> ActionType:
        """Validate that all parameter apiNames are unique."""
        names = [p.api_name for p in self.parameters]
        duplicates = [n for n in names if names.count(n) > 1]
        if duplicates:
            raise ValueError(f"Duplicate parameter apiNames found: {set(duplicates)}")
        return self

    @model_validator(mode="after")
    def validate_declarative_has_edit_specs(self) -> ActionType:
        """Validate that DECLARATIVE implementation has edit specifications."""
        if self.implementation.type == ActionImplementationType.DECLARATIVE:
            if not self.edit_specifications:
                raise ValueError(
                    "DECLARATIVE implementation requires at least one edit_specification"
                )
        return self

    def get_parameter(self, api_name: str) -> ActionParameter | None:
        """Get a parameter by its apiName."""
        for param in self.parameters:
            if param.api_name == api_name:
                return param
        return None

    def get_required_parameters(self) -> list[ActionParameter]:
        """Get all required parameters."""
        return [p for p in self.parameters if p.required]

    def affects_object_type(self, object_type_api_name: str) -> bool:
        """Check if this action affects a given ObjectType."""
        return any(
            aot.object_type_api_name == object_type_api_name
            for aot in self.affected_object_types
        )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Palantir Foundry-compatible dictionary format."""
        result = super().to_foundry_dict()

        if self.category:
            result["category"] = self.category
        result["hazardous"] = self.hazardous

        if self.parameters:
            result["parameters"] = [p.to_foundry_dict() for p in self.parameters]

        result["affectedObjectTypes"] = [
            aot.to_foundry_dict() for aot in self.affected_object_types
        ]

        if self.edit_specifications:
            result["editSpecifications"] = [
                es.to_foundry_dict() for es in self.edit_specifications
            ]

        if self.submission_criteria:
            result["submissionCriteria"] = [
                sc.to_foundry_dict() for sc in self.submission_criteria
            ]

        if self.side_effects:
            result["sideEffects"] = [se.to_foundry_dict() for se in self.side_effects]

        result["implementation"] = self.implementation.to_foundry_dict()

        if self.permissions:
            result["permissions"] = self.permissions.to_foundry_dict()

        result["status"] = self.status.value

        if self.audit_config:
            result["auditConfig"] = self.audit_config.to_foundry_dict()

        if self.undo_config:
            result["undoConfig"] = self.undo_config.to_foundry_dict()

        return result


# Update forward references
ParameterDataType.model_rebuild()
