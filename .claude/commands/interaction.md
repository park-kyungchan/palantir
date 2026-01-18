---
description: |
  Create or modify Interaction rules with 5-Stage Lifecycle.
  Implements: define -> validate -> stage -> review -> deploy
allowed-tools: Read, Grep, Glob, Bash, Task
argument-hint: <action> [options]
---

# /interaction Command

Create and manage Interaction rules for the ODA Ontology system.
**Schema Source:** `ontology_definition/schemas/Interaction.schema.json`

## Arguments
$ARGUMENTS - Action to perform:
- `define` - Interactive Interaction rule creation
- `validate <json_path>` - Validate JSON against schema
- `stage <id>` - Stage definition for review
- `review <id>` - Review and approve staged definition
- `deploy <id>` - Deploy approved definition to database
- `list` - List all Interaction rules
- `show <id>` - Show Interaction rule details

## Quick Usage

```bash
/interaction define                    # Interactive mode
/interaction validate cascade.json     # Validate JSON file
/interaction stage cascade-rules       # Stage for review
/interaction review cascade-rules      # Approve staged changes
/interaction deploy cascade-rules      # Deploy to database
/interaction list                      # List all Interactions
/interaction show cascade-rules        # Show details
```

## Delegation

```python
Skill("oda-interaction", args="$ARGUMENTS")
```

## 5-Stage Lifecycle

| Stage | Purpose | Gate |
|-------|---------|------|
| 1. DEFINE | Collect rule definition | JSON structure |
| 2. VALIDATE | Schema compliance | Required fields, patterns |
| 3. STAGE | Preview changes | Diff generation |
| 4. REVIEW | Human approval | Security review |
| 5. DEPLOY | Persist to DB | Audit log entry |

## Required Fields

- `schemaVersion` - Semantic version (e.g., `1.0.0`)
- `objectTypeToLinkType` - Rules for ObjectType-LinkType interactions
- `actionTypeToObjectType` - Rules for ActionType-ObjectType operations
- `actionTypeToLinkType` - Rules for ActionType-LinkType operations

## Related Commands

- `/objecttype` - ObjectType definitions
- `/actiontype` - ActionType definitions
- `/linktype` - LinkType definitions (relationships)
- `/property` - Property/ValueType definitions
