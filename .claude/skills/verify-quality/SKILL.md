---
name: verify-quality
description: |
  [P8·Verify·Quality] Routing effectiveness and description clarity verifier. Checks WHEN conditions are specific and actionable, methodology steps are concrete with tool/agent references, output format specifies L1/L2/L3, protocol covers full flow.

  WHEN: Before committing description changes or after routing failures. Fourth of 5 verification stages. Can run independently.
  DOMAIN: verify (skill 4 of 5). After verify-consistency PASS.
  INPUT_FROM: verify-consistency (relationship integrity confirmed) or direct invocation.
  OUTPUT_TO: verify-cc-feasibility (if PASS) or execution domain (if FAIL, fix required).
  ONTOLOGY_LENS: DO (behavioral quality of descriptions and protocols).

  METHODOLOGY: (1) Read all WHEN conditions, check specificity (reject vague "when needed"), (2) Read METHODOLOGY steps, check numbered concrete steps with tool names, (3) Read OUTPUT_FORMAT, check L1/L2/L3 structure defined, (4) Check description utilization >88% of 1024 chars (quality target), (5) Score and rank by routing effectiveness.
  OUTPUT_FORMAT: L1 YAML quality score per file (0-100), L2 markdown quality report with improvement suggestions.
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

# Verify — Quality

## Output

### L1
```yaml
domain: verify
skill: quality
lens: DO
status: PASS|FAIL
total_files: 0
avg_score: 0
findings:
  - file: ""
    score: 0
    issues: []
```

### L2
- Quality score per file (0-100)
- WHEN condition specificity check
- METHODOLOGY concreteness assessment
