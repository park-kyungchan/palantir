# Decision 014: Observability & RTD Scalability

**Status:** PENDING USER DECISION  
**Date:** 2026-02-11  
**Context:** CLAUDE.md v6.0 · 4 hooks · RTD events.jsonl · 42 agents (D-005) · tmux  
**Depends on:** Decision 005, Decision 006

---

## 1. Problem Statement

The RTD (Real-Time Decisions) observability system captures tool calls via 
`on-rtd-post-tool.sh` (PostToolUse hook). Each tool call is logged as JSONL.

With D-005 expanding to 42 agents, each running in parallel tmux panes:
1. **Event volume increases** — 42 agents × avg 20 tool calls each = 840+ events per pipeline
2. **Session registry grows** — session-registry.json maps session IDs to agent names
3. **Events files proliferate** — one `.jsonl` file per session ID
4. **Execution monitor** reads these events for drift detection

**Core questions:**
- Does the current RTD architecture scale to 42 agents?
- Are there bottlenecks in the event pipeline at 42-agent scale?
- What changes are needed for Opus-4.6 Agent Teams on tmux?

---

## 2. Current RTD Architecture (Code-Level Audit)

### 2.1 Hook Pipeline (4 hooks)

| Hook | Event | Mode | Purpose | Lines |
|------|-------|------|---------|:-----:|
| `on-subagent-start.sh` | SubagentStart | sync | Log + session registry + context injection | 93 |
| `on-rtd-post-tool.sh` | PostToolUse | **async** | JSONL event capture (7 tool types) | 146 |
| `on-pre-compact.sh` | PreCompact | sync | Task snapshot + L1/L2 warning + RTD snapshot | 117 |
| `on-session-compact.sh` | SessionStart(compact) | sync | Recovery context injection | 54 |

### 2.2 Data Flow

```
Agent (tmux pane) → uses tool → Claude CLI fires PostToolUse hook
  → on-rtd-post-tool.sh (async, zero latency)
    → reads session_id, tool_name from stdin JSON
    → resolves agent name from session-registry.json
    → reads current DP from current-dp.txt
    → constructs JSONL event
    → appends to events/{session_id}.jsonl
```

### 2.3 Storage Layout

```
.agent/observability/
├── .current-project           ← project slug
└── {slug}/
    ├── session-registry.json  ← {session_id: {name, type}}
    ├── current-dp.txt         ← current Decision Point number
    ├── rtd-index.md           ← Decision Point journal
    ├── events/
    │   ├── {session-1}.jsonl  ← Lead's events
    │   ├── {session-2}.jsonl  ← Agent 1's events
    │   └── ...                ← one file per session
    └── snapshots/
        └── {timestamp}-pre-compact.json
```

### 2.4 Code Quality Assessment (from audit)

| File | Quality | Issues Found |
|------|---------|-------------|
| `on-rtd-post-tool.sh` | **HIGH** | Clean error handling, proper || exit 0 fallbacks, 7 tool-type parsers. Previously had set -e anti-pattern (F-007, fixed). |
| `on-subagent-start.sh` | **GOOD** | Session registry works. Had redundant jq check (fixed). Known limitation: maps Lead's SID to spawned agent. |
| `on-pre-compact.sh` | **GOOD** | Task snapshot + L1/L2 warning + RTD snapshot. Had ls anti-pattern (F-009, fixed) and redundant jq check (fixed). |
| `on-session-compact.sh` | **GOOD** | RTD-enhanced recovery with graceful degradation. Has manual JSON fallback for no-jq case. |

---

## 3. Scalability Analysis

### 3.1 Event Volume Projection

| Pipeline Tier | Agents | Avg Tools/Agent | Total Events | Events File Size |
|--------------|:---:|:---:|:---:|:---:|
| TRIVIAL (current) | 5-8 | 15 | ~100 | ~50 KB |
| STANDARD (current) | 12-18 | 20 | ~300 | ~150 KB |
| COMPLEX (D-005) | 30-42 | 25 | **~800-1000** | **~500 KB** |

**Verdict:** File I/O at 500 KB across 42 files is trivially within disk limits.
The async mode ensures zero latency impact. **NOT a bottleneck.**

### 3.2 Session Registry Scaling

```json
// session-registry.json with 42 agents:
{
  "session-abc123": {"name": "structure-architect", "type": "teammate"},
  "session-def456": {"name": "interface-architect", "type": "teammate"},
  // ... 42 entries
}
```

Current registry write pattern (on-subagent-start.sh):
```bash
jq '. + {($sid): {name: $name, type: $type}}' "$REGISTRY" > "$TMP" && mv "$TMP" "$REGISTRY"
```

**Concern:** With 42 concurrent agents, multiple `SubagentStart` hooks may fire nearly
simultaneously. Each reads the full JSON, adds entry, writes back. This is a classic
read-modify-write race condition.

