# ActionType

> **Ontology Element Type:** ActionType
> **Schema Complexity:** Highest (894 lines JSON Schema)
> **Implementation:** `ontology_definition/types/action_type.py`

---

## Definition

**Palantir Official Definition:**

> "An ActionType is the schema definition of a set of changes or edits to objects, property values, and links that a user can take at once."

An ActionType represents a user-initiated operation that modifies the Ontology state. Unlike ObjectTypes (which define data structures) or LinkTypes (which define relationships), ActionTypes define **behaviors** - the operations users can perform to create, modify, or delete objects and their relationships.

---

## Core Concepts

### What is an ActionType

An ActionType is the **schema definition** for an operation, not the operation itself. It specifies:

1. **What inputs are needed** (parameters)
2. **What will be affected** (affected ObjectTypes)
3. **What changes will occur** (edit specifications)
4. **What conditions must be met** (submission criteria)
5. **What happens after** (side effects)
6. **How it is executed** (implementation)

### User Interaction Model

```
User Request                 ActionType Schema              Execution
     |                              |                          |
     v                              v                          v
[Input Form] -----> [Parameter Validation] -----> [Implementation Logic]
                           |                              |
                           v                              v
               [Submission Criteria Check]      [Edit Specifications]
                           |                              |
                           v                              v
                    [Pass/Fail?] ------------> [Side Effects Triggered]
```

### Connection to Functions

ActionTypes in Palantir Foundry are tightly coupled with **Functions**:

| Implementation Type | Function Connection |
|---------------------|---------------------|
| **DECLARATIVE** | No function - uses declarative edit specifications |
| **FUNCTION_BACKED** | Calls TypeScript or Python function for logic |
| **INLINE_EDIT** | Simple property edits, hidden from UI |

---

## Schema Structure

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `apiName` | string | Programmatic identifier (immutable once Active). Pattern: `^[a-zA-Z][a-zA-Z0-9_.]*$` |
| `displayName` | string | Human-friendly UI name (1-255 chars) |
| `affectedObjectTypes` | array | ObjectTypes that this action can create/modify/delete (min 1) |
| `implementation` | object | How the action logic is implemented |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `description` | string | null | Documentation (max 4096 chars) |
| `rid` | string | auto | Resource ID, auto-generated |
| `category` | string | null | Action category for organization |
| `hazardous` | boolean | false | Requires Proposal approval if true |
| `parameters` | array | [] | User input definitions |
| `editSpecifications` | array | [] | Declarative edit operations |
| `submissionCriteria` | array | [] | Preconditions for execution |
| `sideEffects` | array | [] | Post-execution effects |
| `permissions` | object | null | Permission requirements |
| `status` | enum | EXPERIMENTAL | Lifecycle status |
| `auditConfig` | object | null | Audit trail configuration |
| `undoConfig` | object | null | Undo/revert configuration |
| `metadata` | object | null | Tracking information |

### Nested Types Reference

```
ActionType
├── parameters: ActionParameter[]
│   ├── dataType: ParameterDataType
│   ├── constraints: ParameterConstraints
│   └── uiHints: ParameterUIHints
├── affectedObjectTypes: AffectedObjectType[]
├── editSpecifications: EditSpecification[]
│   ├── propertyMappings: PropertyMapping[]
│   ├── objectSelection: ObjectSelection
│   ├── linkSelection: LinkSelection
│   └── conditional: EditCondition
├── submissionCriteria: SubmissionCriterion[]
├── sideEffects: SideEffect[]
│   └── configuration: SideEffectConfig
│       ├── notificationConfig: NotificationConfig
│       ├── webhookConfig: WebhookConfig
│       └── triggerActionConfig: TriggerActionConfig
├── implementation: ActionImplementation
│   └── functionConfig: FunctionConfig
├── permissions: ActionPermissions
│   └── objectTypePermissions: ObjectTypePermission[]
├── auditConfig: AuditConfig
├── undoConfig: UndoConfig
└── metadata: ActionTypeMetadata
```

---

## Implementation Types

### DECLARATIVE

