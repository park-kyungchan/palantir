# Phase 5 Challenge Report — SKL-006 Delivery Pipeline + RSIL

**Reviewer:** devils-advocate-1
**Date:** 2026-02-08
**Plan:** `docs/plans/2026-02-08-skl006-delivery-pipeline.md` (769 lines)
**Architecture:** `.agent/teams/skl006-delivery/phase-3/architect-1/L3-full/architecture-design.md`

---

## Challenge C-1: Correctness

### C-1.1: CLAUDE.md §10 Stale Reference — "Hooks verify L1/L2 file existence automatically" [HIGH]

**Evidence:** CLAUDE.md line 160 states: `"Hooks verify L1/L2 file existence automatically."`

After hook reduction (8→3), this statement becomes **factually incorrect**. The hooks that verified L1/L2 existence were:
- `on-subagent-stop.sh` (line 28-32): logs WARNING if L1/L2 missing
- `on-teammate-idle.sh` (line 34-48): **exit 2 blocks idle** if L1/L2 < 50B/100B
- `on-task-completed.sh` (line 39-53): **exit 2 blocks completion** if L1/L2 < 50B/100B

All three are being deleted. After deletion, **no hook verifies L1/L2 existence**.

**Plan gap:** The implementation plan does NOT include a task to update CLAUDE.md line 160. The closest reference is T-6 AC-6 which mentions "ARCHIVE.md reference in CLAUDE.md §10 line 155 is now resolvable" — but this addresses the ARCHIVE.md dead reference, NOT the stale hooks claim on line 160.

**Also affected:** CLAUDE.md line 172 states: `"hook scripts in .claude/hooks/ (automated enforcement)"` — the "automated enforcement" characterization becomes misleading after removing the enforcement hooks.

**Severity: HIGH** — The stale instruction will mislead future agents and Lead into believing L1/L2 enforcement is still automated when it has been deliberately moved to NL. This is a correctness issue in the governing document.

**Mitigation:** Add a sub-task to T-4 (or create T-4b) that updates CLAUDE.md:
- Line 160: Change to `"Agent instructions reinforce L1/L2 file creation proactively (agent .md + agent-common-protocol)."`
- Line 172: Change to `"hook scripts in .claude/hooks/ (critical-path enforcement), agent instructions (L1/L2 compliance)"`

### C-1.2: on-session-compact.sh statusMessage Still Says "DIA recovery" [LOW]

**Evidence:** settings.json line 81: `"statusMessage": "DIA recovery after compaction"`

The plan's CS-4 updates the hook's internal strings but does NOT update the `statusMessage` field in settings.json. This is a cosmetic NLP conversion miss.

**Severity: LOW** — The statusMessage is shown briefly in the UI; no functional impact.

**Mitigation:** Include settings.json statusMessage update in T-3 scope: `"DIA recovery after compaction"` → `"Recovery after compaction"`.

### C-1.3: Plan Solves Stated Goal [PASS]

The plan does correctly address the stated scope: SKL-006 creation + RSIL hook reduction + NLP conversion + agent memory templates. The 6-task decomposition covers the architecture's two workstreams. This challenge category passes with the above exceptions.

---

## Challenge C-2: Completeness

### C-2.1: Missing Agent MEMORY.md Count — Plan Says 2, Architecture Says "Up to 5" [MEDIUM]

**Evidence:**
- Architecture §4.4 (H-1): "Create initial MEMORY.md files at `~/.claude/agent-memory/{role}/MEMORY.md` for roles that don't have one yet... **Up to 5 new files** (6 roles minus architect which exists)."
- Implementation plan §4 T-5: "Create MEMORY.md templates for **tester and integrator** agents"
- Implementation plan §3 Impl-B file ownership: Only lists `tester/MEMORY.md` and `integrator/MEMORY.md` (2 files)

**Actual state verified:** 4 existing MEMORY.md files (architect, researcher, devils-advocate, implementer). Only **2 missing** (tester, integrator).

**Verdict:** The plan is CORRECT about the count (2 missing). The architecture's "up to 5" was written before verifying the actual state. The plan correctly resolves this by checking existing files. **No issue with the plan** — the architecture overestimated.

**Severity: N/A (PASS)** — Plan is accurate; architecture was conservative.

