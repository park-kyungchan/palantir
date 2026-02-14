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
