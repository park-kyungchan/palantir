# Domain 2: GC Consumption Interface Mapping

## GC Read/Write Inventory Per Skill

### 1. brainstorming-pipeline

**GC Reads:** None (creates GC-v1 at Gate 1; reads its own GC-v1 at 2.1 for Research Needs)
**GC Writes:**
- Gate 1 (1.5): Creates GC-v1 — `version`, `pt_version`, `created`, `feature`, `tier` frontmatter + Scope, Phase Pipeline Status, Constraints, Decisions Log
- Gate 2 (2.5): GC-v1 → GC-v2 — adds Research Findings, Codebase Constraints, Phase 3 Input
- Gate 3 (3.4): GC-v2 → GC-v3 — adds Architecture Summary, Architecture Decisions table, Phase 4 Entry Requirements

**PT Reads:** Phase 0 search; uses PT context alongside Dynamic Context
**PT Writes:** Invokes /permanent-tasks at Gate 1 to create PT-v1 (indirect)

**Internal GC Read (self-referencing):**
- §2.1 reads GC-v1 "Phase 2 Research Needs" to determine research scope

### 2. agent-teams-write-plan

**GC Reads:**
- §4.1 Discovery: scans for `global-context.md` with `Phase 3: COMPLETE`
- §4.1 Validation: V-1 checks GC exists with Phase 3 COMPLETE; V-3 checks GC-v3 contains Scope, Component Map, Interface Contracts
- §4.3 Directive: embeds entire GC-v3 in architect directive

**GC Writes:**
- Gate 4 (4.5) On APPROVE: GC-v3 → GC-v4 — adds Implementation Plan Reference, Task Decomposition, File Ownership Map, Phase 6 Entry Conditions, Phase 5 Validation Targets, Commit Strategy; updates Phase Pipeline Status

**PT Reads:** Phase 0 check; PT provides additional context for architect
**PT Writes:** Gate 4 (4.5): PT-v{N} → PT-v{N+1} with Implementation Plan Reference, Task Decomposition summary, File Ownership Map, Phase 4 COMPLETE status

### 3. plan-validation-pipeline

**GC Reads:**
- §5.1 Discovery: scans for `global-context.md` with `Phase 4: COMPLETE`
- §5.1 Validation: V-1 checks GC exists with Phase 4 COMPLETE; V-4 checks GC-v4 contains Scope, Phase 4 decisions, implementation task breakdown

**GC Writes:**
- Gate 5 (5.5) On APPROVE:
  - If PASS: Add Phase 5 status only (GC stays at v4)
  - If CONDITIONAL_PASS with mitigations: GC-v4 → GC-v5, adds accepted mitigations to Constraints; updates Phase Pipeline Status

**PT Reads:** Phase 0 check; PT provides context for challenge execution
**PT Writes:** None explicitly (no PT update mentioned in Gate 5 On APPROVE)

### 4. agent-teams-execution-plan

**GC Reads:**
- §6.1 Discovery: scans for `global-context.md` with `Phase 4: COMPLETE` or `Phase 5: COMPLETE`
- §6.1 Validation: V-1 checks GC exists with Phase 4 or 5 COMPLETE

**GC Writes:**
- Gate 6 (6.7) Clean Termination: GC-v4 → GC-v5 (or GC-v5 stays) — adds Phase 6 COMPLETE status, Implementation Results, Interface Changes, Gate 6 Record, Phase 7 Entry Conditions

**PT Reads:** Phase 0 check; PT provides Impact Map for understanding verification
**PT Writes:** Gate 6 (6.7): PT-v{N} → PT-v{N+1} with implementation results and Phase 6 COMPLETE status

### 5. verification-pipeline

**GC Reads:**
- §7.1 Discovery: scans for `phase-6/gate-record.yaml` with `result: APPROVED`
- §7.1 Validation: V-1 checks GC exists with `Phase 6: COMPLETE`

