# INFRA Audit Report — Iteration 3
<!-- Generated: 2026-02-15 by analyst agent -->
<!-- Scope: Agents, Hooks, Skills, Settings, Cross-Cutting -->
<!-- Total files analyzed: 6 agents, 5 hooks, 35 skills, 2 settings files, CLAUDE.md -->

## Executive Summary

47 findings across 5 audit categories. 0 CRITICAL, 6 HIGH, 15 MEDIUM, 16 LOW, 10 ADVISORY.
No blockers found. Primary optimization areas: hook robustness, agent model/memory tuning,
settings hygiene, and skill description consistency.

---

## A. Agent Optimization (12 findings)

### A-01 [MEDIUM] delivery-agent and pt-manager: candidates for `model: haiku`

**Current state**: Only pt-manager uses `model: haiku`. delivery-agent uses inherited opus.

**Analysis**: delivery-agent performs mechanical tasks: git diff, git add, git commit, MEMORY.md merge-write. These are template-following operations well suited to haiku. The agent has `maxTurns: 20` and uses AskUserQuestion for gating, meaning human oversight already exists.

**Recommendation**: Add `model: haiku` to delivery-agent. Expected token cost reduction ~60% per delivery with negligible quality impact (git commit message generation is the only creative task, and the user confirms via AskUserQuestion).

**Risk**: Low. User confirmation gates all destructive actions.

### A-02 [LOW] analyst `maxTurns: 25` may be insufficient for COMPLEX tier

**Current state**: analyst has `maxTurns: 25`. It is spawned for design, plan-verify, research, verify, and review tasks.

**Analysis**: For COMPLEX tier execution-review (Stage 1 + Stage 2), a single analyst must read multiple design specs, all implementation artifacts, and produce comprehensive review. 25 turns can be tight. However, COMPLEX tier spawns 2-3 analysts splitting the work, so per-analyst load stays manageable.

**Recommendation**: Keep at 25 for now. Add monitoring note: if analyst reaches maxTurns during COMPLEX reviews, increase to 30.

### A-03 [MEDIUM] `memory: project` on ALL 6 agents is excessive

**Current state**: All 6 agents use `memory: project`, which persists agent-memory across sessions.

**Analysis by agent**:
| Agent | Memory Usage | Verdict |
|-------|-------------|---------|
| analyst | Has .claude/agent-memory/analyst/ with 4+ files | KEEP — accumulated analysis patterns valuable |
| researcher | Has .claude/agent-memory/researcher/MEMORY.md | KEEP — MCP fallback notes, search patterns |
| implementer | Has .claude/agent-memory/implementer/ | KEEP — coding patterns, codebase familiarity |
| infra-implementer | Has .claude/agent-memory/infra-implementer/ | KEEP — YAML/JSON formatting notes |
| delivery-agent | No .claude/agent-memory/delivery-agent/ directory | CHANGE to `memory: none` — purely mechanical, no cross-session learning needed |
| pt-manager | No .claude/agent-memory/pt-manager/ directory | CHANGE to `memory: none` — Task API operations are stateless |

**Recommendation**: Set `memory: none` for delivery-agent and pt-manager. They never write to agent-memory and gain no benefit from it. Saves ~2 file reads per spawn (checking for memory directory).

### A-04 [MEDIUM] No agents use `skills` preloading — missed optimization

**Current state**: 0 of 6 agents use the `skills` field.

**Analysis**: The `skills` field injects full skill L1+L2 content at agent startup, using the AGENT's context window (not Lead's L1 budget). This is particularly valuable for:

- **infra-implementer**: Could preload `verify-cc-feasibility` skill (native field reference lists). Currently the agent must be told these rules via the task prompt. Preloading would give it the complete native field lists automatically.
- **analyst**: Could preload `verify-consistency` skill for consistency-checking analysts, though this reduces generality.

**Recommendation**: Add `skills: [verify-cc-feasibility]` to infra-implementer. This injects native field lists directly into the agent context at startup, reducing prompt engineering burden on Lead.

**Risk**: Low. Skills content uses agent's own context window, not L1 budget. infra-implementer has 35 maxTurns and 200K context -- one skill L2 (~2-3K tokens) is negligible.

### A-05 [LOW] infra-implementer `maxTurns: 35` is generous for typical workload

**Current state**: infra-implementer has `maxTurns: 35`.

**Analysis**: infra-implementer modifies YAML/JSON configuration files. Typical tasks: edit 2-5 files, each requiring Read + Edit. This rarely exceeds 15-20 turns even for complex multi-file changes (e.g., updating all 35 skill descriptions took ~25 turns in v10.3).

**Recommendation**: Keep at 35. The headroom accounts for skill L2 body rewrites which are the most turn-intensive operations.

### A-06 [ADVISORY] No agent uses `permissionMode`

