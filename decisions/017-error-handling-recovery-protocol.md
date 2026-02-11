# Decision 017: Error Handling & Recovery Protocol

**Status:** PENDING USER DECISION  
**Date:** 2026-02-11  
**Context:** CLAUDE.md v6.0 · 42 agents (D-005) · tmux panes · 4 hooks · 8 coordinators  
**Depends on:** Decision 005, Decision 007 (BN-006, BN-007), Decision 013, Decision 014

---

## 1. Problem Statement

Error handling across the INFRA is scattered:
- **Hook scripts:** Each hook has its own error strategy (`|| exit 0`, `set -e`)
- **Agent failures:** Agent `.md` files mention failure handling but inconsistently
- **Coordinator failures:** Mode 3 fallback defined per coordinator (D-013 consolidates)
- **Skill failures:** No unified failure taxonomy
- **Pipeline failures:** delivery-pipeline handles rollback but no other Skill does

With 42 agents running in tmux, failure surface area expands dramatically:
- Agent crashes (tmux pane closes)
- Agent context exhaustion (200K limit → compact → data loss)
- Coordinator becomes unresponsive
- Tool API errors (TaskGet fails, file not found)
- Inter-agent communication failures (SendMessage to dead agent)
- Network errors (MCP server unavailable)

**D-007 BN-006 (No Rollback)** and **BN-007 (Silent Skill Failure)** directly address
this gap.

**Core question:** What is the unified error taxonomy and recovery protocol for 
the 42-agent system?

---

## 2. Current State (Code-Level Audit)

### 2.1 Hook Error Handling

| Hook | Strategy | Quality |
|------|----------|---------|
| `on-rtd-post-tool.sh` | `\|\| exit 0` on all paths. Never blocks pipeline. | ✅ Excellent |
| `on-subagent-start.sh` | `exit 0` at end. Best-effort context injection. | ✅ Good |
| `on-pre-compact.sh` | jq check → exit 0 early. Task snapshot best-effort. | ✅ Good |
| `on-session-compact.sh` | jq fallback to manual JSON echo. Graceful degradation. | ✅ Good |

**Assessment:** Hook error handling is SOLID. All hooks follow "never block, best effort"
principle. No changes needed.

### 2.2 Agent-Level Error Handling

From agent `.md` audit:

| Agent Type | Failure Handling | Quality |
|-----------|-----------------|---------|
| **Coordinators (5)** | Timeout thresholds + Mode 3 fallback + "alert Lead" | ✅ Consistent (D-013 consolidates) |
| **execution-coordinator** | 3x fix-loop exhaustion → escalate to Lead | ✅ Well-defined |
| **execution-monitor** | Polling anomaly → alert Lead | ✅ Good |
| **implementer** | "If context pressure: save + alert Lead" (from protocol) | ⚠️ Generic only |
| **spec-reviewer** | No explicit failure handling | ⚠️ Missing |
| **code-reviewer** | No explicit failure handling | ⚠️ Missing |
| **auditor** | No explicit failure handling | ⚠️ Missing |
| **dynamic-impact-analyst** | No explicit failure handling | ⚠️ Missing |
| **infra-implementer** | No explicit failure handling | ⚠️ Missing |
| **Researchers (3)** | Implicit via protocol (context pressure → alert Lead) | ⚠️ Generic only |
| **Verifiers (3)** | No explicit failure handling | ⚠️ Missing |

**Finding:** 11 of 27 agents have NO explicit failure handling beyond the generic
protocol. For D-005's 42 agents, this gap widens.

### 2.3 Skill-Level Error Handling

| Skill | Error Handling | Gap |
|-------|---------------|-----|
| permanent-tasks | 5-row error table (§Error Handling) | ✅ Well-defined |
| brainstorming-pipeline | Phase 0 Block has "if PT not found → create" | ⚠️ No gate failure protocol |
| write-plan | Gate 2 failure path exists | ⚠️ Vague "request additional research" |
| agent-teams-execution-plan | Not audited | ? |
| delivery-pipeline | Rollback via git | ⚠️ Only Skill with rollback |

### 2.4 Task API Error Handling

From task-api-guideline.md:

| Error | Current Handling |
|-------|----------|
| TaskGet fails | "Report error to user, suggest manual check" (PT Skill) |
| TaskList empty | Treat as "not found" → create PT |
| Multiple PTs found | Use first, warn user |
| Task auto-deleted | ISS-001: save to L1/L2/L3 before marking complete |
| Task orphaned | ISS-003: use team scope or CLAUDE_CODE_TASK_LIST_ID |

