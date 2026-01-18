---
name: oda-interaction
description: |
  Interaction rules management with 5-Stage Lifecycle Protocol.
  Schema source: ontology_definition/schemas/Interaction.schema.json
  Implements: define -> validate -> stage -> review -> deploy
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
user-invocable: false
context: fork
agent: general-purpose
intents:
  korean: ["인터랙션", "상호작용", "규칙", "연동", "캐스케이드"]
  english: ["interaction", "rules", "cascade", "referential integrity", "cross-type"]
---

# ODA Interaction Skill

## Purpose

Manage Interaction rules following 5-Stage Lifecycle:
1. **DEFINE** - Collect rule specification
2. **VALIDATE** - Verify against JSON Schema
3. **STAGE** - Preview before deployment
4. **REVIEW** - Human approval gate
5. **DEPLOY** - Persist to ontology database

**Interaction rules define HOW ObjectTypes, LinkTypes, and ActionTypes interact.**

---

## Schema Reference

**Location:** `/home/palantir/park-kyungchan/palantir/ontology_definition/schemas/Interaction.schema.json`

### Required Fields

| Field | Description |
|-------|-------------|
| `schemaVersion` | Semver (e.g., `1.0.0`) |
| `objectTypeToLinkType` | ObjectType-LinkType participation rules |
| `actionTypeToObjectType` | ActionType-ObjectType operation rules |
| `actionTypeToLinkType` | ActionType-LinkType operation rules |

### Optional Fields

| Field | Description |
|-------|-------------|
| `cascadeEffects` | Cascade on modify/delete |
| `referentialIntegrity` | FK and orphan detection |
| `securityInteractions` | Mandatory control, RV integration |
| `validationOrder` | Validation step ordering |

---

## ObjectTypeToLinkType Rules

### participationRules

```json
{
  "ruleId": "pk-rule",
  "applicableTo": "ALL_OBJECT_TYPES",
  "constraint": {
    "requiredPrimaryKeyType": "STRING",
    "selfLinkAllowed": true,
    "maxLinksAsSource": 10,
    "maxLinksAsTarget": 20
  },
  "enforcement": "STRICT"
}
```

| Option | Values |
|--------|--------|
| `applicableTo` | `ALL_OBJECT_TYPES`, `SPECIFIC_OBJECT_TYPES`, `OBJECT_TYPES_WITH_TAG` |
| `enforcement` | `STRICT`, `WARN`, `AUDIT_ONLY` |

### cardinalityEnforcement

```json
{
  "oneToOneEnforcement": "INDICATOR_ONLY",
  "oneToManyEnforcement": "STRICT",
  "manyToManyEnforcement": "STRICT",
  "minCardinalityEnforcement": "DEFERRED",
  "violationBehavior": "REJECT"
}
```

| Option | Values |
|--------|--------|
| `minCardinalityEnforcement` | `ON_CREATE`, `ON_COMMIT`, `DEFERRED`, `DISABLED` |
| `violationBehavior` | `REJECT`, `WARN_AND_ALLOW`, `AUTO_CORRECT` |

### foreignKeyRules

```json
{
  "nullForeignKeyAllowed": true,
  "orphanedForeignKeyBehavior": "REJECT",
  "indexingRequired": true,
  "typeValidation": "STRICT"
}
```

| Option | Values |
|--------|--------|
| `orphanedForeignKeyBehavior` | `REJECT`, `SET_NULL`, `CREATE_PLACEHOLDER`, `IGNORE` |

### backingTableRules (N:N)

```json
{
  "backingTableRequired": true,
  "duplicateLinkBehavior": "REJECT",
  "auditColumns": { "createdAt": true, "createdBy": true }
}
```

---

## ActionTypeToObjectType Rules

### createRules

```json
{
  "primaryKeyGeneration": "UUID",
  "requiredPropertyValidation": "IMMEDIATE",
  "mandatoryControlValidation": "IMMEDIATE",
  "auditCreation": true,
  "statusInitialization": "ACTIVE"
}
```

| Option | Values |
|--------|--------|
| `primaryKeyGeneration` | `MANUAL`, `AUTO_INCREMENT`, `UUID`, `CUSTOM_FUNCTION` |
| `requiredPropertyValidation` | `IMMEDIATE`, `ON_COMMIT`, `DEFERRED` |

### modifyRules

```json
{
  "immutablePropertyEnforcement": "STRICT",
  "versionIncrement": true,
  "optimisticLocking": true,
  "nullifyBehavior": "REJECTED_IF_REQUIRED",
  "mandatoryControlModification": "RESTRICTED"
}
```

| Option | Values |
|--------|--------|
| `mandatoryControlModification` | `ALLOWED`, `RESTRICTED`, `PROHIBITED` |

### deleteRules

```json
{
  "softDeleteEnabled": true,
  "hardDeleteAllowed": false,
  "linkedObjectBehavior": "REJECT_IF_LINKED",
  "retentionPeriod": 90,
  "statusTransition": { "required": true, "deprecationPeriodDays": 30 }
}
```

