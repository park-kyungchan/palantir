# INFRA v10.8 Native Optimization Analysis

**Date**: 2026-02-15
**Analyst**: analyst agent (Opus 4.6)
**Scope**: Full INFRA audit — 35 skills, 6 agents, 5 hooks, settings.json, CLAUDE.md, agent-memory, dashboard
**Coverage**: 100% of in-scope files read

---

## Executive Summary

The INFRA v10.8 system is mature (health score 9.2/10 from prior RSI) with 6 levels of recursive self-improvement completed. This analysis identifies **28 optimization opportunities** across 7 categories, focusing on pipeline efficiency, underutilized CC features, and architectural consolidation. The highest-impact findings involve pipeline phase consolidation (saving 40-60% of verification overhead) and leveraging prompt/agent hook types that are defined in the CC reference but currently unused.

| Category | Findings | HIGH | MEDIUM | LOW |
|----------|----------|------|--------|-----|
| Phase Efficiency | 5 | 2 | 2 | 1 |
| Hook Gaps | 6 | 2 | 3 | 1 |
| Agent Configuration | 4 | 1 | 2 | 1 |
| Settings Gaps | 3 | 0 | 2 | 1 |
| Skill Consolidation | 5 | 1 | 3 | 1 |
| Memory/Context | 3 | 0 | 2 | 1 |
| Architecture | 2 | 1 | 1 | 0 |
| **Total** | **28** | **7** | **15** | **6** |

---

## 1. Phase Efficiency (5 findings)

### OPT-01: P4 Plan-Verify Consolidation [HIGH]

**Current State**: 3 parallel analysts (correctness, completeness, robustness) spawned as separate agent instances. Each reads the same plan-strategy + design-architecture inputs. Efficiency rated 4/10 in prior analysis.

**Evidence**:
- `/home/palantir/.claude/skills/plan-verify-correctness/SKILL.md` — 232 lines
- `/home/palantir/.claude/skills/plan-verify-completeness/SKILL.md` — 243 lines
- `/home/palantir/.claude/skills/plan-verify-robustness/SKILL.md` — 284 lines
- All three share identical Receives From (plan-strategy, design-architecture), identical PASS/FAIL routing (orchestration-decompose if PASS, plan domain if FAIL)
- The "parallel-capable" notation exists in all three descriptions, meaning Lead spawns 3 analyst agents reading the same data

**Proposed Improvement**: Merge into a single `plan-verify` skill with a unified analyst spawn. The DPS template can request all three checks (correctness, completeness, robustness) in a single analyst session. The three checking dimensions become methodology steps, not separate skills.

**Rationale**:
- Each analyst spawns in a SEPARATE 200K context window (per `context-loading.md`), reads the same plan-strategy L1 + design-architecture L1 — this is 3x the context loading cost for the same input data
- A single analyst with maxTurns:40 can perform all three checks sequentially
- The plan-verify-correctness Step 2 mapping matrix, plan-verify-completeness Step 2 traceability matrix, and plan-verify-robustness Step 2 edge cases are non-overlapping checks that share context naturally
- Quality gate: combined PASS requires all three dimensions PASS — same as current 3-skill AND logic

**Impact**: HIGH — eliminates 2 agent spawns, reduces P4 from 3 parallel agents to 1, saves ~10-15 min and ~400K tokens (2 avoided 200K context windows)
**Effort**: MEDIUM — merge 3 SKILL.md files into 1, update CLAUDE.md counts (35->33), update all INPUT_FROM/OUTPUT_TO references, dashboard sync
**Risk**: LOW — the three checks are already defined as "parallel-capable" meaning they have no dependencies between them; combining into sequential steps in one agent is strictly safer (shared context means cross-check synergies)

### OPT-02: P7 Verify Conditional Execution [HIGH]

**Current State**: 5 sequential verify stages: structure -> content -> consistency -> quality -> cc-feasibility. All primarily check `.claude/` files. Each stage spawns 1 analyst. Efficiency rated 5/10.

**Evidence**:
- `/home/palantir/.claude/skills/verify-structure/SKILL.md:40-54` — skip conditions exist but require ALL conditions met
- `/home/palantir/.claude/skills/verify-content/SKILL.md:67-71` — skip conditions mention "only hook .sh files changed"
- `/home/palantir/.claude/skills/verify-quality/SKILL.md:65-68` — skip if "Previous quality run scored >90 average"
- `/home/palantir/.claude/skills/verify-cc-feasibility/SKILL.md:79-89` — skip conditions explicitly documented

**Proposed Improvement**: Add a verify-router (Lead-inline decision) that categorizes changes and skips inapplicable stages:

| Change Type | Required Stages | Skippable |
|------------|----------------|-----------|
| L2 body only | None (skip all) | structure, content, consistency, quality, cc-feasibility |
| Frontmatter only | structure, cc-feasibility | content, consistency, quality |
| New skill/agent | All 5 | None |
| Source code only | None (skip all) | All 5 (verify is `.claude/`-scoped) |

Additionally, merge verify-structure + verify-content into a single `verify-structural-content` skill (both check individual files independently — no cross-file dependency between them). This reduces sequential stages from 5 to 4 (or 3 with skipping).

