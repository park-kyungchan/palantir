# [PERMANENT] Task API Guideline — Agent Teams Edition

> **Status:** [PERMANENT] — Must be read by EVERY agent before ANY Task API call.
> **Applies to:** Lead, all Teammates, all Subagents spawned by Teammates.
> **Version:** 3.0 (DIA Enforcement + LDAP) | Updated: 2026-02-07
>
> **OWNERSHIP NOTE:** Only Lead may call TaskCreate/TaskUpdate.
> Teammates: TaskList/TaskGet only (read-only).

---

## 1. Mandatory Pre-Call Protocol

**BEFORE** calling `TaskCreate`, `TaskUpdate`, `TaskList`, or `TaskGet`:

1. Read this file (`.claude/references/task-api-guideline.md`)
2. Read your own context:
   - **Teammates:** Read injected context from [DIRECTIVE] (global-context.md + task-context.md)
   - **Lead:** Read `orchestration-plan.md`
3. Ensure Task description meets the Comprehensive Requirements below

---

## 2. Task Storage Architecture

### Scoping Rules (ABSOLUTE — Cross-scope access is IMPOSSIBLE)

| Context | Storage Location | Accessible By |
|---------|-----------------|---------------|
| Team session | `~/.claude/tasks/{team-name}/` | All team members (Lead + Teammates) |
| Solo session (no team) | `~/.claude/tasks/{sessionId}/` | That session only |

- **Always use TeamCreate** to establish team scope — avoids session-scoped task orphaning
- `CLAUDE_CODE_TASK_LIST_ID` env var → forces shared task list override

### File Structure
```
~/.claude/tasks/{scope}/
├── {id}.json         ← Individual task (numeric ID, e.g., "1", "12")
├── .lock             ← File lock (prevents race conditions on concurrent access)
└── .highwatermark    ← Next task ID counter (system-managed, do NOT modify)
```

### Cross-Agent Visibility (Team Scope)
| Operation | Lead↔Teammate | Teammate↔Teammate |
|-----------|---------------|-------------------|
| TaskCreate | Visible ✅ | Visible ✅ |
| TaskGet | Accessible ✅ | Accessible ✅ |
| TaskUpdate | Mutable ✅ | Mutable ✅ |
| TaskList | Full team view ✅ | Full team view ✅ |

### Ownership Partitioning (DIA Enforcement v2.0)

| Operation | Lead | Teammate |
|-----------|------|----------|
| TaskCreate | Sole writer | FORBIDDEN (disallowedTools) |
| TaskUpdate | Sole writer | FORBIDDEN (disallowedTools) |
| TaskList | Full access | Read-only |
| TaskGet | Full access | Read-only |

---

## 3. Comprehensive Task Creation

> **Note:** This section applies to **Lead only**. Teammates cannot call TaskCreate.

Every `TaskCreate` call MUST produce a task that is:
- **DETAILED** — No ambiguity in what needs to be done
- **COMPLETE** — All acceptance criteria explicitly listed
- **DEPENDENCY-AWARE** — Full dependency chain documented
- **IMPACT-AWARE** — Downstream impact explicitly stated
- **VERIFIABLE** — Clear success/failure criteria

### Required Fields

**subject:** Imperative action verb + specific target
- Good: "Implement user authentication module"
- Bad: "Work on auth"

**description:** Must include ALL of the following sections:

```
## Objective
[What this task accomplishes — 1-2 sentences]

## Context in Global Pipeline
- Phase: [which phase this belongs to]
- Upstream: [what tasks produced the inputs for this task]
- Downstream: [what tasks depend on this task's output]

## Detailed Requirements
1. [Specific requirement]
2. [Specific requirement]
...

## Interface Contracts
- [What interfaces/APIs this task must satisfy]
- [What data formats this task must produce]

## File Ownership
- [Exact list of files this task may create/modify]

## Dependency Chain
- blockedBy: [list of task IDs, or [] if none]
- blocks: [list of task IDs that wait for this task]

## Acceptance Criteria
1. [Verifiable criterion]
2. [Verifiable criterion]
...

## Semantic Integrity Check
- [PERMANENT] rules this task enforces: [list]
- Downstream impact if output changes: [description]
```