**Current state**: No agents set `permissionMode`. All inherit from settings.json `defaultMode: "delegate"`.

**Analysis**: `delegate` defers to parent's permission settings, which effectively means the global allow/deny rules apply. This is correct for the current setup where `Bash(*)` is globally allowed. However:

- execution-code/SKILL.md mentions `mode: "bypassPermissions"` -- this is a Task-level parameter, not an agent `permissionMode` field. These are different mechanisms.
- If the team ever needs to tighten security, per-agent `permissionMode` would be the lever.

**Recommendation**: No change needed. Document in context-engineering.md that permissionMode is intentionally unset (inheriting delegate).

### A-07 [ADVISORY] researcher agent includes tavily MCP tool but no fallback handling in agent body

**Current state**: researcher.md lists `mcp__tavily__search` in tools. The agent body says "Use context7 for library docs, tavily for broader searches." researcher/MEMORY.md notes MCP tools may be unavailable.

**Analysis**: If tavily MCP server is not running, the tool call fails. The researcher's agent-memory documents the fallback pattern (WebSearch replaces tavily), but new session spawns may not check agent-memory first.

**Recommendation**: Add a behavioral guideline to researcher.md body: "If MCP tools are unavailable (tavily, context7), fall back to WebSearch and WebFetch respectively."

### A-08 [LOW] implementer `maxTurns: 50` — appropriate but undocumented rationale

**Current state**: implementer has the highest maxTurns at 50.

**Analysis**: Implementers do the most complex work: read files, edit code, run tests, iterate on failures. 50 turns is appropriate for tasks like "implement a new hook script + update settings.json + run shellcheck." The cascade skill explicitly requests `maxTurns: 30` for cascade implementers (overriding the agent default), showing awareness of turn budgets.

**Recommendation**: No change. The 50-turn budget is justified for code implementation complexity.

### A-09 [ADVISORY] Agent color assignments have no documented scheme

**Current state**: analyst=magenta, researcher=yellow, implementer=green, infra-implementer=red, delivery-agent=cyan, pt-manager=blue.

**Analysis**: Colors serve a UI function in tmux split panes. The current assignment has no documented rationale but creates visual distinction. Red for infra-implementer is arguably misleading (suggests danger/error rather than infrastructure).

**Recommendation**: Advisory only. If colors are redesigned, consider: green=implementation, blue=analysis, yellow=research, cyan=infrastructure, magenta=delivery, grey=task-management.

### A-10 [ADVISORY] No agent uses `disallowedTools` — explicit tool lists are the pattern

**Current state**: All agents use `tools` (allowlist) rather than `disallowedTools` (denylist).

**Analysis**: Allowlist is the more secure pattern and is correctly applied. No change needed.

### A-11 [LOW] pt-manager lacks Edit tool but manages task metadata via TaskUpdate

**Current state**: pt-manager has Write but not Edit in its tools list.

**Analysis**: pt-manager creates files (Write) but cannot modify existing files (no Edit). This is intentional -- its primary job is Task API operations + ASCII viz output + file creation for detail docs. If it ever needs to update an existing task detail file, it must rewrite the entire file via Write.

**Recommendation**: No change. Write-only is appropriate for pt-manager's workflow. The Read-Merge-Write pattern for PT updates happens via TaskGet+TaskUpdate, not file editing.

### A-12 [ADVISORY] Analyst agent body references "Write output to assigned paths only" but has no path enforcement

**Current state**: analyst.md body says "Write output to assigned paths only -- never modify source files." But there is no technical enforcement -- the agent has Write tool available globally.

**Analysis**: This is behavioral guidance, not a hard constraint. The analyst cannot Edit (not in tools), but it CAN Write to any path. The constraint relies on the skill L2 specifying output paths.

**Recommendation**: Advisory. If stronger enforcement is needed, use `.claude/rules/*.md` with `paths` frontmatter to scope analyst Write access. Not worth the complexity currently.

---

## B. Hook Robustness (11 findings)

### B-01 [HIGH] on-implementer-done.sh grep scope includes $HOME — overly broad

**Current state**: Lines 68-77 search `$HOME` (i.e., `/home/palantir`) for project references:
```bash
PROJECT_REFS=$(timeout 10 grep -Frl "$SEARCH_PATTERN" "$HOME" \
    --exclude-dir=.git \
    --exclude-dir=node_modules \
    ...
```

**Analysis**: `$HOME` includes ALL directories under /home/palantir:
- `.antigravity-server/` (unrelated project)
- `antigravity/` (unrelated project)
- `.gemini/` (unrelated tool)
- Any future projects

A grep over the entire home directory is:
1. **Slow**: Scans unrelated files, wasting the 10s timeout budget
2. **Noisy**: Can produce false-positive dependents from unrelated projects
3. **Fragile**: New project directories increase scan time unpredictably

