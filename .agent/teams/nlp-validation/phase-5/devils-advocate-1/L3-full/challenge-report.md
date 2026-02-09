# Phase 5 Challenge Report — Architecture Design v2 (NLP + PERMANENT Task)

**Reviewer:** devils-advocate-1 | **Phase:** 5 | **Date:** 2026-02-08
**Target:** `.agent/teams/opus46-nlp-conversion/phase-3/architect-2/L3-full/architecture-design-v2.md`
**Upstream:** `docs/plans/2026-02-08-permanent-tasks-design.md`

---

## C-1: Correctness — Does the NLP conversion solve the stated problem?

### C-1.1: NLP conversion approach is fundamentally sound (PASS)

The design correctly identifies that Opus 4.6 responds better to natural language than
protocol markers. The three axioms (say it once, role prompting, natural language compression)
are well-grounded in the cited research findings. The 4th axiom (self-serve context via TaskGet)
is a logical extension given the PT design.

**Evidence:** The researcher findings (F-001~F-006 in GC-v4) support the claim that
"bloated CLAUDE.md causes Claude to ignore instructions" and that measured language
outperforms ALL CAPS enforcement.

### C-1.2: DIA v6.0 open questions MAY weaken enforcement — severity depends on operator (MEDIUM)

**Challenge:** The current DIA uses specific RC checklist items (RC-01~RC-10) and 7 named
LDAP categories. These provide Lead with an exhaustive menu of verification targets. The
proposed replacement ("1-3 open-ended questions") relies entirely on Lead's skill at
generating good questions. A strong Lead will ask better questions than a checklist; a weak
Lead might miss critical dimensions.

**Evidence against concern:** The Impact Map provides an objective reference that partially
compensates — Lead's questions are "grounded" in documented relationships, not pure intuition.
This is a significant improvement over v5.0's LDAP which operated on guesswork.

**Evidence for concern:** The Impact Map doesn't exist in Phase 1-2 (admitted as R-8). During
these early phases, Lead falls back to pure judgment, which is the exact scenario the
checklists were designed to prevent.

**Mitigation proposed in design:** "Lead uses judgment in early phases" (R-8 detail).
**Assessment:** The mitigation is an acknowledgment, not a solution. However, the design
correctly notes that Phases 1-2 have lower scrutiny levels (Standard/None) anyway, so
the risk is bounded.

**Severity: MEDIUM** — The Impact Map grounding is a net improvement for Phase 3+.
Early-phase weakness is real but low-impact.

---

## C-2: Completeness — Are all behaviors preserved? Missing elements?

### C-2.1: Line count claim is inaccurate (MEDIUM)

**Challenge:** The design claims "~136 lines" for CLAUDE.md v6.0. I counted the actual
proposed text (lines 223-390 of the L3 file, within the code fence):
- Raw lines including blanks: ~167
- Content lines (non-blank): ~136-140

The "~136 lines" appears to be counting content lines only, excluding blank lines that
are part of markdown formatting. This is misleading — real file line count will be
~167 lines, not 136. The claimed "34% reduction" (207→136) is actually closer to
207→167 = **19% reduction**.

