---
version: GC-v1
created: 2026-02-08
feature: coa-e2e-integration
complexity: COMPLEX
---

# Global Context — COA E2E Integration

## Scope
**Goal:** COA (Continuous Orchestration Awareness) — Agent Teams E2E workflow system Meta-Level integration design. Resolve 7 identified GAPs with code-level specifications across all infrastructure files.

**In Scope:**
- COA-1: Sub-Workflow Orchestration Plan (within-phase tracking protocol)
- COA-2: Self-Location Protocol ([SELF-LOCATE] obligation for all agents)
- COA-3: Continuous Documentation (upgrade from threshold-based to continuous enforcement)
- COA-4: Verification Continuity (mid-execution re-verification loops)
- COA-5: MCP Usage Verification (periodic triggers, not just "once per phase")
- COA-6: Operational Constraints consolidation (BUG-001/002, RTDI-009 → CLAUDE.md)
- COA-7: Hook bug fixes (ISSUE-001/002/003 from compatibility audit)
- 12+ E2E workflow scenarios traced through system with COA enforcement points
- Code-level specifications (exact file, section, content for every change)

**Out of Scope:**
- New hook events not in Claude Code v2.1.36
- New agent types (stick with 6)
- Skill restructuring (4 skills updated for COA compliance only)
- New MCP tools

**Approach:** Option B — Parallel Domain Split
- Phase 2: researcher-protocol (COA-1~5) + researcher-code-audit (COA-6~7) in parallel
- Phase 3: architect-1 synthesizes both into unified COA architecture

**Success Criteria:**
1. All 7 GAPs have code-level fix specifications (file, section, exact changes)
2. 12+ E2E workflow scenarios traced with COA enforcement points
3. No conflict with existing DIA protocol
4. Hook fixes validated against Claude Code v2.1.36 schema
5. Architecture document ready for Phase 4 input

## Phase Pipeline Status
- Phase 1: COMPLETE (Gate 1 APPROVED 2026-02-08)
- Phase 2: IN_PROGRESS
- Phase 3: PENDING

## Constraints
- Max 3 teammates at any time
- All teammates: mode "default" (BUG-001: plan mode blocks MCP tools)
- Pre-Spawn Checklist: Gate S-1/S-2/S-3 mandatory
- L3-full/ completeness mandated for all researchers (user requirement)
- Lead Meta-Cognition: MEMORY + sequential-thinking for every orchestration decision (user mandate)

## Decisions Log
| # | Decision | Rationale | Phase |
|---|----------|-----------|-------|
| D-1 | Option B: Parallel Domain Split | Speed + L3 depth = Option A thoroughness | P1 |
| D-2 | Lead Meta-Cognition Obligation | User mandate: MEMORY + sequential-thinking for all Lead orchestration decisions | P1 |
| D-3 | L3 completeness mandate | User: "files 기반으로 L3파일까지 확인하도록 하면 Option A만큼의 철저함" | P1 |

## Infrastructure Inventory (files subject to COA changes)
### Authority Files
- `.claude/CLAUDE.md` (v5.0, 381 lines)
- `.claude/references/task-api-guideline.md` (v5.0, 537 lines)

### Agent Definitions (6 files)
- `.claude/agents/researcher.md` (143 lines)
- `.claude/agents/architect.md` (160 lines)
- `.claude/agents/devils-advocate.md` (127 lines)
- `.claude/agents/implementer.md` (179 lines)
- `.claude/agents/tester.md` (154 lines)
- `.claude/agents/integrator.md` (185 lines)

### Hook Scripts (8 files)
- `.claude/hooks/on-subagent-start.sh` (46 lines) — ISSUE-001
- `.claude/hooks/on-subagent-stop.sh` (48 lines) — ISSUE-001
- `.claude/hooks/on-tool-failure.sh` (28 lines) — ISSUE-002
- `.claude/hooks/on-teammate-idle.sh` (46 lines) — OK
- `.claude/hooks/on-task-completed.sh` (51 lines) — OK
- `.claude/hooks/on-task-update.sh` (31 lines) — OK
- `.claude/hooks/on-pre-compact.sh` (40 lines) — OK
- `.claude/hooks/on-session-compact.sh` (25 lines) — OK

### Skills (4 files)
- `.claude/skills/brainstorming-pipeline/SKILL.md`
- `.claude/skills/agent-teams-write-plan/SKILL.md`
- `.claude/skills/agent-teams-execution-plan/SKILL.md`
- `.claude/skills/plan-validation-pipeline/SKILL.md`

### Settings
- `.claude/settings.json` (133 lines)

### Reference Design
- `docs/plans/2026-02-08-opus46-compatibility-audit.md` (hook schema + fix specs)

## GAP Definitions (for researcher reference)

### COA-1: Sub-Workflow Orchestration Plan
- Problem: orchestration-plan.md tracks phase-level only. Within P6 with 3 implementers, no formal sub-workflow tracking.
- Location: CLAUDE.md §6 + orchestration-plan.md structure

### COA-2: Self-Location Protocol
- Problem: No obligation for agents to periodically confirm their position in the pipeline.
- Location: CLAUDE.md §4 Communication Protocol (new format needed)

### COA-3: Continuous Documentation
- Problem: §9 says "proactively throughout execution" but no enforcement mechanism.
- Location: CLAUDE.md §9 + agent .md files + hooks

### COA-4: Verification Continuity
- Problem: DIA verification is entry-gate only. No mid-execution re-verification.
- Location: CLAUDE.md [PERMANENT] + task-api-guideline.md §11

### COA-5: MCP Usage Verification
- Problem: §7 says "Required = at least once per phase". No periodic triggers.
- Location: CLAUDE.md §7 + agent .md execution phases

### COA-6: Operational Constraints Consolidation
- Problem: BUG-001, BUG-002, RTDI-009 not in CLAUDE.md (authority file).
- Location: CLAUDE.md (new section or integrated into existing)
- Sources: MEMORY.md, memory/agent-teams-bugs.md, GC-v7 (RTDI Sprint)

### COA-7: Hook Bug Fixes
- Problem: ISSUE-001 (SubagentStart/Stop), ISSUE-002 (tool-failure), ISSUE-003 (missing transcript_path)
- Location: 3 hook scripts
- Reference: docs/plans/2026-02-08-opus46-compatibility-audit.md §8-§10