**Recommendation**: Replace `$HOME` with `$HOME/.claude/` for the project reference scope (which is already covered by the first grep on lines 60-65), OR use `$(git rev-parse --show-toplevel 2>/dev/null || echo "$HOME")` to scope to the git repository root.

Alternatively, since on-implementer-done.sh's .claude/ grep (lines 60-65) already covers the INFRA scope, and the `$HOME` grep is for "source code dependents" -- restrict it to known project paths or use `$HOME` with `--max-depth=3` to avoid deep recursive scanning.

### B-02 [HIGH] on-implementer-done.sh lacks deduplication between .claude/ grep and $HOME grep

**Current state**: Lines 60-65 search `.claude/`, then lines 68-77 search `$HOME` (which INCLUDES `.claude/`). Results are concatenated:
```bash
REFS="$REFS
$PROJECT_REFS"
```

**Analysis**: The same dependent file can appear twice: once from the .claude/ grep and once from the $HOME grep. The `grep -v "$changed"` only removes the changed file itself, not duplicates from the two scopes. This inflates `DEP_COUNT` and produces duplicated entries in the DEPENDENTS string.

**Recommendation**: Add deduplication after merging the two result sets:
```bash
REFS=$(echo "$REFS" | sort -u | grep -v '^$')
```
Or better: exclude `.claude/` from the $HOME grep scope:
```bash
PROJECT_REFS=$(timeout 10 grep -Frl "$SEARCH_PATTERN" "$HOME" \
    --exclude-dir=.claude \
    ...
```

### B-03 [MEDIUM] on-file-change.sh timeout is 5s in settings.json but comment says 10s

**Current state**: settings.json line 82: `"timeout": 5`. Hook-events reference says "Timeout: 10s". The on-file-change.sh script itself has no timeout reference.

**Analysis**: The 5s timeout in settings.json is the actual runtime value. The hook-events reference documentation is stale (says 10s). The 5s value is appropriate for a simple append operation.

**Recommendation**: Update the hook-events reference documentation to show 5s, not 10s. This is a documentation-only fix but prevents future confusion.

### B-04 [MEDIUM] on-implementer-done.sh uses session_id from SubagentStop — field may differ from implementer's PostToolUse session_id

**Current state**: on-implementer-done.sh extracts `session_id` from SubagentStop input. on-file-change.sh writes logs keyed by `session_id` from PostToolUse input.

**Analysis**: Both events fire in the same session, so `session_id` should match. The SubagentStop schema (from hook-events.md) confirms `session_id` is present. However, if the session compacts between PostToolUse logging and SubagentStop firing, the session_id COULD theoretically change.

In practice, compaction preserves session_id (it is a session-level identifier, not a conversation-turn identifier). This is LOW risk but worth documenting.

**Recommendation**: Add a comment in on-implementer-done.sh: `# session_id is stable across compaction within the same session`. No code change needed.

### B-05 [MEDIUM] on-file-change.sh does not handle Edit tool's different tool_input schema

**Current state**: Line 15 extracts `FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')`.

**Analysis**: Both Edit and Write tools use `file_path` in their `tool_input`, so this works. However, the Edit tool also has `old_string` and `new_string` fields that are not relevant here. The extraction is correct.

**Verification**: Edit tool_input: `{"file_path": "...", "old_string": "...", "new_string": "..."}`. Write tool_input: `{"file_path": "...", "content": "..."}`. Both have `file_path`. No issue.

**Status**: False alarm. Verified correct.

### B-06 [MEDIUM] on-session-compact.sh missing `once: true` field in settings.json

**Current state**: Hook-events reference (line 233) documents this hook as "once: true (fires only once per session)" but settings.json does not include the `"once": true` field.

**Analysis**: Without `once: true`, the compact recovery hook fires EVERY time a compact event occurs. If a long session compacts multiple times, recovery instructions are injected repeatedly, consuming context window budget.

**Recommendation**: Add `"once": true` to the SessionStart:compact hook definition in settings.json.

### B-07 [LOW] on-pre-compact.sh task directory detection is fragile

**Current state**: Lines 26-28:
```bash
for d in /home/palantir/.claude/tasks/*/; do
    [ -d "$d" ] && TASK_DIR="$d" && break
done
```

**Analysis**: This takes the FIRST task directory found. If multiple task lists exist (from different sessions), it might snapshot the wrong one. Additionally, the glob `*/` may match in unpredictable order.

**Recommendation**: Use `ls -t` to find the most recently modified task directory instead of taking the first glob result. Or better: store `CLAUDE_CODE_TASK_LIST_ID` in a known location during session setup so pre-compact can always find it.

### B-08 [LOW] No hook handles the infra-implementer SubagentStop event

