# L2 Summary — Interface Architecture (PT-Centric Contract + §10 Modification)

## Summary

Designed the PT-centric interface contract for all 9 skills and the CLAUDE.md §10 modification for fork agent Task API access. PT becomes the sole cross-phase source of truth with lean pointers to L3 detail. GC reduces from 14 section types to 3 scratch concerns (execution metrics, gate records, version marker). L2 Downstream Handoff replaces 9 GC "Phase N Entry Requirements" sections as the phase-to-phase data bridge. The §10 modification is tightly scoped: 3 named fork agents (pt-manager, delivery-agent, rsil-agent) with explicit enumeration, frontmatter enforcement, and existing observability coverage for audit trail.

## Interface Analysis

### PT-Centric Model

Every skill's interface follows one of two patterns:

**Coordinator-based (5 Pipeline Core skills):**
- INPUT: PT (authoritative context) + predecessor coordinator L2 §Downstream Handoff (phase-specific entry data)
- OUTPUT: PT-v{N+1} (phase results as lean pointers) + own coordinator L2 §Downstream Handoff
- GC: Session scratch only (spawn state, timing)

**Fork-based (4 Lead-Only + RSIL skills):**
- INPUT: $ARGUMENTS (primary) + Dynamic Context (session state) + PT via TaskGet (cross-phase)
- OUTPUT: PT-v{N+1} (via TaskUpdate) + L1/L2/L3 files
- GC: No interaction

