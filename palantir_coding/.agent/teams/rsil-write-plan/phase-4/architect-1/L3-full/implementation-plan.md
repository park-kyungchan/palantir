# RSIL System — Implementation Plan

> **For Lead:** This plan is designed for Agent Teams native execution.
> Read this file, then orchestrate using CLAUDE.md Phase Pipeline protocol.

**Goal:** Build the INFRA Meta-Cognition self-improvement system: /rsil-global (NEW, auto-invoked)
+ /rsil-review (REFINED, 5 deltas) with shared agent memory, unified tracker, and CLAUDE.md integration.

**Architecture:** `.agent/teams/rsil-system/phase-3/architect-1/L3-full/architecture-design.md` (1011L, approved)

**GC-v3:** `.agent/teams/rsil-system/global-context.md` (95L)

**Pipeline:** Full Phase 6 — 2 implementers in parallel, zero file overlap.

---

## 1. Orchestration Overview (Lead Instructions)

### Pipeline Structure

```
Phase 4: Detailed Design   — THIS PLAN (YOU ARE HERE)
Phase 5: Plan Validation    — devils-advocate reviews this plan
Phase 6: Implementation     — 2 implementers execute in parallel
Phase 7: Testing            — Verification of cross-file consistency
Phase 8: Integration        — Shared Foundation character-level diff
Phase 9: Delivery            — Commit and cleanup
```

### Teammate Allocation

| Role | Count | Agent Type | File Ownership | Phase |
|------|-------|-----------|----------------|-------|
| implementer-1 | 1 | `implementer` | rsil-global SKILL.md (NEW) | Phase 6 |
| implementer-2 | 1 | `implementer` | rsil-review SKILL.md + CLAUDE.md + agent memory + tracker | Phase 6 |

**WHY two implementers:** /rsil-global is ~400-500L of new content with zero dependency on the
other 4 files. Pure parallelism — the only shared element (Foundation text) is provided verbatim
in §5 for both implementers. Tasks B+C share an implementer because /rsil-review Delta 3 (agent
memory integration) references the agent memory schema that implementer-2 also creates.

### Execution Sequence

```
Lead:   TeamCreate("rsil-execution")
Lead:   TaskCreate × 4 (Task A, B, C, D — see §4)
Lead:   Spawn implementer-1 (Task A) + implementer-2 (Tasks B, C) in parallel
Lead:   Send [DIRECTIVE] with PT-v{N} content + §5 specs
        ┌──────────────────────────────────────────────────────┐
        │ Understanding Verification (both implementers)        │
        │                                                        │
        │ Implementer: Explains understanding of task scope      │
        │ Lead: 1-3 probing questions (grounded in Impact Map)  │
        │ Implementer: Defends with evidence                     │
        │ Lead: Approves implementation plan                     │
        └──────────────────────────────────────────────────────┘
        implementer-1: Task A (rsil-global SKILL.md)     ─┐
        implementer-2: Task B (rsil-review deltas) → C   ─┤ parallel
                                                            │
        Both: Write L1/L2/L3                               │
        Both: Report COMPLETE                               ┘
Lead:   Task D: Cross-file integration validation
Lead:   Gate 6 Review
Lead:   Commit → Phase 9 (Delivery)
```

---

## 2. Architecture Summary

### Component Map (from GC-v3)

| ID | Component | Files | Status |
|----|-----------|-------|--------|
| C-1 | /rsil-global Complete Flow (G-0→G-4) | .claude/skills/rsil-global/SKILL.md (NEW) | Spec ready |
| C-2 | /rsil-review Refinement (5 deltas) | .claude/skills/rsil-review/SKILL.md (MODIFY) | Spec ready |
| C-3 | Shared Foundation | Embedded in C-1 and C-2 (~85L each) | Spec ready |
| C-4 | CLAUDE.md Integration | .claude/CLAUDE.md (MODIFY) | Spec ready |
| C-5 | Agent Memory Schema | ~/.claude/agent-memory/rsil/MEMORY.md (NEW) | Spec ready |
| C-6 | Tracker Migration | docs/plans/2026-02-08-narrow-rsil-tracker.md (MODIFY) | Spec ready |

### Interface Contracts

| Interface | From | To | Contract |
|-----------|------|----|----------|
| Shared Foundation | C-3 | C-1, C-2 | 8 Lenses + AD-15 + Boundary Test = character-identical text |
| Agent Memory R/W | C-5 | C-1, C-2 | Read: dynamic context head -50; Write: G-4/R-4 Read-Merge-Write |
| Tracker Namespacing | C-6 | C-1, C-2 | G-{N} (global) vs P-R{N} (narrow), cross_refs/promoted_to/decomposed_to |
| NL Discipline | C-4 | C-1 | CLAUDE.md §2 instruction triggers Lead to invoke /rsil-global |
| Agent Memory Section Headers | C-5 | C-1, C-2 | §1 Configuration, §2 Lens Performance, §3 Cross-Cutting Patterns, §4 Lens Evolution |

### Key Decisions

| # | Decision | Rationale | Phase |
|---|----------|-----------|-------|
| D-1 | /rsil-global = Lead NL auto-invoke | AD-15 compatible, no hook needed | P1 |
| D-2 | Three-Tier + parallel agent discovery | Context efficiency + INFRA boundary discovery | P1 |
| D-3 | Immediate Cat B proposal (not auto-apply) | User present, approval fast | P1 |
| D-4 | Shared Foundation architecture | Both skills share Lenses/AD-15 but independent | P1 |
| D-5 | /rsil-review also refined | Feasibility research improvements applicable | P1 |
| AD-6 | Findings-only output (no auto-apply) | Safety > speed for INFRA changes | P3 |
| AD-7 | Three-Tier per work type (adaptive A/B/C) | Uniform strategy wastes tokens for Type B/C | P3 |
| AD-8 | BREAK escalation via AskUserQuestion | User present in auto-invoke context | P3 |
| AD-9 | Tracker section isolation + ID namespacing | G-{N} vs P-R{N}; sequential consistency | P3 |
| AD-10 | Shared Foundation = embedded copy | 85L stable; no external dependency | P3 |
| AD-11 | Single shared agent memory | Patterns universal; separation fragments learning | P3 |

---

## 3. File Ownership Assignment

| File | Ownership | Operation | Lines |
|------|-----------|-----------|-------|
| `.claude/skills/rsil-global/SKILL.md` | implementer-1 | NEW | ~400-500L |
| `.claude/skills/rsil-review/SKILL.md` | implementer-2 | MODIFY (5 deltas) | 561→~551L |
| `.claude/CLAUDE.md` | implementer-2 | MODIFY (+5L) | 172→~177L |
| `~/.claude/agent-memory/rsil/MEMORY.md` | implementer-2 | NEW | ~86L seed |
| `docs/plans/2026-02-08-narrow-rsil-tracker.md` | implementer-2 | MODIFY (+section) | 254→~280L |

