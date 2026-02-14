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

## Execution Model
- **TRIVIAL**: Lead-direct. Quick review of 1-2 file changes.
- **STANDARD**: Spawn 1 analyst. Spec-compliance and code quality review.
- **COMPLEX**: Spawn 2-3 analysts. Parallel spec-review + code-review + contract-review.

## Methodology

### 1. Collect Implementation Artifacts
Gather outputs from execution-code and execution-infra:
- File change manifests (L1 YAML)
- Implementation summaries (L2 markdown)
- Design specifications for comparison

### 2. Stage 1 — Spec Review
Spawn analyst for design compliance check:
- Compare each changed file against design-architecture decisions
- Verify interface implementations match design-interface contracts
- Flag deviations from approved architecture

### 3. Stage 2 — Code Quality Review
Spawn analyst for code quality assessment:
- Check coding patterns and conventions
- Verify error handling and edge cases
- Assess test coverage adequacy
- Flag security concerns (OWASP top 10)

### 4. Consolidate Findings
Merge findings from all review stages:
- Categorize by severity: critical / high / medium / low
- Separate required fixes (blocking) from suggestions (non-blocking)
- Map findings to specific file:line locations

### 5. Issue Fix Loop
If critical or high findings exist:
- Report to execution-code/infra for implementer fixes
- Re-review after fixes applied
- Max 3 review-fix iterations

## Quality Gate
- Zero critical findings remaining
- All high findings addressed or explicitly deferred with rationale
- Spec compliance verified for all changed files
- No security concerns unaddressed

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