**Assessment:** Task API error handling is adequate but passive (warn, not recover).

---

## 3. Error Taxonomy

### 3.1 Proposed 3-Tier Error Model

```
TIER 1: SELF-RECOVERABLE
  Agent can handle without external help. Log and continue.
  Examples: File not found (create it), jq parse fail (use fallback)

TIER 2: ESCALATION-REQUIRED
  Agent cannot resolve alone. Escalate to coordinator or Lead.
  Examples: Context pressure, tool API failure, cross-boundary conflict

TIER 3: PIPELINE-AFFECTING
  Failure affects pipeline continuation. Requires Lead decision.
  Examples: Gate failure, coordinator crash, PT corruption, all workers failed
```

### 3.2 Error → Tier Mapping

| Error | Tier | Recovery Path |
|-------|:---:|--------------|
| File not found during Read | 1 | Create from template or skip with warning |
| jq parse failure in hook | 1 | Exit 0 (never block) — already implemented |
| MCP server unavailable | 1 | Retry 1x, then proceed without (graceful degradation) |
| Agent context approaching 75% | 2 | Save L1/L2/L3, alert coordinator/Lead |
| Agent context exhaustion (compact) | 2 | Auto-recovery via SessionStart hook + L1/L2 reload |
| Tool API error (TaskGet fails) | 2 | Use embedded PT content from directive, alert Lead |
| Worker unresponsive | 2 | Coordinator timeout protocol → escalate to Lead |
| SendMessage to dead agent | 2 | Detect via no response → alert coordinator/Lead |
| Coordinator unresponsive | 3 | Mode 3 fallback — Lead takes over workers |
| Gate FAIL | 3 | Lead determines: retry, skip, abort |
| PT corruption (malformed content) | 3 | Lead re-creates PT from conversation context |
| All workers in a category failed | 3 | Lead decides: re-spawn, skip phase, abort pipeline |
| Fix loop exhausted (3x) | 3 | execution-coordinator escalates to Lead |
| Pipeline rollback needed | 3 | delivery-pipeline: git revert (only Phase 9 currently) |

---

## 4. Proposed: Universal Error Protocol

### 4.1 Agent-Level Error Protocol

Add to `agent-common-protocol.md`:

```markdown
## Error Handling

### Tier 1: Self-Recoverable
Errors you can handle yourself. Log the error in your L2 output and continue.
- File not found → Create from template or skip with warning
- Tool parse error → Use fallback or retry once
- MCP server timeout → Proceed without that tool's data, note in L2

### Tier 2: Escalation-Required
Errors requiring external help. Save your work immediately, then escalate.
1. Write current L1/L2/L3 files (your recovery checkpoint)
2. SendMessage to coordinator (or Lead if no coordinator):
   - What failed: exact error description
   - What you tried: Tier 1 recovery attempt (if any)
   - What you need: specific ask (re-assign, more context, intervention)
   - Current status: what work is saved and what is lost
3. Wait for response. Do NOT continue working on the failed task.
4. If no response in 5 minutes: SendMessage to Lead directly.

### Tier 3: Pipeline-Affecting
Errors that stop the pipeline. This is typically handled by coordinators and Lead.
If you detect a Tier 3 error as a worker:
1. Save all work immediately
2. Escalate to coordinator with URGENT flag in SendMessage
3. The coordinator/Lead will determine: retry, skip, or abort
```

### 4.2 Coordinator Error Protocol

Already partially defined in D-013 (coordinator-shared-protocol.md). Add:

```markdown
## Error Escalation Matrix

| Worker Error | Your Response | Lead Escalation? |
|-------------|---------------|:---:|
| Worker unresponsive (T1 threshold) | Send status query | NO |
| Worker unresponsive (T2 threshold) | Alert Lead for re-spawn | YES |
| Worker reports Tier 2 error | Attempt reassignment or retry | Only if unresolvable |
| Worker reports Tier 3 error | Immediate escalation to Lead | YES |
| All workers in your category failed | Stop coordination, full escalation | YES (URGENT) |
| Your own context pressure | Save L1/L2, trigger Mode 3 | YES (URGENT) |
```

### 4.3 Lead Error Protocol

Add to CLAUDE.md (or gate-evaluation-standard reference):