Actions defined entirely through declarative edit specifications without custom code.

**Characteristics:**
- No external function required
- Changes defined via `editSpecifications`
- Fully auditable and traceable
- Best for simple CRUD operations

**Requirements:**
- Must have at least one `editSpecification`

**Example:**
```json
{
  "implementation": {
    "type": "DECLARATIVE"
  },
  "editSpecifications": [
    {
      "operationType": "CREATE_LINK",
      "targetLinkType": "ProjectToTeamMember",
      "linkSelection": {
        "sourceObjectParameter": "project",
        "targetObjectParameter": "employee"
      }
    }
  ]
}
```

### FUNCTION_BACKED

Actions with custom logic implemented in TypeScript or Python functions.

**Characteristics:**
- Calls external function for execution
- Supports complex business logic
- Can interact with external systems
- Function reference required

**Configuration:**
```json
{
  "implementation": {
    "type": "FUNCTION_BACKED",
    "functionRef": "lib.oda.actions.file.modify_file",
    "functionLanguage": "PYTHON",
    "functionConfig": {
      "timeout": 30000,
      "retries": 0
    }
  }
}
```

**Function Languages:**
| Language | Use Case |
|----------|----------|
| `TYPESCRIPT` | Foundry Functions (native) |
| `PYTHON` | Data processing, ML integration |

### INLINE_EDIT

Simple property edits that appear as inline editing in the UI.

**Characteristics:**
- Direct property modification
- No form UI - appears as inline edit
- Hidden from action catalog
- Best for single-field updates

---

## Parameters

### ActionParameter Structure

```json
{
  "apiName": "filePath",
  "displayName": "File Path",
  "description": "Path to the file to modify",
  "dataType": {
    "type": "STRING"
  },
  "required": true,
  "defaultValue": null,
  "constraints": {
    "pattern": "^[a-zA-Z0-9/_.-]+$"
  },
  "uiHints": {
    "inputType": "text",
    "placeholder": "Enter file path...",
    "helperText": "Use forward slashes for path separators",
    "order": 1
  }
}
```

### Parameter Data Types

| Type | Description | Special Requirements |
|------|-------------|---------------------|
| `STRING` | Text value | - |
| `INTEGER` | 32-bit integer | - |
| `LONG` | 64-bit integer | - |
| `FLOAT` | Single-precision float | - |
| `DOUBLE` | Double-precision float | - |
| `BOOLEAN` | True/false | - |
| `DATE` | Calendar date | - |
| `TIMESTAMP` | Date and time | - |
| `ARRAY` | Collection | Requires `arrayItemType` |
| `OBJECT_PICKER` | Object reference | Requires `objectTypeRef` |
| `OBJECT_SET` | Multiple objects | Requires `objectTypeRef` |
| `ATTACHMENT` | File attachment | - |
| `STRUCT` | Nested structure | Requires `structDefinition` |

### OBJECT_PICKER and OBJECT_SET

For selecting Ontology objects:

```json
{
  "apiName": "employee",
  "displayName": "Employee",
  "dataType": {
    "type": "OBJECT_PICKER",
    "objectTypeRef": "Employee"
  },
  "required": true,
  "constraints": {
    "objectFilter": "status == 'ACTIVE'"
  }
}
```

### ARRAY Type

For collections:

```json
{
  "apiName": "tags",
  "displayName": "Tags",
  "dataType": {
    "type": "ARRAY",
    "arrayItemType": {
      "type": "STRING"
    }
  }
}
```

### Validation Rules (ParameterConstraints)

| Constraint | Type | Description |
|------------|------|-------------|
| `enum` | array | Allowed values |
| `minValue` | number | Minimum numeric value |
| `maxValue` | number | Maximum numeric value |
| `minLength` | integer | Minimum string length |
| `maxLength` | integer | Maximum string length |
| `pattern` | string | Regex pattern |
| `objectFilter` | string | Filter for OBJECT_PICKER |

**Example with all constraints:**
```json
{
  "constraints": {
    "enum": ["Lead", "Developer", "Designer", "QA", "Manager"],
    "minLength": 1,
    "maxLength": 50
  }
}
```