**Impact:** Line count is a secondary metric (the design itself says "semantic quality >
line count" in R-5), but the claim is used as a success criterion in GC-v4 ("Total:
847 → 525 lines") and the preservation checklist. The discrepancy could erode trust
in other numerical claims.

**Severity: MEDIUM** — Does not affect semantic correctness but misrepresents a key metric.
Recommend recounting with consistent methodology (either all lines including blanks, or
content-only with clear labeling).

### C-2.2: Multiple v5.1 behaviors LOST in v6.0 rewrite (HIGH)

I systematically compared every line of CLAUDE.md v5.1 against the v6.0 rewrite.
The design claims "28/28 original behavioral requirements preserved." This is **incorrect**.
The following behaviors are present in v5.1 but absent from v6.0:

| # | Lost Behavior | v5.1 Location | Impact |
|---|--------------|---------------|--------|
| 1 | **"Max 3 iterations per phase"** | §2 line 33 | Gate iteration limit is a safety valve. Without it, Lead could iterate indefinitely on a failing phase. |
| 2 | **"APPROVE / ITERATE / ABORT" gate vocabulary** | §2 line 33 | Explicit gate outcome options give Lead structured decision vocabulary. |
| 3 | **"DIA Enforcement: Every task assignment requires Context Injection + Impact Verification before work begins"** | §2 line 34 | This explicit DIA mandate at pipeline level is removed. §6 describes verification but doesn't state it as a pipeline-level rule. |
| 4 | **Spawn Matrix** (Phase→role mapping formula) | §6 "Spawn Matrix" | "Phase 1, 9 = Lead only. Count by module/research domain." is operational guidance for teammate count decisions. |
| 5 | **Deviation levels taxonomy** (COSMETIC / INTERFACE_CHANGE / ARCHITECTURE_CHANGE) | §6 "DIA Engine" Propagation | v6.0 §6 "Monitoring Progress" says "log cosmetic deviations, re-inject for interface changes, re-plan for architectural changes" — this preserves the behavior but loses the explicit naming. Borderline loss. |
| 6 | **Gate S-2 threshold "6000 lines total read"** | §6 "Pre-Spawn Checklist" | v6.0 says ">4 files, split" but drops the 6000-line read threshold. |
| 7 | **"CLAUDE_CODE_TASK_LIST_ID for persistence"** | §6 "DIA Engine" | Mentioned only in risk R-9 mitigation, not in the CLAUDE.md v6.0 rewrite. |
| 8 | **Delegate Mode** (in Lead description) | §1 | v5.1: "Pipeline Controller (Delegate Mode — never modifies code directly)". v6.0: "Pipeline Controller — spawns teammates, manages gates, never modifies code directly". The "Delegate Mode" label is removed, which is a naming loss but the behavior is preserved. |

**Analysis:** Items 1-4 are genuine behavioral losses. Items 5-8 are borderline (behavior
partially preserved but degraded). The claim "28/28 preserved" should be revised to
acknowledge these gaps.

**Most concerning:** Item 1 (max iterations) and Item 3 (DIA mandate at pipeline level) are
safety mechanisms. Removing them assumes Lead will self-regulate, which contradicts the
design's own principle that verification should be grounded rather than judgment-based.

**Severity: HIGH** — Multiple behavioral requirements lost. The preservation checklist in
the design (lines 410-447) does not include items 1, 3, 4, or 6, meaning they were
never tracked. This suggests the checklist itself is incomplete.

### C-2.3: PERMANENT Task design integration gaps (MEDIUM)

Cross-referencing L3-v2 against `permanent-tasks-design.md`:

| PT Design Section | Requirement | L3-v2 Coverage | Gap? |
|------------------|-------------|----------------|------|
| §1 "Operational Constraints" | Max 2 concurrent teammates | In GC-v4 constraints, not in CLAUDE.md v6.0 | **YES** |
| §1 "Task Granularity" | Split tasks maximally, 1 file = 1 task | In GC-v4 constraints, not in CLAUDE.md v6.0 | **YES** |
| §1 "Token Policy" | Claude Max X20 — no token conservation | In GC-v4 constraints, not in CLAUDE.md v6.0 | **YES** |
| §3 PT description structure | Fixed structure with 5 sections | Mentioned in L3-v2 §6 Coordination Infrastructure | OK |
| §4 `/permanent-tasks` skill | Full execution flow | Mentioned as T1, with reference in §3 and §10 | OK |
| §5 Phase 0 integration | All pipeline skills gain Phase 0 | In task breakdown (T5-T7) but not in CLAUDE.md v6.0 §2 | **MINOR** |
| §6 CIP/DIA changes | 4-layer protocol update | Described in DIA v6.0 spec | OK |
| §7 PT lifecycle | Create → Maintain → Archive | In §10 Lead responsibilities | OK |
| §8 Migration plan | 10-file change matrix | Expanded to 12 tasks | OK |
| §3 "Consolidation Rules" | Deduplicate/resolve/elevate | In §10 "refined current state, never append-only" | **PARTIAL** — rules not spelled out |

**Operational Constraints omission:** The permanent-tasks-design §1 states explicit
operational constraints (max 2 concurrent, split maximally, no token conservation) that are
labeled "mandatory for all pipeline execution." These are NOT in the proposed CLAUDE.md v6.0
at all. They exist only in GC-v4, which is a transient document. Since the whole point of
the PT design is that GC is replaced by PERMANENT Task, these constraints must be either:
1. In CLAUDE.md (as permanent infrastructure rules), OR
2. In the PERMANENT Task description template

The L3-v2 design places them neither in CLAUDE.md nor defines them as part of the PT
description structure. This is a **gap** — these constraints could be lost between sessions.

**Severity: MEDIUM** — The constraints will likely be captured in the actual PT instance
at runtime, but the design doesn't mandate it. Recommend either adding a "Operational
Constraints" subsection to CLAUDE.md v6.0 or adding it to the PT description template
structure defined in permanent-tasks-design §3.

### C-2.4: agent-common-protocol.md — Tags dropped without replacement (LOW)

v5.1 agent-common-protocol.md line 50 defines Team Memory tags:
`[Finding]`, `[Pattern]`, `[Decision]`, `[Warning]`, `[Dependency]`, `[Conflict]`, `[Question]`

The v2.0 rewrite drops these entirely. While the tags are arguably protocol markers being
converted, they served as a lightweight taxonomy for Team Memory entries that enabled
search/filter.

**Severity: LOW** — Tags were lightly used in practice. Natural language entries are
likely sufficient for Opus 4.6 to parse.

---

## C-3: Consistency — Do different parts contradict?

### C-3.1: AD-7/8/9 are consistent with AD-1~6 (PASS)

I checked for contradictions between the 6 preserved ADs and 3 new ADs:
- AD-1 (deduplication) ↔ AD-7 (PT): Compatible. PT replaces GC as authoritative source.
- AD-2 ([PERMANENT] → §10) ↔ AD-7 (PT lifecycle in §10): Compatible. §10 naturally houses PT principles.
- AD-5 (DIA v6.0) ↔ AD-8 (Impact Map): Compatible. AD-8 enhances AD-5 with grounding.
- AD-6 (agent template) ↔ AD-9 (TaskGet recovery): Compatible. "Before Starting Work" section naturally includes TaskGet.

No inter-AD contradictions found.

### C-3.2: Terminology inconsistency — "Impact Map" vs "Codebase Impact Map" (LOW)

The design uses both terms interchangeably:
- "Codebase Impact Map" in CLAUDE.md §4, §6 "Verifying Understanding", §6 "Monitoring Progress", §10
- "Impact Map" in agent .md files "Before Starting Work" sections, DIA v6.0 spec

While contextually clear, this creates two terms for one concept. The PT design
(permanent-tasks-design.md) consistently uses "Codebase Impact Map."

**Severity: LOW** — Contextually unambiguous but violates AD-1's "say it once" principle at
the naming level.

### C-3.3: CLAUDE.md §3 says "use TaskList and TaskGet only" — but CLAUDE.md §9 says "call TaskGet on the PERMANENT Task" (PASS)

These are consistent — §9 describes a specific use case of the capability described in §3.
No contradiction.

### C-3.4: Devils-advocate exemption inconsistency (LOW)

CLAUDE.md v6.0 §6 "Verifying Understanding" says "If understanding remains insufficient
after 3 attempts, re-spawn" — this applies to all roles. But the devils-advocate is exempt
from understanding checks (stated in devils-advocate.md: "exempt from the understanding check").

The CLAUDE.md text doesn't mention this exemption. A strict reader of CLAUDE.md alone
would expect to verify the devils-advocate's understanding too.

**Mitigation:** The DIA v6.0 spec table shows "Devils-advocate: 0 (exempt)" — but this
is in the L3 design doc, not in the CLAUDE.md itself.

**Severity: LOW** — The devils-advocate .md file states exemption clearly. Cross-file
inconsistency is minor since Lead reads both.

---

## C-4: Feasibility — Can this be implemented within constraints?

### C-4.1: 12 tasks in 5-6 rounds with max 2 concurrent is feasible (PASS)

The task dependency graph is:
```
T1 ∥ T2 → T4 ∥ T11 → T5 ∥ T6 → T7 ∥ T8 → T9 ∥ T10 → T12
```

Each task modifies a single file (aligned with PT design "1 file = 1 task"). The DIA
overhead per task is manageable given the "no token conservation" policy.

### C-4.2: T11 and T12 dependency on T2 AND T4 — Round 2 parallelism question (MEDIUM)

**Challenge:** The design shows:
- Round 2: T4 (common-protocol) ∥ T11 (3 agent .md)
- Both depend on T2 (CLAUDE.md)

T11 modifies researcher.md, architect.md, devils-advocate.md. These files reference
agent-common-protocol.md (T4). If T11 starts before T4 completes, the implementer
working on T11 may reference the OLD common-protocol, leading to inconsistency.

The design acknowledges this: "T11: researcher.md, architect.md, devils-advocate.md →
MODIFY → depends T2, T4 → Round 2". But then says "OR T4 (common-protocol) + T12
(3 agent .md)" — this acknowledges the ambiguity.

**However**, the dependency graph on line 1196 shows:
```
T2 ──→ T4 ──→ T11, T12
```
This means T11 and T12 depend on T4 completing first, which contradicts the "Round 2:
T4 ∥ T11" execution order.

**Impact:** If T4 and T11 are truly parallel (Round 2), implementers may produce
inconsistent agent files. If T11 depends on T4, Rounds 2-3 become sequential, adding
1-2 rounds.

**Severity: MEDIUM** — The dependency graph and round table contradict each other.
Implementation Lead must choose: parallel (risk inconsistency) or sequential (add rounds).
Recommend making T11/T12 strictly depend on T4 and adjusting round count to 6-7.

### C-4.3: T3 exclusion creates a coordination gap (MEDIUM)

**Challenge:** T3 (task-api-guideline.md) is "excluded — being modified concurrently in
another terminal." But task-api-guideline.md is referenced from CLAUDE.md v5.1 (§4 line 69,
§6, [PERMANENT] Cross-References) and from agent-common-protocol.md. The v6.0 rewrite
removes most of these references, but the file still exists and is being modified.