**Zero file overlap.** implementer-1 owns exactly 1 file (NEW). implementer-2 owns 4 files (2 MODIFY, 1 NEW, 1 MODIFY).

---

## 4. Task Decomposition

### Task A: Create /rsil-global SKILL.md

```
subject: "Create /rsil-global SKILL.md — complete auto-invoked INFRA health assessment skill"

description: |
  ## Objective
  Create the complete /rsil-global skill file from scratch. This is a Lead-only
  auto-invoked skill with Three-Tier Observation Window, 8 Meta-Research Lenses,
  AD-15 Filter, and ~2000 token context budget.

  ## Context in Global Pipeline
  - Phase: 6 (Implementation)
  - Upstream: Architecture design (L3, 1011L) — components C-1, C-3
  - Downstream: Task D (cross-file validation)

  ## Detailed Requirements
  See §5 "File Specifications — Task A" in this plan for complete content outline.
  The spec provides: frontmatter, When to Use tree, Dynamic Context shell commands,
  G-0→G-4 phase flow, Shared Foundation (verbatim), error handling, and principles.

  ## File Ownership
  - .claude/skills/rsil-global/SKILL.md (NEW, ~400-500L)

  ## Dependency Chain
  - blockedBy: []
  - blocks: [Task D]

  ## Acceptance Criteria
  AC-0: Read implementation plan §5 spec for this file. Verify plan matches current
        codebase state before writing.
  AC-1: YAML frontmatter with name, description, argument-hint
  AC-2: When to Use decision tree with INVOKE/SKIP criteria
  AC-3: Dynamic Context with 6 shell commands (including head -50 for agent memory)
  AC-4: G-0 classification logic for Type A/B/C with fallback rules
  AC-5: G-1 Tiered Reading with per-type data sources and health indicators
  AC-6: G-2 Discovery (Tier 3 only, Explore agent spawn)
  AC-7: G-3 Classification + Presentation with AD-15 filter and AskUserQuestion for BREAKs
  AC-8: G-4 Record phase with tracker update and agent memory Read-Merge-Write
  AC-9: Shared Foundation sections (Lenses, AD-15, Boundary Test) character-identical
        to /rsil-review (verbatim text provided in §5)
  AC-10: Error handling table covering all edge cases
  AC-11: Principles section (~10-12 items, positive-form)
  AC-12: Total file ~400-500 lines

activeForm: "Creating /rsil-global SKILL.md"
```

### Task B: Apply /rsil-review 5 Deltas + CLAUDE.md Integration

```
subject: "Apply 5 deltas to /rsil-review SKILL.md and add CLAUDE.md NL discipline"

description: |
  ## Objective
  Apply 5 precisely-specified modifications to the existing /rsil-review SKILL.md
  (561L → ~551L, net -10L) and insert 5 lines of NL discipline into CLAUDE.md
  after §2 Phase Pipeline table.

  ## Context in Global Pipeline
  - Phase: 6 (Implementation)
  - Upstream: Architecture design (L3) — components C-2, C-4
  - Downstream: Task D (cross-file validation)

  ## Detailed Requirements
  See §5 "File Specifications — Task B" in this plan for exact old→new text.
  All 5 deltas are independently applicable (no ordering dependency).

  ## File Ownership
  - .claude/skills/rsil-review/SKILL.md (MODIFY, 5 deltas)
  - .claude/CLAUDE.md (MODIFY, +5L after line 33)

  ## Dependency Chain
  - blockedBy: []
  - blocks: [Task D]

  ## Acceptance Criteria
  AC-0: Read implementation plan §5 spec for these files. Read current files.
        Verify plan's old_string matches actual file content before modifying.
  AC-1: Delta 1 (ultrathink): "ultrathink" keyword in intro paragraph (line 9)
  AC-2: Delta 2 (wc -l): `!`wc -l $ARGUMENTS 2>/dev/null`` added after line 51
  AC-3: Delta 3a (memory read): `!`cat ~/.claude/agent-memory/rsil/MEMORY.md ...``
        added after Delta 2 line
  AC-4: Delta 3b (memory write): Agent Memory Update section added after line 483
  AC-5: Delta 4 (principles merge): 25 lines (Key Principles + Never) replaced with
        15-line merged Principles section
  AC-6: Delta 5 (output simplify): Output Format section simplified (~30 → ~25 lines)
  AC-7: CLAUDE.md: 5-line NL discipline inserted after "Every task assignment
        requires understanding verification before work begins." (line 33), before
        "## 3. Roles" (line 35)
  AC-8: /rsil-review total: ~551 lines (±3)
  AC-9: CLAUDE.md total: ~177 lines

activeForm: "Applying rsil-review deltas and CLAUDE.md integration"
```

### Task C: Create Agent Memory + Migrate Tracker

```
subject: "Create rsil agent memory seed file and add Global Findings section to tracker"

description: |
  ## Objective
  Create the shared agent memory file with seed data derived from the current tracker
  (24 findings, 79% acceptance). Add a "Global Findings" section to the tracker with
  extended schema fields and source_skill column in Summary Table.

  ## Context in Global Pipeline
  - Phase: 6 (Implementation)
  - Upstream: Architecture design (L3) — components C-5, C-6
  - Downstream: Task D (cross-file validation)

  ## Detailed Requirements
  See §5 "File Specifications — Task C" in this plan for exact content.

  ## File Ownership
  - ~/.claude/agent-memory/rsil/MEMORY.md (NEW, ~86L seed)
  - docs/plans/2026-02-08-narrow-rsil-tracker.md (MODIFY, +section)

  ## Dependency Chain
  - blockedBy: []
  - blocks: [Task D]

  ## Acceptance Criteria
  AC-0: Read implementation plan §5 spec for these files. Read current tracker.
        Verify plan's existing content descriptions match actual file.
  AC-1: Agent memory file created at ~/.claude/agent-memory/rsil/MEMORY.md
  AC-2: 4 sections: §1 Configuration, §2 Lens Performance, §3 Cross-Cutting Patterns,
        §4 Lens Evolution — section headers EXACTLY as specified
  AC-3: Seed data derived from tracker §2 Summary Table (24 findings, 79% acceptance)
  AC-4: Lens Performance table populated from tracker finding distribution
  AC-5: 4 cross-cutting patterns (P-1 through P-4) from tracker §4
  AC-6: Tracker §2 Summary Table gains "Source" column (all existing = "rsil-review")
  AC-7: Tracker §3 gains "### 3.5 Global Findings" section (empty, ready for G-{N})
  AC-8: Tracker §6 gains extended schema fields (source_skill, finding_type,
        detection_tier, cross_refs, decomposed_to)
  AC-9: Existing tracker content (§1-§6) unchanged except additions
  AC-10: Backward compatible — existing P-R{N} findings untouched

activeForm: "Creating agent memory and migrating tracker"
```

### Task D: Cross-File Integration Validation