**Impact**: HIGH — for the common case (frontmatter-only edits), reduces verification from 5 stages to 2. For L2-body-only edits, skips P7 entirely.
**Effort**: MEDIUM — update skip-condition logic in CLAUDE.md or Lead's routing awareness, optionally merge 2 skills
**Risk**: MEDIUM — verify-quality depends on verify-consistency's PASS output. If consistency is skipped, quality runs without relationship confirmation. Mitigation: quality has explicit skip conditions already.

### OPT-03: P2 Research-Audit COMPLEX-Only [MEDIUM]

**Current State**: `research-audit` skill exists as third research skill. Per MEMORY.md pending analysis, efficiency rated 6/10.

**Evidence**:
- `/home/palantir/.claude/skills/research-audit/SKILL.md` — only meaningfully used in COMPLEX tier
- STANDARD tier uses research-codebase + research-external (sufficient for 3-file changes)
- COMPLEX tier adds research-audit for cross-module compliance checking

**Proposed Improvement**: Add `disable-model-invocation: true` to research-audit and route it ONLY from Lead when tier is COMPLEX. For STANDARD tier, P2 uses only codebase + external.

**Impact**: MEDIUM — reduces L1 budget consumption by ~800-900 chars (research-audit description excluded from auto-load). Slightly faster STANDARD pipelines.
**Effort**: LOW — single frontmatter change + CLAUDE.md tier table note
**Risk**: LOW — research-audit is already rarely invoked for non-COMPLEX work

### OPT-04: P1 Design STANDARD Streamlining [MEDIUM]

**Current State**: STANDARD tier runs all 3 design skills (architecture, interface, risk). For 3-file changes, full design is often over-engineered.

**Evidence**:
- Per MEMORY.md: "P1 Design interface+risk (7/10): Consider STANDARD running architecture-only"
- STANDARD criteria: "3 files, 1-2 modules" — interface contracts and formal risk assessment add limited value at this scale

**Proposed Improvement**: For STANDARD tier, run only design-architecture (produces component structure). Skip design-interface and design-risk. The architecture output contains sufficient design decisions for a 3-file change.

**Impact**: MEDIUM — eliminates 2 analyst spawns for STANDARD tier P1 phase
**Effort**: LOW — Lead routing decision only, no skill file changes needed (CLAUDE.md tier table already says "Lead overrides skill-level WHEN conditions")
**Risk**: LOW — for 3-file changes, interface contracts are typically trivial and risk is bounded

### OPT-05: P3 Plan STANDARD Streamlining [LOW]

**Current State**: STANDARD tier runs all 3 plan skills (decomposition, interface, strategy). For 3-file changes, full planning is excessive.

**Evidence**:
- Per MEMORY.md: "P3 Plan strategy (7/10): Consider STANDARD running decomposition-only"
- plan-interface and plan-strategy add value primarily for COMPLEX multi-module work

**Proposed Improvement**: For STANDARD tier, run only plan-decomposition. The decomposition output is sufficient to drive orchestration for 3-file scope.

**Impact**: LOW — eliminates 2 Lead-direct steps (plan is often Lead-direct anyway)
**Effort**: LOW — Lead routing decision only
**Risk**: LOW — plan-strategy mainly adds phasing/sequencing which is trivial for 3 files

---

## 2. Hook Gaps (6 findings)

### OPT-06: Add Prompt Hook for Commit Message Quality [HIGH]

**Current State**: No Stop or TaskCompleted hooks exist. The delivery-agent creates commit messages without automated quality checks.

**Evidence**:
- `/home/palantir/.claude/projects/-home-palantir/memory/cc-reference/hook-events.md:29-76` — documents `prompt` and `agent` hook types, neither of which are currently used
- Current hooks: all 5 are type `command` (bash scripts)
- The `prompt` hook type: "Single-turn LLM evaluation (no tool access). Returns `{ ok: true/false, reason: ... }`. Configurable model via `model` field (default: haiku for cost efficiency)"
- `Stop` event available globally, can use prompt type for lightweight verification