**Risk:** If the separate terminal's modifications to task-api-guideline.md assume v5.1
protocol markers that v6.0 replaces (e.g., GC-v{N} → PT-v{N}), the two files will be
inconsistent. There's no coordination mechanism defined between the two terminals.

**Severity: MEDIUM** — Real risk of cross-terminal inconsistency. Recommend defining a
handoff protocol: which terminal updates task-api-guideline.md's GC→PT references?

---

## C-5: Robustness — What happens when things go wrong?

### C-5.1: Impact Map chicken-and-egg problem is partially addressed (MEDIUM)

**Challenge:** The Impact Map is the centerpiece of DIA v6.0's grounding mechanism.
But it's empty in Phase 1 and sparse in Phase 2. The design admits this (R-8) and says
"Lead uses judgment until populated."

**Deeper issue:** The researcher in Phase 2 is the first non-Lead agent to undergo
DIA verification. At this point, the Impact Map has zero entries (researcher hasn't
researched yet). So the first verification cycle of every pipeline operates exactly
like the old DIA v5.0 — judgment-based, no grounding.

The Impact Map only becomes useful starting Phase 3 (architect), after the researcher
has identified module dependencies. This means Phases 1-2 get zero benefit from AD-8.

**Mitigation assessment:** The design's mitigation ("progressive enrichment") is
accurate but undersells the gap. For a 9-phase pipeline, the first 2 phases (22% of
phases, 40% of pre-execution effort allocation) operate without the flagship feature.