```
subject: "Validate cross-file consistency across all 5 modified/created files"

description: |
  ## Objective
  Verify that all interface contracts hold across the 5 files. This is a Lead-only
  verification task — no implementer needed.

  ## Cross-File Checks
  1. Shared Foundation: Lenses table, AD-15 table, Boundary Test character-identical
     between rsil-global and rsil-review
  2. Agent memory section headers referenced in rsil-global G-4 AND rsil-review R-4
     match actual MEMORY.md headers
  3. Tracker namespacing: G-{N} schema in rsil-global G-4 matches new tracker §3.5
  4. CLAUDE.md NL discipline: trigger phrasing consistent with rsil-global When to Use
  5. Dynamic Context agent memory line: head -50 in both skills

  ## Dependency Chain
  - blockedBy: [Task A, Task B, Task C]
  - blocks: []

  ## Acceptance Criteria
  AC-1: Shared Foundation diff = 0 (except intro line adaptation)
  AC-2: All 4 agent memory section headers match across 3 files
  AC-3: Tracker schema fields match rsil-global G-4 output format
  AC-4: CLAUDE.md "pipeline delivery (Phase 9)" phrasing aligns with rsil-global
        When to Use "Pipeline delivery (Phase 9) finished?"
  AC-5: No orphan cross-references

activeForm: "Validating cross-file integration"
```

---

## 5. Detailed File Specifications

### Spec A: /rsil-global SKILL.md (NEW) — implementer-1

**Verification Level: VL-2 (guided generation)** — structural outline with key text blocks provided.
implementer synthesizes into cohesive skill file following /rsil-review as structural reference.

#### A1: Frontmatter [VL-1]

```yaml
---
name: rsil-global
description: "INFRA Meta-Cognition health assessment — auto-invoked by Lead after pipeline delivery or .claude/ infrastructure changes. Three-Tier observation window, 8 universal lenses, AD-15 filter. Lightweight (~2000 token budget). Findings-only output."
argument-hint: "[optional: specific area of concern]"
---
```

#### A2: Skill Intro [VL-2]

```markdown
# RSIL Global

INFRA Meta-Cognition health assessment with ultrathink deep reasoning. Auto-invoked by Lead
after pipeline delivery or .claude/ infrastructure changes. Three-Tier Observation Window
reads only what's needed (~2000 token budget). Identifies INFRA consistency issues across
the just-completed work. Findings-only output — user approves before any changes.

**Announce at start:** "Running RSIL Global health assessment for the just-completed work."

**Core flow:** G-0 Observation Classification → G-1 Tiered Reading → G-2 Discovery (rare) → G-3 Classification → G-4 Record
```

#### A3: When to Use Decision Tree [VL-1]

Copy verbatim from L3 architecture §3.2 (lines 138-156):

```
## When to Use

```
Work just completed in this session?
├── Pipeline delivery (Phase 9) finished? ── yes ──→ INVOKE /rsil-global
├── .claude/ files committed?
│   ├── yes
│   │   ├── ≥2 files changed? ── yes ──→ INVOKE /rsil-global
│   │   ├── 1 file changed
│   │   │   ├── Change touches cross-referenced file? ── yes ──→ INVOKE
│   │   │   └── Trivial edit (typo, formatting)? ── yes ──→ SKIP
│   │   └── no changes to .claude/ ──→ SKIP
│   └── no
├── Skill execution modified INFRA files? ── yes ──→ INVOKE
├── Read-only session (research, questions)? ──→ SKIP
└── Non-.claude/ changes only (application code)? ──→ SKIP
```

**Key principle:** Default to INVOKE for pipeline work and multi-file INFRA changes.
Default to SKIP for trivial edits, non-INFRA work, and read-only sessions.
When uncertain, invoke — the lightweight budget means low cost for a false positive.

**What this skill does:** Lightweight INFRA health scan using Three-Tier Observation
Window. Reads session artifacts and git diffs. Classifies findings using 8 Lenses
and AD-15 filter. Presents findings for user approval.

**What this skill does NOT do:** Deep component analysis (use /rsil-review), modify
files directly, spawn long-lived teammates, or auto-chain to other skills.
```

#### A4: Dynamic Context Shell Commands [VL-1]

```markdown
## Dynamic Context

!`ls -dt .agent/teams/*/ 2>/dev/null | head -3`

!`ls .agent/teams/*/phase-*/gate-record*.yaml 2>/dev/null | wc -l`

!`find .agent/teams/ -name "L1-index.yaml" 2>/dev/null | wc -l`

!`git diff --name-only HEAD~1 2>/dev/null | head -20`

!`cat ~/.claude/agent-memory/rsil/MEMORY.md 2>/dev/null | head -50`

!`wc -l docs/plans/2026-02-08-narrow-rsil-tracker.md 2>/dev/null`

**Feature Input:** $ARGUMENTS (optional — specific area of concern)
```

**Note:** Agent memory reads head -50 (not head -30 as in L3 §3.3). §7 is authoritative:
"The 50-line head captures §1 + §2 (the most operationally useful data)."

#### A5: Phase 0 — PERMANENT Task Check [VL-2]

Follow the same Phase 0 pattern as /rsil-review (lines 56-77). Implementer should:
1. Include TaskList check for [PERMANENT] subject
2. If found → TaskGet → read PT for pipeline context
3. If not found → AskUserQuestion → offer /permanent-tasks or continue without
4. Proceed to G-0

#### A6: Phase G-0 — Observation Window Classification [VL-2]

Lead-only. Use sequential-thinking.

Content based on L3 architecture §3.4. Must include:

1. **Classification rules** (Type A/B/C/No work):
   - Type A: `.agent/teams/` has session directories with gate records → pipeline work
   - Type B: No session dir, but git diff shows .claude/ skill or reference changes → skill execution
   - Type C: No session dir, git diff shows .claude/ .md changes (not skills) → direct edit
   - No work: No git diff, no new sessions → skip entirely

2. **Decision tree** (ASCII art from L3 §3.4, lines 182-198)

3. **Fallback rule:** When uncertain, treat as Type A (most comprehensive)

4. **$ARGUMENTS handling:** If user specified a concern, note it for lens prioritization in G-1

#### A7: Phase G-1 — Tiered Reading + Health Assessment [VL-3]

This is the core creative section. Based on L3 architecture §3.5. Must include:

1. **Tier 1 Reading per work type** (3 subsections for Type A, B, C):
   - Type A reads: latest gate-record.yaml, latest L1-index.yaml (cap: 3), orchestration-plan.md tail
   - Type B reads: git diff HEAD~1 for .claude/, tracker diff, reference chain check
   - Type C reads: git diff HEAD~1 content, MEMORY.md diff, reference listing

2. **Health Indicator Assessment** (5 indicators table from L3 §3.5):
   H-1 Gate pass rate, H-2 L1/L2 existence, H-3 Re-spawn count, H-4 Warning density, H-5 Cross-ref consistency
   Note: Type B/C only have H-5 as directly measurable indicator.

