# Narrow RSIL — Process Definition & Cumulative Tracker

> Future brainstorming-pipeline topic candidate. Tracks meta-cognitive skill improvements across pipeline executions.

**Created:** 2026-02-08
**Origin:** SKL-006 Delivery Pipeline sprint — user-initiated pilot test
**Status:** Active (updating after each pipeline skill execution)

---

## 1. Workflow Definition

### What Is Narrow RSIL?

A post-execution meta-cognitive quality review of each pipeline skill. Identifies improvements grounded in Claude Code native capabilities (Layer 1 only), filtered through the NL-First Boundary Framework (AD-15).

### Why?

Each pipeline skill execution is an opportunity to observe:
- What worked well vs. what deviated from design
- What native CC/Opus 4.6 capabilities could improve the skill
- Where NL instructions succeeded or fell short

### Workflow Steps

```
Pipeline Skill Execution Complete
         │
         ▼
┌────────────────────────────────┐
│ Step 1: Meta-Cognition Review  │
│ • Process adherence            │
│ • Expected vs actual gaps      │
│ • Quality observations         │
└────────┬───────────────────────┘
         ▼
┌────────────────────────────────┐
│ Step 2: claude-code-guide      │
│         Research               │
│ • Native CC CLI features       │
│ • Opus 4.6 characteristics     │
│ • Layer 1 boundary only        │
└────────┬───────────────────────┘
         ▼
┌────────────────────────────────┐
│ Step 3: AD-15 Filter           │
│ • Cat A (Hook) → 8→3 violation?│
│   → REJECT                     │
│ • Cat B (NL) → SKILL.md change │
│   → ACCEPT                     │
│ • Cat C (Layer 2) → DEFER      │
└────────┬───────────────────────┘
         ▼
┌────────────────────────────────┐
│ Step 4: Record & Decide        │
│ • Good findings → MEMORY.md    │
│ • This tracker → update        │
│ • NL-only changes permitted    │
└────────────────────────────────┘
```

### Principles

| # | Principle | Rationale |
|---|-----------|-----------|
| P-1 | Always claude-code-guide grounded | Native Capabilities perspective, not intuition |
| P-2 | Layer 1 boundary inviolable | Never propose Layer 2 solutions |
| P-3 | No new hooks (AD-15: 8→3) | Category A additions rejected |
| P-4 | NL-only (Category B) changes | SKILL.md, agent .md, CLAUDE.md — never hooks |
| P-5 | Narrow scope per skill | Only review the skill just executed |
| P-6 | Evidence-based findings | Each improvement must cite native capability source |

---

## 2. Cumulative Results

### Summary Table

| Sprint | Skill | Phase | Source | Findings | Accepted | Rejected | Deferred |
|--------|-------|-------|--------|----------|----------|----------|----------|
| SKL-006 | /agent-teams-write-plan | P4 | rsil-review | 4 | 2 | 1 | 1 |
| SKL-006 | /plan-validation-pipeline | P5 | rsil-review | 4 | 2 | 1 | 1 |
| SKL-006 | /agent-teams-execution-plan | P6 | rsil-review | 7 | 7 | 0 | 0 |
| SKL-006 | /delivery-pipeline | P9 | rsil-review | 9 | 8 | 0 | 1 |
| COW-iter1 | COW pipeline iteration | run | rsil-global | 4 | 4 | 0 | 0 |
| INFRA-v7 | /brainstorming-pipeline | P0-3 | rsil-review S-1 | 8 | 8 | 0 | 0 |
| INFRA-v7 | /agent-teams-write-plan + /plan-validation-pipeline | P4+P5 | rsil-review S-2 | 10+5 | 15 | 0 | 0 |
| INFRA-v7 | /permanent-tasks | — | rsil-review S-3 | 7+4 | 10 | 0 | 1 |
| INFRA-v7 | /agent-teams-execution-plan | P6 | rsil-review S-4 | 6+4 | 10 | 0 | 0 |
| INFRA-v7 | CLAUDE.md | — | rsil-review S-6 | 9 | 9 | 0 | 0 |
| INFRA-v7 | write-plan + plan-validation + protocol + hooks | P4+P5+X | rsil-review S-7 | 7+13 | 20 | 0 | 0 |
| **Total** | | | | **92** | **86** | **2** | **4** |