### UI Hints (ParameterUIHints)

| Field | Type | Description |
|-------|------|-------------|
| `inputType` | enum | UI control type |
| `placeholder` | string | Placeholder text |
| `helperText` | string | Helper text below input |
| `order` | integer | Display order in form |

**Input Types:**
- `text` - Single-line text
- `textarea` - Multi-line text
- `number` - Numeric input
- `select` - Dropdown single select
- `multiselect` - Multi-select dropdown
- `datepicker` - Date picker
- `filepicker` - File selection
- `objectpicker` - Object selector

---

## Affected Object Types

### AffectedObjectType Structure

Declares which ObjectTypes the action can manipulate:

```json
{
  "objectTypeApiName": "File",
  "operations": ["CREATE", "MODIFY", "DELETE"],
  "modifiableProperties": ["content", "modifiedAt", "modifiedBy"]
}
```

### Operations

| Operation | Description |
|-----------|-------------|
| `CREATE` | Action can create new object instances |
| `MODIFY` | Action can update existing objects |
| `DELETE` | Action can remove object instances |

### Modifiable Properties

For `MODIFY` operations, specifies which properties can be changed:

- **Empty array (`[]`):** All properties can be modified
- **Populated array:** Only listed properties can be changed

```json
{
  "objectTypeApiName": "Employee",
  "operations": ["MODIFY"],
  "modifiableProperties": ["department", "title", "manager"]
}
```

---

## Edit Specifications

Edit specifications define declarative edit operations for `DECLARATIVE` implementation type.

### EditSpecification Structure

```json
{
  "operationType": "MODIFY_OBJECT",
  "targetObjectType": "File",
  "objectSelection": {
    "selectionType": "QUERY",
    "queryExpression": "path == $filePath"
  },
  "propertyMappings": [
    {
      "targetProperty": "content",
      "sourceParameter": "content"
    },
    {
      "targetProperty": "modifiedAt",
      "expression": "now()"
    }
  ],
  "conditional": {
    "conditionType": "PARAMETER_NOT_NULL",
    "parameterRef": "content"
  }
}
```

### Operation Types

| Operation Type | Description | Required Fields |
|----------------|-------------|-----------------|
| `CREATE_OBJECT` | Create new object | `targetObjectType` |
| `MODIFY_OBJECT` | Update existing object | `targetObjectType`, `objectSelection` |
| `DELETE_OBJECT` | Remove object | `targetObjectType`, `objectSelection` |
| `CREATE_LINK` | Create relationship | `targetLinkType`, `linkSelection` |
| `DELETE_LINK` | Remove relationship | `targetLinkType`, `linkSelection` |
| `MODIFY_PROPERTY` | Update single property | `targetObjectType`, `objectSelection` |

### Property Mappings

Maps parameter values to object properties:

| Source Type | Field | Description |
|-------------|-------|-------------|
| Parameter | `sourceParameter` | Parameter apiName providing value |
| Static | `staticValue` | Hard-coded value |
| Expression | `expression` | Computed value (e.g., `now()`) |

**At least one source must be specified.**

```json
{
  "propertyMappings": [
    { "targetProperty": "name", "sourceParameter": "employeeName" },
    { "targetProperty": "createdAt", "expression": "now()" },
    { "targetProperty": "status", "staticValue": "ACTIVE" }
  ]
}
```

### Object Selection

Specifies how to find objects for modification/deletion:

| Selection Type | Description | Required Field |
|----------------|-------------|----------------|
| `PARAMETER` | Object from parameter | `parameterRef` |
| `QUERY` | Find by query | `queryExpression` |
| `CURRENT` | Current context object | - |

```json
{
  "objectSelection": {
    "selectionType": "QUERY",
    "queryExpression": "path == $filePath"
  }
}
```

### Link Selection

For link operations, specifies source and target objects:

```json
{
  "linkSelection": {
    "sourceObjectParameter": "project",
    "targetObjectParameter": "employee"
  }
}
```