**activeForm:** Present continuous form (e.g., "Implementing user authentication")

---

## 4. Dependency Chain Rules

| Rule | Rationale |
|------|-----------|
| Every task MUST declare `blockedBy` (even if empty `[]`) | Forces conscious consideration of dependencies |
| Every task MUST declare what it `blocks` | Forces awareness of downstream impact |
| Circular dependencies are FORBIDDEN | Prevents deadlocks in distributed execution |
| Cross-Teammate dependencies MUST be reported to Lead | Lead needs this for DIA cross-impact analysis |

### Dependency Behavior (Verified)
- `addBlockedBy(["X"])` → **Bidirectional auto-sync**: `this.blockedBy += ["X"]` AND `X.blocks += [this.id]`
- `addBlocks(["Y"])` → **Bidirectional auto-sync**: `this.blocks += ["Y"]` AND `Y.blockedBy += [this.id]`
- **Blocker completion does NOT auto-remove blockedBy entries** — they persist as permanent record
- **TaskList filters blockedBy to show only OPEN blockers** — use TaskList (not TaskGet) to determine if truly blocked
- **TaskGet shows raw blockedBy** (includes completed blockers) — do NOT use for blocked/unblocked judgment

---

## 5. Task Lifecycle

```
pending ──→ in_progress ──→ completed
  │                              │
  │                              └──→ [CAUTION] File may be auto-cleaned (see §8)
  │
  └──→ deleted (file immediately removed from disk, "Task not found" on access)
```

- **Before starting:** Check `blockedBy` is resolved (use TaskList, not TaskGet)
- **During work:** Update status to `in_progress`
- **On completion:** Update to `completed` + send Status Report to Lead
- **On blocker:** Update with `addBlockedBy` + send Status Report with BLOCKED
- **Delete:** `status: "deleted"` permanently removes the task JSON from disk

---

## 6. [PERMANENT] Semantic Integrity Integration

### Lead-Level (DIA Enforcement)
Before EVERY Task API call:
1. Read `orchestration-plan.md` — understand current pipeline state
2. Read all active teammates' L1-index.yaml — understand current progress
3. Verify no cross-impact conflicts exist
4. Update task-context.md for affected teammates if deviation detected
5. Embed FULL global-context.md (GC-v{N}) + task-context.md in EVERY [DIRECTIVE]
6. Review teammate [IMPACT-ANALYSIS] before approving any work
7. Conduct [VERIFICATION-QA] for gaps in teammate understanding

### Teammate-Level
On EVERY [DIRECTIVE] received:
1. Parse [INJECTION] — extract global-context.md and task-context.md
2. Send [STATUS] CONTEXT_RECEIVED with version numbers
3. Submit [IMPACT-ANALYSIS] before ANY work begins
4. Wait for [IMPACT_VERIFIED] before proceeding
5. Reference .claude/references/task-api-guideline.md for protocol rules

### Task API Restrictions (Teammates)
- TaskList: Read-only access — check task status and dependencies
- TaskGet: Read-only access — retrieve task details
- TaskCreate: FORBIDDEN (enforced via disallowedTools in agent definition)
- TaskUpdate: FORBIDDEN (enforced via disallowedTools in agent definition)
- State persistence: Use L1/L2/L3 files + SendMessage to Lead

---

## 7. Anti-Patterns

