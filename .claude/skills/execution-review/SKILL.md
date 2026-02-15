---
name: execution-review
description: |
  Evaluates implementation in two stages: design-spec compliance then code quality/security. Classifies findings: CRITICAL/HIGH block, MEDIUM/LOW pass. Fix loop max 3 iterations. Terminal execution skill.

  Use when: After code/infra implementation complete, need quality review before verification.
  WHEN: After execution-code and/or execution-infra complete. All execution outputs converge here.
  CONSUMES: execution-code (code changes), execution-infra (infra changes), execution-impact (impact report), execution-cascade (cascade results), design domain (specs).
  PRODUCES: L1 YAML review verdict with severity breakdown, L2 file:line findings → verify domain (PASS) | execution-code/infra (FAIL: fix loop).
user-invocable: true
disable-model-invocation: false
---

# Execution — Review

## Execution Model
- **TRIVIAL**: Lead-direct. Quick review of 1-2 file changes.
- **STANDARD**: Spawn 1 analyst. Spec-compliance and code quality review.
- **COMPLEX**: Spawn 2-3 analysts. Parallel spec-review + code-review + contract-review.

## Decision Points

### Tier Classification for Review
Lead determines review depth based on change scope:
- **TRIVIAL**: 1-2 files changed, single function/field modification. Lead-direct quick review: read the diff, verify against spec, approve or reject. No analyst spawn needed.
- **STANDARD**: 3-6 files changed, single module scope. Spawn 1 analyst for combined spec+quality review. Stage 1 and Stage 2 can be merged into single analyst prompt.
- **COMPLEX**: 7+ files changed, multiple modules or architectural change. Spawn 2-3 analysts in parallel: separate spec-review, code-quality, and contract-review stages.

### Review Scope Decision
Determine what to review based on inputs available:
- **Code-only review**: Only execution-code produced changes. Standard 2-stage review.
- **Infra-only review**: Only execution-infra produced changes. Review focuses on YAML validity, CC native compliance, and description quality rather than code patterns.
- **Combined review**: Both execution-code and execution-infra produced changes. Assign separate reviewers: code analyst for source files, infra analyst for .claude/ files.
- **Post-cascade review**: execution-cascade ran and reports `convergence: false` or `warnings[]`. Apply extra scrutiny to cascade-updated files — these automated updates may have subtle errors.

### Skip Conditions
Review can be skipped (set status: PASS, findings: 0) ONLY when:
- TRIVIAL tier AND change is purely cosmetic (whitespace, comment-only, non-functional)
- No actual file changes occurred (implementer reported 0 files_changed)
Never skip review for any functional code change, regardless of tier.

### Input Quality Assessment
Before starting review, validate inputs:
1. execution-code and/or execution-infra L1 have `status: complete` or `status: partial`
2. File change manifests are non-empty (have actual file paths)
3. Design specifications are available for comparison (design-architecture L2, design-interface L2)
4. If execution-impact ran: impact report available for context

If design specs are missing: review can still proceed but findings are limited to code quality only (no spec compliance check). Set `spec_review: skipped` in L1.

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
- **Delivery**: Upon completion, send L1 summary to Lead via SendMessage. Include: status (PASS/FAIL), files changed count, key metrics. L2 detail stays in agent context.

#### Stage 1 Tier-Specific DPS Variations

**TRIVIAL**: Skip Stage 1 analyst spawn. Lead directly reads the changed file, compares against design spec in context, and produces PASS/FAIL verdict. Max 2 minutes.

**STANDARD**: Single analyst covers both spec compliance and quality:
- Merge Stage 1 and Stage 2 prompts into one
- Analyst reviews all files sequentially
- Expected completion: 15-20 turns

**COMPLEX**: Full Stage 1 analyst with focused scope:
- Analyst reviews ONLY spec compliance (Stage 2 handles quality separately)
- Provide the full design-architecture L2 and design-interface L2
- Expected completion: 20-25 turns

