# INFRA Audit v3 — Iteration 4: Remaining Optimization Gaps

**Date**: 2026-02-15
**Scope**: Skill L2 body quality (35 skills), cc-reference cache accuracy (4 files), hook logic edge cases (5 hooks), agent body quality (6 agents)
**Methodology**: Full-read analysis of all 50+ files, cross-referenced against current INFRA state v10.5

---

## Summary

| Severity | Count | Category Breakdown |
|----------|-------|--------------------|
| CRITICAL | 0 | -- |
| HIGH | 2 | cc-reference stale data (1), on-file-change async+additionalContext (1) |
| MEDIUM | 7 | skill L2 body issues (4), cc-reference gaps (2), hook edge case (1) |
| LOW | 6 | skill naming inconsistencies (2), agent body gaps (2), cc-reference minor (2) |
| ADVISORY | 5 | skill methodology improvements (3), agent guideline enhancements (2) |
| **TOTAL** | **20** | |

---

## Focus Area 1: Skill L2 Body Quality

### F1-01 [MEDIUM] execution-code references undefined "mode" parameter

**File**: `/home/palantir/.claude/skills/execution-code/SKILL.md` (line 35)
**Finding**: Step 2 says `Set mode: "default" for code implementation (agent permissions inherited from settings).` There is no `mode` parameter on the Task tool. The `permissionMode` field is set on the agent frontmatter, not per-spawn. This instruction is misleading.
**Also in**: `/home/palantir/.claude/skills/execution-cascade/SKILL.md` (line 43) — same `mode: "default"` reference.
**Impact**: Lead may attempt to pass a nonexistent `mode` parameter when spawning implementers.
**Fix**: Remove "Set mode" instructions. Permissions are inherited from agent frontmatter + settings.json `defaultMode: delegate`.

### F1-02 [MEDIUM] pre-design-brainstorm L1 description says "TIER_BEHAVIOR: TRIVIAL=Lead-only, STANDARD=1-2 analysts, COMPLEX=2-4 analysts" — contradicts L2

**File**: `/home/palantir/.claude/skills/pre-design-brainstorm/SKILL.md` (L1 line 12 vs L2 lines 22-24)
**Finding**: L1 description says `TIER_BEHAVIOR: TRIVIAL=Lead-only, STANDARD=1-2 analysts, COMPLEX=2-4 analysts`. But this is P0 which per CLAUDE.md Section 2.1 runs as "Lead-only" for P0-P2. The Execution Model in L2 says "Spawn 1-2 analysts" for STANDARD and "Spawn 2-4 analysts" for COMPLEX — these would spawn actual Team agents during a Lead-only phase.
**Also in**: `pre-design-validate`, `pre-design-feasibility`, `design-architecture`, `design-interface`, `design-risk` — all P0-P2 skills reference spawning analysts in their Execution Model but P0-P2 is Lead-only.
**Impact**: Contradiction between CLAUDE.md S2.1 ("No Team infrastructure needed") and skill bodies referencing analyst/researcher spawns. S2.1 says "local agents (run_in_background)" which is the Task tool with `run_in_background`, not Team teammates. The skill bodies don't distinguish this nuance.
**Fix**: Clarify in P0-P2 skill Execution Models that "Spawn analyst" means `run_in_background` local subagent (Task tool), not Team teammate (TaskCreate/SendMessage).

### F1-03 [MEDIUM] self-improve references "claude-code-guide" agent that does not exist in agents/

**File**: `/home/palantir/.claude/skills/self-improve/SKILL.md` (lines 20, 26-29)
**Finding**: References "Spawn claude-code-guide" and "claude-code-guide agent" but there is no `.claude/agents/claude-code-guide.md`. This agent is presumably a built-in or plugin agent (from `superpowers-developing-for-claude-code@superpowers-marketplace` plugin). The skill body doesn't clarify this — it reads as if claude-code-guide is a custom team agent.
**Also in**: `pre-design-feasibility` (line 21), `verify-cc-feasibility` (lines 22, 56-59).
**Impact**: If the plugin is not installed, these skills silently fail. No graceful degradation documented.
**Fix**: Add clarifying note that claude-code-guide is a plugin-provided agent (requires superpowers plugin), not a custom team agent. Add fallback: if plugin unavailable, use researcher with WebSearch for CC documentation.

