---
description: |
  Create or modify ActionType definitions with 5-Stage Lifecycle.
  Implements: define -> validate -> stage -> review -> deploy
allowed-tools: Read, Grep, Glob, Bash, Task
argument-hint: <action> [options]
---

# /actiontype Command

Create and manage ActionType definitions for the ODA Ontology system.
**Schema Source:** `ontology_definition/schemas/ActionType.schema.json`

## Arguments
$ARGUMENTS - Action to perform:
- `define` - Interactive ActionType creation
- `validate <json_path>` - Validate JSON against schema
- `stage <id>` - Stage definition for review
- `review <id>` - Review and approve staged definition
- `deploy <id>` - Deploy approved definition to database
- `list` - List all ActionTypes
- `show <id>` - Show ActionType details

## Quick Usage

```bash
/actiontype define                     # Interactive mode
/actiontype validate file-modify.json  # Validate JSON file
/actiontype stage file-modify          # Stage for review
/actiontype review file-modify         # Approve staged changes
/actiontype deploy file-modify         # Deploy to database
/actiontype list                       # List all ActionTypes
/actiontype show file-modify           # Show details
```

## Delegation

```python
Skill("oda-actiontype", args="$ARGUMENTS")
```

## 5-Stage Lifecycle

| Stage | Purpose | Gate |
|-------|---------|------|
| 1. DEFINE | Collect definition | JSON structure |
| 2. VALIDATE | Schema compliance | Required fields, patterns |
| 3. STAGE | Preview changes | Diff generation |
| 4. REVIEW | Human approval | Security review (hazardous check) |
| 5. DEPLOY | Persist to DB | Audit log entry |

## Required Fields

- `id` - Lowercase with hyphens (e.g., `file-modify`, `assign-employee`)
- `apiName` - camelCase/dot notation (e.g., `file.modify`, `assignEmployee`)
- `displayName` - Human-readable name
- `affectedObjectTypes` - ObjectTypes this action affects
- `implementation` - How action is implemented (DECLARATIVE/FUNCTION_BACKED)

## Hazardous Actions

Actions marked `hazardous: true` require Proposal workflow:
- File modifications, deletions
- Database changes
- Security-sensitive operations

## Related Commands

- `/objecttype` - ObjectType definitions
- `/linktype` - LinkType definitions (relationships)
- `/property` - Property/ValueType definitions
- `/interface` - Interface definitions
