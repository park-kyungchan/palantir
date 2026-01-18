---
description: |
  Create or modify LinkType definitions with 5-Stage Lifecycle.
  Implements: define -> validate -> stage -> review -> deploy
allowed-tools: Read, Grep, Glob, Bash, Task
argument-hint: <action> [options]
---

# /linktype Command

Create and manage LinkType definitions for ODA Ontology relationships.
**Schema Source:** `ontology_definition/schemas/LinkType.schema.json`

## Arguments
$ARGUMENTS - Action to perform:
- `define` - Interactive LinkType creation
- `validate <json_path>` - Validate JSON against schema
- `stage <id>` - Stage definition for review
- `review <id>` - Review and approve staged definition
- `deploy <id>` - Deploy approved definition to database
- `list` - List all LinkTypes
- `show <id>` - Show LinkType details

## Quick Usage

```bash
/linktype define                         # Interactive mode
/linktype validate employee-dept.json    # Validate JSON file
/linktype stage employee-department      # Stage for review
/linktype review employee-department     # Approve staged changes
/linktype deploy employee-department     # Deploy to database
/linktype list                           # List all LinkTypes
/linktype show employee-department       # Show details
```

## Delegation

```python
Skill("oda-linktype", args="$ARGUMENTS")
```

## 5-Stage Lifecycle

| Stage | Purpose | Gate |
|-------|---------|------|
| 1. DEFINE | Collect definition | JSON structure |
| 2. VALIDATE | Schema compliance | Source/Target ObjectTypes, Cardinality |
| 3. STAGE | Preview changes | Diff generation |
| 4. REVIEW | Human approval | Security review |
| 5. DEPLOY | Persist to DB | Audit log entry |

## Required Fields

- `id` - Lowercase with hyphens (e.g., `employee-department`)
- `apiName` - PascalCase (e.g., `EmployeeToDepartment`)
- `displayName` - Human-readable name
- `sourceObjectType` - Reference to source ObjectType
- `targetObjectType` - Reference to target ObjectType
- `cardinality` - Relationship type (ONE_TO_ONE, ONE_TO_MANY, etc.)
- `implementation` - FOREIGN_KEY or BACKING_TABLE

## Related Commands

- `/objecttype` - ObjectType definitions
- `/actiontype` - ActionType definitions
- `/property` - Property/ValueType definitions
- `/interface` - Interface definitions