### Acceptance Rate: 93% (86/92)
### Rejection Reason: AD-15 Hook violation or API-level only (P4/P5 only)

---

## 3. Detailed Findings

### 3.1 /agent-teams-write-plan (Phase 4) — 2026-02-08

**Context:** architect-1 skipped understanding verification, went straight to plan generation. Plan quality was high but process was violated.

| ID | Finding | Category | AD-15 | Status |
|----|---------|----------|-------|--------|
| P4-R1 | Directive needs explicit Understanding Checkpoint (Step 1: explain → Wait → Step 2: write) | B (NL) | ✅ | ACCEPTED |
| P4-R2 | Gate evaluation should verify per-criterion with specific evidence, not single-pass | B (NL) | ✅ | ACCEPTED |
| P4-R3 | SubagentStop hook for L1/L2 verification | A (Hook) | ❌ 8→3 violation | REJECTED |
| P4-R4 | Skill preload with templates | — | — | DEFERRED (H-2) |

**claude-code-guide sources:** Sub-agents docs (permissionMode, disallowedTools), Hooks Guide (Stop/SubagentStop events), Best Practices (directive structure)

**Key insight:** The most effective native mechanism for understanding verification is explicit Step 1/Step 2 structure in the directive prompt — zero overhead, aligns with natural agent workflow.

### 3.2 /plan-validation-pipeline (Phase 5) — 2026-02-08

**Context:** devils-advocate produced high-quality CONDITIONAL_PASS with 18 findings. MCP tool (tavily/context7) actual usage was unverifiable by Lead.

| ID | Finding | Category | AD-15 | Status |
|----|---------|----------|-------|--------|
| P5-R1 | L2 output must include "Evidence Sources" section listing MCP tool usage with citations | B (NL) | ✅ | ACCEPTED |
| P5-R2 | CRITICAL findings trigger Lead→teammate re-verification message (multi-turn) | B (NL) | ✅ | ACCEPTED |
| P5-R3 | Structured Output via strict tool schema for L1 validation | API-level | ❌ Not CC CLI | REJECTED |
| P5-R4 | Adaptive thinking effort parameter per agent | API-level | ❌ H-6 equivalent | DEFERRED |

**claude-code-guide sources:** Hooks Guide (no per-subagent tool logging), Structured Outputs docs (API-level only), Extended Thinking docs (adaptive mode)

**Key insight:** No native per-subagent tool usage logging exists. The NL alternative: require evidence citations in L2 output. This shifts verification from "did you use the tool?" to "show me what the tool found."

### 3.3 /agent-teams-execution-plan (Phase 6) — 2026-02-08

**Context:** First execution of `/rsil-review` skill (Meta-Cognition framework). 8 Lenses applied, 9 Research Questions generated, 6 Integration Axes audited. All 7 findings accepted — 100% acceptance rate for this target (no AD-15 violations).

| ID | Finding | Category | AD-15 | Status |
|----|---------|----------|-------|--------|
| P6-R1 | CLAUDE.md "Task #1" hardcoded → parametric PT reference | B (NL) | ✅ | ACCEPTED + APPLIED |
| P6-R2 | "2 probing questions" → "1-3" to align with CLAUDE.md §6 | B (NL) | ✅ | ACCEPTED + APPLIED |
| P6-R3 | agent-common-protocol directive description → 3-layer alignment | B (NL) | ✅ | ACCEPTED + APPLIED |
| P6-R4 | implementer.md Task tool availability clarification | B (NL) | ✅ | ACCEPTED + APPLIED |
| P6-R5 | L2 template: add self-test output section for G6-3 evidence | B (NL) | ✅ | ACCEPTED + APPLIED |
| P6-R6 | Spec-reviewer prompt: mandate file:line evidence for PASS | B (NL) | ✅ | ACCEPTED + APPLIED |
| P6-R7 | [STATUS] protocol markers → NL status format (NLP v6.0) | B (NL) | ✅ | ACCEPTED + APPLIED |

