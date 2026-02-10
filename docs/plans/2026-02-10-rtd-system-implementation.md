# INFRA v7.0 — RTD System Implementation Plan

> Phase 4 Detailed Design | architect-1 | PT-v3 | 2026-02-10

**Goal:** Implement 4-layer Real-Time-Documenting system (events.jsonl, rtd-index.md,
enhanced DIA, precision recovery) across 23 files with ~355 lines of changes.

**Design Source:** `.agent/teams/rtd-system/phase-3/architect-1/L3-full/architecture-design.md`

---

## 1. Executive Summary

| Item | Value |
|------|-------|
| Feature | INFRA v7.0 — RTD System (4-layer observability) |
| Complexity | MEDIUM-HIGH (23 files, 5 groups, shell + markdown) |
| Implementers | 2 (zero file overlap: Hooks+Config vs Documentation) |
| Estimated lines | ~355 (200 hook/config + 35 CLAUDE.md/protocol + 60 skills + 20 agents + 40 bootstrap) |
| New files | 1 (on-rtd-post-tool.sh) + 3 bootstrap templates |
| Modified files | 19 (4 hooks/config + 2 CLAUDE.md/protocol + 7 skills + 6 agents) |
| Key risk | Recovery hook rewrite (on-session-compact.sh) — mitigated by graceful degradation |
| Architecture decisions | AD-22~28 (7 decisions) |
| Requirements | R-1~R-7 (real-time monitoring, drill-down, code completeness, session independence, shared capture, causation chain, Lead omniscience) |

---

## 2. Architecture Reference

- **Full architecture:** `.agent/teams/rtd-system/phase-3/architect-1/L3-full/architecture-design.md` (1240 lines, 16 sections)
- **L2 summary:** `.agent/teams/rtd-system/phase-3/architect-1/L2-summary.md`
- **PERMANENT Task:** Task #1, PT-v3
- **Key ADs:** AD-22 (scope isolation), AD-23 (session registry 3-tier), AD-24 (DP signal), AD-25 (recovery priority), AD-26 (project-scoped directory), AD-27 (templated skill RTD), AD-28 (async PostToolUse)
- **Constraints:** C-1 (existing hooks safe), C-2 (minimal overhead), C-3 (machine-parseable), C-4 (CC hooks API), C-5 (YAGNI), C-6 (graceful degradation), C-7 (cohesive INFRA)

Do NOT re-specify architecture. Read the L3 for details.

---

## 3. File Ownership Map

### Implementer 1: Hooks + Config (Groups A + E)

| File | Operation | Lines | Group |
|------|-----------|-------|-------|
| `.claude/hooks/on-rtd-post-tool.sh` | CREATE | ~100 | A |
| `.claude/hooks/on-subagent-start.sh` | EXTEND | +15 | A |
| `.claude/hooks/on-pre-compact.sh` | EXTEND | +25 | A |
| `.claude/hooks/on-session-compact.sh` | REWRITE | ~55 | A |
| `.claude/settings.json` | MODIFY | +10 | A |
| `.agent/observability/.current-project` | TEMPLATE | 1 | E |
| `.agent/observability/{slug}/manifest.json` | TEMPLATE | ~15 | E |
| `.agent/observability/{slug}/rtd-index.md` | TEMPLATE | ~20 | E |
| **Total** | | **~240** | |

### Implementer 2: Documentation (Groups B + C + D)

| File | Operation | Lines | Group |
|------|-----------|-------|-------|
| `.claude/CLAUDE.md` | MODIFY | +20 | B |
| `.claude/references/agent-common-protocol.md` | MODIFY | +15 | B |
| `.claude/skills/brainstorming-pipeline/SKILL.md` | MODIFY | +10 | C |
| `.claude/skills/agent-teams-write-plan/SKILL.md` | MODIFY | +10 | C |
| `.claude/skills/plan-validation-pipeline/SKILL.md` | MODIFY | +10 | C |
| `.claude/skills/agent-teams-execution-plan/SKILL.md` | MODIFY | +10 | C |
| `.claude/skills/verification-pipeline/SKILL.md` | MODIFY | +10 | C |
| `.claude/skills/delivery-pipeline/SKILL.md` | MODIFY | +10 | C |
| `.claude/skills/permanent-tasks/SKILL.md` | MODIFY | +8 | C |
| `.claude/agents/researcher.md` | MODIFY | +3 | D |
| `.claude/agents/architect.md` | MODIFY | +3 | D |
| `.claude/agents/implementer.md` | MODIFY | +3 | D |
| `.claude/agents/tester.md` | MODIFY | +3 | D |
| `.claude/agents/devils-advocate.md` | MODIFY | +3 | D |
| `.claude/agents/integrator.md` | MODIFY | +3 | D |
| **Total** | | **~121** | |

---

## 4. Task Decomposition

### Implementer 1 Tasks

#### T-1: Create PostToolUse Hook Script (Group A)

**File:** `.claude/hooks/on-rtd-post-tool.sh` (NEW, ~100 lines)
**Dependency:** None (foundational)
**Blocks:** T-3, T-4
**Acceptance Criteria:**
1. AC-0: Read §5 spec A1. Verify actual PostToolUse hook input format matches expected schema before writing event parsing logic. Log a sample `$INPUT` to a temporary file on first run to validate.
2. Script creates events directory if missing (`mkdir -p`)
3. Reads `.current-project` for project slug, falls back to "default"
4. Reads `session-registry.json` for agent name, falls back to "lead" (if not found)
5. Reads `current-dp.txt` for current DP, falls back to `null`
6. Produces valid 8-field JSONL events per §4.1 schema
7. Tool-specific summarization matches §4.2 for Write, Edit, Read, Bash, Glob, Grep, Task, Other
8. Each event is < 2000 bytes
9. All errors exit 0 (never blocks pipeline)
10. Script is executable (`chmod +x`)

#### T-2: Extend Existing Hook Scripts + Config (Group A)

**Files:**
- `.claude/hooks/on-subagent-start.sh` (EXTEND, +15 lines)
- `.claude/hooks/on-pre-compact.sh` (EXTEND, +25 lines)
- `.claude/settings.json` (MODIFY, +10 lines)

**Dependency:** None (independent of T-1)
**Blocks:** T-3
**Acceptance Criteria:**
1. AC-0: Read current on-subagent-start.sh (67 lines) and on-pre-compact.sh (65 lines). Verify insertion points match the expected line context before editing.
2. on-subagent-start.sh: RTD session registry write added after line 20 (after logging, before context injection). Uses `$AGENT_NAME` and `$AGENT_TYPE` already parsed.
3. on-pre-compact.sh: RTD state snapshot added before `exit 0`. Produces `{ts}-pre-compact.json` in snapshots/ directory.
4. settings.json: PostToolUse entry added with `async: true`, `timeout: 5`, empty matcher. Existing 3 entries UNCHANGED.
5. All additions fail silently (no exit code > 0 on failure)
6. jq availability checked before use

#### T-3: Rewrite Session Compact Hook (Group A)

