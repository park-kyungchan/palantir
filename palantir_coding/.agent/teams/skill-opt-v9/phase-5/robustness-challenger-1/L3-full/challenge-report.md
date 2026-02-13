# Robustness Challenge Report — Skill Optimization v9.0

> **Agent:** robustness-challenger-1
> **Phase:** P5 (Plan Validation)
> **Scope:** C-5 (Robustness) + C-6 (Interface Contracts)
> **Artifacts Reviewed:** Implementation plan (630L), Phase 3 architecture (arch-coord L2, risk L3, interface L3, structure L3), Phase 4 design (decomposition L3, strategy L3, interface-planner L3)

---

## C-5: Robustness Challenges

### ROB-1: BUG-002 Escalation — infra-c (8 files) Has No Partial Completion Recovery

**Severity:** HIGH
**Section Ref:** §3 Ownership Verification, §10 Rollback & Recovery

**Scenario:** infra-c (infra-implementer) is assigned 8 coordinator .md files. Despite being described as "small files (38-83L), highly templated," the implementer must:
1. Read all 8 current files (768L total current state)
2. Read coordinator-shared-protocol.md + agent-common-protocol.md (references)
3. Read Template B design from structure-architect L3 §5.2 (~120L)
4. Read gap analysis from §5 per-file specifications (~200L estimated)
5. Apply transformations to each of 8 files (write operations)
6. Write L1/L2/L3 output

**Total estimated read load:** ~1,200L+ before any writing begins. With tool call overhead (Read tool calls, Glob for discovery, Write for each file + L1/L2/L3), this agent faces significant context pressure.

**The gap:** §10 (Rollback & Recovery) addresses pre-commit and post-commit rollback but **never addresses mid-implementation partial completion**. If infra-c compacts after transforming 5/8 coordinators:
- 5 coordinators are in Template B (new format)
- 3 coordinators remain in Template A (old format)
- No consistency across the 8 — verifier (Task V) would catch this, but the plan has no protocol for "re-spawn infra-c for remaining 3 files only"

**Proposed Mitigation:**
1. Add explicit instruction in Task C: "Write L1 after EACH file completion (not just at the end), listing completed files"
2. Add to §10 a "Mid-Implementation Partial Completion" recovery protocol: "If implementer compacts, Lead reads L1 to identify completed files, re-spawns with only remaining files"
3. Consider splitting infra-c into two: infra-c1 (4 Template A→B: research, verification, execution, testing) and infra-c2 (4 already-Template-B: architecture, planning, validation, infra-quality). This stays within BUG-002 4-file guideline.

---

### ROB-2: BUG-002 Escalation — impl-b (5 large SKILL.md files) Is the True Critical Path

**Severity:** HIGH
**Section Ref:** §3 Ownership Verification, §6 Execution Sequence

**Scenario:** impl-b must read and restructure 5 coordinator-based SKILL.md files ranging from 362L to 692L. Total: ~2,475L of current content alone. Plus architecture references (~300L), template structure (~150L), and L1/L2/L3 output.

**The plan acknowledges this risk** (§3 shows "⚠ exceeds 4, justified: same template variant") but the justification is weak. "Same template variant" reduces cognitive complexity but does NOT reduce context window consumption. Each SKILL.md requires full read → structural analysis → restructure → write.

**Critical path analysis:** §6 timeline shows impl-a1 as the critical path (4 files, 2 creates). This is WRONG. impl-b has 5 files of 362-692L each. Even though it processes smaller number of creates, the total read+write volume is ~3x higher than impl-a1. impl-b is the true critical path for Wave 1.

**If impl-b compacts at file 3/5:** The same partial completion problem as ROB-1, but worse because these are large, structurally complex files. A new impl-b-2 would need to read the architecture references again, understand the template, and complete the remaining 2 files — essentially re-incurring the startup cost.

**Proposed Mitigation:**
1. Reorder impl-b's processing: smallest first (as already specified), but add explicit L1 checkpointing after EACH file
2. Add an explicit splitting contingency: if impl-b reaches 60% context after 3 files, Lead should be prepared to spawn impl-b-2 for files 4-5
3. Consider whether the two most complex skills (brainstorming-pipeline 613L + agent-teams-execution-plan 692L) should be their own implementer, reducing impl-b to 3 files

---

### ROB-3: Fork Context:fork Returns Error — No Error Taxonomy in Plan

**Severity:** MEDIUM-HIGH
**Section Ref:** §8 Pre-Deploy Validation (Phase A4)

**Scenario:** The plan assumes `context:fork` works but acknowledges it's untested in this codebase (RISK-1). Phase A4 tests fork spawn mechanism. However, the plan provides NO error taxonomy for fork failures. What specific errors might `context:fork` produce?

Possible failure modes:
1. **Agent .md not found:** `agent: "pt-manager"` but `pt-manager.md` doesn't exist or is in wrong directory → skill invocation error
2. **Agent .md parse error:** YAML frontmatter in agent .md is malformed → fork loads with default agent behavior?
3. **Fork context isolation:** Fork starts but with unexpected tool restrictions or permissions
4. **Dynamic Context command failure:** `!command` in Dynamic Context fails → skill body rendered with error text or empty
5. **$ARGUMENTS too large:** CC has undocumented limits on $ARGUMENTS size → truncation or rejection

**The gap:** Phase A4 says "Critical — investigate" for fork spawn failure. This is a black box. The plan needs:
- Specific expected behavior for each failure mode
- Whether CC returns an error message, loads a default agent, or silently fails
- Whether the fork skill body is still visible to the agent if the agent .md fails to load

**Proposed Mitigation:**
1. Add pre-Phase-A research step: create a minimal test skill with `context:fork` + `agent: "nonexistent-agent"` to observe CC's error behavior
2. Document the error taxonomy in the implementation plan so that Phase A validation can check against expected behaviors
3. Add FM-8 to the Failure Mode Catalog covering context:fork error responses

---

### ROB-4: Coordinator Convergence Regression — Template B May Break execution-coordinator

**Severity:** MEDIUM-HIGH
**Section Ref:** §5 Gap Analysis (Task C), structure-architect L3 §5.2

