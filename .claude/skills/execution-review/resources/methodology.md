# Execution Review — Detailed Methodology

> On-demand reference. Contains Stage 1/2 DPS templates, severity classification rubric, fix loop protocol, and failure sub-case details.

## Stage 1 — Spec Review: Full DPS Template

Spawn analyst for design compliance check. Construct the delegation prompt with:

**Context (D11 — cognitive focus first)**:
- INCLUDE: execution-code/infra L1 `files_changed[]` manifest (file paths and change type). Design-architecture L2 (component decisions relevant to changed files). Design-interface L2 (contract specifications for affected interfaces). If cascade ran: execution-cascade L1 `status` and `warnings[]` only.
- EXCLUDE: Cascade iteration details beyond `warnings[]`. Full ADR history. Other phases' outputs not needed for compliance check.
- Budget: Context field ≤ 30% of analyst effective context.

**Task**: "Review each changed file against the provided design specs. For each file: (1) verify it implements the correct architecture component, (2) check interface contracts match design-interface signatures exactly, (3) flag any deviations with severity classification."

**Constraints**: Read-only analysis (analyst agent, no Bash). Review only the listed changed files — do not explore the entire codebase.

**Expected Output**: Per-file compliance verdict (PASS/FAIL) with file:line references for deviations. Severity: critical (spec violation), high (interface mismatch), medium (pattern deviation), low (style issue).

**Delivery**: Upon completion, send L1 summary to Lead via file-based signal. Include: status (PASS/FAIL), files changed count, key metrics. L2 detail stays in agent context.

### Stage 1 Tier-Specific DPS Variations

**TRIVIAL**: Skip Stage 1 analyst spawn. Lead directly reads the changed file, compares against design spec in context, and produces PASS/FAIL verdict. Max 2 minutes.

**STANDARD**: Single analyst covers both spec compliance and quality:
- Merge Stage 1 and Stage 2 prompts into one
- Analyst reviews all files sequentially
- Expected completion: 15-20 turns

**COMPLEX**: Full Stage 1 analyst with focused scope:
- Analyst reviews ONLY spec compliance (Stage 2 handles quality separately)
- Provide the full design-architecture L2 and design-interface L2
- Expected completion: 20-25 turns

## Stage 2 — Code Quality Review: Full DPS Template

Spawn analyst for code quality assessment. Construct the delegation prompt with:

**Context (D11 — cognitive focus first)**:
- INCLUDE: execution-code/infra L1 `files_changed[]` manifest (same file list as Stage 1). Stage 1 findings summary received via file-based signal. Relevant convention patterns from research-codebase if available.
- EXCLUDE: Design-architecture and design-interface L2 full content (covered by Stage 1). Cascade history. Full pipeline state.
- Budget: Context field ≤ 30% of analyst effective context.

**Task**: "Review code quality for each changed file. For each file check: (1) coding patterns match existing codebase conventions, (2) error handling covers failure modes from design-risk assessment, (3) no security vulnerabilities (OWASP top 10: injection, XSS, auth bypass), (4) no obvious performance regressions."

**Constraints**: Read-only analysis (analyst agent, no Bash). Focus on implementation quality — spec compliance is already covered by Stage 1.

**Expected Output**: Per-file quality findings with file:line locations. Categorize each as: required fix (blocking merge) vs suggestion (non-blocking). Security findings always classified as critical severity.

**Delivery**: Upon completion, send L1 summary to Lead via file-based signal. Include: status (PASS/FAIL), files changed count, key metrics. L2 detail stays in agent context.

### Stage 2 Tier-Specific Adjustments

**TRIVIAL**: Skipped entirely (covered by Lead-direct review in Stage 1).

**STANDARD**: Merged with Stage 1 (single analyst handles both).

**COMPLEX**: Dedicated code quality analyst:
- Receives Stage 1 findings summary to avoid duplicate work
- Focuses exclusively on implementation quality, patterns, security
- For .claude/ infra changes: check YAML validity, frontmatter field compliance, description char limits
- Expected completion: 15-20 turns

## Severity Classification Guide

When consolidating findings, apply these severity rules:

- **Critical** (blocking, must fix): Spec violation (wrong behavior), security vulnerability (OWASP top 10), data loss risk, breaking API contract
- **High** (blocking, should fix): Interface mismatch (wrong return type, missing error case), missing error handling for external calls, performance regression (O(n^2) where O(n) expected)
- **Medium** (non-blocking, recommend fix): Pattern deviation from codebase conventions, missing edge case handling for internal calls, inconsistent naming
- **Low** (non-blocking, suggestion): Style issues, documentation gaps, minor optimization opportunities

Blocking findings (critical + high) trigger the fix loop. Non-blocking findings (medium + low) are reported but do not prevent PASS verdict.

## Fix Loop Protocol

1. **Triage**: Separate blocking (critical/high) from non-blocking (medium/low) findings
2. **Route blocking fixes**: Send to execution-code (for source files) or execution-infra (for .claude/ files) with precise finding locations
3. **Fix scope**: Each fix spawn addresses ALL blocking findings for its assigned files. Do not spawn per-finding — batch by file ownership.
4. **Re-review scope**: After fixes applied, spawn a MINIMAL re-review analyst focusing ONLY on previously-found issues. Do NOT re-review the entire codebase.
5. **Convergence check**: If re-review finds new critical/high issues in the fix itself: iterate (max 3 total iterations). If the fix created more problems than it solved: flag as architectural issue, recommend plan revision.
6. **Non-blocking carryover**: Medium/low findings from any iteration are accumulated and reported in final L2, not lost across iterations.

### Context Budget for Re-Reviews
- Iteration 2 re-review: Spawn 1 analyst with ONLY the changed files from the fix + the specific finding details. Do NOT include full design specs again.
- Iteration 3 re-review: Same scope as iteration 2. If still finding blocking issues: the problem is likely in the design, not the implementation.

## Failure Sub-Cases

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
