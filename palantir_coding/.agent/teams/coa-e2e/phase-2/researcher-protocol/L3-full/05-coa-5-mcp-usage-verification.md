# COA-5: MCP Usage Verification — Complete Specification

## Problem Statement

**Gap:** §7 says "Required = must use at least once during the phase." No periodic triggers enforce this.

**Current State:**
- CLAUDE.md §7 (lines 229-256): MCP Tools table defines Required/As needed per phase per tool.
- "Required" definition (line 255): "must use at least once during the phase."
- Agent .md execution phases: Mention specific MCP tools ("Use mcp__xxx for...") but no frequency tracking.
- L2-summary.md reporting: "Teammates report MCP tool usage in their L2-summary.md" (line 256) — but only at completion, no intermediate checkpoint.
- No mechanism to detect a teammate at 80% task completion with zero MCP calls in a Required phase.

**Impact of Gap:** A researcher in Phase 2 (where tavily and context7 are Required) could complete research using only local file reads, never verifying against external documentation. The "Required" obligation is checked only in L2 at completion — too late to improve the research quality. Similarly, an implementer could write code without checking latest API docs (context7), only discovering version mismatches in Phase 7 testing.

## Proposed Protocol

### Design Philosophy
COA-5 is a **specialized check type within the COA-4 re-verification framework**, not a standalone protocol. It uses COA-2 self-location as its data source and COA-4 re-verification as its enforcement mechanism.

### MCP Usage Tracking (via COA-2)

The `MCP: {count}` field in [SELF-LOCATE] carries cumulative MCP tool call count per teammate session. This provides real-time visibility without requiring separate tracking.

**MCP Status Classification:**
| Status | Condition | Lead Action |
|--------|-----------|-------------|
| ACTIVE | Required tools used, count growing with work | None |
| LOW | Required tools used but count seems low relative to progress | Note in sub-workflow, monitor |
| MISSING | MCP count = 0 AND task progress > 50% AND phase has Required tools | Trigger COA-4 RV-2 |
| EXEMPT | Phase marks all tools as "As needed" and agent determined no need | None |

### Phase-Based MCP Expectations

Derived from CLAUDE.md §7 table, with added milestone expectations:

| Phase | Required Tools | Expected Minimum by 50% | Expected Minimum by Completion |
|-------|---------------|--------------------------|-------------------------------|
| P2 (Research) | tavily, context7, github | 2 calls (any Required tool) | 3 calls (at least 1 per Required tool) |
| P3 (Architecture) | tavily | 1 call | 1 call |
| P4 (Design) | tavily, context7 | 1 call | 2 calls (1 per Required tool) |
| P5 (Validation) | — (all As needed) | 0 (exempt) | 0 (exempt) |
| P6 (Implementation) | context7 | 1 call | 1 call |
| P7 (Testing) | — (all As needed) | 0 (exempt) | 0 (exempt) |
| P8 (Integration) | — (all As needed) | 0 (exempt) | 0 (exempt) |

### Re-Verification Trigger (within COA-4)

When Lead detects MISSING status from COA-2 data:

```
[REVERIFY] Phase {N} | Level 2 | Target: {role-id} | Reason: MCP usage below minimum (COA-5) | Question: Your MCP tool count is {count} at {progress}% task completion. Phase {N} requires {tool_list}. Explain why external verification tools are not needed for your current work, or use them to verify your findings.
```

**Expected response types:**
1. **Justified exemption:** "I'm working on local file analysis that doesn't require external verification. Context7/tavily not applicable to this sub-task." → Lead evaluates, accepts or pushes back.
2. **Acknowledged gap:** "I should have used context7 to verify the API signatures. Doing that now." → Teammate uses tools, reports findings in next [SELF-LOCATE].
3. **Defensive response:** "I used WebSearch instead of tavily." → Lead notes tool substitution (acceptable fallback per researcher MEMORY.md).

### L2 Intermediate MCP Reporting

In addition to final L2 MCP reporting, teammates should include intermediate MCP usage in their checkpoint L2 updates (tied to COA-3 documentation checkpoints):

```markdown
## MCP Tools Usage (Intermediate — Task {T}/{total})
| Tool | Calls | Key Findings |
|------|-------|-------------|
| sequential-thinking | 5 | Used for gap analysis, protocol design |
| tavily | 2 | Verified heartbeat protocol patterns, multi-agent best practices |
| context7 | 0 | Not yet needed — will use for library docs in next task |
```