3. **Lens Application During Reading** (table of 8 lenses with global relevance from L3 §3.5):
   Generate observations, not full findings. Observations feed G-3.

4. **Escalation Decision** (Tier 1 → Tier 2, from L3 §3.5):
   All healthy + no observations → "INFRA healthy. No findings." → G-4
   Any anomaly → Tier 2

5. **Tier 2 Reading** (selective, ~1000 tokens, from L3 §3.5):
   Only flagged areas. Read L2/TEAM-MEMORY for context.
   Tier 2 → Tier 3 escalation: ≥3 cross-file anomalies OR ≥2 BREAK-severity OR systemic pattern

#### A8: Phase G-2 — Discovery (Tier 3 Only) [VL-2]

Most runs skip this phase. Based on L3 §3.6.

1. Spawn Explore agent with anomaly list from Tier 2
2. Agent directive construction (from L3 §3.6):
   ```
   subagent_type: "Explore"
   prompt: "Investigate the following INFRA anomalies... {list from Tier 2}"
   ```
3. Optional claude-code-guide spawn only if CC capability gap suspected
4. Collect structured findings

#### A9: Phase G-3 — Classification + Presentation [VL-2]

Based on L3 §3.7. Must include:

1. **AD-15 Filter application** (classification logic from L3 §3.7)
2. **Severity assignment:** BREAK / FIX / WARN
3. **Presentation template** (from L3 §3.7, lines 349-373):

```markdown
## RSIL Global Assessment — {date}

**Work Type:** {A/B/C}
**Observation:** {what was reviewed}
**Tiers Used:** {0-1 / 0-2 / 0-3}
**Lenses Applied:** {N}/8

### Findings
| ID | Finding | Severity | Category | Lens |

### BREAK Items (if any)
{detail per BREAK finding — file:line, evidence, proposed fix}

### FIX Items (Category B)
{detail per FIX — proposed NL text change}

### DEFER Items (Category C)
{detail — why L1 insufficient}

### Summary
BREAK: {N} | FIX: {N} | DEFER: {N} | WARN: {N} | PASS: {N}
INFRA Health: {assessment}
```

4. **BREAK handling:** AskUserQuestion — "RSIL Global found {N} BREAK-severity issues. Review and fix now, or defer?"
5. **Zero findings:** "INFRA healthy. No findings from this assessment." → G-4

#### A10: Phase G-4 — Record [VL-2]

Based on L3 §3.8. Must include:

1. **Tracker Update** (Read-Merge-Write to docs/plans/2026-02-08-narrow-rsil-tracker.md):
   - §2 Summary Table: add row with source_skill=rsil-global
   - §3 Global Findings: append G-{N} entries using extended schema:
     ```yaml
     - id: G-{N}
       source_skill: rsil-global
       finding_type: global
       finding: "{description}"
       category: "B"
       severity: "FIX"
       detection_tier: 1
       cross_refs: []
       decomposed_to: []
       status: "ACCEPTED"
     ```
   - §4 Cross-Cutting Patterns: add if new systemic pattern discovered
   - §5 Backlog: add accepted-but-not-applied items

2. **Agent Memory Update** (Read-Merge-Write to ~/.claude/agent-memory/rsil/MEMORY.md):
   - §1 Configuration: increment review count, update date
   - §2 Lens Performance: increment findings/accepted per lens used
   - §3 Cross-Cutting Patterns: add new universal pattern (if discovered)
   - §4 Lens Evolution: add lens candidate (if identified)

3. **Terminal Summary** (from L3 §3.8):
   ```markdown
   ## RSIL Global Complete

   **Work Type:** {A/B/C}
   **Tiers Used:** {0-1 / 0-2 / 0-3}
   **Findings:** BREAK {N} | FIX {N} | DEFER {N} | WARN {N}
   **Applied:** {N} (user-approved)
   **INFRA Health:** {healthy / needs-attention / critical}

   Tracker updated: {N} new findings (G-{start}~G-{end})
   Agent memory updated: review #{N}, cumulative {total} findings

   No auto-chaining. Session continues normally.
   ```

#### A11: Error Handling [VL-1]

Copy from L3 §3.9:

| Situation | Response |
|-----------|----------|
| No git diff and no sessions | "No recent work detected. Skipping." |
| Tier 0 misclassification suspected | Fall back to Type A reading (most comprehensive) |
| Tier 1 reads exceed budget | Cap at 3 L1 files + 1 gate record. Note truncation. |
| Tier 3 agent returns empty | Proceed with Tier 1/2 findings only |
| Tracker file not found | Create initial section structure, then append |
| Agent memory not found | Create with seed data from tracker |
| User cancels mid-review | Preserve partial tracker updates |

#### A12: Shared Foundation — 8 Meta-Research Lenses [VL-1]

**VERBATIM COPY.** This text must be character-identical to /rsil-review lines 149-166,
EXCEPT the intro line which is adapted:

```markdown
## Static Layer: 8 Meta-Research Lenses

Universal quality principles. Apply to any target — the specific research questions
are generated by Lead during G-1 based on which lenses are relevant to the observation window.

| # | Lens | Core Question |
|---|------|---------------|
| L1 | TRANSITION INTEGRITY | Are state transitions explicit and verifiable? Could implicit transitions allow steps to be skipped? |
| L2 | EVALUATION GRANULARITY | Are multi-criteria evaluations individually evidenced? Or bundled into single pass-through judgments? |
| L3 | EVIDENCE OBLIGATION | Do output artifacts require proof of process (sources, tools used)? Or only final results? |
| L4 | ESCALATION PATHS | Do critical findings trigger appropriate multi-step responses? Or only single-shot accept/reject? |
| L5 | SCOPE BOUNDARIES | Are shared resources accessible across scope boundaries? Are cross-scope access patterns handled? |
| L6 | CLEANUP ORDERING | Are teardown/cleanup prerequisites explicitly sequenced? Or assumed to "just work"? |
| L7 | INTERRUPTION RESILIENCE | Is intermediate state preserved against unexpected termination? Or does the process assume completion? |
| L8 | NAMING CLARITY | Are identifiers unambiguous across all contexts where they appear? Or could the same name mean different things? |

Lenses evolve: if new universal patterns are discovered, add L9, L10, etc. Update this
table and MEMORY.md accordingly.
```

**Difference from rsil-review:** Line 2 says "generated by Lead during G-1 based on which
lenses are relevant to the observation window" instead of "generated by Lead in Phase R-0
based on which lenses are relevant to $ARGUMENTS." The 8-row table is IDENTICAL.

#### A13: Shared Foundation — AD-15 Filter [VL-1]

**VERBATIM COPY** from /rsil-review lines 170-176:

```markdown
## Static Layer: AD-15 Filter

| Category | Test | Action |
|----------|------|--------|
| A (Hook) | Would require adding a new hook | REJECT unconditionally |
| B (NL) | Achievable through .md file changes | ACCEPT — propose exact text |
| C (Layer 2) | Requires structured systems | DEFER — document why L1 insufficient |
```