**Severity:** LOW — SubagentStart hooks fire sequentially during Lead's spawn loop
(Lead spawns agents one-by-one in the Skill's spawn algorithm). Parallel spawning
is not supported in Agent Teams.

### 3.3 Execution Monitor Impact

`execution-monitor` reads events/*.jsonl to detect anomalies. With 42 agents:
- Monitor must Glob 42 .jsonl files
- Monitor must Read and parse each file for recent entries
- At 25 events per file, monitor reads ~1000 events per polling cycle

**Concern:** Monitor's polling cycle (Lead-specified cadence) may become expensive
with 42 files at ~25 entries each.

**Severity:** MEDIUM — Monitor currently runs on 1-2 minute intervals. Reading 42
small files is well within tmux session limits. But the USEFUL signals are increasingly
diluted in noise (routine Read/Grep tool calls).

### 3.4 Hook AD-15 Constraint

CLAUDE.md AD-15 prohibits adding new hooks. Current 4 hooks are the ceiling.
All observability improvements must work within existing hook events.

---

## 4. Identified Issues

### ISS-RTD-001: Session ID → Agent Name Resolution (Known, D-006 F-006)

**Problem:** `$CLAUDE_SESSION_ID` is not available in hook contexts. The SubagentStart
hook receives the PARENT's (Lead's) session_id, not the spawned agent's session_id.

**Result:** session-registry.json maps Lead's SID to agent names. When PostToolUse fires
for an agent's tool call, the SID may not match any registry entry → agent tagged as "lead".

**Current state:** Documented as a known limitation. Agent name resolution is best-effort.

**Impact with 42 agents:** More events tagged as "lead" when they should be tagged as
specific agents. Execution monitor's anomaly detection accuracy degrades.

**L1 mitigation:** None possible without $CLAUDE_SESSION_ID in hooks.
**L2 mitigation:** ActionType: TagEvent — associate events with agents via Ontology.

### ISS-RTD-002: No Event Aggregation

**Problem:** Events are raw JSONL. No aggregation layer exists. Execution monitor
must read and parse raw events on every polling cycle.

**L1 mitigation:** Add periodic aggregation script (via cron or monitor self-invoked).
But AD-15 prevents adding new hooks.

**Pragmatic L1 approach:** execution-monitor writes its own summary after each polling
cycle → `monitoring-summary.md`. Next cycle reads only NEW events (by tracking last-read
line count per file).

### ISS-RTD-003: No Event Pruning

**Problem:** Events accumulate indefinitely. A COMPLEX pipeline with 1000+ events 
creates 500+ KB of JSONL that grows across sessions.

**L1 mitigation:** delivery-pipeline Skill (Phase 9) archives events as part of
pipeline cleanup. Already done — events moved to archive directory.

**Post D-005:** Verify delivery-pipeline handles 42-agent event files correctly.

---

## 5. Recommended Changes

### 5.1 Execution Monitor Enhancement

Update `execution-monitor.md` to handle 42-agent scale:

```markdown
## Monitoring Loop Enhancement (D-014)

When monitoring 42 agents:
1. Read ALL events/*.jsonl files (Glob pattern)
2. For each file: read only lines beyond last-read checkpoint
3. Aggregate by agent name → tool type → count
4. Detect anomalies against EXPECTED patterns:
   - Implementer using Read-only tools for >80% of calls → drift alert
   - Agent with 0 events for >10 minutes → possible block
   - Agent modifying files not in ownership → ownership violation
5. Write monitoring-summary.md with per-agent status
6. Report anomalies to Lead via SendMessage
```

### 5.2 Session Registry Improvement (L1)

Add timestamp to registry entries for staleness detection:

```json
{
  "session-abc123": {
    "name": "structure-architect",
    "type": "teammate",
    "spawned_at": "2026-02-11T16:45:00Z"
  }
}
```

### 5.3 No New Hooks (AD-15 Compliant)

All improvements work within existing 4 hooks. No hook additions needed.

---

## 6. Options

### Option A: No Change (Current system sufficient)
- Trust async PostToolUse + execution-monitor as-is
- 42-agent scale is within current limits

### Option B: Execution Monitor Enhancement Only (Recommended)
- Update execution-monitor.md with §5.1 enhancements
- Add timestamp to session registry (§5.2)
- No structural changes to hook pipeline

### Option C: Event Aggregation Layer
- Add aggregation logic to execution-monitor
- Create per-pipeline summary files
- Higher complexity, moderate benefit

---

## 7. User Decision Items

- [ ] Which option? (A / **B recommended** / C)
- [ ] Accept ISS-RTD-001 as known limitation (L1 unfixable)?
- [ ] Accept execution-monitor enhancement for 42-agent polling?
- [ ] Accept timestamp addition to session registry?
- [ ] Confirm AD-15 (no new hooks) remains in effect?

---

## 8. Claude Code Directive (Fill after decision)

```
DECISION: RTD scalability — Option [X]
SCOPE:
  - execution-monitor.md: update monitoring loop for 42-agent scale
  - on-subagent-start.sh: add spawned_at timestamp to registry entries
  - delivery-pipeline/SKILL.md: verify 42-agent event archive handling
CONSTRAINTS:
  - AD-15: no new hooks
  - Async mode for PostToolUse preserved
  - ISS-RTD-001 accepted as known limitation
PRIORITY: Execution monitor > Session registry > Event aggregation
DEPENDS_ON: D-005 (agent count), D-006 (hook quality)
```
