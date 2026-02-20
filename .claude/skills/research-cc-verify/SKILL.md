---
name: research-cc-verify
description: >-
  Empirically verifies CC-native behavioral claims via actual file
  inspection before they enter cc-reference cache or CLAUDE.md directives.
  Tests filesystem structure, task JSON persistence, configuration
  fields, and directory layouts. Shift-Left gate after claude-code-guide
  investigation or research-codebase CC-native findings. Prevents
  unverified assumptions from propagating downstream. Use after any
  CC-native investigation produces behavioral claims, before ref cache
  update. Reads from investigation findings with CC-native claims.
  Produces verification verdict with per-claim evidence for Lead routing.
  On FAIL (claim unverifiable or filesystem access denied), flags claim as
  UNVERIFIED and routes back to source skill. Never auto-approve unverifiable
  claims. DPS needs specific CC-native claims with file paths to verify.
  Exclude pipeline context — verify agent needs only the claim list.
user-invocable: true
disable-model-invocation: true
argument-hint: "[claim-source or investigation-context]"
---

# CC-Native Claim Verification — Shift-Left Gate

## Execution Model

- **TRIVIAL**: Lead-direct. Single claim, quick file check. No agent spawn.
- **STANDARD**: Single analyst spawn. 3-10 claims, file-based verification. maxTurns: 10.
- **COMPLEX**: Multiple analysts. 10+ claims across multiple CC subsystems. maxTurns: 15.

> Phase-aware routing and compaction survival: read `.claude/resources/phase-aware-execution.md`

## Phase-Aware Execution

- **All modes**: Subagent (`run_in_background:true`, `context:fork`). Two-channel output — Ch2 (disk file) + Ch3 (micro-signal to Lead). Read upstream outputs from `tasks/{work_dir}/`. Only modify files assigned to you.

## Methodology

### 1. Extract and Categorize Claims

Parse CC-native behavioral claims from source (claude-code-guide output, research findings, `$ARGUMENTS`). Tag each with `[CC-CLAIM]`. Categorize:

| Category | Description | Verification Method |
|---|---|---|
| FILESYSTEM | "X file exists at Y path" | Glob + Read |
| PERSISTENCE | "X survives Y event" | Read files, check timestamps |
| STRUCTURE | "Directory X has layout Y" | Glob tree comparison |
| CONFIG | "Setting X accepts value Y" | Read settings.json or .claude.json |
| BEHAVIORAL | "Feature X produces effect Y" | Inspect artifacts (hooks, profiles) |
| BUG | "Bug X causes behavior Y" | Check symptoms in file state |

### 2. Design Verification Tests

For each claim, identify the file path to inspect and the expected evidence. Map category → path using the lookup tables.

> Filesystem path lookup tables and verification test patterns: read `resources/methodology.md`

### 3. Execute Tests

Run tests with Read, Glob, Grep (read-only; no Bash, no file modification). Each test produces:
- **PASS**: Empirical evidence confirms the claim (include file:line)
- **FAIL**: Evidence contradicts the claim — **BLOCKS ref cache update** (include file:line)
- **NEEDS-REVIEW**: Cannot verify empirically (behavioral/bug claims, or no live test data)

> Claim evidence template and category inspection checklist: read `resources/methodology.md`

### 4. Gate Decision

| Verdict Distribution | Gate Decision |
|---|---|
| All PASS | PROCEED — claims safe for ref cache |
| Any FAIL | BLOCK — failed claims must be corrected before applying |
| PASS + NEEDS-REVIEW only | PROCEED WITH CAUTION — flag NEEDS-REVIEW as unverified |

### 5. Produce Verification Report

Per-claim verdict table with evidence, gate decision, and recommended actions for FAIL/NEEDS-REVIEW claims.

## Decision Points

### When to Invoke
- **ALWAYS**: Before writing CC-native behavioral claims to ref_*.md cache
- **ALWAYS**: Before adding CC-native directives to CLAUDE.md
- **RECOMMENDED**: After claude-code-guide investigation produces findings
- **OPTIONAL**: When existing ref cache content is suspected stale

### When NOT to Invoke
- CC-native FIELD validation → handled by `validate-behavioral` (P7)
- Application code verification → not CC-native scope
- Skill frontmatter compliance → handled by `validate-syntactic`