**File:** `.claude/hooks/on-session-compact.sh` (REWRITE, ~55 lines)
**Dependency:** T-1 (PostToolUse creates events that recovery reads), T-2 (SubagentStart populates registry)
**Blocks:** None
**Acceptance Criteria:**
1. AC-0: Read current on-session-compact.sh (25 lines). Understand the exact current behavior before replacing. The new version must produce identical additionalContext JSON structure.
2. RTD-enhanced recovery reads .current-project → rtd-index.md frontmatter → builds precise recovery message
3. Graceful degradation: if no RTD data available, produces IDENTICAL output to current v6.2 script
4. additionalContext string < 1000 chars
5. JSON output structure matches current: `{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}`
6. Exit 0 always

#### T-4: Create Bootstrap Templates (Group E)

**Files:**
- `.agent/observability/.current-project` (TEMPLATE, 1 line)
- `.agent/observability/{slug}/manifest.json` (TEMPLATE, ~15 lines)
- `.agent/observability/{slug}/rtd-index.md` (TEMPLATE, ~20 lines)

**Dependency:** T-1 (hooks need directory structure to exist)
**Blocks:** None
**Acceptance Criteria:**
1. AC-0: Read existing pilot files at `.agent/observability/rtd-system/`. Templates must be compatible with but not overwrite the pilot data.
2. Templates are documentation — these are the REFERENCE formats for Lead initialization, not files that implementers create for real projects
3. .current-project template shows single-line format
4. manifest.json template matches §4.6 schema
5. rtd-index.md template matches §4.3 format with frontmatter
6. NOTE: The actual rtd-system pilot files already exist and MUST NOT be modified. Templates go into the plan documentation, not into the live directory.

### Implementer 2 Tasks

#### T-5: Update CLAUDE.md to v7.0 (Group B)

**File:** `.claude/CLAUDE.md` (MODIFY, +20 lines)
**Dependency:** None (documentation can be written before hooks exist)
**Blocks:** T-7, T-8
**Acceptance Criteria:**
1. AC-0: Read current CLAUDE.md (180 lines). Verify §6 structure (lines 77-128) and §9 structure (lines 143-153) before editing.
2. §6 "Monitoring Progress" (after line 106): RTD Operating Principle subsection added (~8 lines)
3. §6 "Coordination Infrastructure" (after line 128): Observability directory spec added (~7 lines)
4. §9 (lines 143-153): REWRITTEN with RTD-centric recovery (~15 lines, net +4)
5. Version line updated: "v6.0" → "v7.0" if present in any header (verify first)
6. No changes to §0-§5, §7, §8, §10

#### T-6: Update agent-common-protocol.md to v3.0 (Group B)

**File:** `.claude/references/agent-common-protocol.md` (MODIFY, +15 lines)
**Dependency:** None
**Blocks:** T-8
**Acceptance Criteria:**
1. AC-0: Read current agent-common-protocol.md (89 lines). Verify "Saving Your Work" section (lines 61-67) structure before inserting.
2. L1/L2 PT Goal Linkage subsection added after "Saving Your Work" section
3. Content matches architecture §8.1 spec
4. Backward-compatible: omitting new fields does not break any process
5. No changes to other sections

#### T-7: Add RTD Template to 7 Pipeline Skills (Group C)

**Files:** 7 × `.claude/skills/*/SKILL.md` (MODIFY, +8-10 lines each)
**Dependency:** T-5 (skills reference §6 principles)
**Blocks:** None
**Acceptance Criteria:**
1. AC-0: Read each skill's "Cross-Cutting Requirements" section. Verify the section exists and identify exact insertion point before editing.
2. RTD Index subsection added to "Cross-Cutting Requirements" section of each skill
3. Template text is IDENTICAL across all 7 skills (except per-skill DP catalog)
4. Per-skill DP catalog matches architecture §10.2 table
5. permanent-tasks skill gets a shortened version (2-3 DPs vs 6-12 for pipeline skills)

#### T-8: Add RTD Awareness to 6 Agent .md Files (Group D)

**Files:** 6 × `.claude/agents/*.md` (MODIFY, +3 lines each)
**Dependency:** T-5, T-6 (agents reference §6 and protocol)
**Blocks:** None
**Acceptance Criteria:**
1. AC-0: Read each agent's "Constraints" and "Output Format" sections. Verify structure before inserting.
2. Each agent's "Constraints" section gets 1-2 lines about RTD auto-capture
3. Each agent's "Output Format" L1 schema gets 1-2 lines about optional pt_goal_link
4. Text is IDENTICAL across all 6 agents
5. No changes to YAML frontmatter, Role, or How to Work sections

### Task Dependency Graph

```
T-1 (PostToolUse hook) ──┐
                          ├──→ T-3 (Session compact rewrite)
T-2 (Extend hooks+cfg) ──┘

T-1 ──→ T-4 (Bootstrap templates)

T-5 (CLAUDE.md) ──→ T-7 (Skills)
                ──→ T-8 (Agents)

T-6 (Protocol) ──→ T-8 (Agents)
```

**Parallel opportunities:**
- Implementer 1: T-1 ∥ T-2, then T-3, then T-4
- Implementer 2: T-5 ∥ T-6, then T-7, then T-8
- Cross-implementer: fully parallel (zero file overlap)

---

## 5. Detailed Specifications

### A1: on-rtd-post-tool.sh (NEW) — V-EXACT

**Complete file content:**

