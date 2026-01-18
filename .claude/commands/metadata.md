---
description: |
  Create or modify Metadata definitions with 5-Stage Lifecycle.
  Polymorphic schema with 5 $type variants: OntologyMetadata, AuditLog, ChangeSet, ExportMetadata, ProposalMetadata.
  Implements: classify -> define -> validate -> stage -> review -> deploy
allowed-tools: Read, Grep, Glob, Bash, Task
argument-hint: <action> [options]
---

# /metadata Command

Create and manage Metadata definitions for the ODA Ontology system.
**Schema Source:** `ontology_definition/schemas/Metadata.schema.json`

## Arguments
$ARGUMENTS - Action to perform:
- `define` - Interactive Metadata creation (auto-classifies $type)
- `define <$type>` - Create specific variant (OntologyMetadata, AuditLog, etc.)
- `validate <json_path>` - Validate JSON against schema
- `stage <id>` - Stage definition for review
- `review <id>` - Review and approve staged definition
- `deploy <id>` - Deploy approved definition to database
- `list [<$type>]` - List Metadata entries (optional type filter)
- `show <id>` - Show Metadata details
- `rollback <changeSetId>` - Rollback a ChangeSet
- `transition <proposalId> <status>` - Transition ProposalMetadata FSM

## Quick Usage

```bash
/metadata define                          # Interactive (auto-classify)
/metadata define OntologyMetadata         # Define ontology metadata
/metadata define AuditLog                 # Create audit log entry
/metadata define ChangeSet                # Create change set (batch)
/metadata define ExportMetadata           # Define export metadata
/metadata define ProposalMetadata         # Create proposal workflow
/metadata validate audit.json             # Validate JSON file
/metadata stage meta-001                  # Stage for review
/metadata review meta-001                 # Approve staged changes
/metadata deploy meta-001                 # Deploy to database
/metadata list                            # List all metadata
/metadata list AuditLog                   # List only audit logs
/metadata show meta-001                   # Show details
/metadata rollback cs-001                 # Rollback change set
/metadata transition prop-001 APPROVED    # FSM transition
```

## Delegation

```python
Skill("oda-metadata", args="$ARGUMENTS")
```

## 6-Stage Lifecycle (Extended)

| Stage | Purpose | Gate |
|-------|---------|------|
| 0. CLASSIFY | Determine $type variant | User intent mapping |
| 1. DEFINE | Collect specification | $type-specific fields |
| 2. VALIDATE | Schema compliance | Discriminator + variant rules |
| 3. STAGE | Preview changes | Diff generation |
| 4. REVIEW | Human approval | Security review |
| 5. DEPLOY | Persist to DB | Audit log entry |

## $type Variants

| Variant | Use Case | Key Fields |
|---------|----------|------------|
| `OntologyMetadata` | Ontology version info | apiName, schemaVersion, stats |
| `AuditLog` | Operation tracking | operationType (12 types), actor, target |
| `ChangeSet` | Batch changes | operations[], rollbackInfo |
| `ExportMetadata` | Export format | exportScope, includedTypes, checksums |
| `ProposalMetadata` | Approval workflow | status (7-state FSM), history[] |

## Related Commands

- `/objecttype` - ObjectType definitions
- `/actiontype` - ActionType definitions
- `/linktype` - LinkType definitions (relationships)
- `/property` - Property/ValueType definitions
- `/interface` - Interface definitions