### C-2.2: No Rollback Plan for Hook Deletion [MEDIUM]

**Evidence:** The plan deletes 5 hook .sh files and removes 5 entries from settings.json. The risk mitigation (§8) addresses JSON validity (R-1) and edge case coverage (R-2) but does NOT define a rollback procedure if the NL migration proves insufficient.

If L1/L2 compliance degrades significantly after removing the blocking hooks, there is no documented path to restore them without re-creating from scratch.

**Severity: MEDIUM** — The files are in git history (recoverable via `git checkout`), but the plan should acknowledge this explicitly.

**Mitigation:** Add a note to §8 R-2: "Rollback: `git checkout HEAD -- .claude/hooks/on-subagent-stop.sh .claude/hooks/on-teammate-idle.sh .claude/hooks/on-task-completed.sh` + restore settings.json entries."

### C-2.3: Op-7 (Task List Cleanup) — TaskUpdate Tool Access [MEDIUM]

**Evidence:** SKL-006 is a Lead-only skill (Phase 9). The architecture says "Lead executes all operations directly" (§2.2 line 135). Op-7 (Task List Cleanup) requires calling TaskUpdate to mark tasks as completed and update the PT subject.

Lead has full tool access including TaskCreate/TaskUpdate, so this works. However, the skill spec (CS-1 §5) does not explicitly note that this operation needs Lead to be the executor. If a teammate ever invoked /delivery-pipeline, they'd be blocked by `disallowedTools: [TaskCreate, TaskUpdate]`.

**Severity: MEDIUM** — The "Lead-only" designation in the skill description handles this, but the skill's "When to Use" decision tree should explicitly check "Am I Lead?" as an entry condition.

**Mitigation:** Add to the When to Use decision tree: `"Are you the Pipeline Lead? ── no ──→ Only Lead can run this skill"`.

### C-2.4: NL-MIGRATE — agent-common-protocol.md Already Has L1/L2 Reminder [LOW]

**Evidence:** agent-common-protocol.md lines 57-64 ("Saving Your Work") already contains:
> "Write L1/L2/L3 files throughout your work, not just at the end. These files are your only recovery mechanism..."

The plan adds essentially the same instruction to each agent .md Constraints section. While the plan acknowledges this ("Note: agent-common-protocol.md already has this guidance in 'Saving Your Work'"), it's worth noting this is now triple-reinforcement:
1. agent-common-protocol.md (existing)
2. CLAUDE.md §10 line 168 (existing)
3. agent .md Constraints (new, from T-4)

**Severity: LOW** — Triple reinforcement is actually beneficial for NL enforcement. This is a design note, not a flaw.

### C-2.5: Missing Edit Tool for devils-advocate.md [LOW]

**Evidence:** The plan CS-6 says all 6 agents get the same NL reminder. But the plan specifically calls out: "devils-advocate.md gets a read-only variant (reminder to write L1/L2 despite being read-only for source code)."

However, the actual text in CS-6 for devils-advocate is identical to the others: "Write L1/L2/L3 files proactively throughout your work — they are your only recovery mechanism if your session compacts. Do not wait until the end."

This is fine — devils-advocate has Write/Edit tools in the custom agent instructions (my own agent definition includes these), and the agent-common-protocol already says to write L1/L2/L3. The plan's T-4 AC-4 notes a "read-only variant" but CS-6 provides the same text. Minor inconsistency between task description and change spec.

**Severity: LOW** — The actual text works for all agents regardless.

---

## Challenge C-3: Consistency

### C-3.1: Architecture §10 Item 3 vs Plan — "PR default" Unanswered [MEDIUM]

**Evidence:** Architecture §10 lists 4 "Items Requiring User Input" including:
> "3. PR default: Always offer PR creation, or only when on a non-main branch?"

The implementation plan's CS-1 §5 specifies Op-5 as "Ask user: Create a pull request?" — always offered. But this architectural question was listed as requiring user confirmation during Gate 3/4 approval. If the user didn't explicitly decide, the plan assumes "always offer."

**Severity: MEDIUM** — This was likely decided during the gate approval process. The plan should note this decision explicitly.