| Anti-Pattern | Correct Pattern |
|-------------|----------------|
| `TaskCreate({subject: "Do the thing"})` | Full comprehensive description |
| Skipping `blockedBy` declaration | Always declare, even if `[]` |
| Not reading task-context.md first | ALWAYS read before Task API call |
| Creating tasks without acceptance criteria | Every task must be verifiable |
| Ignoring downstream impact | Always state what this task blocks |
| Updating status without Status Report | Always notify Lead on completion |
| Using TaskGet to check if task is blocked | Use TaskList — it filters completed blockers |
| Relying on completed task data persistence | Save important info to separate files |
| Mixing team scope and session scope | Always use TeamCreate for team work |
| Teammate calling TaskCreate/TaskUpdate | FORBIDDEN — Lead only (enforced by disallowedTools) |

---

## 8. Known Issues & Operational Cautions

### ISS-001: Completed Task Auto-Cleanup [HIGH]
- **Completed tasks may be auto-deleted from disk** under certain conditions
- Exact trigger unknown (possible: background GC, time-based, turn boundary)
- **Mitigation:** Do NOT rely on completed task data. Save critical information to L1/L2/L3 files or separate artifacts before marking complete.

### ISS-002: TaskGet vs TaskList — blockedBy Display Mismatch [MEDIUM]
- TaskGet shows raw `blockedBy` array (includes completed blockers)
- TaskList shows only open blockers (correctly filtered)
- **Mitigation:** Always use TaskList output to determine blocked status.

### ISS-003: Task Orphaning on Context Clear [HIGH]
- Context clear creates new sessionId → previous session's tasks become invisible
- **Mitigation:** Always use Team scope. Set `CLAUDE_CODE_TASK_LIST_ID` env var if needed.

### ISS-004: Platform Limitations
| Limitation | Impact | Workaround |
|-----------|--------|-----------|
| `/resume` cannot restore teammates | Spawn new teammates | Plan for teammate replacement |
| Task status lag (teammate miss marking) | Dependent tasks appear stuck | Lead manually updates |
| One team per session | Cannot run parallel teams | Sequential team lifecycle |
| No nested teams | Teammates cannot create sub-teams | Only Lead spawns teams |
| Fixed lead (no leadership transfer) | Lead is permanent | Plan at team creation |

---

## 9. Sub-Orchestrator Task Patterns

When a Teammate acts as Sub-Orchestrator (spawning subagents via Task tool):

1. **Task tool only:** Use Task tool to spawn subagents — NOT TaskCreate (forbidden)
2. **Communication:** Use SendMessage to coordinate with subagents, report to Lead
3. **Nesting Limit:** Subagents spawned by Teammate CANNOT spawn further subagents (depth = 1)
4. **Boundary Constraint:** All sub-work must stay within the Teammate's assigned file ownership
5. **Reporting:** Report significant sub-orchestration decisions to Lead via SendMessage
6. **Shared Task List:** Lead-only. Teammates coordinate sub-work through direct messaging, not Task API.

---

## 10. Metadata Operations

| Operation | Syntax | Result |
|-----------|--------|--------|
| Add key | `metadata: {"key": "value"}` | Merged into existing |
| Update key | `metadata: {"key": "new_value"}` | Overwrites value |
| Delete key | `metadata: {"key": null}` | Key removed |
| Unchanged keys | (not included in update) | Preserved |

---

## 11. DIA Enforcement Protocol

### Context Injection Protocol (CIP)

Every [DIRECTIVE] from Lead to Teammate MUST include:
1. Global-context.md full text (with version: GC-v{N})
2. Task-context.md full text
3. Explicit [REQUIRED] context receipt confirmation instruction

**WHY:** Eliminates GAP-001 (no read verification) and GAP-005 (auto-compact context loss).
Physical embedding guarantees delivery regardless of teammate's context window state.