#### A14: Shared Foundation — Boundary Test [VL-1]

**VERBATIM COPY** from /rsil-review lines 133-145:

```markdown
### Boundary Test

Apply to every finding:

```
"Can this be achieved through NL .md instructions + 3 existing hooks
 + Task API + MCP tools + Agent Teams messaging + Skill features?"

YES     → Layer 1, Category B — propose exact NL text change
NO      → Layer 2, Category C — document why L1 insufficient
PARTIAL → Split: L1 portion as B + L2 remainder as C
Hook    → REJECT unconditionally (AD-15: 8→3 inviolable)
```
```

#### A15: Principles Section [VL-2]

~10-12 items in positive form. Based on L3 §3.10. Key items:

- Lightweight by design — most runs complete at Tier 1 with zero findings
- Observation window stays under ~2000 tokens (Tier 0+1+2 combined)
- Findings-only output — user approves before any changes
- AD-15 inviolable — Category A REJECT, B ACCEPT, C DEFER
- Lenses generate observations, not prescriptions
- Tier 3 (Explore agent) is the exception, not the norm
- Record everything — even "clean" runs update agent memory statistics
- Self-healing through persistence — unfixed BREAKs are re-detected next session
- Terminal — no auto-chaining to /rsil-review or other skills
- INFRA scope only — never assess application code
- Use sequential-thinking at every tier transition and classification decision

---

### Spec B: /rsil-review Deltas + CLAUDE.md — implementer-2

#### B1: Delta 1 — Ultrathink Integration [VL-1]

**File:** `.claude/skills/rsil-review/SKILL.md`
**Location:** Lines 9-11

**Old text:**
```
Meta-Cognition-Level quality review skill. Applies universal research lenses and
integration auditing to any target within .claude/ infrastructure. Identifies Layer 1
(NL-achievable) improvements and Layer 2 (Ontology Framework) deferrals.
```

**New text:**
```
Meta-Cognition-Level quality review skill with ultrathink deep reasoning. Applies
universal research lenses and integration auditing to any target within .claude/
infrastructure. Identifies Layer 1 (NL-achievable) improvements and Layer 2
(Ontology Framework) deferrals.
```

**Net change:** 0 lines (reflow only). +1 word ("ultrathink").

#### B2: Delta 2 — Target Size Pre-Check [VL-1]

**File:** `.claude/skills/rsil-review/SKILL.md`
**Location:** After line 51 (after `!`wc -l /home/palantir/.claude/references/agent-common-protocol.md 2>/dev/null``)

**Insert new line:**
```
!`wc -l $ARGUMENTS 2>/dev/null`
```

**Net change:** +1 line.

#### B3: Delta 3a — Agent Memory Read [VL-1]

**File:** `.claude/skills/rsil-review/SKILL.md`
**Location:** After Delta 2's new line (after `!`wc -l $ARGUMENTS 2>/dev/null``)

**Insert new line:**
```
!`cat ~/.claude/agent-memory/rsil/MEMORY.md 2>/dev/null | head -50`
```

**Net change:** +1 line.

#### B4: Delta 3b — Agent Memory Write [VL-1]

**File:** `.claude/skills/rsil-review/SKILL.md`
**Location:** After line 483 ("One-off findings go to tracker only. MEMORY.md receives patterns only.")

**Insert new section:**
```markdown

### Agent Memory Update

Update `~/.claude/agent-memory/rsil/MEMORY.md` using Read-Merge-Write:
- §1 Configuration: increment review count, update last review date
- §2 Lens Performance: update per-lens statistics from this review
- §3 Cross-Cutting Patterns: add new universal pattern (if discovered in this review)
- §4 Lens Evolution: add candidate (if a new universal pattern suggests a new lens)

Only add patterns that apply across ANY target. One-off findings stay in tracker only.
```

**Net change:** +7 lines (including blank line before section header).

#### B5: Delta 4 — Principles Section Merge [VL-1]

**File:** `.claude/skills/rsil-review/SKILL.md`
**Location:** Lines 537-561 (entire Key Principles + Never sections to end of file)

**Old text (25 lines):**
```
## Key Principles

- **Framework is universal, scope is dynamic** — SKILL.md never changes per target
- **Lead's R-0 synthesis is the core value** — Lenses × TARGET = specific questions
- **Accumulated context is distilled into Lenses** — individual findings are not in SKILL.md
- **AD-15 inviolable** — Category A REJECT, Category B ACCEPT, Category C DEFER
- **Layer 1/2 boundary is the single test** — "achievable through NL + existing infra?"
- **Lenses evolve** — new patterns discovered in future reviews can become L9, L10
- **Evidence-based only** — every finding cites CC docs or file:line references
- **User confirms application** — BREAK/FIX applied only after user approval
- **Sequential thinking always** — Lead uses structured reasoning at every decision point
- **Terminal, no auto-chain** — after RSIL, the user decides what happens next

## Never

- Use hardcoded Research Questions (generate from Lenses in R-0)
- Use hardcoded Integration Axes (derive from file references in R-0)
- Propose adding a new hook (AD-15 8→3 inviolable)
- Promote Category C to Category B (if L2 needed, it's DEFER)
- Accept findings without evidence (CC doc or file:line required)
- Modify files without user approval
- Auto-chain to another skill after completion
- Embed accumulated context in SKILL.md (only Lenses, never raw findings)
- Skip R-0 synthesis (the universal→specific bridge is mandatory)
- Treat Lenses as fixed (they evolve with new pattern discoveries)
```

**New text (15 lines):**
```
## Principles

- Framework is universal, scope is dynamic — generate Research Questions and Integration Axes from Lenses in R-0, never hardcode them
- R-0 synthesis is the core value — the universal→specific bridge is mandatory for every review
- Accumulated context distills into Lenses — individual findings stay in tracker, not SKILL.md
- AD-15 inviolable — Category A REJECT, B ACCEPT, C DEFER. Never propose new hooks.
- Layer 1/2 boundary test is definitive — if Layer 2 is needed, it's DEFER. Never promote C to B.
- Lenses evolve — new universal patterns from future reviews become L9, L10
- Every finding cites CC documentation or file:line references — no unsupported claims
- User confirms all changes — present findings, wait for approval before modifying files
- Use sequential-thinking at every decision point throughout the review
- Terminal skill — user decides next step. No auto-chaining to other skills.
- Never embed raw findings in SKILL.md — only universal Lenses belong here
```

**Net change:** -10 lines (25 removed, 15 added). Bold removed from list items.

#### B6: Delta 5 — Output Format Simplification [VL-1]

**File:** `.claude/skills/rsil-review/SKILL.md`
**Location:** Lines 201-231 (Static Layer: Output Format section)

**Old text (31 lines):**
```
## Static Layer: Output Format

Both agents use this standardized output structure.

**[A] claude-code-guide output:**
```
## Findings Table
| ID | Finding | Layer | Category | Lens | CC Evidence |