**Mitigation:** Add a note to CS-1 Op-5: "Per architecture §10.3 — decided: always offer PR creation (user can decline)."

### C-3.2: Architecture RSIL Count Discrepancy — "5 In-Sprint" vs Plan "7 Items" [LOW]

**Evidence:**
- Architecture AD-6 title: "5 In-Sprint, 8 Deferred"
- Architecture AD-6 table: lists 5 items (IMP-002, IMP-003, IMP-004, H-1, IMP-010)
- Plan §2 RSIL table: lists 7 items (HOOK-REDUCE, HOOK-DELETE, IMP-002, IMP-003, NL-MIGRATE, H-1, IMP-004)

The plan added HOOK-REDUCE, HOOK-DELETE, and NL-MIGRATE which weren't in the architecture's in-sprint list. These were part of the AD-15 (NL-First Boundary Framework) which was a separate architecture decision.

**Severity: LOW** — The plan correctly expanded scope based on AD-15. This is evolution, not inconsistency. But the naming difference (arch says 5 items, plan says 7) could confuse implementers.

### C-3.3: T-4 blockedBy T-2 but T-3 Not Blocked [LOW]

**Evidence:** Plan §4 T-4 says `blockedBy: [T-2]` with rationale "hooks must be removed first to avoid duplicate enforcement." But T-3 (Hook NLP conversion) also modifies hooks and has `blockedBy: []`.

This is actually correct — T-3 modifies the *remaining* hooks (on-session-compact, on-subagent-start), not the deleted ones. T-4 needs T-2 to remove the blocking hooks first because adding NL reminders while hooks still exist would create duplicate enforcement. T-3's targets are unrelated to T-4's concerns.

**Severity: N/A (PASS)** — The dependency graph is correct upon analysis.

---

## Challenge C-4: Feasibility

### C-4.1: NL Enforcement Reliability for L1/L2 — The Core Trade-off [HIGH]

**Evidence:** The plan removes three hooks that provided **hard enforcement** of L1/L2 creation:
- `on-teammate-idle.sh`: **exit 2** blocks idle if L1 < 50 bytes or L2 < 100 bytes
- `on-task-completed.sh`: **exit 2** blocks task completion if L1/L2 missing

These are replaced with a **natural language instruction** in each agent .md Constraints section:
> "Write L1/L2/L3 files proactively throughout your work — they are your only recovery mechanism if your session compacts. Do not wait until the end."

The claim (AD-15, plan IC-3): "Opus 4.6's instruction following is strong enough for non-critical enforcement."

**Challenge:** The L1/L2 hooks served as a **safety net**, not primary enforcement. Even well-intentioned agents sometimes forget to write output files, especially:
1. When context is running low (BUG-002 symptom)
2. When the agent is about to compact (most critical moment to have L1/L2)
3. After long complex analysis where the agent has consumed significant context on reasoning

The hooks caught these exact failure modes — an agent going idle without L1/L2 was blocked and reminded. The NL instruction cannot catch a "forgot to save before compacting" scenario because the agent is already losing context.

**Counter-argument:** The plan notes "triple reinforcement" (agent-common-protocol + CLAUDE.md + agent .md). Opus 4.6 does follow positive instructions reliably. The pre-compact hook (`on-pre-compact.sh`, which is KEPT) saves task state but not L1/L2 content.

**Key gap:** The `on-pre-compact.sh` hook (line 26-39) saves task list snapshots but does NOT trigger L1/L2 creation. When compaction is about to happen, there is NO mechanism (hook or NL) that forces L1/L2 to be written. The NL instruction says "proactively" but agents under context pressure are least likely to comply.

**Severity: HIGH** — The risk is real but accepted by the user via AD-15. The mitigation of triple-reinforcement is reasonable for most cases, but the compaction edge case remains unmitigated.

**Mitigation:** Consider adding to `on-pre-compact.sh` (which is KEPT) a check and warning similar to the deleted hooks: log a WARNING if the agent's L1/L2 files don't exist at pre-compact time. This is NOT a blocking action (exit 0 always) — just a diagnostic log entry. This stays within the "3 hooks only" constraint since it modifies an existing hook, doesn't add a new one.

### C-4.2: Implementer B Scope — 16 File Operations [MEDIUM]

