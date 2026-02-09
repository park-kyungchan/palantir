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
| **Total** | | | | **28** | **23** | **2** | **3** |

### Acceptance Rate: 82% (23/28)
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

| ID | Target Skill | Change Type | Effort |
|----|-------------|-------------|--------|
| P4-R1 | /agent-teams-write-plan | Directive template update | ~10 lines |
| P4-R2 | /agent-teams-write-plan | Gate section guidance | ~5 lines |
| P5-R1 | /plan-validation-pipeline | Directive output requirements | ~5 lines |
| P5-R2 | /plan-validation-pipeline | Gate section multi-turn logic | ~10 lines |

**Total estimated effort:** ~30 lines across 2 SKILL.md files

**Note:** P6-R1~R7 and P9-R1~R8+B1 were ALL applied immediately during their RSIL sessions (not backlogged).

**When to apply remaining backlog:** After SKL-006 sprint completes, or as part of a dedicated skill improvement sprint.

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