## Category B Detail (Layer 1 — actionable)
Per finding: What, Where (file:section), CC Capability, Why suboptimal, Proposed NL text

## Category C Detail (Layer 2 — deferred)
Per finding: What, Why L1 cannot, What L2 provides, Current best NL workaround

## L1 Optimality Score: X/10
## Top 3 Recommendations
```

**[B] Explore output:**
```
## Axis Results
| Axis | File A | File B | Status | Findings |

## Findings Detail
Per finding: Axis, Severity, File A (path:line + content), File B (path:line + content),
Inconsistency description, Specific fix

## Integration Score: X/N axes passing
```
```

**New text (26 lines):**
```
## Static Layer: Output Format

Both agents produce structured findings reports.

**[A] claude-code-guide output should include:**
- Findings Table: ID, Finding, Layer, Category, Lens, CC Evidence
- Category B Detail: What, Where (file:section), CC Capability, Why suboptimal, Proposed NL text
- Category C Detail: What, Why L1 cannot, What L2 provides, Current best NL workaround
- L1 Optimality Score (X/10)
- Top 3 Recommendations

**[B] Explore output should include:**
- Axis Results Table: Axis, File A, File B, Status, Findings
- Findings Detail: Axis, Severity, File A (path:line + content), File B (path:line + content), Inconsistency, Specific fix
- Integration Score (X/N axes passing)
```

**Net change:** -5 lines (31 removed, 26 added). Nested code blocks → bullet lists.

#### B7: CLAUDE.md NL Discipline Insertion [VL-1]

**File:** `.claude/CLAUDE.md`
**Location:** After line 33 ("Every task assignment requires understanding verification before work begins."),
before line 35 ("## 3. Roles")

**Insert (5 lines):**
```markdown

After completing pipeline delivery (Phase 9) or committing .claude/ infrastructure
changes, Lead invokes /rsil-global for INFRA health assessment. Skip for trivial
single-file edits (typo fixes), non-.claude/ changes, or read-only sessions.
The review is lightweight (~2000 token observation budget) and presents findings
for user approval before any changes are applied.
```

**Net change:** +5 lines (including blank line before paragraph). CLAUDE.md: 172 → 177 lines.

---

### Spec C: Agent Memory + Tracker — implementer-2

#### C1: Agent Memory Seed File [VL-1]

**File:** `~/.claude/agent-memory/rsil/MEMORY.md` (NEW)
**Create directory:** `~/.claude/agent-memory/rsil/` if it doesn't exist.

**Exact content (verbatim from L3 §7 seed data):**

```markdown
# RSIL Agent Memory

## 1. Configuration
- Last review: 2026-02-08
- Total reviews: 4 (global: 0, narrow: 4)
- Cumulative findings: 24 (accepted: 19, rejected: 2, deferred: 3)
- Acceptance rate: 79%
- Active lenses: L1-L8

## 2. Lens Performance
| Lens | Applied | Findings | Accepted | Rate |
|------|---------|----------|----------|------|
| L1 TRANSITION INTEGRITY | 4 | 3 | 3 | 100% |
| L2 EVALUATION GRANULARITY | 3 | 2 | 2 | 100% |
| L3 EVIDENCE OBLIGATION | 4 | 3 | 3 | 100% |
| L4 ESCALATION PATHS | 3 | 2 | 2 | 100% |
| L5 SCOPE BOUNDARIES | 4 | 4 | 4 | 100% |
| L6 CLEANUP ORDERING | 2 | 1 | 1 | 100% |
| L7 INTERRUPTION RESILIENCE | 2 | 1 | 0 | 0% |
| L8 NAMING CLARITY | 3 | 2 | 2 | 100% |

Top performers: L1, L3, L5 (highest finding yield with 100% acceptance)
Low yield: L7 (1 finding, 0% acceptance — deferred to Layer 2)

## 3. Cross-Cutting Patterns
Patterns applicable across ANY target. One-off findings stay in tracker.

### P-1: Evidence Sources in All L2 Outputs
- Origin: P5-R1
- Scope: All teammate types producing L2 output
- Principle: Require "Evidence Sources" section in every L2-summary.md
- Applied in: plan-validation-pipeline, agent-common-protocol.md

### P-2: Explicit Checkpoint Steps in Directives
- Origin: P4-R1
- Scope: All skills that spawn teammates requiring understanding verification
- Principle: Structure as "Step 1: Read+Explain → Wait → Step 2: Execute"
- Applied in: agent-teams-write-plan, agent-teams-execution-plan

### P-3: Cross-File Integration Audit as Standard Step
- Origin: P6 (full RSIL review)
- Scope: All pipeline skill reviews
- Principle: Bidirectional consistency audit catches drift that single-file review misses
- Applied in: rsil-review methodology (standard)

### P-4: Rejection Cascade Specification
- Origin: P9-R1
- Scope: Skills with 2+ user confirmation gates
- Principle: Document which artifacts preserved, which ops skipped, what cleanup needed on rejection
- Applied in: delivery-pipeline

## 4. Lens Evolution
No candidates yet. Monitoring for patterns from future reviews.
```

**Total:** ~86 lines. Section headers MUST be exactly: `## 1. Configuration`,
`## 2. Lens Performance`, `## 3. Cross-Cutting Patterns`, `## 4. Lens Evolution`.

#### C2: Tracker Migration — Summary Table [VL-1]

**File:** `docs/plans/2026-02-08-narrow-rsil-tracker.md`
**Location:** §2 Summary Table (lines 77-85)

**Old table header (line 79):**
```
| Sprint | Skill | Phase | Findings | Accepted | Rejected | Deferred |
```

**New table header:**
```
| Sprint | Skill | Phase | Source | Findings | Accepted | Rejected | Deferred |
```

**Old data rows (lines 81-85):**
```
| SKL-006 | /agent-teams-write-plan | P4 | 4 | 2 | 1 | 1 |
| SKL-006 | /plan-validation-pipeline | P5 | 4 | 2 | 1 | 1 |
| SKL-006 | /agent-teams-execution-plan | P6 | 7 | 7 | 0 | 0 |
| SKL-006 | /delivery-pipeline | P9 | 9 | 8 | 0 | 1 |
| **Total** | | | **24** | **19** | **2** | **3** |
```

**New data rows (add Source column with "rsil-review" for all existing):**
```
| SKL-006 | /agent-teams-write-plan | P4 | rsil-review | 4 | 2 | 1 | 1 |
| SKL-006 | /plan-validation-pipeline | P5 | rsil-review | 4 | 2 | 1 | 1 |
| SKL-006 | /agent-teams-execution-plan | P6 | rsil-review | 7 | 7 | 0 | 0 |
| SKL-006 | /delivery-pipeline | P9 | rsil-review | 9 | 8 | 0 | 1 |
| **Total** | | | | **24** | **19** | **2** | **3** |
```