### F1-04 [MEDIUM] manage-skills references "8 pipeline domains" — actual count is 9

**File**: `/home/palantir/.claude/skills/manage-skills/SKILL.md` (lines 46, 60)
**Finding**: Step 3 says "For each of 8 pipeline domains" and Quality Gate says "All 8 pipeline domains". But CLAUDE.md S1 says "35 across 8 pipeline domains + 4 homeostasis + 3 cross-cutting", and counting unique domains from skill descriptions:
1. pre-design (3 skills)
2. design (3 skills)
3. research (3 skills)
4. plan (3 skills)
5. plan-verify (3 skills)
6. orchestration (3 skills)
7. execution (5 skills)
8. verify (5 skills)

That is indeed 8 pipeline domains. However, the skill also needs to cover homeostasis (4 skills) and cross-cutting (3 skills) — a total of 11 domain groups. The "8 pipeline domains" phrasing excludes the skill's own domain (homeostasis) and cross-cutting from its coverage scope check.
**Impact**: manage-skills would not detect missing homeostasis or cross-cutting skills.
**Fix**: Change to "all 11 domain groups" (8 pipeline + homeostasis + cross-cutting + delivery) or explicitly state that homeostasis/cross-cutting are in-scope for the coverage check.

### F1-05 [LOW] Plan-strategy references "4-teammate limit per group" — should be "per execution phase"

**File**: `/home/palantir/.claude/skills/plan-strategy/SKILL.md` (line 33)
**Finding**: Step 2 says "Within 4-teammate limit per group" but the constraint is per execution phase (CLAUDE.md doesn't actually state a hard 4-teammate limit — it's a practical limit). The orchestration-verify skill (line 44) says "teammate count <=4" per phase, which is more accurate.
**Impact**: Minor inconsistency in constraint language across skills.
**Fix**: Standardize constraint language: "4-teammate limit per execution phase" across all skills that reference it.

### F1-06 [LOW] Inconsistent "SKILL N of M" domain position numbering

**File**: Multiple skill descriptions
**Finding**: Some skills use "skill N of M" in their DOMAIN field (e.g., "skill 1 of 3", "skill 3 of 5"), which is useful for routing. However, execution domain says "skill 1 of 5" through "skill 5 of 5" which is correct. Plan domain says "skill 1 of 3" through "skill 3 of 3" which is correct. All numbering is consistent. No actual issue found upon full check. WITHDRAWN.

### F1-07 [ADVISORY] Several skill L2 bodies lack specific tool name references in methodology steps

**File**: Multiple skills
**Finding**: While most skills reference specific tools (Glob, Grep, Read, Task, etc.) in their methodology, several use generic language:
- `research-audit`: Steps reference "Read" and "map" but don't mention specific CC tools
- `plan-verify-correctness/completeness/robustness`: Steps are all Lead-reasoning (no tool calls specified)
- `orchestration-decompose/assign/verify`: Steps reference "use Agent L1" but no specific tool invocations
**Impact**: These are Lead-direct skills where the "tool" is Lead's own reasoning — so generic language is arguably correct. However, plan-verify skills could benefit from specifying "Read plan output files" explicitly.
**Fix**: Add "Read" tool references to plan-verify skills for concrete methodology.

### F1-08 [ADVISORY] Quality Gates mostly use qualitative criteria, few have numeric thresholds

**File**: Multiple skills
**Finding**: Most Quality Gates are specific enough (e.g., "Zero critical findings", "All 4 dimensions have >=1 requirement", ">=90% coverage"). Some are qualitative but appropriate (e.g., "No circular dependencies"). The quality level is generally good.
Best practice examples: plan-verify-completeness (>=90% coverage), verify-quality (average >75/100), verify-content (>80% utilization).
**Impact**: Minimal. Quality Gates serve as internal checkpoints, not automated validation.