**Injection Points:**
| ID | Trigger | Content | Method |
|----|---------|---------|--------|
| IP-001 | Initial Spawn | GC + TC full text | Task tool prompt |
| IP-002 | Mid-session Assignment | GC + TC full text | SendMessage |
| IP-003 | Interface Change | GC + TC (affected teammates) | SendMessage |
| IP-004 | Architecture Change | GC + TC (ALL teammates) | Sequential SendMessage |
| IP-005 | Auto-compact Recovery | GC + TC + L1/L2 | SendMessage |
| IP-006 | L1/L2/L3 Handoff Replacement | GC + TC + predecessor L1/L2 | Task tool prompt |
| IP-007 | Plan Approval/Rejection | Version assert header only | SendMessage |
| IP-008 | Deviation Correction | Updated TC full text | SendMessage |
| IP-009 | Phase Broadcast | GC only | Broadcast |

### Impact Awareness Verification Protocol (DIAVP)

**WHY:** Eliminates GAP-002 (read ≠ understood). Echo-back in own words proves comprehension.
Verification before execution prevents rework cost (prevention << correction).

**Verification Tiers:**
| Tier | Agent Type | IAS Sections | Checklist Items | Max Attempts |
|------|-----------|-------------|-----------------|-------------|
| TIER 1 (Full) | implementer, integrator | 6 | 10 (RC-01~10) | 3 |
| TIER 2 (Standard) | architect, tester | 4 | 7 (RC-01~07) | 3 |
| TIER 3 (Lightweight) | researcher | 3 | 5 | 2 |
| TIER 0 (Exempt) | devils-advocate | N/A | N/A | N/A |

**Lead's Review Checklist (RC):**
| ID | Criterion | Failure Meaning |
|----|-----------|----------------|
| RC-01 | Task accurately restated in own words | Task itself misunderstood |
| RC-02 | Phase position correctly identified | Pipeline awareness absent |
| RC-03 | Upstream artifacts specifically referenced | Context files not actually read |
| RC-04 | Affected file list is complete | Change scope incomplete |
| RC-05 | Interface signatures are accurate | Interface spec not mastered |
| RC-06 | Cross-teammate impact identified | Isolated thinking |
| RC-07 | Downstream causal chain explained | Ripple effect reasoning absent |
| RC-08 | Breaking change risk assessed | Vulnerability awareness absent |
| RC-09 | No factual errors in claims | Information fabrication |
| RC-10 | No critical omissions vs Lead DIA | Analysis blind spots |

**Verification Flow:**
1. Teammate submits [IMPACT-ANALYSIS] to Lead
2. Lead reviews against RC checklist:
   - ALL PASS → [IMPACT_VERIFIED] Proceed.
   - 1-2 FAIL (non-critical) → [VERIFICATION-QA] → Teammate answers → re-evaluate
   - 1-2 FAIL (RC-05/06/07) → [VERIFICATION-QA] mandatory → correction confirmation
   - 3+ FAIL → [IMPACT_REJECTED] + [RE-EDUCATION] (Attempt N/3)
3. Max 3 failures → [IMPACT_ABORT] → Teammate terminated → re-spawn with enhanced context

**Layer 3: Adversarial Challenge Protocol (LDAP)**

**WHY:** Eliminates GAP-003 (understood but no systemic impact awareness).
RC checklist verifies "do you understand WHAT to do?" but not "do you understand
HOW your work affects the interconnected system?" LDAP forces critical reasoning
about interconnection (GAP-003a) and ripple propagation (GAP-003b).

**GAP-003 Definition:**
- GAP-003a (Interconnection Blindness): Teammate does not see how their module participates
  in the organic/integrated operation of the whole system.
- GAP-003b (Ripple Blindness): Teammate cannot trace where and how far their changes
  propagate through the entire task scope and codebase.

**Challenge Categories:**

| ID | GAP | Purpose |
|----|-----|---------|
| INTERCONNECTION_MAP | 003a | Verify module participation in organic whole |
| SCOPE_BOUNDARY | 003a | Verify scope is neither too narrow nor too wide |
| RIPPLE_TRACE | 003b | Verify change propagation tracing to terminal effects |
| FAILURE_MODE | 003b | Verify system-wide failure consequence awareness |
| DEPENDENCY_RISK | 003b | Verify upstream volatility propagation awareness |
| ASSUMPTION_PROBE | 003a+b | Challenge unstated assumptions hiding impact gaps |
| ALTERNATIVE_DEMAND | 003a+b | Force consideration of systemic alternatives |