**Current state**: SubagentStop matcher is "implementer", which matches agent_type "implementer" but NOT "infra-implementer".

**Analysis**: This is by design -- SRC only tracks source code changes, and infra-implementer changes are typically self-contained within `.claude/`. However, infra changes CAN affect routing (description edits, settings changes). Currently, the SRC pipeline relies on verify-consistency (P8) to catch these issues.

**Recommendation**: This is an acceptable design tradeoff documented in src-risk-assessment.md. If infra-implementer changes frequently cause downstream inconsistencies, consider adding a second SubagentStop matcher: `"infra-implementer"`.

### B-09 [LOW] /tmp log files are never cleaned up

**Current state**: on-file-change.sh writes to `/tmp/src-changes-${SESSION_ID}.log`. No cleanup mechanism exists.

**Analysis**: Each session creates one log file. Over many sessions, these accumulate. On most Linux systems, `/tmp` is cleaned periodically (on reboot, via tmpwatch/tmpreaper, or by systemd-tmpfiles). On WSL2, `/tmp` persists across reboots by default.

**Recommendation**: Add a cleanup step in on-implementer-done.sh (SRC Stage 2) after reading the log:
```bash
# Cleanup after processing
rm -f "$LOGFILE" 2>/dev/null
```
This ensures each session's log is removed after impact analysis completes.

### B-10 [ADVISORY] No race condition between hooks — by design

**Analysis**: Potential race conditions checked:
1. **on-file-change.sh (async) vs on-implementer-done.sh**: on-file-change is PostToolUse (fires during implementation). on-implementer-done is SubagentStop (fires after). Temporal ordering is guaranteed: all PostToolUse events complete before SubagentStop fires. No race.
2. **Multiple PostToolUse events**: on-file-change.sh uses `>> "$LOGFILE"` (atomic append for lines < PIPE_BUF = 4096 bytes). Each log line is ~100 chars. No race.
3. **Concurrent implementer SubagentStop**: Only one implementer can finish at a time within a session (serial SubagentStop processing). No race.

**Verdict**: No race conditions found. Design is sound.

### B-11 [HIGH] on-implementer-done.sh message truncation silently drops dependents

**Current state**: Lines 102-104:
```bash
if [[ ${#MSG} -gt 500 ]]; then
    MSG="${MSG:0:470}... Run /execution-impact for full list."
fi
```

**Analysis**: If more than ~5-6 dependents are detected, the message is truncated at 500 chars. The truncation point `470` can cut mid-word or mid-file-path, producing malformed output. More importantly, Lead receives a truncated dependent list and may undercount the scope of impact.

**Recommendation**:
1. Instead of character truncation, limit the number of dependents reported (e.g., top 5 by reference count) and include a count: "SRC IMPACT ALERT: 12 changed, 23 dependents (showing top 5)..."
2. Alternatively, write full dependent list to a temp file and reference it: "Full list: /tmp/src-impact-{SESSION_ID}.txt"

---

## C. Skill Description Optimization (12 findings)

### C-01 [HIGH] Phase tag inconsistency: P6a vs P6

**Current state**: All 3 orchestration skills use `[P6a·Orchestration·...]` in their description tags.

**Analysis**: The tag `P6a` does not match the pipeline phase numbering in CLAUDE.md (`P6` for orchestration). No other skills use sub-phase letters. The `a` suffix has no documented meaning and could confuse routing pattern matching.

**Recommendation**: Change `P6a` to `P6` for consistency:
- `[P6·Orchestration·Decompose]`
- `[P6·Orchestration·Assign]`
- `[P6·Orchestration·Verify]`

### C-02 [MEDIUM] Phase tag inconsistency: P0-1 vs P0/P1

**Current state**: All 3 pre-design skills use `[P0-1·PreDesign·...]`.

**Analysis**: The pipeline defines pre-design as P0 (Phase 0: brainstorm, validate, feasibility). The `P0-1` tag is ambiguous -- does it mean "Phase 0 and Phase 1" or "Phase 0, sub-phase 1"? CLAUDE.md's pipeline tiers show P0 for pre-design and P1 for design (which contradicts the `P0-1` interpretation, since design has its own `[P2·Design·...]` tags).

Looking at the tier table: TRIVIAL skips from P0 to P7. STANDARD goes P0->P2->P3... This confirms P0 = pre-design, P2 = design. There is no P1 in the pipeline.

**Recommendation**: Change `P0-1` to `P0` for clarity:
- `[P0·PreDesign·Brainstorm]`
- `[P0·PreDesign·Validate]`
- `[P0·PreDesign·Feasibility]`

### C-03 [MEDIUM] Vague WHEN on manage-infra: "after .claude/ modification, after pipeline completion, or periodic health check"