**Scenario:** execution-coordinator has ~45L of UNIQUE review dispatch logic (ADR-S2 exemption). It's the most complex coordinator at 151L. The convergence to Template B requires:
1. Remove ~68L of inlined protocol (Worker Management, Communication, Understanding Verification, Failure Handling, Recovery)
2. Add 2-line protocol references
3. Retain ~45L unique review dispatch logic
4. Restructure from Template A sections to Template B sections (Role, Before Starting Work, How to Work, Output Format, Constraints)

**The risk:** The review dispatch logic in execution-coordinator is tightly coupled to its current section structure. Moving it from the current "How to Work" into a new "How to Work" section within Template B requires careful preservation of:
- Two-stage review protocol (spec-reviewer → code-reviewer chain)
- Fix loop iteration tracking
- Contract-reviewer and regression-reviewer dispatch conditions
- Worker stage transition management

If any of this unique logic is accidentally removed or restructured incorrectly during the Template A→B transformation, execution-coordinator loses its core differentiating capability. This is particularly risky because the infra-c implementer is processing 8 files — cognitive load increases the chance of mistakes on the most complex file.

**Proposed Mitigation:**
1. Make execution-coordinator.md the FIRST file infra-c processes (not mixed into the middle) — highest risk should be done with freshest context
2. Add a V6b-specific check: "execution-coordinator retains Two-Stage Review Protocol section with spec-reviewer/code-reviewer/contract-reviewer/regression-reviewer dispatch"
3. Consider making execution-coordinator a separate task from the other 7, given its unique complexity

---

### ROB-5: RISK-2 Escalation — permanent-tasks Fork Context Loss Is Worse Than Documented

**Severity:** MEDIUM
**Section Ref:** §8 RISK-2 Mitigation

**Scenario:** The 3-layer mitigation for RISK-2 is well-designed for pipeline auto-invocation (Layer 1) and rich manual invocation (Layer 2). But Layer 3 (sparse $ARGUMENTS) reveals a deeper problem.

**What Layer 3 actually means in practice:** A user types `/permanent-tasks` with no arguments. The pt-manager fork agent starts with:
- No conversation history
- No $ARGUMENTS (or empty string)
- Dynamic Context: git log, plans list, infrastructure version — generic session state

The agent must now figure out what the user wants to update in the PT. It has AskUserQuestion, but **it doesn't even know what the current conversation context was about**. The user might have been discussing a bug fix, a feature design, or an architecture decision. The pt-manager has zero knowledge of this.

**Comparison with current Lead-in-context:** Today, Lead reads the conversation history, understands what just happened, and updates the PT accordingly. The step-down from this to "AskUserQuestion from a blank slate" is more severe than "degraded but functional."

**Worse scenario:** Mid-pipeline, Lead invokes `/permanent-tasks` to update the PT after requirements changed. $ARGUMENTS carries the change description, but the pt-manager can't validate whether the change is consistent with the existing pipeline state because it has no conversation history about what happened in the current session.

**Proposed Mitigation:**
1. Accept this as a known UX degradation and document it clearly
2. Add to permanent-tasks SKILL.md Dynamic Context: `!cat .agent/teams/{session}/orchestration-plan.md 2>/dev/null` — gives the fork agent pipeline state context
3. Strengthen the AskUserQuestion protocol: require pt-manager to ask "What is the current context of your work?" as its first question when $ARGUMENTS is empty

---

### ROB-6: RISK-3 Escalation — Delivery Fork Mid-Sequence Failure Window

**Severity:** MEDIUM
**Section Ref:** §8 RISK-3 Mitigation

**Scenario:** The plan identifies delivery fork's 7-operation sequence and notes idempotent design. However, there's a specific failure window that isn't addressed:

**Failure window:** Between Op-2 (MEMORY.md write) and Op-4 (git commit):
1. Op-2: MEMORY.md updated via Read-Merge-Write ✓
2. Op-3: ARCHIVE.md created ✓ (idempotent)
3. **Fork crashes here** (context limit, CC platform error, user cancellation)
4. Op-4: Git commit never happens

**State:** MEMORY.md has been modified (Op-2) but not committed. ARCHIVE.md exists but isn't committed. The user now has dirty working tree state that doesn't match any commit.

**The plan says:** "Recovery: user re-runs /delivery-pipeline — discovery algorithm picks up partial state." But re-running delivery-pipeline will:
1. Re-discover sessions ✓
2. Attempt Op-2 again → Read-Merge-Write on already-modified MEMORY.md → potential duplication of merged content
3. Create ARCHIVE.md again ✓ (overwrite-safe)

**The gap:** The Read-Merge-Write pattern for MEMORY.md is NOT idempotent in the presence of a previous partial write. If the first run merged "Session X findings" into MEMORY.md, the second run would attempt to merge the same findings again, potentially creating duplicate entries.

**Proposed Mitigation:**
1. delivery-agent should write a `delivery-state.yaml` checkpoint file after each operation, recording which operations completed
2. On re-run, check delivery-state.yaml and skip completed operations
3. Alternatively, document that the user should `git checkout -- MEMORY.md` before re-running if a mid-sequence failure occurs

---

### ROB-7: RISK-3 Escalation — Nested Skill Dependency in delivery-pipeline

**Severity:** LOW-MEDIUM
**Section Ref:** §8 RISK-3 Mitigation Layer 1

**Scenario:** The plan correctly eliminates nested /permanent-tasks invocation from delivery-pipeline. The delivery-agent will instead say "Please run /permanent-tasks first." However:

**Edge case:** What if the user has already run `/permanent-tasks` but the PT isn't in the expected "Phase 7/8 COMPLETE" state? For example:
- User ran `/permanent-tasks` for a different purpose (mid-pipeline update)
- PT exists but phase_status doesn't show P7/P8 COMPLETE
- delivery-agent finds PT but can't proceed with delivery

**The plan's Phase 0 check says:** "Verify PT exists with Phase 7/8 COMPLETE." But it doesn't specify the behavior when PT exists but phases aren't complete. Does it:
a. Abort with "Pipeline not complete — please complete phases first"?
b. Offer to proceed anyway with a warning?
c. Show what phases ARE complete and ask user to confirm?