**RSIL skill sources:** claude-code-guide (Agent Teams docs, hooks guide, sub-agents), Explore (6-axis integration audit)

**Key insights:**
- Integration audit (Axis ②) revealed PT task scope conflict already mitigated by inline embedding — documentation needed alignment, not code fix
- All 7 findings were NL-only (Category B) — execution-plan has no Layer 2 dependencies
- [STATUS] markers were the only NLP v6.0 violations remaining in the skill

### 3.4 /delivery-pipeline (Phase 9) — 2026-02-08

**Context:** Lead-only terminal skill (422 lines). RSIL applied for general refinement/improvement. 8/8 Lenses applied, 8 RQs generated, 5 Integration Axes audited. 8 of 9 findings accepted — 1 deferred (compact recovery state marker, Layer 2).

| ID | Finding | Category | AD-15 | Status |
|----|---------|----------|-------|--------|
| P9-R1 | Op-4 rejection cascade logic (skip Op-5, proceed Op-6/7) | B (NL) | ✅ | ACCEPTED + APPLIED |
| P9-R2 | V-1 PT vs GC reconciliation rule (PT takes precedence) | B (NL) | ✅ | ACCEPTED + APPLIED |
| P9-R3 | Phase 9 Delivery Record section in ARCHIVE.md template | B (NL) | ✅ | ACCEPTED + APPLIED |
| P9-R4 | MEMORY/ARCHIVE consistency note on Op-4 rejection | B (NL) | ✅ | ACCEPTED + APPLIED |
| P9-R5 | Multi-session discovery — explicit PT session-id extraction | B (NL) | ✅ | ACCEPTED + APPLIED |
| P9-R6 | Cleanup preserve/delete classification with L2 cross-check | B (NL) | ✅ | ACCEPTED + APPLIED |
| P9-R7 | Compact recovery state marker between Op-2 and Op-4 | C (L2) | — | DEFERRED |
| P9-R8 | "Primary session" definition — gate record timestamp rule | B (NL) | ✅ | ACCEPTED + APPLIED |
| P9-B1 | Tilde→absolute path notation (line 162) | B (NL) | ✅ | ACCEPTED + APPLIED |

**RSIL sources:** claude-code-guide (skill features, recovery docs), Explore (5-axis integration audit)

**Key insights:**
- Integration Score 4.8/5 — delivery-pipeline has strong cross-file consistency (only 1 cosmetic path issue)
- L1 Optimality Score 8/10 — only F-7 (compact recovery) requires Layer 2 for a clean solution
- Lead-only skills are simpler to review (no teammate contract verification needed)
- The "rejection cascade" pattern (F-1) may apply to other skills with user confirmation gates

### 3.5 Global Findings (/rsil-global)

### First /rsil-global run — 2026-02-09 (COW pipeline iteration 1)

| ID | Finding | Category | Severity | Tier | Lens | Status |
|----|---------|----------|----------|------|------|--------|
| G-25 | PT-v1 Phase Status stale — Stage 3-6 shows PENDING, actual = TESTED | B | FIX | 1 | L1, L5 | ACCEPTED — PT updated to v2 |
| G-26 | Stage 5 TikZ escape bug (BUG-COW-1) not recorded in PT Constraints | B | FIX | 1 | L3 | ACCEPTED — added to PT Known Bugs |
| G-27 | MEMORY.md "Next steps" lists completed item as pending | B | WARN | 1 | L3 | ACCEPTED — MEMORY updated |
| G-28 | cow/ changes 24 files uncommitted — interruption risk | B | WARN | 1 | L7 | ACCEPTED — noted for user |

---