### F1-09 [ADVISORY] No skill references obsolete patterns (RTD, DIA, coordinator)

**File**: All 35 skills
**Finding**: Comprehensive grep confirms zero references to obsolete patterns:
- "RTD" — not found in any skill L2 body
- "DIA" — not found (except as substring in other words)
- "coordinator" — not found
- "architect" — not found as an agent role reference
These were all cleaned in v10.1. Confirmed clean.

---

## Focus Area 2: cc-reference Cache Accuracy

### F2-01 [HIGH] native-fields.md "Our Usage Pattern" section is stale

**File**: `/home/palantir/.claude/projects/-home-palantir/memory/cc-reference/native-fields.md` (lines 84-91)
**Finding**: Lines 85-89 state:
```
- All 6 agents use: name, description, tools (explicit allowlist), maxTurns
- 6 agents use: memory: project (all agents)
- 6 agents use: color (visual distinction in tmux)
- 1 agent uses: model (pt-manager: `model: haiku` for cost optimization)
- 0 agents use: permissionMode, skills, mcpServers, hooks, disallowedTools
```
Multiple inaccuracies after Iteration 3 fixes:
1. "6 agents use: memory: project (all agents)" — **WRONG**. delivery-agent and pt-manager now use `memory: none`. Only 4 agents use `memory: project`.
2. "1 agent uses: model (pt-manager)" — **WRONG**. delivery-agent also now uses `model: haiku`. Should say "2 agents use: model".
3. Line 37: "All 32 skills use:" — **WRONG**. There are 35 skills total, with 4 having `disable-model-invocation: true` and 31 auto-loaded. The "32" is a stale count from before SRC added 3 skills.
4. Line 38: "7 skills use: argument-hint" — needs verification. Current count: brainstorm, delivery, resume, self-improve, task-management, manage-codebase, pipeline-resume = 7. This is correct.

**Impact**: Other agents (or Lead during self-improve) reading cc-reference as ground truth will have incorrect agent configuration data.
**Fix**: Update lines 85-89 to reflect current state: 4 agents with memory:project, 2 with memory:none, 2 with model:haiku. Update "32" to "35" on line 37.

### F2-02 [MEDIUM] context-loading.md references wrong skill count for budget

**File**: `/home/palantir/.claude/projects/-home-palantir/memory/cc-reference/context-loading.md` (line 37)
**Finding**: Line 37 says "Our budget usage: 35 skills, 4 have disable-model-invocation:true, so ~31 L1s loaded". This is correct for count. However, line 38 says "Post-optimization (v10.3): all 27 auto-loaded descriptions" — should be 31 (35 total minus 4 disabled = 31 auto-loaded).
**Cross-check**: Looking at the actual skill files:
- `disable-model-invocation: true`: brainstorm, delivery-pipeline, pipeline-resume, task-management = 4 skills
- Remaining auto-loaded: 35 - 4 = 31 skills
Line 38's "27" is stale from pre-SRC when there were 32 skills total (32-5=27, and there were also 5 disabled back then — wait, checking: the 4 current disabled are brainstorm, delivery, resume, task-management. Pre-SRC there were 32 skills and 4 disabled = 28 auto-loaded. The "27" is simply wrong either way.
**Impact**: Budget analysis calculations would be off.
**Fix**: Change "27" to "31" on line 38.

### F2-03 [MEDIUM] context-engineering.md agent memory section is stale

**File**: `/home/palantir/.claude/projects/-home-palantir/memory/context-engineering.md` (lines 79-83)
**Finding**: Lines 80-81 say:
```
- 4 of 6 agents configured: analyst, researcher, implementer, infra-implementer (`memory: project`)
- 2 without memory: delivery-agent (terminal), pt-manager (procedural)
```
This was accurate pre-Iteration 3 but now delivery-agent and pt-manager explicitly have `memory: none`. The description says "2 without memory" which is technically still correct (none = no memory), but the actual frontmatter now says `memory: none` explicitly rather than omitting the field. This is a minor accuracy issue.
**Impact**: Low — the functional behavior is the same, but the description should note the explicit `memory: none` configuration for accuracy.
**Fix**: Update to: "2 with explicit memory: none (delivery-agent, pt-manager) — no persistent memory needed for terminal/procedural roles."

