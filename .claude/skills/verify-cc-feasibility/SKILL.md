---
name: verify-cc-feasibility
description: |
  Validates CC native field compliance via cc-reference cache and cc-guide verification. Checks each frontmatter field against CC native field lists. Terminal verify stage — gates delivery pipeline.

  Use when: After quality verification, need CC native compliance check before delivery.
  WHEN: After verify-quality PASS. Also after skill/agent creation or frontmatter modification.
  CONSUMES: verify-quality (routing quality confirmed), execution-infra (frontmatter changes).
  PRODUCES: L1 YAML native compliance per file, L2 field-level feedback → delivery-pipeline (all PASS) | execution-infra (FAIL: fix required).
user-invocable: true
disable-model-invocation: false
---

# Verify — CC Feasibility

## Execution Model
- **TRIVIAL**: Lead-direct. Quick field check on 1-2 files. Lead reads frontmatter inline, compares against the native field lists below. No agent spawn needed.
- **STANDARD**: Spawn analyst (maxTurns: 25) with cc-reference cache and all target frontmatter. Analyst performs systematic comparison. Lead escalates to claude-code-guide only if analyst flags ambiguous fields.
- **COMPLEX**: Spawn analyst (maxTurns: 30) for full field validation across 10+ files. Spawn claude-code-guide in parallel if any field is not in the cc-reference cache or cache is stale. Two-pass: structural field check first, then value type validation.

## Decision Points

### Tier Classification for CC Feasibility Check

| Tier | File Count | Scope | Approach | Agent Cost |
|------|-----------|-------|----------|------------|
| TRIVIAL | 1-2 files | Quick field check | Lead reads frontmatter, compares against native field lists inline | None |
| STANDARD | 3-10 files | Full compliance audit | Spawn analyst with native field reference lists and all target frontmatter | 1 analyst |
| COMPLEX | 10+ files OR new field type discovered | Deep validation with live CC verification | Spawn analyst + claude-code-guide for field verification | 1 analyst + 1 guide |

Tier is determined by the number of .claude/ files with frontmatter changes since last verified state. If only L2 body changes exist, skip entirely (see Skip Conditions below).

### Primary vs Supplementary Validation

Two validation sources exist. They serve different purposes and have different availability profiles.

**Primary: CC Reference Cache** (`memory/cc-reference/native-fields.md`)
- Always available. No agent cost. No network dependency.
- Contains verified field tables for both skills and agents with types, defaults, and notes.
- Includes known non-native field examples and flag combination semantics.
- Trustworthy when cache date is within 30 days and no CC version update has occurred.
- Lead should always consult this FIRST, even in TRIVIAL tier.

**Supplementary: claude-code-guide Agent Spawn**
- Authoritative but expensive (full agent spawn, reads CC source docs).
- Required ONLY when: (a) cc-reference cache is stale (>30 days), (b) a field is not in the cache at all (possible new CC addition), (c) CC version changed since last cache update.
- Output goes to /tmp (volatile). Lead must read immediately after task completion.
- If claude-code-guide is unavailable or returns empty, fall back to cc-reference cache verdict and document the limitation in L1 warnings.

### Field Ambiguity Decision Tree

When a field is encountered that is not obviously in the native list, follow this decision path:

```
Field extracted from frontmatter
│
├── Field in cc-reference native-fields.md skill table?
│   ├── YES → Check value type (proceed to Step 3 validation)
│   └── NO →
│       ├── Field in cc-reference native-fields.md agent table?
│       │   ├── YES → Wrong file type! Skill field in agent or vice versa → FAIL
│       │   └── NO →
│       │       ├── Field in cc-reference "Non-Native Fields" list?
│       │       │   ├── YES → Confirmed non-native → FAIL (silently ignored by CC)
│       │       │   └── NO → Field is UNKNOWN
│       │       │       ├── cc-reference cache < 30 days old?
│       │       │       │   ├── YES → FAIL (not in verified list = non-native)
│       │       │       │   └── NO → Cache stale. Spawn claude-code-guide
│       │       │       │       ├── Guide confirms native → PASS + update cache
│       │       │       │       ├── Guide confirms non-native → FAIL
│       │       │       │       └── Guide unavailable → FAIL conservative + WARN
│       │       │       └── (If field looks like recent CC addition)
│       │       │           └── Spawn claude-code-guide regardless of cache age
```

