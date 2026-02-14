---
name: verify-structure
description: |
  [P8·Verify·Structure] File-level structural integrity verifier. Checks file existence for all .claude/ components, validates YAML frontmatter parse-ability, ensures directory structure compliance, and enforces naming conventions.

  WHEN: After any INFRA file creation or modification. First of 5 verification stages. Can run independently via /verify-structure.
  DOMAIN: verify (skill 1 of 5). Sequential recommended: structure → content → consistency → quality → cc-feasibility.
  INPUT_FROM: execution domain (implementation artifacts) or any file modification trigger.
  OUTPUT_TO: verify-content (if PASS, proceed) or execution domain (if FAIL, fix required).
  ONTOLOGY_LENS: ARE (existence and structure of objects).

  METHODOLOGY: (1) Glob .claude/agents/*.md and .claude/skills/*/SKILL.md, (2) Validate YAML frontmatter parses without errors, (3) Check required fields present (name, description), (4) Verify naming conventions (lowercase, hyphens, correct prefixes), (5) Check directory structure matches expected layout.
  OUTPUT_FORMAT: L1 YAML PASS/FAIL per file with check details, L2 markdown structural integrity report with file:line evidence.
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

# Verify — Structure

## Output

### L1
```yaml
domain: verify
skill: structure
lens: ARE
status: PASS|FAIL
total_files: 0
pass: 0
fail: 0
findings:
  - file: ""
    check: frontmatter|naming|directory
    status: PASS|FAIL
```

### L2
- File inventory with PASS/FAIL per check
- Structural issues with file:line evidence
- Next: verify-content (if PASS)