**Evidence:** Implementer B owns:
- settings.json (modify)
- 5 .sh files (delete)
- 2 .sh files (modify)
- 6 agent .md files (modify)
- 2 MEMORY.md templates (create)

Total: 16 file operations across 5 tasks (T-2, T-3, T-4, T-5).

CLAUDE.md §6 Pre-Spawn Checklist says: "Is the scope manageable? (If >4 files, split into multiple tasks.)"

The plan does split into multiple tasks (T-2 through T-5), which satisfies the splitting requirement. But a single implementer doing 16 operations is at the upper end. The plan estimates ~250 lines changed + ~30 lines created — well within single-implementer comfort zone for mechanical edits.

**Severity: MEDIUM** — The file count is high but the edits are mostly mechanical (deletions, small insertions). The risk is manageable if the implementer reads all target files before starting.

**Mitigation:** Ensure Implementer B's directive emphasizes reading ALL target files first (AC-0 on each task already requires this). Consider splitting T-2 (delete 5 files + settings.json) and T-4 (modify 6 agent .md files) to separate implementers if context becomes a concern during Phase 6. But current plan is feasible.

### C-4.3: SKL-006 ~380 Lines — Feasible for Single Implementer [PASS]

**Evidence:** The plan estimates ~380 lines for SKL-006. verification-pipeline is 522 lines and was written by a single implementer. The architecture provides detailed structure (§2 with subsections for every operation). Reference files (verification-pipeline, brainstorming-pipeline) provide clear patterns.

**Severity: N/A (PASS)** — Feasible.

---

## Challenge C-5: Robustness

### C-5.1: Silent Behavior Loss — on-task-update.sh Logging [LOW]

**Evidence:** `on-task-update.sh` logs every TaskUpdate call to `task-lifecycle.log` (line 20). This provides an audit trail of all task state changes. After deletion, this logging silently disappears.

The plan correctly notes this is deferred to "Layer 2 audit" (plan §2 RSIL table, T-2 Key Context). But there's no Layer 2 implementation yet. Between deletion and Layer 2, there is **zero task lifecycle logging**.

**Severity: LOW** — The logging was debugging-oriented, not functional. Lead can manually review TaskList. But the gap should be documented.

### C-5.2: Silent Behavior Loss — on-tool-failure.sh Logging [LOW]

**Evidence:** `on-tool-failure.sh` logs tool execution failures to `tool-failures.log`. After deletion, tool failures go unrecorded.

Same analysis as C-5.1 — debugging aid, not functional. Lead can observe failures in real-time through agent messages.

**Severity: LOW** — Document the gap.

### C-5.3: on-subagent-stop.sh L1/L2 WARNING Logging Lost [MEDIUM]

**Evidence:** `on-subagent-stop.sh` (lines 28-32) checks if a stopping agent left L1/L2 files and logs a WARNING. This is a post-hoc diagnostic — it doesn't block anything, but it records the fact that an agent stopped without output.

After deletion, this WARNING is lost. The NL migration (agent .md reminder) is proactive ("write before you stop") but there's no post-hoc detection ("agent X stopped without output").

The most concerning scenario: an agent crashes or is killed by the system. It never gets to read the NL instruction "write L1/L2 before going idle." The hook would have caught this and logged a WARNING. Now nothing catches it.

**Severity: MEDIUM** — Crash/kill scenarios are rare but real (BUG-002 documents exactly this pattern). Lead would need to manually check for missing L1/L2 during gate evaluation.

**Mitigation:** The plan's T-6 validation (Lead task) should include a check: "For every teammate that participated, verify L1/L2 exists." This is already implied by CLAUDE.md §6 "Phase Gates: Are L1/L2/L3 generated?" — but it's worth being explicit in the SKL-006 gate evaluation.

### C-5.4: settings.json Structural Integrity After Removal [LOW]

**Evidence:** Lead's focus question #4 asked about JSON structural integrity. The plan addresses this with R-1 mitigation: "Verify with `jq .` immediately after edit."

The current settings.json has 8 hook entries as a flat object. Removing 5 entries from a JSON object is straightforward — no comma-dangling issues if the implementer uses Edit tool correctly (or jq for the modification).

**Severity: LOW** — The risk is real but well-mitigated by jq validation.

