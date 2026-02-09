# E2E Workflow Scenarios — COA-6~7

## Scenario 1: Teammate Spawn → SubagentStart Hook

```
Lead reads CLAUDE.md §6
  → Gate S-1: Requirements clear? PASS
  → Gate S-2: File count OK? PASS
  → Gate S-3: Not a re-spawn? N/A
  → SC-1: mode: "default" → Applied ✓
  → SC-2: Plan mode overridden → Confirmed ✓
Lead calls Task(mode: "default", subagent_type: "researcher", name: "researcher-code-audit", team_name: "coa-e2e")
  → Claude Code spawns agent process
  → SubagentStart hook fires
  → FIXED HOOK reads: agent_id="abc-123", agent_type="researcher"
  → Logs: [timestamp] SUBAGENT_START | id=abc-123 | type=researcher
  → Finds GC via filesystem heuristic → GC-v1
  → Outputs additionalContext: "[DIA-HOOK] Active team: coa-e2e. Current GC: GC-v1. Agent ID: abc-123..."
  → Teammate receives additionalContext
```
**Result:** Correct logging with real agent_id. GC version injected. No "unknown" entries.

## Scenario 2: Teammate Stops → SubagentStop Hook

```
Teammate finishes execution
  → SubagentStop hook fires
  → FIXED HOOK reads: agent_id="abc-123", agent_type="researcher", agent_transcript_path="/path/transcript.json"
  → Logs: [timestamp] SUBAGENT_STOP | id=abc-123 | type=researcher | transcript=/path/transcript.json
  → Outputs JSON: {agentId: "abc-123", agentType: "researcher", transcriptPath: "/path/..."}
  → NO false "stopped without L1/L2" warning (check removed)
  → L1/L2 enforcement already handled by TeammateIdle hook (fired earlier)
```
**Result:** Audit trail complete. Start/stop correlated by agent_id. Transcript path available for post-mortem.

## Scenario 3: Tool Failure → PostToolUseFailure Hook

```
Agent calls Read("/nonexistent/file.txt")
  → Read fails → PostToolUseFailure fires
  → FIXED HOOK: no set -euo pipefail → runs to completion
  → Reads: tool_name="Read", error="File not found"
  → NO agent_name attempt (field doesn't exist)
  → Finds active team dir via filesystem fallback
  → Logs: [timestamp] TOOL_FAILURE | tool=Read | error=File not found
  → If no team dir exists → logs to central $LOG_DIR/tool-failures.log (new fallback)
```
**Result:** Tool failure always logged. Never silently dropped. No misleading "agent=unknown".

## Scenario 4: New Session → Lead Reads CLAUDE.md with COA-6

```
New Lead session starts
  → Claude Code loads CLAUDE.md
  → Lead reads §6 Orchestrator Decision Framework
  → §6 Pre-Spawn Checklist: S-1 (ambiguity), S-2 (scope/BUG-002), S-3 (post-failure/BUG-002)
  → §6 Spawn Constraints: SC-1 (mode override/BUG-001), SC-2 (plan mode disabled/RTDI-009)
  → Lead KNOWS all three operational constraints from the authority file
  → No need to discover BUG-001 workaround from MEMORY.md or agent-teams-bugs.md
  → When spawning any teammate → SC-1 automatically applied
```
**Result:** BUG-001 knowledge persists across sessions via authority file. No knowledge loss on session boundaries.

## Scenario 5: Pre-Spawn Full Constraint Check

```
Lead needs to spawn implementer for Phase 6 (4 files to modify)
  → Gate S-1: "Implement COA hook fixes" — clear requirement → PASS
  → Gate S-2: 4 files (≤4 threshold) — within limits → PASS
  → Gate S-3: First spawn for this task → N/A
  → SC-1: mode: "default" → Task(mode: "default") ✓
  → SC-2: Implementer's agent.md has permissionMode: acceptEdits → already default-compatible ✓
  → Spawn proceeds
```
**Result:** Full gate + constraint check completed. All spawn-time rules in one section.

## Scenario 6: Researcher with mode: "default" → MCP Tools Accessible

```
Lead spawns researcher with mode: "default" (per SC-1)
  → researcher.md has: disallowedTools: [Edit, Write, Bash, TaskCreate, TaskUpdate]
  → researcher.md has: tools: [Read, Glob, Grep, WebSearch, WebFetch, TaskList, TaskGet]
  → Researcher calls mcp__sequential-thinking__sequentialthinking → SUCCEEDS ✓
  → Researcher calls mcp__tavily__search → SUCCEEDS ✓
  → Researcher calls mcp__context7__resolve-library-id → SUCCEEDS ✓
  → Researcher calls Edit → BLOCKED by disallowedTools ✓
  → Researcher calls Write → ALLOWED (L1/L2/L3 output) ✓
  → Researcher calls Bash → BLOCKED by disallowedTools ✓
```
**Result:** MCP tools work with mode: "default". Mutation tools blocked by disallowedTools. BUG-001 prevented.

## Scenario 7: SubagentStart/Stop Correlation via agent_id

```
SubagentStart fires for researcher → logs id=abc-123 | type=researcher
  ...researcher works for 30 minutes...
TeammateIdle fires → checks L1/L2 via teammate_name → enforces exit 2 if missing
  ...researcher writes L1/L2...
TeammateIdle fires again → L1/L2 exist → PASS (exit 0)
SubagentStop fires → logs id=abc-123 | type=researcher | transcript=/path/to/transcript

Admin can now:
1. Match start/stop by agent_id=abc-123
2. Calculate session duration from timestamps
3. Access full transcript at logged path
4. Verify L1/L2 enforcement happened (via TeammateIdle hook)
```
**Result:** Complete audit trail with lifecycle correlation, duration analysis, and transcript access.

## Cross-Impact Summary

| Scenario | COA-6 Impact | COA-7 Impact | Hooks Involved |
|----------|-------------|-------------|----------------|
| 1. Spawn | SC-1 applied | SubagentStart fixed | on-subagent-start.sh |
| 2. Stop | — | SubagentStop fixed | on-subagent-stop.sh |
| 3. Failure | — | ToolFailure fixed | on-tool-failure.sh |
| 4. New session | SC-1/SC-2 read | — | — (CLAUDE.md read) |
| 5. Pre-spawn | S-1/S-2/S-3 + SC-1/SC-2 | — | — (Lead decision) |
| 6. MCP access | SC-1 enables | — | — (mode: default) |
| 7. Correlation | — | Start+Stop fixed | on-subagent-start/stop.sh |