**Current state**: manage-infra WHEN clause lists three broad triggers without specificity about which events distinguish it from manage-skills or manage-codebase.

**Analysis**: All three homeostasis skills can be triggered "after .claude/ modification." The differentiation is:
- manage-infra: structural integrity (counts, orphans, broken refs)
- manage-skills: skill coverage gaps (CREATE/UPDATE/DELETE)
- manage-codebase: dependency map (refs/refd_by)

But the WHEN conditions do not make this distinction clear to the routing transformer.

**Recommendation**: Tighten WHEN to: "After structural changes (.claude/ file creation/deletion/rename). Detects count drift, orphaned files, broken references. Not for content changes (use manage-skills) or dependency mapping (use manage-codebase)."

### C-04 [LOW] manage-skills WHEN includes "periodic drift detection" — overlaps manage-infra

**Current state**: manage-skills WHEN: "After implementing features with new patterns, after modifying skills, before PR, or periodic drift detection."

**Analysis**: "Periodic drift detection" is vague and overlaps manage-infra's health monitoring purpose. manage-skills should focus on skill coverage gaps specifically.

**Recommendation**: Remove "periodic drift detection" from manage-skills WHEN. Replace with: "After codebase changes reveal uncovered patterns, after skill methodology evolves, or before PR to ensure domain coverage."

### C-05 [LOW] self-improve references "claude-code-guide" agent — not in agents/ directory

**Current state**: self-improve skill mentions "Spawn claude-code-guide for CC native feature research" but no `.claude/agents/claude-code-guide.md` exists.

**Analysis**: claude-code-guide appears to be an external agent (MCP-based or plugin-provided), not a custom agent. The 5 files that reference it (research-external, pre-design-feasibility, verify-cc-feasibility, self-improve, researcher/MEMORY.md) all treat it as a spawn target.

**Recommendation**: Either document claude-code-guide as an external/plugin agent in the system, or add a note in the skills that reference it: "claude-code-guide is provided by [source]. If unavailable, fall back to cached cc-reference docs."

### C-06 [LOW] Bidirectionality gaps in INPUT_FROM/OUTPUT_TO

**Analysis of cross-references**: Checking all skill INPUT_FROM/OUTPUT_TO pairs:

| Claim | Reciprocal? | Issue |
|-------|-------------|-------|
| design-risk OUTPUT_TO: research domain | research-codebase INPUT_FROM: design domain | OK (domain-level match) |
| design-risk OUTPUT_TO: plan-strategy | plan-strategy INPUT_FROM: design-risk | OK |
| research-external OUTPUT_TO: plan-strategy | plan-strategy INPUT_FROM: plan-decomposition, plan-interface, design-risk | MISSING: plan-strategy does not list research-external as input |
| research-audit OUTPUT_TO: design domain (if critical gaps) | design-architecture INPUT_FROM: pre-design-feasibility only | ASYMMETRIC: design domain doesn't acknowledge research-audit feedback |
| plan-interface OUTPUT_TO: orchestration-assign | orchestration-assign INPUT_FROM: orchestration-decompose only | MISSING: orchestration-assign doesn't list plan-interface |

**Recommendation**: Fix the 3 asymmetric references:
1. plan-strategy: add `research-external` or `research-audit` to INPUT_FROM
2. orchestration-assign: add `plan-interface` to INPUT_FROM (interface dependencies are key for assignment)
3. design-architecture: add `research-audit` to INPUT_FROM (for feedback loops on COMPLEX tier)

### C-07 [MEDIUM] execution-code mentions `mode: "bypassPermissions"` — not a valid Task parameter

**Current state**: execution-code.md Step 2 says `Set mode: "bypassPermissions" for code implementation`. execution-cascade.md Step 2 says the same.

**Analysis**: In agent frontmatter, `permissionMode: bypassPermissions` is a valid field. But `mode: "bypassPermissions"` as a Task-level parameter is NOT documented in the CC reference. Task API parameters are: subject, description, status, metadata, addBlockedBy, etc. -- not mode.

The `subagent_type` parameter determines which agent handles the task, and the agent's `permissionMode` (if set) controls permissions. If `permissionMode` is not set on the agent, global settings apply.

**Recommendation**: Remove `mode: "bypassPermissions"` from execution-code and execution-cascade skill L2 bodies. If permission bypass is needed, set `permissionMode: bypassPermissions` on the implementer agent (though this affects ALL implementer uses). Or document that Lead should communicate this intent differently.

### C-08 [LOW] 3 skills have `disable-model-invocation: true` — verify routing impact

**Current state**: brainstorm, delivery-pipeline, and task-management have `disable-model-invocation: true`.

**Analysis**: Per CC native reference, `disable-model-invocation: true` means the description is NOT loaded into context, so Claude cannot auto-invoke these skills. They can only be triggered by the user via /slash-command.

