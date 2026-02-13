# L2 Summary — Interface Planner (Phase 4)

## Summary

Interface planner produced 6 deliverables for Phase 4 detailed design: §C Interface Section content for all 9 skills (hybrid Input/Output/Next format), PT Read/Write mapping per skill with version chain (PT-v1 through PT-vFinal), cross-file dependency matrix (22 files, 7 reference categories, 11 coupling dependencies), §10 modification exact text (CLAUDE.md + agent-common-protocol.md), GC migration per-skill specs (5 coordinator-based skills + delivery-pipeline GC fallback removal), and 4-way naming consistency contract (3 fork agents across 4 locations with validation checklist). All evidence extracted from direct reads of 9 SKILL.md files (4,430L total) plus 4 Phase 3 architecture L3/L2 files.

## §C Interface Section Design

### Format: Hybrid Input/Output/Next

All 9 skills get 3 fixed headers (Input, Output, Next) with variant-specific content:

**Coordinator-based (5 skills):** Input lists PT sections read + predecessor L2 path. Output lists PT sections written + L1/L2/L3 + gate records. Next names the successor skill and its entry requirements.

**Fork-based (4 skills):** Input lists $ARGUMENTS + Dynamic Context + PT (via TaskGet). Output lists PT update + file artifacts + terminal summary. Next is user-directed (fork skills are terminal or user-controlled). Each fork skill includes RISK-8 fallback delta.

### Key Design Decisions

1. **Input specificity:** Each skill names EXACT PT sections it reads (e.g., "§User Intent, §Codebase Impact Map, §Architecture Decisions, §Constraints") — not generic "reads PT."
2. **Output specificity:** Each skill names EXACT PT sections it writes and their new values (e.g., "adds §Implementation Plan with l3_path pointer") — auditable version chain.
3. **Next specificity:** Names the exact successor skill and what it needs in PT + L2 to start.
4. **RISK-8 fallback:** All 4 fork skills have explicit fallback behavior if task list is isolated. permanent-tasks is CRITICAL (highest impact), rsil-global is LOW (PT optional).

## PT Discovery Protocol

Replaces GC version scan with 5-step PT + L2 discovery:
1. TaskGet PT → read full content
2. Verify §phase_status.P{N-1}.status == COMPLETE
3. Read §phase_status.P{N-1}.l2_path → predecessor L2 location
4. Read predecessor L2 §Downstream Handoff
5. Validate entry conditions

Fork skills use simpler 4-step pattern (no L2 chain participation).

## §10 Modification

**CLAUDE.md §10:** Replace single-line Lead-only statement with 7-line exception clause naming pt-manager (TaskCreate+TaskUpdate), delivery-agent (TaskUpdate), rsil-agent (TaskUpdate).

**agent-common-protocol.md §Task API:** Append 4-line exception paragraph after existing text (additive, not replacement).

**3-layer enforcement:** Primary=disallowedTools frontmatter, Secondary=NL in agent .md, Tertiary=CLAUDE.md §10 policy.

## GC Migration

### Per-Skill Summary

| Skill | GC Writes Removed | GC Reads Replaced | GC Kept (scratch) |
|-------|:-----------------:|:-----------------:|:-----------------:|
| brainstorming | 6 sections (Gates 2-3) | 0 (pipeline start) | 3 sections (Gate 1) |
| write-plan | 6 sections (Gate 4) | 5 operations (discovery+directive) | 1 section (status) |
| validation | 2 sections (Gate 5) | 4 operations (discovery) | 1 section (status) |
| execution | 5 sections (termination) | 3 operations (discovery) | 2 sections (status+gate) |
| verification | 3 sections (Gates 7-8+term) | 2 operations (V-1+copy) | 1 section (status) |
| delivery | 0 (no GC writes) | 1 fallback REMOVED | 0 |

**Total:** 22 GC write sections removed, 15 GC read operations replaced, 8 GC scratch sections kept.

## Naming Contract

3 canonical names (pt-manager, delivery-agent, rsil-agent) enforced across 4 locations: skill `agent:` field, agent .md filename, CLAUDE.md §10, agent-common-protocol.md §Task API. Pre-deployment validation checklist (5 items) ensures consistency.

## Cross-File Dependency Matrix

22 files mapped across 7 reference categories:
- 5 TIGHT coupling dependencies (breaking change = cascade)
- 3 MEDIUM coupling dependencies (change requires coordination)
- 3 LOOSE coupling dependencies (independent change)

Highest coupling: PT section headers → all 9 skills. Fork `agent:` → agent .md filename.

## Downstream Handoff

### Decisions Made
- §C format: hybrid Input/Output/Next with variant-specific content
- §10 modification: additive exception clause (CLAUDE.md) + additive paragraph (protocol)
- GC migration: 22 writes removed, 15 reads replaced, 8 scratch kept
- Naming contract: 4-location enforcement with 5-item validation checklist
- PT discovery: 5-step protocol replaces GC scan for coordinator-based skills

### Interface Contracts Defined
- C-1: PT Read/Write (N:1) — per-skill exact sections mapped
- C-2: L2 Downstream Handoff Chain — 6 links, path pattern deterministic
- C-3: GC Scratch-Only — 3 concerns (metrics, gate records, version)
- C-4: Fork-to-PT Direct — 4 skills with RISK-8 fallback
- C-5: §10 Exception — 3 named agents, 3-layer enforcement
- C-6: 4-Way Naming — 3 agents × 4 locations consistency

### Constraints
- §C content is NEW for all 9 skills — no current structural home exists
- §10 modification must be CHARACTER-LEVEL precise (old→new replacement)
- GC migration is ALL-OR-NOTHING within Big Bang (D-8)
- Naming contract validation is pre-deployment GATE requirement

### Artifacts Produced
- `L3-full/dependency-matrix.md` (326L) — 8-section cross-file dependency matrix
- `L3-full/interface-design.md` (~350L) — §C content + §10 text + GC migration + naming contract
- `L1-index.yaml` — deliverable index with contract registry
- `L2-summary.md` (this file)