### 3. Stage 2 — Code Quality Review
Spawn analyst for code quality assessment. Construct the delegation prompt with:
- **Context**: Paste execution-code/infra L1 `files_changed[]` manifest (same file list as Stage 1). Include Stage 1 findings summary received via SendMessage (Stage 1 analyst sends review findings via SendMessage; Lead uses that summary to inform Stage 2 scope). If research-codebase findings exist, include relevant convention patterns.
- **Task**: "Review code quality for each changed file. For each file check: (1) coding patterns match existing codebase conventions, (2) error handling covers failure modes from design-risk assessment, (3) no security vulnerabilities (OWASP top 10: injection, XSS, auth bypass), (4) no obvious performance regressions."
- **Constraints**: Read-only analysis (analyst agent, no Bash). Focus on implementation quality — spec compliance is already covered by Stage 1.
- **Expected Output**: Per-file quality findings with file:line locations. Categorize each as: required fix (blocking merge) vs suggestion (non-blocking). Security findings always classified as critical severity.
- **Delivery**: Upon completion, send L1 summary to Lead via SendMessage. Include: status (PASS/FAIL), files changed count, key metrics. L2 detail stays in agent context.

#### Stage 2 Tier-Specific Adjustments

**TRIVIAL**: Skipped entirely (covered by Lead-direct review in Stage 1).

**STANDARD**: Merged with Stage 1 (single analyst handles both).

**COMPLEX**: Dedicated code quality analyst:
- Receives Stage 1 findings summary to avoid duplicate work
- Focuses exclusively on implementation quality, patterns, security
- For .claude/ infra changes: check YAML validity, frontmatter field compliance, description char limits
- Expected completion: 15-20 turns

### 4. Consolidate Findings
Merge findings from all review stages:
- Categorize by severity: critical / high / medium / low
- Separate required fixes (blocking) from suggestions (non-blocking)
- Map findings to specific file:line locations

#### Severity Classification Guide
When consolidating findings, apply these severity rules:
- **Critical** (blocking, must fix): Spec violation (wrong behavior), security vulnerability (OWASP top 10), data loss risk, breaking API contract
- **High** (blocking, should fix): Interface mismatch (wrong return type, missing error case), missing error handling for external calls, performance regression (O(n^2) where O(n) expected)
- **Medium** (non-blocking, recommend fix): Pattern deviation from codebase conventions, missing edge case handling for internal calls, inconsistent naming
- **Low** (non-blocking, suggestion): Style issues, documentation gaps, minor optimization opportunities

Blocking findings (critical + high) trigger the fix loop. Non-blocking findings (medium + low) are reported but do not prevent PASS verdict.

### 5. Issue Fix Loop
If critical or high findings exist:
- Report to execution-code/infra for implementer fixes
- Re-review after fixes applied
- Max 3 review-fix iterations

**Context Budget Note**: Re-review spawns should be minimal: 1 analyst focused on previously-found issues only. Implementer fixes should be consolidated into a single spawn per iteration. Avoid spawning new full-review analysts in retry iterations.

#### Fix Loop Protocol
1. **Triage**: Separate blocking (critical/high) from non-blocking (medium/low) findings
2. **Route blocking fixes**: Send to execution-code (for source files) or execution-infra (for .claude/ files) with precise finding locations
3. **Fix scope**: Each fix spawn addresses ALL blocking findings for its assigned files. Do not spawn per-finding — batch by file ownership.
4. **Re-review scope**: After fixes applied, spawn a MINIMAL re-review analyst focusing ONLY on previously-found issues. Do NOT re-review the entire codebase.
5. **Convergence check**: If re-review finds new critical/high issues in the fix itself: iterate (max 3 total iterations). If the fix created more problems than it solved: flag as architectural issue, recommend plan revision.
6. **Non-blocking carryover**: Medium/low findings from any iteration are accumulated and reported in final L2, not lost across iterations.

#### Context Budget for Re-Reviews
- Iteration 2 re-review: Spawn 1 analyst with ONLY the changed files from the fix + the specific finding details. Do NOT include full design specs again.
- Iteration 3 re-review: Same scope as iteration 2. If still finding blocking issues: the problem is likely in the design, not the implementation.