**GC Writes:**
- Gate 7 (7.5) On APPROVE: Add Phase 7 COMPLETE status
- Gate 8 (8.3) On APPROVE: Add Phase 8 COMPLETE or SKIPPED status
- Clean Termination: Adds Verification Results, Phase 9 Entry Conditions

**PT Reads:** Phase 0 check; PT content embedded in coordinator directives
**PT Writes:** None explicitly (no PT update mentioned)

### 6. delivery-pipeline

**GC Reads:**
- §9.1 Discovery: reads GC as backup to PT for Phase 7/8 status
- §9.1 Validation: V-1 checks PT or GC for Phase 7/8 COMPLETE (PT takes precedence)

**GC Writes:** None explicitly (delivery focuses on PT final update, ARCHIVE, and git)

**PT Reads:** Phase 0 check; §9.1 reads PT for session references; §9.2 Op-1 reads PT for final update
**PT Writes:** §9.2 Op-1: Final PT update — adds metrics, marks all phases COMPLETE, bumps to PT-v{final}, changes subject to "DELIVERED"

### 7. rsil-global

**GC Reads:** None (reads session artifacts and git diffs directly)
**GC Writes:** None
**PT Reads:** Phase 0 check; extracts pipeline context for observation classification
**PT Writes:** None

### 8. rsil-review

**GC Reads:** None
**GC Writes:** None
**PT Reads:** Phase 0 check
**PT Writes:** §R-4: Updates PT Phase Status with RSIL results (if PT exists)

### 9. permanent-tasks

**GC Reads:** None (manages PT only)
**GC Writes:** None
**PT Reads:** Step 1 discovery; Step 2B.1 reads current PT
**PT Writes:** Step 2A creates PT-v1; Step 2B.3 updates PT-v{N} → PT-v{N+1}

---

## GC Version Flow Diagram

```
PIPELINE FLOW:

brainstorming-pipeline
  │
  ├─ Gate 1 (1.5): Creates GC-v1
  │   Sections: frontmatter + Scope + Pipeline Status + Constraints + Decisions Log
  │
  ├─ Gate 2 (2.5): GC-v1 → GC-v2
  │   Adds: Research Findings + Codebase Constraints + Phase 3 Input
  │
  └─ Gate 3 (3.4): GC-v2 → GC-v3
      Adds: Architecture Summary + Architecture Decisions + Phase 4 Entry Requirements
                │
                ▼
agent-teams-write-plan
  │
  ├─ §4.1: READS GC-v3 (Phase 3 COMPLETE, Scope, Components, Interfaces)
  ├─ §4.3: EMBEDS entire GC-v3 in architect directive
  │
  └─ Gate 4 (4.5): GC-v3 → GC-v4
      Adds: Impl Plan Reference + Task Decomposition + File Ownership
            + Phase 6 Entry + Phase 5 Targets + Commit Strategy
                │
                ▼
plan-validation-pipeline
  │
  ├─ §5.1: READS GC-v4 (Phase 4 COMPLETE, Scope, Decisions, Tasks)
  │
  └─ Gate 5 (5.5): GC-v4 → GC-v4 (PASS) or GC-v4 → GC-v5 (CONDITIONAL_PASS)
      Adds (if cond): Accepted mitigations to Constraints
                │
                ▼
agent-teams-execution-plan
  │
  ├─ §6.1: READS GC-v4/v5 (Phase 4 or 5 COMPLETE)
  │
  └─ Gate 6 (6.7): GC-v4/v5 → GC-v5/v6
      Adds: Phase 6 COMPLETE + Impl Results + Interface Changes
            + Gate 6 Record + Phase 7 Entry Conditions
                │
                ▼
verification-pipeline
  │
  ├─ §7.1: READS GC-v5/v6 (Phase 6 COMPLETE)
  │
  ├─ Gate 7 (7.5): Adds Phase 7 COMPLETE status
  ├─ Gate 8 (8.3): Adds Phase 8 COMPLETE/SKIPPED status
  │
  └─ Clean Term: Adds Verification Results + Phase 9 Entry Conditions
                │
                ▼
delivery-pipeline
  │
  ├─ §9.1: READS PT (primary) or GC (backup) for Phase 7/8 status
  │
  └─ No GC writes (focuses on PT final update + ARCHIVE + git)


SEPARATE FLOWS (no GC interaction):

rsil-global     → Reads session artifacts + git diffs directly
rsil-review     → Reads target files directly
permanent-tasks → Manages PT only (no GC awareness)
```

