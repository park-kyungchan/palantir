# L2 Summary — Correctness Challenge (C-1 + C-2)

## Summary

The implementation plan **correctly solves the stated problem**: 22-file Big Bang achieves 9-skill restructuring, 3 fork agents, 8 coordinator convergence, and §10 modification as designed. No fundamental logic errors found. However, 2 HIGH consistency issues and 7 MEDIUM issues require attention before Phase 6 execution. Verdict: **CONDITIONAL_PASS** — resolve CH-01 and CH-02 before proceeding.

## Correctness Issues (C-1)

### CH-02: Protocol Exception Text Ambiguity [HIGH]

**Location:** Implementation plan §5 line 262 + interface-planner L3 §2.2 line 291-292

**Issue:** The agent-common-protocol.md §Task API exception says:
> "If your agent .md frontmatter does NOT include TaskCreate/TaskUpdate in `disallowedTools`, you have explicit Task API write access."

The slash in "TaskCreate/TaskUpdate" creates three possible readings:
1. "Neither tool in disallowedTools" → only pt-manager qualifies (wrong for delivery-agent, rsil-agent)
2. "Both tools absent from disallowedTools" → only pt-manager qualifies (same issue)
3. "For whichever tool is NOT in disallowedTools" → intended reading (partial access)

**Impact:** delivery-agent and rsil-agent have `disallowedTools: [TaskCreate]` — TaskCreate IS listed but TaskUpdate is NOT. Under reading #1/#2, they might incorrectly conclude the exception doesn't apply to them.

**Mitigation:** Low runtime risk because `disallowedTools` frontmatter (primary layer) enforces correct behavior regardless of NL interpretation. But the text should be clarified.

**Proposed fix:** Replace with:
> "If your agent .md grants Task API tools not blocked by `disallowedTools`, you have explicit write access for those specific tools."

### CH-05: testing-coordinator Line Count Wrong [MEDIUM]

**Location:** Implementation plan §5 gap analysis (line 338)

**Issue:** Plan says testing-coordinator current size is 98L. Actual file is 117L (verified via `wc -l`). 19-line discrepancy affects Template A→B delta estimation (target ~55L = 62L reduction, not 43L as planned).

**Impact:** infra-c implementer will find more content than expected. The extra 19 lines may contain unique logic that should be preserved vs boilerplate that should be removed. Without knowing the actual content distribution, the implementer may make wrong preservation decisions.

**Proposed fix:** Update gap analysis to 117→~55L. Infra-c implementer should read current file before editing (AC-0 already requires this, providing defense-in-depth).

### CH-08: impl-b 5-File Assignment [MEDIUM]

**Location:** Implementation plan §1 line 168, §3 line 168

**Issue:** impl-b owns 5 coordinator-based SKILL.md files, exceeding the BUG-002 4-file guideline. Justification is "same template variant" — but the architecture confirms 61-75% unique content per skill. Each skill is 362-692L with unique orchestration logic, gate criteria, and phase-specific workflows. Total read load: ~2,675L of existing content plus P3/P4 architecture artifacts.

**Impact:** Context pressure risk. impl-b must read each skill, understand its unique 60%+ content, apply template restructuring while preserving unique logic, add §C Interface per C-1 contract, migrate GC operations per D-14, and ensure voice/cross-cutting consistency. This is the most cognitively demanding single-implementer assignment.

**Proposed mitigation:** Accept 5 files (splitting creates cross-template consistency risk) but set explicit checkpoint: impl-b reports L1 after completing first 2 skills. If context pressure is evident, split remaining 3 skills to a second implementer.

### CH-09: infra-c 8-File Assignment [MEDIUM]

**Location:** Implementation plan §1 line 169, §3 line 169

**Issue:** infra-c owns 8 coordinator .md files (2x BUG-002 guideline). While justified as "small files, highly templated," the reality is mixed:
- 3 files (architecture, planning, validation): Minor frontmatter changes only (~5 edits each). Truly trivial.
- 5 files (research, verification, execution, testing, infra-quality): Template A→B restructure requiring removal of 5 inlined sections, retention of unique logic, and addition of protocol references. Non-trivial.

Total read load: ~700L of existing coordinator files + coordinator-shared-protocol.md + agent-common-protocol.md for reference.

**Proposed mitigation:** Accept 8 files — the total read load is manageable even though file count is high. The formulaic nature (same Template B target) reduces cognitive load. AC-0 read-first requirement provides safety.

### CH-11: planning-coordinator Line Count [LOW]

**Location:** Implementation plan §5 gap analysis (line 336)

**Issue:** Plan says planning-coordinator is 58L, actual is 60L (2L off). Trivial discrepancy, likely a trailing newline difference from P2 research.

**Impact:** None. AC-0 read-first requirement catches this.

## Requirement Coverage