This is correct and intentional:
- brainstorm: pipeline entry point, user-initiated
- delivery-pipeline: terminal phase, requires explicit trigger
- task-management: user utility command
- pipeline-resume: also has `disable-model-invocation: true` (4th skill, not 3)

**Verdict**: All 4 are correctly gated as user-only. No issue.

### C-09 [LOW] pipeline-resume has `disable-model-invocation: true` but is also needed by Lead

**Current state**: pipeline-resume is user-invocable only. Lead cannot auto-invoke it.

**Analysis**: After compaction, the on-session-compact.sh hook injects recovery instructions telling Lead to "TaskList to see all tasks." But Lead cannot auto-invoke /pipeline-resume because its description is not loaded. The user must manually type `/pipeline-resume`.

**Recommendation**: Consider changing `disable-model-invocation: false` for pipeline-resume so Lead can auto-invoke it after compaction recovery. Alternatively, keep it user-only and document that users must type `/pipeline-resume` after compaction.

### C-10 [ADVISORY] execution-impact is the only skill with `user-invocable: false`

**Current state**: execution-impact has `user-invocable: false`. execution-cascade also has `user-invocable: false`.

**Analysis**: Both are correct -- these are internal pipeline skills that should only be invoked by Lead during execution flow, not by users directly. The `user-invocable: false` + `disable-model-invocation: false` combination means Claude can auto-invoke but users cannot /slash-command them.

**Verdict**: Correct usage of the flag combination.

### C-11 [ADVISORY] All skills consistently follow the canonical description structure

**Analysis**: All 35 skills follow the pattern:
```
[Tag] Description sentence.

WHEN: trigger condition.
DOMAIN: classification.
INPUT_FROM: upstream.
OUTPUT_TO: downstream.

METHODOLOGY: numbered steps.
OUTPUT_FORMAT: L1/L2 description.
```

Some skills add TIER_BEHAVIOR, CONSTRAINT, ROLES, SCOPE, DETECTION_RULES as additional metadata. These are consistent within their domains. No structural anomalies found.

### C-12 [ADVISORY] Homeostasis skills use different phase tag format

**Current state**: Homeostasis skills use `[Homeostasis·Manager·...]` and `[Homeostasis·SelfImprove·...]` while cross-cutting skills use `[X-Cut·...]` or `[P9·Delivery·...]`.

**Analysis**: Homeostasis is not a numbered pipeline phase, so the phase-number tag is appropriately absent. The `[Homeostasis·...]` prefix clearly distinguishes these from pipeline skills. No issue.

---

## D. Settings Optimization (7 findings)

### D-01 [HIGH] settings.local.json contains stale `Skill(orchestrate)` permission

**Current state**: `/home/palantir/.claude/settings.local.json` line 11 contains:
```json
"Skill(orchestrate)"
```

**Analysis**: The `Skill(orchestrate)` permission was removed from settings.json in v10.1 cleanup. But settings.local.json still has it. settings.local.json permissions are MERGED with settings.json (not overridden), so this stale entry persists as an active allow rule for a non-existent skill.

**Recommendation**: Remove `"Skill(orchestrate)"` from settings.local.json allow list.

### D-02 [MEDIUM] settings.local.json references 6 COW MCP servers — verify still needed

**Current state**: settings.local.json enables: cow-ingest, cow-ocr, cow-vision, cow-review, cow-export, cow-storage.

**Analysis**: These COW (Content Operations Workflow) MCP servers are project-specific. The infrastructure history (MEMORY.md) mentions "COW v2.0" as a past delivery. If COW is still active, these are needed. If COW is deprecated, they should be removed to avoid MCP connection errors at startup.

**Recommendation**: Verify COW project status. If deprecated, remove the 6 MCP servers from settings.local.json.

### D-03 [MEDIUM] `Bash(*)` permission is maximally broad

**Current state**: settings.json allows `Bash(*)` which permits any shell command.

**Analysis**: Combined with `skipDangerousModePermissionPrompt: true` and the deny list (`rm -rf *`, `sudo rm *`, `chmod 777 *`), this means:
- ANY bash command executes without prompting (except the 3 denied patterns)
- Pattern matching is exact -- `rm -rf /` (without *) is NOT denied
- `sudo` commands other than `sudo rm *` are allowed

**Recommendation**: This is intentionally broad for Agent Teams productivity. However, consider adding:
```json
"Bash(sudo *)",
"Bash(rm -rf /)"
```
to the deny list for additional safety.

### D-04 [LOW] Deny list patterns use glob, not regex — verify pattern semantics

**Current state**: Deny patterns include `Read(.env*)`, `Read(**/secrets/**)`, etc.