## 4. Cross-Cutting Patterns Discovered

### Pattern 1: "Evidence Sources" in All L2 Outputs

**Origin:** P5-R1
**Scope:** Applicable to ALL teammate types, not just devils-advocate
**Principle:** Require every teammate's L2-summary.md to include an "Evidence Sources" section listing MCP tools used and key findings. This is the NL alternative to tool usage logging.
**Implementation:** Add to agent-common-protocol.md or each agent .md Constraints section.

### Pattern 2: Explicit Checkpoint Steps in Directives

**Origin:** P4-R1
**Scope:** Applicable to all skills that spawn teammates requiring understanding verification
**Principle:** Structure directives as "Step 1: Read + Explain → Wait for Lead → Step 2: Execute" rather than "Read → Execute." The explicit wait forces the verification handshake.
**Implementation:** Update directive templates in each pipeline SKILL.md.

### Pattern 3: Cross-File Integration Audit as Standard RSIL Step

**Origin:** P6 (full RSIL execution)
**Scope:** Applicable to ALL pipeline skill reviews
**Principle:** Every skill references other .claude/ files. Bidirectional consistency audit catches stale references, scope conflicts, and documentation drift that single-file review misses.
**Implementation:** RSIL skill's Integration Audit Methodology (6-axis pattern derived from file references).

### Pattern 4: Rejection Cascade Specification in User-Confirmed Operations

**Origin:** P9-R1
**Scope:** Applicable to all skills with multiple sequential user confirmation points
**Principle:** When a later confirmation (e.g., Op-4 commit) is rejected, explicitly document which earlier operations' artifacts are preserved, which downstream operations are skipped, and what cleanup is needed.
**Implementation:** Add cascade logic to rejection handlers in skills with 2+ user confirmation gates.

---

## 5. Improvement Backlog (Not Yet Applied)

These accepted findings have NOT been implemented yet — they are design improvements for future SKILL.md updates.

| ID | Target Skill | Change Type | Effort | Status |
|----|-------------|-------------|--------|--------|
| P4-R1 | /agent-teams-write-plan | Directive template update | ~10 lines | APPLIED (S-2) |
| P4-R2 | /agent-teams-write-plan | Gate section guidance | ~5 lines | APPLIED (S-2) |
| P5-R1 | /plan-validation-pipeline | Directive output requirements | ~5 lines | APPLIED (S-2) |
| P5-R2 | /plan-validation-pipeline | Gate section multi-turn logic | ~10 lines | APPLIED (S-2) |

**All backlog items applied in S-2 retroactive audit (2026-02-10).**

---

## 3.6 Retroactive Audit (2026-02-10)

### S-1: R1 brainstorming-pipeline (509L → 564L)

| # | Finding | Category | Severity | Lens | Status |
|---|---------|----------|----------|------|--------|
| RA-R1-1 | Phase 0 missing from CLAUDE.md §2 Phase Pipeline table | B | FIX | L8 | APPLIED |
| RA-R1-2 | Self-description "Phase 1-3" vs actual "Phase 0-3" (frontmatter + announce) | B | FIX | L8 | APPLIED |
| RA-R1-3 | PT disambiguation: auto-match $ARGUMENTS vs PT User Intent, AskUser on mismatch only | B | FIX | L5 | APPLIED |
| RA-R1-4 | Phase 1 auto-compact recovery gap: qa-checkpoint.md after 1.3 | B | FIX | L7 | APPLIED |
| RA-R1-5 | Phase 1 intermediate state not persisted (category tracking) | B | WARN | L7 | ACCEPTED |
| RA-R1-6 | GC-v2/v3 incremental schema formalized (explicit section templates) | B | FIX | L5 | APPLIED |
| RA-R1-7 | Gate criteria lack per-criterion rationale fields | B | WARN | L2 | ACCEPTED |
| RA-R1-8 | Phase 1 reasoning artifact not preserved beyond Scope Statement | B | WARN | L3 | ACCEPTED |