| Option | Values |
|--------|--------|
| `linkedObjectBehavior` | `REJECT_IF_LINKED`, `CASCADE_DELETE`, `UNLINK`, `ORPHAN` |

### permissionIntegration

```json
{
  "checkTiming": "BEFORE_VALIDATION",
  "resolutionOrder": ["INSTANCE", "OBJECT_TYPE", "TEAM", "ROLE", "DEFAULT"],
  "denyOverridesAllow": true
}
```

---

## ActionTypeToLinkType Rules

### linkRules

```json
{
  "existenceValidation": "STRICT",
  "cardinalityValidation": "STRICT",
  "duplicateLinkBehavior": "REJECT",
  "bidirectionalCreation": true
}
```

### unlinkRules

```json
{
  "nonExistentLinkBehavior": "IGNORE",
  "cascadeToBackingTable": true,
  "orphanProtection": true
}
```

---

## Cascade Effects Rules

```json
{
  "objectDeleteCascade": {
    "linksFromObject": "CASCADE_DELETE",
    "linksToObject": "CASCADE_DELETE",
    "nestedObjects": "CASCADE_DELETE"
  },
  "statusTransitionCascade": {
    "onDeprecate": "WARN_LINKED",
    "onArchive": "UNLINK"
  },
  "maxCascadeDepth": 5
}
```

| Option | Values |
|--------|--------|
| Cascade behavior | `CASCADE_DELETE`, `ORPHAN`, `SET_NULL`, `REJECT` |
| `onDeprecate` | `WARN_LINKED`, `DEPRECATE_LINKED`, `NO_ACTION` |

---

## Referential Integrity Rules

```json
{
  "enforcementLevel": "STRICT",
  "foreignKeyIntegrity": { "onInsert": "VALIDATE", "onUpdate": "VALIDATE" },
  "orphanDetection": { "enabled": true, "frequency": "DAILY", "action": "REPORT" },
  "circularReferenceHandling": "WARN"
}
```

| Option | Values |
|--------|--------|
| `enforcementLevel` | `STRICT`, `EVENTUAL`, `DISABLED` |
| `orphanDetection.action` | `REPORT`, `AUTO_CLEANUP`, `QUARANTINE` |

---

## Security Interaction Rules (P1-CRITICAL)

### mandatoryControlEnforcement

```json
{
  "onCreate": "REQUIRED",
  "onModify": "ALLOWED_WITH_APPROVAL",
  "inheritanceFromSource": true,
  "unionWithTarget": false
}
```

### restrictedViewIntegration

```json
{
  "filterOnRead": true,
  "filterOnWrite": true,
  "filterOnLink": true,
  "policyEvaluationOrder": ["MARKINGS", "ORGANIZATIONS", "CLASSIFICATIONS"]
}
```

### fieldLevelSecurity

```json
{
  "maskingOnRead": true,
  "hiddenPropertiesInResponse": "OMIT",
  "auditHiddenAccess": true
}
```

---

## Validation Order Rules

```json
{
  "operationValidationOrder": [
    "PERMISSION_CHECK", "SCHEMA_VALIDATION", "CONSTRAINT_VALIDATION",
    "REFERENTIAL_INTEGRITY", "CARDINALITY_CHECK", "MANDATORY_CONTROL_CHECK",
    "SUBMISSION_CRITERIA", "CUSTOM_VALIDATORS"
  ],
  "failFast": true
}
```

---

## 5-Stage Lifecycle Protocol

### Stage 1: DEFINE
- Schema version, participation rules, operation rules
- Output: `.agent/tmp/staging/<id>.json`

### Stage 2: VALIDATE
- Required fields, pattern/enum validation, cross-reference consistency
- Output: Validation report

### Stage 3: STAGE
- Generate ID, add metadata, calculate diff
- Output: `.agent/tmp/staging/<id>.staged.json`

### Stage 4: REVIEW
- Display summary, cascade/security config, diff
- Approval Prompt: [y/n]

### Stage 5: DEPLOY
- Write to DB, audit log, update registry

---

## Actions

| Action | Command | Description |
|--------|---------|-------------|
| define | `/interaction define` | Interactive creation |
| validate | `/interaction validate <file>` | Schema validation |
| stage | `/interaction stage <id>` | Stage for review |
| review | `/interaction review <id>` | Approve staged |
| deploy | `/interaction deploy <id>` | Deploy to DB |
| list | `/interaction list` | List all rules |
| show | `/interaction show <id>` | Show details |

---

## Output Formats

### Success
```json
{
  "status": "success",
  "action": "deploy",
  "interaction": { "id": "cascade-rules", "schemaVersion": "1.0.0" }
}
```

