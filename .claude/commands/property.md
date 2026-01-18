---
description: |
  Create or modify Property definitions with 5-Stage Lifecycle.
  Supports: SharedProperty, ValueType, StructType
  Implements: define -> validate -> stage -> review -> deploy
allowed-tools: Read, Grep, Glob, Bash, Task
argument-hint: <action> [options]
---

# /property Command

Create and manage Property definitions for the ODA Ontology system.
**Schema Source:** `ontology_definition/schemas/Property.schema.json`

## Arguments
$ARGUMENTS - Action to perform:
- `define <type>` - Interactive creation (sharedproperty|valuetype|structtype)
- `validate <json_path>` - Validate JSON against schema
- `stage <id>` - Stage definition for review
- `review <id>` - Review and approve staged definition
- `deploy <id>` - Deploy approved definition to database
- `list [type]` - List properties (optionally filter by type)
- `show <id>` - Show Property details

## Quick Usage

```bash
/property define sharedproperty       # Define SharedProperty
/property define valuetype            # Define ValueType (e.g., Email)
/property define structtype           # Define StructType (e.g., Address)
/property validate email.json         # Validate JSON file
/property stage email-address         # Stage for review
/property review email-address        # Approve staged changes
/property deploy email-address        # Deploy to database
/property list valuetype              # List ValueTypes only
/property show created-at             # Show details
```

## Delegation

```python
Skill("oda-property", args="$ARGUMENTS")
```

## 5-Stage Lifecycle

| Stage | Purpose | Gate |
|-------|---------|------|
| 1. DEFINE | Collect definition | JSON structure |
| 2. VALIDATE | Schema compliance | Required fields, patterns |
| 3. STAGE | Preview changes | Diff generation |
| 4. REVIEW | Human approval | Security review |
| 5. DEPLOY | Persist to DB | Audit log entry |

## Property Types

| Type | Purpose | Example |
|------|---------|---------|
| `SharedProperty` | Reusable across ObjectTypes | `createdAt`, `securityMarkings` |
| `ValueType` | Custom constrained types | `EmailAddress`, `PhoneNumber` |
| `StructType` | Complex nested structures | `Address`, `MonetaryAmount` |

## Related Commands

- `/objecttype` - ObjectType definitions
- `/actiontype` - ActionType definitions
- `/linktype` - LinkType definitions (relationships)
- `/interface` - Interface definitions