#### C3: Tracker Migration — Global Findings Section [VL-1]

**File:** `docs/plans/2026-02-08-narrow-rsil-tracker.md`
**Location:** After §3.4 (/delivery-pipeline section, ending ~line 168), before "---" separator and §4

**Insert new subsection:**

```markdown

### 3.5 Global Findings (/rsil-global)

_No global findings yet. This section will be populated when /rsil-global runs._

| ID | Finding | Category | Severity | Tier | Lens | Status |
|----|---------|----------|----------|------|------|--------|
```

#### C4: Tracker Migration — Extended Schema Documentation [VL-2]

**File:** `docs/plans/2026-02-08-narrow-rsil-tracker.md`
**Location:** After §6 (Rejected & Deferred Items, ~line 238), before §7

**Insert new section:**

```markdown

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
```

---

## 6. Integration Points

### 6.1 Shared Foundation Character-Identity Check

**After both implementers complete:**

1. Extract Lenses table rows from `/rsil-global/SKILL.md` (grep for `| L[1-8] |`)
2. Extract same from `/rsil-review/SKILL.md`
3. Diff: MUST be character-identical (8 rows)
4. Extract AD-15 table from both (3 rows: A/B/C)
5. Diff: MUST be character-identical
6. Extract Boundary Test block from both (lines containing "Can this be achieved" through "Hook")
7. Diff: MUST be character-identical
8. **Allowed difference:** Lenses intro line (R-0 vs G-1 reference). Only line 2 of the Lenses section may differ.

**If diff found:** Adjust the file that deviates from the verbatim §5 spec.

### 6.2 Agent Memory Section Header Consistency

Verify the 4 section headers appear identically in 3 places:
- `~/.claude/agent-memory/rsil/MEMORY.md` (actual headers)
- `/rsil-global/SKILL.md` G-4 Agent Memory Update instructions (referenced names)
- `/rsil-review/SKILL.md` Agent Memory Update section (Delta 3b, referenced names)

Expected headers:
```
## 1. Configuration
## 2. Lens Performance
## 3. Cross-Cutting Patterns
## 4. Lens Evolution
```

### 6.3 Tracker Schema Consistency

Verify:
- rsil-global G-4 output format (G-{N} YAML fields) matches tracker §6.5 Extended Schema
- Summary Table column count matches between header and data rows
- Global Findings section (§3.5) column headers match the extended schema

### 6.4 NL Discipline ↔ When to Use Alignment

Verify CLAUDE.md NL discipline trigger phrasing aligns with rsil-global When to Use:
- CLAUDE.md: "After completing pipeline delivery (Phase 9)" ↔ rsil-global: "Pipeline delivery (Phase 9) finished?"
- CLAUDE.md: "or committing .claude/ infrastructure changes" ↔ rsil-global: ".claude/ files committed?"
- CLAUDE.md: "Skip for trivial single-file edits" ↔ rsil-global: "Trivial edit (typo, formatting)? → SKIP"

### 6.5 Dynamic Context Agent Memory Line

Both skills must read agent memory with `head -50`:
- rsil-global: `!`cat ~/.claude/agent-memory/rsil/MEMORY.md 2>/dev/null | head -50``
- rsil-review (Delta 3a): `!`cat ~/.claude/agent-memory/rsil/MEMORY.md 2>/dev/null | head -50``

---

## 7. Validation Checklist

### V1: File Existence and Line Counts

- [ ] `.claude/skills/rsil-global/SKILL.md` exists, ~400-500 lines
- [ ] `.claude/skills/rsil-review/SKILL.md` is ~551 lines (±3)
- [ ] `.claude/CLAUDE.md` is ~177 lines
- [ ] `~/.claude/agent-memory/rsil/MEMORY.md` exists, ~86 lines
- [ ] `docs/plans/2026-02-08-narrow-rsil-tracker.md` has new §3.5 and §6.5 sections

### V2: Shared Foundation Identity

- [ ] 8 Lenses table rows character-identical between rsil-global and rsil-review
- [ ] AD-15 Filter table character-identical between rsil-global and rsil-review
- [ ] Boundary Test block character-identical between rsil-global and rsil-review
- [ ] Only Lenses intro line differs (G-1 vs R-0 reference)

### V3: Agent Memory Interface

- [ ] MEMORY.md section headers = `## 1. Configuration`, `## 2. Lens Performance`,
      `## 3. Cross-Cutting Patterns`, `## 4. Lens Evolution`
- [ ] rsil-global G-4 references these same 4 section names
- [ ] rsil-review Agent Memory Update (Delta 3b) references these same 4 section names
- [ ] Both skills use `head -50` for dynamic context agent memory read

### V4: Tracker Consistency

- [ ] Summary Table has "Source" column; all existing rows = "rsil-review"
- [ ] §3.5 Global Findings section exists with correct column headers
- [ ] §6.5 Extended Schema documents all YAML fields used in rsil-global G-4
- [ ] Existing findings (P4-R{N} through P9-R{N}) unchanged

### V5: CLAUDE.md Integration

- [ ] 5-line NL discipline paragraph exists after §2 table, before §3 Roles
- [ ] Trigger language aligns with rsil-global When to Use (§6.4 checks)
- [ ] No other CLAUDE.md sections modified

### V6: Code Plausibility (Architect Cannot Run)

Items requiring runtime verification or manual testing post-deployment:

| ID | Item | Risk | Recommended Verification |
|----|------|------|--------------------------|
| V6-1 | Dynamic Context shell commands with no sessions | G-0 receives empty output | Test: invoke /rsil-global in clean workspace |
| V6-2 | `git diff --name-only HEAD~1` on fresh repo | Silent failure | Test: invoke in repo with 0-1 commits |
| V6-3 | `head -50` agent memory read captures §1+§2 | Seed file is 86L, head -50 gets first 50 | Verify: seed data §1+§2 fit within 50 lines |
| V6-4 | G-0 Type A/B/C classification correctness | NL logic may misclassify edge cases | Test: 3 scenarios (pipeline, skill edit, direct edit) |
| V6-5 | Tier budget adherence (~2000 tokens) | No runtime enforcement | Monitor: first 3 runs, check actual token usage |
| V6-6 | rsil-review Delta 5 (Output Format) doesn't break R-1 agent output | Agents may rely on exact format | Verify: R-1 agents use guidance, not template matching |
| V6-7 | `wc -l $ARGUMENTS` with multi-word argument | Shell word splitting risk | Test: invoke with path containing spaces |