### Skip Conditions

CC feasibility verification can be skipped entirely when ALL of the following are true:
- Only L2 body changes made (no frontmatter field additions, removals, or value changes)
- Only non-.claude/ files changed (no agent/skill frontmatter affected)
- Previous full scan confirmed compliance AND no new skill/agent files were created since that scan
- No CC version update occurred since last verification

When skip conditions are met, Lead records `status: SKIP` with rationale in L1 output.

Note: Even if skip conditions are met, Lead MAY still invoke cc-feasibility if routing through the full verify domain (all 4 stages). In that case, a quick re-confirmation is cheaper than debugging a false-positive later.

### Value Type Strictness

How strict to be on field value validation:
- **Strict mode** (default): Reject any value that doesn't match documented type (e.g., `user-invocable: "yes"` instead of `true`)
- **Lenient mode**: Accept values that CC would coerce correctly (e.g., string "true" for boolean). Use only when mass-checking and deferring fixes.
- **Always strict for**: `model`, `permissionMode`, `context` (enum fields with no coercion)

Strictness is not configurable per-invocation. Always default to strict mode unless Lead explicitly passes lenient mode in the delegation prompt context.

## Methodology

### 1. Read Target Frontmatter
For each agent and skill file in scope:
- Extract all YAML frontmatter field names (everything between the `---` delimiters)
- Build field inventory per file: `{file_path: [field_name, field_name, ...]}`
- Separate files into two categories: skill files (SKILL.md) and agent files (.claude/agents/*.md)
- Record the raw field values alongside field names for Step 3 validation

Scope determination:
- If `$ARGUMENTS` contains specific file paths: check only those files
- If `$ARGUMENTS` is "full" or empty: scan all `.claude/skills/*/SKILL.md` and `.claude/agents/*.md`
- If invoked after verify-quality: use the file list from the previous verify stage output

### 2. Check Against Native Fields

**Complete Native Field List for Skills (SKILL.md)**:

| Field | Type | Required | Default | Valid Values |
|-------|------|----------|---------|-------------|
| `name` | string | no | directory name | Lowercase, numbers, hyphens. Max 64 chars |
| `description` | string | recommended | none | Multi-line via YAML `\|`. Max 1024 chars |
| `argument-hint` | string | no | none | Free text, e.g., `[topic]`, `[file] [format]` |
| `user-invocable` | boolean | no | true | `true` or `false` only |
| `disable-model-invocation` | boolean | no | false | `true` or `false` only |
| `allowed-tools` | list | no | all | Array of CC tool registry names |
| `model` | enum | no | inherit | `sonnet`, `opus`, `haiku`, `inherit` |
| `context` | enum | no | none | `fork` (DANGER: replaces agent body with skill L2) |
| `agent` | string | no | general-purpose | Must match an existing agent name exactly |
| `hooks` | object | no | none | Skill-scoped hook configuration object |

**Complete Native Field List for Agents (.claude/agents/*.md)**:

| Field | Type | Required | Default | Valid Values |
|-------|------|----------|---------|-------------|
| `name` | string | yes | none | Agent identifier for subagent_type matching |
| `description` | string | yes | none | Free text. No enforced length limit (unlike skill 1024) |
| `tools` | list | no | all | Explicit allowlist of CC tool registry names |
| `disallowedTools` | list | no | none | Denylist of tool names. Ignored if `tools` is set |
| `model` | enum | no | inherit | `sonnet`, `opus`, `haiku` (aliases to latest) |
| `permissionMode` | enum | no | default | `default`, `acceptEdits`, `delegate`, `dontAsk`, `bypassPermissions`, `plan` |
| `maxTurns` | number | no | unlimited | Positive integer. One turn = one agentic loop iteration |
| `skills` | list | no | none | Array of skill names. Full L1+L2 injected at agent startup |
| `mcpServers` | list | no | none | MCP server access configuration |
| `hooks` | object | no | none | Agent-scoped hooks (cleaned up when agent finishes) |
| `memory` | enum | no | none | `user`, `project`, `local` |
| `color` | string | no | none | UI color coding string |

**Known Non-Native Fields (silently ignored by CC)**:
- `input_schema` -- was used in 12 skills before v10.2, removed
- `confirm` -- was used in 3 skills before v10.2, removed
- `once` -- was used in pt-manager before v10.5, removed
- `priority`, `weight` -- no native priority mechanism exists
- `working_dir`, `timeout`, `env` -- shell-like fields, not consumed by CC
- `routing`, `meta_cognition`, `ontology_lens` -- custom metadata blocks, ignored
- `context-dependent`, `closed_loop` -- custom protocol fields, ignored
- Any key not in the tables above is non-native and silently ignored

Flag any field NOT in the skill or agent tables above as non-native. Ensure you are checking against the correct table for the file type (skill fields for SKILL.md, agent fields for agent .md files).

For STANDARD/COMPLEX tiers, construct the DPS delegation prompt for each analyst:
- **Context**: All frontmatter fields extracted from target files. Include the full native field tables above. Include the known non-native field list. Include the cc-reference cache path for the analyst to read directly.
- **Task**: "Compare each extracted field against the native field lists. Flag any field NOT in the native list as non-native. For each native field, validate value type correctness (booleans, enums, strings, lists). If questionable fields found: read cc-reference cache at `memory/cc-reference/native-fields.md` for latest reference. Report per-file status."
- **Constraints**: Read-only analysis. No file modifications. Use cc-reference cache as primary validation source (NOT claude-code-guide spawn -- that is Lead's decision, not the analyst's). Do not remove or rename fields. Do not check L2 body content.
- **Expected Output**: L1 YAML with `non_native_fields` count, `findings[]` array (file, field, status, reason). L2 markdown compliance report with per-file breakdown.
- **Delivery**: Upon completion, send L1 summary to Lead via SendMessage. Include: status (PASS/FAIL), files changed count, key metrics. L2 detail stays in agent context.

### 3. Validate Field Values

For each native field found in Step 2, validate the value matches the expected type:

**Skill Field Value Validation**:

| Field | Expected Type | Validation Rule | Common Errors |
|-------|--------------|-----------------|---------------|
| `name` | string | Lowercase, numbers, hyphens only. Max 64 chars. | Spaces, uppercase, underscores |
| `description` | string | Multi-line via `\|`. Max 1024 chars total. | Exceeding 1024 causes L1 truncation |
| `argument-hint` | string | Free text hint shown in UI. | None common |
| `user-invocable` | boolean | `true` or `false` only. | `"yes"`, `"no"`, `1`, `0` |
| `disable-model-invocation` | boolean | `true` or `false` only. | `"true"` (string), `enabled` |
| `allowed-tools` | list | Array of valid tool names. | Single string instead of list |
| `model` | enum | One of: `sonnet`, `opus`, `haiku`, `inherit`. | `"fast"`, `"claude-3"`, version numbers |
| `context` | enum | Only valid value: `fork`. | `"shared"`, `"isolated"`, other strings |
| `agent` | string | Must match an existing `.claude/agents/*.md` name. | Typo in agent name, deleted agent |
| `hooks` | object | Valid hook event keys (PreToolUse, PostToolUse, etc.). | String instead of object |

**Agent Field Value Validation**:

| Field | Expected Type | Validation Rule | Common Errors |
|-------|--------------|-----------------|---------------|
| `name` | string | Agent identifier. Must be unique across agents. | Duplicate names |
| `description` | string | Free text. Used in Task tool L1. | None common |
| `tools` | list | Array of CC tool registry names. | Invalid tool name |
| `disallowedTools` | list | Array of CC tool registry names. | Setting both tools + disallowedTools (tools wins) |
| `model` | enum | One of: `sonnet`, `opus`, `haiku`. | `inherit` (not valid for agents per docs) |
| `permissionMode` | enum | One of: `default`, `acceptEdits`, `delegate`, `dontAsk`, `bypassPermissions`, `plan`. | `plan` blocks MCP tools (BUG-001) |
| `maxTurns` | number | Positive integer. | String, negative, zero |
| `skills` | list | Array of existing skill names. | Non-existent skill name |
| `mcpServers` | list | Array of MCP server configs. | None common |
| `hooks` | object | Valid hook event structure. | String instead of object |
| `memory` | enum | One of: `user`, `project`, `local`. | `"none"`, `true`, path string |
| `color` | string | Color identifier string. | None common |

### 4. Validate Questionable Fields
If any questionable fields are found (not clearly native or non-native):

1. **Primary check**: Read `memory/cc-reference/native-fields.md` for field validity. The cc-reference cache is the most reliable and always-available source. Check both the skill and agent sections.
2. **Cross-reference check**: If the field exists in the OTHER table (e.g., agent field used in a skill file), flag as "wrong file type" rather than "non-native." This is a different category of error.
3. **Supplementary check**: If cc-reference cache is stale (>30 days) or field is genuinely absent from all tables, analyst sends compliance verdict via SendMessage including the ambiguous field details. Lead escalates to claude-code-guide only if verdict includes ambiguous fields.
4. **Record verdict**: For each questionable field, record one of: NATIVE (confirmed), NON_NATIVE (confirmed), WRONG_FILE_TYPE (agent field in skill or vice versa), UNKNOWN (could not verify).

If claude-code-guide is spawned by Lead:
- Prompt: "Is the frontmatter field `{field_name}` valid for Claude Code {skills|agents}? Check current CC documentation."
- If guide confirms native: PASS the field, and flag cc-reference cache for update via execution-infra.
- If guide confirms non-native: FAIL the field.
- If guide is unavailable (spawn failure, empty output): Conservative FAIL with WARN annotation. Do NOT mark as PASS.

### 5. Generate Compliance Report
Produce per-file compliance status:
- **PASS**: All fields are native, all values are correct types, no warnings.
- **FAIL**: Non-native fields found, value type mismatches found, or unverifiable fields present. List each finding with file path, field name, current value, expected type/status, and recommended action.
- **SKIP**: Skip conditions met (no frontmatter changes). Include rationale.

The compliance report must clearly separate:
- Non-native field findings (blocking -- must be removed before delivery)
- Value type mismatch findings (blocking -- must be corrected before delivery)
- Warning-level findings (non-blocking -- cache staleness, unverifiable fields)

Aggregate verdict: PASS only if zero blocking findings across all files.

## Failure Handling

### Failure Summary Table

| Failure Type | Severity | Action | Route To | Pipeline Impact |
|-------------|----------|--------|----------|----------------|
| Non-native field detected | BLOCKING | FAIL with file/field/evidence | execution-infra (removal) | Blocks delivery until removed |
| Field value type mismatch | BLOCKING | FAIL with file/field/current/expected | execution-infra (correction) | Blocks delivery until corrected |
| Wrong file type (agent field in skill) | BLOCKING | FAIL with migration guidance | execution-infra (removal or relocation) | Blocks delivery until resolved |
| cc-reference cache stale | WARNING | Spawn claude-code-guide for live check | Lead (escalation decision) | Non-blocking if guide confirms |
| cc-reference cache missing | WARNING | Spawn claude-code-guide as sole source | Lead (escalation decision) | Non-blocking if guide confirms |
| claude-code-guide unavailable | WARNING | Fall back to cache verdict | Lead (manual assessment) | Non-blocking if cache available |
| Both cache and guide unavailable | BLOCKING | FAIL with "unable to validate" | Lead (manual assessment) | Blocks until validation source restored |
| Deprecated field discovered | BLOCKING | FAIL with migration path | execution-infra (replacement) | Blocks delivery until migrated |

### Detailed Failure Protocols

**Non-Native Field Detected**
- Cause: Custom field added to skill or agent frontmatter (e.g., `input_schema`, `confirm`, `once`, `priority`)
- Action: FAIL with specific file path, field name, and evidence. Route to execution-infra for removal.
- Never proceed with non-native fields in place. They are silently ignored by CC, creating a false sense of configuration. The field appears to do something but has zero runtime effect.

**Field Value Type Mismatch**
- Cause: Native field used with wrong value type (e.g., `disable-model-invocation: "yes"` instead of `true`)
- Action: FAIL with file path, field, current value, and expected type. Route to execution-infra for correction.
- Note: Some mismatches cause silent failures (field ignored), others cause YAML parse errors. Boolean fields are especially prone to string/boolean confusion.

**CC Reference Cache Stale or Missing**
- Cause: `memory/cc-reference/native-fields.md` doesn't exist, is empty, or has a verification date >30 days old
- Action: Spawn claude-code-guide for fresh field validation. After verification, route cache update to execution-infra.
- Never mark unverifiable fields as PASS. If both cache and guide are unavailable, mark as UNKNOWN and escalate to Lead.

**claude-code-guide Agent Unavailable**
- Cause: claude-code-guide agent failed to spawn or returned empty output (output goes to /tmp, may be cleaned)
- Action: Fall back to cc-reference cache as sole validation source. If cache is also unavailable, FAIL with "unable to validate" and route to Lead for manual assessment.
- Report: Include which specific fields could not be verified in L1 `warnings[]` array.

**Deprecated Field Discovered**
- Cause: Field was previously native but has been removed from CC (discovered via claude-code-guide or updated cache)
- Action: FAIL with deprecation details and migration path. Route to execution-infra for replacement or removal.

## Anti-Patterns

### DO NOT: Accept Fields Just Because They Look Useful
Only native fields are consumed by the CC runtime. A field like `priority: high` or `context-dependent: true` looks intentional but is silently ignored. The cc-reference native field list is the sole authority, not intuition about what CC "should" support.

### DO NOT: Trust claude-code-guide as Sole Authority
The cc-reference cache is the primary validation source. claude-code-guide is supplementary -- it is expensive (full agent spawn), its output is volatile (/tmp), and it may be unavailable. Never skip the cache check and go straight to guide.

### DO NOT: Skip Field Value Type Validation
Checking field names alone is insufficient. A native field with the wrong value type (e.g., `model: "fast"` when valid values are sonnet/opus/haiku) silently fails or produces unexpected behavior. Step 3 value validation is mandatory even when all field names are confirmed native.

### DO NOT: Auto-Remove Non-Native Fields
CC feasibility is a read-only verification skill. Removing fields during verification mixes assessment with modification and risks unintended side effects. The analyst must only report findings. Actual removal is routed to execution-infra with specific removal instructions.

### DO NOT: Check L2 Body Content for CC Compliance
L2 body is free-form markdown. Only frontmatter (YAML between `---` markers) needs CC native field validation. Checking L2 content for CC compliance is verify-structural-content's domain, not cc-feasibility's.

### DO NOT: Confuse Skill Frontmatter Fields with Agent Frontmatter Fields
Skills and agents have DIFFERENT native field lists. A field like `tools` is native for agents but non-native for skills. A field like `argument-hint` is native for skills but non-native for agents. Always check against the correct table for the file type. Misidentifying which table to use is a common source of false positives and false negatives.

## Transitions

### Receives From

| Source Skill | Trigger Condition | Data Expected | Format |
|-------------|-------------------|---------------|--------|
| verify-quality | Quality check PASS, routing to final verify stage | Routing quality confirmed, file list from previous stages | L1 YAML: `status: PASS`, quality scores per skill |
| Direct invocation | User runs `/verify-cc-feasibility` or Lead routes directly | Specific files or "full" scan | File paths via $ARGUMENTS or "full" for all .claude/ files |
| execution-infra | After infra changes that modified frontmatter | Changed file list from implementation | L1 YAML: modified file paths |

### Sends To

| Target Skill | Trigger Condition | Data Produced | Format |
|-------------|-------------------|---------------|--------|
| delivery-pipeline | PASS verdict AND all 4 verify stages complete | Full verify domain PASS confirmation | L1 YAML: `status: PASS`, zero findings |
| execution-infra | FAIL verdict with blocking findings | Non-native field removal or value fix requests | L1 YAML: findings[] with file/field/action |

### Failure Routes

| Failure Type | Route To | Data Passed | Expected Response |
|-------------|----------|-------------|-------------------|
| Non-native field detected | execution-infra | File path, field name, recommended action (remove) | Field removed from frontmatter |
| Field value type mismatch | execution-infra | File path, field, current value, expected type | Value corrected to valid type |
| Wrong file type field | execution-infra | File path, field, which table it belongs to | Field removed (or file restructured) |
| CC reference unavailable | Lead (manual assessment) | List of unverifiable fields with file locations | Lead decides: retry, manual check, or accept risk |
| Deprecated field found | execution-infra | File path, field, deprecation details, migration path | Field replaced with current equivalent |

### Re-entry After Fix

After execution-infra completes fixes routed from cc-feasibility:
- Lead re-invokes cc-feasibility on the specific fixed files (not full scan)
- If PASS on re-check: proceed to delivery-pipeline (if all 4 verify stages done)
- If FAIL on re-check: route back to execution-infra (max 3 iterations per pipeline rules)
- After 3 failed iterations: escalate to Lead for manual intervention

## Quality Gate

CC feasibility verification PASSES only when ALL of the following are true:
- Zero non-native fields detected across all checked files
- All native field values match their expected types (per Step 3 validation tables)
- Skill fields validated against the skill native field table (not agent table)
- Agent fields validated against the agent native field table (not skill table)
- No deprecated or removed fields detected
- cc-reference cache was consulted (or claude-code-guide if cache was stale)
- No UNKNOWN-status fields remain (all resolved to NATIVE or NON_NATIVE)

Quality gate FAILS if ANY of the following are true:
- One or more non-native fields exist in any file
- One or more native fields have incorrect value types
- Any field could not be verified (UNKNOWN status) and guide was unavailable
- A deprecated field is present without a migration path applied

## Output

### L1
```yaml
domain: verify
skill: cc-feasibility
status: PASS|FAIL|SKIP
total_files: 0
non_native_fields: 0
value_type_errors: 0
validation_source: cache|guide|both
cache_date: "YYYY-MM-DD"
findings:
  - file: "path/to/file.md"
    field: "field_name"
    status: native|non-native|wrong-type|deprecated|unknown
    current_value: "..."
    expected: "type or valid values"
    action: remove|correct|investigate
warnings:
  - "cc-reference cache older than 30 days"
  - "claude-code-guide unavailable for field X"
```

### L2
- Executive summary: total files checked, pass/fail counts, validation source used
- Per-file compliance breakdown with field-level status
- Non-native field removal recommendations with specific file paths
- Value type correction recommendations with current and expected values
- claude-code-guide validation summary (if spawned): fields queried, verdicts received
- cc-reference cache status: date, staleness assessment, update recommendation
- Skip justification (if status is SKIP): which conditions were met