**Severity: MEDIUM** — Not a design flaw, but a limitation that should be explicitly
acknowledged. The Impact Map is a Phase 3+ feature, not a pipeline-wide one.

### C-5.2: TaskGet failure during recovery — insufficient fallback (LOW)

**Challenge:** AD-9 introduces self-recovery via TaskGet. What if TaskGet fails?
Possible reasons: Task API service issue, task list scope mismatch (F-4 from PT design),
or task deleted after pipeline crash.

**Current mitigation (R-7):** "TaskGet is in every agent's tool list; TaskList + subject
search as backup."

**Assessment:** TaskList + subject search is the same API layer — if TaskGet fails,
TaskList likely fails too. The real fallback is Lead re-injection (the v5.0 approach),
which is mentioned: "You can begin self-recovery with steps 2-3 while waiting for Lead,
but always confirm your understanding with Lead before resuming work."

This is adequate. The self-recovery is an optimization, not a replacement for Lead
re-injection.

**Severity: LOW** — Adequate fallback exists.

### C-5.3: PT description size growth is a real concern (MEDIUM)

**Challenge:** The PERMANENT Task description will grow as the pipeline progresses:
- Phase 1: User Intent + Constraints (~20 lines)
- Phase 2: + Research-informed Impact Map entries (~30 lines)
- Phase 3: + Architecture Decisions + comprehensive Impact Map (~80 lines)
- Phase 4+: + more decisions, phase status, refined entries

The PT design mentions "Consolidation Rules" (deduplicate, resolve, elevate) to control
growth, but the architecture-design-v2 only mentions this as "refined current state,
never an append-only log" — one line in §10.

**Risk:** If consolidation discipline breaks down, the PT description becomes the new
bloated CLAUDE.md — the very problem this design solves. The irony is that TaskUpdate
description has no enforced size limit, so bloat is technically easier than in a .md file.