Or using queries:
```json
{
  "linkSelection": {
    "sourceObjectQuery": "Project.where(id == $projectId)",
    "targetObjectQuery": "Employee.where(id == $employeeId)"
  }
}
```

### Conditional Execution

Edit specifications can have conditions:

| Condition Type | Description |
|----------------|-------------|
| `PARAMETER_EQUALS` | Parameter matches expected value |
| `PARAMETER_NOT_NULL` | Parameter is provided |
| `OBJECT_STATE` | Object in specific state |
| `EXPRESSION` | Custom boolean expression |

```json
{
  "conditional": {
    "conditionType": "PARAMETER_EQUALS",
    "parameterRef": "updateStatus",
    "expectedValue": true
  }
}
```

---

## Submission Criteria

Pre-conditions that must be satisfied before action execution.

### SubmissionCriterion Structure

```json
{
  "apiName": "fileExists",
  "displayName": "File Must Exist",
  "description": "Ensures the target file exists before modification",
  "criterionType": "OBJECT_STATE_CHECK",
  "expression": "File.exists($filePath)",
  "errorMessage": "File does not exist at the specified path.",
  "severity": "ERROR"
}
```

### Criterion Types

| Type | Description | Use Case |
|------|-------------|----------|
| `PARAMETER_VALIDATION` | Validate parameter values | Required fields, format checks |
| `OBJECT_STATE_CHECK` | Verify object state | Object exists, status check |
| `PERMISSION_CHECK` | Verify user permissions | Write access, role check |
| `CARDINALITY_CHECK` | Verify relationship constraints | Not already linked |
| `CUSTOM_FUNCTION` | Call custom validation function | Complex business rules |

### Severity Levels

| Severity | Behavior |
|----------|----------|
| `ERROR` | Blocks execution (default) |
| `WARNING` | Allows execution with warning |

### Examples

**Permission Check:**
```json
{
  "apiName": "hasWritePermission",
  "criterionType": "PERMISSION_CHECK",
  "expression": "user.hasPermission('file.write', $filePath)",
  "errorMessage": "You do not have write permission for this file.",
  "severity": "ERROR"
}
```

**Cardinality Check:**
```json
{
  "apiName": "notAlreadyAssigned",
  "criterionType": "CARDINALITY_CHECK",
  "expression": "!ProjectToTeamMember.exists($project, $employee)",
  "errorMessage": "Employee is already assigned to this project."
}
```

---

## Side Effects

Post-execution effects triggered after successful action completion.

### SideEffect Structure

```json
{
  "apiName": "notifyFileOwner",
  "effectType": "NOTIFICATION",
  "configuration": {
    "notificationConfig": {
      "recipientExpression": "File.getOwner($filePath)",
      "messageTemplate": "File ${filePath} was modified by ${user.name}. Reason: ${reason}",
      "channel": "IN_APP"
    }
  },
  "conditional": {
    "conditionType": "PARAMETER_NOT_NULL",
    "parameterRef": "reason"
  },
  "async": true
}
```

### Side Effect Types

| Type | Description | Configuration |
|------|-------------|---------------|
| `NOTIFICATION` | Send notification to users | `notificationConfig` |
| `WEBHOOK` | Call external HTTP endpoint | `webhookConfig` |
| `EMAIL` | Send email notification | (via notificationConfig) |
| `AUDIT_LOG` | Create audit entry | (automatic) |
| `TRIGGER_ACTION` | Trigger another action | `triggerActionConfig` |
| `CUSTOM_FUNCTION` | Call custom function | (custom) |

### NOTIFICATION

```json
{
  "notificationConfig": {
    "recipients": ["user-123", "group-456"],
    "recipientExpression": "Project.getMembers($projectId)",
    "messageTemplate": "Project ${projectName} was updated",
    "channel": "IN_APP"
  }
}
```

**Channels:**
- `IN_APP` - Foundry in-app notification (default)
- `EMAIL` - Email notification
- `SLACK` - Slack integration
- `TEAMS` - Microsoft Teams integration

### WEBHOOK

