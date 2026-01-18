---
description: |
  Create or modify Interface definitions with 5-Stage Lifecycle.
  Implements: define -> validate -> stage -> review -> deploy
allowed-tools: Read, Grep, Glob, Bash, Task
argument-hint: <action> [options]
---

# /interface Command

Create and manage Interface definitions for the ODA Ontology system.
**Schema Source:** `ontology_definition/schemas/Interface.schema.json`

## Arguments
$ARGUMENTS - Action to perform:
- `define` - Interactive Interface creation
- `validate <json_path>` - Validate JSON against schema
- `stage <id>` - Stage definition for review
- `review <id>` - Review and approve staged definition
- `deploy <id>` - Deploy approved definition to database
- `list` - List all Interfaces
- `show <id>` - Show Interface details
- `implementers <id>` - List ObjectTypes implementing interface

## Quick Usage

```bash
/interface define                    # Interactive mode
/interface validate facility.json    # Validate JSON file
/interface stage facility            # Stage for review
/interface review facility           # Approve staged changes
/interface deploy facility           # Deploy to database
/interface list                      # List all Interfaces
/interface show facility             # Show details
/interface implementers facility     # Show implementing ObjectTypes
```

## Delegation

```python
Skill("oda-interface", args="$ARGUMENTS")
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

- `apiName` - Programmatic name (e.g., `facility`, `Auditable`)
- `displayName` - Human-readable name

## Key Features

- **Shared Properties** - Define common property contracts
- **Link Constraints** - Specify required relationships
- **Interface Inheritance** - Extend other interfaces via `extends`
- **Polymorphic Search** - Search all implementing ObjectTypes at once

## Related Commands

- `/objecttype` - ObjectType definitions (implements interfaces)
- `/property` - Property/SharedProperty definitions
- `/linktype` - LinkType definitions
- `/actiontype` - ActionType definitions
