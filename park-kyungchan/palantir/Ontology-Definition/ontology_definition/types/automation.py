"""
Automation Type Definition for Ontology.

Automate is an application for setting up business automation. The Automate
application allows users to define conditions and effects. Conditions are
checked continuously, and effects are executed automatically when the
specified conditions were met.

Aligned with Ontology.md Section 8 - Automation specification.

Key components:
    - AutomationCondition: TIME or OBJECT_SET based triggers
    - AutomationEffect: ACTION, NOTIFICATION, FALLBACK effects
    - RetryPolicy: CONSTANT or EXPONENTIAL retry strategies
    - Automation: Main automation definition model

Example:
    # Time-based automation (daily at 9 AM)
    daily_report = Automation(
        api_name="dailySalesReport",
        display_name="Daily Sales Report",
        condition=AutomationCondition(
            condition_type=AutomationConditionType.TIME,
            time_condition=TimeCondition(
                mode=TimeConditionMode.DAILY,
                cron="0 9 * * *",
                timezone="America/New_York",
            ),
        ),
        effects=[
            AutomationEffect(
                effect_type=AutomationEffectType.ACTION,
                action_effect=ActionEffect(
                    action_type_ref="generateSalesReport",
                ),
            ),
        ],
    )
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ontology_definition.core.enums import (
    ActionExecutionMode,
    AutomationConditionType,
    AutomationEffectType,
    AutomationStatus,
    EvaluationLatency,
    NotificationEffectType,
    ObjectSetConditionTrigger,
    RetryPolicyType,
    TimeConditionMode,
)


class RetryPolicy(BaseModel):
    """
    Retry policy for automation effect execution.

    Defines how to handle failures:
    - CONSTANT: Fixed delay between retries
    - EXPONENTIAL: Exponentially increasing delay (backoff)

    Example:
        # Exponential backoff: 1s, 2s, 4s, 8s...
        RetryPolicy(
            policy_type=RetryPolicyType.EXPONENTIAL,
            max_retries=5,
            initial_delay_ms=1000,
            max_delay_ms=60000,
        )
    """

    policy_type: RetryPolicyType = Field(
        default=RetryPolicyType.CONSTANT,
        description="Retry strategy type.",
        alias="type",
    )

    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts.",
        ge=0,
        le=10,
        alias="maxRetries",
    )

    initial_delay_ms: int = Field(
        default=1000,
        description="Initial delay between retries in milliseconds.",
        ge=100,
        alias="initialDelayMs",
    )

    max_delay_ms: Optional[int] = Field(
        default=None,
        description="Maximum delay for exponential backoff (ms).",
        ge=100,
        alias="maxDelayMs",
    )

    multiplier: float = Field(
        default=2.0,
        description="Multiplier for exponential backoff.",
        ge=1.0,
        le=10.0,
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_exponential_config(self) -> "RetryPolicy":
        """Validate exponential backoff configuration."""
        if self.policy_type == RetryPolicyType.EXPONENTIAL:
            if self.max_delay_ms is None:
                # Set default max delay for exponential backoff
                self.max_delay_ms = 60000  # 1 minute
        return self

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "type": self.policy_type.value,
            "maxRetries": self.max_retries,
            "initialDelayMs": self.initial_delay_ms,
        }

        if self.policy_type == RetryPolicyType.EXPONENTIAL:
            result["multiplier"] = self.multiplier
            if self.max_delay_ms:
                result["maxDelayMs"] = self.max_delay_ms

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "RetryPolicy":
        """Create from Foundry JSON format."""
        return cls(
            policy_type=RetryPolicyType(data["type"]),
            max_retries=data.get("maxRetries", 3),
            initial_delay_ms=data.get("initialDelayMs", 1000),
            max_delay_ms=data.get("maxDelayMs"),
            multiplier=data.get("multiplier", 2.0),
        )


class TimeCondition(BaseModel):
    """
    Time-based automation condition.

    Supports various schedule modes:
    - HOURLY: Run every hour at specified minute
    - DAILY: Run daily at specified time
    - WEEKLY: Run weekly on specified days
    - MONTHLY: Run monthly on specified days
    - CRON: Custom schedule using 5-field cron expression

    Example:
        # Daily at 9 AM EST
        TimeCondition(
            mode=TimeConditionMode.DAILY,
            cron="0 9 * * *",
            timezone="America/New_York",
        )

        # Every Monday and Friday at 6 PM
        TimeCondition(
            mode=TimeConditionMode.WEEKLY,
            cron="0 18 * * 1,5",
            timezone="UTC",
        )
    """

    mode: TimeConditionMode = Field(
        ...,
        description="Schedule mode (HOURLY, DAILY, WEEKLY, MONTHLY, CRON).",
    )

    cron: str = Field(
        ...,
        description="5-field cron expression (minute hour day month weekday).",
        min_length=9,
        max_length=100,
    )

    timezone: str = Field(
        default="UTC",
        description="IANA timezone identifier (e.g., 'America/New_York').",
        min_length=1,
        max_length=50,
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @field_validator("cron")
    @classmethod
    def validate_cron_format(cls, v: str) -> str:
        """Basic validation of cron expression format."""
        parts = v.split()
        if len(parts) != 5:
            raise ValueError(
                f"Cron expression must have 5 fields (minute hour day month weekday), "
                f"got {len(parts)} fields"
            )
        return v

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        return {
            "mode": self.mode.value,
            "cron": self.cron,
            "timezone": self.timezone,
        }

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "TimeCondition":
        """Create from Foundry JSON format."""
        return cls(
            mode=TimeConditionMode(data["mode"]),
            cron=data["cron"],
            timezone=data.get("timezone", "UTC"),
        )


class ObjectSetCondition(BaseModel):
    """
    Object set-based automation condition.

    Triggers automation based on data changes:
    - OBJECTS_ADDED: New objects matching the set criteria
    - OBJECTS_REMOVED: Objects removed from the set
    - OBJECTS_MODIFIED: Existing objects in the set were updated
    - METRIC_CHANGED: Aggregated metric value changed
    - THRESHOLD_CROSSED: Metric crossed a defined threshold
    - OBJECTS_EXIST: Objects matching criteria exist (batch processing)

    Example:
        # Trigger when new high-priority tickets are created
        ObjectSetCondition(
            trigger=ObjectSetConditionTrigger.OBJECTS_ADDED,
            object_set_ref="highPriorityTickets",
            filter_expression="priority = 'HIGH' AND status = 'NEW'",
        )
    """

    trigger: ObjectSetConditionTrigger = Field(
        ...,
        description="What data change should trigger the automation.",
    )

    object_set_ref: Optional[str] = Field(
        default=None,
        description="Reference to a saved ObjectSet definition.",
        alias="objectSetRef",
    )

    object_type_ref: Optional[str] = Field(
        default=None,
        description="ObjectType apiName to watch.",
        alias="objectTypeRef",
    )

    filter_expression: Optional[str] = Field(
        default=None,
        description="Filter expression to narrow down objects.",
        alias="filterExpression",
    )

    function_ref: Optional[str] = Field(
        default=None,
        description="Reference to a function that returns the ObjectSet.",
        alias="functionRef",
    )

    # For THRESHOLD_CROSSED trigger
    threshold_metric: Optional[str] = Field(
        default=None,
        description="Metric to monitor for threshold crossing.",
        alias="thresholdMetric",
    )

    threshold_value: Optional[float] = Field(
        default=None,
        description="Threshold value to trigger on.",
        alias="thresholdValue",
    )

    threshold_operator: Optional[str] = Field(
        default=None,
        description="Comparison operator (GT, GTE, LT, LTE, EQ).",
        alias="thresholdOperator",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_object_source(self) -> "ObjectSetCondition":
        """Validate that at least one object source is specified."""
        if not any([self.object_set_ref, self.object_type_ref, self.function_ref]):
            raise ValueError(
                "Must specify at least one of: object_set_ref, object_type_ref, or function_ref"
            )
        return self

    @model_validator(mode="after")
    def validate_threshold_config(self) -> "ObjectSetCondition":
        """Validate threshold configuration for THRESHOLD_CROSSED trigger."""
        if self.trigger == ObjectSetConditionTrigger.THRESHOLD_CROSSED:
            if not all([self.threshold_metric, self.threshold_value is not None, self.threshold_operator]):
                raise ValueError(
                    "THRESHOLD_CROSSED trigger requires threshold_metric, threshold_value, and threshold_operator"
                )
        return self

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {"trigger": self.trigger.value}

        if self.object_set_ref:
            result["objectSetRef"] = self.object_set_ref

        if self.object_type_ref:
            result["objectTypeRef"] = self.object_type_ref

        if self.filter_expression:
            result["filterExpression"] = self.filter_expression

        if self.function_ref:
            result["functionRef"] = self.function_ref

        if self.threshold_metric:
            result["thresholdMetric"] = self.threshold_metric

        if self.threshold_value is not None:
            result["thresholdValue"] = self.threshold_value

        if self.threshold_operator:
            result["thresholdOperator"] = self.threshold_operator

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "ObjectSetCondition":
        """Create from Foundry JSON format."""
        return cls(
            trigger=ObjectSetConditionTrigger(data["trigger"]),
            object_set_ref=data.get("objectSetRef"),
            object_type_ref=data.get("objectTypeRef"),
            filter_expression=data.get("filterExpression"),
            function_ref=data.get("functionRef"),
            threshold_metric=data.get("thresholdMetric"),
            threshold_value=data.get("thresholdValue"),
            threshold_operator=data.get("thresholdOperator"),
        )


class AutomationCondition(BaseModel):
    """
    Automation trigger condition.

    Supports two types:
    - TIME: Schedule-based triggers
    - OBJECT_SET: Data-driven triggers

    Example:
        # Time-based condition
        AutomationCondition(
            condition_type=AutomationConditionType.TIME,
            time_condition=TimeCondition(
                mode=TimeConditionMode.CRON,
                cron="0 9 * * 1-5",  # 9 AM on weekdays
                timezone="America/New_York",
            ),
        )

        # Object set-based condition
        AutomationCondition(
            condition_type=AutomationConditionType.OBJECT_SET,
            objectset_condition=ObjectSetCondition(
                trigger=ObjectSetConditionTrigger.OBJECTS_ADDED,
                object_type_ref="Ticket",
                filter_expression="priority = 'CRITICAL'",
            ),
        )
    """

    condition_type: AutomationConditionType = Field(
        ...,
        description="Type of condition (TIME or OBJECT_SET).",
        alias="type",
    )

    time_condition: Optional[TimeCondition] = Field(
        default=None,
        description="For TIME type, the schedule configuration.",
        alias="timeCondition",
    )

    objectset_condition: Optional[ObjectSetCondition] = Field(
        default=None,
        description="For OBJECT_SET type, the data trigger configuration.",
        alias="objectsetCondition",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_condition_config(self) -> "AutomationCondition":
        """Validate that appropriate condition is specified for the type."""
        if self.condition_type == AutomationConditionType.TIME:
            if not self.time_condition:
                raise ValueError("TIME condition type requires time_condition")
        elif self.condition_type == AutomationConditionType.OBJECT_SET:
            if not self.objectset_condition:
                raise ValueError("OBJECT_SET condition type requires objectset_condition")
        return self

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {"type": self.condition_type.value}

        if self.time_condition:
            result["timeCondition"] = self.time_condition.to_foundry_dict()

        if self.objectset_condition:
            result["objectsetCondition"] = self.objectset_condition.to_foundry_dict()

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "AutomationCondition":
        """Create from Foundry JSON format."""
        time_condition = None
        if data.get("timeCondition"):
            time_condition = TimeCondition.from_foundry_dict(data["timeCondition"])

        objectset_condition = None
        if data.get("objectsetCondition"):
            objectset_condition = ObjectSetCondition.from_foundry_dict(data["objectsetCondition"])

        return cls(
            condition_type=AutomationConditionType(data["type"]),
            time_condition=time_condition,
            objectset_condition=objectset_condition,
        )


class ActionEffect(BaseModel):
    """
    ACTION type automation effect.

    Executes an ActionType when the automation triggers.

    Example:
        ActionEffect(
            action_type_ref="sendNotificationEmail",
            parameter_mapping={"recipient": "owner", "subject": "Alert"},
            execution_mode=ActionExecutionMode.ONCE_EACH_GROUP,
            retry_policy=RetryPolicy(max_retries=3),
        )
    """

    action_type_ref: str = Field(
        ...,
        description="apiName of the ActionType to execute.",
        alias="actionTypeRef",
    )

    parameter_mapping: dict[str, Any] = Field(
        default_factory=dict,
        description="Map from action parameters to condition output values.",
        alias="parameterMapping",
    )

    execution_mode: ActionExecutionMode = Field(
        default=ActionExecutionMode.ONCE_ALL,
        description="How to batch action execution.",
        alias="executionMode",
    )

    retry_policy: Optional[RetryPolicy] = Field(
        default=None,
        description="Retry policy for failed executions.",
        alias="retryPolicy",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "actionTypeRef": self.action_type_ref,
            "executionMode": self.execution_mode.value,
        }

        if self.parameter_mapping:
            result["parameterMapping"] = self.parameter_mapping

        if self.retry_policy:
            result["retryPolicy"] = self.retry_policy.to_foundry_dict()

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "ActionEffect":
        """Create from Foundry JSON format."""
        retry_policy = None
        if data.get("retryPolicy"):
            retry_policy = RetryPolicy.from_foundry_dict(data["retryPolicy"])

        return cls(
            action_type_ref=data["actionTypeRef"],
            parameter_mapping=data.get("parameterMapping", {}),
            execution_mode=ActionExecutionMode(data.get("executionMode", "ONCE_ALL")),
            retry_policy=retry_policy,
        )


class NotificationEffect(BaseModel):
    """
    NOTIFICATION type automation effect.

    Sends notifications when the automation triggers.

    Example:
        NotificationEffect(
            notification_type=NotificationEffectType.EMAIL,
            recipients=["team@example.com"],
            subject_template="Alert: {{alert.title}}",
            body_template="A critical issue was detected...",
        )
    """

    notification_type: NotificationEffectType = Field(
        default=NotificationEffectType.PLATFORM,
        description="Notification delivery type (PLATFORM or EMAIL).",
        alias="type",
    )

    recipients: list[str] = Field(
        default_factory=list,
        description="List of recipient user IDs or email addresses.",
    )

    recipient_expression: Optional[str] = Field(
        default=None,
        description="Expression to compute recipients dynamically.",
        alias="recipientExpression",
    )

    subject_template: Optional[str] = Field(
        default=None,
        description="Subject line template (for EMAIL type).",
        alias="subjectTemplate",
    )

    body_template: Optional[str] = Field(
        default=None,
        description="Notification body template with placeholders.",
        alias="bodyTemplate",
    )

    attachment_refs: list[str] = Field(
        default_factory=list,
        description="References to Notepad documents to attach.",
        alias="attachmentRefs",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_recipients(self) -> "NotificationEffect":
        """Validate that recipients are specified."""
        if not self.recipients and not self.recipient_expression:
            raise ValueError("Must specify recipients or recipient_expression")
        return self

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {"type": self.notification_type.value}

        if self.recipients:
            result["recipients"] = self.recipients

        if self.recipient_expression:
            result["recipientExpression"] = self.recipient_expression

        if self.subject_template:
            result["subjectTemplate"] = self.subject_template

        if self.body_template:
            result["bodyTemplate"] = self.body_template

        if self.attachment_refs:
            result["attachmentRefs"] = self.attachment_refs

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "NotificationEffect":
        """Create from Foundry JSON format."""
        return cls(
            notification_type=NotificationEffectType(data.get("type", "PLATFORM")),
            recipients=data.get("recipients", []),
            recipient_expression=data.get("recipientExpression"),
            subject_template=data.get("subjectTemplate"),
            body_template=data.get("bodyTemplate"),
            attachment_refs=data.get("attachmentRefs", []),
        )


class FallbackEffect(BaseModel):
    """
    FALLBACK type automation effect.

    Executed when primary effects fail.

    Example:
        FallbackEffect(
            action_effects=[
                ActionEffect(action_type_ref="logFailure"),
                ActionEffect(action_type_ref="notifyAdmin"),
            ],
        )
    """

    action_effects: list[ActionEffect] = Field(
        default_factory=list,
        description="List of action effects to execute as fallback.",
        alias="actionEffects",
    )

    notification_effects: list[NotificationEffect] = Field(
        default_factory=list,
        description="List of notification effects to execute as fallback.",
        alias="notificationEffects",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_has_effects(self) -> "FallbackEffect":
        """Validate that at least one fallback effect is specified."""
        if not self.action_effects and not self.notification_effects:
            raise ValueError("Fallback must have at least one action or notification effect")
        return self

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {}

        if self.action_effects:
            result["actionEffects"] = [e.to_foundry_dict() for e in self.action_effects]

        if self.notification_effects:
            result["notificationEffects"] = [e.to_foundry_dict() for e in self.notification_effects]

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "FallbackEffect":
        """Create from Foundry JSON format."""
        action_effects = [
            ActionEffect.from_foundry_dict(e) for e in data.get("actionEffects", [])
        ]
        notification_effects = [
            NotificationEffect.from_foundry_dict(e) for e in data.get("notificationEffects", [])
        ]
        return cls(
            action_effects=action_effects,
            notification_effects=notification_effects,
        )


class AutomationEffect(BaseModel):
    """
    Automation effect definition.

    Wraps the specific effect type (ACTION, NOTIFICATION, FALLBACK).

    Example:
        # Action effect
        AutomationEffect(
            effect_type=AutomationEffectType.ACTION,
            action_effect=ActionEffect(action_type_ref="processTicket"),
        )

        # Notification effect
        AutomationEffect(
            effect_type=AutomationEffectType.NOTIFICATION,
            notification_effect=NotificationEffect(
                notification_type=NotificationEffectType.EMAIL,
                recipients=["admin@example.com"],
            ),
        )
    """

    effect_type: AutomationEffectType = Field(
        ...,
        description="Type of effect (ACTION, NOTIFICATION, FALLBACK).",
        alias="type",
    )

    action_effect: Optional[ActionEffect] = Field(
        default=None,
        description="For ACTION type, the action configuration.",
        alias="actionEffect",
    )

    notification_effect: Optional[NotificationEffect] = Field(
        default=None,
        description="For NOTIFICATION type, the notification configuration.",
        alias="notificationEffect",
    )

    fallback_effect: Optional[FallbackEffect] = Field(
        default=None,
        description="For FALLBACK type, the fallback configuration.",
        alias="fallbackEffect",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_effect_config(self) -> "AutomationEffect":
        """Validate that appropriate effect is specified for the type."""
        if self.effect_type == AutomationEffectType.ACTION:
            if not self.action_effect:
                raise ValueError("ACTION effect type requires action_effect")
        elif self.effect_type == AutomationEffectType.NOTIFICATION:
            if not self.notification_effect:
                raise ValueError("NOTIFICATION effect type requires notification_effect")
        elif self.effect_type == AutomationEffectType.FALLBACK:
            if not self.fallback_effect:
                raise ValueError("FALLBACK effect type requires fallback_effect")
        return self

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {"type": self.effect_type.value}

        if self.action_effect:
            result["actionEffect"] = self.action_effect.to_foundry_dict()

        if self.notification_effect:
            result["notificationEffect"] = self.notification_effect.to_foundry_dict()

        if self.fallback_effect:
            result["fallbackEffect"] = self.fallback_effect.to_foundry_dict()

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "AutomationEffect":
        """Create from Foundry JSON format."""
        action_effect = None
        if data.get("actionEffect"):
            action_effect = ActionEffect.from_foundry_dict(data["actionEffect"])

        notification_effect = None
        if data.get("notificationEffect"):
            notification_effect = NotificationEffect.from_foundry_dict(data["notificationEffect"])

        fallback_effect = None
        if data.get("fallbackEffect"):
            fallback_effect = FallbackEffect.from_foundry_dict(data["fallbackEffect"])

        return cls(
            effect_type=AutomationEffectType(data["type"]),
            action_effect=action_effect,
            notification_effect=notification_effect,
            fallback_effect=fallback_effect,
        )


class ExecutionSettings(BaseModel):
    """
    Execution settings for automation.

    Controls batching, parallelism, and evaluation mode.

    Example:
        ExecutionSettings(
            batch_size=100,
            parallelism=4,
            evaluation_latency=EvaluationLatency.LIVE,
        )
    """

    batch_size: int = Field(
        default=100,
        description="Number of objects to process per batch.",
        ge=1,
        le=10000,
        alias="batchSize",
    )

    parallelism: int = Field(
        default=1,
        description="Number of parallel execution threads.",
        ge=1,
        le=16,
    )

    evaluation_latency: EvaluationLatency = Field(
        default=EvaluationLatency.LIVE,
        description="How quickly conditions are evaluated.",
        alias="evaluationLatency",
    )

    timeout_ms: int = Field(
        default=300000,
        description="Maximum execution time in milliseconds (5 min default).",
        ge=1000,
        alias="timeoutMs",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        return {
            "batchSize": self.batch_size,
            "parallelism": self.parallelism,
            "evaluationLatency": self.evaluation_latency.value,
            "timeoutMs": self.timeout_ms,
        }

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "ExecutionSettings":
        """Create from Foundry JSON format."""
        return cls(
            batch_size=data.get("batchSize", 100),
            parallelism=data.get("parallelism", 1),
            evaluation_latency=EvaluationLatency(data.get("evaluationLatency", "LIVE")),
            timeout_ms=data.get("timeoutMs", 300000),
        )


class Automation(BaseModel):
    """
    Automation definition - business automation with conditions and effects.

    Automate allows users to define conditions and effects. Conditions are
    checked continuously, and effects are executed automatically when the
    specified conditions are met.

    Example:
        # Time-based automation
        daily_report = Automation(
            api_name="dailySalesReport",
            display_name="Daily Sales Report",
            description="Generate sales report every morning",
            enabled=True,
            condition=AutomationCondition(
                condition_type=AutomationConditionType.TIME,
                time_condition=TimeCondition(
                    mode=TimeConditionMode.DAILY,
                    cron="0 9 * * *",
                    timezone="America/New_York",
                ),
            ),
            effects=[
                AutomationEffect(
                    effect_type=AutomationEffectType.ACTION,
                    action_effect=ActionEffect(
                        action_type_ref="generateSalesReport",
                    ),
                ),
            ],
        )

        # Object set-based automation
        ticket_escalation = Automation(
            api_name="criticalTicketEscalation",
            display_name="Critical Ticket Escalation",
            description="Escalate critical tickets immediately",
            enabled=True,
            condition=AutomationCondition(
                condition_type=AutomationConditionType.OBJECT_SET,
                objectset_condition=ObjectSetCondition(
                    trigger=ObjectSetConditionTrigger.OBJECTS_ADDED,
                    object_type_ref="Ticket",
                    filter_expression="priority = 'CRITICAL'",
                ),
            ),
            effects=[
                AutomationEffect(
                    effect_type=AutomationEffectType.ACTION,
                    action_effect=ActionEffect(
                        action_type_ref="escalateTicket",
                        execution_mode=ActionExecutionMode.ONCE_EACH_GROUP,
                    ),
                ),
                AutomationEffect(
                    effect_type=AutomationEffectType.NOTIFICATION,
                    notification_effect=NotificationEffect(
                        notification_type=NotificationEffectType.EMAIL,
                        recipients=["oncall@example.com"],
                        subject_template="Critical Ticket: {{ticket.title}}",
                    ),
                ),
            ],
        )
    """

    # Identity
    api_name: str = Field(
        ...,
        description="Unique identifier for this automation.",
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
        description="Documentation for this automation.",
        max_length=4096,
    )

    # State
    enabled: bool = Field(
        default=True,
        description="If true, the automation is active and will execute.",
    )

    expiry: Optional[datetime] = Field(
        default=None,
        description="Optional expiration timestamp after which automation stops.",
    )

    # Condition
    condition: AutomationCondition = Field(
        ...,
        description="Trigger condition for this automation.",
    )

    # Effects
    effects: list[AutomationEffect] = Field(
        ...,
        description="Effects to execute when condition is met.",
        min_length=1,
    )

    # Execution settings
    execution_settings: ExecutionSettings = Field(
        default_factory=ExecutionSettings,
        description="Execution configuration (batching, parallelism).",
        alias="executionSettings",
    )

    # Status
    status: AutomationStatus = Field(
        default=AutomationStatus.DRAFT,
        description="Lifecycle status of this automation.",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        use_enum_values=False,
    )

    @model_validator(mode="after")
    def validate_fallback_not_first(self) -> "Automation":
        """Validate that FALLBACK effect is not the first effect."""
        if self.effects and self.effects[0].effect_type == AutomationEffectType.FALLBACK:
            raise ValueError("FALLBACK effect cannot be the first effect")
        return self

    def get_action_effects(self) -> list[ActionEffect]:
        """Get all ACTION type effects."""
        return [
            e.action_effect
            for e in self.effects
            if e.effect_type == AutomationEffectType.ACTION and e.action_effect
        ]

    def get_notification_effects(self) -> list[NotificationEffect]:
        """Get all NOTIFICATION type effects."""
        return [
            e.notification_effect
            for e in self.effects
            if e.effect_type == AutomationEffectType.NOTIFICATION and e.notification_effect
        ]

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Palantir Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "apiName": self.api_name,
            "displayName": self.display_name,
            "enabled": self.enabled,
            "condition": self.condition.to_foundry_dict(),
            "effects": [e.to_foundry_dict() for e in self.effects],
            "executionSettings": self.execution_settings.to_foundry_dict(),
            "status": self.status.value,
        }

        if self.description:
            result["description"] = self.description

        if self.expiry:
            result["expiry"] = self.expiry.isoformat()

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "Automation":
        """Create from Foundry JSON format."""
        expiry = None
        if data.get("expiry"):
            expiry = datetime.fromisoformat(data["expiry"])

        execution_settings = ExecutionSettings()
        if data.get("executionSettings"):
            execution_settings = ExecutionSettings.from_foundry_dict(data["executionSettings"])

        return cls(
            api_name=data["apiName"],
            display_name=data["displayName"],
            description=data.get("description"),
            enabled=data.get("enabled", True),
            expiry=expiry,
            condition=AutomationCondition.from_foundry_dict(data["condition"]),
            effects=[AutomationEffect.from_foundry_dict(e) for e in data["effects"]],
            execution_settings=execution_settings,
            status=AutomationStatus(data.get("status", "DRAFT")),
        )