---

## PT Version Flow Diagram

```
brainstorming-pipeline
  └─ Gate 1 (1.5): Invokes /permanent-tasks → Creates PT-v1
                      │
                      ▼
agent-teams-write-plan
  └─ Gate 4 (4.5): PT-v{N} → PT-v{N+1}
      Adds: Impl Plan Reference + Task Decomposition + File Ownership + Phase 4 COMPLETE
                      │
                      ▼
plan-validation-pipeline
  └─ (No PT write — reads only)
                      │
                      ▼
agent-teams-execution-plan
  └─ Gate 6 (6.7): PT-v{N} → PT-v{N+1}
      Adds: Impl Results + Phase 6 COMPLETE
                      │
                      ▼
verification-pipeline
  └─ (No PT write — reads only)
                      │
                      ▼
delivery-pipeline
  └─ §9.2 Op-1: PT-v{N} → PT-v{final}
      Adds: Final metrics + all phases COMPLETE + "DELIVERED" suffix
                      │
                      ▼
rsil-review (optional)
  └─ §R-4: Updates PT Phase Status with RSIL results
```

---

## GC Section Dependency Map

Shows which GC sections are written by one skill and read by downstream skills.

```
GC Section                  | Writer (Phase)    | Reader(s) (Phase)
─────────────────────────────────────────────────────────────────────
Scope                       | brainstorming G1  | write-plan §4.1, validation §5.1
Phase Pipeline Status       | brainstorming G1  | ALL downstream (status check)
Constraints                 | brainstorming G1  | validation §5.5 (mitigations added)
Decisions Log               | brainstorming G1  | (general reference)
Research Findings           | brainstorming G2  | (general reference)
Codebase Constraints        | brainstorming G2  | (general reference)
Phase 3 Input               | brainstorming G2  | (general reference)
Architecture Summary        | brainstorming G3  | write-plan §4.3 (embedded in directive)
Architecture Decisions      | brainstorming G3  | write-plan §4.3 (embedded in directive)
Phase 4 Entry Requirements  | brainstorming G3  | write-plan §4.1 V-3
Implementation Plan Ref     | write-plan G4     | execution §6.1, validation §5.1
Task Decomposition          | write-plan G4     | execution §6.2
File Ownership Map          | write-plan G4     | execution §6.2, §6.3
Phase 6 Entry Conditions    | write-plan G4     | execution §6.1 V-1
Phase 5 Validation Targets  | write-plan G4     | validation §5.4
Commit Strategy             | write-plan G4     | delivery §9.3
Implementation Results      | execution G6      | verification §7.1
Interface Changes           | execution G6      | verification §7.4
Gate 6 Record               | execution G6      | verification §7.1 V-2
Phase 7 Entry Conditions    | execution G6      | verification §7.1
Verification Results        | verification term | delivery §9.1
Phase 9 Entry Conditions    | verification term | delivery §9.1
```

---

## PT vs GC Data Analysis

### Data Currently in Both PT and GC

| Data | PT Location | GC Location | Authoritative? |
|------|-------------|-------------|----------------|
| User Intent | §User Intent | §Scope | PT (GC is subset) |
| Phase Status | §Phase Status | §Phase Pipeline Status | PT (delivery §9.1 confirms) |
| Architecture Decisions | §Architecture Decisions | §Architecture Decisions + §Decisions Log | PT (GC may have older version) |
| Constraints | §Constraints | §Constraints | PT (GC adds mitigations) |
| File Ownership | §Codebase Impact Map | §File Ownership Map | Split (PT has dependencies, GC has assignments) |
| Impl Plan Reference | §description | §Implementation Plan Reference | Both (PT has summary, GC has path) |

