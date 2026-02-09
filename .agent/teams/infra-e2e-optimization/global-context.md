---
version: GC-v1
project: INFRA End-to-End Verification & Optimization
pipeline: Simplified Infrastructure (Phase 6 → 6.V → 9)
current_phase: 6
---

# Global Context — INFRA E2E Optimization

## Project Summary
Optimize Agent Teams infrastructure for Opus 4.6: fix critical safety issues (WS-1) and
structurally reduce instruction overhead by ~33% (WS-2). Two independent workstreams,
zero file overlap, parallel execution.

## Design Reference
- Implementation plan: `/home/palantir/.claude/plans/soft-mapping-swan.md`
- Current CLAUDE.md: v5.0 (DIA v5.0)
- Current task-api-guideline.md: v4.0

## Key Design Decisions
- Opus 4.6 natural language over rigid protocol formatting
- Single authoritative statement per rule (no redundancy)
- Shared reference file (agent-common-protocol.md) for deduplication
- Mechanical enforcement (frontmatter) over instructional redundancy
- ~2400 → ~1600 lines total instruction reduction target

## Workstream Structure
- WS-1: Safety Fixes — 8 files (settings.json + 7 hooks)
- WS-2: Structural Optimization — 8 files (1 CREATE + 6 agent .md + CLAUDE.md)
- Zero file overlap between workstreams

## Scope
- Files modified: 15 (7 hooks + settings.json + CLAUDE.md + 6 agent .md)
- Files created: 1 (agent-common-protocol.md)
- Hooks added: 0

## Active Teammates
- implementer-ws1: WS-1 Safety Fixes (Tasks #1-#5)
- implementer-ws2: WS-2 Structural Optimization (Tasks #6-#8)

## Phase Status
- Phase 6 (Implementation): IN_PROGRESS
- Phase 6.V (Verification): PENDING (Task #9)
- Phase 9 (Delivery): PENDING (Task #10)

## [PERMANENT] User Requirements (Real-Time Captured)
1. Use Task API for comprehensive task tracking (ToDoWrite)
2. Lead must follow CLAUDE.md protocol strictly
3. [PERMANENT] section compiled after all tasks complete
4. [PERMANENT] serves as Lead reference for Teammates Management + overall guidelines
5. Work can be split freely — orchestrate with dependency chain awareness
6. User wants Real-Time-Dynamic-Impact-Awareness (RTDIA)