```bash
#!/bin/bash
# Hook: PostToolUse — RTD event capture for observability
# Captures ALL tool calls from ALL sessions as JSONL events.
# Async mode (settings.json) — zero latency impact on agentic loop.
# Any error → exit 0 (never block pipeline). AD-28.

set -e
trap 'exit 0' ERR

INPUT=$(cat)

# Require jq
command -v jq &>/dev/null || exit 0

# Parse common fields from hook input
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null) || exit 0
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null) || exit 0
TOOL_USE_ID=$(echo "$INPUT" | jq -r '.tool_use_id // empty' 2>/dev/null) || exit 0

[ -z "$SESSION_ID" ] && exit 0
[ -z "$TOOL_NAME" ] && exit 0

# Determine project slug from .current-project
OBS_BASE="/home/palantir/.agent/observability"
PROJECT_FILE="$OBS_BASE/.current-project"
SLUG="default"
if [ -f "$PROJECT_FILE" ]; then
  SLUG=$(head -1 "$PROJECT_FILE" 2>/dev/null)
  [ -z "$SLUG" ] && SLUG="default"
fi

OBS_DIR="$OBS_BASE/$SLUG"
EVENTS_DIR="$OBS_DIR/events"
mkdir -p "$EVENTS_DIR"

# Resolve agent name from session registry
AGENT="lead"
REGISTRY="$OBS_DIR/session-registry.json"
if [ -f "$REGISTRY" ]; then
  RESOLVED=$(jq -r --arg sid "$SESSION_ID" '.[$sid].name // empty' "$REGISTRY" 2>/dev/null)
  if [ -n "$RESOLVED" ]; then
    AGENT="$RESOLVED"
  else
    # Not in registry = likely Lead (Lead's session not registered via SubagentStart)
    AGENT="lead"
  fi
fi

# Read current DP from signal file (best-effort, AD-24)
DP="null"
DP_FILE="$OBS_DIR/current-dp.txt"
if [ -f "$DP_FILE" ]; then
  DP_VAL=$(head -1 "$DP_FILE" 2>/dev/null)
  [ -n "$DP_VAL" ] && DP="\"$DP_VAL\""
fi

# Build tool-specific input_summary and output_summary
TOOL_INPUT=$(echo "$INPUT" | jq -c '.tool_input // {}' 2>/dev/null) || TOOL_INPUT="{}"
TOOL_RESPONSE=$(echo "$INPUT" | jq -c '.tool_response // {}' 2>/dev/null) || TOOL_RESPONSE="{}"

case "$TOOL_NAME" in
  Write)
    INPUT_SUMMARY=$(echo "$TOOL_INPUT" | jq -c '{
      file_path: .file_path,
      content_lines: (.content | split("\n") | length),
      content_bytes: (.content | length)
    }' 2>/dev/null) || INPUT_SUMMARY='{"error":"parse_failed"}'
    OUTPUT_SUMMARY='{"success":true}'
    ;;
  Edit)
    INPUT_SUMMARY=$(echo "$TOOL_INPUT" | jq -c '{
      file_path: .file_path,
      old_preview: (.old_string | .[0:80]),
      new_preview: (.new_string | .[0:80]),
      replace_all: (.replace_all // false)
    }' 2>/dev/null) || INPUT_SUMMARY='{"error":"parse_failed"}'
    OUTPUT_SUMMARY='{"success":true}'
    ;;
  Read)
    INPUT_SUMMARY=$(echo "$TOOL_INPUT" | jq -c '{
      file_path: .file_path,
      offset: .offset,
      limit: .limit
    }' 2>/dev/null) || INPUT_SUMMARY='{"error":"parse_failed"}'
    OUTPUT_SUMMARY=$(echo "$TOOL_RESPONSE" | jq -c '{
      lines: (if type == "string" then (split("\n") | length) else 0 end)
    }' 2>/dev/null) || OUTPUT_SUMMARY='{"lines":0}'
    ;;
  Bash)
    INPUT_SUMMARY=$(echo "$TOOL_INPUT" | jq -c '{
      command: (.command | .[0:200]),
      description: (.description | .[0:100])
    }' 2>/dev/null) || INPUT_SUMMARY='{"error":"parse_failed"}'
    OUTPUT_SUMMARY=$(echo "$TOOL_RESPONSE" | jq -c '{
      exit_code: (.exit_code // 0)
    }' 2>/dev/null) || OUTPUT_SUMMARY='{"exit_code":0}'
    ;;
  Glob)
    INPUT_SUMMARY=$(echo "$TOOL_INPUT" | jq -c '{
      pattern: .pattern,
      path: .path
    }' 2>/dev/null) || INPUT_SUMMARY='{"error":"parse_failed"}'
    OUTPUT_SUMMARY=$(echo "$TOOL_RESPONSE" | jq -c '{
      count: (if type == "array" then length elif type == "string" then (split("\n") | length) else 0 end)
    }' 2>/dev/null) || OUTPUT_SUMMARY='{"count":0}'
    ;;
  Grep)
    INPUT_SUMMARY=$(echo "$TOOL_INPUT" | jq -c '{
      pattern: .pattern,
      path: .path,
      glob: .glob
    }' 2>/dev/null) || INPUT_SUMMARY='{"error":"parse_failed"}'
    OUTPUT_SUMMARY=$(echo "$TOOL_RESPONSE" | jq -c '{
      count: (if type == "array" then length elif type == "string" then (split("\n") | length) else 0 end)
    }' 2>/dev/null) || OUTPUT_SUMMARY='{"count":0}'
    ;;
  Task)
    INPUT_SUMMARY=$(echo "$TOOL_INPUT" | jq -c '{
      description: (.description | .[0:100]),
      subagent_type: .subagent_type
    }' 2>/dev/null) || INPUT_SUMMARY='{"error":"parse_failed"}'
    OUTPUT_SUMMARY='{"status":"ok"}'
    ;;
  *)
    # Generic: first 3 keys from tool_input
    INPUT_SUMMARY=$(echo "$TOOL_INPUT" | jq -c 'to_entries | .[0:3] | from_entries' 2>/dev/null) || INPUT_SUMMARY='{}'
    OUTPUT_SUMMARY='{"status":"ok"}'
    ;;
esac

# Construct JSONL event and append
TIMESTAMP=$(date -u '+%Y-%m-%dT%H:%M:%S.%3NZ')
EVENT_FILE="$EVENTS_DIR/${SESSION_ID}.jsonl"

jq -n -c \
  --arg ts "$TIMESTAMP" \
  --arg sid "$SESSION_ID" \
  --arg agent "$AGENT" \
  --arg tool "$TOOL_NAME" \
  --arg tid "$TOOL_USE_ID" \
  --argjson input_summary "$INPUT_SUMMARY" \
  --argjson output_summary "$OUTPUT_SUMMARY" \
  --argjson dp "$DP" \
  '{ts: $ts, sid: $sid, agent: $agent, tool: $tool, tid: $tid, input_summary: $input_summary, output_summary: $output_summary, dp: $dp}' \
  >> "$EVENT_FILE" 2>/dev/null

exit 0
```

**Lines:** ~110
**Verification Level:** V-EXACT — copy-paste ready. Implementer verifies against actual PostToolUse hook input format (AC-0).

**V6 Code Plausibility Notes:**
- VP-1: PostToolUse input JSON structure is assumed from Claude Code hooks API documentation (`.session_id`, `.tool_name`, `.tool_use_id`, `.tool_input`, `.tool_response`). If field names differ, adjust the jq selectors accordingly.
- VP-2: `date -u '+%Y-%m-%dT%H:%M:%S.%3NZ'` requires GNU date (Linux). On macOS, use `gdate` or `date -u '+%Y-%m-%dT%H:%M:%SZ'` (no ms). Since target is WSL2 Linux, GNU date is available.
- VP-3: The `Read` tool_response structure is unknown — it may be a string or an object. The jq `if type == "string"` branching handles both. First-run observation recommended.
- VP-4: jq's `split("\n") | length` for line counting works on strings. If `content` is absent or null for Write, jq will error — the `|| INPUT_SUMMARY=...` fallback handles this.

---

### A2: on-subagent-start.sh EXTENSION — V-EXACT

**Current file:** 67 lines. Insertion point: after line 20 (after logging line), before line 22 (context injection comment).

**Exact old_string to match for insertion:**

```
echo "[$TIMESTAMP] SUBAGENT_START | name=$AGENT_NAME | type=$AGENT_TYPE | team=$TEAM_NAME" >> "$LOG_DIR/teammate-lifecycle.log"

# Context injection via additionalContext
```

**Exact new_string (replace with):**

