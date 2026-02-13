# Correctness Challenge — Full Report

## Methodology

1. Read all Phase 4 L3 artifacts (2,713L total across 4 files)
2. Read Phase 3 architecture L2 (221L) and partial L3s (~553L from risk/structure/interface architects)
3. Verified current file states for 12 files via `wc -l` and `grep`
4. Cross-referenced implementation plan against architecture decisions, per-file specs, interface contracts, and strategy specs
5. Applied C-1 (correctness) and C-2 (consistency) lenses systematically

## Challenge Analysis

### CH-01: RISK-8 Fallback Contradiction for permanent-tasks [HIGH, C-2]

**Full analysis:**

Two Phase 4 planners independently wrote RISK-8 fallback specs for permanent-tasks — the highest-impact RISK-8 scenario. They made different assumptions about the depth of scope isolation.

**Decomposition planner (section-5-specs file #2, lines 162-170):**
```
Fallback: Dynamic Context injects TaskList output pre-fork via `!command`.
Fork agent parses rendered output for [PERMANENT] task ID. If found, uses TaskGet
directly. If not found, proceeds to Step 2A (create).
```
This assumes: TaskList fails in fork scope, but TaskGet with explicit ID still works. The fallback relies on Dynamic Context `!cd /home/palantir && claude task list` to discover the task ID, then TaskGet to read PT content.

**Interface planner (interface-design.md lines 233-238):**
```
permanent-tasks IS the PT lifecycle manager. If isolated task list:
- TaskList/TaskGet in wrong scope → cannot discover or read PT
- TaskCreate creates PT in wrong list → Lead cannot find it
- Fallback: $ARGUMENTS must carry full PT content. Fork agent writes PT content
  to a file (permanent-tasks-output.md). Lead reads file and applies via
  TaskUpdate/TaskCreate manually.
```
This assumes: ALL Task API calls are isolated. TaskGet also fails. The entire Task API is unreachable from fork scope. Fallback requires file-based workaround.

**Why this matters:** If pre-deploy Phase A3 reveals isolated task scope, the implementer needs ONE fallback path. Currently there are two incompatible paths. If the decomposition-planner path is chosen but scope isolation is deep (TaskGet also fails), the fallback silently fails — pt-manager can discover the ID from Dynamic Context but can't actually read the PT.

**Recommendation:** Interface-planner version is safer (conservative assumption). Adopt it as the authoritative fallback. Additionally:
- The interface-planner fallback is also more aligned with RISK-8's stated nature ("Task list scope in fork" implies scope-level isolation, not tool-level)
- The decomposition-planner's `!claude task list` injection is creative but depends on CC CLI availability in Dynamic Context — another unvalidated assumption

---

### CH-02: Protocol Exception Text Ambiguity [HIGH, C-1]

**Full analysis:**

The proposed agent-common-protocol.md exception text reads:
> "If your agent .md frontmatter does NOT include TaskCreate/TaskUpdate in `disallowedTools`, you have explicit Task API write access."

**Three possible readings:**
1. "If your disallowedTools doesn't include [either TaskCreate or TaskUpdate]" → only agents with `disallowedTools: []` qualify (pt-manager only)
2. "If your disallowedTools doesn't include [both TaskCreate and TaskUpdate]" → agents missing either one qualify (all 3 agents)
3. "For whichever of [TaskCreate, TaskUpdate] is NOT in your disallowedTools" → intended reading (partial access per tool)

**Why reading #3 is intended but not clear:**
- pt-manager: `disallowedTools: []` → gets both TaskCreate + TaskUpdate ✓
- delivery-agent: `disallowedTools: [TaskCreate]` → gets TaskUpdate only ✓
- rsil-agent: `disallowedTools: [TaskCreate]` → gets TaskUpdate only ✓

Under reading #1, delivery-agent and rsil-agent would conclude the exception doesn't apply (since TaskCreate IS in their disallowedTools). They'd think they have NO Task API write access — even though the tool is actually available to them (CC enforces disallowedTools at the tool level, not NL level).

**Practical risk assessment:**
- PRIMARY enforcement: `disallowedTools` frontmatter → CC enforces this regardless of NL text
- SECONDARY enforcement: agent .md body explicitly states scope ("No TaskCreate" etc.)
- TERTIARY: this protocol text

So the ambiguity is in the tertiary layer — CC's tool enforcement is correct regardless. Risk is LOW for actual behavior failure, but MEDIUM for agent confusion/hallucination if the fork agent reads the protocol and concludes it has no write access.

**Proposed fix options:**
1. Rewrite: "For each Task API tool (TaskCreate, TaskUpdate) that is NOT listed in your `disallowedTools`, you have explicit write access."
2. Rewrite: "Fork agents have Task API write access as scoped by their agent .md `disallowedTools` — tools not listed are available."
3. Remove the generic statement; list per-agent access explicitly (most unambiguous but verbose).

---

### CH-03: VL Count Distribution Mismatch [MEDIUM, C-2]

**Implementation plan §5 (lines 238-240):**
```
| VL-1 (visual inspection) | 6 | CLAUDE.md, protocol, architecture-coord, planning-coord, validation-coord |
| VL-2 (cross-reference) | 5 | research-coord, verification-coord, execution-coord, testing-coord, infra-quality-coord |
| VL-3 (full spec validation) | 11 | 3 new agent .md, 4 fork SKILL.md, 4 complex coord SKILL.md (brainstorming excluded from VL-3→VL-3) |
```

**Actual VL assignment from per-file specs (section-5-specs.md):**
- VL-1: files #15 (arch-coord), #16 (plan-coord), #17 (val-coord), #21 (CLAUDE.md), #22 (protocol) = **5**
- VL-2: files #13 (research-coord), #14 (verif-coord), #18 (exec-coord), #19 (testing-coord), #20 (infra-quality-coord) = **5**
- VL-3: files #1-#12 (3 agents + 4 fork skills + 5 coord skills) = **12**

The plan's VL-1 list names only 5 files but claims count=6. The plan's VL-3 claims 11 files with a garbled note "(brainstorming excluded from VL-3→VL-3)." All 5 coordinator-based SKILL.md files (#8-#12) are VL-3 in the per-file specs.

**Root cause:** Likely an editing error — one file may have been shifted between VL-1 and VL-3 during plan consolidation, with the count updated but the list not (or vice versa).

---

### CH-04: §10 Modification Text Divergence [MEDIUM, C-2]

Three documents provide the "exact" replacement text for CLAUDE.md §10. They differ:

**Difference 1 — Intro phrase:**
- Implementation plan §5 + interface-planner L3: "Fork Task API scope:"
- section-5-specs file #21: "Fork Task API access is:"

**Difference 2 — rsil-agent description:**
- Implementation plan §5 + interface-planner L3: "rsil-agent: TaskUpdate only (updates PT with review results)"
- section-5-specs file #21: "rsil-agent: TaskUpdate only (updates PT Phase Status with review results)"

The section-5-specs version adds "Phase Status" which is more precise (rsil-agent's primary TaskUpdate target is the phase_status section). But it deviates from the interface-planner's "exact text."

**Authority hierarchy:** Implementation plan §5 explicitly says "Authority: interface-architect L3 §2.2 (exact text)" for file #21. The section-5-specs should have quoted the interface-planner verbatim but deviated.

---

### CH-05: testing-coordinator Line Count [MEDIUM, C-1]

**Verified:** `wc -l .claude/agents/testing-coordinator.md` = **117L**
**Plan gap analysis (line 338):** states **98L**
**Discrepancy:** 19 lines (16% error)

This means the delta is larger than expected: 117→~55 = 62L reduction, not 43L (from 98→~55). The implementer will find ~19 extra lines that weren't accounted for in the template analysis. These could be:
- Additional unique logic that should be preserved
- Boilerplate that should be removed (but wasn't inventoried)
- Blank lines or comments

AC-0 (read before edit) provides defense, but the infra-c implementer's mental model of "small 98L file" will be wrong, potentially causing premature decisions about what to keep vs remove.

---

### CH-06: Interface Section Heading [MEDIUM, C-2]

**Variant inventory:**
| Source | Text |
|--------|------|
| structure-architect L3 §1.2 line 87 | `## C) Interface Section` |
| interface-planner L3 §1.1 examples | `## C) Interface` |
| Implementation plan §5 line 287 (format) | `## C) Interface` |
| Strategy-planner V4 line 235 (coordinator template) | `## C) Interface Section` |
| Strategy-planner V4 line 249 (fork template) | `## Interface` (no C prefix) |
| Common changes block (section-5-specs line 383) | `## C) Interface Section` |

The fork template drops the "C)" prefix (correct — fork sections are unprefixed per template design). But the coordinator template has two variants: with and without "Section" suffix.

If V4 validation uses exact heading match, 50% of references will fail regardless of which form the implementer chooses. The implementer needs ONE canonical form.

---

### CH-07: Section-5-Specs Range Header [MEDIUM, C-2]

The section organizing Template A→B coordinator files uses header:
```
### Files #13-#17: Template A → Template B (5 coordinators requiring body restructure)
```
But actually contains: File #13 (research), #14 (verification), #18 (execution), #19 (testing), #20 (infra-quality).

Files #15-#17 (architecture, planning, validation) are in the next section for Template B→B minor changes.

The range "#13-#17" suggests contiguous numbering but the actual contents skip #15-17 and include #18-20. This creates a reading confusion where infra-c implementer might:
1. Look for files #15-17 in the A→B section (not there)
2. Miss files #18-20 thinking they're in a different section
3. Incorrectly apply A→B restructure to #15-17 (already Template B)

---

### CH-08: impl-b 5-File Scope [MEDIUM, C-1]

**Quantitative analysis:**
- 5 skills × avg 535L = 2,675L of source reading
- Plus architecture artifacts (template skeleton ~100L, per-skill inventory ~150L, interface contract ~120L)
- Plus current GC operations to identify and remove (~50 operations across 5 skills per interface-planner §3)
- Total input: ~3,100L

Each skill requires:
1. Read current file (362-692L)
2. Identify unique vs template sections (per structure-architect §6.2 classification)
3. Apply §A/§B/§C/§D restructure
4. Migrate GC operations (5-15 per skill per interface-planner §3)
5. Add §C Interface content (per interface-planner §1.1)
6. Change voice if needed (coordinator = third person)
7. Self-verify template conformance (V4 section ordering)

BUG-002 guideline exists because context pressure causes auto-compaction before L1/L2 generation. While "same template" reduces cognitive complexity, the 61-75% unique content means each skill is substantially its own problem. The template provides structural scaffolding but not content guidance.

**Risk:** impl-b hits context pressure after completing 3 of 5 skills. Remaining 2 skills lose architecture context. impl-b produces lower-quality output for skills 4 and 5.

**Counter-argument:** impl-b builds template familiarity with each skill (stated rationale). By skill 3-4, the template pattern is internalized. Also, impl-b's task is primarily restructuring (moving existing sections into new template) not creation — lower creative load than impl-a1/a2.

---

### CH-09: infra-c 8-File Scope [MEDIUM, C-1]

**Quantitative analysis:**
- 5 Template A→B files × avg 114L = 570L source reading
- 3 Template B→B files × avg 60L = 180L source reading
- coordinator-shared-protocol.md reference: ~100L
- agent-common-protocol.md reference: ~180L
- Total input: ~1,030L

While the total is manageable, the Template A→B work requires:
1. Identify which sections are inlined boilerplate (→ remove)
2. Identify unique logic (→ preserve in "How to Work")
3. Restructure to 5-section body
4. Add protocol references (2 lines)
5. Update frontmatter (memory, color, disallowedTools)

The 3 Template B→B files are trivially simple (3 frontmatter additions each).

**Risk:** Lower than CH-08. Coordinator files are shorter and the work is more formulaic (same target template, clear preserve-vs-remove classification). The main risk is the execution-coordinator (#18) which has ~45L of unique review dispatch logic that must be carefully preserved — but at 150L total, it's still small.

---

### CH-10: Task B Processing Order [LOW, C-2]

Stated principle: "smallest to largest (build template familiarity)"
Actual order: write-plan (362), validation (434), **brainstorming (613)**, **verification (574)**, execution (692)

Correct by-size order: write-plan (362), validation (434), verification (574), brainstorming (613), execution (692)

Brainstorming and verification are swapped. This might be intentional (brainstorming covers 3 phases P1-P3 making it architecturally more complex despite similar size to verification) but contradicts the stated size-based rationale.

---

### CH-11: planning-coordinator Line Count [LOW, C-1]

Plan says 58L, actual is 60L. 2-line difference is within measurement error (trailing newlines, P2 research timing).

---

### CH-12: Commit Message C-1~C-5 [LOW, C-2]

Commit message line: "All 9 skills gain new Interface Section (C-1~C-5 contracts)"
Plan defines C-1 through C-6 where C-6 is 4-way naming consistency.

C-6 is not about Interface Sections specifically — it's about cross-file naming. So "C-1~C-5 contracts" in the Interface Section context is defensible. But the commit message represents the full change, not just Interface Sections. A reader might infer only 5 contracts exist.

## Cross-Reference Verification

### 4-Way Naming Contract
All 4 locations checked for consistency:
1. Implementation plan §5 naming table (line 343-347): ✓ all 3 names match
2. Per-file specs agent: fields: ✓ match
3. §10 text in interface-planner L3: ✓ match
4. Protocol exception in interface-planner L3: ✓ match

### File Ownership vs Per-File Specs
- Implementation plan §3 (22 files, 5 coupling groups): ✓
- section-5-specs (22 files, 5 groups): ✓ same mapping
- No file appears in two owners: ✓ verified

### Architecture Decisions vs Plan
All 8 ADR-S/D decisions from arch-coord L2 are reflected in the plan:
- ADR-S1 (2 templates): ✓
- D-7 (PT-centric): ✓
- D-11 (fork agents): ✓
- D-13 (coordinator convergence): ✓
- C-5 (§10 exception): ✓
- D-14 (GC 14→3): ✓
- ADR-S5 (shared rsil-agent): ✓
- ADR-S8 (fork inline cross-cutting): ✓

### Fork Agent Tool Lists
Verified against risk-architect L3 §1:
- pt-manager: 9 tools, `disallowedTools: []` ✓
- delivery-agent: 10 tools, `disallowedTools: [TaskCreate]` ✓
- rsil-agent: 10 tools, `disallowedTools: [TaskCreate]` ✓

## Summary of Mitigations Required

| # | Challenge | Severity | Required Action | Owner |
|---|-----------|----------|----------------|-------|
| CH-01 | RISK-8 fallback | HIGH | Designate interface-planner as authoritative; update section-5-specs | Lead (pre-P6) |
| CH-02 | Protocol text | HIGH | Rewrite exception paragraph; get infra-d clear directive | Lead (pre-P6) |
| CH-03 | VL counts | MEDIUM | Fix summary to VL-1=5, VL-3=12 | Lead (plan update) |
| CH-04 | §10 text | MEDIUM | Designate interface-planner §2.2 as sole source; tell infra-d | Lead (directive) |
| CH-05 | Line count | MEDIUM | Update 98→117 in gap analysis; note in infra-c directive | Lead (directive) |
| CH-06 | Heading | MEDIUM | Standardize on "## C) Interface" for coordinator, "## Interface" for fork | Lead (directive) |
| CH-07 | Range header | MEDIUM | Rename to "#13-#14, #18-#20" or add clarifying note | Lead (plan update) |
| CH-08 | impl-b scope | MEDIUM | Add checkpoint after first 2 skills; split if pressure detected | Lead (directive) |
| CH-09 | infra-c scope | MEDIUM | Accept; flag execution-coord unique logic preservation | Lead (directive) |
| CH-10 | Order | LOW | Accept or swap brainstorming/verification in directive | Lead (optional) |
| CH-11 | Line count | LOW | Accept; AC-0 catches | No action |
| CH-12 | Commit msg | LOW | Update to C-1~C-6 or accept | Lead (optional) |

---

## Critical Scrutiny Areas (Coordinator-Assigned)

The following 4 areas were specifically requested by validation-coord for deep analysis.

### CSA-1: Wave Ordering vs Cross-Implementer Timing

**Question:** §6 says all 5 implementers start simultaneously. What if infra-d modifies §10 AFTER impl-a1 reads §10 for context?

**Analysis:** No cross-implementer data dependency exists during Wave 1:

| Implementer | Reads from other implementers? | Creates/Modifies | Data source |
|-------------|:------------------------------:|-------------------|-------------|
| impl-a1 | NO | pt-manager.md, permanent-tasks SKILL, delivery-agent.md, delivery-pipeline SKILL | risk-architect L3 §1.1/§1.2 (pre-existing P3 artifact) |
| impl-a2 | NO | rsil-agent.md, rsil-global SKILL, rsil-review SKILL | risk-architect L3 §1.3 (pre-existing P3 artifact) |
| impl-b | NO | 5 coordinator SKILL.md | structure-architect L3 + interface-planner L3 (pre-existing P3/P4 artifacts) |
| infra-c | NO | 8 coordinator .md | structure-architect L3 §5.2 (pre-existing P3 artifact) |
| infra-d | NO | CLAUDE.md §10, agent-common-protocol.md | interface-planner L3 §2.2 (pre-existing P4 artifact) |

**Key insight:** Every implementer's data source is a Phase 3 or Phase 4 artifact — NOT another implementer's output. impl-a1 does NOT read CLAUDE.md §10 during implementation. It reads the risk-architect L3 for pt-manager.md's design. The §10 reference is for runtime enforcement (when agents read CLAUDE.md), not build-time dependency.

**The INTERNAL dependency within impl-a1/impl-a2 is correctly identified:** Each must CREATE their agent .md BEFORE modifying the corresponding SKILL.md (because the SKILL.md frontmatter `agent: "X"` references the agent .md filename). This is sequential within one implementer, not cross-implementer.

**Conclusion:** The plan's simultaneous start claim is **CORRECT**. No cross-implementer timing issues exist. The cross-file dependency matrix (§6 lines 396-408) correctly classifies all cross-group dependencies as "weak" (consistency) or "none," with the only "STRONG" dependency (fork SKILL → fork agent .md) being INTERNAL to the same implementer.

### CSA-2: PT Chain Integrity

**Question:** Each skill reads PT-v{N} and writes PT-v{N+1}. What if two skills run in the same phase and both try to increment?

**Analysis of the PT version chain:**

```
brainstorming-pipeline  → creates PT-v1       (Phase 1-3)
agent-teams-write-plan  → writes PT-v2        (Phase 4)
plan-validation-pipeline → writes PT-v3       (Phase 5)
agent-teams-execution-plan → writes PT-v4     (Phase 6)
verification-pipeline   → writes PT-v5        (Phase 7-8)
delivery-pipeline       → writes PT-vFinal    (Phase 9)
permanent-tasks         → writes PT-v{N+1}    (any time, user-invoked)
rsil-global             → writes PT-v{N+1}    (post-pipeline, rare)
rsil-review             → writes PT-v{N+1}    (any phase, user-invoked)
```

**No concurrent increment risk for pipeline skills:** The 6 pipeline skills (brainstorming through delivery) run sequentially — each phase completes before the next begins. No two pipeline skills execute simultaneously. PT-v{N} always refers to a single, consistent state.

**Cross-cutting skills (permanent-tasks, rsil-global, rsil-review):** These can be invoked at any time. However:
- **Fork execution model:** These are fork-context skills — Lead invokes them via Skill tool, CC creates a fork. Lead is BLOCKED during fork execution and cannot invoke another skill concurrently.
- **No concurrent Lead:** There's only one Lead session. Lead can't run /permanent-tasks AND /agent-teams-execution-plan simultaneously.
- **Read-Merge-Write pattern:** permanent-tasks uses Read-Merge-Write (TaskGet → merge → TaskUpdate), which is idempotent. Even if theoretical concurrency existed, the pattern would produce a valid merged state.

**Conclusion:** PT chain integrity is **MAINTAINED** by sequential skill execution. No concurrent increment risk exists.

### CSA-3: §10 Text Precision

**Question:** Does the exact replacement text semantically match the 3-layer enforcement model?

**Analysis:** Covered by CH-04 (text divergence) and CH-02 (protocol ambiguity). Additionally:

The 3-layer enforcement model (§2 table, line 96-97):
- Layer 1 (Primary): `disallowedTools` frontmatter → CC enforces at tool level
- Layer 2 (Secondary): NL instruction in agent .md body → behavioral guidance
- Layer 3 (Tertiary): CLAUDE.md §10 policy statement → documentation

The §10 text (interface-planner L3 §2.1, lines 258-267) correctly reflects this model:
- Names all 3 agents ✓
- Specifies per-agent Task API scope ✓
- Uses language consistent with "extensions of Lead's intent" framing ✓
- References "agent .md frontmatter" as the enforcement mechanism (Layer 1) ✓

The protocol text (interface-planner L3 §2.2, lines 291-295) has the ambiguity noted in CH-02, but semantically supports the 3-layer model by referencing `disallowedTools` as the gating mechanism.

**Conclusion:** §10 text **semantically matches** the 3-layer model. CH-02 ambiguity and CH-04 text divergence are the only issues.

### CSA-4: GC Migration Completeness

**Question:** 22 writes removed + 15 reads replaced + 8 kept = does this account for all GC operations?

**Analysis:** Verified against the interface-planner L3 §3 per-skill GC migration specs (lines 318-431) which provide line-level references to current SKILL.md files:

| Skill | Writes Removed | Reads Replaced | Kept | Subtotal |
|-------|:--------------:|:--------------:|:----:|:--------:|
| brainstorming | 6 (Gates 2-3) | 0 (pipeline start) | 3 (Gate 1 scratch) | 9 |
| write-plan | 6 (Gate 4) | 5 (discovery+directive) | 1 (status) | 12 |
| validation | 2 (Gate 5) | 4 (discovery) | 1 (status) | 7 |
| execution | 5 (termination) | 3 (discovery) | 2 (status+gate) | 10 |
| verification | 3 (Gates 7-8+term) | 2 (V-1+copy) | 1 (status) | 6 |
| delivery | 0 | 1 (GC fallback removed) | 0 | 1 |
| rsil-global | 0 | 0 | 0 | 0 |
| rsil-review | 0 | 0 | 0 | 0 |
| permanent-tasks | 0 | 0 | 0 | 0 |
| **Total** | **22** | **15** | **8** | **45** |

**Verification method:** The interface-planner L3 §3 provides specific SKILL.md line references for each operation (e.g., "Gate 2 (L377-387)", "V-1 (L106)"). These line references were checked against the actual skill files during P4 research (23 source files read per planning-coord L2 evidence).

**rsil-global, rsil-review, permanent-tasks have zero GC operations** — confirmed. These skills never read or write GC (they were built after the GC pattern was deprecated).

**delivery-pipeline has 1 GC read removed:** The current V-1 fallback at line ~127 says "PT exists with Phase 7/8 COMPLETE — OR — GC exists." The OR-GC fallback is removed entirely — PT becomes the sole authority.

**Are any GC operations missed?** The interface-planner analyzed all 9 SKILL.md files (4,430L total per evidence table). The per-skill line references anchor each claimed operation to specific code. Unless a GC operation uses non-standard terminology not caught by the search, the count is complete.

**Conclusion:** GC migration accounting is **COMPLETE**. 22+15+8=45 operations across 6 skills (3 fork skills have zero GC interaction). The remaining 3 GC "kept" concerns (execution metrics, gate records, version marker) are correctly classified as session-scoped scratch that no downstream skill consumes for logic decisions.