### Verification Depth by Tier
- **TRIVIAL**: 1-3 claims, single file check each. Lead-direct.
- **STANDARD**: 3-10 claims, multiple file checks. Single analyst.
- **COMPLEX**: 10+ claims, cross-subsystem. Multiple analysts, parallel by category.

### DPS for Analyst Spawn
- **Context (D11)**: Specific claims with expected paths and categories. EXCLUDE pipeline history, other subagents' tasks, design rationale. Budget: ≤30% of effective context.
- **Task**: "Verify each claim via Glob/Read/Grep. Produce PASS/FAIL/NEEDS-REVIEW verdict with file:line evidence."
- **Constraints**: `analyst` agent, read-only, no file modification, no Bash.
- **Delivery (2-channel)**: Ch2 → `tasks/{work_dir}/p2-cc-verify.md`. Ch3 → `"PASS|claims:{total}|fail:{n}|ref:tasks/{work_dir}/p2-cc-verify.md"`. Lead routes result to research-coordinator via file path.

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Tool error, read timeout, single claim inaccessible | L0 Retry | Re-invoke same analyst, same claim list |
| Incomplete verdicts or off-scope evidence | L1 Nudge | Respawn with refined DPS targeting refined paths or narrower scope |
| Analyst exhausted turns or context polluted | L2 Respawn | Kill → fresh analyst with remaining unverified claims |
| Claim list too large, cross-subsystem scope | L3 Restructure | Split by category, assign to parallel analysts |
| 3+ L2 failures or filesystem access denied for all claims | L4 Escalate | AskUserQuestion with blocked claims and options |

- **Claim FAIL**: Mark with contradicting evidence. Do NOT write to ref cache. Lead re-routes to claude-code-guide.
- **Insufficient data**: Mark NEEDS-REVIEW. Document attempted test and why inconclusive.
- **Contradictory evidence**: Mark NEEDS-REVIEW. Document both results. Escalate to claude-code-guide.

> Escalation ladder details: read `.claude/resources/failure-escalation-ladder.md`

## Anti-Patterns

- **DO NOT skip "obvious" claims**: Every CC-native claim must be verified. The ephemeral message assumption cost 4 re-modified files.
- **DO NOT skip PERSISTENCE claims**: Highest-value targets. Don't skip because they're harder to test.
- **DO NOT write FAIL claims to ref cache**: Failed claims must be corrected or removed — never applied as-is.
- **DO NOT treat NEEDS-REVIEW as PASS**: Unverifiable claims must be flagged explicitly in all downstream output.

## Transitions

### Receives From
| Source | Data Expected | Format |
|---|---|---|
| claude-code-guide (agent) | CC-native investigation findings | Structured text with claims |
| research-codebase | CC-native patterns in codebase | Pattern inventory with file:line refs |
| research-external | Community-reported CC behaviors | Source-attributed claims |
| (User invocation) | Specific claims to verify | `$ARGUMENTS` text |

### Sends To
| Target | Data Produced | Trigger Condition |
|---|---|---|
| Lead context | Verification verdict | Always — Lead decides next action |
| execution-infra (ref cache update) | Verified claims | On ALL PASS or PASS+NEEDS-REVIEW |
| claude-code-guide (agent) | Failed claims for re-investigation | On FAIL |

### Failure Routes
| Failure Type | Route To | Data Passed |
|---|---|---|
| Claim FAIL | claude-code-guide | Failed claim + contradicting evidence |
| Insufficient data | (Self — flag) | NEEDS-REVIEW with test details |
| Contradictory evidence | claude-code-guide | Both evidence sets |

> D17 Note: use 2-channel protocol (Ch2 output file `tasks/{work_dir}/`, Ch3 micro-signal to Lead).
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

## Quality Gate
- Every claim has a clear PASS / FAIL / NEEDS-REVIEW verdict
- FAIL claims include contradicting evidence with file:line
- PASS claims include confirming evidence with file:line
- No claim applied to ref cache without verification
- Gate decision matches verdict distribution rules

## Output

### L1
```yaml
domain: research
skill: research-cc-verify
status: PASS|FAIL|NEEDS-REVIEW
claims_total: 0
claims_pass: 0
claims_fail: 0
claims_review: 0
pt_signal: "metadata.phase_signals.p2_research"
signal_format: "PASS|claims:{total}|fail:{n}|ref:tasks/{work_dir}/p2-cc-verify.md"
```

### L2
- Per-claim verdict table with evidence
- Gate decision with rationale
- Recommended actions for FAIL/NEEDS-REVIEW claims