**Totals:** 8 findings (5 APPLIED, 3 ACCEPTED-as-WARN), 0 BREAK, 0 REJECT, 0 DEFER
**L1 Optimality:** 7.5/10 → ~8.5/10 (after applying 5 FIX items)
**Integration Score:** 4/5 axes → 5/5 (after fixing Axis 1)
**Files Modified:** CLAUDE.md (+1L), brainstorming-pipeline/SKILL.md (+55L)
**Cross-Cutting Pattern Candidate:** P-5 "Phase 0 documentation gap" — Phase 0 exists in all 7 pipeline skills but was absent from CLAUDE.md §2.

### 3.7 /agent-teams-write-plan + /plan-validation-pipeline (S-2) — 2026-02-10

**Context:** Dual-skill retroactive audit as part of INFRA v7.0 Integration Sprint WS-B. Included 4 backlog items (P4-R1/R2, P5-R1/R2) plus 6 new findings + 2 architecture-derived RQs. Integration audit verified 5 axes.

**Layer Boundary Findings (10, all Category B):**

| ID | Finding | Lens | Severity | Target | Status |
|----|---------|------|----------|--------|--------|
| RA-S2-R1 | GC version schema implicit — add explicit preservation note | L1 | HIGH | both | APPLIED |
| RA-S2-R2 | Gate-record lacks per-criterion evidence requirement (P4-R2) | L2 | MED | write-plan | APPLIED |
| RA-S2-R3 | L2 output lacks Evidence Sources section (P5-R1) | L3 | MED | both | APPLIED |
| RA-S2-R4 | G4-2 vs V-3 structural/semantic mismatch — align V-3 with 10-section | L5 | HIGH | validation | APPLIED |
| RA-S2-R5 | PT scope disambiguation missing from Phase 0 (RA-R1-3) | L5 | MED | both | APPLIED |
| RA-S2-R6 | CRITICAL verdict lacks multi-turn re-verification (P5-R2) | L4 | MED | validation | APPLIED |
| RA-S2-R7 | Understanding checkpoint not explicit in directive template (P4-R1) | L1 | MED | write-plan | APPLIED |
| RA-S2-R8 | Phase 0 not in frontmatter descriptions (P-5 pattern) | L8 | LOW | both | APPLIED |
| RA-S2-R9 | RTD DP naming inconsistent — standardize DP-{N} format | L8 | LOW | both | APPLIED |
| RA-S2-R10 | v6.0 task-api compatibility undocumented | L5 | MED | both | APPLIED |

**Integration Audit (5 axes):**

| Axis | Files | Status | Finding |
|------|-------|--------|---------|
| 1 | write-plan ↔ brainstorming-pipeline (GC-v3) | PASS | Consistent after S-1 fixes |
| 2 | write-plan ↔ validation (GC-v4 contract) | WARN | V-3 semantic vs structural → fixed (RA-S2-R4) |
| 3 | write-plan ↔ CLAUDE.md §6 (verification) | PASS | Aligned |
| 4 | validation ↔ devils-advocate.md (exemption) | WARN | Evidence Sources gap → fixed (RA-S2-R3) |
| 5 | Both ↔ tracker backlog (P4-R1/R2, P5-R1/R2) | BREAK→FIXED | Backlog status contradicted actual → §5 updated |

**Totals:** 15 findings (10 layer + 5 integration), all APPLIED, 0 REJECT, 0 DEFER
**L1 Optimality:** 6.5/10 → ~8/10 (after applying all FIX items)
**Integration Score:** 3/5 → 5/5 (after BREAK fix + 2 WARN fixes)
**Files Modified:** write-plan/SKILL.md (+8L), validation/SKILL.md (+7L), tracker §5 (backlog status)
**Backlog cleared:** P4-R1, P4-R2, P5-R1, P5-R2 all APPLIED in this review

### 3.8 /permanent-tasks (S-3) — 2026-02-10