```
echo "[$TIMESTAMP] SUBAGENT_START | name=$AGENT_NAME | type=$AGENT_TYPE | team=$TEAM_NAME" >> "$LOG_DIR/teammate-lifecycle.log"

# RTD Session Registry — map session_id → agent for PostToolUse identification (AD-23)
RTD_SID="${CLAUDE_SESSION_ID:-}"
if [ -n "$RTD_SID" ] && [ -n "$AGENT_NAME" ] && [ "$AGENT_NAME" != "unknown" ]; then
  PROJECT_FILE="/home/palantir/.agent/observability/.current-project"
  if [ -f "$PROJECT_FILE" ]; then
    RTD_SLUG=$(head -1 "$PROJECT_FILE" 2>/dev/null)
    if [ -n "$RTD_SLUG" ]; then
      REGISTRY="/home/palantir/.agent/observability/$RTD_SLUG/session-registry.json"
      if [ -f "$REGISTRY" ] && command -v jq &>/dev/null; then
        TMP=$(mktemp)
        jq --arg sid "$RTD_SID" --arg name "$AGENT_NAME" --arg type "$AGENT_TYPE" \
          '. + {($sid): {name: $name, type: $type}}' "$REGISTRY" > "$TMP" && mv "$TMP" "$REGISTRY"
      elif command -v jq &>/dev/null; then
        mkdir -p "$(dirname "$REGISTRY")"
        jq -n --arg sid "$RTD_SID" --arg name "$AGENT_NAME" --arg type "$AGENT_TYPE" \
          '{($sid): {name: $name, type: $type}}' > "$REGISTRY"
      fi
    fi
  fi
fi

# Context injection via additionalContext
```

**Lines added:** ~18
**Verification Level:** V-EXACT

**V6 Code Plausibility Notes:**
- VP-5: `$CLAUDE_SESSION_ID` — this env var is the hook's OWN session context (Lead's session, since SubagentStart fires in Lead context). Per AD-23's 3-tier mechanism, this may NOT be the child's session ID. The implementer should log the actual value during first run (Tier 1 verification). If it's Lead's session ID, the registry entry maps Lead's SID → the spawned agent's name — which is still useful for Lead identification but not for the child. In that case, Tier 2 (Lead-initiated registry) or Tier 3 (PostToolUse fallback) activates.
- VP-6: The `mktemp` + `jq > tmp && mv tmp` pattern is atomic-enough for sequential writes (teammates spawn one at a time from Lead). No concurrent write risk.

---

### A3: on-pre-compact.sh EXTENSION — V-EXACT

**Current file:** 65 lines. Insertion point: before the final `exit 0` at line 65.

**Exact old_string to match:**

```
  fi
fi

exit 0
```

(This is lines 62-65: closing the `MISSING_AGENTS` if block, closing the `TEAM_DIR` if block, blank line, exit 0.)

**Exact new_string (replace with):**

```
  fi
fi

# RTD State Snapshot for recovery (AD-25)
PROJECT_FILE="/home/palantir/.agent/observability/.current-project"
if [ -f "$PROJECT_FILE" ]; then
  RTD_SLUG=$(head -1 "$PROJECT_FILE" 2>/dev/null)
  OBS_DIR="/home/palantir/.agent/observability/$RTD_SLUG"
  RTD_INDEX="$OBS_DIR/rtd-index.md"

  if [ -d "$OBS_DIR" ] && command -v jq &>/dev/null; then
    SNAPSHOT_DIR="$OBS_DIR/snapshots"
    mkdir -p "$SNAPSHOT_DIR"
    SNAPSHOT_FILE="$SNAPSHOT_DIR/$(date '+%s')-pre-compact.json"

    # Extract state from rtd-index.md frontmatter
    LAST_DP=""
    ACTIVE_PHASE=""
    if [ -f "$RTD_INDEX" ]; then
      LAST_DP=$(grep -oP '### DP-\K\d+' "$RTD_INDEX" 2>/dev/null | tail -1)
      ACTIVE_PHASE=$(grep -oP '^current_phase: \K.*' "$RTD_INDEX" 2>/dev/null | tail -1)
    fi

    jq -n \
      --arg slug "$RTD_SLUG" \
      --arg last_dp "DP-${LAST_DP:-0}" \
      --arg phase "${ACTIVE_PHASE:-unknown}" \
      --arg ts "$(date -Iseconds)" \
      '{slug: $slug, last_dp: $last_dp, phase: $phase, ts: $ts, type: "pre-compact"}' \
      > "$SNAPSHOT_FILE" 2>/dev/null

    echo "[$TIMESTAMP] PRE_COMPACT | RTD snapshot: $SNAPSHOT_FILE (DP=$LAST_DP, Phase=$ACTIVE_PHASE)" \
      >> "$LOG_DIR/compact-events.log"
  fi
fi

exit 0
```

**Lines added:** ~25
**Verification Level:** V-EXACT

**V6 Code Plausibility Notes:**
- VP-7: `grep -oP` requires PCRE support. On WSL2 Ubuntu, `grep` supports `-P` natively. If not available, use `grep -o 'DP-[0-9]*'` with `sed` to extract the number instead.
- VP-8: `$TIMESTAMP` is already defined at line 7 of the current script. Reuse is safe.

---

### A4: on-session-compact.sh REWRITE — V-EXACT

**Current file:** 25 lines. Full replacement.

**Complete new file content:**

```bash
#!/bin/bash
# Hook: SessionStart(compact) — RTD-centric auto-compact recovery
# Provides precise recovery context when RTD data is available,
# falls back to generic recovery when it isn't (C-6).

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_DIR="/home/palantir/.agent/teams"
mkdir -p "$LOG_DIR"

echo "[$TIMESTAMP] SESSION_COMPACT | Context compacted — recovery active" \
  >> "$LOG_DIR/compact-events.log"

# Attempt RTD-enhanced recovery
RTD_CONTEXT=""
PROJECT_FILE="/home/palantir/.agent/observability/.current-project"

if [ -f "$PROJECT_FILE" ] && command -v jq &>/dev/null; then
  RTD_SLUG=$(head -1 "$PROJECT_FILE" 2>/dev/null)
  OBS_DIR="/home/palantir/.agent/observability/$RTD_SLUG"
  RTD_INDEX="$OBS_DIR/rtd-index.md"

  if [ -f "$RTD_INDEX" ]; then
    # Extract key state from rtd-index.md
    PHASE=$(grep -oP '^current_phase: \K.*' "$RTD_INDEX" 2>/dev/null | tail -1)
    LAST_DP=$(grep -oP '### DP-\d+' "$RTD_INDEX" 2>/dev/null | tail -1)
    RECENT=$(grep -E '^### DP-' "$RTD_INDEX" 2>/dev/null | tail -3 | tr '\n' ' ')

    RTD_CONTEXT="RTD Recovery — Project: $RTD_SLUG | Phase: ${PHASE:-?} | Last: ${LAST_DP:-?}. Recent: $RECENT"
  fi
fi

# Build recovery message
if [ -n "$RTD_CONTEXT" ]; then
  MSG="Your session was compacted. $RTD_CONTEXT. Steps: 1) Read .agent/observability/$RTD_SLUG/rtd-index.md for decision history 2) Read orchestration-plan.md for teammate status 3) TaskGet PERMANENT Task for project context 4) Send context to active teammates with latest PT version."
else
  # Graceful degradation: no RTD data → current generic recovery (v6.2 identical)
  MSG="Your session was compacted. As Lead: 1) Read orchestration-plan.md 2) Read task list (including PERMANENT Task) 3) Send fresh context to each active teammate with the latest PT version 4) Teammates should read their L1/L2/L3 files to restore progress."
fi

# Output JSON
if command -v jq &>/dev/null; then
  jq -n --arg msg "$MSG" '{
    "hookSpecificOutput": {
      "hookEventName": "SessionStart",
      "additionalContext": $msg
    }
  }'
else
  echo "{\"hookSpecificOutput\":{\"hookEventName\":\"SessionStart\",\"additionalContext\":\"$MSG\"}}"
fi

exit 0
```