---

## Challenge C-6: Interface Contracts

### C-6.1: Implementer A/B Boundary — Clean [PASS]

**Evidence:** File ownership has zero overlap:
- Impl-A: 1 new file (SKILL.md)
- Impl-B: 16 existing file operations (modify/delete/create)

No shared file. The only conceptual dependency is that SKL-006 (Impl-A) must be consistent with the NL-First framework that Impl-B implements. But SKL-006 doesn't reference hook files or agent .md files directly.

**Severity: N/A (PASS)** — Clean separation.

### C-6.2: SKL-006 Input Interface — GC vs PT Discovery [LOW]

**Evidence:** Architecture §2.4 specifies a dual-discovery algorithm: check PT (preferred), fall back to GC. The plan's CS-1 §5 specifies Phase 9.1 Input Discovery with the same algorithm.

verification-pipeline (the pattern reference) uses GC-based discovery (V-1: "global-context.md exists with Phase 6: COMPLETE"). SKL-006 should handle both, but the pattern reference only demonstrates GC.

**Severity: LOW** — The plan explicitly specifies PT-first discovery. The implementer needs to deviate from the pattern reference (which is GC-only) to implement PT-first. This is documented but could cause confusion.

**Mitigation:** The directive to Implementer A should explicitly note: "Discovery differs from verification-pipeline pattern — use PT-first, GC-fallback as specified in architecture §2.4."

### C-6.3: SKL-006 ARCHIVE.md Template — Cross-Session Gate Aggregation [LOW]

**Evidence:** Architecture §2.5 Op-3 says: "Generate from PT + gate records (across ALL related session directories)." The ARCHIVE.md template (§3) includes a "Gate Record Summary" table spanning all phases.

The multi-session discovery algorithm finds related directories by feature name prefix. But there's no guarantee that all pipeline sessions use a consistent naming convention. Current naming:
- `{feature}` (brainstorming)
- `{feature}-write-plan` (P4)
- `{feature}-validation` (P5)
- `{feature}-execution` (P6)
- `{feature}-verification` (P7-8)

If the feature name varies between sessions (e.g., "skl006" vs "skl006-delivery"), the aggregation could miss directories.

**Severity: LOW** — The plan's Dynamic Context includes `$ARGUMENTS` for explicit feature specification, and the discovery algorithm falls back to user selection via `AskUserQuestion`.

---

## Summary of Findings

### By Severity

| Severity | Count | Issues |
|----------|-------|--------|
| CRITICAL | 0 | — |
| HIGH | 2 | C-1.1 (CLAUDE.md stale hook reference), C-4.1 (NL enforcement gap at compact time) |
| MEDIUM | 5 | C-2.2 (no rollback plan), C-2.3 (Op-7 Lead-only check), C-3.1 (PR default undecided), C-4.2 (Impl-B scope), C-5.3 (stop WARNING lost) |
| LOW | 7 | C-1.2, C-2.4, C-2.5, C-3.2, C-5.1, C-5.2, C-5.4 |
| PASS | 4 | C-1.3, C-2.1, C-3.3, C-4.3, C-6.1 |

### Critical Path Analysis

The two HIGH issues are:
1. **C-1.1** is a documentation correctness issue in the governing document (CLAUDE.md). Easy fix — add 2 line changes to Implementer B's scope.
2. **C-4.1** is the fundamental trade-off of the NL-First strategy. It's accepted by design (AD-15) with triple-reinforcement mitigation. The suggested enhancement (add WARNING to on-pre-compact.sh) stays within the 3-hook constraint and provides a safety net without blocking.

Neither issue is CRITICAL (blocking implementation). Both have actionable mitigations within the plan's scope.

---

## Verdict: CONDITIONAL_PASS

The plan is well-structured, the task decomposition is clean, and the file ownership boundaries are sound. The two HIGH issues have feasible mitigations:

1. **C-1.1:** Add CLAUDE.md line 160 and 172 updates to Implementer B's T-4 scope (2 line changes)
2. **C-4.1:** Optionally enhance on-pre-compact.sh to log a WARNING if active agent lacks L1/L2 (stays within 3-hook constraint)

With these mitigations applied, the plan is ready for Phase 6 implementation.
