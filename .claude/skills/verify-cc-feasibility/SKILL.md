---
name: verify-cc-feasibility
description: |
  [P8·Verify·CCFeasibility] Claude Code native capabilities compliance verifier. Ensures all frontmatter uses ONLY native fields, no custom fields exist (routing, meta_cognition), and validates via claude-code-guide agent spawn.

  WHEN: After every skill/agent creation or frontmatter modification. Fifth and final verification stage. Can run independently.
  DOMAIN: verify (skill 5 of 5). Terminal skill in verify domain. After verify-quality PASS.
  INPUT_FROM: verify-quality (routing quality confirmed) or direct invocation.
  OUTPUT_TO: delivery-pipeline (if all 5 stages PASS) or execution domain (if FAIL, fix required).
  ONTOLOGY_LENS: ARE (structural compliance) + DO (behavioral feasibility).

  METHODOLOGY: (1) Read target frontmatter fields, (2) Check against allowed native fields (name, description, model, tools, disallowedTools, permissionMode, memory, color, maxTurns, hooks, mcpServers, skills, user-invocable, disable-model-invocation, confirm, input_schema, working_dir, timeout, env), (3) Flag any non-native field, (4) Spawn claude-code-guide: "Is this valid?", (5) Return verdict.
  CLOSED_LOOP: Verify → FAIL → Remove non-native fields → Re-verify → PASS.
  OUTPUT_FORMAT: L1 YAML native compliance per file, L2 markdown feasibility report with field-level feedback.
user-invocable: true
disable-model-invocation: false
input_schema:
  type: object
  properties:
    target:
      type: string
      description: "File or directory to verify (default: .claude/)"
  required: []
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
Allowed native fields:
- `name`, `description`, `model`, `tools`, `disallowedTools`
- `permissionMode`, `memory`, `color`, `maxTurns`
- `hooks`, `mcpServers`, `skills`
- `user-invocable`, `disable-model-invocation`, `confirm`
- `input_schema`, `working_dir`, `timeout`, `env`

Flag any field NOT in this list as non-native.

### 3. Validate Field Values
For each native field, check value types:
- `name`: string
- `description`: string (multi-line allowed)
- `user-invocable`: boolean
- `input_schema`: object with JSON Schema structure
- `model`: one of known model identifiers

### 4. Spawn Claude-Code-Guide Verification
If any questionable fields found:
- Spawn claude-code-guide agent: "Are these frontmatter fields valid for Claude Code skills/agents?"
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
lens: ARE+DO
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