**Context:** Standalone skill (265L) for PERMANENT Task management. Reviewed for RA-R1-3 cascade, RTD naming, v6.0 compat. Integration audit verified 4 axes.

**Layer Boundary Findings (7, all Category B):**

| ID | Finding | Lens | Severity | Status |
|----|---------|------|----------|--------|
| RA-S3-R1 | DELIVERED transition contract note | L1 | MED | ACCEPTED-as-is |
| RA-S3-R2 | Notification threshold adequate | L4 | MED | ACCEPTED-as-is |
| RA-S3-R3 | PT disambiguation missing (RA-R1-3) | L5 | HIGH | APPLIED |
| RA-S3-R4 | v6.0 task-api reference | L5 | LOW | APPLIED |
| RA-S3-R5 | Compaction recovery idempotency | L7 | MED | APPLIED |
| RA-S3-R6 | "Task #1" hardcoded (P6-R1) | L8 | LOW | APPLIED |
| RA-S3-R7 | RTD DP naming (RA-S2-R9) | L8 | LOW | APPLIED |

**Integration Audit (4 axes):**

| Axis | Files | Status | Finding |
|------|-------|--------|---------|
| 1 | permanent-tasks ↔ brainstorming Phase 0 | PASS | All consistent |
| 2 | permanent-tasks ↔ CLAUDE.md | PASS | 1 WARN (notification asymmetry) |
| 3 | permanent-tasks ↔ task-api-guideline v6.0 | FIX | Missing blockedBy/blocks → APPLIED |
| 4 | permanent-tasks ↔ agent-common-protocol | PASS | 1 WARN (Phase Status mention) |

**Totals:** 11 findings (7 layer + 4 integration), 5 APPLIED, 2 ACCEPTED-as-is, 1 FIX APPLIED, 2 WARN, 1 ACCEPTED-as-is
**L1 Optimality:** 7/10 → ~8.5/10
**Integration Score:** 3/4 → 4/4
**Files Modified:** permanent-tasks/SKILL.md (+8L, 265→273L)

### 3.9 /agent-teams-execution-plan (S-4) — 2026-02-10

**Context:** Phase 6 orchestrator skill (597L). CRITICAL focus on §3 reference check (V-3 semantic vs structural), GC schema chain preservation, Phase 0 cascade. Integration audit verified 4 axes.

**Layer Boundary Findings (6, all Category B):**

| ID | Finding | Lens | Severity | Status |
|----|---------|------|----------|--------|
| RA-EP-1 | V-3 semantic validation — replace §-number references with semantic descriptions | L5 | HIGH | APPLIED |
| RA-EP-2 | Phase 0 PT disambiguation missing (RA-R1-3 cascade) | L5 | MED | APPLIED |
| RA-EP-3 | Phase 0 not in frontmatter description (P-5 pattern) | L8 | LOW | APPLIED |
| RA-EP-4 | RTD DP naming inconsistent — standardize DP-{N} (RA-S2-R9 cascade) | L8 | LOW | APPLIED |
| RA-EP-5 | GC-v4→v5 update lacks explicit preservation instruction | L1 | MED | APPLIED |
| RA-EP-6 | Implementer completion report missing Evidence Sources section (P-1 cascade) | L3 | MED | APPLIED |

**Integration Audit (4 axes):**

| Axis | Files | Status | Finding |
|------|-------|--------|---------|
| 1 | execution-plan ↔ write-plan (GC-v4 contract) | PASS | Input validation aligned |
| 2 | execution-plan ↔ CLAUDE.md §6 (verification protocol) | WARN | Minor wording variation, functionally aligned |
| 3 | execution-plan ↔ implementer.md (self-review source) | FIX | "implementer.md checklist" ambiguous → clarified "per §6.4 flow" — APPLIED |
| 4 | execution-plan ↔ task-api-guideline v6.0 | PASS | §3 reference verified safe |