**Lines:** ~55
**Verification Level:** V-EXACT

**Critical verification:** The `else` branch (no RTD data) produces IDENTICAL output to the current v6.2 script. Compare:
- Current: `"Your session was compacted. As Lead: 1) Read orchestration-plan.md 2) Read task list (including PERMANENT Task) 3) Send fresh context to each active teammate with the latest PT version 4) Teammates should read their L1/L2/L3 files to restore progress."`
- New fallback: identical string.

---

### A5: settings.json PostToolUse Entry — V-EXACT

**Current file:** 68 lines. Insertion point: after the SessionStart block (line 60), before `"enabledPlugins"` (line 62).

**Exact old_string to match:**

```json
    ]
  },
  "enabledPlugins": {
```

(This is lines 59-62: closing hooks array for SessionStart, closing SessionStart, closing hooks, then enabledPlugins.)

Wait — let me re-examine. The `"hooks"` object closes with `}` before `"enabledPlugins"`. The actual structure is:

```json
    "SessionStart": [
      ...
    ]
  },
  "enabledPlugins": {
```

**Exact old_string (lines 47-62):**

```json
    "SessionStart": [
      {
        "matcher": "compact",
        "hooks": [
          {
            "type": "command",
            "command": "/home/palantir/.claude/hooks/on-session-compact.sh",
            "timeout": 15,
            "statusMessage": "Recovery after compaction",
            "once": true
          }
        ]
      }
    ]
  },
  "enabledPlugins": {
```

**Exact new_string:**

```json
    "SessionStart": [
      {
        "matcher": "compact",
        "hooks": [
          {
            "type": "command",
            "command": "/home/palantir/.claude/hooks/on-session-compact.sh",
            "timeout": 15,
            "statusMessage": "Recovery after compaction",
            "once": true
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "/home/palantir/.claude/hooks/on-rtd-post-tool.sh",
            "timeout": 5,
            "async": true
          }
        ]
      }
    ]
  },
  "enabledPlugins": {
```

**Lines added:** ~14 (PostToolUse block)
**Verification Level:** V-EXACT

**Note:** The key change is adding a comma after the SessionStart `]` to make it `],` and adding the PostToolUse block before the closing `}` of the hooks object. JSON syntax must be valid — implementer should validate with `jq . .claude/settings.json` after editing.

---

### A6: Bootstrap Templates (Group E) — V-HIGH

**Note:** These are TEMPLATE specifications. The actual pilot files already exist at `.agent/observability/rtd-system/`. These templates serve as:
1. Documentation of the expected format
2. Reference for skills that initialize new projects
3. Validation targets for the PostToolUse hook

**Template: .current-project**
```
{project-slug}
```
Single line, no trailing newline. Example: `rtd-system`

**Template: manifest.json**
```json
{
  "version": "1.0",
  "project_slug": "{project-slug}",
  "pt_subject": "[PERMANENT] {feature description}",
  "created": "{ISO8601}",
  "sessions": [
    {
      "session_id": "{team-name}",
      "team_name": "{team-name}",
      "started": "{ISO8601}",
      "status": "active"
    }
  ]
}
```

**Template: rtd-index.md**
```markdown
---
project: {project-slug}
pt_subject: "[PERMANENT] {feature description}"
pt_version: PT-v1
created: {ISO8601}
updated: {ISO8601}
current_phase: 1
current_dp: DP-0
total_entries: 0
---

# RTD Index — {feature description}

## Phase 1: Discovery
```

**Verification Level:** V-HIGH — templates are complete, implementer adapts variable names.

**Implementation Note:** These templates should be documented in the plan (this file) and referenced by skill RTD templates (T-7). Do NOT overwrite the existing pilot files. Implementer creates a `docs/templates/rtd-bootstrap/` directory with these templates if Lead requests it, otherwise they remain specification-only.

---

### B1: CLAUDE.md §6 RTD Addition — V-EXACT

**Current file:** 180 lines.

**Edit 1: Add RTD Operating Principle to §6**

Insert after the "Monitoring Progress" paragraph (after line 106, before "### Phase Gates"):

**Exact old_string:**

```markdown
Log cosmetic deviations, re-inject context for interface changes, re-plan for architectural
changes. No gate approval while any teammate has stale context.

### Phase Gates
```

**Exact new_string:**

```markdown
Log cosmetic deviations, re-inject context for interface changes, re-plan for architectural
changes. No gate approval while any teammate has stale context.

### Observability (RTD)
Lead maintains real-time documentation through the RTD system:
- Write an rtd-index.md entry at each Decision Point (gate approvals, task assignments,
  architecture decisions, conflict resolutions, context updates)
- Update `.agent/observability/{slug}/current-dp.txt` before each DP's associated actions
- Read rtd-index.md alongside L1/L2/L3 when monitoring progress — it provides the
  temporal dimension that Impact Map queries need
- The PostToolUse hook automatically captures all tool calls to events.jsonl — no
  manual event logging needed

### Phase Gates
```

**Lines added:** ~9

---

**Edit 2: Add Observability Directory to §6 Coordination Infrastructure**

Insert after the output directory spec (after line 128, before "## 7. Tools"):

**Exact old_string:**

```markdown
  └── phase-{N}/ → gate-record.yaml, {role}-{id}/ → L1, L2, L3-full/, task-context.md
  ```

## 7. Tools
```

**Exact new_string:**

```markdown
  └── phase-{N}/ → gate-record.yaml, {role}-{id}/ → L1, L2, L3-full/, task-context.md
  ```
- **Observability directory:**
  ```
  .agent/observability/
  ├── .current-project           # Active project slug
  └── {project-slug}/
      ├── manifest.json, rtd-index.md, current-dp.txt, session-registry.json
      └── events/{session}.jsonl
  ```
  Lead initializes at pipeline start. Hooks populate automatically.
  Persists across sessions for project-scoped observability.

## 7. Tools
```

**Lines added:** ~8

---

**Edit 3: Rewrite §9 Recovery**

**Exact old_string (lines 143-153):**

