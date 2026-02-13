# L2 Summary — Skill Duplication Analysis + GC Interface Mapping

## Summary

Analysis of all 9 SKILL.md files (4,426 lines total) reveals **~18.3% extractable duplication** (808 lines) across two categories: IDENTICAL text blocks (358L, 8.1%) that can be directly templated, and SIMILAR pattern sections (450L extractable, 10.2%) that share structure but vary in content. GC serves as a session-level state machine with a clear version chain (v1→v7), while PT serves as the project-level single source of truth. There is meaningful data overlap between the two, with 6 categories of duplicated data and clear migration candidates.

---

## Domain 1: Duplication Findings

### Highest-Value Extraction Targets (IDENTICAL)

| Section | Skills | Lines/Skill | Total Lines | Notes |
|---------|--------|-------------|-------------|-------|
| Phase 0 PT Check | 7 of 9 | ~30L | ~210L | Canonical flow with only destination variable |
| RTD Index instructions | 9 of 9 | ~8L | ~72L | Verbatim text; only DP list varies |
| Team Setup | 5 of 9 | ~5L | ~25L | TeamCreate + orchestration-plan pattern |
| Rollback Detection | 3 of 9 | ~5L | ~15L | Identical 3-line pattern |
| Sequential Thinking core | 9 of 9 | ~3L | ~27L | One-line MCP reference |
| Announce at start | 9 of 9 | ~1L | ~9L | Template: "I'm using {name} to..." |
| **Subtotal** | | | **~358L** | **8.1% of total** |

### Medium-Value Extraction Targets (SIMILAR)

| Section | Skills | Extractable % | Est. Lines | Notes |
|---------|--------|--------------|------------|-------|
| Input Discovery + Validation | 5 of 9 | 70% | ~140L | Common 5-step pattern; criteria unique |
| Error Handling | 9 of 9 | 50% | ~54L | 5 common entries across 7+ skills |
| Clean Termination | 5 of 9 | 60% | ~75L | 4-step pattern with variable content |
| Gate Evaluation structure | 5 of 9 | 40% | ~40L | Table format + audit clause identical |
| Key Principles | 9 of 9 | 40% | ~36L | 4 principles appear in 8+ skills |
| Never Section | 9 of 9 | 30% | ~22L | 5 items appear in 3+ skills |
| Compact Recovery | 7 of 9 | 50% | ~18L | Lead pattern identical; teammate varies |
| Spawn Patterns | 5 of 9 | 60% | ~24L | 4-param Task tool pattern identical |
| Understanding Verification | 4 of 9 | 50% | ~30L | Common 5-step flow; depth varies |
| Tier-Based Routing table | 4 of 9 | 70% | ~11L | Table structure identical |
| **Subtotal** | | | **~450L** | **10.2% of total** |

### Skill Groupings by Structure Similarity

**Pipeline Core Skills** (highest mutual duplication): brainstorming, write-plan, validation, execution, verification — share 15 of 19 section types

**Lead-Only Skills** (lower duplication): delivery, permanent-tasks — no spawn/team patterns

**RSIL Skills** (distinct structure): rsil-global, rsil-review — share Phase 0 and cross-cutting only; core logic is entirely unique (Tier system, Lens system)

### Section Presence Heatmap

```
Section                  BP WP PV EP VP DP RG RR PT
─────────────────────────── ── ── ── ── ── ── ── ──
Frontmatter              ✓  ✓  ✓  ✓  ✓  ✓  ✓  ✓  ✓
Phase 0 PT Check         S  I  I  I  I  I  I  I  —
Dynamic Context          U  U  U  U  U  U  U  U  U
When to Use              U  U  U  U  U  U  U  U  U
Announce at start        I  I  I  I  I  I  I  I  I
Input Discovery          —  S  S  S  S  S  —  —  —
Rollback Detection       —  —  I  I  I  —  —  —  —
Team Setup               I  I  I  I  I  —  —  —  —
Spawn Patterns           S  S  S  S  S  —  —  —  —
Tier-Based Routing       S  S  S  —  S  —  —  —  —
Understanding Verif      S  S  —  S  S  —  —  —  —
Gate Evaluation          S  S  S  S  S  —  —  —  —
Clean Termination        S  S  S  S  S  S  S  S  S
RTD Index                I  I  I  I  I  I  I  I  I
Sequential Thinking      I  I  I  I  I  I  I  I  I
Error Handling           S  S  S  S  S  S  S  S  S
Compact Recovery         S  S  S  S  S  S  —  S  —
Key Principles           S  S  S  S  S  S  S  S  S
Never Section            S  S  S  S  S  S  S  S  S

Legend: I=IDENTICAL, S=SIMILAR, U=UNIQUE, —=Absent
Skills: BP=brainstorming, WP=write-plan, PV=validation,
        EP=execution, VP=verification, DP=delivery,
        RG=rsil-global, RR=rsil-review, PT=permanent-tasks
```

### Unique Orchestration Logic Per Skill

Each skill has substantial unique logic that cannot be templated:

| Skill | Unique Lines (est.) | Key Unique Logic |
|-------|---------------------|------------------|
| brainstorming | ~400L | P1 Discovery, Q&A, Feasibility, Approach Exploration, P2 Research, P3 Architecture |
| write-plan | ~220L | Directive Construction (5-layer), 10-section template refs, Plan Generation |
| validation | ~280L | 6 Challenge Categories, Verdict flow (PASS/COND/FAIL), Re-verification |
| execution | ~480L | Adaptive Spawn Algorithm, Review Templates, Two-Stage Review, Cross-Boundary Escalation |
| verification | ~370L | Component Analysis, Test Design Protocol, Integration Protocol, Coordinator Transition |
| delivery | ~350L | Multi-session Discovery, 7 Ops (PT update, MEMORY migration, ARCHIVE, Git, PR, Cleanup) |
| rsil-global | ~340L | Three-Tier Observation, 5 Health Indicators, Lens Application, AD-15 Filter |
| rsil-review | ~400L | R-0 Lead Synthesis, Layer 1/2 Definitions, Integration Audit, Dual-Agent Research |
| permanent-tasks | ~200L | PT Discovery, Create/Update, Consolidation Rules, Template |