**Totals:** 10 findings (6 layer + 4 integration), 7 APPLIED (6 layer + 1 axis FIX), 3 PASS/WARN (noted), 0 REJECT, 0 DEFER
**L1 Optimality:** 6.5/10 → ~8/10 (after applying all FIX items)
**Integration Score:** 3.5/4 → 4/4
**Files Modified:** execution-plan/SKILL.md (+7L, 597→604L)
**Key insight:** V-3 semantic validation (EP-1) was the highest-value finding — structural §-number references are fragile against plan template evolution; semantic descriptions are resilient.

### 3.10 CLAUDE.md (S-6) — 2026-02-10

**Context:** RSIL Cycle 6 — CLAUDE.md v7.0 optimization review. 6 lenses, 9 RQs, 4 integration axes. Parallel with cosmetic residual fixes (3 items from Cycle 5).

| ID | Finding | Lens | Severity | Status |
|----|---------|------|----------|--------|
| F-S6-01 | Phase category "5, 6+" → "5, 6" (misleading suffix) | L8 | FIX | APPLIED |
| F-S6-02 | §6 Agent Selection Flow — 8-step decision pattern documented | L1 | FIX | APPLIED |
| F-S6-03 | Phase overlap note missing (P2b∥P2, P2d∥P3) | L1 | FIX | APPLIED |
| F-S6-04 | Spawn Quick Reference section needed in agent-catalog.md | L5 | FIX | APPLIED |
| F-S6-05 | §6 "Directive Templates" reference name → "Spawn Quick Reference" | L8 | FIX | APPLIED (S-7) |
| F-S6-06 | O-4 CLAUDE.md structural optimization (removal of duplicate blocks) | L5 | FIX | APPLIED |
| F-S6-07 | O-2 Decision flow visualization for Lead | L1 | FIX | APPLIED |
| F-S6-08 | Agent catalog category templates (10 categories) | L5 | FIX | APPLIED |
| F-S6-09 | DA verification exemption not in CLAUDE.md | L4 | FIX | APPLIED (S-7) |

**Totals:** 9 findings, 9 APPLIED, 0 REJECT, 0 DEFER
**Files Modified:** CLAUDE.md, agent-catalog.md (+68L)

### 3.11 write-plan + plan-validation + protocol + hooks (S-7) — 2026-02-11

**Context:** RSIL Cycle 7 — Multi-track RSIL with 4 parallel agents. 7-axis integration audit (write-plan + plan-validation ↔ CLAUDE.md + catalog + protocol) and S-7 protocol+hooks audit (5 files, 8 lenses).

**Integration Audit (7 axes, 7 findings):**

| ID | Axis | Severity | Files | Status |
|----|------|----------|-------|--------|
| IA-1 | 2 | FIX | plan-validation ↔ CLAUDE.md | APPLIED (DA exemption) |
| IA-2 | 4 | FIX | plan-validation ↔ DA agent def | APPLIED (Write tool + read-only note) |
| IA-3 | 7 | FIX | CLAUDE.md §6 ↔ agent-catalog | APPLIED (naming mismatch) |
| IA-4 | 3 | WARN | write-plan ↔ protocol | APPLIED (TEAM-MEMORY instruction) |
| IA-5 | 6 | WARN | write-plan ↔ catalog | APPLIED (tool list note) |
| IA-6 | 6 | WARN | plan-validation ↔ catalog | NOTED (amplifies IA-2) |
| IA-7 | 1 | INFO | write-plan ↔ catalog | NOTED (architect vs plan-writer) |

**Protocol + Hooks Audit (5 files, 13 findings):**

