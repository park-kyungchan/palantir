# L2-summary.md — researcher-code-audit (COA-6~7)

**Status:** COMPLETE
**GC Version:** GC-v1
**Phase:** 2 (Deep Research)

## Executive Summary

Complete code-level audit of COA-6 (operational constraints consolidation) and COA-7 (hook bug fixes). All 8 hook scripts validated against Claude Code v2.1.36 official schema. Three broken hooks have validated, copy-paste-ready fix code. CLAUDE.md placement architecture designed with Gate vs Constraint taxonomy — no duplication.

## COA-6: Operational Constraints Consolidation

### Placement Decision
New "Spawn Constraints (Permanent)" subsection within CLAUDE.md §6, placed after Pre-Spawn Checklist gates and before Spawn Matrix.

### Taxonomy
- **Gates (S-*):** Conditional checks evaluated per-spawn (S-1, S-2, S-3) — UNCHANGED
- **Constraints (SC-*):** Fixed rules that always apply (SC-1, SC-2) — NEW

### Constraint Mapping
| Bug | Constraint | Placement | Rationale |
|-----|-----------|-----------|-----------|
| BUG-001 | SC-1: Mode Override | §6 Spawn Constraints | Always spawn with mode: "default" — spawn-time rule |
| BUG-002 | Already in S-2/S-3 | §6 Pre-Spawn Checklist | No change — complete coverage, no duplication |
| RTDI-009 | SC-2: Plan Mode Disabled | §6 Spawn Constraints | Consequence of SC-1 — plan mode permanently overridden |

### Key Design Principle
CLAUDE.md owns the RULE. MEMORY.md owns the diagnostic HISTORY. Cross-reference, not duplication.

## COA-7: Hook Bug Fixes

### Drift Check
**Zero drift.** All 3 broken hooks' current code exactly matches audit doc "Current Code (BROKEN)" sections.

### Fix Validation (per-hook)

| Hook | Issue | Fix | Schema Fields Used | Validated |
|------|-------|-----|-------------------|-----------|
| on-subagent-start.sh | ISSUE-001: non-existent agent_name, tool_input.* | Use agent_id, agent_type; filesystem GC heuristic | agent_id, agent_type | Yes |
| on-subagent-stop.sh | ISSUE-001+003: non-existent fields, broken L1/L2 check | Use agent_id, agent_transcript_path; remove L1/L2 check | agent_id, agent_type, agent_transcript_path | Yes |
| on-tool-failure.sh | ISSUE-002: non-existent agent_name, dangerous set -euo pipefail | Remove agent_name and set flags; add fallback logging | tool_name, error, tool_input | Yes |

### L1/L2 Check Removal Justification (SubagentStop)
- Check was ALWAYS failing (used non-existent fields → 100% false warnings)
- TeammateIdle hook already enforces L1/L2 (exit 2, correct fields)
- TaskCompleted hook already enforces L1/L2 (exit 2, correct fields)
- SubagentStop cannot block (agent already stopped)

### 5 Working Hooks
All verified correct: on-teammate-idle.sh, on-task-completed.sh, on-task-update.sh, on-pre-compact.sh, on-session-compact.sh. No changes needed.

## E2E Workflow Scenarios (7 traced)

1. **Teammate spawn** → SC-1 applied → SubagentStart logs real agent_id → GC injected
2. **Teammate stop** → SubagentStop logs agent_id + transcript_path → no false warnings
3. **Tool failure** → Hook runs to completion → failure always logged
4. **New session** → Lead reads SC-1/SC-2 from CLAUDE.md → BUG-001 knowledge preserved
5. **Pre-spawn check** → Gates S-1/S-2/S-3 + Constraints SC-1/SC-2 in one section
6. **Researcher MCP access** → mode: "default" enables MCP → disallowedTools blocks mutations
7. **Start/Stop correlation** → Same agent_id in both events → transcript path for post-mortem

## Additional Findings

- **No undocumented operational constraints found** beyond BUG-001/002/RTDI-009
- **No additional hook issues** beyond ISSUE-001/002/003
- **settings.json** all 8 hook configs structurally valid
- **agent_type occasionally empty** on some SubagentStop events (runtime behavior, handled by fallback)

## Cross-Impact Matrix

| Finding | CLAUDE.md | Hooks | settings.json | Agent .md | Skills |
|---------|-----------|-------|---------------|-----------|--------|
| COA-6 SC-1/SC-2 | §6 addition | — | — | — | — |
| COA-7 ISS-001 start | — | Replace file | — | — | — |
| COA-7 ISS-001 stop | — | Replace file | — | — | — |
| COA-7 ISS-002 | — | Replace file | — | — | — |

## Recommendations for Architect (Phase 3)

1. **COA-6 implementation:** Insert "Spawn Constraints (Permanent)" text from L3-full/COA-6-claude-md-placement.md into CLAUDE.md §6 (after line 158, before Spawn Matrix)
2. **COA-7 implementation:** Replace 3 hook files with copy-paste code from L3-full/COA-7-hook-fix-*.sh
3. **Log format migration:** No migration needed (old logs were all "unknown")
4. **Verification:** Spawn a test subagent after fix to verify new log format

## L3-full/ Contents

| File | Purpose |
|------|---------|
| COA-6-claude-md-placement.md | Exact CLAUDE.md text + insertion point |
| COA-7-hook-fix-subagent-start.sh | Copy-paste-ready fixed hook |
| COA-7-hook-fix-subagent-stop.sh | Copy-paste-ready fixed hook |
| COA-7-hook-fix-tool-failure.sh | Copy-paste-ready fixed hook |
| COA-7-change-rationale.md | Line-by-line change rationale for all 3 hooks |
| current-hooks-reference.md | Complete current code of all 8 hooks (pre-fix snapshot) |
| e2e-scenarios.md | 7 E2E workflow scenario traces |

## MCP Tools Usage Report

| Tool | Used | Purpose |
|------|------|---------|
| sequential-thinking | Yes (8 steps) | Execution planning, hook validation (3 hooks), working hook verification, undocumented constraint search, placement architecture, E2E scenarios |
| tavily | No | Schema already verified in audit doc; no external validation needed beyond existing reference |
| context7 | No | No library documentation lookup needed for hook scripts |
| github | No | No cross-repo search needed |

## Sources Read

- All 8 hook scripts (.claude/hooks/*.sh)
- CLAUDE.md v5.0 (381 lines)
- settings.json (134 lines)
- opus46-compatibility-audit.md (931 lines)
- MEMORY.md (~83 lines)
- agent-teams-bugs.md (34 lines)
- TEAM-MEMORY.md (24 lines)