**DEPENDENCY — Fork PT access assumes shared task list (Open Question #3):**
The fork-to-PT interface (C-4) assumes fork agents see the main session's task list,
enabling TaskGet/TaskUpdate on the PERMANENT Task. This is unverified — P2 flagged
"Which task list does fork agent see?" as Critical Unknown #3. If fork agents see an
isolated task list, the entire fork-to-PT interface breaks. **Fallback:** Dynamic Context
injects PT content via `!command` pre-fork, but this makes PT read-only from the fork's
perspective (no TaskUpdate). This would require redesigning pt-manager and delivery-agent
to return PT changes as output text for Lead to apply manually.
Risk-architect-1's open question resolution should determine which path is viable.

### GC Migration Result

14 GC section types → **3 final steady-state** (after all gate transitions complete):
- 3 KEEP as scratch: execution metrics, gate record embeds, version marker
- 2 MIGRATE to PT at gate transitions: Codebase Constraints → PT §Constraints (at Gate 2), Interface Changes → PT §Impact Map (at Gate 6). These 2 sections exist transiently in GC until their respective gate writes them to PT, after which they are not carried forward in GC. The advertised "14→3" count reflects the final steady-state after pipeline completion.
- 9 ELIMINATE: Phase N Entry Requirements (×5), Validation Targets, Research Findings, Architecture Summary/Decisions, Task Decomposition, File Ownership → all replaced by L2 Downstream Handoff or PT pointers

### Skill Discovery Protocol

Old: GC version scan (`scans for global-context.md with "Phase N: COMPLETE"`)
New: PT query + L2 path (`TaskGet PT → phase_status.P{N}.l2_path → read L2 §Downstream Handoff`)

## Contract Definitions

### Per-Skill PT Read/Write Contract

| Skill | PT Reads | PT Writes | Version Bump |
|-------|----------|-----------|:------------:|
| brainstorming | User Intent (seed) | Creates full PT-v1 | v1 |
| write-plan | Impact Map, Arch Decisions, Constraints | Impl Plan pointer, File Ownership | v{N+1} |
| validation | Arch Decisions, Constraints, Impl Plan | Validation Verdict, (mitigations if COND) | v{N+1} |
| execution | Impact Map, Impl Plan, Constraints | Impl Results pointer | v{N+1} |
| verification | Impact Map, Impl Results | Verification Summary | v{N+1} |
| delivery [fork] | All sections | Final metrics, DELIVERED status | vFinal |
| permanent-tasks [fork] | Full PT (for merge) | Any section (user-directed) | v{N+1} |
| rsil-global [fork] | Phase Status, Constraints | None or findings (rare) | optional |
| rsil-review [fork] | Phase Status | RSIL results in Phase Status | v{N+1} |

### PT Schema (Lean Pointers)

PT description uses YAML structure with pointer fields:
- `phase_status.P{N}.l2_path` → path to coordinator L2 (discovery mechanism)
- `implementation_plan.l3_path` → path to planning L3 directory
- `implementation_results.l3_path` → path to execution L3 directory
- Bulk data stays in L3; PT holds 1-2 sentence summaries + paths

### GC Scratch Definition

GC retains only:
1. **Execution metrics:** spawn_count, spawn_log, timing — too verbose for PT
2. **Gate record embeds:** inline summaries — PT points to gate-record.yaml files
3. **Version marker:** gc_version — Dynamic Context reads for session discovery

No downstream skill reads GC for logic decisions. GC is write-once-read-never for
cross-phase purposes.

## §10 Modification Design

### Precise Change

**CLAUDE.md §10 first bullet** adds exception clause:
```
...except for Lead-delegated fork agents (pt-manager, delivery-agent, rsil-agent)
which receive explicit Task API access via their agent .md frontmatter.
```

With per-agent scope: pt-manager (Create+Update), delivery-agent (Update), rsil-agent (Update).

**agent-common-protocol.md §Task API** adds exception paragraph for fork-context agents.

### Scope Boundaries

- **Who:** Only 3 named agents (extensible only by updating CLAUDE.md §10)
- **How:** `disallowedTools` frontmatter omission (not platform change)
- **What:** PT operations only, defined by skill instructions
- **Enforcement:** 3 layers — frontmatter (primary), agent .md NL (secondary), CLAUDE.md §10 (tertiary)

### Audit & Safeguards

No new audit mechanism needed — PostToolUse hook captures all Task API calls to events.jsonl.
PT version chain provides operation log. Fork agents start clean (no context drift),
run only when Lead invokes skill (no autonomous activation), and have single-responsibility scope.

## Dependency Map

### L2 Handoff Chain (New Primary Data Path)

```
brainstorming → [research-coord/L2, arch-coord/L2]
  → write-plan → [planning-coord/L2]
    → validation → [validation-coord/L2]
      → execution → [exec-coord/L2]
        → verification → [testing-coord/L2]
          → delivery (terminal)
```

### Cardinality

- Skill→PT: N:1 (all read/write same PT)
- Skill→predecessor L2: 1:1 or 1:2 (execution reads 2)
- Fork→GC: 0 (complete decoupling)
- Fork→PT: 1:1 (direct TaskGet/TaskUpdate)

## PT Goal Linkage

| Decision | Design Contribution |
|----------|-------------------|
| D-7 (PT-centric) | Full per-skill read/write contract, PT schema, discovery protocol |
| D-10 (§10 modification) | Precise change text, scope boundaries, 3-layer enforcement |
| D-12 (Lean PT) | Pointer-based schema — bulk data in L3, PT holds summaries |
| D-14 (GC 14→3) | Complete migration map: 9 eliminate, 2 migrate, 3 keep |
| D-8 (Big Bang) | Simultaneous deployment analysis — no partial migration possible |

## Evidence Sources

| Source | What It Provided |
|--------|-----------------|
| Phase 2 research-coord/L2 | GC 14→3 migration path, skill family classification |
| Phase 2 codebase-researcher-1/L2+L3 | GC version chain, section dependency map, PT/GC overlap |
| Phase 2 codebase-researcher-2/L2 | Fork mechanism, D-10 design draft, Task API enforcement |
| Design doc §4 (PT-Centric Interface) | Target model, PT version chain |
| Design doc §9 (CC Research) | PT lean pointers recommendation, skill-to-skill handoff feasibility |
| CLAUDE.md §10 | Current rule text (lines 359-387) |
| agent-common-protocol.md §Task API | Current enforcement text (lines 72-76) |
| coordinator-shared-protocol.md §Handoff | Downstream Handoff 6-category structure |
