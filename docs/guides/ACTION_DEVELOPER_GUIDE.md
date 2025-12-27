# Action Developer Guide

## Orion ODA v3.0 - Semantic Action System

> **Version**: 3.0
> **Compliance**: Palantir AIP/Foundry Compatible
> **Last Updated**: 2025-12-27

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Creating ActionType Subclasses](#creating-actiontype-subclasses)
4. [Submission Criteria](#submission-criteria)
5. [Side Effects](#side-effects)
6. [Governance Metadata](#governance-metadata)
7. [Action Registration](#action-registration)
8. [Execution Flow](#execution-flow)
9. [Best Practices](#best-practices)
10. [Complete Examples](#complete-examples)
11. [Troubleshooting](#troubleshooting)

---

## Overview

The Action System is the **ONLY** mechanism for mutating the Ontology in Orion ODA v3.0. This ensures:

- **Validation**: All changes pass through `SubmissionCriteria` before execution
- **Audit Trail**: Every mutation is recorded via `EditOperation` objects
- **Side Effect Decoupling**: Post-commit effects (notifications, webhooks) are isolated
- **Governance**: Hazardous actions require explicit proposal approval

### Design Principles

1. **Declarative Definition**: Actions are defined as classes, not ad-hoc instances
2. **Fail-Fast Validation**: Parameters are validated before any mutation occurs
3. **Post-Commit Side Effects**: External integrations run after successful commits
4. **Full Audit Trail**: Who, what, when, and why for every change

---

## Architecture

```
+------------------+     +--------------------+     +------------------+
|   ActionContext  |---->|    ActionType      |---->|  ActionResult    |
| (actor, time,    |     | (validate, apply)  |     | (success, edits) |
|  correlation_id) |     +--------------------+     +------------------+
+------------------+              |                          |
                                  v                          v
                    +----------------------------+   +------------------+
                    |   SubmissionCriteria       |   |   SideEffects    |
                    | (RequiredField, MaxLength) |   | (Log, Webhook)   |
                    +----------------------------+   +------------------+
```

### Core Components

| Component | File | Purpose |
|-----------|------|---------|
| `ActionType` | `__init__.py` | Abstract base class for all actions |
| `ActionContext` | `__init__.py` | Execution context (actor, timestamp, metadata) |
| `ActionResult` | `__init__.py` | Execution result with success/failure and edits |
| `ActionRegistry` | `__init__.py` | Global registry for action discovery |
| `SubmissionCriterion` | `__init__.py` | Validation protocol and built-in validators |
| `SideEffect` | `side_effects.py` | Post-commit effect protocol and implementations |
| `EditOperation` | `__init__.py` | Audit record for ontology mutations |

---

## Creating ActionType Subclasses

### Basic Structure

Every action must inherit from `ActionType` and implement the required class attributes and methods:

```python
from typing import Any, Dict, List, Optional
from scripts.ontology.actions import (
    ActionType,
    ActionContext,
    ActionResult,
    EditOperation,
    EditType,
    RequiredField,
)
from scripts.ontology.ontology_types import OntologyObject

class MyAction(ActionType[MyOntologyObject]):
    """
    Docstring describing what this action does.
    This becomes the action's description in metadata.
    """

    # REQUIRED: Unique API name (namespace.action_name convention)
    api_name: str = "domain.my_action"

    # REQUIRED: The OntologyObject type this action operates on
    object_type: type = MyOntologyObject

    # OPTIONAL: List of validation criteria
    submission_criteria: List[SubmissionCriterion] = [
        RequiredField("field_name"),
    ]

    # OPTIONAL: List of side effects to execute post-commit
    side_effects: List[SideEffect] = []

    # OPTIONAL: Whether this action requires proposal approval
    requires_proposal: bool = False

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[MyOntologyObject], List[EditOperation]]:
        """
        Implement the actual mutation logic here.

        Args:
            params: Validated action parameters
            context: Execution context with actor info

        Returns:
            Tuple of (created/modified object, list of edit operations)
        """
        # Your implementation here
        pass
```

### API Name Convention

Use a namespaced naming convention for `api_name`:

| Domain | Pattern | Examples |
|--------|---------|----------|
| Memory | `memory.<action>` | `memory.save_insight`, `memory.save_pattern` |
| LLM | `llm.<action>` | `llm.generate_plan`, `llm.route_task` |
| Learning | `learning.<action>` | `learning.save_state` |
| Logic | `<action>` | `execute_logic` |

### The `apply_edits` Method

This is the core implementation method. Key requirements:

1. **Return Type**: Must return `tuple[Optional[T], List[EditOperation]]`
   - First element: The created/modified object (or `None`)
   - Second element: List of `EditOperation` records for audit

2. **Transaction Safety**: Use repository patterns for database operations

3. **ID Generation**: Generate IDs if not provided in params

```python
async def apply_edits(
    self,
    params: Dict[str, Any],
    context: ActionContext
) -> tuple[Optional[MyEntity], List[EditOperation]]:
    # 1. Extract or generate ID
    entity_id = params.get("id")
    if not entity_id:
        import uuid
        entity_id = f"ENT-{uuid.uuid4()}"

    # 2. Construct the entity
    entity = MyEntity(
        id=entity_id,
        field1=params.get("field1"),
        field2=params.get("field2", "default"),
    )

    # 3. Persist via repository
    db = get_database()
    repo = MyRepository(db)
    await repo.save(entity, actor_id=context.actor_id)

    # 4. Create edit operation for audit
    edit = EditOperation(
        edit_type=EditType.CREATE,
        object_type="MyEntity",
        object_id=entity_id,
        changes=entity.model_dump()
    )

    return entity, [edit]
```

---

## Submission Criteria

Submission Criteria are validators that run **before** `apply_edits`. If any criterion fails, the action is rejected without mutation.

### Built-in Criteria

#### RequiredField

Ensures a field is present and non-empty:

```python
from scripts.ontology.actions import RequiredField

class MyAction(ActionType):
    submission_criteria = [
        RequiredField("title"),
        RequiredField("description"),
    ]
```

**Behavior**:
- Fails if field is `None`
- Fails if field is an empty string (after trimming whitespace)

#### AllowedValues

Restricts a field to specific values:

```python
from scripts.ontology.actions import AllowedValues

class MyAction(ActionType):
    submission_criteria = [
        AllowedValues("priority", ["low", "medium", "high", "critical"]),
        AllowedValues("status", ["draft", "pending", "approved"]),
    ]
```

**Behavior**:
- Only validates if the field is present (allows `None`)
- Fails if value is not in the allowed list

#### MaxLength

Enforces string length limits:

```python
from scripts.ontology.actions import MaxLength

class MyAction(ActionType):
    submission_criteria = [
        MaxLength("title", 200),
        MaxLength("description", 5000),
        MaxLength("code", 100000),
    ]
```

**Behavior**:
- Only applies to string values
- Fails if `len(value) > max_length`

#### CustomValidator

For complex validation logic:

```python
from scripts.ontology.actions import CustomValidator

def validate_date_range(params: Dict[str, Any], context: ActionContext) -> bool:
    """Ensure end_date is after start_date."""
    start = params.get("start_date")
    end = params.get("end_date")
    if start and end:
        return end > start
    return True

class MyAction(ActionType):
    submission_criteria = [
        CustomValidator(
            name="DateRangeValidator",
            validator_fn=validate_date_range,
            error_message="end_date must be after start_date"
        ),
    ]
```

### Creating Custom Criteria

Implement the `SubmissionCriterion` protocol:

```python
from scripts.ontology.actions import SubmissionCriterion, ValidationError, ActionContext

class MinValue:
    """Validates that a numeric field meets a minimum value."""

    def __init__(self, field_name: str, min_value: float):
        self.field_name = field_name
        self.min_value = min_value

    @property
    def name(self) -> str:
        return f"MinValue({self.field_name}, {self.min_value})"

    def validate(self, params: Dict[str, Any], context: ActionContext) -> bool:
        value = params.get(self.field_name)
        if value is not None and value < self.min_value:
            raise ValidationError(
                criterion=self.name,
                message=f"Field '{self.field_name}' must be >= {self.min_value}",
                details={
                    "field": self.field_name,
                    "value": value,
                    "min": self.min_value
                }
            )
        return True
```

### Combining Multiple Criteria

Criteria are evaluated in order. All must pass:

```python
class CreateProposalAction(ActionType):
    submission_criteria = [
        # Required fields first
        RequiredField("title"),
        RequiredField("description"),
        RequiredField("submitter_id"),

        # Then constraints
        MaxLength("title", 200),
        MaxLength("description", 10000),
        AllowedValues("priority", ["low", "medium", "high"]),

        # Then complex validation
        CustomValidator(
            name="ProposalComplexity",
            validator_fn=lambda p, c: len(p.get("steps", [])) >= 1,
            error_message="Proposal must have at least one step"
        ),
    ]
```

---

## Side Effects

Side effects are operations that execute **after** a successful action commit. They are fire-and-forget: failures are logged but do not roll back the action.

### Built-in Side Effects

#### LogSideEffect

Logs action execution to the standard logger:

```python
from scripts.ontology.actions import LogSideEffect
import logging

class MyAction(ActionType):
    side_effects = [
        LogSideEffect(log_level=logging.INFO),
    ]
```

**Output**: `Action executed: memory.save_insight by user-123 - SUCCESS`

#### WebhookSideEffect

Sends action result to a webhook URL:

```python
from scripts.ontology.actions import WebhookSideEffect

class MyAction(ActionType):
    side_effects = [
        WebhookSideEffect(
            url="https://api.example.com/webhooks/actions",
            headers={"Authorization": "Bearer token123"}
        ),
    ]
```

**Behavior**:
- POST request with `ActionResult.to_dict()` as JSON body
- 10 second timeout
- Errors logged but not raised

#### SlackNotification

Sends notification to a Slack channel:

```python
from scripts.ontology.actions import SlackNotification

class MyAction(ActionType):
    side_effects = [
        SlackNotification(
            channel="#orion-actions",
            webhook_url="https://hooks.slack.com/..."  # Optional, from config
        ),
    ]
```

#### EventBusSideEffect

Publishes an event to the internal EventBus:

```python
from scripts.ontology.actions import EventBusSideEffect

class MyAction(ActionType):
    side_effects = [
        EventBusSideEffect(
            event_type_template="{action_type}.completed"
        ),
    ]
```

**Template Variables**:
- `{action_type}`: The action's `api_name`
- `{actor_id}`: The executing actor's ID

**Example Output Event**: `memory.save_insight.completed`

### Creating Custom Side Effects

Implement the `SideEffect` protocol:

```python
from scripts.ontology.actions.side_effects import SideEffect
from scripts.ontology.actions import ActionResult, ActionContext

class MetricsEmitter:
    """Emits action metrics to monitoring system."""

    def __init__(self, metrics_endpoint: str):
        self.metrics_endpoint = metrics_endpoint

    @property
    def name(self) -> str:
        return f"MetricsEmitter({self.metrics_endpoint})"

    async def execute(
        self,
        action_result: ActionResult,
        context: ActionContext
    ) -> None:
        import httpx

        try:
            metrics = {
                "action_type": action_result.action_type,
                "success": action_result.success,
                "actor_id": context.actor_id,
                "timestamp": action_result.timestamp.isoformat(),
                "edit_count": len(action_result.edits),
            }

            async with httpx.AsyncClient() as client:
                await client.post(
                    self.metrics_endpoint,
                    json=metrics,
                    timeout=5.0
                )
        except Exception as e:
            # Side effects should NOT raise - log and continue
            logger.error(f"Metrics emission failed: {e}")
```

### Side Effect Best Practices

1. **Never Raise Exceptions**: Log errors but allow other side effects to continue
2. **Be Idempotent**: Side effects may be retried
3. **Use Timeouts**: External calls should have reasonable timeouts
4. **Check Success**: Only emit if `action_result.success is True`

```python
async def execute(self, action_result: ActionResult, context: ActionContext) -> None:
    if not action_result.success:
        return  # Don't notify on failures

    # ... notification logic
```

---

## Governance Metadata

Actions can be configured with governance metadata to control execution policies.

### Class-Level Configuration

```python
class DangerousAction(ActionType):
    api_name = "admin.delete_all_data"
    requires_proposal: bool = True  # MUST go through proposal workflow
```

### Registry-Level Configuration

Override metadata during registration:

```python
from scripts.ontology.actions import action_registry

action_registry.register(
    MyAction,
    requires_proposal=True,
    is_dangerous=True
)
```

### ActionMetadata Fields

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `requires_proposal` | `bool` | `False` | Requires proposal approval before execution |
| `is_dangerous` | `bool` | `False` | Marks action as potentially destructive |
| `description` | `str` | Class docstring | Human-readable description |

### GovernanceEngine

Query execution policies:

```python
from scripts.ontology.actions import GovernanceEngine, action_registry

engine = GovernanceEngine(action_registry)

# Check if action can execute immediately
policy = engine.check_execution_policy("admin.delete_all_data")
# Returns: "REQUIRE_PROPOSAL" | "ALLOW_IMMEDIATE" | "DENY"

# List all hazardous actions
hazardous = action_registry.get_hazardous_actions()
# Returns: ["admin.delete_all_data", "admin.reset_system", ...]
```

---

## Action Registration

Actions must be registered with the global `ActionRegistry` to be discoverable.

### Using the Decorator

The simplest approach:

```python
from scripts.ontology.actions import register_action, ActionType

@register_action
class MyAction(ActionType):
    api_name = "domain.my_action"
    # ...

# With governance override
@register_action(requires_proposal=True)
class HazardousAction(ActionType):
    api_name = "admin.hazardous_action"
    # ...
```

### Manual Registration

For dynamic or conditional registration:

```python
from scripts.ontology.actions import action_registry

# Register with default metadata
action_registry.register(MyAction)

# Register with overrides
action_registry.register(
    MyAction,
    requires_proposal=True,
    is_dangerous=True
)
```

### Registry Operations

```python
from scripts.ontology.actions import action_registry

# Get an action class by api_name
action_class = action_registry.get("memory.save_insight")

# Get metadata
metadata = action_registry.get_metadata("memory.save_insight")
print(metadata.requires_proposal)  # False
print(metadata.description)  # "Action to persist an Insight..."

# List all registered actions
all_actions = action_registry.list_actions()
# ["memory.save_insight", "memory.save_pattern", "llm.generate_plan", ...]

# Get hazardous actions
hazardous = action_registry.get_hazardous_actions()
```

---

## Execution Flow

### Complete Execution Lifecycle

```
1. INSTANTIATION
   action = MyAction()

2. CONTEXT CREATION
   context = ActionContext(
       actor_id="user-123",
       correlation_id="req-456",
       metadata={"session": db_session}
   )

3. VALIDATION (SubmissionCriteria)
   errors = action.validate(params, context)
   if errors:
       return ActionResult(success=False, error_details=errors)

4. APPLY EDITS (with retry on ConcurrencyError)
   for attempt in range(MAX_RETRIES):
       try:
           obj, edits = await action.apply_edits(params, context)
           break
       except ConcurrencyError:
           await asyncio.sleep(backoff)

5. SIDE EFFECTS (fire-and-forget)
   for effect in action.side_effects:
       try:
           await effect.execute(result, context)
       except Exception:
           logger.error(...)  # Don't re-raise

6. RETURN RESULT
   return ActionResult(
       action_type=action.api_name,
       success=True,
       edits=edits,
       created_ids=[obj.id]
   )
```

### Concurrency Handling

The execution engine automatically retries on `ConcurrencyError`:

- **Max Retries**: 3 attempts
- **Backoff**: Exponential (0.5s, 1s, 2s)
- **After Exhaustion**: Returns failure result

```python
# Concurrency errors from optimistic locking are handled automatically
# Your apply_edits just needs to use the repository correctly:

async def apply_edits(self, params, context):
    repo = MyRepository(get_database())

    # The repository's save() method checks version and raises
    # ConcurrencyError if the object was modified
    await repo.save(entity, actor_id=context.actor_id)
```

### ActionContext Usage

```python
from scripts.ontology.actions import ActionContext

# User-initiated action
context = ActionContext(
    actor_id="user-123",
    correlation_id="req-abc-456",  # For distributed tracing
    metadata={
        "session": db_session,      # Pass DB session for transaction
        "source": "api",
        "request_ip": "192.168.1.1"
    }
)

# System-initiated action
context = ActionContext.system()
# Creates: ActionContext(actor_id="system", metadata={"automated": True})
```

---

## Best Practices

### 1. Naming Conventions

```python
# Good: Namespaced, descriptive api_names
api_name = "memory.save_insight"
api_name = "learning.update_learner_state"
api_name = "llm.generate_plan"

# Avoid: Vague or non-namespaced names
api_name = "save"  # Too generic
api_name = "doThing"  # Not descriptive
```

### 2. Validation First

Always validate thoroughly before mutation:

```python
submission_criteria = [
    # 1. Required fields
    RequiredField("title"),
    RequiredField("owner_id"),

    # 2. Type/format constraints
    MaxLength("title", 200),
    AllowedValues("status", ["draft", "active"]),

    # 3. Business rules
    CustomValidator("OwnerExists", check_owner_exists, "Owner not found"),
    CustomValidator("UniqueTitle", check_unique_title, "Title already exists"),
]
```

### 3. Idempotent Operations

Design actions to be safely re-executable:

```python
async def apply_edits(self, params, context):
    # Use upsert pattern when appropriate
    entity_id = params.get("id")

    existing = await repo.get_by_id(entity_id)
    if existing:
        # Update existing
        existing.field = params.get("field", existing.field)
        edit_type = EditType.MODIFY
    else:
        # Create new
        existing = MyEntity(id=entity_id, ...)
        edit_type = EditType.CREATE

    await repo.save(existing)

    return existing, [EditOperation(edit_type=edit_type, ...)]
```

### 4. Comprehensive EditOperations

Record all changes for audit:

```python
async def apply_edits(self, params, context):
    edits = []

    # Track the main entity change
    edits.append(EditOperation(
        edit_type=EditType.CREATE,
        object_type="Task",
        object_id=task.id,
        changes={"title": task.title, "priority": task.priority}
    ))

    # Track related changes (links, cascades)
    if assigned_to:
        edits.append(EditOperation(
            edit_type=EditType.LINK,
            object_type="Task",
            object_id=task.id,
            changes={"link_type": "assigned_to", "target_id": assigned_to}
        ))

    return task, edits
```

### 5. Error Handling

Return structured errors, don't raise in apply_edits:

```python
async def apply_edits(self, params, context):
    try:
        # Attempt operation
        result = await external_service.call(params)
    except ExternalServiceError as e:
        # Return failure result instead of raising
        return ActionResult(
            action_type=self.api_name,
            success=False,
            error=f"External service failed: {e}",
            error_details={"service": "external", "code": e.code}
        )

    # Continue with success path
    ...
```

### 6. Schema Generation

Use `get_parameter_schema()` for API documentation:

```python
# Automatically generates JSON Schema from SubmissionCriteria
schema = MyAction.get_parameter_schema()

# Returns:
# {
#     "$schema": "http://json-schema.org/draft-07/schema#",
#     "title": "memory.save_insight",
#     "type": "object",
#     "required": ["content", "provenance"],
#     "properties": {
#         "content": {"type": "string"},
#         "provenance": {"type": "string"}
#     }
# }
```

---

## Complete Examples

### Example 1: Memory Action (CRUD)

```python
"""
File: scripts/ontology/actions/memory_actions.py
"""
from typing import Any, Dict, Optional, List
from scripts.ontology.actions import (
    ActionType,
    ActionContext,
    ActionResult,
    EditOperation,
    EditType,
    RequiredField,
    MaxLength,
    LogSideEffect,
    EventBusSideEffect,
)
from scripts.ontology.ontology_types import ObjectStatus
from scripts.ontology.schemas.memory import OrionInsight, InsightContent, InsightProvenance
from scripts.ontology.storage import InsightRepository, get_database


class SaveInsightAction(ActionType[OrionInsight]):
    """
    Action to persist an Insight to the Ontology.
    Replaces legacy memory_manager.save_object('insight').
    """
    api_name = "memory.save_insight"
    object_type = OrionInsight

    submission_criteria = [
        RequiredField("content"),
        RequiredField("provenance"),
        MaxLength("content.summary", 10000),
    ]

    side_effects = [
        LogSideEffect(),
        EventBusSideEffect("{action_type}.completed"),
    ]

    requires_proposal = False  # Insights don't need approval

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[OrionInsight, List[EditOperation]]:
        # 1. Generate ID if not provided
        insight_id = params.get("id")
        if not insight_id:
            import uuid
            insight_id = f"INS-{uuid.uuid4()}"

        # 2. Parse status
        status = ObjectStatus.ACTIVE
        if "status" in params:
            try:
                status = ObjectStatus(params["status"])
            except ValueError:
                pass

        # 3. Construct value objects
        content_data = params.get("content", {})
        if isinstance(content_data, str):
            content_data = {"summary": content_data}

        content = InsightContent(
            summary=content_data.get("summary", "No summary"),
            domain=content_data.get("domain", "general"),
            tags=content_data.get("tags", [])
        )

        prov_data = params.get("provenance", {})
        provenance = InsightProvenance(
            source_episodic_ids=prov_data.get("source_episodic_ids", []),
            method=prov_data.get("method", "manual")
        )

        # 4. Create entity
        insight = OrionInsight(
            id=insight_id,
            status=status,
            confidence_score=params.get("confidence_score", 1.0),
            decay_factor=params.get("decay_factor", 0.95),
            provenance=provenance,
            content=content,
        )

        # 5. Persist
        db = get_database()
        repo = InsightRepository(db)
        await repo.save(insight, actor_id=context.actor_id)

        # 6. Create edit operation
        edit = EditOperation(
            edit_type=EditType.CREATE,
            object_type="OrionInsight",
            object_id=insight_id,
            changes=insight.model_dump()
        )

        return insight, [edit]
```

### Example 2: LLM Action (External Integration)

```python
"""
File: scripts/ontology/actions/llm_actions.py
"""
from typing import Any, Dict, List
from scripts.ontology.actions import (
    ActionType,
    ActionContext,
    EditOperation,
    EditType,
    RequiredField,
    register_action,
)
from scripts.ontology.plan import Plan


@register_action
class GeneratePlanAction(ActionType[Plan]):
    """
    Action to generate a Plan using an LLM.
    Audited and Governed.
    """
    api_name = "llm.generate_plan"
    object_type = Plan

    submission_criteria = [
        RequiredField("goal")
    ]

    requires_proposal = False

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Plan, List[EditOperation]]:
        prompt = params["goal"]
        model = params.get("model", "gpt-4o")

        # Lazy import to avoid circular dependency
        from scripts.llm.instructor_client import InstructorClient

        client = InstructorClient()

        try:
            plan = client.generate(prompt, Plan, model_name=model)
        except Exception as e:
            # Raise to let execute() handle it
            raise RuntimeError(f"LLM Generation Failed: {e}")

        # Create audit edit
        edit = EditOperation(
            edit_type=EditType.CREATE,
            object_type="Plan",
            object_id=plan.id,
            changes=plan.model_dump(mode='json')
        )

        return plan, [edit]
```

### Example 3: Governance-Required Action

```python
"""
File: scripts/ontology/actions/admin_actions.py
"""
from typing import Any, Dict, List
from scripts.ontology.actions import (
    ActionType,
    ActionContext,
    EditOperation,
    EditType,
    RequiredField,
    CustomValidator,
    register_action,
    WebhookSideEffect,
    SlackNotification,
)


def validate_admin_role(params: Dict[str, Any], context: ActionContext) -> bool:
    """Only admins can execute this action."""
    return context.metadata.get("role") == "admin"


@register_action(requires_proposal=True)
class PurgeOldDataAction(ActionType):
    """
    DANGEROUS: Purges data older than specified date.
    Requires proposal approval before execution.
    """
    api_name = "admin.purge_old_data"
    object_type = None

    submission_criteria = [
        RequiredField("before_date"),
        RequiredField("confirmation_code"),
        CustomValidator(
            "AdminRole",
            validate_admin_role,
            "Only administrators can execute this action"
        ),
        CustomValidator(
            "ConfirmationMatch",
            lambda p, c: p.get("confirmation_code") == "PURGE-CONFIRM",
            "Invalid confirmation code"
        ),
    ]

    side_effects = [
        SlackNotification(channel="#orion-alerts"),
        WebhookSideEffect(url="https://audit.example.com/dangerous-actions"),
    ]

    requires_proposal = True  # MUST go through approval

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Dict[str, Any], List[EditOperation]]:
        from datetime import datetime

        before_date = datetime.fromisoformat(params["before_date"])

        # Perform purge (implementation details omitted)
        deleted_count = await self._perform_purge(before_date)

        result = {
            "deleted_count": deleted_count,
            "before_date": before_date.isoformat(),
            "executed_by": context.actor_id,
        }

        edit = EditOperation(
            edit_type=EditType.DELETE,
            object_type="MultipleObjects",
            object_id="bulk-purge",
            changes=result
        )

        return result, [edit]

    async def _perform_purge(self, before_date) -> int:
        # Implementation
        return 0
```

---

## Troubleshooting

### Common Errors

#### "Missing api_name"

```python
# Error: ValueError: MyAction missing api_name

# Solution: Add the class attribute
class MyAction(ActionType):
    api_name = "domain.my_action"  # Add this
```

#### "Submission criteria failed"

```python
# Error: ActionResult(success=False, error="Submission criteria failed")

# Solution: Check error_details for specific failures
result = await action.execute(params, context)
if not result.success:
    print(result.error_details)
    # {'validation_errors': ['[RequiredField(title)] Field \'title\' is required']}
```

#### "ConcurrencyError after N retries"

```python
# Error: Concurrency conflict after 3 retries

# Cause: Object was modified by another process between read and write
# Solution:
# 1. Reduce transaction scope
# 2. Use optimistic locking correctly (version field)
# 3. Implement conflict resolution in apply_edits
```

#### "Submodule import failed"

```python
# Error: ImportError during initialization

# Cause: Circular import in action submodules
# Solution: Use lazy imports inside apply_edits
async def apply_edits(self, params, context):
    from scripts.module import SomeClass  # Lazy import here
```

### Debugging Tips

1. **Enable Debug Logging**
   ```python
   import logging
   logging.getLogger("scripts.ontology.actions").setLevel(logging.DEBUG)
   ```

2. **Inspect Schema Generation**
   ```python
   schema = MyAction.get_parameter_schema()
   print(json.dumps(schema, indent=2))
   ```

3. **Test Validation Separately**
   ```python
   action = MyAction()
   errors = action.validate(params, context)
   print(errors)  # List of validation error messages
   ```

4. **Check Registry State**
   ```python
   from scripts.ontology.actions import action_registry
   print(action_registry.list_actions())
   print(action_registry.get_metadata("my.action"))
   ```

---

## Appendix: File Locations

| File | Purpose |
|------|---------|
| `scripts/ontology/actions/__init__.py` | Core action system, registry, criteria |
| `scripts/ontology/actions/side_effects.py` | Side effect implementations |
| `scripts/ontology/actions/memory_actions.py` | Memory domain actions |
| `scripts/ontology/actions/llm_actions.py` | LLM domain actions |
| `scripts/ontology/actions/learning_actions.py` | Learning domain actions |
| `scripts/ontology/actions/logic_actions.py` | Logic execution actions |
| `scripts/ontology/ontology_types.py` | Base types and OntologyObject |

---

*Document generated for Orion ODA v3.0 - Palantir AIP/Foundry Compliant*