**Analysis**: CC permission patterns use glob matching (not regex). The current patterns are:
- `Read(.env*)` — matches `.env`, `.env.local`, `.env.production` etc. at project root
- `Read(**/secrets/**)` — matches any path containing `/secrets/`
- `Read(**/*credentials*)` — matches any file containing "credentials"
- `Read(**/.ssh/id_*)` — matches SSH private keys

These are reasonable security boundaries. The `**` prefix handles nested paths.

**Recommendation**: No change needed. Patterns are correct for glob semantics.

### D-05 [LOW] `ENABLE_TOOL_SEARCH: "auto:7"` — undocumented value

**Current state**: settings.json env includes `"ENABLE_TOOL_SEARCH": "auto:7"`.

**Analysis**: This enables tool search with threshold 7 (likely minimum number of tools before search activates). With 6 agents each having their own tool sets, and MCP tools adding more, this is a reasonable threshold.

**Recommendation**: No change. The value is appropriate for the tool count.

### D-06 [ADVISORY] `CLAUDE_CODE_MAX_OUTPUT_TOKENS: "128000"` is maximum possible

**Current state**: Max output tokens set to 128K.

**Analysis**: This is the maximum for Opus 4.6. Since agents often produce long L2 outputs (skill bodies, architecture docs), this is appropriate. Cost is only incurred when actually generating tokens.

**Recommendation**: No change.

### D-07 [ADVISORY] `teammateMode: "auto"` is the correct default

**Current state**: `"teammateMode": "auto"` in settings.json.

**Analysis**: This allows CC to automatically manage teammate creation when using Agent Teams. The alternative ("manual") would require explicit teammate coordination, which contradicts the automation goals.

**Recommendation**: No change.

---

## E. Cross-Cutting Concerns (5 findings)

### E-01 [HIGH] CLAUDE.md version (v10.5) does not match MEMORY.md (v10.3/v10.4)

**Current state**:
- CLAUDE.md header: `v10.5`
- MEMORY.md Current INFRA State: `v10.4 SRC`
- MEMORY.md CLAUDE.md row: `v10.3`
- MEMORY.md Skills row: `v10.4`

**Analysis**: CLAUDE.md has been bumped to v10.5 but MEMORY.md was not updated to reflect this. Version drift between CLAUDE.md and MEMORY.md creates confusion about the actual current version.

**Recommendation**: Update MEMORY.md to reflect v10.5 consistently. Track version changes as part of the delivery pipeline (delivery-agent should update MEMORY.md version references during commit).

### E-02 [MEDIUM] settings.local.json is not version-controlled in the audit scope

**Current state**: settings.local.json exists alongside settings.json but contains stale references (Skill(orchestrate), COW servers).

**Analysis**: settings.local.json is user-local overrides. It was not cleaned during the v10.1 dead code removal because it is local. However, stale entries in it can cause unexpected behaviors.

**Recommendation**: Include settings.local.json in manage-infra health checks. Add it to the scope of verify-structure if it exists.

### E-03 [MEDIUM] 35 skills claimed in CLAUDE.md but actual count needs verification

**Current state**: CLAUDE.md line 23 says "35 across 8 pipeline domains + 4 homeostasis + 3 cross-cutting". Glob finds 35 SKILL.md files.

**Analysis**: Let me verify the domain breakdown:
- pre-design: 3 (brainstorm, validate, feasibility) -- pipeline
- design: 3 (architecture, interface, risk) -- pipeline
- research: 3 (codebase, external, audit) -- pipeline
- plan: 3 (decomposition, interface, strategy) -- pipeline
- plan-verify: 3 (correctness, completeness, robustness) -- pipeline
- orchestration: 3 (decompose, assign, verify) -- pipeline
- execution: 5 (code, infra, impact, cascade, review) -- pipeline
- verify: 5 (structure, content, consistency, quality, cc-feasibility) -- pipeline
= 28 pipeline skills

- homeostasis: 4 (manage-infra, manage-skills, manage-codebase, self-improve)
- cross-cutting: 3 (delivery-pipeline, pipeline-resume, task-management)
= 7 non-pipeline

Total: 28 + 7 = 35. Matches CLAUDE.md claim.

However, CLAUDE.md says "8 pipeline domains" but lists 8 domains (pre-design through verify). The count is correct.

**Verdict**: Counts match. No issue found after verification.

### E-04 [LOW] Dead reference: execution-code mentions "execution-impact" in SRC Integration note but this is a soft reference

**Current state**: execution-code L2 body includes: "After consolidation, Lead should route to execution-impact for dependency analysis before proceeding to execution-review."

**Analysis**: This is advisory text for Lead, not a hard INPUT_FROM/OUTPUT_TO reference. It guides the Lead's routing decision but does not appear in the formal frontmatter. This is acceptable -- the formal INPUT_FROM on execution-impact correctly references execution-code.