**Mitigation proposed (R-6):** "Split Impact Map to file; PT holds path only."
**Assessment:** This is reactive (wait for problem) rather than proactive (prevent problem).
Recommend adding a target line count or consolidation frequency to the PT lifecycle.

**Severity: MEDIUM** — Growth is inevitable; discipline is the only control.

### C-5.4: What if a teammate doesn't call TaskGet? (LOW)

**Challenge:** The self-serve model relies on teammates calling TaskGet after receiving
a directive. If a teammate skips this step and works from the directive's summary alone,
they may have incomplete context.

**Mitigations:**
1. on-subagent-start.sh hook injects PT Task ID (mentioned in design)
2. Agent .md "Before Starting Work" says "Read the PERMANENT Task via TaskGet"
3. DIA verification (Lead's probing questions) would catch lack of context

**Assessment:** Three-layer defense is sufficient. A teammate that skips TaskGet would
fail the understanding check.

**Severity: LOW** — Adequate defense in depth.

---

## C-6: Interface Contracts — Are all interfaces consistent?

### C-6.1: CLAUDE.md ↔ agent-common-protocol.md interface is clean (PASS)

v6.0 CLAUDE.md §3 says "Follow `.claude/references/agent-common-protocol.md` for shared
procedures." The common-protocol v2.0 covers: context receipt, mid-work updates, completion,
task API, team memory, saving work, context loss, agent memory. These map to the behaviors
referenced in CLAUDE.md §3 (understand first, plan approval, read-only tasks) and §9
(recovery), and §10 (save work, persistence).

No orphaned references or missing cross-links.

### C-6.2: Agent .md "Before Starting Work" ↔ CLAUDE.md §6 "Verifying Understanding" alignment (PASS)

CLAUDE.md §6 says Lead asks "1-3 open-ended questions appropriate to their role." Each
agent .md "If Lead Asks Probing Questions" section describes how to respond. The focus
areas match:
- Researcher: scope, downstream consumers → §6 says "interconnection awareness"
- Architect: propagation, alternatives → §6 says "alternative approaches for P3/P4"
- Implementer: interface impact, rollback → §6 says "interconnection, failure reasoning"
- Integrator: merge conflicts, system coherence → §6 says same
- Tester: test priorities, coverage gaps → §6 says same
- Devils-advocate: exempt → §6 doesn't mention exemption (see C-3.4)

### C-6.3: YAML frontmatter unchanged — but Write/Edit tool assignment carries hidden significance (LOW)

The design says "YAML frontmatter unchanged" for all 6 agents. This is correct for the
tool list. However, the tool assignment determines Team Memory access (Edit = direct write,
no Edit = Lead relay). The new common-protocol v2.0 correctly states this rule. The
agent .md files correctly reflect it:
- implementer, integrator: "Write discoveries to your TEAM-MEMORY.md section"
- researcher, architect, tester: "Report key findings to Lead for Team Memory relay"
- devils-advocate: "Read-only access to Team Memory"

No inconsistency found.

### C-6.4: "/permanent-tasks" skill referenced but not fully defined in design (LOW)

CLAUDE.md v6.0 §3 and §10 reference `/permanent-tasks`. The skill is defined in T1 of
the task breakdown and fully specified in permanent-tasks-design.md §4. However, the
CLAUDE.md v6.0 rewrite doesn't include any details about what the skill does — it just
says "Use `/permanent-tasks` to reflect mid-work requirement changes."

**Assessment:** This is intentional (AD-1: say it once, the skill itself documents its
behavior). But a teammate or Lead reading only CLAUDE.md won't know the skill exists
until they encounter the reference. The §10 "See also" line mentions it, which helps.

**Severity: LOW** — Follows deduplication principle. Not a gap.

---

## Summary of All Findings

| # | Challenge | Category | Severity | Blocks Gate? |
|---|-----------|----------|----------|-------------|
| C-1.1 | NLP approach is sound | Correctness | PASS | No |
| C-1.2 | DIA v6.0 may weaken enforcement in early phases | Correctness | MEDIUM | No |
| C-2.1 | Line count claim inaccurate (~167 not ~136) | Completeness | MEDIUM | No |
| C-2.2 | Multiple v5.1 behaviors lost (max iterations, DIA mandate, spawn matrix, S-2 threshold) | Completeness | **HIGH** | **Potential** |
| C-2.3 | PT Operational Constraints not in CLAUDE.md or PT template | Completeness | MEDIUM | No |
| C-2.4 | Team Memory tags dropped | Completeness | LOW | No |
| C-3.1 | AD-7/8/9 consistent with AD-1~6 | Consistency | PASS | No |
| C-3.2 | "Impact Map" vs "Codebase Impact Map" naming | Consistency | LOW | No |
| C-3.3 | §3 ↔ §9 TaskGet references | Consistency | PASS | No |
| C-3.4 | Devils-advocate exemption not in CLAUDE.md | Consistency | LOW | No |
| C-4.1 | 12 tasks in 5-6 rounds feasible | Feasibility | PASS | No |
| C-4.2 | T4 ∥ T11 dependency contradiction | Feasibility | MEDIUM | No |
| C-4.3 | T3 exclusion coordination gap | Feasibility | MEDIUM | No |
| C-5.1 | Impact Map chicken-and-egg (Phases 1-2) | Robustness | MEDIUM | No |
| C-5.2 | TaskGet failure fallback | Robustness | LOW | No |
| C-5.3 | PT description size growth risk | Robustness | MEDIUM | No |
| C-5.4 | Teammate skips TaskGet | Robustness | LOW | No |
| C-6.1 | CLAUDE.md ↔ common-protocol interface | Interface | PASS | No |
| C-6.2 | Agent .md ↔ CLAUDE.md §6 alignment | Interface | PASS | No |
| C-6.3 | YAML frontmatter ↔ Team Memory access | Interface | LOW | No |
| C-6.4 | /permanent-tasks skill reference | Interface | LOW | No |

---

## Recommended Mitigations for HIGH/MEDIUM Issues

### C-2.2 (HIGH): Restore lost behaviors

Add to CLAUDE.md v6.0:
1. **§2 last line:** Add "Max 3 iterations per phase before escalating" after the
   shift-left sentence.
2. **§2 or §3:** Add one sentence: "Every assignment requires understanding verification
   before work begins." (restores the DIA pipeline-level mandate)
3. **§6 "Before Spawning":** Add the 6000-line read threshold back alongside the >4 files rule.
4. **§6 "Assigning Work":** Add a brief spawn count note: "Scale teammate count by
   module/research domain; Lead only for Phases 1 and 9."

These are ~4 additional lines. Well within the spirit of the design.

### C-2.1 (MEDIUM): Recount lines accurately

Recount using a consistent methodology: either total file lines (including blanks) or
explicitly label as "content lines excluding blanks." Update all line count tables.

### C-2.3 (MEDIUM): Place operational constraints

Add to CLAUDE.md v6.0 §6 "Before Spawning" or as a new subsection: "Max 2 concurrent
teammates. Split tasks to 1 file each when feasible." Alternatively, make these part of
the PT description template in permanent-tasks-design §3 under "Constraints."

### C-4.2 (MEDIUM): Fix dependency graph

Make T11 and T12 strictly dependent on T4 (not parallel with it). Adjust execution order:
```
R1: T1 ∥ T2
R2: T4 (common-protocol)
R3: T11 ∥ T12 (agent .md files, depend on T2 + T4)
R4: T5 ∥ T6
R5: T7 ∥ T8
R6: T9 ∥ T10
```
This adds 1 round but eliminates the dependency contradiction.

### C-4.3 (MEDIUM): Define cross-terminal coordination

Add a note to the task breakdown: "task-api-guideline.md GC→PT reference replacement
is the responsibility of the separate terminal. This pipeline's integrator (Phase 8)
verifies cross-terminal consistency."

### C-5.1 (MEDIUM): Explicitly acknowledge Impact Map scope

Add to CLAUDE.md v6.0 §6 "Verifying Understanding": "In early phases where the Impact Map
is sparse, ground questions in the task assignment context and available constraints."

### C-5.3 (MEDIUM): Add PT size discipline

Add to §10 Lead responsibilities: "Keep the PERMANENT Task description under 150 lines.
If it exceeds this, move the Impact Map to a referenced file."

---

## Final Assessment

The design is architecturally sound. The NLP conversion approach is well-grounded in research,
the PT integration is thorough, and the DIA v6.0 model is a genuine improvement over v5.0's
checklist-based verification. The 9 Architecture Decisions are internally consistent.

The main concern is C-2.2: the "28/28 preserved" claim is incorrect — at least 4 behavioral
requirements are lost in the rewrite. These are recoverable with ~4 additional lines, which
would not materially impact the design's line reduction goals.

All other issues are MEDIUM or LOW and have straightforward mitigations.