| ID | Section | Severity | Target | Status |
|----|---------|----------|--------|--------|
| S7-A1 | Protocol | FIX | agent-common-protocol.md:24-29 | APPLYING (TaskGet fallback) |
| S7-A2 | Protocol | WARN | agent-common-protocol.md:106-110 | ACCEPTED (agent memory sparse) |
| S7-A3 | Protocol | WARN | agent-common-protocol.md (global) | ACCEPTED (edge cases) |
| S7-A4 | Protocol | INFO | agent-common-protocol.md:55-59 | NOTED (condition overlap) |
| S7-B1 | Hooks | FIX | on-session-compact.sh:49 | APPLYING (JSON escaping) |
| S7-B2 | Hooks | WARN | on-pre-compact.sh:42-62 | ACCEPTED (hookOutput missing) |
| S7-B3 | Hooks | WARN | CLAUDE.md:201-214 | ACCEPTED (PreCompact mention) |
| S7-B4 | Hooks | INFO | on-subagent-start.sh:53-65 | NOTED (GC legacy) |
| S7-B5 | Hooks | INFO | on-subagent-start.sh:12-14 | NOTED (jq optimization) |
| S7-B6 | Hooks | INFO | on-rtd-post-tool.sh:124-128 | NOTED (SendMessage handling) |
| S7-C1 | Optimization | FIX | agent-common-protocol.md (missing) | APPLYING (Evidence Sources) |
| S7-C2 | Optimization | WARN | 22 agent .md files | ACCEPTED (RTD line duplication) |
| S7-C3 | Optimization | INFO | Multiple files | NOTED (PT redundancy intentional) |

**Totals:** 20 findings (7 integration + 13 protocol), 6 FIX (applying), 7 WARN (accepted), 7 INFO (noted)
**Integration Score:** 4/7 axes passing → 7/7 after fixes
**Files Modified:** CLAUDE.md (+2L), plan-validation/SKILL.md (~2L), write-plan/SKILL.md (+2L), agent-common-protocol.md (+3L), on-session-compact.sh (+1L)

---

## 6. Rejected & Deferred Items

### Rejected (AD-15 Violation)

| ID | Proposal | Rejection Reason |
|----|----------|-----------------|
| P4-R3 | SubagentStop hook for L1/L2 | Adds new hook, violates 8→3 constraint |
| P5-R3 | Strict tool schema for output | API-level feature, not CC CLI configurable |

### Deferred (Separate Work)

| ID | Proposal | Defer Reason | Related |
|----|----------|-------------|---------|
| P4-R4 | Skill preload templates | Content creation per agent, low ROI this sprint | H-2 |
| P5-R4 | Effort parameter per agent | API-level only, not CC CLI | H-6 |
| P9-R7 | Compact recovery state marker (Op-2→Op-4 gap) | Layer 2: requires persistent state across compaction | — |

---

## 6.5 Finding Schema (Extended)

Findings from /rsil-global use extended YAML schema fields:

```yaml
- id: G-{N}                    # Global finding ID (monotonically increasing)
  source_skill: rsil-global    # or rsil-review
  finding_type: global         # or narrow
  finding: "{description}"
  category: "B"                # A (REJECT) / B (ACCEPT) / C (DEFER)
  severity: "FIX"              # BREAK / FIX / WARN
  detection_tier: 1            # 0-3 (which tier detected it)
  cross_refs: []               # Related finding IDs from other skill
  decomposed_to: []            # Narrow finding IDs if decomposed
  promoted_to: null            # Global ID if promoted from narrow
  status: "ACCEPTED"           # ACCEPTED / REJECTED / DEFERRED / APPLIED
```

Existing narrow findings (P4-R{N}, P5-R{N}, etc.) retain their current format.
New narrow findings may optionally use the extended schema.

---

## 7. Future Brainstorming Topic Notes

This document is a candidate for `/brainstorming-pipeline` topic execution. Potential scope:

- **Systematize Narrow RSIL** as a formal post-execution step in all pipeline skills
- **Apply backlog** (§5) to existing SKILL.md files
- **Expand pattern discovery** across more pipeline executions
- **Design NL-based quality gates** that replace mechanical enforcement without hooks
- **Investigate** whether Narrow RSIL findings converge (diminishing returns) or diverge (new patterns each time)

**Pre-requisites for brainstorming:**
- Complete SKL-006 sprint (more data points from Phase 6, 7-8)
- Analyze whether accepted findings actually improve execution in later phases
