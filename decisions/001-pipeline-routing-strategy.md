# Decision 001: Phase Pipeline Routing Strategy

**Status:** PENDING USER DECISION  
**Date:** 2026-02-11  
**Context:** CLAUDE.md v6.0 · Agent Teams · 22 Agents · 10 Categories  
**Question:** Should the Phase Pipeline operate as Real-Time-Dynamic (RTD), follow a fixed Skill-Driven Workflow, or use a hybrid approach?

---

## 1. As-Is Analysis

### 1.1 Current System is a Skill-Driven + Lead Discretion Hybrid

The infrastructure analysis reveals the current architecture is neither pure RTD nor pure fixed pipeline:

| Aspect | Current Implementation | Evidence |
|--------|----------------------|----------|
| **Phase Order** | Fixed (P2→P2b→P2d→P3→P4→P5→P6→P7→P8→P9) | CLAUDE.md Line 19: explicit dependency chain |
| **Phase Skipping** | Possible at Lead discretion | No explicit skip criteria defined |
| **Skill Invocation** | User manually selects (`/brainstorming-pipeline`, `/agent-teams-write-plan`, etc.) | Each Skill's "When to Use" section |
| **Agent Selection** | Lead applies §6 Selection Flow | Category matching → Agent selection (reactive) |
| **Dependency Enforcement** | Gate evaluation blocks/permits phase transitions | Gate criteria defined per Skill |

### 1.2 Core Problems

```
User Prompt ──→ [Lead Interpretation] ──→ Which Skill?
                        │
                        ├── "Refactor X" → User calls /brainstorming-pipeline?
                        │                  Or jump to /agent-teams-execution-plan?
                        │                  Lead decides by itself?
                        │
                        └── ❌ No explicit routing logic exists
                            Relies on Lead's "free discretion"
```

**Problem A: No Phase Skip Criteria**
- Must a single-line code fix traverse P2→P3→P4→P5?
- CLAUDE.md states "Phase 0 (~500 tokens) is a lightweight prerequisite" — no fast-path defined for trivial work.

**Problem B: Skill ↔ Phase Mapping is Distributed**
- `/brainstorming-pipeline` = P0-P3
- `/agent-teams-write-plan` = P4
- `/plan-validation-pipeline` = P5
- `/agent-teams-execution-plan` = P6-P8
- `/delivery-pipeline` = P9
- User must know this sequence. Lead does not auto-chain (explicitly prohibited by all Skills).

**Problem C: No Complexity-Based Path Branching**
- SIMPLE/MEDIUM/COMPLEX classification happens at Phase 1.4 (Scope Crystallization).
- This classification has zero effect on which phases to execute or which to skip.

---

## 2. Options

### Option A: Full RTD (Real-Time Dynamic Pipeline)

**Summary:** Lead constructs a dynamic Phase graph per user request.

```
User Prompt
     │
     ↓
[Lead Analysis] ── sequential-thinking ──→ Request complexity analysis
     │
     ↓
┌───────────────────────────────────────────────┐
│  Dynamic Phase Graph Construction              │
│                                                │
│  "Which Phases does THIS request require?"     │
│                                                │
│  ✅ P2 Research    (confidence LOW → needed)   │
│  ❌ P2b Verify     (internal code → skip)      │
│  ❌ P2d Impact     (single file → skip)        │
│  ❌ P3 Arch        (existing arch preserved)   │
│  ❌ P4 Plan        (scope < 3 files)           │
│  ❌ P5 Validate    (skip)                      │
│  ✅ P6 Implement   (core work)                 │
│  ✅ P7 Test        (verify changes)            │
│  ❌ P8 Integrate   (single implementer)        │
│  ✅ P9 Delivery    (commit required)           │
└───────────────────────────────────────────────┘
     │
     ↓
  Custom Pipeline: P2 → P6 → P7 → P9
```

**Changes Required:**
- Add Phase Selection Matrix to CLAUDE.md §2
- Define Skip Criteria per Phase
- Introduce Skill auto-chaining (currently explicitly prohibited)
- Inject dynamic pipeline context via `on-subagent-start.sh`

**Pros:**
- Pipeline optimized per request — unnecessary Phases eliminated
- "One-line fix" and "full refactor" take different paths
- Maximizes Lead's orchestration capability

**Cons:**
- Over-reliance on LLM judgment for routing → consistency risk
- Phase skip errors are expensive to recover (e.g., skipping P3 causes architecture conflict)
- Debugging difficulty — "why was this Phase skipped?" requires trace
- Conflicts with auto-chaining prohibition (a core design principle in all Skills)

**Best for:** Highly experienced users, frequent small tasks, speed-optimized workflows.

---

### Option B: Tiered Fixed Pipelines (Complexity-Based Fixed Paths)

**Summary:** Pre-defined paths selected by complexity tier (TRIVIAL/SIMPLE/MEDIUM/COMPLEX).