### F2-04 [LOW] hook-events.md timeout values don't match settings.json

**File**: `/home/palantir/.claude/projects/-home-palantir/memory/cc-reference/hook-events.md` (lines 238-247)
**Finding**: Hook configuration section documents:
- SubagentStart: timeout 10s — matches settings.json (line 43)
- PreCompact: timeout 30s — matches settings.json (line 56)
- SessionStart:compact: timeout 15s — matches settings.json (line 69)
- PostToolUse:Edit|Write: timeout 10s — **DOES NOT MATCH** settings.json (line 83 shows `"timeout": 5`)
- SubagentStop:implementer: timeout 30s — **DOES NOT MATCH** settings.json (line 96 shows `"timeout": 15`)

Two timeouts in cc-reference/hook-events.md are wrong:
1. on-file-change.sh: documented as 10s, actual is 5s
2. on-implementer-done.sh: documented as 30s, actual is 15s
**Impact**: Reference data would mislead anyone debugging timeout issues.
**Fix**: Update hook-events.md lines 239 and 247 to match actual settings.json values (5s and 15s respectively).

### F2-05 [LOW] hook-events.md on-file-change.sh description says "async: false" — actual is async: true

**File**: `/home/palantir/.claude/projects/-home-palantir/memory/cc-reference/hook-events.md` (line 239)
**Finding**: Line 239 says `Timeout: 10s, async: false` but settings.json line 84 shows `"async": true`. The hook IS async.
**Impact**: Misleading documentation about hook execution model. An async hook means its output is delivered on the NEXT turn, and it cannot return blocking decisions.
**Fix**: Update to `Timeout: 5s, async: true`.

---

## Focus Area 3: Hook Logic Edge Cases

### F3-01 [HIGH] on-file-change.sh is async but tries to be synchronous — output never reaches anyone

**File**: `/home/palantir/.claude/hooks/on-file-change.sh`
**Settings**: `/home/palantir/.claude/settings.json` (line 84: `"async": true`)
**Finding**: The hook has `"async": true` in settings.json. Per CC hook mechanics:
- Async hooks run in the background
- Their stdout is NOT processed for the current turn
- Async hook results are delivered on the NEXT conversation turn
- Importantly: `additionalContext` from async hooks IS injected when results arrive

The hook produces NO stdout output (exit 0 with no JSON), so async is fine for this use case — it's a pure logger. However, there is a subtle issue: if the hook takes longer than timeout (5s) and fails, the error is silently swallowed since it's async. With `set -euo pipefail`, if `jq` fails or `echo >> "$LOGFILE"` fails (e.g., /tmp full), the hook exits non-zero, and the error is silently lost.

More critically: on-file-change.sh writes to `/tmp/src-changes-${SESSION_ID}.log`, and on-implementer-done.sh reads from that same file. If the PostToolUse hook (async) hasn't finished writing by the time SubagentStop fires (sync), there could be a race condition where the log file is incomplete. In practice, the implementer will make many tool calls before finishing, so the last few async writes should complete before SubagentStop fires. But the LAST Edit/Write call's async hook could theoretically still be running when SubagentStop fires immediately after the implementer's final tool call.

**Impact**: Potential for the last file change to be missed in the SRC impact analysis. The window is small (5s timeout) but theoretically possible.
**Fix**: Either (a) add a small `sleep 1` at the start of on-implementer-done.sh to ensure async hooks drain, or (b) document this as an accepted limitation in src-architecture.md. Option (b) is more appropriate since the risk is very low and the fix introduces its own latency cost.

### F3-02 [MEDIUM] on-pre-compact.sh task directory discovery may find wrong directory