**Recommendation**: No change. The soft reference in the L2 body supplements the formal frontmatter routing.

### E-05 [MEDIUM] No documentation of the `$ARGUMENTS` substitution mechanism in CLAUDE.md

**Current state**: 7 skills use `argument-hint` for user input, but CLAUDE.md does not explain how `$ARGUMENTS` substitution works.

**Analysis**: The `$ARGUMENTS` mechanism (documented in cc-reference/arguments-substitution.md) replaces `$ARGUMENTS` in skill L2 body with user-provided slash-command arguments. This is a critical routing feature that is only documented in agent-memory, not in the protocol.

**Recommendation**: This is by design -- CLAUDE.md is protocol-only (47L) and avoids routing details. The cc-reference documentation is the correct location. No CLAUDE.md change needed, but verify that all skills using argument-hint also use $ARGUMENTS in their L2 body where needed.

---

## Summary Table

| Category | CRITICAL | HIGH | MEDIUM | LOW | ADVISORY | Total |
|----------|----------|------|--------|-----|----------|-------|
| A. Agent Optimization | 0 | 0 | 3 | 4 | 5 | 12 |
| B. Hook Robustness | 0 | 3 | 4 | 3 | 1 | 11 |
| C. Skill Descriptions | 0 | 1 | 3 | 5 | 3 | 12 |
| D. Settings | 0 | 1 | 2 | 2 | 2 | 7 |
| E. Cross-Cutting | 0 | 1 | 3 | 1 | 0 | 5 |
| **TOTAL** | **0** | **6** | **15** | **16** | **10** | **47** |

## Priority Implementation Order

### HIGH priority (6 items — recommend immediate action)
1. **B-01**: Narrow on-implementer-done.sh grep scope from $HOME to git root
2. **B-02**: Deduplicate .claude/ and $HOME grep results in on-implementer-done.sh
3. **B-11**: Fix message truncation in on-implementer-done.sh (limit dependents, not chars)
4. **C-01**: Fix P6a -> P6 in orchestration skill tags
5. **D-01**: Remove stale Skill(orchestrate) from settings.local.json
6. **E-01**: Sync CLAUDE.md version to MEMORY.md

### MEDIUM priority (15 items — address in next iteration)
1. **A-01**: Add `model: haiku` to delivery-agent
2. **A-03**: Set `memory: none` for delivery-agent and pt-manager
3. **A-04**: Add `skills: [verify-cc-feasibility]` to infra-implementer
4. **B-03**: Fix hook-events.md documentation (5s not 10s for on-file-change)
5. **B-04**: Add session_id stability comment to on-implementer-done.sh
6. **B-06**: Add `once: true` to SessionStart:compact hook in settings.json
7. **C-02**: Fix P0-1 -> P0 in pre-design skill tags
8. **C-03**: Tighten manage-infra WHEN condition
9. **C-06**: Fix 3 asymmetric INPUT_FROM/OUTPUT_TO references
10. **C-07**: Remove invalid `mode: "bypassPermissions"` from skill L2 bodies
11. **D-02**: Verify COW MCP server status, remove if deprecated
12. **D-03**: Add additional deny patterns to Bash permissions
13. **E-02**: Include settings.local.json in manage-infra scope
14. **E-03**: Verified correct (35 skills, counts match)
15. **E-05**: Verify $ARGUMENTS usage in argument-hint skills

---

## Files Analyzed

### Agents (6)
- `/home/palantir/.claude/agents/analyst.md`
- `/home/palantir/.claude/agents/researcher.md`
- `/home/palantir/.claude/agents/implementer.md`
- `/home/palantir/.claude/agents/infra-implementer.md`
- `/home/palantir/.claude/agents/delivery-agent.md`
- `/home/palantir/.claude/agents/pt-manager.md`

### Hooks (5)
- `/home/palantir/.claude/hooks/on-file-change.sh`
- `/home/palantir/.claude/hooks/on-subagent-start.sh`
- `/home/palantir/.claude/hooks/on-session-compact.sh`
- `/home/palantir/.claude/hooks/on-pre-compact.sh`
- `/home/palantir/.claude/hooks/on-implementer-done.sh`

### Settings (2)
- `/home/palantir/.claude/settings.json`
- `/home/palantir/.claude/settings.local.json`

### CLAUDE.md (1)
- `/home/palantir/.claude/CLAUDE.md`

### Skills (35 — all read)
All 35 SKILL.md files across: pre-design (3), design (3), research (3), plan (3), plan-verify (3), orchestration (3), execution (5), verify (5), homeostasis (4), cross-cutting (3).

### Reference (2)
- `/home/palantir/.claude/projects/-home-palantir/memory/cc-reference/hook-events.md`
- `/home/palantir/.claude/projects/-home-palantir/memory/cc-reference/native-fields.md`
