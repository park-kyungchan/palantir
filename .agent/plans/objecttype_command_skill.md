# Plan: /objecttype Command and oda-objecttype Skill

> **Version:** 1.0 | **Status:** IN_PROGRESS | **Date:** 2026-01-18
> **Auto-Compact Safe:** This file persists across context compaction

## Overview
| Item | Value |
|------|-------|
| Complexity | medium |
| Total Tasks | 4 |
| Files Affected | 2 |

## Requirements
1. Create `/objecttype` command as thin wrapper (~60 lines)
2. Create `oda-objecttype` skill with full implementation
3. Implement 5-Stage Lifecycle: define → validate → stage → review → deploy
4. Use ObjectType.schema.json for validation rules

## Schema Analysis: ObjectType.schema.json

### Required Fields
- `id`: Unique identifier (pattern: `^[a-z][a-z0-9-]*$`)
- `apiName`: Programmatic identifier (pattern: `^[a-zA-Z][a-zA-Z0-9_]*$`)
- `displayName`: Human-friendly name
- `primaryKey`: Property that uniquely identifies instances
- `properties`: Array of PropertyReference definitions

### Key $defs (Validation Reference)
- `PropertyReference`: Inline property definitions
- `DataType`: 23 base types including STRUCT, ARRAY, VECTOR
- `PropertyConstraints`: Validation rules (required, unique, enum, etc.)
- `SecurityConfig`: Mandatory control properties, row-level security
- `ObjectTypeStatus`: experimental | active | deprecated | example

### Conditional Validation
- If `status === "deprecated"` → `deprecation` required

## Tasks
| # | Phase | Task | Status |
|---|-------|------|--------|
| 1 | Plan | Analyze existing patterns | ✅ completed |
| 2 | Execute | Create objecttype.md command | ⏳ pending |
| 3 | Execute | Create oda-objecttype.md skill | ⏳ pending |
| 4 | Verify | Validate file creation | ⏳ pending |

## Progress Tracking
| Phase | Tasks | Completed | Status |
|-------|-------|-----------|--------|
| Plan | 1 | 1 | ✅ |
| Execute | 2 | 0 | ⏳ |
| Verify | 1 | 0 | ⏳ |

## Quick Resume After Auto-Compact

If context is compacted, resume by:

1. Read this file: `.agent/plans/objecttype_command_skill.md`
2. Check TodoWrite for current task status
3. Continue from first PENDING task in sequence
4. Use subagent delegation pattern from "Execution Strategy" section

## Execution Strategy

### Parallel Execution Groups
- Group 1: Create command file (objecttype.md)
- Group 2: Create skill file (oda-objecttype.md)
- Both can be created in parallel by same general-purpose subagent

### Subagent Delegation
| Task Group | Subagent Type | Context | Budget |
|------------|---------------|---------|--------|
| File Creation | general-purpose | fork | 15K tokens |

## Critical File Paths
```yaml
schema_source: /home/palantir/park-kyungchan/palantir/ontology_definition/schemas/ObjectType.schema.json
command_target: /home/palantir/.claude/commands/objecttype.md
skill_target: /home/palantir/.claude/skills/oda-objecttype.md
pattern_reference_cmd: /home/palantir/.claude/commands/audit.md
pattern_reference_skill: /home/palantir/.claude/skills/oda-audit.md
```

## 5-Stage Lifecycle Design

### Stage 1: DEFINE
- Collect ObjectType definition from user
- Support both interactive and JSON input modes
- Fields: id, apiName, displayName, description, properties

### Stage 2: VALIDATE
- JSON Schema validation against ObjectType.schema.json
- Pattern validation (id, apiName formats)
- Required field checks
- Conditional validation (deprecated → deprecation required)

### Stage 3: STAGE
- Preview the ObjectType definition
- Show what will be created/modified
- Generate unique RID if not provided

### Stage 4: REVIEW
- Human approval gate
- Show diff if modifying existing ObjectType
- Security config review for mandatory controls

### Stage 5: DEPLOY
- Write to ontology database
- Create audit log entry
- Update registry

## Agent Registry (Auto-Compact Resume)

| Task | Agent ID | Status | Resume Eligible |
|------|----------|--------|-----------------|
| File Creation | pending | pending | No |