### Error
```json
{
  "status": "error",
  "errors": [{ "code": "MISSING_REQUIRED_FIELD", "path": "$.objectTypeToLinkType" }]
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| `MISSING_REQUIRED_FIELD` | Required field not present |
| `INVALID_SCHEMA_VERSION` | Version doesn't match semver |
| `INVALID_ENFORCEMENT_LEVEL` | Unknown enforcement level |
| `INVALID_CASCADE_OPTION` | Unknown cascade option |
| `CIRCULAR_CASCADE_DETECTED` | Cascade creates infinite loop |
| `APPROVAL_REQUIRED` | Deploy without approval |

---

## Database Operations

### Schema
```sql
CREATE TABLE IF NOT EXISTS interaction_rules (
    id TEXT PRIMARY KEY,
    schema_version TEXT NOT NULL,
    definition JSON NOT NULL,
    created_at TEXT NOT NULL,
    modified_at TEXT NOT NULL,
    version INTEGER DEFAULT 1
);
```

### Insert
```python
cursor.execute("""
    INSERT OR REPLACE INTO interaction_rules
    (id, schema_version, definition, created_at, modified_at, version)
    VALUES (?, ?, ?, datetime('now'), datetime('now'), 1)
""", (id, definition["schemaVersion"], json.dumps(definition)))
```

---

## Integration

| Resource | Path |
|----------|------|
| Database | `.agent/tmp/ontology.db` |
| Staging | `.agent/tmp/staging/<id>.json` |
| Audit Log | `.agent/logs/ontology_changes.log` |

### Related Skills
- `oda-objecttype`, `oda-actiontype`, `oda-linktype`

---

## Complete Example

```json
{
  "schemaVersion": "1.0.0",
  "objectTypeToLinkType": {
    "participationRules": [{
      "ruleId": "pk-rule",
      "applicableTo": "ALL_OBJECT_TYPES",
      "constraint": { "requiredPrimaryKeyType": "STRING", "selfLinkAllowed": true },
      "enforcement": "STRICT"
    }],
    "cardinalityEnforcement": {
      "oneToOneEnforcement": "INDICATOR_ONLY",
      "manyToManyEnforcement": "STRICT",
      "violationBehavior": "REJECT"
    },
    "foreignKeyRules": { "nullForeignKeyAllowed": true, "orphanedForeignKeyBehavior": "REJECT" },
    "backingTableRules": { "backingTableRequired": true, "duplicateLinkBehavior": "REJECT" }
  },
  "actionTypeToObjectType": {
    "createRules": { "primaryKeyGeneration": "UUID", "auditCreation": true },
    "modifyRules": { "immutablePropertyEnforcement": "STRICT", "optimisticLocking": true },
    "deleteRules": { "softDeleteEnabled": true, "linkedObjectBehavior": "REJECT_IF_LINKED" }
  },
  "actionTypeToLinkType": {
    "linkRules": { "existenceValidation": "STRICT", "bidirectionalCreation": true },
    "unlinkRules": { "cascadeToBackingTable": true, "orphanProtection": true }
  },
  "cascadeEffects": {
    "objectDeleteCascade": { "linksFromObject": "CASCADE_DELETE", "linksToObject": "CASCADE_DELETE" },
    "maxCascadeDepth": 5
  },
  "referentialIntegrity": {
    "enforcementLevel": "STRICT",
    "orphanDetection": { "enabled": true, "frequency": "DAILY", "action": "REPORT" }
  },
  "securityInteractions": {
    "mandatoryControlEnforcement": { "onCreate": "REQUIRED", "inheritanceFromSource": true },
    "restrictedViewIntegration": { "filterOnRead": true, "filterOnWrite": true, "filterOnLink": true }
  },
  "validationOrder": { "failFast": true }
}
```

---

## Cross-Type Patterns

### Soft Delete with Cascade
1. Check `linkedObjectBehavior` - fail if `REJECT_IF_LINKED` and links exist
2. Apply `objectDeleteCascade` rules
3. Respect `maxCascadeDepth`

### FK Integrity on Link Create
1. Validate source/target exist
2. Check cardinality constraints
3. Handle duplicates per `duplicateLinkBehavior`

### Mandatory Control Inheritance
1. `inheritanceFromSource: true` - link inherits source markings
2. `unionWithTarget: true` - requires both visible

### Deprecation Workflow
1. Check `statusTransition.required`
2. Apply `onDeprecate` cascade
3. Wait `deprecationPeriodDays` before delete

---

## Anti-Hallucination Rule

**CRITICAL:** All operations MUST reference actual files.

```python
if not evidence.get("source_file") and not evidence.get("user_input"):
    raise AntiHallucinationError("Operation without evidence source")
```

---

## TodoWrite Integration

```json
[
  {"content": "[Stage 1] Define Interaction rules", "status": "completed", "activeForm": "Defining rules"},
  {"content": "[Stage 2] Validate against schema", "status": "in_progress", "activeForm": "Validating"},
  {"content": "[Stage 3] Stage for review", "status": "pending", "activeForm": "Staging"},
  {"content": "[Stage 4] Review and approve", "status": "pending", "activeForm": "Reviewing"},
  {"content": "[Stage 5] Deploy to database", "status": "pending", "activeForm": "Deploying"}
]
```

---

## Best Practices

1. Start with **STRICT enforcement**, relax only when necessary
2. Enable **soft delete** for data recovery
3. Set reasonable **cascade depth** (5 typical)
4. Enable **orphan detection** at least for reporting
5. Always require **mandatory controls** on create
6. Use **optimistic locking** for concurrent access
7. **Audit all operations** for compliance