```markdown
## Pipeline Error Decision Framework

On Tier 3 escalation, Lead uses this decision tree:
1. Is the error in a MANDATORY phase? → Must resolve before continuing
2. Is re-spawn feasible? → Respawn agent with L1/L2 context reload
3. Is the phase CONDITIONAL? → Can skip (P2b, P7, P8)
4. Is manual intervention needed? → Ask user
5. Is pipeline rollback needed? → Only P9 delivery-pipeline supports git rollback
```

---

## 5. Silent Failure Detection (D-007 BN-007)

### 5.1 Problem

Skills can fail silently — the Skill completes but its output is missing critical
content. Lead may not notice until a downstream phase reads incomplete input.

### 5.2 Proposed: Post-Skill Validation Checklist

After each Skill invocation, Lead checks:
1. **Output exists:** L2 file was written (Glob check)
2. **L1 is parseable:** L1-index.yaml has mandatory keys (agent, phase, status)
3. **Evidence count > 0:** L1.evidence_count > 0 (from D-015 canonical format)
4. **No BLOCKED status:** All workers report complete or in_progress (not blocked)

If any check fails → Tier 2/3 error depending on severity.

### 5.3 Where to Implement

In gate evaluation protocol (D-008). The pre-gate checklist should include Skill
output validation before assessing gate criteria.

---

## 6. Tmux-Specific Recovery

### 6.1 Agent Crash (Tmux Pane Closes)

When a tmux pane closes unexpectedly:
- Lead detects missing agent via `tmux list-panes` (if checking)
- More likely: coordinator detects via timeout protocol
- Recovery: Lead re-spawns agent with L1/L2 context

### 6.2 Lead Crash (Main Tmux Pane)

If Lead's session compacts or crashes:
- SessionStart(compact) hook provides recovery context
- Lead reads RTD index, orchestration plan, PT
- Lead messages all active teammates with recovery announcement

### 6.3 Multiple Simultaneous Failures

In a 42-agent system, cascading failures are possible:
- If coordinator fails + 3 workers fail simultaneously → Tier 3 emergency
- Lead should prioritize: save pipeline state → re-spawn coordinator → assess damage
- Worst case: abort pipeline, preserve all L1/L2/L3, restart from last gate

---

## 7. Options

### Option A: Minimal Protocol (Add Tier taxonomy to agent-common-protocol only)
- Define 3-tier taxonomy
- Add basic error handling guidance
- No changes to coordinator or Skill protocols

### Option B: Full Protocol (Recommended)
- Define 3-tier taxonomy
- Add agent-level error protocol to agent-common-protocol.md
- Add coordinator error escalation matrix to coordinator-shared-protocol.md (D-013)
- Add Lead error decision framework to CLAUDE.md (or reference file)
- Add D-008 post-Skill validation checklist
- Document tmux-specific recovery

### Option C: Error Protocol + Automated Recovery Scripts
- Everything in Option B
- Plus: shell scripts for tmux pane monitoring and auto-restart
- Higher complexity, potentially violates AD-15 (no new hooks)

---

## 8. User Decision Items

- [ ] Which option? (A / **B recommended** / C)
- [ ] Accept 3-tier error taxonomy (Self-recoverable / Escalation / Pipeline-affecting)?
- [ ] Accept error → tier mapping table (§3.2)?
- [ ] Accept coordinator error escalation matrix?
- [ ] Accept Lead error decision framework?
- [ ] Accept silent failure detection via D-008 post-Skill validation?
- [ ] Accept tmux-specific recovery documentation?
- [ ] Should error protocol live in agent-common-protocol.md or separate reference file?

---

## 9. Claude Code Directive (Fill after decision)

```
DECISION: Error handling & recovery — Option [X]
SCOPE:
  - agent-common-protocol.md: add §Error Handling (3-tier taxonomy)
  - coordinator-shared-protocol.md (D-013): add §Error Escalation Matrix
  - gate-evaluation-standard.md (D-008): add post-Skill validation checklist
  - CLAUDE.md: add Lead error decision framework (or reference)
  - Agent .md files: remove ad-hoc failure handling, reference shared protocol
CONSTRAINTS:
  - Hook error handling unchanged (already solid)
  - AD-15: no new hooks or scripts
  - Workers cannot resolve Tier 3 errors — must escalate
  - Tmux recovery is documented, not automated
PRIORITY: Agent protocol > Coordinator matrix > Lead framework > Tmux docs
DEPENDS_ON: D-005 (agent count), D-007 (BN-006/007), D-008 (gate), D-013 (coordinator)
```
