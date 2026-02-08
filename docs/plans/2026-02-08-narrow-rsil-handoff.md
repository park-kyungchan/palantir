# Narrow RSIL — Brainstorming Handoff Document

> **Purpose:** Enable Lead to design a formalized RSIL skill via `/brainstorming-pipeline`.
> The skill will systematize meta-cognitive quality improvement across all pipeline executions.
> **Format:** Machine-readable for Opus 4.6. English only.
> **Date:** 2026-02-08
> **Origin:** SKL-006 Delivery Pipeline sprint — user-initiated pilot test
> **Data Source:** `docs/plans/2026-02-08-narrow-rsil-tracker.md` (cumulative findings)

---

## 0. User Decisions Log (Confirmed, Chronological)

| # | Decision | User Statement (translated) |
|---|----------|-----------------------------|
| 1 | Post-skill meta-cognition review mandatory | "각 파이프라인 실행 후 실행한 스킬의 품질을 Meta-Cognition-Level에서 검토" |
| 2 | claude-code-guide grounded, always | "RSIL의 기본은 항상 claude-code-guide agent를 통한 Native Capabilities 관점" |
| 3 | Layer 1 boundary inviolable | "절대 Layer 1의 boundary를 벗어나면 안됨" |
| 4 | Tracker for brainstorming topic input | "문서 하나를 만들어서 계속 update, 차후 brainstorming-pipeline Topic으로 사용" |
| 5 | Execution-time patterns belong in RSIL | "team scope PT 접근 불가 같은 것들도 RSIL에 포함되는 것이 당연" |
| 6 | Will become a formalized skill | "RSIL에 대해서도 스킬로 만들 것" |

### Critical Scope Expansion (Decision #5)

The initial Narrow RSIL scope was limited to **post-skill quality review** — reviewing the
skill just executed for NL improvements. User Decision #5 expands this to include
**execution-time pattern discovery** — capturing recurring infrastructure issues, orchestration
pitfalls, and cross-skill bugs that emerge DURING pipeline execution.

This means the future RSIL skill must cover TWO observation windows:
```
Window 1: Post-Skill Review (existing Narrow RSIL)
  "Did the skill work as designed? What CC-native improvements exist?"
  → Findings about SKILL.md content quality

Window 2: Execution-Time Patterns (new, per Decision #5)
  "What recurring problems appeared during execution?"
  → Findings about infrastructure, orchestration, and cross-skill issues
```

---

## 1. User Intent

The user wants to **formalize meta-cognitive quality improvement** as a repeatable,
skilled pipeline step — not an ad-hoc Lead activity. Each pipeline execution should
produce quality observations that compound across sessions:

- Post-skill reviews identify NL improvements grounded in Claude Code native capabilities
- Execution-time patterns capture recurring bugs, workarounds, and infrastructure gaps
- Both are filtered through the NL-First Boundary Framework (AD-15) to stay within Layer 1
- Accepted findings are applied to SKILL.md, agent .md, and CLAUDE.md files
- Rejected/deferred findings are tracked for Layer 2 (Ontology Framework) resolution
- The cumulative data reveals whether improvements converge (diminishing returns) or
  diverge (new patterns each time)

The skill should be **lightweight** — it runs after each pipeline skill execution as a
quick meta-cognitive step, not a full pipeline sprint.

---

## 2. What the RSIL Skill Must Provide

Based on the pilot test workflow and user decisions:

```
┌────────────────────────────────────────────────────────────────┐
│  RSIL Skill                                                     │
│  ══════════════════════════════════════════════════════════════ │
│                                                                  │
│  Inputs:                                                         │
│  ├── Skill just executed (name, phase, SKILL.md path)           │
│  ├── Execution observations (Lead's meta-cognition notes)       │
│  └── Cumulative tracker (docs/plans/narrow-rsil-tracker.md)     │
│                                                                  │
│  Step 1: Meta-Cognition Review                                   │
│  ├── Process adherence: Did the skill execute as designed?      │
│  ├── Expected vs actual gaps: What deviated?                    │
│  ├── Quality observations: What worked well/poorly?             │
│  └── Execution-time patterns: What recurring issues appeared?   │
│                                                                  │
│  Step 2: claude-code-guide Research                              │
│  ├── Spawn claude-code-guide agent for CC CLI + Opus 4.6 info  │
│  ├── Focus: Native capabilities relevant to observed gaps       │
│  └── Constraint: Layer 1 boundary only                          │
│                                                                  │
│  Step 3: AD-15 Filter                                            │
│  ├── Category A (Hook) → REJECT (8→3 constraint)               │
│  ├── Category B (NL) → ACCEPT (SKILL.md/agent.md changes)      │
│  └── Category C (Layer 2) → DEFER (future Ontology Framework)  │
│                                                                  │
│  Step 4: Record & Decide                                         │
│  ├── Update tracker with findings + status                      │
│  ├── Good findings → MEMORY.md update                           │
│  ├── Pattern detection → cross-cutting improvements             │
│  └── Present summary to user                                    │
│                                                                  │
│  Outputs:                                                        │
│  ├── Updated tracker (cumulative findings table)                │
│  ├── MEMORY.md updates (if accepted findings are significant)   │
│  └── Improvement backlog (accepted but not-yet-applied changes) │
│                                                                  │
│  Principles:                                                     │
│  ├── P-1: Always claude-code-guide grounded                     │
│  ├── P-2: Layer 1 boundary inviolable                           │
│  ├── P-3: No new hooks (AD-15: 8→3)                            │
│  ├── P-4: NL-only (Category B) changes                         │
│  ├── P-5: Narrow scope per execution (one skill at a time)     │
│  ├── P-6: Evidence-based findings (cite capability source)      │
│  └── P-7: Execution-time patterns captured (Decision #5)       │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

---

## 3. Pilot Test Data (SKL-006 Sprint)

### 3.1 Summary Statistics

| Sprint | Skill | Phase | Findings | Accepted | Rejected | Deferred |
|--------|-------|-------|----------|----------|----------|----------|
| SKL-006 | /agent-teams-write-plan | P4 | 4 | 2 | 1 | 1 |
| SKL-006 | /plan-validation-pipeline | P5 | 4 | 2 | 1 | 1 |
| SKL-006 | /agent-teams-execution-plan | P6 | TBD | TBD | TBD | TBD |
| **Total** | | | **8+** | **4+** | **2** | **2** |

**Acceptance Rate:** 50% (4/8) — significant; half of all findings are implementable
**Rejection Reason:** 100% AD-15 Hook violation or API-level only

### 3.2 Accepted Findings (Improvement Backlog)

| ID | Target Skill | Change Type | Effort | Status |
|----|-------------|-------------|--------|--------|
| P4-R1 | /agent-teams-write-plan | Directive template: explicit checkpoint steps | ~10 lines | PENDING |
| P4-R2 | /agent-teams-write-plan | Gate evaluation: per-criterion with evidence | ~5 lines | PENDING |
| P5-R1 | /plan-validation-pipeline | L2 output: "Evidence Sources" section required | ~5 lines | PENDING |
| P5-R2 | /plan-validation-pipeline | CRITICAL findings: Lead→teammate re-verification | ~10 lines | PENDING |

### 3.3 Cross-Cutting Patterns Discovered

**Pattern 1: "Evidence Sources" in All L2 Outputs**
- Origin: P5-R1
- Scope: ALL teammate types
- Principle: Require "Evidence Sources" section in every L2-summary.md
- NL alternative to tool usage logging (which doesn't exist at CC CLI level)

**Pattern 2: Explicit Checkpoint Steps in Directives**
- Origin: P4-R1
- Scope: All skills with understanding verification
- Principle: "Step 1: Read + Explain → Wait → Step 2: Execute" structure

### 3.4 Execution-Time Patterns (Decision #5 — New Category)

These are NOT post-skill quality findings but recurring infrastructure issues discovered
during execution. They are equally important RSIL candidates.

| ID | Pattern | Occurrences | Impact | Category |
|----|---------|-------------|--------|----------|
| EX-1 | Team scope blocks main PT access | 3+ times (P4, P5, P6) | HIGH — every team session hits this | Infrastructure |
| EX-2 | TeamDelete fails with "active" member despite isActive=false | 2 times (P4→P5, P5→P6) | MEDIUM — workaround exists | Infrastructure |
| EX-3 | Auto-compact before L1/L2 production (BUG-002) | 3 times (RTDI Sprint) | CRITICAL — total work loss | Context management |
| EX-4 | PT numbering confusion (main #3 vs team #1) | 2 times (P4, P5) | MEDIUM — causes failed updates | Orchestration |

**EX-1 Deep Analysis (most recurring):**
- **Problem:** PERMANENT Task lives in main task list. When Lead creates a team (TeamCreate),
  all TaskGet/TaskUpdate calls operate on the team-scoped task list. Teammates cannot access
  the main PT.
- **Current workaround:** Lead embeds PT content directly in directive (CLAUDE.md §6)
- **Ideal solution:** CC CLI feature request for cross-scope task access, OR RSIL-level
  systematic directive template that always includes PT embedding
- **AD-15 Filter:** Category B (NL — directive template improvement) for now, Category C
  (Layer 2 — proper task scope management) for future

---

## 4. Design Questions for Brainstorming

These questions should be explored during `/brainstorming-pipeline` execution:

### Q-1: Skill or Integrated Step?
Should RSIL be a standalone skill (`/rsil-review`) or an integrated step within each
existing pipeline skill? Trade-off: standalone is cleaner but requires manual invocation;
integrated is automatic but adds ~50 lines to every skill.

### Q-2: Execution-Time Pattern Capture Mechanism
How should the Lead systematically capture execution-time patterns (EX-1~EX-4)?
Currently these are ad-hoc observations. Options:
- NL instruction in CLAUDE.md to "maintain an observation log during execution"
- Dedicated section in orchestration-plan.md for "execution observations"
- Post-phase micro-review (lighter than full RSIL)

### Q-3: claude-code-guide Research Scope
Should every RSIL execution spawn a claude-code-guide agent, or only when the meta-cognition
step identifies a specific CC-native capability gap? Trade-off: always-spawn ensures
comprehensive research but costs tokens; conditional-spawn is cheaper but may miss opportunities.

### Q-4: Tracker Architecture
Current tracker is a single markdown file. As data accumulates across sprints:
- Should it remain flat or split into per-sprint sections?
- Should there be a separate "applied" tracker for backlog items that have been implemented?
- How does the tracker relate to MEMORY.md (which should capture durable patterns)?

### Q-5: Convergence Analysis
The pilot data (8 findings, 50% acceptance) is too small for convergence analysis.
When is the right time to evaluate: after 20 findings? 50? Should the RSIL skill
include an automatic convergence check?

### Q-6: Integration with Layer 2
When the Ontology Framework (Layer 2) is built, how does RSIL evolve?
- Does Layer 2 provide structured quality tracking that replaces the markdown tracker?
- Do execution-time patterns (EX-1~EX-4) become systematic monitoring via Ontology?
- Is RSIL the bridge between "NL-based quality" (Layer 1) and "structured quality" (Layer 2)?

---

## 5. Reference Files

| File | Purpose | Lines |
|------|---------|-------|
| `docs/plans/2026-02-08-narrow-rsil-tracker.md` | Cumulative findings + workflow definition | ~190 |
| `.claude/projects/-home-palantir/memory/MEMORY.md` | "Narrow RSIL Process [PERMANENT]" section | ~15 |
| `.claude/projects/-home-palantir/memory/agent-teams-bugs.md` | BUG-001/002 details (EX-3 source) | ~30 |
| `.claude/CLAUDE.md` | Current infrastructure (v6.1, 172 lines) | 172 |
| `.claude/skills/brainstorming-pipeline/SKILL.md` | Pipeline skill pattern | ~350 |
| `docs/plans/2026-02-08-ontology-bridge-handoff.md` | Sibling handoff document pattern | ~420 |

---

## 6. Prerequisites for Brainstorming

- [ ] SKL-006 sprint complete (more data from Phase 6, 7-8 RSIL reviews)
- [ ] At least 12+ total findings (currently 8) for meaningful pattern analysis
- [ ] Analyze whether accepted findings (P4-R1/R2, P5-R1/R2) actually improved execution quality
  in later phases (Phase 6+ data needed)
- [ ] User decision on Q-1 (standalone skill vs integrated step)

---

## 7. Relationship to Other Pending Topics

```
Ontology Framework (T-1~T-4)          Narrow RSIL Skill
─────────────────────────────          ─────────────────
Layer 2 structured quality    ←─────── Layer 1 NL quality (bridge)
Execution monitoring           ←─────── Execution-time patterns (EX-1~4)
Audit trail / artifact registry ←───── Tracker / MEMORY.md
Domain-agnostic framework      ←─────── Pipeline-specific quality

Both topics feed each other:
- RSIL findings inform what Layer 2 needs to automate
- Layer 2 infrastructure enables RSIL to evolve beyond markdown tracking
```
