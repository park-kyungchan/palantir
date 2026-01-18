---
description: |
  Create or modify ObjectType definitions with 5-Stage Lifecycle.
  Implements: define -> validate -> stage -> review -> deploy
allowed-tools: Read, Grep, Glob, Bash, Task
argument-hint: <action> [options]
---

# /objecttype Command

Create and manage ObjectType definitions for the ODA Ontology system.
**Schema Source:** `ontology_definition/schemas/ObjectType.schema.json`

## Arguments
$ARGUMENTS - Action to perform:
- `define` - Interactive ObjectType creation
- `validate <json_path>` - Validate JSON against schema
- `stage <id>` - Stage definition for review
- `review <id>` - Review and approve staged definition
- `deploy <id>` - Deploy approved definition to database
- `list` - List all ObjectTypes
- `show <id>` - Show ObjectType details

## Quick Usage

```bash
/objecttype define                    # Interactive mode
/objecttype validate employee.json    # Validate JSON file
/objecttype stage employee            # Stage for review
/objecttype review employee           # Approve staged changes
/objecttype deploy employee           # Deploy to database
/objecttype list                      # List all ObjectTypes
/objecttype show employee             # Show details
```

## Delegation

```python
Skill("oda-objecttype", args="$ARGUMENTS")
```

## 5-Stage Lifecycle

| Stage | Purpose | Gate |
|-------|---------|------|
| 1. DEFINE | Collect definition | JSON structure |
| 2. VALIDATE | Schema compliance | Required fields, patterns |
| 3. STAGE | Preview changes | Diff generation |
| 4. REVIEW | Human approval | Security review |
| 5. DEPLOY | Persist to DB | Audit log entry |

## Required Fields

- `id` - Lowercase with hyphens (e.g., `employee`, `flight-log`)
- `apiName` - PascalCase (e.g., `Employee`, `FlightLog`)
- `displayName` - Human-readable name
- `primaryKey` - Property reference for unique ID
- `properties` - At least one property definition

## Related Commands

- `/actiontype` - ActionType definitions
- `/linktype` - LinkType definitions (relationships)
- `/property` - Property/ValueType definitions
- `/interface` - Interface definitions