---

## Domain 2: GC Interface Mapping

### GC Version Chain

```
brainstorming  →  GC-v1 → GC-v2 → GC-v3
write-plan     →  reads v3, writes GC-v4
validation     →  reads v4, writes GC-v4/v5 (conditional)
execution      →  reads v4/v5, writes GC-v5/v6
verification   →  reads v5/v6, writes GC-v6/v7
delivery       →  reads PT (GC backup only)
rsil-*         →  no GC interaction
permanent-tasks → no GC interaction
```

### PT Version Chain

```
brainstorming  →  invokes /permanent-tasks → PT-v1
write-plan     →  PT-v{N} → PT-v{N+1}
validation     →  reads PT only
execution      →  PT-v{N} → PT-v{N+1}
verification   →  reads PT only
delivery       →  PT-v{N} → PT-v{final} ("DELIVERED")
rsil-review    →  updates PT Phase Status
permanent-tasks → creates or updates PT (any version)
```

### GC Section Dependencies (Cross-Skill)

| GC Section | Writer | Consumer(s) | Critical? |
|------------|--------|-------------|-----------|
| Scope | brainstorming G1 | write-plan V-3, validation V-4 | YES |
| Phase Pipeline Status | all gate phases | all downstream discovery | YES |
| Architecture Summary | brainstorming G3 | write-plan directive | YES |
| Architecture Decisions | brainstorming G3 | write-plan directive | YES |
| Phase 4 Entry Reqs | brainstorming G3 | write-plan V-3 | YES |
| File Ownership Map | write-plan G4 | execution §6.2-6.3 | YES |
| Task Decomposition | write-plan G4 | execution §6.2 | YES |
| Phase N Entry Conditions | each gate writer | next phase V-1 | MEDIUM |
| Research Findings | brainstorming G2 | general reference | LOW |
| Commit Strategy | write-plan G4 | delivery §9.3 | LOW |

### PT vs GC Data Overlap

6 data categories exist in both PT and GC with different authority levels:

1. **User Intent / Scope** — PT authoritative (GC is subset)
2. **Phase Status** — PT authoritative (delivery confirms)
3. **Architecture Decisions** — PT authoritative (GC may lag)
4. **Constraints** — PT authoritative (GC adds mitigations)
5. **File Ownership** — Split (PT has dependency graph, GC has task assignments)
6. **Implementation Plan** — Both (PT has summary, GC has path)

### GC-Only Data (14 section types)

Phase handoff sections (transient, consumed once by next phase):
- Research Findings, Codebase Constraints, Phase 3 Input
- Phase 4/5/6/7/9 Entry Requirements/Conditions
- Phase 5 Validation Targets

Execution metrics (recorded, not consumed by later phases):
- Implementation Results, Interface Changes, Verification Results
- Gate N Records (embedded summaries)
- Commit Strategy

### Migration Recommendations

**Should migrate to PT:**
1. Codebase Constraints → merge into PT §Constraints
2. Interface Changes → update PT §Codebase Impact Map

**Could be eliminated if skills read predecessor L2 directly:**
3. Phase N Entry Requirements (9 occurrences across GC versions) — these are mostly consumed once by the next phase and could be replaced by L2 Downstream Handoff sections

**Should remain in GC:**
4. Execution metrics (Implementation Results, Verification Results) — too verbose for PT
5. GC version marker — needed for Dynamic Context discovery

### Dual State Machine Architecture

```
        PT (Project Level)              GC (Session Level)
    ┌────────────────────────┐     ┌───────────────────────┐
    │ User Intent            │     │ Scope (subset of PT)  │
    │ Codebase Impact Map    │     │ Phase Pipeline Status │
    │ Architecture Decisions │     │ Phase Handoff Data    │
    │ Phase Status           │     │ Execution Metrics     │
    │ Constraints            │     │ Gate Records          │
    │ Budget Constraints     │     │ GC Version Marker     │
    └────────────────────────┘     └───────────────────────┘
         ↑                              ↑
         │ Authoritative for:           │ Authoritative for:
         │ - User intent                │ - Session artifacts
         │ - Impact map                 │ - Phase handoffs
         │ - Architecture decisions     │ - Execution metrics
         │ - Phase status               │ - GC version chain
         │ - Constraints                │
         │                              │
    Written by: permanent-tasks,    Written by: pipeline skills
    write-plan, execution, delivery at each gate transition
```

---

## Evidence Sources

- All 9 SKILL.md files read in full (brainstorming-pipeline 613L, agent-teams-write-plan 362L, plan-validation-pipeline 434L, agent-teams-execution-plan 692L, verification-pipeline 574L, delivery-pipeline 471L, rsil-global 452L, rsil-review 549L, permanent-tasks 279L)
- agent-common-protocol.md (247L) — L1/L2/L3 format, Downstream Handoff protocol
- CLAUDE.md §6 Agent Selection and Routing — coordinator management context
- Cross-referenced Phase 0 blocks across all skills for exact text comparison
- Cross-referenced GC write/read patterns across all gate transitions

---

## PT Goal Linkage

- R-1 (Skill Structure Analysis): Duplication matrix directly supports template extraction design
- R-2 (GC Interface Mapping): GC flow diagram enables state machine redesign
- AD-TBD (Shared Template vs Inline): duplication data quantifies extraction ROI