```markdown
## 9. Recovery

If your session is continued from a previous conversation:
- **Lead:** Read orchestration-plan.md, task list (including PERMANENT Task), latest gate
  record, and teammate L1 indexes. Send fresh context to each active teammate.
- **Teammates:** See agent-common-protocol.md for recovery procedure. You can call TaskGet
  on the PERMANENT Task for immediate self-recovery — it contains the full project context.
  Core rule: never proceed with summarized or remembered information alone.

If a teammate reports they're running low on context: read their L1/L2/L3, shut them down,
and re-spawn with their saved progress.
```

**Exact new_string:**

```markdown
## 9. Recovery

If your session is continued from a previous conversation:
- **Lead:** The SessionStart hook provides RTD recovery context (project slug, phase,
  last decision point). Follow these steps:
  1. Read `.agent/observability/{slug}/rtd-index.md` for decision history (last 10 entries)
  2. Read orchestration-plan.md for teammate status and phase details
  3. TaskGet on the PERMANENT Task for full project context
  4. Send fresh context to each active teammate with the latest PT version
  If no RTD data is available, read orchestration-plan.md, task list, latest gate record,
  and teammate L1 indexes directly.
- **Teammates:** See agent-common-protocol.md for recovery procedure. You can call TaskGet
  on the PERMANENT Task for immediate self-recovery — it contains the full project context.
  Core rule: never proceed with summarized or remembered information alone.

If a teammate reports they're running low on context: read their L1/L2/L3, shut them down,
and re-spawn with their saved progress.
```

**Net lines added:** +4
**Verification Level:** V-EXACT

---

### B2: agent-common-protocol.md v3.0 — V-EXACT

**Current file:** 89 lines.

**Insert after "Saving Your Work" section (after line 67, before "## If You Lose Context"):**

**Exact old_string:**

```markdown
If you notice you're running low on context: save all work immediately, then tell Lead.
Lead will shut you down and re-spawn you with your saved progress.

---

## If You Lose Context
```

**Exact new_string:**

```markdown
If you notice you're running low on context: save all work immediately, then tell Lead.
Lead will shut you down and re-spawn you with your saved progress.

### L1/L2 Project Goal Linkage (Optional)

When working on a project with RTD active, include goal references in your deliverables:

- **L1 YAML:** Add `pt_goal_link:` field to findings or task entries, referencing
  the requirement (R-{N}) or architecture decision (AD-{M}) your work addresses.
  ```yaml
  findings:
    - id: F-1
      summary: "Hooks fire for all sessions"
      pt_goal_link: "R-5 (Agent Teams Shared)"
  ```

- **L2 MD:** Add a `## PT Goal Linkage` section at the end connecting your work
  to the project's requirements and architecture decisions.

This is backward-compatible — omitting these fields does not break any process.
Lead uses them for traceability.

---

## If You Lose Context
```

**Lines added:** ~16
**Verification Level:** V-EXACT

---

### C1: Skill RTD Template (7 skills) — V-HIGH

**Target section:** "Cross-Cutting Requirements" in each skill. Insert BEFORE the existing content (as a new subsection at the top of Cross-Cutting).

**Exact template (identical across all 7 pipeline skills, except DP catalog):**

```markdown
### RTD Index

At each Decision Point in this phase, update the RTD index:
1. Update `current-dp.txt` with the new DP number
2. Write an rtd-index.md entry with WHO/WHAT/WHY/EVIDENCE/IMPACT/STATUS
3. Update the frontmatter (current_phase, current_dp, updated, total_entries)

Decision Points for this skill:
{PER-SKILL DP CATALOG — see below}
```

**Per-skill DP catalogs:**

**brainstorming-pipeline:**
```
- DP: Scope crystallization (1.4 approval)
- DP: Approach selection (1.3 user choice)
- DP: Researcher spawn (2.3)
- DP: Gate 1 evaluation
- DP: Gate 2 evaluation
- DP: Architect spawn (3.1)
- DP: Gate 3 evaluation
```

**agent-teams-write-plan:**
```
- DP: Input validation and plan scope
- DP: Architect spawn
- DP: Plan completion assessment
- DP: Gate 4 evaluation
```

**plan-validation-pipeline:**
```
- DP: Devils-advocate spawn
- DP: Verdict evaluation
- DP: User review decision
- DP: Gate 5 evaluation
```

**agent-teams-execution-plan:**
```
- DP: Input validation and spawn algorithm
- DP: Each implementer spawn
- DP: Per-task completion assessment
- DP: Monitoring interventions
- DP: Gate 6 evaluation
```

**verification-pipeline:**
```
- DP: Tester spawn
- DP: Test evaluation
- DP: Integrator spawn
- DP: Integration review
- DP: Gate 7/8 evaluation
```

**delivery-pipeline:**
```
- DP: Session identification
- DP: Consolidation strategy
- DP: Commit decision
- DP: Cleanup classification
```

**permanent-tasks:**
```
- DP: PT creation or update decision
- DP: Teammate notification (if PT version changes mid-work)
```

**Insertion method:** For each skill, find `## Cross-Cutting Requirements` (or `## Cross-Cutting` for agent-teams-write-plan), and insert the RTD block as the first subsection (before `### Sequential Thinking` or equivalent).

**Lines added per skill:** ~10 (template + catalog)
**Total across 7 skills:** ~70
**Verification Level:** V-HIGH — template is exact, implementer adapts insertion point per skill.

---

### D1: Agent .md RTD Awareness (6 agents) — V-EXACT

**Pattern (identical text for all 6 agents):**

**Add to "Constraints" section (append at end, before any blank trailing line):**

```markdown
- Your tool calls are automatically captured by the RTD system for observability. No action needed — focus on your assigned work.
```

**Add to "Output Format" section (append to L1 bullet, or after L1 bullet):**

```markdown
- Include `pt_goal_link:` in L1 entries when your work directly addresses a project requirement (R-{N}) or architecture decision (AD-{M}).
```

**Per-agent insertion points:**

| Agent | Constraints last line | Output Format L1 line |
|-------|----------------------|----------------------|
| researcher.md | Line 63 (spawn subagents line) | After line 57 (L1 bullet) |
| architect.md | Line 74 (L1/L2/L3 line) | After line 61 (L1 bullet) |
| implementer.md | Line 81 (L1/L2/L3 line) | After line 66 (L1 bullet) |
| tester.md | Line 77 (L1/L2/L3 line) | After line 69 (L1 bullet) |
| devils-advocate.md | Line 73 (L1/L2/L3 line) | After line 65 (L1 bullet) |
| integrator.md | Line 81 (L1/L2/L3 line) | After line 72 (L1 bullet) |

**Lines added per agent:** ~3 (2 lines content + 1 blank line)
**Total across 6 agents:** ~18
**Verification Level:** V-EXACT

---

## 6. Interface Contracts

### Between Implementers

