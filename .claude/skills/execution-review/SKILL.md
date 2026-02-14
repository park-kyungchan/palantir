---
name: execution-review
description: |
  [P7·Execution·Review] Two-stage code and spec review executor. Spawns reviewer agents (spec-reviewer, code-reviewer, contract-reviewer) to validate implementation against design specifications and coding standards.

  WHEN: After execution-code and/or execution-infra complete. Implementation artifacts exist but unreviewed.
  DOMAIN: execution (skill 3 of 3). Terminal skill in execution domain. Runs after code and infra.
  INPUT_FROM: execution-code (code changes), execution-infra (infra changes), design domain (specs to review against).
  OUTPUT_TO: verify domain (reviewed implementation for final verification) or execution-code/infra (FAIL, fix required).

  METHODOLOGY: (1) Read implementation artifacts, (2) Stage 1: spawn spec-reviewer for design compliance, (3) Stage 2: spawn code-reviewer for code quality and patterns, (4) Optional: spawn contract-reviewer for interface compliance, (5) Consolidate review findings into unified report.
  CLOSED_LOOP: Review → Find issues → Implementer fixes → Re-review (max 3 iterations).
  MAX_TEAMMATES: 4.
  OUTPUT_FORMAT: L1 YAML review verdict per reviewer, L2 markdown consolidated review report, L3 per-file review details with line references.
user-invocable: true
disable-model-invocation: false
---

# Execution — Review

## Output

### L1
```yaml
domain: execution
skill: review
status: PASS|FAIL
reviewers:
  - type: spec|code|contract
    verdict: PASS|FAIL
    findings: 0
total_findings: 0
```

### L2
- Consolidated review findings by reviewer
- Severity categorization (critical/high/medium/low)
- Required fixes vs suggestions