**Proposed Improvement**: Add a `Stop` prompt hook on the delivery-agent that validates commit message format:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Check if the agent completed ALL required steps: git commit created, MEMORY.md updated, PT marked DELIVERED. Reply {\"ok\": true} or {\"ok\": false, \"reason\": \"missing step: ...\"}",
            "model": "haiku",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

This uses agent-scoped hooks (in `delivery-agent.md` frontmatter `hooks` field) rather than global settings.json. The `prompt` type is cost-efficient (Haiku, no tool access, single turn).

**Impact**: HIGH — catches incomplete delivery-agent runs before they finalize. Currently delivery-agent mistakes (missing MEMORY.md update, incomplete commit) require manual recovery.
**Effort**: LOW — add `hooks` frontmatter to delivery-agent.md (native field per `native-fields.md`)
**Risk**: LOW — prompt hooks are non-blocking by default; `exit 2` (block) behavior only applies if the hook returns `ok: false`

### OPT-07: Add TaskCompleted Agent Hook for Quality Gate [HIGH]

**Current State**: No `TaskCompleted` hook exists. When teammates complete tasks, there is no automated verification that the task output meets quality standards.

**Evidence**:
- `/home/palantir/.claude/projects/-home-palantir/memory/cc-reference/hook-events.md:63-76` — `TaskCompleted` event documented with exit code 2 blocking capability
- `agent` hook type: "Spawns a subagent with tool access (Read, Grep, Glob, Bash) for verification logic. Returns { ok: true } or { ok: false, reason: ... }. Max 50 turns, default 60s timeout."
- No hook currently fires when a task is marked complete

**Proposed Improvement**: Add a global `TaskCompleted` command hook that verifies:
1. If the task was assigned to an implementer/infra-implementer, check that claimed changed files actually exist and were modified
2. If the task had file ownership constraints, verify no ownership violations occurred

```json
"TaskCompleted": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "/home/palantir/.claude/hooks/on-task-completed.sh",
        "timeout": 15,
        "statusMessage": "Verifying task completion quality"
      }
    ]
  }
]
```

The script would read `task_subject` and `task_description` from stdin, check that referenced files exist, and block (exit 2) if critical files are missing.

**Impact**: HIGH — catches silent task failures (task marked complete but deliverables missing). BUG-004 (no cross-agent compaction notification) means some task completions may be incomplete.
**Effort**: MEDIUM — write new hook script (~40-60 lines), add to settings.json
**Risk**: MEDIUM — false positives could block legitimate completions. Mitigation: start with logging-only (exit 0 always) for 1-2 sessions, then enable blocking.

### OPT-08: Add SessionEnd Hook for Cleanup [MEDIUM]

**Current State**: No `SessionEnd` hook exists. SRC change logs (`/tmp/src-changes-*.log`) accumulate in `/tmp` without explicit cleanup.

**Evidence**:
- `/home/palantir/.claude/hooks/on-implementer-done.sh:98-99` — "Log left in place for parallel implementers... /tmp is ephemeral; log naturally expires with session end"
- `/home/palantir/.claude/projects/-home-palantir/memory/cc-reference/hook-events.md:22` — `SessionEnd` event fires on clear, logout, other
- No cleanup mechanism for `/tmp/claude-hooks/` directory either

**Proposed Improvement**: Add `SessionEnd` hook that cleans up session-scoped temporary files:

```bash
#!/usr/bin/env bash
# Cleanup session-scoped temp files
rm -f /tmp/src-changes-*.log 2>/dev/null
rm -rf /tmp/claude-hooks/ 2>/dev/null
exit 0
```

**Impact**: MEDIUM — prevents /tmp accumulation in long-running WSL2 sessions
**Effort**: LOW — simple script, add to settings.json
**Risk**: LOW — SessionEnd is non-blocking, files are already ephemeral

### OPT-09: SRC Stage 1 Async Race Condition Mitigation [MEDIUM]

**Current State**: `on-file-change.sh` runs with `async: true`. The last file change before SubagentStop could be missed because the async hook hasn't completed when the stop hook fires.

**Evidence**:
- `/home/palantir/.claude/settings.json:84` — `"async": true`
- `/home/palantir/.claude/agent-memory/analyst/infra-audit-v3-iter4.md` — "async race condition in SRC Stage 1 hook (last file change could be missed)"
- `/home/palantir/.claude/hooks/on-implementer-done.sh` — reads log file immediately, no delay

**Proposed Improvement**: Add a 500ms sleep at the start of `on-implementer-done.sh` to allow the last async file-change hook to flush:

```bash
# Allow last async PostToolUse hook to complete
sleep 0.5
```

This is a pragmatic mitigation. The alternative (making Stage 1 synchronous) would add latency to every Edit/Write operation.

**Impact**: MEDIUM — prevents missed impact analysis for the final file change in an implementer session
**Effort**: LOW — single line addition
**Risk**: LOW — 500ms delay on SubagentStop is negligible (30s timeout budget)

### OPT-10: PreCompact Hook Enhancement — L1 Budget Snapshot [MEDIUM]

**Current State**: `on-pre-compact.sh` saves task list snapshots but does not capture the current skill L1 budget usage, which is critical for post-compaction recovery decisions.

**Evidence**:
- `/home/palantir/.claude/hooks/on-pre-compact.sh` — saves task JSON snapshots only
- After compaction, Lead may not remember which skills were near budget limits
- L1 budget at 92% (29,630/32,000 chars) — tight enough that any new skill addition could cause exclusion

**Proposed Improvement**: Add L1 budget estimation to the PreCompact snapshot by counting total description characters across all non-disabled skills:

```bash
# Calculate approximate L1 budget usage
TOTAL_CHARS=$(grep -l 'disable-model-invocation: false' /home/palantir/.claude/skills/*/SKILL.md 2>/dev/null | \
  xargs -I{} awk '/^description:/{flag=1;next}/^[a-z]/{flag=0}flag' {} | wc -c)
echo "[$TIMESTAMP] PRE_COMPACT | L1 budget: ${TOTAL_CHARS}/32000 chars" >> "$LOG_DIR/compact-events.log"
```

**Impact**: MEDIUM — aids post-compaction decision-making about skill additions
**Effort**: LOW — add ~5 lines to existing hook
**Risk**: LOW — additive change, existing functionality unchanged

### OPT-11: on-subagent-start.sh Team Detection Improvement [LOW]

**Current State**: The SubagentStart hook only injects PT context when `team_name` is present, but P0-P1 agents are spawned with `run_in_background` (no team), missing PT context.

**Evidence**:
- `/home/palantir/.claude/hooks/on-subagent-start.sh:23` — `if [ "$TEAM_NAME" != "no-team" ]`
- `/home/palantir/.claude/CLAUDE.md:39` — "P0-P1: Lead with local agents (run_in_background). No Team infrastructure"
- P0-P1 agents don't get PT injection because they're not in a team

**Proposed Improvement**: For P0-P1 background agents, inject a simpler context message (without PT reference) indicating the pipeline phase. Check for `agent_type` patterns:

```bash
if [ "$TEAM_NAME" = "no-team" ] || [ -z "$TEAM_NAME" ]; then
  # Background agent (P0-P1) — inject phase context only
  jq -n '{...additionalContext: "You are a background agent (P0-P1 phase). No PT available yet."}'
fi
```

**Impact**: LOW — P0-P1 agents function correctly without this; they receive their instructions from the Lead's task prompt
**Effort**: LOW — small hook modification
**Risk**: LOW — additive, doesn't change existing team-context path

---

## 3. Agent Configuration (4 findings)

### OPT-12: Analyst Agent — Add Targeted Skill Preloading [HIGH]

**Current State**: Analyst agent has no `skills` frontmatter field. Every analyst spawn receives only the task prompt from Lead + agent body. The DPS template in each skill L2 must recreate all methodology context in the task prompt.

**Evidence**:
- `/home/palantir/.claude/agents/analyst.md` — no `skills` field
- `/home/palantir/.claude/projects/-home-palantir/memory/cc-reference/context-loading.md:55` — "If agent has `skills` field: FULL skill content (L1+L2) preloaded at startup"
- Analyst is used by 19+ skills across all domains — it is the most spawned agent type
- Each DPS template copies methodology steps, quality gates, and output format into the task prompt

**Proposed Improvement**: Do NOT add `skills` preloading for analyst. Despite the apparent efficiency gain, this is a trap:

**Why NOT to implement**:
1. Analyst serves 19+ different skills. Preloading all would inject ~19 * 2KB = ~38K tokens of L2 content into EVERY analyst spawn
2. Per `context-loading.md:118`: "Agent `skills` field preloads FULL content (L1+L2), not just descriptions (context expensive)"
3. The DPS template approach (context-specific methodology injection) is more token-efficient because it provides only the RELEVANT skill's methodology
4. Preloading would fill ~19% of the 200K context window before the analyst even starts work

**Revised Assessment**: The current DPS approach is optimal for multi-skill agents. `skills` preloading is only appropriate for single-skill fork agents (delivery-agent, pt-manager) — and those already have their methodologies in their agent body.

**Impact**: HIGH (avoidance of a harmful change)
**Effort**: N/A (no change needed)
**Risk**: HIGH (implementing this would degrade analyst performance)

### OPT-13: Researcher Agent — Excessive maxTurns [MEDIUM]

**Current State**: Researcher has `maxTurns: 30`, but research tasks typically complete in 10-15 turns.

**Evidence**:
- `/home/palantir/.claude/agents/researcher.md:22` — `maxTurns: 30`
- Research skills (codebase, external, audit) are analysis-focused: read files, search web, write output
- 30 turns = safety margin, but excessive margin means runaway researchers consume resources

**Proposed Improvement**: Reduce to `maxTurns: 20`. This is still generous for research tasks and matches delivery-agent/pt-manager budgets.

**Impact**: MEDIUM — prevents runaway researcher agents from consuming excessive resources
**Effort**: LOW — single field change
**Risk**: LOW — 20 turns is still 2x typical research task duration

### OPT-14: Agent Memory File Bloat [MEDIUM]

**Current State**: Analyst agent-memory contains 17 files (including audit reports from RSI L3-L6). Many are historical audit artifacts that will never be re-read.

**Evidence**:
- `/home/palantir/.claude/agent-memory/analyst/` — 17 files totaling multiple thousand lines
- `MEMORY.md` in analyst agent-memory: 128 lines, all audit summaries
- Per `context-loading.md:56`: "If agent has `memory` field: MEMORY.md first 200 lines auto-loaded into system prompt"
- Analyst MEMORY.md is 128 lines — within budget, but growing toward the 200-line cap
- Historical reports (src-architecture.md, infra-audit-v3.md, etc.) are never auto-loaded but clutter the directory

**Proposed Improvement**:
1. Archive historical audit reports to a `archive/` subdirectory (or delete — they are tracked in git)
2. Trim analyst MEMORY.md to only actionable patterns (remove completed audit summaries)
3. Keep MEMORY.md under 100 lines for safety margin

**Impact**: MEDIUM — prevents MEMORY.md truncation as more audits are recorded
**Effort**: LOW — file moves/deletions
**Risk**: LOW — all data preserved in git history

### OPT-15: Implementer Memory Stale Content [LOW]

**Current State**: Implementer MEMORY.md contains patterns from pre-v10 architecture (DIA Protocol Learnings, Phase sections, Two-Gate System references).

**Evidence**:
- `/home/palantir/.claude/agent-memory/implementer/MEMORY.md:16-27` — DIA Protocol references (DIA was removed in v10)
- `/home/palantir/.claude/agent-memory/implementer/MEMORY.md:46-57` — Phase 0, Phase 1, Phase 1.5 structure (pre-v10 naming)
- These patterns are loaded into every implementer spawn (200 lines auto-loaded)

**Proposed Improvement**: Clean up implementer MEMORY.md: remove DIA references, update phase naming to P0-P8, keep only currently-applicable patterns.

**Impact**: LOW — stale memories don't cause errors (implementer ignores irrelevant context) but waste ~50 tokens per spawn
**Effort**: LOW — edit single file
**Risk**: LOW — removing obsolete patterns has no functional impact

---

## 4. Settings Gaps (3 findings)

### OPT-16: Missing PostToolUseFailure Hook [MEDIUM]

**Current State**: Only `PostToolUse` hook for `Edit|Write` exists. Failed tool uses are unmonitored.

**Evidence**:
- `/home/palantir/.claude/settings.json:76-89` — PostToolUse matcher "Edit|Write" only
- `/home/palantir/.claude/projects/-home-palantir/memory/cc-reference/hook-events.md:14` — `PostToolUseFailure` event available, fires when tool fails
- Failed Edit/Write operations (e.g., old_string not found) are silently swallowed

**Proposed Improvement**: Add a `PostToolUseFailure` hook that logs failed operations:

```json
"PostToolUseFailure": [
  {
    "matcher": "Edit|Write",
    "hooks": [
      {
        "type": "command",
        "command": "/home/palantir/.claude/hooks/on-file-change-fail.sh",
        "timeout": 5,
        "async": true,
        "statusMessage": "Logging failed file operation"
      }
    ]
  }
]
```

The script would log the failure to a session-scoped error log for debugging.

**Impact**: MEDIUM — aids debugging when implementers encounter edit failures (especially "old_string not found" errors that indicate code drift)
**Effort**: LOW — simple script + settings.json addition
**Risk**: LOW — async, non-blocking

### OPT-17: CLAUDE_AUTOCOMPACT_PCT_OVERRIDE Not Set [MEDIUM]

**Current State**: No `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` environment variable is configured. Default is ~95% context usage before auto-compaction.

**Evidence**:
- `/home/palantir/.claude/settings.json:2-10` — env vars defined, but no `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`
- `/home/palantir/.claude/projects/-home-palantir/memory/cc-reference/context-loading.md:98` — `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE: 1-100, Compaction trigger threshold percentage`
- BUG-002 (HIGH): "Large-task teammates auto-compact before L1/L2" — earlier compaction could mitigate this

**Proposed Improvement**: Set `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` to 85 (trigger compaction at 85% context usage instead of ~95%). This gives agents more headroom to finish producing L1/L2 output before compaction.

```json
"CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "85"
```

**Impact**: MEDIUM — reduces probability of BUG-002 (compaction before L1/L2 output). Agents get compacted earlier with more headroom for recovery.
**Effort**: LOW — single env var addition
**Risk**: MEDIUM — earlier compaction means more frequent compactions, potentially losing more context. May need tuning. Start with 90 and observe.

### OPT-18: ENABLE_TOOL_SEARCH Optimization [LOW]

**Current State**: `ENABLE_TOOL_SEARCH` is set to `"auto:7"`. This means tool suggestions activate after 7 tool uses.

**Evidence**:
- `/home/palantir/.claude/settings.json:8` — `"ENABLE_TOOL_SEARCH": "auto:7"`
- This controls when Claude suggests additional tools — unclear if the threshold is optimal

**Proposed Improvement**: This setting appears functional. No change recommended unless specific tool-suggestion issues are observed.

**Impact**: LOW
**Effort**: N/A
**Risk**: N/A

---

## 5. Skill Consolidation (5 findings)

### OPT-19: Plan-Verify 3-to-1 Merge [HIGH] (see OPT-01)

Already detailed in Phase Efficiency section. The three plan-verify skills (correctness, completeness, robustness) can be merged into a single `plan-verify` skill with three methodology sections. This eliminates 2 skill directories, reduces skill count from 35 to 33, frees ~1600 chars of L1 budget.

### OPT-20: Verify-Structure + Verify-Content Merge [MEDIUM]

**Current State**: verify-structure checks file existence, YAML parseability, naming conventions. verify-content checks description utilization, orchestration keys, body sections. Both operate on individual files independently.

**Evidence**:
- `/home/palantir/.claude/skills/verify-structure/SKILL.md` — per-file structural checks
- `/home/palantir/.claude/skills/verify-content/SKILL.md` — per-file content checks
- No cross-file dependency between structure and content checks
- Both spawn analysts that read the same files

**Proposed Improvement**: Merge into `verify-structural-content` — a single analyst reads each file once and performs both structural checks (YAML parse, required fields, naming) and content checks (utilization, orchestration keys, body sections). Reduces verify stages from 5 to 4.

**Impact**: MEDIUM — eliminates 1 analyst spawn and 1 sequential stage in P7
**Effort**: MEDIUM — merge 2 SKILL.md files, update all transition references
**Risk**: LOW — both checks are per-file with no cross-file dependencies

### OPT-21: Orchestration Domain Overhead [MEDIUM]

**Current State**: Orchestration has 3 skills: decompose (Lead-direct), assign (Lead-direct), verify (Lead-direct). All three are Lead-direct — no agent spawning occurs.

**Evidence**:
- `/home/palantir/.claude/skills/orchestration-decompose/SKILL.md:25` — "This skill is always Lead-direct"
- orchestration-assign and orchestration-verify are similarly Lead-direct
- 3 separate Lead-direct skills = 3 separate skill invocations with L2 body loading/unloading

**Proposed Improvement**: Consider merging into a single `orchestration` skill with 3 methodology sections. Since all three are Lead-direct, the L2 body can contain the full decompose->assign->verify flow as sequential steps. This eliminates 2 skill invocations and their L2 load/unload cycles.

**Impact**: MEDIUM — reduces P5 from 3 Lead-direct invocations to 1
**Effort**: MEDIUM — merge 3 SKILL.md files
**Risk**: MEDIUM — the individual skills serve as documentation for distinct concerns. Merging reduces granularity of the pipeline dashboard view.

### OPT-22: Homeostasis manage-infra vs verify-* Overlap [MEDIUM]

**Current State**: `manage-infra` performs "detect configuration drift, stale references, structural decay" — which overlaps significantly with the verify domain (structure, content, consistency, quality, cc-feasibility).

**Evidence**:
- `/home/palantir/.claude/skills/manage-infra/SKILL.md` — inventories files, checks counts, validates settings, detects orphans
- verify-structure does the same file inventory and YAML validation
- verify-consistency does the same count checking and cross-reference validation

**Proposed Improvement**: Clarify scope boundaries rather than merge. Document that manage-infra is the PROACTIVE scan (scheduled health check, detects new issues) while verify-* is the REACTIVE check (triggered after changes, validates specific modifications). Currently the L2 bodies don't explicitly distinguish these roles.

**Impact**: MEDIUM — reduces confusion about when to invoke manage-infra vs verify-*
**Effort**: LOW — documentation update in both skill L2 bodies
**Risk**: LOW — no structural change

### OPT-23: Cross-Cutting Skill Count Optimization [LOW]

**Current State**: 3 cross-cutting skills (delivery-pipeline, pipeline-resume, task-management) plus 4 homeostasis skills = 7 skills outside the pipeline domain. All have `disable-model-invocation: true` (user-only) or are rarely auto-invoked.

**Evidence**:
- delivery-pipeline, pipeline-resume, task-management all have `disable-model-invocation: true`
- These 3 skills consume 0 L1 budget (excluded from auto-load)
- manage-infra, manage-skills, manage-codebase, self-improve are auto-loadable but rarely triggered

**Proposed Improvement**: No consolidation needed. The current separation is appropriate — each has distinct trigger conditions and tool requirements. The `disable-model-invocation: true` skills already have zero L1 budget cost.

**Impact**: LOW (validation that current state is optimal)
**Effort**: N/A
**Risk**: N/A

---

## 6. Memory/Context (3 findings)

### OPT-24: Rules Directory Unused [MEDIUM]

**Current State**: The `.claude/rules/` directory is empty. Per CC reference, rules files supplement CLAUDE.md and support path-scoped conditional loading via `paths` glob patterns.

**Evidence**:
- Glob for `.claude/rules/*.md` returned no files
- `/home/palantir/.claude/projects/-home-palantir/memory/cc-reference/context-loading.md:21-28` — rules directory documented with path-specific loading
- "Supports YAML frontmatter with `paths` glob patterns for conditional loading"

**Proposed Improvement**: Use rules files for path-scoped agent guidelines:

```markdown
---
paths: ["antigravity/**"]
---
# Antigravity Project Rules
- Follow existing codebase patterns in antigravity/
- Test with pytest after changes
```

This would provide project-specific context without bloating the global CLAUDE.md (which is intentionally kept at 54 lines).

**Impact**: MEDIUM — enables per-project coding standards without increasing global context load
**Effort**: LOW — create 1-2 rules files per project directory
**Risk**: LOW — rules supplement CLAUDE.md, they don't override it

### OPT-25: Researcher Memory Growing Stale [MEDIUM]

**Current State**: Researcher MEMORY.md contains patterns from pre-v10 era (DIA, Gate Records, RSIL, Two-Gate System).

**Evidence**:
- `/home/palantir/.claude/agent-memory/researcher/MEMORY.md:19-45` — references to DIA protocol, LDAP, Gate Records, RSIL
- `/home/palantir/.claude/agent-memory/researcher/MEMORY.md:84-110` — Pattern Correlation Analysis, Artifact Signal Analysis (pre-v10 concepts)
- Lines 90-97: "Ultrathink in Skills" documentation contradiction — this was researched in v9 era
- Total: 110 lines, ~40% is stale content from pre-v10 architecture

**Proposed Improvement**: Trim researcher MEMORY.md to retain only currently-applicable patterns:
- Keep: Write Tool Requires Read First, MCP Tool Availability, Context Compaction Recovery, Research Output Format
- Remove: DIA Protocol sections, RSIL/LDAP patterns, Gate Record patterns, pre-v10 architecture references
- Target: ~50 lines (down from 110)

**Impact**: MEDIUM — researchers spawn with ~50 fewer tokens of irrelevant context, faster orientation
**Effort**: LOW — edit single file
**Risk**: LOW — all removed content is in git history

### OPT-26: Agent Memory for delivery-agent and pt-manager [LOW]

**Current State**: Both agents have `memory: none`. They accumulate no learning across sessions.

**Evidence**:
- `/home/palantir/.claude/agents/delivery-agent.md:21` — `memory: none`
- `/home/palantir/.claude/agents/pt-manager.md:20` — `memory: none`
- These agents are fork agents (single-skill, single-use) — memory is intentionally disabled

**Proposed Improvement**: No change. `memory: none` is correct for fork agents that execute a fixed protocol (delivery-pipeline, task-management). Their behavior should be deterministic, not adaptive. Any learning should be captured in the SKILL L2 body or the Lead's MEMORY.md, not the agent's memory.

**Impact**: LOW (validation of current design)
**Effort**: N/A
**Risk**: N/A

---

## 7. Architecture (2 findings)

### OPT-27: Skill-Scoped Hooks for Agent-Specific Behavior [HIGH]

**Current State**: All 5 hooks are global (defined in `settings.json`). The system has no skill-scoped or agent-scoped hooks. Per CC native fields, both skills and agents support `hooks` frontmatter.

**Evidence**:
- `/home/palantir/.claude/projects/-home-palantir/memory/cc-reference/native-fields.md:18` — skills: `hooks | object | no | none | Skill-scoped hook configuration object`
- `/home/palantir/.claude/projects/-home-palantir/memory/cc-reference/native-fields.md:44` — agents: `hooks | object | no | none | Agent-scoped hooks (cleaned up when agent finishes)`
- Current global hooks fire for ALL agents/skills regardless of relevance
- The SRC PostToolUse hook fires on EVERY Edit/Write across ALL agents, even when SRC is not relevant (e.g., during P0 brainstorm)

**Proposed Improvement**: Move SRC hooks (on-file-change.sh, on-implementer-done.sh) to agent-scoped hooks on `implementer.md` and `infra-implementer.md` frontmatter. This eliminates unnecessary hook firing during non-execution phases.

Implementer agent would get:
```yaml
hooks:
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: /home/palantir/.claude/hooks/on-file-change.sh
          timeout: 5
          async: true
```

And SubagentStop would remain global (it fires on the PARENT context, not inside the agent).

**Caveat**: This requires verification that agent-scoped PostToolUse hooks work correctly in the tmux Agent Teams mode. The CC reference confirms it's a native field, but runtime behavior in tmux mode may differ. Test before deploying.

**Impact**: HIGH — eliminates unnecessary hook overhead during P0-P4 phases (no SRC logging when no code is being written)
**Effort**: MEDIUM — move hook config from settings.json to agent frontmatter, verify tmux compatibility
**Risk**: MEDIUM — agent-scoped hooks are a native feature but may have edge cases. Test with a single agent first.

### OPT-28: Pipeline Tier Decision Automation [MEDIUM]

**Current State**: Tier classification (TRIVIAL/STANDARD/COMPLEX) is a manual Lead decision at P0. No automated heuristic beyond the criteria in CLAUDE.md (file count, module count).

**Evidence**:
- `/home/palantir/.claude/CLAUDE.md:28-32` — tier criteria: TRIVIAL (<=2 files, single module), STANDARD (3 files, 1-2 modules), COMPLEX (>=4 files, 2+ modules)
- Lead must estimate file/module count from the user request before any analysis
- Misclassification causes either over-engineering (COMPLEX for a 2-file change) or under-engineering (TRIVIAL for a cross-module change)

**Proposed Improvement**: Add a `PreToolUse` prompt hook on the Skill tool that validates tier classification when a pipeline-entry skill (brainstorm, delivery, task-management) is invoked. The prompt hook can ask the Haiku model to estimate scope from the user's request:

```json
"PreToolUse": [
  {
    "matcher": "Skill",
    "hooks": [
      {
        "type": "prompt",
        "prompt": "Based on the user's request, estimate: (1) number of files likely to change, (2) number of modules/directories involved. Classify as TRIVIAL (<=2 files, 1 module), STANDARD (3 files, 1-2 modules), or COMPLEX (>=4 files, 2+ modules). Reply {\"ok\": true, \"reason\": \"Tier: [TIER]. Estimated [N] files in [M] modules.\"}",
        "model": "haiku",
        "timeout": 10
      }
    ]
  }
]
```

**Impact**: MEDIUM — provides a second opinion on tier classification, reducing misclassification errors
**Effort**: MEDIUM — prompt hook design + testing
**Risk**: MEDIUM — Haiku's estimation may be inaccurate for domain-specific requests. Should be advisory (ok: true always), not blocking.

---

## Consolidated Impact-Effort Matrix

### Quick Wins (HIGH impact, LOW effort)
| ID | Finding | Action |
|----|---------|--------|
| OPT-06 | Prompt hook for delivery-agent completion | Add `hooks` to agent frontmatter |
| OPT-12 | Analyst skill preloading (AVOID) | No change — current DPS approach is optimal |

### High-Value Investments (HIGH impact, MEDIUM effort)
| ID | Finding | Action |
|----|---------|--------|
| OPT-01 | P4 plan-verify 3-to-1 merge | Merge skill files, update references |
| OPT-02 | P7 verify conditional execution | Update routing logic, optionally merge 2 skills |
| OPT-07 | TaskCompleted quality gate hook | New hook script + settings.json |
| OPT-27 | Agent-scoped SRC hooks | Move PostToolUse from global to agent frontmatter |

### Incremental Improvements (MEDIUM impact, LOW effort)
| ID | Finding | Action |
|----|---------|--------|
| OPT-03 | research-audit COMPLEX-only | Add disable-model-invocation: true |
| OPT-08 | SessionEnd cleanup hook | New simple script |
| OPT-09 | SRC async race mitigation | Add sleep 0.5 |
| OPT-13 | Researcher maxTurns reduction | Change 30 -> 20 |
| OPT-14 | Analyst memory cleanup | Archive/delete historical reports |
| OPT-15 | Implementer memory cleanup | Remove stale DIA patterns |
| OPT-16 | PostToolUseFailure logging | New hook for failed operations |
| OPT-17 | Auto-compact threshold | Set env var to 85-90 |
| OPT-24 | Rules directory usage | Create project-specific rules files |
| OPT-25 | Researcher memory cleanup | Remove pre-v10 patterns |

### Deferred / No Action
| ID | Finding | Reason |
|----|---------|--------|
| OPT-18 | ENABLE_TOOL_SEARCH | Functional as-is |
| OPT-22 | manage-infra vs verify-* overlap | Clarify scope, no structural change |
| OPT-23 | Cross-cutting skill count | Already optimal |
| OPT-26 | Fork agent memory | Correctly set to none |

---

## Implementation Priority Recommendation

### Phase 1: Quick Wins + Memory Cleanup (1 session, ~30 min)
1. OPT-14: Archive analyst memory reports
2. OPT-15: Clean implementer MEMORY.md
3. OPT-25: Clean researcher MEMORY.md
4. OPT-09: Add sleep 0.5 to on-implementer-done.sh
5. OPT-13: Reduce researcher maxTurns 30->20
6. OPT-03: Add disable-model-invocation:true to research-audit

### Phase 2: Hook Enhancements (1 session, ~45 min)
1. OPT-06: Add prompt hook to delivery-agent frontmatter
2. OPT-08: Add SessionEnd cleanup hook
3. OPT-16: Add PostToolUseFailure logging hook
4. OPT-17: Set CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=90

### Phase 3: Pipeline Consolidation (1-2 sessions, ~2 hours)
1. OPT-01: Merge plan-verify 3->1 skill
2. OPT-02: Implement verify conditional execution
3. OPT-20: Merge verify-structure + verify-content
4. Update CLAUDE.md, dashboard, all references

### Phase 4: Advanced Architecture (1 session, ~1 hour, requires testing)
1. OPT-27: Move SRC hooks to agent-scoped (test first)
2. OPT-07: Add TaskCompleted hook (deploy logging-only first)
3. OPT-28: Tier classification prompt hook (advisory mode)

---

## Appendix A: L1 Budget Impact Analysis

| Change | Budget Impact (chars) |
|--------|-----------------------|
| OPT-01 (merge 3 plan-verify) | -1600 (remove 2 descriptions) |
| OPT-03 (research-audit disable) | -900 (excluded from auto-load) |
| OPT-20 (merge structure+content) | -800 (remove 1 description) |
| OPT-21 (merge orchestration) | -1600 (remove 2 descriptions, if implemented) |
| **Total potential savings** | **-4900 chars** |
| **Current budget** | 29,630 / 32,000 (92%) |
| **Post-optimization budget** | ~24,730 / 32,000 (77%) |

This would recover 15% of L1 budget headroom, providing capacity for 4-5 new skills without hitting the budget cap.

## Appendix B: Skill Count Impact

| Change | Skill Count Impact |
|--------|--------------------|
| OPT-01 (merge plan-verify) | 35 -> 33 (-2) |
| OPT-20 (merge verify) | 33 -> 32 (-1) |
| OPT-21 (merge orchestration, if implemented) | 32 -> 30 (-2) |
| **Potential final count** | **30 skills** (from 35) |

All merges preserve functionality — no methodology steps are deleted, they become sections within unified skills.

## Appendix C: Token Budget Impact Per Pipeline Execution

| Optimization | Token Savings per Pipeline | Applies To |
|-------------|---------------------------|------------|
| OPT-01 (plan-verify merge) | ~400K (2 avoided 200K contexts) | COMPLEX |
| OPT-02 (verify conditional skip) | ~200K-600K (1-3 avoided analyst spawns) | All tiers |
| OPT-04 (design STANDARD skip) | ~400K (2 avoided analyst spawns) | STANDARD |
| OPT-05 (plan STANDARD skip) | Minimal (Lead-direct steps) | STANDARD |
| OPT-27 (agent-scoped SRC hooks) | ~50K (fewer hook context injections) | All tiers |
| **Total for STANDARD pipeline** | **~600K-1000K tokens** | Per pipeline |
| **Total for COMPLEX pipeline** | **~600K-1000K tokens** | Per pipeline |