```
User Prompt
     │
     ↓
[Lead Analysis] ── sequential-thinking ──→ Complexity classification
     │
     ├── TRIVIAL (≤1 file, clear fix)
     │     Pipeline: P6 → P9
     │     Skill:    /quick-fix (new)
     │
     ├── SIMPLE (2-3 files, single module)
     │     Pipeline: P2 → P6 → P7 → P9
     │     Skill:    /simple-pipeline (new)
     │
     ├── MEDIUM (4-8 files, multi-module)
     │     Pipeline: P2 → P3 → P4 → P6 → P7 → P9
     │     Skill:    Existing Skills in sequence
     │
     └── COMPLEX (9+ files, architecture change)
           Pipeline: P2 → P2b → P2d → P3 → P4 → P5 → P6 → P7 → P8 → P9
           Skill:    Full Pipeline (unchanged)
```

**Changes Required:**
- Add Complexity-Pipeline Mapping Table to CLAUDE.md §2
- Create 2 new lightweight Skills (quick-fix, simple-pipeline)
- No changes to existing Skills (MEDIUM/COMPLEX use current pipeline)
- Strengthen complexity classification logic in Phase 0

**Pros:**
- Predictable — same complexity = same pipeline
- Minimizes LLM judgment dependency (one classification decision only)
- Easy to debug — "SIMPLE tier, so this path was taken"
- No conflict with existing Skills or auto-chaining prohibition
- Dramatically reduces overhead for small tasks

**Cons:**
- Edge cases at tier boundaries ("SIMPLE but needs architecture decision")
- Misclassification risk — insufficient pipeline for actual complexity
- Requires 2 new Skill files (initial investment)

**Best for:** Stable operations, mixed task sizes, team scaling.

---

### Option C: Adaptive Gates (Current + Skip Conditions at Gates)

**Summary:** Fixed order preserved, but each Gate evaluates "should next Phase be skipped?"

```
User Prompt
     │
     ↓
  Current flow: P0 → P1 start
     │
     ↓
  Gate 1 evaluation:
     ├── G1-SKIP: "Is P2 Research needed?"
     │     ├── YES → proceed to P2
     │     └── NO  → skip P2, jump to P3 (or P6)
     │
  Gate 2 evaluation:
     ├── G2-SKIP: "Is P2b Verification needed?"
     │     ├── YES → proceed to P2b
     │     └── NO  → jump to P3
     ...
```

**Changes Required:**
- Add "Skip Condition" (G{N}-SKIP) to each Skill's Gate criteria
- Add `skipped_phases` field to Gate Record YAML
- Document skippable Phases in CLAUDE.md §2
- Existing Skill structure largely preserved

**Pros:**
- Minimal change — existing infrastructure mostly preserved
- Reuses Gate verification mechanism
- Order maintained while skipping unnecessary Phases
- Traceability maintained — Gate Record captures skip reasoning

**Cons:**
- Skip evaluation overhead at every Gate (Lead token consumption)
- P0→P1 always required (even TRIVIAL tasks go through Phase 1 Q&A)
- Cumulative skips can approximate Option A behavior (defeats predictability)
- "P1-free jump to P6" is impossible in this structure

**Best for:** Incremental improvement from current state, minimal risk.

---

## 3. Comparison Matrix

| Criterion | Option A (Full RTD) | Option B (Tiered) | Option C (Adaptive Gates) |
|-----------|:---:|:---:|:---:|
| Speed optimization | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| Predictability | ⭐ | ⭐⭐⭐ | ⭐⭐ |
| Existing INFRA compatibility | ⭐ | ⭐⭐ | ⭐⭐⭐ |
| Implementation complexity | HIGH | MEDIUM | LOW |
| LLM judgment dependency | HIGH | LOW (1 decision) | MEDIUM |
| Debuggability | ⭐ | ⭐⭐⭐ | ⭐⭐ |
| TRIVIAL task efficiency | ⭐⭐⭐ | ⭐⭐⭐ | ⭐ |
| COMPLEX task safety | ⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

---

## 4. Recommendation

**Option B (Tiered Fixed Pipelines)** is recommended.

**Rationale:**
1. Complexity classification already exists at Phase 1.4 — connecting it to pipeline selection is natural
2. TRIVIAL/SIMPLE lightweight Skills dramatically improve daily task speed
3. COMPLEX retains the full existing pipeline — no safety regression
4. Lead's LLM judgment dependency is minimized to a single classification decision
5. No conflict with auto-chaining prohibition
6. Two new Skills (quick-fix, simple-pipeline) are bounded, well-defined deliverables

---

## 5. User Decision Items

- [ ] **Option A** — Full RTD (Real-Time Dynamic Pipeline)
- [ ] **Option B** — Tiered Fixed Pipelines (RECOMMENDED)
- [ ] **Option C** — Adaptive Gates (minimal change)
- [ ] **Hybrid A+B** — TRIVIAL/SIMPLE use Option B, MEDIUM/COMPLEX use Option A
- [ ] **Other** — alternative direction

After selection, this file will be passed to Claude Code to build the implementation plan for the chosen option.

---

## 6. Claude Code Directive (Fill after decision)

```
DECISION: Option [A/B/C/Hybrid]
SCOPE: CLAUDE.md §2 modification + [required Skill creation/modification list]
CONSTRAINTS:
  - Existing Skill phase ordering preserved
  - Auto-chaining prohibition preserved
  - Gate Records must include routing decision
  - brainstorming-pipeline excluded from this decision (marked for separate enhancement)
PRIORITY: [Speed / Safety / Predictability]
```