### Token Cost Analysis

- MCP field in [SELF-LOCATE]: 0 additional tokens (already included in COA-2 format)
- RV-2 MCP trigger: ~300 tokens (same as standard COA-4 RV-2)
- Intermediate L2 MCP section: ~100 tokens per checkpoint
- Total: ~400 additional tokens per teammate with MCP issues; 0 for compliant teammates
- Net: Almost zero standalone cost — COA-5 leverages COA-2 and COA-4 infrastructure

## Integration Points

### 1. CLAUDE.md §7 — Add Verification Triggers Subsection

**Current text (lines 254-256):**
```markdown
"Required" = must use at least once during the phase. "As needed" = use when relevant.
Teammates report MCP tool usage in their L2-summary.md.
```

**Proposed replacement:**
```markdown
"Required" = must use at least once during the phase. "As needed" = use when relevant.
Teammates report MCP tool usage in their L2-summary.md (intermediate + final).

**Verification (COA-5):** MCP usage count is carried in [SELF-LOCATE] MCP field.
If MCP count = 0 at >50% task progress in a Required phase, Lead triggers COA-4 RV-2
to verify whether external tools are needed. Justified exemptions are acceptable;
unjustified gaps require immediate tool usage.
```

### 2. Agent .md Execution Phases — MCP Reporting in Self-Locate

**For all 6 agent .md, the [SELF-LOCATE] instruction (from COA-2) already includes MCP field.**
No additional change needed beyond COA-2 integration.

**For agents in Required phases (researcher, architect, implementer):**
Add to execution phase instructions:
```markdown
- Include MCP usage summary in intermediate L2 updates (COA-3 checkpoints)
```

### 3. L2-summary.md Template — Intermediate MCP Section

No file change needed — this is a content guideline already implied by "report MCP tool usage in L2."
COA-3 documentation checkpoints ensure intermediate L2 updates exist where MCP sections can be included.

## Conflict Analysis

| Existing Protocol | Conflict? | Analysis |
|-------------------|-----------|----------|
| CLAUDE.md §7 MCP table | EXTENDS | Adds verification triggers. "Required = once per phase" unchanged. |
| L2 MCP reporting | EXTENDS | Adds intermediate reporting. Final reporting unchanged. |
| COA-2 Self-Location | DEPENDS ON | Uses MCP field as data source. No conflict — cooperative design. |
| COA-4 Re-Verification | CONTAINED IN | MCP check is a specific RV-2 trigger type. Follows same escalation. |
| Agent .md tool lists | NO CONFLICT | Tool availability unchanged. Only usage frequency monitoring added. |
| BUG-001 (plan mode blocks MCP) | NO CONFLICT | COA-5 monitors MCP usage, doesn't change mode. Workaround (mode: default) still applies. |

## Scenario: MCP Gap Detection in Phase 2

```
T+0:   researcher-1 spawned for Phase 2 research. Required: tavily, context7, github.
T+5:   researcher-1 verified, begins research.
T+10:  [SELF-LOCATE] Phase 2 | Task 1/1 | Step: reading infrastructure files | Progress: 30% | MCP: 0 | Docs: current
       → Lead sub-workflow: MCP = 0 at 30%. Below 50% threshold — monitor but no trigger.
T+20:  [SELF-LOCATE] Phase 2 | Task 1/1 | Step: analyzing gap patterns | Progress: 55% | MCP: 0 | Docs: current
       → Lead sub-workflow: MCP = 0 at 55%. ABOVE 50% threshold in Required phase.
       → COA-5 triggers COA-4 RV-2:
       [REVERIFY] Phase 2 | Level 2 | Target: researcher-1 | Reason: MCP usage below minimum (COA-5) | Question: Your MCP tool count is 0 at 55% completion. Phase 2 requires tavily, context7, and github. Explain why external verification is not needed, or use these tools now.
T+21:  researcher-1: [REVERIFY-RESPONSE] Phase 2 | Level 2 | I've been focused on local infrastructure file analysis. I should use tavily to verify my protocol design patterns against industry best practices, and context7 to check if Claude Code has relevant API documentation. Doing that now.
T+25:  [SELF-LOCATE] Phase 2 | Task 1/1 | Step: cross-referencing with external docs | Progress: 65% | MCP: 3 | Docs: current
       → Lead: MCP count now 3, actively using tools. Status → ON_TRACK.
```
