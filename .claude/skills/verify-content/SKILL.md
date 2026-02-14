---
name: verify-content
description: |
  [P8·Verify·Content] Content completeness and quality verifier. Checks description field utilization (target >80% of 1024 chars), orchestration map presence (WHEN, DOMAIN, INPUT_FROM, OUTPUT_TO), required body sections, L1/L2/L3 format standards.

  WHEN: After description rewrites or new agent/skill creation. Second of 5 verification stages. Can run independently.
  DOMAIN: verify (skill 2 of 5). After verify-structure PASS.
  INPUT_FROM: verify-structure (structural integrity confirmed) or direct invocation.
  OUTPUT_TO: verify-consistency (if PASS) or execution domain (if FAIL, fix required).
  ONTOLOGY_LENS: ARE (what object contains) + DO (what it describes doing).

  METHODOLOGY: (1) Read all frontmatter descriptions, (2) Measure char utilization (target >80% of 1024), (3) Check orchestration map keys present (WHEN, DOMAIN, INPUT_FROM, OUTPUT_TO, METHODOLOGY), (4) Verify body sections if present, (5) Check L1/L2/L3 output format defined.
  OUTPUT_FORMAT: L1 YAML utilization percentage per file, L2 markdown content completeness report with missing items.
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

# Verify — Content

## Output

### L1
```yaml
domain: verify
skill: content
lens: ARE+DO
status: PASS|FAIL
total_files: 0
avg_utilization_pct: 0
findings:
  - file: ""
    utilization_pct: 0
    missing_keys: []
```

### L2
- Description utilization percentages
- Missing orchestration map keys per file
- Content completeness assessment