| Contract | From (Impl) | To (Impl) | Interface | Validation |
|----------|-------------|-----------|-----------|------------|
| IC-A | Impl 1 (hooks) | Impl 2 (CLAUDE.md §9) | Recovery message format matches §9 text | String comparison of fallback message |
| IC-B | Impl 1 (.current-project) | Impl 2 (skills RTD template) | Project slug format = single line, no spaces | `head -1` yields valid directory name |
| IC-C | Impl 1 (events.jsonl schema) | Impl 2 (skill DP catalog) | DP naming convention: "DP-{N}" monotonic | grep pattern `DP-\d+` matches both |

### Between Components

| Contract | From | To | Format | Notes |
|----------|------|-----|--------|-------|
| IC-1 | PostToolUse hook | events/{sid}.jsonl | JSONL append, 8 fields | < 2000 bytes per event |
| IC-2 | Lead | rtd-index.md | Markdown write | 6-field entries per DP |
| IC-3 | Lead | current-dp.txt | Single-line overwrite | "DP-{N}" format |
| IC-4 | SubagentStart hook | session-registry.json | JSON merge | {sid: {name, type}} |
| IC-5 | PostToolUse hook | session-registry.json | JSON read | Lookup by session_id |
| IC-6 | PreCompact hook | snapshots/{ts}.json | JSON write | {slug, last_dp, phase, ts, type} |
| IC-7 | SessionStart hook | rtd-index.md | Markdown read (grep) | Frontmatter + DP headers |
| IC-8 | SessionStart hook | additionalContext | JSON string | < 1000 chars |
| IC-11 | Lead → .current-project | All hooks | Single-line read | Key coordination file |

---

## 7. Validation Checklist

### V1: Hook Script Correctness

- [ ] on-rtd-post-tool.sh is executable and produces valid JSONL
- [ ] on-rtd-post-tool.sh handles missing .current-project gracefully (uses "default")
- [ ] on-rtd-post-tool.sh handles missing session-registry.json gracefully (uses "lead")
- [ ] on-rtd-post-tool.sh handles missing current-dp.txt gracefully (uses null)
- [ ] on-subagent-start.sh RTD section handles missing .current-project gracefully
- [ ] on-pre-compact.sh RTD section handles missing observability directory gracefully
- [ ] on-session-compact.sh fallback produces IDENTICAL output to v6.2 version

### V2: settings.json Validity

- [ ] `jq . .claude/settings.json` succeeds (valid JSON)
- [ ] PostToolUse entry has `async: true`
- [ ] Existing SubagentStart, PreCompact, SessionStart entries UNCHANGED

### V3: CLAUDE.md Structural Integrity

- [ ] §6 has "Observability (RTD)" subsection
- [ ] §6 has observability directory spec in Coordination Infrastructure
- [ ] §9 references rtd-index.md as first recovery step
- [ ] §9 fallback matches v6.2 behavior
- [ ] All other sections (§0-§5, §7, §8, §10) UNCHANGED

### V4: Protocol + Agent Consistency

- [ ] agent-common-protocol.md has "L1/L2 Project Goal Linkage" subsection
- [ ] All 6 agent .md files have RTD awareness line in Constraints
- [ ] All 6 agent .md files have pt_goal_link line in Output Format
- [ ] Text is IDENTICAL across all 6 agents

### V5: Skill Template Consistency

- [ ] All 7 skills have "### RTD Index" subsection in Cross-Cutting
- [ ] Template text (non-catalog part) is IDENTICAL across all 7 skills
- [ ] Per-skill DP catalogs match §10.2 from architecture

### V6: Code Plausibility

- [ ] VP-1: PostToolUse hook input field names verified against actual API (first-run test)
- [ ] VP-2: GNU `date` format with milliseconds works on WSL2 Linux
- [ ] VP-3: Read tool_response handling for both string and object types
- [ ] VP-4: jq null-safety for Write content field
- [ ] VP-5: `$CLAUDE_SESSION_ID` value in SubagentStart context logged and documented
- [ ] VP-6: mktemp + mv atomic pattern for session-registry.json
- [ ] VP-7: `grep -oP` PCRE support confirmed on WSL2 Ubuntu
- [ ] VP-8: `$TIMESTAMP` variable reuse in pre-compact.sh extension

### V7: Interface Contract Verification

- [ ] IC-A: Recovery fallback message in on-session-compact.sh matches CLAUDE.md §9 fallback text
- [ ] IC-B: .current-project format is single-line with valid directory name
- [ ] events.jsonl 8-field schema matches §4.1 exactly

---

## 8. Risk Mitigation

| Risk (from architecture §13) | Implementation Mitigation |
|-------------------------------|--------------------------|
| R2: Recovery hook rewrite breaks existing | T-3 AC: fallback branch produces IDENTICAL v6.2 output. Test both branches. |
| R4: PostToolUse large stdin (100KB+) | Tool-specific summarization in A1 (§4.2). Truncation limits: 80/200/100 chars. Per-event < 2000 bytes. |
| R5: Session registry race condition | Sequential spawning from Lead. mktemp+mv atomic write. Read-only concurrent access safe. |
| R12: SubagentStart lacks child session_id | VP-5 first-run verification. 3-tier fallback: (1) verify → (2) Lead-write → (3) PostToolUse "lead" default. |
| R3: 7 skills consistency drift | Identical template text (C1 spec). Implementer copy-pastes, only adapts catalog. |
| R10: events.jsonl grows unbounded | Per-session files (events/{sid}.jsonl). Natural size management. No rotation logic needed. |
| R9: additionalContext too long | Session compact MSG capped implicitly — grep extracts 3 DP headers (~60 chars each). |
| NEW: JSON syntax error in settings.json | Post-edit validation with `jq .` (AC for T-2). |
| NEW: CLAUDE.md section numbering drift | Implementer reads current file (AC-0) and verifies line context before editing. |

---

## 9. Commit Strategy

**Recommended: Single commit after all tasks complete**