## Failure Handling

### All Reviewers Fail to Complete
- **Cause**: maxTurns exhausted, analyst stuck in loop
- **Action**: Set `status: PARTIAL`, include findings from completed portions
- **Routing**: Pipeline continues — partial review is better than no review
- **Lead responsibility**: Note in L1 `warnings[]` which files were not reviewed

### Fix Loop Non-Convergence (3 iterations exhausted)
- **Cause**: Fixes creating new issues, indicating architectural problem
- **Action**: Set `status: FAIL`, include all accumulated findings across iterations
- **Routing**: Route to plan-relational for contract revision, NOT back to execution-code
- **Pipeline impact**: Blocks delivery until plan revision cycle completes

### Missing Design Specs
- **Cause**: Design documents not available (skipped design phase in TRIVIAL/STANDARD)
- **Action**: Proceed with code-quality-only review. Set `spec_review: skipped` in L1.
- **Routing**: Normal pipeline continuation. Spec compliance not verified but code quality assured.

### Conflicting Findings Between Reviewers
- **Cause**: Stage 1 says PASS but Stage 2 says FAIL for same file (different perspectives)
- **Action**: Apply the MORE RESTRICTIVE verdict. If spec says PASS but quality says FAIL, the overall verdict is FAIL.
- **Routing**: Fix loop uses the combined finding set from all reviewers.

## Anti-Patterns

### DO NOT: Review Unchanged Files
Only review files in the execution-code/infra L1 `files_changed[]` manifests. Analysts exploring the broader codebase waste turns and may produce false findings against pre-existing code.

### DO NOT: Spawn Full Re-Review After Fixes
Re-review analysts should ONLY check the specific files and specific findings from the previous iteration. A full re-review wastes context budget and may surface new medium/low findings that delay completion.

### DO NOT: Block on Medium/Low Findings
Only critical and high severity findings trigger the fix loop. Medium/low findings are reported but never block the pipeline. Blocking on style issues is a common Lead mistake that wastes iterations.

### DO NOT: Mix Review Concerns
In COMPLEX tier, keep spec-review and quality-review separate. Mixing them in a single analyst prompt creates cognitive overload and inconsistent severity classification.

### DO NOT: Review Without Impact Context
If execution-impact ran, its L1 report provides critical context: which files were cascade-updated, what references changed, confidence level. Reviewing cascade-updated files without this context misses the root cause of changes.

### DO NOT: Trust Fix Implementers to Self-Verify
After a fix loop iteration, ALWAYS re-review. Implementers fixing review findings may introduce new issues. Self-certification is not verification.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| execution-code | Code change manifest + implementer L1/L2 | L1 YAML: `tasks[].{files[], status}`, L2: implementation summary |
| execution-infra | Infra change manifest + implementer L1/L2 | L1 YAML: `files_changed[]`, L2: configuration change summary |
| execution-impact | Dependency impact report | L1 YAML: `impacts[].{changed_file, dependents[]}`, `cascade_recommended` |
| execution-cascade | Cascade convergence results | L1 YAML: `status`, `convergence`, `warnings[]`, `iteration_details[]` |
| design-architecture | Architecture specs for compliance check | L2 markdown: component structure, module boundaries |
| design-interface | Interface contracts for compliance check | L2 markdown: function signatures, data types, error contracts |
| design-risk | Risk assessment for security focus areas | L2 markdown: identified risk areas and mitigations |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| verify domain | Reviewed + approved implementation | PASS verdict (zero critical/high remaining) |
| execution-code | Fix requests for source files | FAIL verdict with blocking findings in non-.claude/ files |
| execution-infra | Fix requests for .claude/ files | FAIL verdict with blocking findings in .claude/ files |
| plan-relational | Contract revision request | Fix loop non-convergence suggesting architectural issue |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Fix loop non-convergence | plan-relational | All findings across 3 iterations, pattern analysis |
| Missing design specs | Continue (degraded) | `spec_review: skipped` flag in L1 |
| Reviewer maxTurns exhausted | Continue (partial) | Findings from completed portion + unreviewed file list |

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
