---
version: GC-v1
created: 2026-02-11
feature: readme-infra-viz
complexity: STANDARD
---

# Global Context — README INFRA Visualization

## Scope
**Goal:** Rewrite README.md with comprehensive ASCII visualization of `.claude/` INFRA v9.0 — Architecture-First structure.

**In Scope:**
- Full `.claude/` directory tree visualization
- 43 agents (35W + 8C) across 14 categories
- 10 skills with phase mapping
- 4 hooks with lifecycle events
- 9 reference documents
- Settings (env, permissions, hooks, plugins)
- Observability (RTD) system structure
- Inter-component relationships

**Out of Scope:**
- Workspace projects (COW, Ontology, park-kyungchan/)
- `.agent/` runtime state details
- Historical versions
- Implementation guides

**Approach:** Architecture-First (big picture diagram → component detail sections)

**Success Criteria:**
- Every `.claude/` component represented with no omissions
- GitHub-renderable ASCII diagrams
- 30-second component lookup
- English primary, Korean annotations

## Phase Pipeline Status
- Phase 1: COMPLETE (Gate 1 APPROVED)
- Phase 2: PENDING
- Phase 3: PENDING

## Constraints
- Single file output (README.md)
- GitHub markdown rendering
- English primary, Korean secondary

## Decisions Log
| # | Decision | Rationale | Phase |
|---|----------|-----------|-------|
| D-1 | Architecture-First structure | Big picture → drill-down best for system comprehension | P1 |
| D-2 | .claude/ INFRA only scope | Focused, avoids scope creep into project-specific content | P1 |