```json
{
  "webhookConfig": {
    "url": "https://api.example.com/hooks/ontology-change",
    "method": "POST",
    "headers": {
      "Authorization": "Bearer ${secrets.webhookToken}",
      "Content-Type": "application/json"
    },
    "payloadTemplate": "{\"action\": \"${actionApiName}\", \"user\": \"${user.id}\"}",
    "retryPolicy": {
      "maxRetries": 3,
      "retryDelay": 1000
    }
  }
}
```

### TRIGGER_ACTION

```json
{
  "triggerActionConfig": {
    "actionApiName": "audit.createEntry",
    "parameterMappings": {
      "entityType": "'File'",
      "entityId": "$filePath",
      "action": "'MODIFY'"
    }
  }
}
```

### Async Execution

| `async` | Behavior |
|---------|----------|
| `true` (default) | Runs after response returns |
| `false` | Blocks until complete |

---

## Audit Configuration

### AuditConfig Structure

```json
{
  "enabled": true,
  "logLevel": "DETAILED",
  "includeParameters": true,
  "includeBeforeAfter": true,
  "sensitiveParameters": ["password", "apiKey"],
  "retentionDays": 365
}
```

### Audit Log Levels

| Level | Content Logged |
|-------|----------------|
| `MINIMAL` | Action name, user, timestamp |
| `STANDARD` | + affected objects, status (default) |
| `DETAILED` | + parameter values, before/after state |

### Sensitive Parameters

Parameters listed in `sensitiveParameters` are masked in audit logs:

```json
{
  "sensitiveParameters": ["password", "secretToken", "apiKey"]
}
```

Logged as: `"password": "***MASKED***"`

### Retention Policies

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `retentionDays` | integer | 365 | Days to retain audit logs (min: 1) |

---

## Undo Configuration

### UndoConfig Structure

```json
{
  "undoable": true,
  "undoWindowMinutes": 60,
  "undoStrategy": "RESTORE_SNAPSHOT",
  "inverseActionRef": null
}
```

### Undo Strategies

| Strategy | Description | Requirements |
|----------|-------------|--------------|
| `RESTORE_SNAPSHOT` | Restore from before-state snapshot (default) | `includeBeforeAfter` in audit |
| `INVERSE_ACTION` | Execute inverse action | `inverseActionRef` required |
| `CUSTOM_FUNCTION` | Call custom undo function | Custom implementation |

### Undo Time Limits

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `undoable` | boolean | false | Enable undo capability |
| `undoWindowMinutes` | integer | 60 | Time window for undo (0 = no limit) |

### Inverse Action Example

```json
{
  "undoable": true,
  "undoStrategy": "INVERSE_ACTION",
  "inverseActionRef": "file.restore"
}
```

---

## Lifecycle Status

### ActionTypeStatus Values

| Status | Description | Constraints |
|--------|-------------|-------------|
| `DRAFT` | Initial development | Not visible in production |
| `EXPERIMENTAL` | Under testing (default) | May change without notice |
| `ALPHA` | Early adopter phase | Limited support |
| `BETA` | Feature complete, stabilizing | May have issues |
| `ACTIVE` | Production use | Stable API |
| `STABLE` | Schema frozen | No breaking changes |
| `DEPRECATED` | Marked for removal | Use alternative |
| `SUNSET` | End-of-life announced | Migration required |
| `ARCHIVED` | Soft-deleted | Not executable |
| `DELETED` | Hard-deleted | Removed from system |

### ENDORSED Status NOT Supported

**IMPORTANT:** Unlike ObjectType, ActionType does **NOT** support the `ENDORSED` status.

> "Endorsed status is only available for ObjectTypes. LinkTypes, Properties, and ActionTypes cannot be endorsed." - Palantir Documentation

This is enforced in the implementation:

```python
class ActionTypeStatus(str, Enum):
    """
    Lifecycle status for ActionTypes.

    Same as ObjectStatus but WITHOUT ENDORSED status.
    Only ObjectTypes can be endorsed.
    """
    DRAFT = "DRAFT"
    EXPERIMENTAL = "EXPERIMENTAL"
    # ... (no ENDORSED)
```

