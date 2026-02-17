---
name: research-cc-verify
description: >-
  Empirically verifies CC-native behavioral claims via actual file
  inspection before they enter cc-reference cache or CLAUDE.md directives.
  Tests filesystem structure, inbox/task JSON persistence, configuration
  fields, and directory layouts. Shift-Left gate after claude-code-guide
  investigation or research-codebase CC-native findings. Prevents
  unverified assumptions from propagating downstream. Use after any
  CC-native investigation produces behavioral claims, before ref cache
  update. Reads from investigation findings with CC-native claims.
  Produces verification verdict with per-claim evidence for Lead routing.
user-invocable: true
disable-model-invocation: false
argument-hint: "[claim-source or investigation-context]"
---

# CC-Native Claim Verification — Shift-Left Gate

## Execution Model

- **TRIVIAL**: Lead-direct. Single claim, quick file check. No agent spawn.
- **STANDARD**: Single analyst spawn. 3-10 claims, file-based verification. maxTurns: 10.
- **COMPLEX**: Multiple analysts. 10+ claims across multiple CC subsystems. maxTurns: 15.

## Phase-Aware Execution

This skill operates at P2 (Research) or as ad-hoc gate before any ref cache update.
- **P0-P1 mode**: Lead with local agent (run_in_background).
- **P2+ mode**: Team agent with SendMessage delivery.

## Phase-Aware Execution (P2+ Team Protocol)

- **Communication**: Use SendMessage for result delivery to Lead. Write large outputs to disk.
- **Task tracking**: Update task status via TaskUpdate after completion.
- **No shared memory**: Insights exist only in your context. Explicitly communicate findings.
- **File ownership**: Only modify files assigned to you. No overlapping edits with parallel agents.

## Methodology

### 1. Extract Claims

Parse CC-native behavioral claims from source (claude-code-guide output, research findings, or user-provided context via $ARGUMENTS). Categorize each claim:

| Category | Description | Verification Method |
|----------|-------------|-------------------|
| FILESYSTEM | "X file exists at Y path" | Glob + Read |
| PERSISTENCE | "X survives Y event" | Read actual files, check timestamps |
| STRUCTURE | "Directory X has layout Y" | Glob tree comparison |
| CONFIG | "Setting X accepts value Y" | Read settings.json, validate format |
| BEHAVIORAL | "Feature X produces effect Y" | Flag for deeper investigation |
| BUG | "Bug X causes behavior Y" | Check for described symptoms |

### 2. Design Verification Tests

For each FILESYSTEM/PERSISTENCE/STRUCTURE/CONFIG claim, design a minimal empirical test:

**FILESYSTEM test pattern:**
```
Claim: "Inbox files stored at ~/.claude/teams/{name}/inboxes/{agent}.json"
Test: Glob("~/.claude/teams/*/inboxes/*.json")
Expected: Files matching pattern exist
Verdict: PASS if files found, FAIL if not
```

**PERSISTENCE test pattern:**
```
Claim: "Inbox JSON persists after agent termination"
Test: Read inbox file for terminated agent
Expected: File exists and contains messages with timestamps before termination
Verdict: PASS if messages present, FAIL if file missing/empty
```

**STRUCTURE test pattern:**
```
Claim: "Tasks use file locking via .lock file"
Test: Glob("~/.claude/tasks/*/.lock")
Expected: .lock file exists in active task directories
Verdict: PASS if found, NEEDS-REVIEW if not (may be transient)
```

**CONFIG test pattern:**
```
Claim: "teammateMode accepts 'tmux', 'in-process', 'auto'"
Test: Read settings.json, check teammateMode value
Expected: Value is one of the documented options
Verdict: PASS if valid value, NEEDS-REVIEW if field absent
```

### 3. Execute Tests

Run all designed tests using file inspection tools (Read, Glob, Grep).

Rules:
- Each test must produce a clear PASS / FAIL / NEEDS-REVIEW verdict
- **PASS**: Empirical evidence confirms the claim
- **FAIL**: Empirical evidence contradicts the claim — **BLOCKS ref cache update**
- **NEEDS-REVIEW**: Cannot verify empirically (behavioral/bug claims, or insufficient test data)
- Include file:line evidence for each verdict

### 4. Gate Decision