**Proposed Mitigation:**
1. Specify in the delivery-pipeline skill body: explicit handling for "PT exists but pipeline incomplete" — show phase_status summary, ask user to confirm whether to proceed
2. This is a common real-world scenario (user wants to do partial delivery or delivery of a subset of changes)

---

### ROB-8: Pre-Deploy Validation Failure at Step C — Rollback of Steps A and B

**Severity:** MEDIUM
**Section Ref:** §8 Pre-Deploy Validation Sequence

**Scenario:** Pre-deploy validation runs A → B → C → D. If Step C fails (rsil-review + permanent-tasks functional test):

**State at failure:**
- Step A: Structural validation PASSED (all V6a checks clean)
- Step B: rsil-global functional PASSED (fork works, Dynamic Context renders)
- Step C: permanent-tasks FAILS (e.g., pt-manager can't create PT via Task API from fork)

**Question:** What happens to the files that passed Steps A and B? They are already validated and correct. But the plan's fix-loop says "fix → re-run":
1. Fix pt-manager.md or permanent-tasks SKILL.md
2. Re-run C1

**Shared file rule (correctly identified):** "if C fix touches rsil-agent.md → re-run B." But this only covers rsil-agent.md sharing. What about:
- If the fix touches CLAUDE.md §10 (adding a constraint) → should we re-run A?
- If the fix touches agent-common-protocol.md (protocol clarification) → does this affect any completed validation?

**The gap:** The shared-file awareness rule covers rsil-agent.md but doesn't cover the PROTOCOL FILES (CLAUDE.md, agent-common-protocol.md). These files are consumed by ALL agents and ALL skills. A fix to §10 during Phase C could theoretically affect behaviors validated in Phase B.

**Proposed Mitigation:**
1. Extend the shared-file awareness rule: "If ANY Phase C/D fix modifies CLAUDE.md or agent-common-protocol.md → re-run from Phase A (structural re-validation)"
2. In practice, Phase C/D fixes should almost never touch protocol files — they should only touch agent .md and SKILL.md. Add this as an explicit constraint: "Phase C/D fixes MUST NOT modify CLAUDE.md or agent-common-protocol.md without re-running the full A→D sequence"

---

### ROB-9: BUG-002 Triggers During Verification (Task V)

**Severity:** MEDIUM
**Section Ref:** §4 Task V, §6 Wave 2

**Scenario:** The verifier (integrator type) must read ALL 22 files for cross-reference validation. Total read load estimate:
- 9 SKILL.md files: ~4,000L (range 280-692L each)
- 8 coordinator .md: ~400L (target ~38-83L each)
- 3 fork agent .md: ~300L (target ~85-100L each)
- CLAUDE.md: ~378L
- agent-common-protocol.md: ~247L
- **Total: ~5,325L**

This is a massive read load. The verifier must also cross-reference patterns across files, meaning many files need to be read partially multiple times.

**The risk:** If the verifier compacts mid-verification:
- Some checks may have completed, others not
- The verifier's partial L1/L2 output may show PASS for checks 1-5 but checks 6-8 are unknown
- Lead would need to re-spawn the verifier for remaining checks, but the new verifier doesn't know which checks already passed

**Proposed Mitigation:**
1. Verifier should write L1 incrementally: after each of the 8 checks, update L1-index.yaml with the check result
2. If re-spawned, the new verifier reads its own L1 and skips already-passed checks
3. Consider splitting verification: V-structural (checks 1, 2, 6, 7, 8 — frontmatter/schema) and V-naming (checks 3, 4, 5 — cross-reference names). This reduces per-agent read load.

---

## C-6: Interface Contracts Challenges

### IFC-1: C-1 through C-6 Contract Completeness in Implementation Plan

**Severity:** MEDIUM
**Section Ref:** §2 Interface Contracts

**Analysis of each contract's specification completeness:**

| Contract | Specified? | Gap |
|----------|:---------:|-----|
| C-1 (PT Read/Write) | ✓ Complete | §5 references interface-planner L3 §1. Per-skill table in §5 Per-Skill Specifications. No gap. |
| C-2 (L2 Handoff chain) | ⚠ Partial | §5 references the chain but doesn't specify EXACTLY what each §Downstream Handoff section must contain for the next skill. The 6-category format is defined in protocol, but the per-skill expected content within those categories is not in the implementation plan. |
| C-3 (GC scratch-only) | ✓ Complete | §5 GC Migration Summary specifies removes/replaces/keeps per skill. Clear. |
| C-4 (Fork-to-PT Direct) | ⚠ Partial | Assumes task list scope (RISK-8 dependency). Well-documented but not validated. |
| C-5 (§10 exception) | ✓ Complete | §5 §10 Modification provides exact old→new text. 4-way naming contract fully specified. |
| C-6 (4-way naming) | ✓ Complete | §5 4-Way Naming Contract table provides all 4 locations × 3 agents. |

**C-2 gap detail:** The L2 Downstream Handoff chain has 6 links (brainstorming→write-plan→validation→execution→verification→delivery). The interface-planner L3 §5 specifies the protocol format (6 categories), but the implementation plan doesn't specify what SPECIFIC content each coordinator should place in each category for the next phase. This is important because:
- If brainstorming's arch-coord doesn't include "Architecture Decisions" in §Decisions Made, write-plan can't find it
- If execution's exec-coord doesn't include "Implementation Results Summary" in §Artifacts Produced, verification can't discover it
- The content is currently in GC — when GC is removed, the L2 must carry ALL this content or it's lost

**Proposed Mitigation:**
1. Add to Task B instructions: "For each skill's §C Interface → Next section, specify the minimum content the predecessor L2 must contain for this skill to function"
2. This doesn't need to be in the implementation plan directly — the implementer can derive it from the GC migration table — but it should be called out as an acceptance criterion

---

### IFC-2: Inter-Implementer Boundary — impl-a1 ↔ impl-a2 Fork Coupling

**Severity:** LOW-MEDIUM
**Section Ref:** §3 Coupling Groups, §6 Cross-File Dependency Matrix

**Analysis:** The plan correctly identifies that impl-a1 and impl-a2 have "no cross-pair coupling beyond shared fork template pattern." This is accurate at the FILE level — their files are completely non-overlapping.

However, at the PATTERN level, both implementers must produce agent .md files and fork SKILL.md files that follow the exact same structural patterns:
- Same `context:fork` + `agent:` frontmatter structure
- Same §Interface section format (Input → Output → RISK-8 Fallback)
- Same voice (second person)
- Same cross-cutting approach (inline, not 1-line refs)

If impl-a1 interprets the fork template slightly differently from impl-a2 (e.g., different §Interface subsection headings, different RISK-8 fallback phrasing), the verifier will catch the inconsistency but the fix-loop becomes complex because two different implementers would need to converge.

**Why this is LOW-MEDIUM (not higher):** The fork template is well-specified in structure-architect L3 §1.3 with explicit skeleton. Both implementers read the same reference. Divergence is unlikely but possible if one implementer adapts the template more liberally.

**Proposed Mitigation:**
1. Add to Task V (Check 8 or a new Check 9): "Verify all 4 fork skills follow the same §Interface section structure (identical subsection headings)"
2. Include the exact expected subsection headings in the task directive for both impl-a1 and impl-a2

---

### IFC-3: impl-b ↔ infra-c Interface — Skill References Coordinator Names

**Severity:** LOW
**Section Ref:** §3 Coupling Groups, §6 Cross-File Dependency Matrix

**Analysis:** The plan marks this as "weak coupling — pre-existing names." This is correct. The 5 coordinator-based skills reference coordinator subagent_type names that already exist and won't change in this optimization. infra-c modifies coordinator BODIES and FRONTMATTER but doesn't change their NAMES.

**Remaining risk:** infra-c might accidentally change a coordinator's `name:` field in frontmatter during the Template B convergence. If `name: research-coordinator` becomes `name: research-coord` (abbreviation during cleanup), all skill references to `research-coordinator` break.

**Proposed Mitigation:** Already covered by Task V Check 5 (subagent_type references → agent .md exists) and Check 6 (coordinator Workers lists). No additional mitigation needed. This is LOW severity with adequate existing checks.

---

### IFC-4: 4-Way Naming Contract — Exact old→new Mapping Mismatch Risk

**Severity:** MEDIUM
**Section Ref:** §5 §10 Modification, §5 4-Way Naming Contract

**Analysis:** The §10 modification (Task D) provides exact replacement text. The 4-way naming contract table specifies all 3 agents × 4 locations. The risk is in execution precision:

1. **CLAUDE.md §10 text:** The exact replacement text in §5 lists `pt-manager (TaskCreate+TaskUpdate)`, `delivery-agent (TaskUpdate only)`, `rsil-agent (TaskUpdate only)`. If infra-d uses slightly different formatting (e.g., `pt-manager: TaskCreate, TaskUpdate` vs `pt-manager (TaskCreate+TaskUpdate)`), it's functionally equivalent but textually different from the plan.

2. **agent-common-protocol.md §Task API:** The APPEND text lists "Lead-delegated fork agents (pt-manager, delivery-agent, rsil-agent)." If infra-d uses the full names with hyphens — correct. But note the plan says "APPEND after existing text" while the interface-architect L3 §2.2 shows a "replacement text" for the entire §Task API section. This is a contradiction:
   - Implementation plan §5 says "APPEND after existing text"
   - Interface-architect L3 §2.2 header says "replacement text"

**The inconsistency:** Is infra-d supposed to APPEND a new paragraph to the existing §Task API, or REPLACE the entire §Task API section? The current §Task API is 3 lines (lines 74-76 per interface-architect §2.1). The "replacement text" in interface-architect L3 §2.2 shows both the original 3 lines AND the new exception paragraph — implying it's a replacement of the full section with the expanded version. But the implementation plan's §5 says "APPEND."

**Proposed Mitigation:**
1. Clarify in Task D's acceptance criteria: "Replace the entire §Task API section (lines 72-76 header + body) with the expanded version that includes both the original text and the fork exception paragraph"
2. This eliminates ambiguity about APPEND vs REPLACE — the end result is the same, but the operation type matters for the Edit tool

---

### IFC-5: GC Scratch Interface — 3 Remaining Concerns Compatibility with PT-Centric Model

**Severity:** MEDIUM
**Section Ref:** §2 D-14, interface-architect L3 §1.4

**Analysis:** GC retains 3 scratch concerns:
1. **Execution Metrics:** spawn_count, spawn_log, timing data
2. **Gate Records (embedded):** Inline gate summaries
3. **Version Marker:** gc_version

**Compatibility questions:**

**Q1: Who writes execution metrics to GC in the new model?** Currently, orchestration-plan.md tracks spawn_count and spawn_log (per CLAUDE.md §6). GC also has these metrics. After the redesign, do skills still write metrics to GC? The plan removes GC writes from skills but doesn't explicitly address whether the metrics concern migrates elsewhere or stays in GC.

**Q2: Gate records embedded in GC vs. gate-record.yaml files.** PT holds pointers to gate-record.yaml files. GC also embeds gate summaries. After the redesign, are both maintained? This is redundant data that could diverge.

**Q3: gc_version marker purpose.** The plan says "Dynamic Context reads this for session discovery." But if the new model uses PT §phase_status for session discovery (the L2 path mechanism), what is gc_version still needed for? Is it vestigial?

**Proposed Mitigation:**
1. Clarify in the implementation plan whether GC scratch concerns are actively maintained by the new skills or are legacy artifacts that happen to persist
2. If execution metrics stay in GC, specify which skill/coordinator writes them (currently Lead writes to orchestration-plan.md, which is separate from GC)
3. If gc_version is no longer needed for session discovery (replaced by PT §phase_status), consider removing it in a future cleanup

---

### IFC-6: L2 Downstream Handoff Chain — 6 Links Fully Specified?

**Severity:** MEDIUM
**Section Ref:** §5 Per-Skill PT Version Chain, interface-planner L3 §5

**Analysis of each link:**

| Link | From | To | L2 Path Discovery | Content Specified? |
|------|------|----|-------------------|--------------------|
| 1 | brainstorming (arch-coord/L2) | write-plan | PT §phase_status.P3.l2_path | ⚠ Content assumed from GC migration |
| 2 | write-plan (planning-coord/L2) | validation | PT §phase_status.P4.l2_path | ⚠ Same |
| 3 | write-plan (planning-coord/L2) | execution | PT §phase_status.P4.l2_path | ⚠ Same |
| 4 | validation (validation-coord/L2) | execution | PT §phase_status.P5.l2_path | ⚠ Same |
| 5 | execution (exec-coord/L2) | verification | PT §phase_status.P6.l2_path | ⚠ Same |
| 6 | verification (testing-coord/L2) | delivery | PT §phase_status.P7.l2_path | ⚠ Same |

**All 6 links share the same gap:** The L2 path DISCOVERY mechanism is fully specified (PT §phase_status → l2_path → read L2). But the L2 CONTENT that each predecessor must provide is not specified in the implementation plan. It's implied by the GC migration table (§5 GC Migration Summary) — the removed GC sections become L2 Downstream Handoff content.

**Example of what could go wrong:**
- write-plan currently reads GC "Phase 3 Input" + "Architecture Summary" + "Architecture Decisions"
- After redesign, write-plan reads arch-coord/L2 §Downstream Handoff
- But §Downstream Handoff has 6 categories (Decisions Made, Risks, Interface Contracts, Constraints, Open Questions, Artifacts Produced)
- The current GC "Architecture Decisions" maps to §Decisions Made
- The current GC "Architecture Summary" maps to... where? It's a summary, not a decision. Does it go in §Artifacts Produced? Or does it become implicit (read the full L2)?

**This is not a blocking issue** because the L2 Downstream Handoff format is already in use (all Phase 3 coordinators wrote it in this very pipeline). But the SKILL BODY needs to know which specific Downstream Handoff categories to read for its entry conditions. This mapping should be in the §C Interface section of each skill.

**Proposed Mitigation:**
1. In Task B §C Interface section specifications, include explicit mapping: "For write-plan: read arch-coord/L2 §Downstream Handoff → §Decisions Made for architecture decisions, §Constraints for enforced limits, §Artifacts Produced for L3 paths"
2. This is guidance for the implementer, not a structural change — but it's needed to ensure the L2 bridge actually carries the right data

---

## Addendum: Additional Challenges from Coordinator Scrutiny Areas

### ROB-10: Fork-Back Is NOT "Always Safe" — Skill Bodies Are Also Changed

**Severity:** HIGH
**Section Ref:** §10 Fork-Back Contingency

**Scenario:** The plan claims fork-back is "always safe" because "all 4 skills worked in Lead-in-context before." This claim is FALSE in the general case.

**What fork-back actually removes:** Only `context:fork` and `agent:` from SKILL.md frontmatter. The rest of the skill body is NOT reverted.

**What the rest of the skill body contains after this optimization:**
- NEW §C Interface Section (PT-centric, not GC-mediated)
- REMOVED GC write instructions (D-14: 22 GC writes eliminated)
- REMOVED GC read instructions (D-14: 15 GC reads replaced)
- REWRITTEN discovery protocol (TaskGet PT → l2_path instead of GC version scan)
- NEW fork voice (second person "You do X" instead of third person "Lead does X")
- NEW inline cross-cutting (ADR-S8: instead of 1-line CLAUDE.md references)

**After fork-back:** The skill body still has ALL these changes. It is now a Lead-in-context skill that:
1. Uses second-person voice ("You do X") — Lead is not "You"
2. Has no GC write instructions — Lead can't write phase status to GC
3. Has PT-centric discovery — which works for Lead, BUT
4. Has inline cross-cutting — Lead already has CLAUDE.md, so inline references are redundant but harmless
5. Has no GC read instructions — Lead must use PT + L2 instead of GC scan

**The critical issue:** Second-person voice and fork-specific instructions (e.g., "You operate in fork context — no coordinator, no team recovery") would confuse Lead-in-context execution. Lead is not in fork context. Lead DOES have a coordinator. Lead DOES have team recovery.

**This means fork-back requires MORE than removing 2 frontmatter fields.** It requires:
1. Voice rewrite: second person → third person (throughout body)
2. Cross-cutting cleanup: inline → 1-line references (or accept redundancy)
3. Error handling: fork-specific → Lead-in-context error handling
4. Remove fork-specific instructions (e.g., "You have no conversation history")

**Estimated fork-back effort per skill:** 50-100L of edits, not "remove 2 fields."

**Proposed Mitigation:**
1. Correct the fork-back contingency: "Fork-back requires skill body adaptation (voice, error handling, context references). Estimated 50-100L of edits per skill. NOT a 2-field removal."
2. Add a fork-back task specification: for each of the 4 fork skills, document the minimum body changes needed to restore Lead-in-context operation
3. Alternative: accept that fork-back is a "small new task" not a "trivial revert" — still much less work than full re-architecture

---

### ROB-11: rsil-agent Shared State Between Invocations — Is There Isolation?

**Severity:** MEDIUM
**Section Ref:** ADR-S5, risk-architect L3 §1.3

**Scenario:** rsil-agent is shared between rsil-global and rsil-review (ADR-S5). The coordinator asks: "What if rsil-global leaves state that corrupts rsil-review's execution?"

**Analysis:** Fork agents start clean per invocation — `context:fork` creates a NEW isolated session each time. There is no persistent state between invocations EXCEPT:
1. **Agent memory:** `~/.claude/agent-memory/rsil/MEMORY.md` (shared, persistent)
2. **Tracker file:** `docs/plans/2026-02-08-narrow-rsil-tracker.md` (shared, persistent)
3. **PT state:** PERMANENT Task (shared, persistent)

**The risk:** If rsil-global writes something incorrect to agent memory (e.g., "All coordinators use Template A" — stale after convergence), rsil-review reads this stale memory and bases analysis on outdated information.

**Mitigating factors:**
- Fork context provides true process isolation between invocations
- Agent memory is designed for stable patterns, not session state
- Tracker file is append-only with timestamps
- PT is always current state (Read-Merge-Write)

**Verdict:** Isolation between invocations is STRONG (fork creates new session). The shared persistent files (memory, tracker) are designed for cross-session use. The risk of corruption is LOW. However, if rsil-global writes stale data to agent memory, rsil-review inherits it.

**Proposed Mitigation:**
1. rsil-agent.md §Never: "Never write session-specific observations to agent memory — only universal Lens-level patterns" (already present in the design)
2. Accept LOW residual risk — this is the standard pattern for all agents with persistent memory

---

### ROB-12: Fork Agents Don't Have CLAUDE.md Loaded — Convention References Break

**Severity:** MEDIUM-HIGH
**Section Ref:** structure-architect L3 §1.3, ADR-S8

**Scenario:** Fork agents with `context:fork` start clean. They receive the SKILL body as their operating instruction. **CLAUDE.md is NOT part of the fork agent's context** — fork agents don't inherit the invoking session's system prompt.

**What this means:** Any reference in the fork skill body to CLAUDE.md conventions assumes the fork agent can read CLAUDE.md if needed. But:
1. The fork agent CAN read CLAUDE.md via the Read tool (it has Read access)
2. The fork agent does NOT automatically have CLAUDE.md loaded at startup
3. The fork skill's inline cross-cutting (ADR-S8) is specifically designed for this — fork skills embed error handling, principles, and constraints INLINE rather than referencing CLAUDE.md sections

**The gap:** ADR-S8 handles this for cross-cutting. But what about:
- **§10 integrity principles:** Fork agents are supposed to follow §10. If §10 says "Only Lead creates tasks except fork agents," the fork agent doesn't know this unless it reads CLAUDE.md. The fork agent's agent .md body says "Full Task API is the EXCEPTION granted by D-10" — but the agent doesn't know what D-10 IS.
- **Safety constraints (§8):** The fork agent doesn't automatically know about blocked commands, protected files, or git safety rules from CLAUDE.md §8. delivery-agent has Bash access — does it know about the `rm -rf` block?
- **Language Policy (§0):** Fork agents won't know to use Korean for user-facing conversation unless the skill body specifies it.

**Real failure scenario:** delivery-agent runs `git push --force main` because it doesn't have CLAUDE.md §8 "Never force push main" in its context. The agent .md §Never list says "Force push or skip git hooks" — but only if the implementer correctly includes this in the agent .md body.

**Assessment:** The risk-architect's agent .md designs DO include relevant Never lists (delivery-agent.md has "Force push or skip git hooks"), so this is PARTIALLY mitigated. But it depends on the implementer correctly transferring ALL safety constraints from CLAUDE.md §8 into each fork agent .md's Never section.

**Proposed Mitigation:**
1. Add to Task A1/A2 acceptance criteria: "Verify fork agent .md §Never covers ALL relevant CLAUDE.md §8 safety constraints (rm -rf, sudo rm, chmod 777, force push, secrets in commits)"
2. Consider adding to each fork agent .md: "Read `.claude/CLAUDE.md` §8 (Safety) at startup for safety constraints" — one extra Read tool call but ensures safety awareness
3. Alternatively, accept that the agent .md designs already cover this (risk-architect was thorough) and rely on V6b-4 behavioral plausibility review

---

### ROB-13: Recovery Decision Tree — /rsil-global Circular Assessment

**Severity:** LOW-MEDIUM
**Section Ref:** §10 Recovery Decision Tree

**Scenario:** The recovery decision tree's "Uncertain scope?" branch says "Run /rsil-global for assessment." But /rsil-global is ONE OF THE 22 CHANGED FILES. If the commit broke rsil-global itself, running it for assessment would either:
1. Fail (rsil-global is broken) → no assessment possible
2. Succeed but produce incorrect analysis (rsil-global works but with wrong instructions)

**Mitigating factor:** rsil-global's skill body changes are focused on:
- New §C Interface Section (PT read/write)
- Fork frontmatter (`context:fork`, `agent:rsil-agent`)
- GC interaction removal (rsil-global had none per interface-planner L3)
- rsil-global's CORE logic (8 lenses, 3-tier observation) is NOT changed

So the core analysis capability is preserved. The changes are structural/interface, not analytical. If rsil-global can fork and load rsil-agent successfully, its analysis output should be valid.

**Residual risk:** If the fork mechanism itself is broken (RISK-1), rsil-global can't run at all. But in that case, fork-back removes the fork frontmatter and rsil-global reverts to Lead-in-context (with the caveats from ROB-10).

**Proposed Mitigation:**
1. Add to recovery decision tree: "If /rsil-global fails to invoke → revert /rsil-global to Lead-in-context (remove context:fork + agent: frontmatter) → re-run as Lead-in-context"
2. This provides a concrete fallback for the circular case

---

### IFC-7: PT Version Chain — TRIVIAL Tier Skips Phases

**Severity:** MEDIUM
**Section Ref:** §5 Per-Skill PT Version Chain, CLAUDE.md D-001 Pipeline Tiers

**Scenario:** The PT version chain (§5) assumes sequential phase execution: brainstorming→v1, write-plan→v2, validation→v3, execution→v4, verification→v5, delivery→vFinal. But TRIVIAL tier skips P2b, P5, P7, P8. STANDARD tier skips P2b, P5, P8.

**Questions:**
1. If validation (P5) is skipped in STANDARD tier, v3 is never created. Does execution still read "Validation Verdict" from PT? It would be empty/missing.
2. If verification (P7/P8) is skipped in TRIVIAL tier, v5 is never created. Does delivery check for "Phase 7/8 COMPLETE"? It would fail.

**Analysis:** The version numbers (v1, v2, v3...) in §5 are ILLUSTRATIVE, not prescriptive. The actual protocol uses PT-v{N+1} (monotonically increasing). Skipped phases simply don't bump the version. The real question is: do downstream skills gracefully handle MISSING PT sections?

**The answer is in each skill's Phase 0 check.** Phase 0 verifies specific phase_status entries. If a phase was skipped, its status would be absent (not "COMPLETE"). The skill's Phase 0 should handle this case.

**The gap:** The implementation plan's §C Interface sections don't specify behavior for "predecessor phase was skipped." For example, execution's §C says "Input: ... Impl Plan pointer" — but in TRIVIAL tier, there's no explicit "implementation plan" because write-plan was run but validation was skipped.

**Proposed Mitigation:**
1. Add to each skill's §C Interface section: "If predecessor phase was skipped (tier-dependent), verify available sections and proceed with what exists"
2. This is guidance, not a structural change — but it prevents fork agents from failing on missing PT sections in non-COMPLEX pipelines

---

### IFC-8: /permanent-tasks Mid-Pipeline Breaks Sequential Version Chain

**Severity:** LOW
**Section Ref:** §5 Per-Skill PT Version Chain (row: permanent-tasks)

**Scenario:** /permanent-tasks can be invoked at ANY point, writing PT-v{N+1}. If the user invokes it between write-plan (v2) and validation (v3), the version becomes v3 (from permanent-tasks), and then validation would create v4 instead of v3.

**Analysis:** This is NOT actually a problem because:
1. Version numbers are monotonically increasing counters, not semantic identifiers
2. Skills don't depend on specific version numbers — they read PT sections by name
3. The version bump protocol (Read-Merge-Write) ensures no data loss
4. /permanent-tasks preserves all existing sections and only modifies what the user requests

**Verdict:** No actual vulnerability. The version chain is resilient to mid-pipeline /permanent-tasks invocations by design.

---

### IFC-9: L2 Downstream Handoff Durability — What If L2 Is Truncated?

**Severity:** MEDIUM
**Section Ref:** §2 C-2, interface-planner L3 §5

**Scenario:** L2 replaces GC as the cross-phase data bus. But L2 files are written by coordinator agents who may compact (BUG-002/BUG-004). If a coordinator's L2 is truncated (agent compacted mid-write), the §Downstream Handoff section might be missing or incomplete.

**Comparison with GC:** GC was written by Lead (who has long context and rarely compacts). L2 is written by coordinators (who have shorter context and DEFINITELY can compact). The new bus is LESS RELIABLE than the old bus in terms of write durability.

**Specific failure path:**
1. arch-coord writes L2 but compacts before writing §Downstream Handoff (the LAST section per protocol)
2. write-plan reads arch-coord/L2 but finds no §Downstream Handoff
3. write-plan can't discover Phase 3 architecture decisions, constraints, or artifacts
4. write-plan fails or produces an incorrect plan

**Mitigating factors:**
- L1/L2/L3 protocol says "write proactively" — but §Downstream Handoff is typically written at COMPLETION
- PT still holds architecture decisions, constraints, and impact map — L2 is supplementary
- Lead monitors coordinator completion and verifies L2 quality before gate approval

**But:** If Lead approves a gate without checking §Downstream Handoff completeness, the gap propagates to the next phase.

**Proposed Mitigation:**
1. Add to gate evaluation criteria: "Verify coordinator L2 §Downstream Handoff has all 6 required categories populated"
2. Add to coordinator-shared-protocol.md: "Write §Downstream Handoff incrementally — after each major decision, not just at completion"
3. Note: this is a protocol improvement, not an implementation plan change. Can be deferred to a post-commit /rsil-review finding.

---

### IFC-10: Fork Agent TaskGet Parsing — Can Fork Agents Parse PT Sections?

**Severity:** LOW
**Section Ref:** §2 C-4, interface-planner L3 §1.7

**Scenario:** Fork agents use TaskGet to read the PERMANENT Task. TaskGet returns a task object with a `description` field (string). The PT sections are embedded in this description as structured text (YAML-like headers + content).

**Question:** Does the fork agent know how to parse this description to extract specific sections (User Intent, Phase Status, etc.)?

**Analysis:** The fork agent receives the skill body as its operating instruction. The skill body says things like "Read PT §Phase Status" or "Read PT §User Intent." The fork agent would:
1. Call TaskGet → receives task description (string)
2. Search for section headers in the string
3. Extract content between headers

This is standard NL-guided text parsing that Claude models do naturally. There's no formal parser required — the sections are delimited by markdown headers within the task description.

**Verdict:** LOW risk. Claude models are well-equipped for structured text extraction. The only failure mode is if PT section headers are ambiguous or non-standard — but the naming contract (§10 integrity principles) freezes header names.

---

### IFC-11: Concurrent Fork Agent PT Updates — Race Condition?

**Severity:** LOW
**Section Ref:** §2 C-4, risk-architect L3 §4 (FM-4)

**Scenario:** Two fork agents run concurrently and both call TaskUpdate on the same PT. One's update overwrites the other's.

**Analysis:** This is addressed by FM-4 in risk-architect L3: "Concurrent PT Modification — Detection: Not easily detected. Recovery: Teammate re-reads PT on next TaskGet call."

**Why this is LOW in practice:** Fork agents are invoked by Lead sequentially (Lead invokes one skill at a time). The only concurrent scenario is if the user manually invokes /permanent-tasks while /rsil-global is running. This requires deliberate user action during a pipeline.

**TaskUpdate is atomic** (single API call), so the PT is never in a partially-written state. The risk is LOST UPDATE, not CORRUPTION. If both updates touch different PT sections, both survive (Task API merges). If both touch the SAME section, last-write-wins.

**Proposed Mitigation:** Accept LOW residual risk. Document in fork skill instructions: "If you read PT at startup and later update it, re-read before writing to avoid stale overwrites."

---

### IFC-12: 3-Layer Enforcement Precedence — Which Layer Wins?

**Severity:** LOW
**Section Ref:** §2 C-5, interface-architect L3 §2.3

**Scenario:** 3-layer enforcement for fork Task API: frontmatter `disallowedTools` (primary) → agent .md NL instructions (secondary) → CLAUDE.md §10 (tertiary). What if layers are inconsistent?

**Analysis:** The precedence is clear and correct:
1. **Frontmatter is HARD enforcement** — Claude Code literally blocks disallowed tools. No NL instruction can override this.
2. **Agent .md NL is SOFT enforcement** — guides the agent's behavior but can be accidentally violated.
3. **CLAUDE.md §10 is POLICY enforcement** — documents the intent but can't block tool calls.

**If layers conflict:**
- Frontmatter blocks + NL allows = BLOCKED (frontmatter wins, correctly)
- Frontmatter allows + NL blocks = ALLOWED but agent shouldn't use (NL violation detectable in review)
- Frontmatter allows + CLAUDE.md blocks = ALLOWED (CLAUDE.md may not be loaded in fork context)

**The only problematic case is #3:** Fork agent has tool access that CLAUDE.md would block, but fork agent doesn't have CLAUDE.md loaded. This is mitigated by ROB-12 (fork agents should have relevant constraints in their agent .md body).

**Verdict:** Enforcement precedence is well-designed. The frontmatter-first approach ensures hard enforcement works. Soft enforcement (NL) is defense-in-depth. ROB-12 covers the CLAUDE.md-not-loaded gap.

---

### IFC-13: 4-Way Naming — Additional Locations Beyond the 4

**Severity:** LOW
**Section Ref:** §5 4-Way Naming Contract

**Scenario:** The naming contract specifies 4 locations: skill `agent:`, agent .md filename, CLAUDE.md §10, agent-common-protocol.md §Task API. Are there OTHER locations where these names appear?

**Potential additional locations:**
1. **Skill `description:` text** — may mention the agent name descriptively
2. **Agent .md `description:` text** — refers to itself by name
3. **Skill body NL references** — "pt-manager will handle this" in other skills
4. **Dynamic Context commands** — `!cat .claude/agents/pt-manager.md 2>/dev/null` if any
5. **Error messages** — "Please run /permanent-tasks first" references the skill, not the agent

**Assessment:** Locations 1-2 are within the agent's own file pair (skill + agent .md), so they're always consistent if the implementer uses the correct name. Location 3 is the risk — if skill B references "pt-manager" in its body, and the name changes, skill B would break. But in this optimization, no coordinator-based skill references fork agent names in their body (fork agents are Lead-invoked, not coordinator-invoked). Location 4 would require explicit construction. Location 5 references skill names, not agent names.

**Verdict:** No additional naming locations beyond the 4 need tracking. The 4-way contract is sufficient.

---

## Severity Summary

| ID | Type | Severity | Category |
|----|------|----------|----------|
| ROB-1 | Robustness | HIGH | BUG-002: infra-c 8-file partial completion |
| ROB-2 | Robustness | HIGH | BUG-002: impl-b critical path misidentification |
| ROB-10 | Robustness | HIGH | Fork-back is NOT safe — skill bodies also changed (voice, GC, cross-cutting) |
| ROB-3 | Robustness | MEDIUM-HIGH | Fork context:fork error taxonomy missing |
| ROB-4 | Robustness | MEDIUM-HIGH | execution-coordinator convergence regression |
| ROB-12 | Robustness | MEDIUM-HIGH | Fork agents don't have CLAUDE.md — safety constraints may be missing |
| ROB-5 | Robustness | MEDIUM | RISK-2: permanent-tasks sparse-context degradation |
| ROB-6 | Robustness | MEDIUM | RISK-3: delivery MEMORY.md Read-Merge-Write non-idempotence |
| ROB-7 | Robustness | LOW-MEDIUM | RISK-3: delivery partial pipeline state handling |
| ROB-8 | Robustness | MEDIUM | Pre-deploy validation protocol file cascade |
| ROB-9 | Robustness | MEDIUM | BUG-002: verifier read load (~5,325L) |
| ROB-11 | Robustness | MEDIUM | rsil-agent shared state — LOW risk, memory isolation adequate |
| ROB-13 | Robustness | LOW-MEDIUM | /rsil-global circular assessment — core logic preserved |
| IFC-1 | Interface | MEDIUM | C-2 L2 Handoff content not specified per-skill |
| IFC-2 | Interface | LOW-MEDIUM | Fork template divergence between impl-a1/impl-a2 |
| IFC-3 | Interface | LOW | Coordinator name change risk (adequate checks exist) |
| IFC-4 | Interface | MEDIUM | §Task API APPEND vs REPLACE contradiction |
| IFC-5 | Interface | MEDIUM | GC scratch 3 concerns: post-redesign maintenance unclear |
| IFC-6 | Interface | MEDIUM | L2 Handoff chain: 6 links content mapping unspecified |
| IFC-7 | Interface | MEDIUM | PT version chain — TRIVIAL tier skips phases, missing sections |
| IFC-8 | Interface | LOW | /permanent-tasks mid-pipeline — version chain is resilient by design |
| IFC-9 | Interface | MEDIUM | L2 Downstream Handoff durability — less reliable than GC |
| IFC-10 | Interface | LOW | Fork TaskGet parsing — NL extraction is natural for Claude |
| IFC-11 | Interface | LOW | Concurrent PT updates — sequential invocation prevents in practice |
| IFC-12 | Interface | LOW | 3-layer enforcement precedence — well-designed, frontmatter-first |
| IFC-13 | Interface | LOW | 4-way naming — no additional locations needed |

**Critical+HIGH count:** 3 (ROB-1, ROB-2, ROB-10)
**MEDIUM-HIGH count:** 3 (ROB-3, ROB-4, ROB-12)
**MEDIUM count:** 10
**LOW-MEDIUM or LOW:** 11

---

## Evidence Sources

| Source | Role | Key Extractions |
|--------|------|-----------------|
| Implementation plan (630L) | Primary artifact under review | §3 ownership, §6 execution, §8 risk, §10 rollback |
| arch-coord/L2 (221L) | Architecture decisions | Unified design, risk summary, downstream handoff |
| risk-architect L3 (662L) | Fork agent designs + risk register | RISK-1~RISK-9, FM-1~FM-7, OQ-1~OQ-3 |
| interface-architect L3 (412L) | Interface contracts + §10 text | C-1~C-6, §2.2 replacement text, GC migration |
| structure-architect L3 (754L, partial) | Template design + coordinator convergence | §1.2-1.3 templates, §5.2 Template B, per-coordinator inventory |
| decomposition-planner L3/section-4 (348L) | Task descriptions with ACs | Tasks D, A1, A2, B, C, V |
| strategy-planner L3 (536L) | Execution strategy + validation + rollback | Waves 1-4, V1-V6, pre-deploy A→D, recovery decision tree |
| interface-planner L3/dependency-matrix (326L) | Cross-file dependencies | Agent refs, protocol refs, §10 refs, coupling assessment |
| Web research: Big Bang deployment patterns | External validation | Coordination failures, troubleshooting difficulty, partial rollback |
| CLAUDE.md §6 | Agent selection and BUG-002 reference | BUG-002 scope gate definition |
| agent-common-protocol.md (247L) | Protocol reference | §Task API current text, L1/L2 canonical format |