**Challenge Intensity by Phase:**

| Phase | Level | Min Questions | Alternative Required | Reason |
|-------|-------|--------------|---------------------|--------|
| P1 | NONE | 0 | — | Lead only phase |
| P2 | MEDIUM | 1 | No | Research scope verification |
| P3 | MAXIMUM | 3 | Yes | Architecture — cheapest to fix |
| P4 | MAXIMUM | 3 | Yes | Detailed design — cheapest to fix |
| P5 | EXEMPT | 0 | — | Devils-advocate owns critique |
| P6 | HIGH | 2 | No | Implementation — code-level propagation |
| P7 | MEDIUM | 1 | No | Testing — scope and failure awareness |
| P8 | HIGH | 2 | No | Integration — cross-boundary awareness |
| P9 | NONE | 0 | — | Lead only phase |

**Challenge Flow (within Gate A, after RC evaluation):**
1. Lead reads teammate's [IMPACT-ANALYSIS] content
2. Lead identifies weak spots in systemic impact reasoning
3. Lead generates N questions (N = phase intensity min_questions)
4. Lead sends: `[CHALLENGE] Phase {N} | Q{X}/{total}: {question} | Category: {category_id}`
5. Teammate responds: `[CHALLENGE-RESPONSE] Phase {N} | Q{X}: {defense}`
6. Repeat for all questions (turn-based via IDLE-WAKE cycle)
7. Lead evaluates combined RC + challenge defense quality:
   - Strong defense → [IMPACT_VERIFIED] Proceed.
   - Partial defense → [VERIFICATION-QA] follow-up for specific gaps
   - Failed defense → [IMPACT_REJECTED] with challenge evidence cited
8. For MAXIMUM intensity: teammate MUST propose at least one alternative approach
   with its own interconnection map and ripple profile

**Enforcement Mechanism:**
- Structural: Lead withholds [IMPACT_VERIFIED] until challenge defense passes
- Turn-based: Teammate IDLE after [IMPACT-ANALYSIS] → Lead sends [CHALLENGE] →
  Teammate WAKES → responds → IDLE → Lead evaluates (natural pause via IDLE state)
- Hard: Gate A prerequisite for Gate B (implementer/integrator)
- Soft: Agent .md Phase 1.5 instructions (guidance)

**Defense Quality Criteria:**
- Strong: Specific module names, concrete propagation paths, quantified blast radius
- Weak: Vague claims, generic statements, missing propagation paths
- Failed: No systemic reasoning, copy-paste from [IMPACT-ANALYSIS], factual errors

**Compaction Recovery:**
- Challenge round/state persisted in task-context.md by Lead
- PreCompact hook includes challenge state in pre-compact snapshot
- On recovery: Lead re-injects task-context.md with challenge state → resumes from last round

**Two-Gate Flow (implementer/integrator only):**
- Gate A: [IMPACT-ANALYSIS] → [IMPACT_VERIFIED] (understanding gate)
- Gate B: [PLAN] → [APPROVED] (execution plan gate)
- Gate A is prerequisite for Gate B. No [PLAN] submission without Gate A pass.

---

## 12. CLAUDE_CODE_TASK_LIST_ID Usage

For persistent task management across sessions:
```
CLAUDE_CODE_TASK_LIST_ID=palantir-dev claude
```

**Priority resolution:**
1. `CLAUDE_CODE_TASK_LIST_ID` env var (highest priority)
2. `team_name` parameter from TeamCreate
3. Session-scoped default (lowest priority — avoid for team work)

**Benefits:**
- Tasks persist across `/resume` and context clears
- All team members share the same task namespace
- Avoids ISS-003 (task orphaning on context clear)