**Recommended:** First 3 /rsil-global runs should be manually monitored for V6-1 through V6-5.
V6-6 can be verified during the next /rsil-review invocation. V6-7 is low-risk (most paths
don't contain spaces in this codebase).

---

## 8. Risk Register

### Carried Forward from Architecture (R-1 through R-7)

| # | Risk | L | I | Score | Mitigation | Implementation Note |
|---|------|---|---|-------|------------|---------------------|
| R-1 | Tier 0 work type misclassification | LOW | MED | 3 | Multiple signals + Type A fallback | §5 A6 specifies fallback rule |
| R-2 | Context budget overrun | MED | LOW | 4 | Cap at 3 L1 files | §5 A11 error handling |
| R-3 | NL discipline non-compliance | MED | LOW | 4 | CLAUDE.md instruction + memory staleness | §5 B7 CLAUDE.md insertion |
| R-4 | Tracker growth | LOW | LOW | 2 | Split at 150 findings | §5 C4 extended schema supports this |
| R-5 | Agent memory 200-line limit | MED | LOW | 4 | Budget allocation + universality filter | §5 C1 seed data is 86L (114L buffer) |
| R-6 | Shared agent memory write conflict | LOW | MED | 3 | Sequential execution only | AD-11, natural ordering |
| R-7 | /rsil-global generates noise | MED | LOW | 4 | Tier gates + AD-15 + acceptance self-correction | §5 A9 AD-15 filter application |

### Implementation-Specific Risks

| # | Risk | L | I | Score | Mitigation |
|---|------|---|---|-------|------------|
| R-8 | Shared Foundation text drift between skills | LOW | HIGH | 4 | §5 provides verbatim text + §6.1 character-level diff check |
| R-9 | Agent memory schema mismatch across files | LOW | MED | 3 | §5 uses identical section names from single source + §6.2 verification |
| R-10 | implementer-1 exceeds 500L budget for rsil-global | MED | LOW | 4 | §5 provides structural outline with line budgets per section. AC-12 caps at ~500L. |
| R-11 | Delta 4 (principles merge) changes semantic meaning | LOW | MED | 3 | §5 B5 provides exact old and new text. Each new item maps to ≥1 old item. |
| R-12 | Tracker §6.5 schema format incompatible with existing | LOW | LOW | 2 | §5 C4 explicitly states "Existing narrow findings retain current format" |

---

## 9. Commit Strategy

### Recommended: Single commit after all validation passes

```bash
# Create rsil-global directory
mkdir -p .claude/skills/rsil-global

# Create agent memory directory
mkdir -p ~/.claude/agent-memory/rsil

# Stage all files
git add .claude/skills/rsil-global/SKILL.md \
  .claude/skills/rsil-review/SKILL.md \
  .claude/CLAUDE.md \
  docs/plans/2026-02-08-narrow-rsil-tracker.md

# Note: ~/.claude/agent-memory/rsil/MEMORY.md is outside the git repo
# (user-scope, not project-scope) — no git add needed

git commit -m "$(cat <<'EOF'
feat(rsil): RSIL System — /rsil-global + /rsil-review refinement

Add /rsil-global auto-invoked INFRA health assessment skill:
- Three-Tier Observation Window (Type A/B/C work classification)
- 8 Meta-Research Lenses + AD-15 Filter (shared with /rsil-review)
- ~2000 token context budget, findings-only output
- G-0→G-4 flow with tracker and agent memory integration

Refine /rsil-review (5 deltas, 561→~551L):
- ultrathink keyword, wc-l pre-check, agent memory R/W
- Principles section merged (21→11 items), output format simplified

CLAUDE.md: +5L NL discipline for auto-invocation trigger
Agent memory: shared ~/.claude/agent-memory/rsil/MEMORY.md (seed data)
Tracker: +Global Findings section, +extended schema documentation

Architecture: .agent/teams/rsil-system/phase-3/architect-1/L3-full/
Decisions: D-1~D-5, AD-6~AD-11

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

### Alternative: Two commits (if Lead prefers granularity)

1. `feat(rsil): add /rsil-global auto-invoked INFRA health assessment skill`
   - .claude/skills/rsil-global/SKILL.md (NEW)
   - .claude/CLAUDE.md (+5L NL discipline)
   - docs/plans/2026-02-08-narrow-rsil-tracker.md (+Global section)

2. `feat(rsil): refine /rsil-review — 5 deltas + agent memory integration`
   - .claude/skills/rsil-review/SKILL.md (5 deltas)
   - (agent memory is outside git repo)

---

## 10. Phase 5 Validation Targets

### What the Devils-Advocate Should Challenge

1. **Shared Foundation identity guarantee:** Is verbatim copy in §5 sufficient, or should
   there be a mechanical verification step (e.g., a diff script)? Challenge: what if
   implementer-1 makes a minor formatting change (trailing space, line break) that breaks
   character identity?

2. **G-0 classification completeness:** The Type A/B/C/No-work categorization covers 4 cases.
   Challenge: what about mixed cases (pipeline session + direct edit in same session)?
   Is the fallback to Type A always correct?

3. **Token budget enforcement:** ~2000 tokens is a soft limit enforced by NL instruction.
   Challenge: what happens when Tier 1 reads a gate-record.yaml that's unusually large
   (e.g., 200+ lines)? Is the 3-L1-file cap sufficient?

4. **Agent memory seed data accuracy:** Seed data is derived from tracker §2 Summary Table
   (24 findings). Challenge: is the per-lens distribution in the seed data (§2 Lens Performance)
   actually derivable from the tracker, or does it require manual reconstruction? Are the
   numbers in the seed data correct?

5. **Tracker backward compatibility:** New "Source" column in §2 Summary Table and new §3.5/§6.5
   sections. Challenge: does anything currently READ the tracker programmatically? If so,
   does adding columns break parsing?

6. **Delta 4 semantic preservation:** 21 items merged to 11. Challenge: do any original
   prohibitions (from "Never" section) lose their force when merged into positive-form
   statements? Specifically: "Skip R-0 synthesis" prohibition — is "R-0 synthesis is the
   core value" an equally strong instruction?

7. **NL discipline trigger vs hook:** CLAUDE.md NL instruction is the ONLY trigger for
   /rsil-global. Challenge: what's the expected compliance rate? How many sessions before
   Lead forgets? What's the detection mechanism for non-compliance (answer: agent memory
   staleness tracking)?

### Critical Assumptions to Validate

| # | Assumption | Evidence | Risk if Wrong |
|---|-----------|----------|--------------|
| A-1 | Most /rsil-global runs terminate at Tier 1 with zero findings | Design principle, not runtime data | Noise generation (R-7) |
| A-2 | ~2000 token budget is sufficient for Tier 0+1+2 | Estimated from typical L1 files (~30L each) | Context overrun (R-2) |
| A-3 | Agent memory head -50 captures §1+§2 | Seed data has §1 at lines 3-7, §2 at lines 9-28 | Missing lens data in dynamic context |
| A-4 | Sequential execution prevents agent memory write conflicts | Natural ordering (global before review) | Data corruption (R-6) |
| A-5 | Embedded copy maintenance cost < shared reference fragility | 85L × 2 skills = manageable | Foundation drift (R-8) |

---

*Implementation plan complete. All 6 components specified with exact file changes,
integration verification steps, and validation targets.*
