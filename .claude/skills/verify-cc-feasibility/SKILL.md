---
name: verify-cc-feasibility
description: >-
  Validates CC native field compliance via cc-reference cache.
  Checks frontmatter fields against CC native field lists.
  Terminal verify stage: fourth of four sequential stages,
  gates delivery pipeline. Use after verify-quality PASS or
  after skill/agent creation or frontmatter modification. Reads
  from verify-quality routing quality confirmation and
  execution-infra frontmatter changes. Produces native
  compliance per file for delivery-pipeline on all PASS, or
  routes back to execution-infra on FAIL. On FAIL, routes file
  path + non-native field name + recommended removal to
  execution-infra. Validates skills against skill native field
  table, agents against agent native field table. Primary source:
  cc-reference cache (memory/cc-reference/native-fields.md).
  Supplementary: claude-code-guide if cache stale >30 days.
  TRIVIAL: Lead-direct on 1-2 files. STANDARD: 1 analyst
  maxTurns 25. COMPLEX: 1 analyst + claude-code-guide for
  unknown fields. DPS context: extracted frontmatter fields +
  cc-reference native field tables. Exclude L2 body content,
  non-.claude/ source files, and historical field rationale.
user-invocable: true
disable-model-invocation: true
---

# Verify — CC Feasibility

## Execution Model
- **TRIVIAL**: Lead-direct. Read frontmatter of 1-2 files, compare against native field lists. No spawn.
- **STANDARD**: Spawn analyst (maxTurns: 25). Systematic field comparison across 3-10 files.
- **COMPLEX**: Spawn analyst (maxTurns: 30) for 10+ files. Parallel claude-code-guide if cache stale or unknown fields found.

## Decision Points

### Tier Classification
Tier = number of .claude/ files with frontmatter changes since last verified state. If only L2 body changes: SKIP entirely.

| Tier | Files | Approach |
|------|-------|----------|
| TRIVIAL | 1-2 | Lead-direct inline check |
| STANDARD | 3-10 | 1 analyst with native field ref |
| COMPLEX | 10+ or unknown field | 1 analyst + claude-code-guide |

### Validation Source Priority
1. **Primary**: CC Reference Cache (`memory/cc-reference/native-fields.md`) — always check first, zero cost
2. **Supplementary**: claude-code-guide spawn — ONLY when cache stale (>30 days), field absent from cache, or CC version changed

### Field Ambiguity Decision Tree
```
Field NOT in cc-reference skill table?
├── In agent table? → FAIL: wrong file type
├── In "Non-Native" list? → FAIL: silently ignored
└── Genuinely absent?
    ├── Cache <30 days? → FAIL: not verified = non-native
    └── Cache stale → spawn claude-code-guide
        ├── Confirms native → PASS + update cache
        ├── Confirms non-native → FAIL
        └── Unavailable → FAIL conservative + WARN
```

### Skip Conditions
Skip when ALL true:
- Only L2 body changes (no frontmatter)
- Only non-.claude/ files changed
- Previous scan confirmed compliance + no new skill/agent files
- No CC version update since last verification

### Value Type Strictness
- **Default**: Strict — reject any value not matching documented type
- **Always strict for**: `model`, `permissionMode`, `context` (enum fields, no coercion)
- **Lenient**: Only when Lead explicitly passes lenient mode in DPS

## Methodology
For detailed step-by-step procedure: Read `resources/methodology.md`
For native field reference tables: Read `resources/native-field-tables.md`

Summary: Extract frontmatter → check against native tables → validate value types → resolve ambiguous fields → generate compliance report.

## Failure Handling
For D12 escalation ladder: Read `~/.claude/resources/failure-escalation-ladder.md`

Skill-specific failure rules:
- **Non-native field**: BLOCKING → route to execution-infra for removal
- **Value type mismatch**: BLOCKING → route to execution-infra for correction
- **Wrong file type field** (agent field in skill): BLOCKING → route to execution-infra
- **Cache stale + guide unavailable**: Conservative FAIL + WARN. Never PASS unverifiable fields.
- **Deprecated field**: BLOCKING → route to execution-infra with migration path

## Anti-Patterns

### DO NOT: Accept fields because they "look useful"
Only native fields are consumed by CC. `priority: high` is silently ignored. cc-reference is sole authority.

### DO NOT: Trust claude-code-guide as sole source
cc-reference cache is primary. Guide is supplementary — expensive, volatile output (/tmp), may be unavailable.

### DO NOT: Skip value type validation
Native field name with wrong value type (e.g., `model: "fast"`) silently fails. Value validation is mandatory.

### DO NOT: Auto-remove non-native fields
CC feasibility is READ-ONLY verification. Report findings only. Actual removal routes to execution-infra.

### DO NOT: Check L2 body content
Only frontmatter needs CC field validation. L2 body checking is verify-structural-content's domain.

### DO NOT: Confuse skill vs agent field tables
`tools` = native for agents, non-native for skills. `argument-hint` = native for skills, non-native for agents. Always check the correct table.

## Phase-Aware Execution
For shared protocol: Read `~/.claude/resources/phase-aware-execution.md`
This skill runs P2+ Team mode. Four-Channel Protocol applies.

## Transitions

### Receives From
| Source | Data | Format |
|--------|------|--------|
| verify-quality | Quality PASS + file list | L1: `status: PASS` |
| Direct invocation | Specific files or "full" scan | $ARGUMENTS |
| execution-infra | Changed file list | L1: modified file paths |

### Sends To
| Target | Condition | Data |
|--------|-----------|------|
| delivery-pipeline | PASS + all 4 verify stages done | L1: `status: PASS`, zero findings |
| execution-infra | FAIL with blocking findings | L1: findings[] with file/field/action |

### Re-entry After Fix
execution-infra fixes → Lead re-invokes on fixed files only → PASS → delivery-pipeline. Max 3 re-check iterations.

## Quality Gate
PASS requires ALL:
- Zero non-native fields across all files
- All native field values match expected types
- Skill/agent fields validated against correct table
- No deprecated fields detected
- cc-reference consulted (or guide if stale)
- No UNKNOWN-status fields remain

## Output

### L1
```yaml
domain: verify
skill: cc-feasibility
status: PASS|FAIL|SKIP
pt_signal: "metadata.phase_signals.p7_cc_feasibility"
signal_format: "{STATUS}|files:{total_files}|non_native:{non_native_fields}|ref:tasks/{team}/p7-cc-feasibility.md"
total_files: 0
non_native_fields: 0
value_type_errors: 0
validation_source: cache|guide|both
cache_date: "YYYY-MM-DD"
findings:
  - file: "path/to/file.md"
    field: "field_name"
    status: native|non-native|wrong-type|deprecated|unknown
    action: remove|correct|investigate
warnings: []
```

### L2
- Per-file compliance breakdown with field-level status
- Non-native field removal recommendations with file paths
- Value type corrections with current/expected values
- claude-code-guide summary (if spawned)
- cc-reference cache status and update recommendation