```bash
# Stage hook scripts
git add .claude/hooks/on-rtd-post-tool.sh \
  .claude/hooks/on-subagent-start.sh \
  .claude/hooks/on-pre-compact.sh \
  .claude/hooks/on-session-compact.sh \
  .claude/settings.json

# Stage documentation
git add .claude/CLAUDE.md \
  .claude/references/agent-common-protocol.md

# Stage skills (7 files)
git add .claude/skills/brainstorming-pipeline/SKILL.md \
  .claude/skills/agent-teams-write-plan/SKILL.md \
  .claude/skills/plan-validation-pipeline/SKILL.md \
  .claude/skills/agent-teams-execution-plan/SKILL.md \
  .claude/skills/verification-pipeline/SKILL.md \
  .claude/skills/delivery-pipeline/SKILL.md \
  .claude/skills/permanent-tasks/SKILL.md

# Stage agents (6 files)
git add .claude/agents/researcher.md \
  .claude/agents/architect.md \
  .claude/agents/implementer.md \
  .claude/agents/tester.md \
  .claude/agents/devils-advocate.md \
  .claude/agents/integrator.md

git commit -m "$(cat <<'EOF'
feat(infra): INFRA v7.0 — RTD Real-Time-Documenting system

Add 4-layer observability to Agent Teams infrastructure:
- Layer 0: PostToolUse hook captures all tool calls to events.jsonl (async)
- Layer 1: RTD index for curated Decision Point documentation
- Layer 2: L1/L2 pt_goal_link schema extension
- Layer 3: RTD-centric recovery (SessionStart hook rewrite)

Hook changes: new on-rtd-post-tool.sh, extend on-subagent-start.sh
(session registry), extend on-pre-compact.sh (RTD snapshot),
rewrite on-session-compact.sh (RTD-enhanced recovery with v6.2 fallback)

Config: PostToolUse async hook in settings.json
Docs: CLAUDE.md v7.0 (§6 RTD + §9 recovery), protocol v3.0 (goal linkage)
Skills: RTD template added to 7 pipeline skills
Agents: RTD awareness added to 6 agent definitions

Architecture: AD-22~28 | Design: architecture-design.md

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

**Alternative: Per-implementer commits (if Lead prefers granularity)**

- Implementer 1: `feat(infra): add RTD hooks and PostToolUse event capture`
- Implementer 2: `feat(infra): add RTD documentation to CLAUDE.md, skills, and agents`

**Do NOT commit:**
- `.agent/observability/` (already in .gitignore via `.agent/` pattern — verify)
- `.agent/teams/` (session artifacts, not committed)

---

## 10. Phase 5 Validation Targets

The following areas should be challenged by the devils-advocate:

### Target 1: PostToolUse Hook Input Format (VP-1)
**Challenge:** The entire event capture relies on assumed PostToolUse input field names (`.session_id`, `.tool_name`, `.tool_use_id`, `.tool_input`, `.tool_response`). If the actual Claude Code hooks API uses different field names, the hook produces empty/error events.
**Evidence:** Architecture §3.1 lists expected fields but notes "PostToolUse input contains" without citing official documentation.
**Risk if wrong:** Layer 0 (events.jsonl) produces garbage data. Layer 3 recovery is unaffected (reads rtd-index.md, not events).
**Recommended probe:** Verify field names against Claude Code hooks documentation or first-run observation.

### Target 2: $CLAUDE_SESSION_ID in SubagentStart Context (VP-5)
**Challenge:** AD-23 session registry depends on `$CLAUDE_SESSION_ID` being available in the SubagentStart hook shell environment AND being the child's (not parent's) session ID. If it's the parent's session ID, all teammates get mapped to Lead's session.
**Evidence:** Architecture §AD-23 acknowledges this gap with a 3-tier fallback mechanism.
**Risk if wrong:** Session registry is useless (all entries map to Lead). Events use "lead" for all agents. Mitigated by Tier 3 (timestamp correlation).
**Recommended probe:** Is the 3-tier fallback sufficient? What's the blast radius of Tier 3 being the only working tier?

### Target 3: Recovery Hook Rewrite Regression (R2)
**Challenge:** on-session-compact.sh is the PRIMARY recovery mechanism. The rewrite changes 100% of the script. If the new version has a bug in the RTD path AND a bug in the fallback path, recovery is broken.
**Evidence:** V-EXACT spec with character-identical fallback string. But bugs can hide in shell quoting, jq failures, or missing files.
**Risk if wrong:** Lead loses recovery capability on compact. Must re-read all files manually.
**Recommended probe:** Can the fallback path be verified independently? Should there be a pre-deployment test?

### Target 4: Graceful Degradation Completeness (C-6)
**Challenge:** Every hook claims "exit 0 on any error" but there may be code paths where the error trap doesn't fire (e.g., `jq` segfaults, disk full on `>>` append, race condition on `mv`).
**Evidence:** `set -e` + `trap 'exit 0' ERR` covers most cases. But `trap ERR` doesn't fire on commands in `if` conditions.
**Risk if wrong:** Hook returns non-zero, blocking the agentic loop (for sync hooks) or producing error messages (for async hooks).
**Recommended probe:** Review each hook for uncovered error paths outside of `if` conditions.

### Target 5: Skills Template Consistency Maintenance
**Challenge:** 7 identical template blocks across 7 files. Future skill updates may forget to update the RTD block, causing drift.
**Evidence:** AD-27 chose templated pattern over shared include. Architecture §10 notes "Lead applies the principle at each DP using their judgment."
**Risk if wrong:** Some skills have outdated RTD templates. Minor impact — Lead still writes rtd-index.md regardless of skill instruction.
**Recommended probe:** Is there a mechanism to detect template drift across the 7 skills? Should RSIL check this?

### Target 6: .current-project Single-Pipeline Limitation (NOTE-1)
**Challenge:** If two pipelines run simultaneously (unlikely but possible), the last writer to `.current-project` wins. All hooks from both pipelines route events to one project directory.
**Evidence:** Architecture §4.7 documents this explicitly as a known limitation. States "consistent with entire INFRA being single-pipeline."
**Risk if wrong:** Events from pipeline A appear in pipeline B's directory. Post-hoc re-sorting by session_id is possible but manual.
**Recommended probe:** Is the deferred mitigation (`.current-projects.json`) sufficient documentation? Should C-6 apply here?

---

## Appendix A: File Change Summary

| # | File | Op | Spec | VL | Lines |
|---|------|----|------|-----|-------|
| 1 | on-rtd-post-tool.sh | CREATE | A1 | V-EXACT | ~110 |
| 2 | on-subagent-start.sh | EXTEND | A2 | V-EXACT | +18 |
| 3 | on-pre-compact.sh | EXTEND | A3 | V-EXACT | +25 |
| 4 | on-session-compact.sh | REWRITE | A4 | V-EXACT | ~55 |
| 5 | settings.json | MODIFY | A5 | V-EXACT | +14 |
| 6 | CLAUDE.md | MODIFY | B1 | V-EXACT | +21 |
| 7 | agent-common-protocol.md | MODIFY | B2 | V-EXACT | +16 |
| 8-14 | 7 × skills/*/SKILL.md | MODIFY | C1 | V-HIGH | +10 ea |
| 15-20 | 6 × agents/*.md | MODIFY | D1 | V-EXACT | +3 ea |
| 21-23 | 3 × bootstrap templates | TEMPLATE | A6 | V-HIGH | ~35 |
| **Total** | **23 files** | | | | **~360** |

## Appendix B: Architecture Decision Quick Reference

| AD | Decision | Spec Impact |
|----|----------|-------------|
| AD-22 | Scope isolation (RSIL≠RTD hooks) | PostToolUse is NEW hook, not amendment to AD-15 |
| AD-23 | Session registry 3-tier | A2 (SubagentStart write) + A1 (PostToolUse read) + VP-5 |
| AD-24 | DP signal file (best-effort) | A1 (PostToolUse reads current-dp.txt) |
| AD-25 | Recovery priority (rtd-index first) | A4 (SessionStart reads rtd-index) + B1 §9 |
| AD-26 | Project-scoped observability | A6 (bootstrap templates) + A1 (directory structure) |
| AD-27 | Templated skill RTD | C1 (7 skills × identical template) |
| AD-28 | PostToolUse async mode | A5 (settings.json `async: true`) |
