---
name: verify-cc-feasibility
description: |
  [P8·Verify·CCFeasibility] Claude Code native compliance verifier. Ensures all frontmatter uses ONLY CC native fields, no custom fields exist, and validates via claude-code-guide agent spawn.

  WHEN: After every skill/agent creation or frontmatter modification. Fifth and final verification stage. Can run independently.
  DOMAIN: verify (skill 5 of 5). Terminal skill in verify domain. After verify-quality PASS.
  INPUT_FROM: verify-quality (routing quality confirmed) or direct invocation.
  OUTPUT_TO: delivery-pipeline (if all 5 stages PASS) or execution-infra (if FAIL, frontmatter fix required).

  METHODOLOGY: (1) Read target frontmatter fields, (2) Check against CC native field lists for skills and agents (see L2 body for full lists), (3) Flag any non-native field, (4) Spawn claude-code-guide to validate questionable fields, (5) Return compliance verdict with per-file status.
  OUTPUT_FORMAT: L1 YAML native compliance per file, L2 markdown feasibility report with field-level feedback.
user-invocable: true
disable-model-invocation: false
---

# Verify — CC Feasibility

## Execution Model
- **TRIVIAL**: Lead-direct. Quick field check on 1-2 files.
- **STANDARD**: Spawn analyst with claude-code-guide research.
- **COMPLEX**: Spawn 2 analysts. One for field validation, one for claude-code-guide verification.

## Methodology

### 1. Read Target Frontmatter
For each agent and skill file:
- Extract all YAML frontmatter field names
- Build field inventory per file

### 2. Check Against Native Fields
Allowed native fields for **Skills** (SKILL.md):
- `name`, `description`, `argument-hint`
- `user-invocable`, `disable-model-invocation`
- `allowed-tools`, `model`, `context`, `agent`, `hooks`

Allowed native fields for **Agents** (.claude/agents/*.md):
- `name`, `description`, `tools`, `disallowedTools`
- `model`, `permissionMode`, `maxTurns`
- `skills`, `mcpServers`, `hooks`, `memory`, `color`

Flag any field NOT in these lists as non-native.

For STANDARD/COMPLEX tiers, construct the delegation prompt for each analyst with:
- **Context**: All frontmatter fields extracted from target files. Include the CC native field reference lists (Skills: name, description, argument-hint, user-invocable, disable-model-invocation, allowed-tools, model, context, agent, hooks. Agents: name, description, tools, disallowedTools, model, permissionMode, maxTurns, skills, mcpServers, hooks, memory, color).
- **Task**: "Compare each extracted field against the native field lists. Flag any field NOT in the native list as non-native. For each native field, validate value type correctness (booleans, enums, strings). If questionable fields found: check cc-reference cache at `memory/cc-reference/native-fields.md` for latest reference."
- **Constraints**: Read-only. No modifications. Use cc-reference cache as primary validation source (NOT claude-code-guide spawn — that's Lead's decision).
- **Expected Output**: L1 YAML with non_native_fields count, findings[] (file, field, status). L2 compliance report.

### 3. Validate Field Values
For each native field, check value types:
- `name`: string (lowercase, hyphens, max 64 chars)
- `description`: string (multi-line allowed, max 1024 chars)
- `user-invocable`: boolean
- `disable-model-invocation`: boolean
- `model`: one of (sonnet, opus, haiku, inherit)
- `context`: one of (fork)
- `agent`: string (must match existing agent name)
- `argument-hint`: string (e.g., "[topic]")

### 4. Validate Questionable Fields
If any questionable fields found:
- Primary: check `memory/cc-reference/native-fields.md` for field validity. The cc-reference cache is the most reliable and always-available source.
- Supplementary: if cc-reference cache is stale or field is ambiguous, spawn claude-code-guide for confirmation: "Are these frontmatter fields valid for Claude Code skills/agents?" (if unavailable, rely on cc-reference verdict).
- Include the specific fields in question
- Record feasibility verdict per field

### 5. Generate Compliance Report
Produce per-file compliance status:
- PASS: all fields are native and valid
- FAIL: non-native fields found (list them)
- Recommendation: remove or replace non-native fields

## Quality Gate
- Zero non-native fields across all files
- All field values are correct types
- claude-code-guide confirms feasibility (if spawned)
- No deprecated or removed fields used

## Output

### L1
```yaml
domain: verify
skill: cc-feasibility
status: PASS|FAIL
total_files: 0
non_native_fields: 0
findings:
  - file: ""
    field: ""
    status: native|non-native
```

### L2
- Native field compliance per file
- Non-native field removal recommendations
- claude-code-guide validation summary