### Data Only in GC (not in PT)

| Data | GC Section | Why not in PT? |
|------|------------|----------------|
| Research Findings | §Research Findings | Phase-specific, consumed by P3 only |
| Codebase Constraints | §Codebase Constraints | Discovered constraints, should merge into PT Constraints |
| Phase 3 Input | §Phase 3 Input | Transient P2→P3 handoff |
| Architecture Summary | §Architecture Summary | Design detail, too verbose for PT |
| Phase 4 Entry Requirements | §Phase 4 Entry Requirements | Transient P3→P4 handoff |
| Phase 5 Validation Targets | §Phase 5 Validation Targets | Transient P4→P5 handoff |
| Phase 6 Entry Conditions | §Phase 6 Entry Conditions | Transient P4→P6 handoff |
| Phase 7 Entry Conditions | §Phase 7 Entry Conditions | Transient P6→P7 handoff |
| Phase 9 Entry Conditions | §Phase 9 Entry Conditions | Transient P7→P9 handoff |
| Implementation Results | §Implementation Results | Execution metrics |
| Interface Changes | §Interface Changes | Deviations from plan |
| Gate Records (embedded) | §Gate N Record | Verification details |
| Verification Results | §Verification Results | Test metrics |
| Commit Strategy | §Commit Strategy | Delivery-specific |

### Data Only in PT (not in GC)

| Data | PT Section | Why not in GC? |
|------|------------|----------------|
| Codebase Impact Map | §Codebase Impact Map | PT is the source of truth; used for verification questions |
| Budget Constraints | §Budget Constraints | Pipeline-scoped, not phase-scoped |
| Ripple Paths / Risk Hotspots | §Codebase Impact Map | Cross-phase concern |

### Migration Candidates (GC → PT)

Based on the "authoritative source" analysis:

1. **Codebase Constraints** (from GC Research Findings) → should merge into PT §Constraints when discovered
2. **Interface Changes** (from GC Phase 6) → should update PT §Codebase Impact Map
3. **Phase N Entry Requirements** sections → these are transient handoff data. Could be replaced by:
   - PT §Phase Status with more structured entry/exit criteria
   - Or eliminated entirely if skills read predecessor L2 directly

### GC's Remaining Value (if PT absorbs authoritative data)

GC would still serve as:
1. **Session artifact container** — holds phase-specific transient data that doesn't belong in PT
2. **Version marker** — GC-v{N} tracks session progression (readable by Dynamic Context)
3. **Phase handoff data** — "Phase N Entry Requirements" are consumed once and discarded
4. **Execution metrics** — Implementation Results, Verification Results (summary goes to PT at delivery)

---

## Cross-Skill GC Dependency Chain

```
                 brainstorming-pipeline
                ┌─────────┼─────────┐
              GC-v1     GC-v2     GC-v3
                │         │         │
                │         │    ┌────┘
                │         │    │
                │         │  write-plan reads GC-v3
                │         │    │
                │         │  GC-v4
                │         │    │
                │         │  ┌─┴──────────┐
                │         │  │            │
                │         │  validation   execution
                │         │  reads v4     reads v4/v5
                │         │  │            │
                │         │  GC-v4/v5     GC-v5/v6
                │         │               │
                │         │          verification
                │         │          reads v5/v6
                │         │               │
                │         │          GC-v6/v7
                │         │               │
                │         │          delivery
                │         │          reads PT (GC backup)
```

Critical dependency: **Every pipeline skill after brainstorming depends on GC created by brainstorming.** The GC is the session-level state machine. PT is the project-level context.