---

## Permissions

### ActionPermissions Structure

```json
{
  "requiredRoles": ["Developer", "Admin"],
  "requiredPermissions": ["file.write", "file.execute"],
  "objectTypePermissions": [
    {
      "objectTypeApiName": "File",
      "requiredAccess": "WRITE"
    },
    {
      "objectTypeApiName": "AuditLog",
      "requiredAccess": "READ"
    }
  ]
}
```

### Access Levels

| Level | Description |
|-------|-------------|
| `READ` | View objects |
| `WRITE` | Create/modify objects |
| `DELETE` | Remove objects |
| `ADMIN` | Full control |

---

## Hazardous Actions

Actions marked as `hazardous: true` require Proposal approval workflow.

### Hazardous Flag

```json
{
  "apiName": "file.delete",
  "hazardous": true,
  ...
}
```

### Workflow for Hazardous Actions

```
User Initiates Action
         |
         v
  [Action Marked Hazardous?]
         |
    Yes  |   No
         v   |
  [Create Proposal]
         |   |
         v   |
  [Approval Required] <---+
         |
    Approved?
         |
    Yes  |   No
         v   |
  [Execute Action] |
         |         v
         v   [Reject with reason]
  [Log Execution]
```

### ODA Integration

In ODA (Ontology-Driven Architecture), hazardous actions use the Proposal system:

```python
# Hazardous action requires proposal
mcp__oda_ontology__create_proposal(
    action_type="file.modify",
    payload={"path": "...", "content": "..."},
    submit=True
)

# Approval required
mcp__oda_ontology__approve_proposal(proposal_id="prop_123")

# Then execute
mcp__oda_ontology__execute_proposal(proposal_id="prop_123")
```

---

## Examples

### Example 1: Declarative Action (assignEmployeeToProject)

A non-hazardous action that creates a link between Employee and Project:

```json
{
  "apiName": "assignEmployeeToProject",
  "displayName": "Assign Employee to Project",
  "description": "Assigns an employee to a project with a specified role.",
  "category": "project",
  "hazardous": false,
  "parameters": [
    {
      "apiName": "employee",
      "displayName": "Employee",
      "dataType": {
        "type": "OBJECT_PICKER",
        "objectTypeRef": "Employee"
      },
      "required": true
    },
    {
      "apiName": "project",
      "displayName": "Project",
      "dataType": {
        "type": "OBJECT_PICKER",
        "objectTypeRef": "Project"
      },
      "required": true
    },
    {
      "apiName": "role",
      "displayName": "Role",
      "dataType": {
        "type": "STRING"
      },
      "required": true,
      "constraints": {
        "enum": ["Lead", "Developer", "Designer", "QA", "Manager"]
      }
    }
  ],
  "affectedObjectTypes": [
    {
      "objectTypeApiName": "Employee",
      "operations": ["MODIFY"]
    },
    {
      "objectTypeApiName": "Project",
      "operations": ["MODIFY"]
    }
  ],
  "editSpecifications": [
    {
      "operationType": "CREATE_LINK",
      "targetLinkType": "ProjectToTeamMember",
      "linkSelection": {
        "sourceObjectParameter": "project",
        "targetObjectParameter": "employee"
      },
      "propertyMappings": [
        {
          "targetProperty": "assignedRole",
          "sourceParameter": "role"
        },
        {
          "targetProperty": "joinedAt",
          "expression": "now()"
        }
      ]
    }
  ],
  "submissionCriteria": [
    {
      "apiName": "notAlreadyAssigned",
      "displayName": "Not Already Assigned",
      "criterionType": "CARDINALITY_CHECK",
      "expression": "!ProjectToTeamMember.exists($project, $employee)",
      "errorMessage": "Employee is already assigned to this project."
    }
  ],
  "implementation": {
    "type": "DECLARATIVE"
  },
  "status": "ACTIVE"
}
```

### Example 2: Function-Backed Action (file.modify - hazardous)

A hazardous action with function-backed implementation:

