---
name: execution-review
description: >-
  Evaluates implementation for design-spec compliance then code
  quality and security. Classifies findings as CRITICAL/HIGH
  (block) or MEDIUM/LOW (pass). Fix loop max 3 iterations.
  Terminal execution skill where all outputs converge. Use after
  execution-code and/or execution-infra complete. Reads from
  execution-code code changes, execution-infra infra changes,
  execution-impact impact report, execution-cascade cascade
  results, and design domain specs. Produces review verdict with
  severity breakdown for verify domain on PASS, or routes back
  to execution-code/infra on FAIL. On fix loop non-convergence
  (3 iterations), routes to plan-relational for contract
  revision, blocking delivery. DPS needs execution-code/infra
  manifests + design-architecture/interface L2 specs. Exclude
  cascade iteration details beyond warnings[] and full ADR
  history.
user-invocable: true
disable-model-invocation: true
---

# Execution — Review

## Execution Model
- **TRIVIAL**: Lead-direct. Quick review of 1-2 file changes.
- **STANDARD**: Spawn 1 analyst. Spec-compliance and code quality review.
- **COMPLEX**: Spawn 2-3 analysts. Parallel spec-review + code-review + contract-review.

## Decision Points

### Tier Classification for Review
Lead determines review depth based on change scope:
- **TRIVIAL**: 1-2 files changed. Lead-direct: read diff, verify against spec, approve or reject.
- **STANDARD**: 3-6 files changed, single module. Spawn 1 analyst for combined spec+quality review.
- **COMPLEX**: 7+ files or multiple modules. Spawn 2-3 parallel analysts: separate spec-review, code-quality, and contract-review.

### Review Scope Decision
- **Code-only**: Only execution-code changes. Standard 2-stage review.
- **Infra-only**: Only execution-infra changes. Focus on YAML validity, CC native compliance, description quality.
- **Combined**: Both code and infra changes. Assign separate reviewers by file type.
- **Post-cascade**: execution-cascade `convergence: false` or `warnings[]`. Extra scrutiny on cascade-updated files.

### Skip Conditions
Review can be skipped (status: PASS, findings: 0) ONLY when:
- TRIVIAL tier AND change is purely cosmetic (whitespace, comment-only, non-functional)
- No actual file changes occurred (implementer reported 0 files_changed)

### Input Quality Assessment
Before starting review, validate inputs:
1. execution-code and/or execution-infra L1 have `status: complete` or `status: partial`
2. File change manifests are non-empty (have actual file paths)
3. Design specifications available for comparison (design-architecture L2, design-interface L2)
4. If execution-impact ran: impact report available for context

If design specs missing: proceed with code-quality-only review; set `spec_review: skipped` in L1.

## Methodology

### 1. Collect Implementation Artifacts
Gather outputs from execution-code and execution-infra:
- File change manifests (L1 YAML)
- Implementation summaries (L2 markdown)
- Design specifications for comparison

### 2. Stage 1 — Spec Review
Spawn analyst to check design compliance per changed file: architecture component correctness, interface contract match, deviation classification.
- For full DPS template (INCLUDE/EXCLUDE/Budget/Task/Delivery) and tier variations: read `resources/methodology.md`

### 3. Stage 2 — Code Quality Review
Spawn analyst to check: codebase convention alignment, error handling coverage, OWASP top-10 security, performance regressions.
- For full DPS template and tier-specific adjustments: read `resources/methodology.md`

### 4. Consolidate Findings
Merge findings from all review stages:
- Categorize by severity: critical / high / medium / low
- Separate required fixes (blocking) from suggestions (non-blocking)
- Map findings to specific file:line locations
- For severity classification rubric: read `resources/methodology.md`

### 5. Issue Fix Loop
If critical or high findings exist: route to execution-code/infra for fixes, re-review after fixes, max 3 iterations.
- **Context Budget**: Re-review spawns are minimal — 1 analyst on previously-found issues only. Do not spawn full re-review analysts in retry iterations.
- For detailed 6-step fix loop protocol and context budget rules: read `resources/methodology.md`

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Tool error, reviewer spawn timeout | L0 Retry | Re-invoke same analyst with same DPS |
| Reviewer output incomplete or coverage gaps | L1 Nudge | Respawn with refined DPS targeting narrowed scope or focused file list |
| Reviewer exhausted turns or context polluted | L2 Respawn | Kill → fresh analyst with refined DPS focused on pending files |
| Fix loop non-convergent after 2 iterations or scope conflict | L3 Restructure | Reassign review scope, separate spec vs quality reviews, re-stage |
| Fix loop exhausted (3 iterations), architectural contract conflict | L4 Escalate | AskUserQuestion with situation summary + options |

> For failure sub-case details (all reviewers fail, non-convergence, missing specs, conflicting findings): read `resources/methodology.md`

## Anti-Patterns

- **DO NOT review unchanged files** — only review files in the execution-code/infra L1 `files_changed[]` manifests. Analysts exploring the broader codebase waste turns and may produce false findings.
- **DO NOT spawn full re-review after fixes** — re-review analysts check ONLY specific files and findings from the previous iteration.
- **DO NOT block on Medium/Low findings** — only critical and high severity findings trigger the fix loop. Blocking on style issues wastes iterations.
- **DO NOT mix review concerns in COMPLEX tier** — keep spec-review and quality-review separate. Mixing creates cognitive overload and inconsistent severity classification.
- **DO NOT review without impact context** — if execution-impact ran, its L1 provides critical context (cascade-updated files, confidence level). Missing this context misses root causes.
- **DO NOT trust fix implementers to self-verify** — always re-review after a fix loop iteration. Self-certification is not verification.

## Phase-Aware Execution

This skill runs in Two-Channel protocol only. Single-session subagent execution:
- **Subagent writes** output file to `tasks/{work_dir}/p6-review.md`
- **Ch3 micro-signal** to Lead with PASS/FAIL status
- **Task tracking**: Subagent calls TaskUpdate on completion. File ownership: only modify assigned files.

> D17 Note: Two-Channel protocol — Ch2 (file output to tasks/{work_dir}/) + Ch3 (micro-signal to Lead).
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`
> Phase-aware routing and compaction survival: read `.claude/resources/phase-aware-execution.md`
> DPS construction guide: read `.claude/resources/dps-construction-guide.md`
> Escalation ladder details: read `.claude/resources/failure-escalation-ladder.md`

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
pt_signal: "metadata.phase_signals.p6_review"
signal_format: "{STATUS}|findings:{N}|severity:{critical|high}|ref:tasks/{work_dir}/p6-review.md"
```

### L2
- Consolidated review findings by reviewer
- Severity categorization (critical/high/medium/low)
- Required fixes vs suggestions