All 10 PT decisions (D-6 through D-15) are addressed in the plan:
- D-6 (Precision Refocus): 4-section template ✓
- D-7 (PT-centric): §C Interface + GC migration ✓
- D-8 (Big Bang): Atomic commit + rollback ✓
- D-9 (Fork): Fork template + 3 agents ✓
- D-10 (§10): Exact text + 3-layer enforcement ✓
- D-11 (Fork agents): Full designs in risk-architect L3 ✓
- D-12 (Lean PT): Pointer-based schema ✓
- D-13 (Coordinator convergence): Template B + 25 gaps filled ✓
- D-14 (GC 14→3): Per-skill migration specs ✓
- D-15 (Custom agents feasible): Primary path + RISK-1 fallback ✓

All 6 interface contracts (C-1 through C-6) are specified and verifiable.

## Consistency Issues (C-2)

### CH-01: RISK-8 Fallback Contradiction [HIGH]

**Location:** section-5-specs.md (file #2, lines 162-170) vs interface-design.md (lines 233-238)

**Issue:** Two L3 documents describe incompatible fallback mechanisms for permanent-tasks under RISK-8 (isolated task list):

**section-5-specs (decomposition-planner):** Dynamic Context injects `!cd /home/palantir && claude task list` output pre-fork. Fork agent parses rendered output for [PERMANENT] task ID. If found, uses TaskGet directly. Assumes TaskGet works with explicit ID even in isolated scope.

**interface-design (interface-planner):** $ARGUMENTS carries full PT content. Fork agent writes PT to file (`permanent-tasks-output.md`). Lead reads file and applies manually. Declares this "HIGHEST IMPACT RISK-8 scenario" — assumes TaskGet also fails in isolated scope.

**Root cause:** The two planners have different assumptions about RISK-8 scope isolation depth:
- section-5-specs: TaskList fails but TaskGet with explicit ID still works
- interface-design: Full Task API is unreachable from fork scope

**Impact:** If implementer follows section-5-specs and RISK-8 triggers with full isolation, the fallback fails silently (TaskGet returns error, no file-based backup). If implementer follows interface-design, the fallback works but requires more complex implementation.

**Proposed fix:** Designate interface-planner version as authoritative (it's more conservative and addresses the worse scenario). Update section-5-specs RISK-8 delta to align. The conservative approach is correct: if task list is isolated, assume all Task API calls are isolated.

### CH-03: VL Count Mismatch [MEDIUM]

**Location:** Implementation plan §5 VL Summary (lines 238-240)

**Issue:**
- Plan summary: VL-1=6, VL-2=5, VL-3=11 (total=22)
- Per-file specs: VL-1=5, VL-2=5, VL-3=12 (total=22)

VL-1 files by per-file spec: #15 (architecture-coord), #16 (planning-coord), #17 (validation-coord), #21 (CLAUDE.md), #22 (protocol) = **5 files**.
VL-3 files: #1-#12 (3 agents + 4 fork skills + 5 coord skills) = **12 files**.

The plan summary claims 1 extra VL-1 and 1 fewer VL-3. The garbled note "(brainstorming excluded from VL-3→VL-3)" suggests an editing artifact.

**Impact:** Verifier (Task V) uses VL levels to scope validation depth. Wrong VL assignment could under-validate a VL-3 file (treated as VL-1) or over-validate a VL-1 file.

**Proposed fix:** Correct to VL-1=5, VL-2=5, VL-3=12. Remove garbled text.

### CH-04: §10 Modification Text Divergence [MEDIUM]

**Location:** Three sources for the same exact text

| Source | Intro phrase | rsil-agent description |
|--------|-------------|----------------------|
| Implementation plan §5 (line 248-258) | "Fork Task API scope:" | "updates PT with review results" |
| section-5-specs file #21 (line 26-34) | "Fork Task API access is:" | "updates PT Phase Status with review results" |
| interface-planner L3 §2.1 (line 258-267) | "Fork Task API scope:" | "updates PT with review results" |

**Impact:** infra-d implementer has 3 references for the "exact text" — but they disagree on the intro phrase and rsil-agent description detail. The interface-planner L3 §2.2 is designated as "Authority" in both the plan and section-5-specs, so it should be canonical.

**Proposed fix:** Designate interface-planner L3 §2.1/§2.2 as sole authoritative source. Update section-5-specs to match. Alternatively, infra-d's task directive should explicitly say "use interface-planner L3 §2.2 text verbatim."

### CH-06: Interface Section Heading Inconsistency [MEDIUM]

**Location:** Multiple documents use different heading text:

| Document | Heading |
|----------|---------|
| structure-architect L3 §1.2 (line 87) | `## C) Interface Section` |
| interface-planner L3 §1.1 (line 21ff) | `## C) Interface` |
| Implementation plan V4 (line 437) | `C) Interface` (inline) |
| Strategy-planner V4 (line 235) | `## C) Interface Section` |

**Impact:** V4 template validation checks heading ordering. If the canonical heading is "## C) Interface" but an implementer writes "## C) Interface Section" (or vice versa), V4 will false-fail. Inconsistency could also propagate to all 5 coordinator skills with different implementers writing different headings.

**Proposed fix:** Standardize on `## C) Interface` (shorter, matches interface-planner authority). Update V4 spec to use this exact heading.

### CH-07: L3 Section Range Header Mismatch [MEDIUM]

**Location:** section-5-specs.md, Group 5 (coord-convergence)

**Issue:** Section header reads "Files #13-#17: Template A → Template B (5 coordinators requiring body restructure)" but actually contains files #13, #14, #18, #19, #20 (the 5 Template A→B coordinators). Files #15-#17 are in the next section "Files #15-#17: Template B → Template B."

The header "#13-#17" implies contiguous file numbers 13,14,15,16,17 — but files 15,16,17 belong to the Template B→B section, not the Template A→B section.

**Impact:** infra-c implementer reading "#13-#17" header may assume files #15-17 are Template A→B (wrong — they're Template B→B minor changes). Could lead to unnecessary restructuring of already-conformant files.

**Proposed fix:** Rename header to "Files #13-#14, #18-#20: Template A → Template B" for accuracy.

### CH-10: Task B Processing Order [LOW]

**Location:** Implementation plan §4 Task B (line 173-178)

**Issue:** Processing order says "smallest to largest" but lists: write-plan (362), validation (434), brainstorming (613), verification (574), execution (692). Brainstorming (613) comes before verification (574), violating the stated principle.

Correct size order: write-plan (362) < validation (434) < verification (574) < brainstorming (613) < execution (692).

**Impact:** Minor. The ordering principle is advisory (build template familiarity), not a hard dependency. impl-b can reorder at their discretion.

### CH-12: Commit Message C-1~C-5 vs C-1~C-6 [LOW]

**Location:** Implementation plan §9 commit message (line 551)

**Issue:** Commit message says "C-1~C-5 contracts" but the plan defines 6 contracts (C-1 through C-6). C-6 is the 4-way naming consistency contract.

**Impact:** Cosmetic — commit message is for documentation, not execution. C-6 is enforced by Task V checks regardless.

## Verdict

**CONDITIONAL_PASS** — The plan is logically sound and addresses all stated requirements. Two HIGH issues require resolution:

1. **CH-01 (RISK-8 fallback):** Resolve contradiction between two L3 documents by designating interface-planner version as authoritative.
2. **CH-02 (Protocol text):** Clarify the "TaskCreate/TaskUpdate" phrasing to unambiguously describe partial access.

Seven MEDIUM issues should be addressed during Phase 6 setup (directive construction or pre-implementation briefing). Three LOW issues are cosmetic.

## PT Goal Linkage

| PT Decision | Challenge | Status |
|-------------|-----------|--------|
| D-7 (PT-centric) | C-1~C-6 contracts correctly reflected in per-file specs | VERIFIED ✓ |
| D-8 (Big Bang) | 22-file count verified, staging command complete | VERIFIED ✓ |
| D-10 (§10) | CH-04 text divergence across 3 sources | NEEDS FIX |
| D-11 (Fork agents) | Fork .md designs match risk-architect L3 exactly | VERIFIED ✓ |
| D-13 (Coordinator) | CH-05 line count off for testing-coord | NEEDS FIX |
| RISK-5 (Big Bang) | Validation checklist comprehensive (V1-V6) | VERIFIED ✓ |
| RISK-8 (Task scope) | CH-01 fallback contradiction | NEEDS FIX |

## Evidence Sources

| Source | Lines Read | Key Findings |
|--------|:---------:|--------------|
| Implementation plan (main doc) | 630L | CH-03 (VL mismatch), CH-10 (order), CH-12 (commit msg) |
| section-5-specs.md (decomp-planner L3) | 737L | CH-01 (RISK-8 contradiction), CH-04 (§10 text), CH-05 (line count), CH-07 (range header) |
| interface-design.md (interface-planner L3) | 541L | CH-01 (RISK-8 alt), CH-02 (protocol text), CH-04 (§10 text), CH-06 (heading) |
| sections-6-through-10.md (strategy-planner L3) | 536L | CH-06 (heading variant), V4 spec cross-ref |
| section-4-tasks.md (decomp-planner L3) | 348L | Task acceptance criteria verification, CH-08/CH-09 scope |
| Phase 3 arch-coord L2 | 221L | Architecture decision cross-reference |
| Phase 3 risk-architect L3 | 353L (partial) | Fork agent .md design verification |
| Phase 3 structure-architect L3 | 100L (partial) | Template skeleton verification |
| Phase 3 interface-architect L3 | 100L (partial) | PT contract verification |
| Actual files (wc -l) | 12 files | CH-05 (117L vs 98L), CH-11 (60L vs 58L) |
| CLAUDE.md + protocol (grep) | 2 checks | §10 line 364 + §Task API lines 72-76 verified |