```json
{
  "apiName": "file.modify",
  "displayName": "Modify File",
  "description": "Modifies an existing file in the repository.",
  "category": "file",
  "hazardous": true,
  "parameters": [
    {
      "apiName": "filePath",
      "displayName": "File Path",
      "description": "Path to the file to modify.",
      "dataType": {
        "type": "STRING"
      },
      "required": true,
      "constraints": {
        "pattern": "^[a-zA-Z0-9/_.-]+$"
      }
    },
    {
      "apiName": "content",
      "displayName": "New Content",
      "description": "New content for the file.",
      "dataType": {
        "type": "STRING"
      },
      "required": true,
      "uiHints": {
        "inputType": "textarea"
      }
    },
    {
      "apiName": "reason",
      "displayName": "Reason",
      "description": "Reason for the modification.",
      "dataType": {
        "type": "STRING"
      },
      "required": true
    }
  ],
  "affectedObjectTypes": [
    {
      "objectTypeApiName": "File",
      "operations": ["MODIFY"],
      "modifiableProperties": ["content", "modifiedAt", "modifiedBy"]
    }
  ],
  "editSpecifications": [
    {
      "operationType": "MODIFY_OBJECT",
      "targetObjectType": "File",
      "objectSelection": {
        "selectionType": "QUERY",
        "queryExpression": "path == $filePath"
      },
      "propertyMappings": [
        {
          "targetProperty": "content",
          "sourceParameter": "content"
        }
      ]
    }
  ],
  "submissionCriteria": [
    {
      "apiName": "fileExists",
      "displayName": "File Must Exist",
      "criterionType": "OBJECT_STATE_CHECK",
      "expression": "File.exists($filePath)",
      "errorMessage": "File does not exist at the specified path."
    },
    {
      "apiName": "hasWritePermission",
      "displayName": "Write Permission Required",
      "criterionType": "PERMISSION_CHECK",
      "expression": "user.hasPermission('file.write', $filePath)",
      "errorMessage": "You do not have write permission for this file."
    }
  ],
  "sideEffects": [
    {
      "apiName": "notifyFileOwner",
      "effectType": "NOTIFICATION",
      "configuration": {
        "notificationConfig": {
          "recipientExpression": "File.getOwner($filePath)",
          "messageTemplate": "File ${filePath} was modified by ${user.name}. Reason: ${reason}",
          "channel": "IN_APP"
        }
      },
      "async": true
    }
  ],
  "implementation": {
    "type": "FUNCTION_BACKED",
    "functionRef": "lib.oda.actions.file.modify_file",
    "functionLanguage": "PYTHON",
    "functionConfig": {
      "timeout": 30000
    }
  },
  "permissions": {
    "requiredRoles": ["Developer", "Admin"],
    "objectTypePermissions": [
      {
        "objectTypeApiName": "File",
        "requiredAccess": "WRITE"
      }
    ]
  },
  "status": "ACTIVE",
  "auditConfig": {
    "enabled": true,
    "logLevel": "DETAILED",
    "includeBeforeAfter": true
  },
  "undoConfig": {
    "undoable": true,
    "undoWindowMinutes": 60,
    "undoStrategy": "RESTORE_SNAPSHOT"
  },
  "metadata": {
    "createdAt": "2026-01-17T10:00:00Z",
    "createdBy": "system",
    "version": 1,
    "tags": ["file-operations", "core"],
    "module": "file_management"
  }
}
```

---

## Palantir Alignment

### Alignment Matrix

| Aspect | Palantir Official | Our Implementation | Status |
|--------|-------------------|-------------------|--------|
| Definition | Set of changes to objects/properties/links | Matches | Aligned |
| Parameters | User inputs | Comprehensive support | Aligned |
| Affected ObjectTypes | Required, min 1 | Enforced | Aligned |
| Edit Specifications | Declarative rules | Full support | Aligned |
| Submission Criteria | Preconditions | 5 criterion types | Extended |
| Side Effects | notification, webhook | 6 effect types | Extended |
| Implementation Types | DECLARATIVE, FUNCTION_BACKED | + INLINE_EDIT | Extended |
| ENDORSED Status | NOT supported | NOT supported | Aligned |
| Function Languages | TypeScript, Python | Supported | Aligned |