**File**: `/home/palantir/.claude/hooks/on-pre-compact.sh` (lines 22-29)
**Finding**: When `CLAUDE_CODE_TASK_LIST_ID` is not set, the script falls back to:
```bash
for d in /home/palantir/.claude/tasks/*/; do
    [ -d "$d" ] && TASK_DIR="$d" && break
done
```
This takes the FIRST directory found by glob expansion, which is filesystem-ordered (usually alphabetical by UUID). This may not be the most recent or relevant task list. If multiple sessions have left task directories, this could snapshot the wrong one.
**Impact**: Pre-compact snapshot may contain tasks from a different session, leading to confusing recovery state.
**Fix**: Sort by modification time: `TASK_DIR=$(ls -td /home/palantir/.claude/tasks/*/ 2>/dev/null | head -1)` or document that `CLAUDE_CODE_TASK_LIST_ID` should always be set for reliable compaction recovery.

### F3-03 [LOW] on-subagent-start.sh injects generic message — could be more helpful

**File**: `/home/palantir/.claude/hooks/on-subagent-start.sh` (lines 23-30)
**Finding**: When team_name is present, the injected context says:
```
Active team: {team}. Context is managed via PERMANENT Task.
Use TaskGet on task with subject containing [PERMANENT] for full project context.
```
This is helpful but could be more actionable. It doesn't tell the agent:
- What their assigned task ID is (the hook doesn't have this info)
- Which phase the pipeline is in
- What files they own

However, this information isn't available in the SubagentStart hook input (only agent_type, agent_name, team_name). The hook is doing the best it can with available data.
**Impact**: Minimal — agents get their assignment context from the Task prompt, not the hook.
**Recommendation**: No change needed. The hook provides useful PT discovery guidance.

### F3-04 [LOW] on-pre-compact.sh handles no-task-list gracefully

**File**: `/home/palantir/.claude/hooks/on-pre-compact.sh` (lines 30-45)
**Finding**: If no task directory exists (`TASK_DIR` is empty), the script reaches the `if [ -n "$TASK_DIR" ]` check and skips the snapshot. This is correct — it exits 0 cleanly. The error handling is sound.
However, if the task directory exists but contains no JSON files, the `for f in "$TASK_DIR"*.json` loop pattern is `"$TASK_DIR"*.json` which is missing a `/` separator. If TASK_DIR is `/home/palantir/.claude/tasks/uuid/`, the glob becomes `/home/palantir/.claude/tasks/uuid/*.json` which is correct because TASK_DIR from the loop already ends with `/`. This is fine.
**Impact**: None — correctly handled.

---

## Focus Area 4: Agent Body Quality

### F4-01 [LOW] analyst.md says "Write output to assigned paths only" but doesn't specify who assigns

**File**: `/home/palantir/.claude/agents/analyst.md` (line 28)
**Finding**: The constraint says "Write output to assigned paths only — never modify source files" and also "Write output to assigned L1/L2/L3 paths only" (inherited from system prompt). The agent doesn't know what "assigned paths" means without the task prompt specifying them. This relies on Lead providing path assignments in the spawn prompt.
**Impact**: Minimal — Lead always provides output paths in task prompts. The constraint serves as a safety reminder.

### F4-02 [LOW] implementer.md says "Cannot: Task, WebSearch, WebFetch" but doesn't mention TaskCreate/TaskUpdate individually

**File**: `/home/palantir/.claude/agents/implementer.md` (line 8)
**Finding**: The L1 description says `CANNOT: Task, WebSearch, WebFetch. No sub-agent spawning, no web access.` The `tools` list in frontmatter doesn't include any Task tools, which is correct. However, the agent COULD receive Task tools indirectly if Lead passes task context. In practice, the `tools` allowlist prevents this — implementer only has Read, Glob, Grep, Edit, Write, Bash, and sequential-thinking.
**Impact**: None — the `tools` allowlist is the authoritative constraint, not the body text.

### F4-03 [ADVISORY] delivery-agent and pt-manager bodies could reference their new model:haiku and memory:none configurations

**File**: `/home/palantir/.claude/agents/delivery-agent.md`, `/home/palantir/.claude/agents/pt-manager.md`
**Finding**: After Iteration 3 added `model: haiku` and `memory: none` to both agents, the body text doesn't mention these configurations. The bodies focus on behavioral guidelines and safety constraints, which is appropriate. However, adding a brief note about the model/memory configuration could help future maintenance.
**Impact**: Purely informational — the frontmatter is authoritative, not the body.
**Recommendation**: Optional — add a line like "Runs on Haiku model for cost efficiency. No persistent memory (terminal/procedural role)."

### F4-04 [ADVISORY] infra-implementer.md says "Cannot delete files" — this is incorrect

**File**: `/home/palantir/.claude/agents/infra-implementer.md` (line 36)
**Finding**: The constraint says "Cannot delete files — only create and modify." However, the infra-implementer has the `Write` tool which CAN create files with empty content (effectively deleting content), and the `Edit` tool can replace all content. More importantly, the agent could use Write to create a file at a path, overwriting existing content. The "cannot delete" constraint is about not having `Bash(rm)` — which is true since infra-implementer lacks Bash. But the body wording implies a broader restriction than what the tools enforce.
**Impact**: The constraint is functionally correct (no `rm` capability) but could be more precise.
**Fix**: Rephrase to: "Cannot delete files (no Bash/rm access) — only create and modify via Write/Edit."

---

## Cross-Cutting Observations

### F5-01 [ADVISORY] MEMORY.md says "v10.3" for CLAUDE.md version — now v10.5

**File**: `/home/palantir/.claude/projects/-home-palantir/memory/MEMORY.md`
**Finding**: The "Current INFRA State" table says:
```
| CLAUDE.md | v10.3 | 47L | Protocol-only + Section 2.1 (P0-P2 Lead-only rule) |
```
But CLAUDE.md is now v10.5 (updated in Iteration 2). The MEMORY.md version reference is 2 versions behind.
**Note**: This was reported in the original audit as version drift. It was listed as "CLAUDE.md version v10.5" in the "Already Fixed" list, meaning CLAUDE.md itself was fixed to v10.5, but the MEMORY.md reference table was NOT updated.
**Impact**: Lead consulting MEMORY.md gets stale version info for CLAUDE.md.
**Fix**: Update MEMORY.md table row: `| CLAUDE.md | v10.5 | 47L | Protocol-only + Section 2.1 |`

---

## Priority Fix Order

### Immediate (pre-commit):
1. **F2-01** [HIGH]: Update native-fields.md agent usage pattern (memory:none, model:haiku counts)
2. **F3-01** [HIGH]: Document async race condition acceptance in SRC or add sleep guard
3. **F2-04 + F2-05** [LOW]: Fix hook-events.md timeout values and async flag
4. **F2-02** [MEDIUM]: Fix context-loading.md "27" → "31" auto-loaded skill count
5. **F5-01** [ADVISORY]: Update MEMORY.md CLAUDE.md version to v10.5

### Next iteration:
6. **F1-01** [MEDIUM]: Remove "Set mode: default" from execution-code and execution-cascade
7. **F1-02** [MEDIUM]: Clarify P0-P2 skill bodies re: run_in_background vs Team teammates
8. **F1-03** [MEDIUM]: Add claude-code-guide plugin dependency note + fallback
9. **F1-04** [MEDIUM]: Fix manage-skills domain coverage scope (8 → 11 domain groups)
10. **F3-02** [MEDIUM]: Fix on-pre-compact.sh task directory discovery order

### Deferred (low priority):
11-20: LOW and ADVISORY items — address during next self-improve cycle

---

## Validation Checklist

- [x] All 35 skill L2 bodies read and analyzed
- [x] All 4 cc-reference files read and cross-validated against current state
- [x] All 5 hooks read and edge cases analyzed
- [x] All 6 agent bodies read and validated
- [x] settings.json cross-referenced for hook configuration accuracy
- [x] CLAUDE.md cross-referenced for version and count accuracy
- [x] Zero overlap with "Already Fixed" items from Iterations 1-3
- [x] No CRITICAL findings — system is operationally stable
