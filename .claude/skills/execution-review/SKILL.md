---
name: execution-review
description: |
  [P7·Execution·Review] Two-stage code and spec review executor. Spawns analyst reviewers to validate implementation against design specs and coding standards.

  WHEN: After execution-code and/or execution-infra complete. Implementation artifacts exist but unreviewed.
  DOMAIN: execution (skill 5 of 5). Terminal. After code/infra/impact/cascade.
  INPUT_FROM: execution-code (code changes), execution-infra (infra changes), execution-impact (impact report), execution-cascade (cascade results), design domain (specs).
  OUTPUT_TO: verify domain (reviewed implementation) or execution-code/infra (FAIL, fix required).

  METHODOLOGY: (1) Read implementation artifacts, (2) Stage 1: spawn analyst for design/spec compliance, (3) Stage 2: spawn analyst for code quality and patterns, (4) Optional: contract review for interface compliance, (5) Consolidate review findings into unified report.
  OUTPUT_FORMAT: L1 YAML review verdict per reviewer, L2 markdown consolidated review report.
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
Spawn analyst for design compliance check. Construct the delegation prompt with:
- **Context**: Paste execution-code/infra L1 `files_changed[]` manifest (file paths and change type). Paste design-architecture L2 (component decisions relevant to changed files) and design-interface L2 (contract specifications for affected interfaces). If cascade ran, include execution-cascade L1 `status` and `warnings[]`.
- **Task**: "Review each changed file against the provided design specs. For each file: (1) verify it implements the correct architecture component, (2) check interface contracts match design-interface signatures exactly, (3) flag any deviations with severity classification."
- **Constraints**: Read-only analysis (analyst agent, no Bash). Review only the listed changed files — do not explore the entire codebase.
- **Expected Output**: Per-file compliance verdict (PASS/FAIL) with file:line references for deviations. Severity: critical (spec violation), high (interface mismatch), medium (pattern deviation), low (style issue).

### 3. Stage 2 — Code Quality Review
Spawn analyst for code quality assessment. Construct the delegation prompt with:
- **Context**: Paste execution-code/infra L1 `files_changed[]` manifest (same file list as Stage 1). Include Stage 1 findings summary (so this reviewer focuses on different concerns). If research-codebase findings exist, include relevant convention patterns.
- **Task**: "Review code quality for each changed file. For each file check: (1) coding patterns match existing codebase conventions, (2) error handling covers failure modes from design-risk assessment, (3) no security vulnerabilities (OWASP top 10: injection, XSS, auth bypass), (4) no obvious performance regressions."
- **Constraints**: Read-only analysis (analyst agent, no Bash). Focus on implementation quality — spec compliance is already covered by Stage 1.
- **Expected Output**: Per-file quality findings with file:line locations. Categorize each as: required fix (blocking merge) vs suggestion (non-blocking). Security findings always classified as critical severity.

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