### Gap Analysis Notes

| Gap | Severity | Description |
|-----|----------|-------------|
| CUSTOM_FUNCTION side effect | LOW | Extension for custom integrations |
| EMAIL side effect | LOW | Explicit type (vs notification channel) |
| INLINE_EDIT implementation | LOW | UI convenience feature |
| Extended statuses (ALPHA, BETA, SUNSET) | INFO | Extended lifecycle support |

### Validation Rules

The implementation enforces these Palantir-aligned rules:

1. **Parameter names unique:** No duplicate `apiName` in parameters
2. **DECLARATIVE requires edit specs:** At least one `editSpecification` required
3. **FUNCTION_BACKED requires function ref:** `functionRef` required
4. **OBJECT_PICKER/OBJECT_SET requires objectTypeRef:** Type reference required
5. **ARRAY requires arrayItemType:** Item type specification required
6. **INVERSE_ACTION requires inverseActionRef:** Undo action reference required

---

## API Reference

### Python Implementation

```python
from ontology_definition.types.action_type import (
    ActionType,
    ActionParameter,
    ParameterDataType,
    ParameterType,
    ParameterConstraints,
    ParameterUIHints,
    AffectedObjectType,
    ObjectOperation,
    EditSpecification,
    EditOperationType,
    PropertyMapping,
    ObjectSelection,
    ObjectSelectionType,
    LinkSelection,
    EditCondition,
    EditConditionType,
    SubmissionCriterion,
    SubmissionCriterionType,
    CriterionSeverity,
    SideEffect,
    SideEffectType,
    SideEffectConfig,
    NotificationConfig,
    WebhookConfig,
    TriggerActionConfig,
    ActionImplementation,
    ActionImplementationType,
    FunctionLanguage,
    FunctionConfig,
    ActionPermissions,
    ObjectTypePermission,
    ObjectAccessLevel,
    AuditConfig,
    AuditLogLevel,
    UndoConfig,
    UndoStrategy,
    ActionTypeStatus,
)
```

### Creating an ActionType

```python
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
            constraints=ParameterConstraints(pattern=r"^[a-zA-Z0-9/_.-]+$"),
        ),
        ActionParameter(
            api_name="content",
            display_name="New Content",
            data_type=ParameterDataType(type=ParameterType.STRING),
            required=True,
            ui_hints=ParameterUIHints(input_type=ParameterInputType.TEXTAREA),
        ),
    ],
    affected_object_types=[
        AffectedObjectType(
            object_type_api_name="File",
            operations=[ObjectOperation.MODIFY],
            modifiable_properties=["content", "modifiedAt"],
        ),
    ],
    implementation=ActionImplementation(
        type=ActionImplementationType.FUNCTION_BACKED,
        function_ref="lib.oda.actions.file.modify_file",
        function_language=FunctionLanguage.PYTHON,
    ),
    status=ActionTypeStatus.ACTIVE,
)
```

### Exporting to Foundry Format

```python
foundry_dict = modify_file_action.to_foundry_dict()
```

### Utility Methods

```python
# Get parameter by name
param = action.get_parameter("filePath")

# Get all required parameters
required_params = action.get_required_parameters()

# Check if action affects an ObjectType
affects_file = action.affects_object_type("File")  # True
```

---

## Related Documentation

- [ObjectType](./ObjectType.md) - Data structure definitions
- [LinkType](./LinkType.md) - Relationship definitions
- [Interface](./Interface.md) - Polymorphic type contracts
- [Property](./Property.md) - Attribute definitions

---

## References

1. **Palantir Foundry Documentation** - ActionType Reference
2. **Palantir AIP Documentation** - Actions and Functions
3. **JSON Schema** - `/docs/research/schemas/ActionType.schema.json`
4. **Implementation** - `ontology_definition/types/action_type.py`

---

*Last Updated: 2026-01-17*
*Schema Version: 1.0.0*
*Implementation: ontology_definition v1.0.0*