| Verdict Distribution | Gate Decision |
|---------------------|--------------|
| All PASS | PROCEED — claims safe for ref cache |
| Any FAIL | BLOCK — failed claims must be corrected before applying |
| PASS + NEEDS-REVIEW only | PROCEED WITH CAUTION — flag NEEDS-REVIEW items as "unverified" |

### 5. Produce Verification Report

Per-claim verdict table with evidence, gate decision, and recommended actions for FAIL/NEEDS-REVIEW claims.

## Decision Points

### When to Invoke This Skill
- **ALWAYS**: Before writing CC-native behavioral claims to ref_*.md cache
- **ALWAYS**: Before adding CC-native directives to CLAUDE.md
- **RECOMMENDED**: After claude-code-guide investigation produces findings
- **OPTIONAL**: When existing ref cache content is suspected stale or incorrect

### When NOT to Invoke
- CC-native FIELD validation (handled by verify-cc-feasibility in P7)
- Application code verification (not CC-native)
- Skill frontmatter compliance (handled by verify-structural-content)

### Verification Depth by Tier
- **TRIVIAL**: 1-3 claims, single file check each. Lead-direct.
- **STANDARD**: 3-10 claims, multiple file checks. Single analyst.
- **COMPLEX**: 10+ claims, cross-subsystem verification. Multiple analysts, parallel.

### DPS for Analyst Spawn
- **Context**: List of CC-native claims with categories. Include expected file paths and verification patterns.
- **Task**: "Verify each claim empirically via file inspection. For each claim: Glob/Read the expected path, compare actual content against claimed behavior, produce PASS/FAIL/NEEDS-REVIEW verdict with file:line evidence."
- **Constraints**: analyst agent. Read-only operations. No file modification. No Bash.
- **Expected Output**: Per-claim verdict table with evidence.
- **Delivery**: SendMessage to Lead (P2+) or direct output (P0-P1).

## Failure Handling

### Claim Fails Verification
- **Cause**: Empirical evidence contradicts CC-native claim
- **Action**: Mark claim as FAIL with contradicting evidence. Do NOT write to ref cache. Report to Lead.
- **Routing**: Lead re-routes to claude-code-guide for deeper investigation or corrects based on evidence.

### Insufficient Test Data
- **Cause**: No active team/session to verify against (e.g., can't check inbox files if no team exists)
- **Action**: Mark as NEEDS-REVIEW. Document what test was attempted and why inconclusive. Proceed with caution.

### Contradictory Evidence
- **Cause**: Multiple tests for same claim produce conflicting results
- **Action**: Mark as NEEDS-REVIEW. Document both results. Escalate to claude-code-guide for resolution.

## Anti-Patterns

### DO NOT: Skip Verification for "Obvious" Claims
Every CC-native behavioral claim must be verified. The SendMessage "ephemeral" error was an "obvious" assumption that turned out to be wrong. Cost: 4 files re-modified.

### DO NOT: Verify Only File Claims
PERSISTENCE claims (e.g., "survives compaction") are the highest-value verification targets. Don't skip them because they're harder to test.

### DO NOT: Write FAIL Claims to Ref Cache
Failed claims must be corrected or removed. Never write unverified or disproved information to the authoritative ref cache.

### DO NOT: Treat NEEDS-REVIEW as PASS
Unverifiable claims should be explicitly flagged in any downstream output. They are not confirmed.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| claude-code-guide (agent) | CC-native investigation findings | Structured text with claims |
| research-codebase | CC-native patterns discovered in codebase | Pattern inventory with file:line refs |
| research-external | Community-reported CC behaviors | Source-attributed claims |
| (User invocation) | Specific claims to verify | $ARGUMENTS text |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| (Lead context) | Verification verdict | Always — Lead decides next action |
| ref cache update (execution-infra) | Verified claims for ref cache | On ALL PASS or PASS+NEEDS-REVIEW |
| claude-code-guide (agent) | Failed claims for re-investigation | On FAIL — deeper investigation needed |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Claim FAIL | claude-code-guide | Failed claim + contradicting evidence |
| Insufficient data | (Self — flag) | NEEDS-REVIEW with test details |
| Contradictory evidence | claude-code-guide | Both evidence sets |

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
```

### L2
- Per-claim verdict table with evidence
- Gate decision with rationale
- Recommended actions for FAIL/NEEDS-REVIEW claims
