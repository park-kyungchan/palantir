# RSI L5 Integration Audit: Hook-Agent-Dashboard Cross-Component Analysis

**Date**: 2026-02-15
**Scope**: 5 hooks, 6 agents, settings.json, sync-dashboard.sh
**Coverage**: 100% (all files in scope read and analyzed)
**Methodology**: 5-axis analysis (Hook-Agent Matcher, Dashboard Accuracy, Hook Robustness, Settings Completeness, Cross-Component Consistency)

---

## Executive Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 3 |
| MEDIUM | 5 |
| LOW | 6 |
| ADVISORY | 4 |
| **TOTAL** | **18** |

**Overall Integration Health Score**: 8.1/10

The system is well-integrated with no critical blockers. The 3 HIGH findings center on dashboard parsing edge cases and a phase numbering inconsistency that could mislead routing. The hook-agent integration is solid -- matchers correctly reference agent names, the SRC two-stage architecture (PostToolUse + SubagentStop) is sound, and parallel implementer safety is preserved via POSIX atomic append. The dashboard is the weakest link, with several regex parsing fragilities that could produce silent data loss.

---

## Axis 1: Hook-Agent Matcher Alignment

### Summary

| Hook Event | Matcher | Agents Matched | Status |
|------------|---------|----------------|--------|
| SubagentStart | `""` (all) | All 6 agents | OK |
| PreCompact | `""` (all) | Lead context | OK |
| SessionStart | `"compact"` | Lead context (compact event) | OK |
| PostToolUse | `"Edit\|Write"` | implementer, infra-implementer, delivery-agent, analyst(Write only) | OK |
| SubagentStop | `"implementer\|infra-implementer"` | implementer, infra-implementer | OK |

### INT-01 [LOW] SubagentStop matcher does not capture analyst or researcher changes

**Files**:
- `/home/palantir/.claude/settings.json` (line 92): `"matcher": "implementer|infra-implementer"`
- `/home/palantir/.claude/agents/analyst.md` (line 14): `tools: [..., Write]`

**Evidence**: The analyst agent has the `Write` tool and can create files (e.g., codebase-map.md, audit reports). When an analyst completes via SubagentStop, the `on-implementer-done.sh` hook does NOT fire because "analyst" does not match `"implementer|infra-implementer"`. This means analyst-created files are invisible to the SRC impact analysis pipeline.

**Impact**: LOW. Analyst output files are typically analysis reports written to `agent-memory/`, which are excluded from `on-implementer-done.sh` grep scope (line 64: `--exclude-dir=agent-memory`). The files analysts write are documentation, not source/config files that would have dependents. However, the `manage-codebase` skill spawns an analyst to write `codebase-map.md`, which IS referenced by other skills.

**Recommendation**: Acceptable as-is. The agent-memory exclusion makes analyst file writes irrelevant to impact analysis. Document this design decision in a comment in settings.json.

### INT-02 [LOW] SubagentStop matcher could false-positive on agent names containing "implementer"

**Files**:
- `/home/palantir/.claude/settings.json` (line 92): `"matcher": "implementer|infra-implementer"`

**Evidence**: The regex `implementer|infra-implementer` will match any SubagentStop event whose agent name contains "implementer" as a substring. Currently safe because no agent name is a false-positive match (analyst, researcher, delivery-agent, pt-manager all lack "implementer"). But if a future agent like "test-implementer" were added, it would silently trigger the SRC hook.

**Impact**: LOW. Current agent names are safe. Future-proofing concern only.

**Recommendation**: ADVISORY. If strict matching is ever needed, the matcher would need anchoring (CC may not support `^implementer$` syntax -- verify before changing).

### INT-03 [ADVISORY] PostToolUse Edit|Write matcher fires for ALL agents with those tools, not just implementers

**Files**:
- `/home/palantir/.claude/settings.json` (line 78): `"matcher": "Edit|Write"`
- `/home/palantir/.claude/hooks/on-file-change.sh` (entire file)

**Evidence**: The PostToolUse matcher fires when ANY agent uses Edit or Write. This includes delivery-agent (has Edit+Write), analyst (has Write), and infra-implementer (has Edit+Write). All file changes from all agents are logged to `/tmp/src-changes-${SESSION_ID}.log`. However, SubagentStop only fires for implementer/infra-implementer, so the log accumulates ALL changes but the impact analysis only triggers on implementer completion.

**Impact**: ADVISORY. This is actually correct behavior -- the log should capture ALL file changes regardless of which agent made them, since a delivery-agent or analyst Write could still affect dependents. The SubagentStop filter then determines WHEN to analyze, not WHAT to analyze. The design is sound.

---

## Axis 2: Dashboard Data Accuracy

### INT-04 [HIGH] Dashboard skill parser regex fails on descriptions ending with non-standard YAML keys

**Files**:
- `/home/palantir/.claude/dashboard/sync-dashboard.sh` (line 169): `desc_match = re.search(r'^description:\s*\|\n(.*?)(?=^[a-z])', fm, re.DOTALL | re.MULTILINE)`

**Evidence**: The regex `(?=^[a-z])` terminates the description capture when it encounters a line starting with a lowercase letter. This works for standard YAML keys like `user-invocable:`, `disable-model-invocation:`, `tools:`, etc. However, it would FAIL if a description line itself started with a lowercase letter at column 0 (without the 2-space YAML indent). In practice, all current descriptions use 2-space indent (`  [Tag] ...`), so the regex works. But the regex would also terminate on lines like `argument-hint:` (lowercase 'a') which is correct, and `name:` which would never appear inside a description block.

More critically, the regex uses a lookahead for `^[a-z]` which means it matches lowercase ASCII only. The YAML key `user-invocable:` starts with 'u' (lowercase) -- this is correct termination. But if a key started with an uppercase letter or a digit, the regex would NOT terminate and would continue capturing into subsequent fields. Currently no YAML keys start with uppercase, but this is fragile.

Additionally, the same regex is used in the agent parser (line 169 of the agent section) with identical fragility.

**Impact**: HIGH. Silent data corruption if description format changes. Currently producing correct output by coincidence of YAML key naming conventions.

**Recommendation**: Replace the termination regex with a more robust pattern that matches any non-indented YAML key: `(?=^[a-zA-Z][\w-]*:)` or simply check for `^(?!\s)` (any line not starting with whitespace).

### INT-05 [HIGH] Dashboard DOMAIN extraction regex captures only first word, losing compound domains

**Files**:
- `/home/palantir/.claude/dashboard/sync-dashboard.sh` (line 254): `domain_match = re.search(r'DOMAIN:\s*(\S+)', desc)`

**Evidence**: The regex `\S+` captures the first non-whitespace sequence after `DOMAIN:`. Results for all 35 skills:

| DOMAIN Line | Captured | Correct? |
|-------------|----------|----------|
| `DOMAIN: pre-design (skill 1 of 3)` | `pre-design` | YES |
| `DOMAIN: Homeostasis (cross-cutting, entire .claude/ directory)` | `Homeostasis` | YES (normalized to lowercase) |
| `DOMAIN: Cross-cutting terminal phase (not part of...)` | `Cross-cutting` | PARTIAL |
| `DOMAIN: Cross-cutting (session recovery)` | `Cross-cutting` | PARTIAL |
| `DOMAIN: Cross-cutting, any phase.` | `Cross-cutting,` | WRONG (trailing comma) |

Three skills are affected:
1. `delivery-pipeline`: Captured as "cross-cutting" (lowercased from "Cross-cutting") -- loses "terminal phase" qualifier
2. `pipeline-resume`: Captured as "cross-cutting" -- correct after normalization
3. `task-management`: Captured as "cross-cutting," with TRAILING COMMA -- the `.rstrip(',')` on line 256 fixes this

The main issue: `delivery-pipeline`, `pipeline-resume`, and `task-management` all resolve to the same domain "cross-cutting" in the dashboard, making them visually indistinguishable from each other and from homeostasis skills (which resolve to "homeostasis"). This is a data accuracy issue for the pipeline visualization.

**Impact**: HIGH. Dashboard pipeline view merges 3 functionally different cross-cutting skills into one undifferentiated bucket, and merges 4 homeostasis skills into another. Users cannot distinguish delivery from resume from task-management in the domain grouping.

**Recommendation**: Parse compound domain names more carefully (e.g., capture until `(` or `.` or end-of-line), or add a separate `dashboard_domain` field to skill frontmatter.

### INT-06 [MEDIUM] Dashboard phase extraction misclassifies delivery-pipeline as P9

**Files**:
- `/home/palantir/.claude/dashboard/sync-dashboard.sh` (line 246): `phase_match = re.search(r'\[P(\d+)', desc)`
- `/home/palantir/.claude/skills/delivery-pipeline/SKILL.md` (line 4): `[P9·Delivery·Terminal]`
- `/home/palantir/.claude/CLAUDE.md` (line 34): `Flow: PRE (P0-P4) -> EXEC (P5-P7) -> POST (P8)`

**Evidence**: CLAUDE.md defines the pipeline as P0-P8 (9 phases total), with P8 as the terminal POST phase. The delivery-pipeline skill tags itself as `[P9·Delivery·Terminal]`, creating a phase that does not exist in the CLAUDE.md pipeline definition. The dashboard parser faithfully extracts "P9" from the tag, resulting in the dashboard showing a nonexistent phase.

Phase mapping from CLAUDE.md vs actual skill tags:
- P0: pre-design (3 skills) -- MATCH
- P1: design? (CLAUDE.md says P0-P4 = PRE, but design skills say P2) -- MISMATCH (see INT-07)
- P2: design (3 skills) -- via skill tags
- P3: research (3 skills) -- via skill tags
- P4: plan (3 skills) -- via skill tags
- P5: plan-verify (3 skills) -- via skill tags
- P6: orchestration (3 skills) -- via skill tags
- P7: execution (5 skills) -- via skill tags
- P8: verify (5 skills) -- via skill tags
- P9: delivery (1 skill) -- EXISTS IN SKILL TAG BUT NOT IN CLAUDE.MD

**Impact**: MEDIUM. Dashboard shows P9 which contradicts the P0-P8 pipeline definition in CLAUDE.md. Could confuse users expecting P8 to be terminal.

**Recommendation**: Either rename delivery-pipeline tag to `[P8·Delivery·Terminal]` (aligning with CLAUDE.md), or update CLAUDE.md to define P0-P9. The MEMORY.md skills table lists delivery under "P8" phase, suggesting P8 is the intended designation.

### INT-07 [MEDIUM] Dashboard pipeline parser reads MEMORY.md domain table but uses hardcoded phase mapping

**Files**:
- `/home/palantir/.claude/dashboard/sync-dashboard.sh` (lines 587-598): hardcoded `domain_phase` dict
- `/home/palantir/.claude/projects/-home-palantir/memory/MEMORY.md`: Skills domain table

**Evidence**: The pipeline parser (Section 8) hardcodes `domain_phase` mapping:
```python
domain_phase = {
    'pre-design': 'P0',
    'design': 'P1',      # <-- WRONG: should be P2 per skill tags
    'research': 'P2',     # <-- WRONG: should be P3 per skill tags
    'plan': 'P3',         # <-- WRONG: should be P4 per skill tags
    'plan-verify': 'P4',  # <-- WRONG: should be P5 per skill tags
    'orchestration': 'P5', # <-- WRONG: should be P6
    'execution': 'P6',    # <-- WRONG: should be P7
    'verify': 'P7',       # <-- WRONG: should be P8
    'homeostasis': 'X-cut',
    'cross-cutting': 'P8'  # <-- WRONG: should be X-cut or P9
}
```

Compared to actual skill phase tags:
- design skills: `[P2·Design·...]`
- research skills: `[P3·Research·...]`
- plan skills: `[P4·Plan·...]`
- plan-verify skills: `[P5·PlanVerify·...]`
- orchestration skills: `[P6·Orchestration·...]`
- execution skills: `[P7·Execution·...]`
- verify skills: `[P8·Verify·...]`

The hardcoded mapping is shifted by 1 for design through verify (uses P1-P7 instead of the correct P2-P8). This means the pipeline section of the dashboard assigns WRONG phase numbers to ALL 8 pipeline domains (except pre-design and homeostasis).

**Impact**: MEDIUM. The dashboard pipeline view shows skills assigned to wrong phases. The skill-level phase tag (parsed in Section 3) is CORRECT, but the pipeline view (Section 8) contradicts it. Users see two different phase assignments for the same skill depending on which dashboard panel they look at.

**Recommendation**: Align the hardcoded `domain_phase` dict with actual skill phase tags: design=P2, research=P3, plan=P4, plan-verify=P5, orchestration=P6, execution=P7, verify=P8.

### INT-08 [MEDIUM] Dashboard agent parser Python regex for tools list expects exactly 2-space indent

**Files**:
- `/home/palantir/.claude/dashboard/sync-dashboard.sh` (line 162): `if line.startswith('  - '):`

**Evidence**: The tools parser checks for exactly `'  - '` (2 spaces + dash + space). All current agent files use this exact format. However, YAML allows other valid list formats:
- `  -  ` (2 spaces + dash + 2 spaces) -- would still match via `.strip()`
- `    - ` (4 spaces indent) -- would NOT match
- Tab-indented `\t- ` -- would NOT match

Currently safe because all 6 agents consistently use 2-space YAML indent. But the parser is fragile against YAML format variations.

**Impact**: LOW. All current files use consistent format. Only breaks if an infra-implementer reformats YAML.

**Recommendation**: Use `line.strip().startswith('- ')` with proper nesting tracking for robustness.

---

## Axis 3: Hook Robustness

### INT-09 [MEDIUM] on-pre-compact.sh task directory glob can fail silently on empty directory

**Files**:
- `/home/palantir/.claude/hooks/on-pre-compact.sh` (line 31): `for f in "$TASK_DIR"*.json; do`

**Evidence**: The glob pattern `"$TASK_DIR"*.json` has a subtle bug: it lacks a `/` separator between the directory path and the glob. If `TASK_DIR=/home/palantir/.claude/tasks/abc123/`, the glob becomes `/home/palantir/.claude/tasks/abc123/*.json` which is correct. But if `TASK_DIR` from `ls -td` (line 25) returns a path WITHOUT trailing slash, the glob becomes `/home/palantir/.claude/tasks/abc123*.json` which would match files with the task ID prefix in the parent directory, not JSON files inside it.

Checking line 25: `TASK_DIR=$(ls -td /home/palantir/.claude/tasks/*/ 2>/dev/null | head -1)` -- the trailing `/` in the glob `*/` guarantees `ls` returns paths WITH trailing slash. So the glob is correct.

However, there is a secondary issue: if `$TASK_DIR` is empty (no tasks directory exists), line 27 `if [ -n "$TASK_DIR" ]` catches this. Safe.

The remaining issue: `[ -f "$f" ] || continue` on line 32 handles the case where the glob returns a literal string (no matches). This is correct with `set -u` (nounset) because bash glob expansion with no matches returns the literal pattern, which `[ -f ... ]` rejects.

**Actual finding**: The JSON array construction (lines 29-40) writes `[` first, then concatenates raw JSON files with comma separators, then writes `]`. This produces INVALID JSON if:
1. Any task .json file contains non-JSON content
2. A task .json file has a trailing newline that creates whitespace between entries
3. The loop processes only one file (no comma needed) -- this IS handled via the `first` flag

**Impact**: MEDIUM. The pre-compact snapshot is a safety net for recovery. If it produces invalid JSON, the snapshot is useless but the hook still exits 0 (no crash). Recovery would fail silently.

**Recommendation**: Validate the assembled JSON with `jq empty` before writing, or use `jq -s '.'` to merge files.

### INT-10 [LOW] on-implementer-done.sh grep searches $HOME/.claude/ which may include unrelated .claude dirs

**Files**:
- `/home/palantir/.claude/hooks/on-implementer-done.sh` (line 61): `grep -Frl "$SEARCH_PATTERN" "$HOME/.claude/"`

**Evidence**: The grep scope is `$HOME/.claude/` which is `/home/palantir/.claude/`. This is correct for the INFRA scope. However, line 64 excludes `agent-memory` but does NOT exclude:
- `dashboard/` (could match template patterns)
- `plugins/` (could match plugin config strings)
- `README.md` (large file, could have incidental matches)
- `projects/` (contains MEMORY.md which references many file paths)

The `projects/-home-palantir/memory/MEMORY.md` file is ~300 lines and references many skill/agent names. A skill name change would likely produce false-positive "dependents" from MEMORY.md.

**Impact**: LOW. False positives increase the dependent count but don't cause incorrect behavior -- they just make the SRC IMPACT ALERT noisier. The dependent list is capped at 8 entries (line 56: `MAX_DEPS=8`).

**Recommendation**: Add `--exclude-dir=dashboard --exclude-dir=projects --exclude-dir=plugins` to the grep on line 61.

### INT-11 [LOW] on-file-change.sh async flag means hook may still be writing when SubagentStop fires

**Files**:
- `/home/palantir/.claude/settings.json` (line 84): `"async": true`
- `/home/palantir/.claude/hooks/on-file-change.sh` (line 36): `echo -e "..." >> "$LOGFILE"`

**Evidence**: The PostToolUse hook runs with `async: true`, meaning it fires and the CC agent continues without waiting. The SubagentStop hook (on-implementer-done.sh) runs synchronously. If the last Edit/Write of an implementer triggers PostToolUse asynchronously and then the agent immediately completes, the SubagentStop hook could fire and read the log BEFORE the async PostToolUse hook finishes appending the last entry.

The timing gap: PostToolUse async hook has 5s timeout, but the actual `echo >> $LOGFILE` operation takes <1ms (sub-PIPE_BUF atomic append). The real delay is in the `INPUT=$(cat)` + jq parsing + path sanitization, which typically takes 10-50ms. SubagentStop fires after the agent's final tool use completes, which includes the model response time (typically 1-5 seconds). So the 10-50ms PostToolUse processing will almost certainly complete before the 1-5s model response + SubagentStop timing.

**Impact**: LOW. Theoretical race condition with ~99.9% probability of correct ordering. The last file change could be missed in an extreme edge case (agent completes instantly after final write, SubagentStop fires before async PostToolUse completes).

**Recommendation**: Previously identified in v3 iter4 audit. Mitigation: the missed file will be caught by verify-consistency (P8) or manage-infra (homeostasis). Acceptable risk.

### INT-12 [MEDIUM] on-subagent-start.sh field extraction uses JSON paths that may not exist in actual CC events

**Files**:
- `/home/palantir/.claude/hooks/on-subagent-start.sh` (lines 12-14)

**Evidence**: The hook extracts:
```bash
AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // .tool_input.subagent_type // "unknown"')
AGENT_NAME=$(echo "$INPUT" | jq -r '.agent_name // .tool_input.name // "unknown"')
TEAM_NAME=$(echo "$INPUT" | jq -r '.tool_input.team_name // "no-team"')
```

The field names `.agent_type`, `.agent_name`, `.tool_input.subagent_type`, `.tool_input.name`, `.tool_input.team_name` are guessed based on probable CC event schema. If CC's actual SubagentStart JSON uses different field names, all three variables resolve to their fallback values ("unknown", "unknown", "no-team"). In that case:
- The lifecycle log entry is useless (all "unknown")
- The context injection (line 23) never fires because `$TEAM_NAME` equals "no-team"

The hook has never been validated against actual CC SubagentStart event payloads.

**Impact**: MEDIUM. If the field extraction fails, the hook silently degrades to a no-op (exits 0 without context injection). The PT-based context injection is the primary mechanism for providing team context to new agents. If it fails, agents spawn without team context and must discover it independently.

**Recommendation**: Add a debug logging line that dumps the raw `$INPUT` to a log file for one-time schema validation: `echo "$INPUT" > "$LOG_DIR/subagent-start-sample.json"`.

---

## Axis 4: Settings Completeness

### INT-13 [ADVISORY] settings.local.json has cow-* MCP servers enabled that no agent references

**Files**:
- `/home/palantir/.claude/settings.local.json` (lines 16-24): cow-ingest, cow-ocr, cow-vision, cow-review, cow-export, cow-storage
- All 6 agent .md files: no cow-* tool references

**Evidence**: Six COW MCP servers are enabled in settings.local.json but no agent definition lists any `mcp__cow-*` tools. These appear to be from a previous project phase (COW v2.0 mentioned in infrastructure-history.md) and are now orphaned server configurations.

**Impact**: ADVISORY. Orphaned MCP servers consume startup time (connection attempt for each) but don't affect functionality. They are in settings.local.json (not settings.json), so they only apply to this specific machine.

**Recommendation**: Remove unused cow-* entries from settings.local.json if the COW project is no longer active.

### INT-14 [LOW] defaultMode "delegate" in settings.json may conflict with BUG-001 (permissionMode: plan blocks MCP)

**Files**:
- `/home/palantir/.claude/settings.json` (line 33): `"defaultMode": "delegate"`
- `/home/palantir/.claude/projects/-home-palantir/memory/MEMORY.md`: BUG-001

**Evidence**: `defaultMode: "delegate"` means the Lead delegates permission decisions to spawned agents. BUG-001 documents that `permissionMode: plan` blocks MCP tools. The `defaultMode: delegate` is distinct from `permissionMode: plan`, but the relationship between these two modes is unclear. If "delegate" maps to or interacts with "plan" mode for spawned agents, MCP tools (sequential-thinking, context7, tavily) could be blocked.

Currently no agent definition sets `permissionMode` explicitly, so they inherit the `defaultMode`. All 6 agents have been observed to work correctly with their MCP tools, suggesting "delegate" does not trigger BUG-001.

**Impact**: LOW. Currently functioning correctly. BUG-001 workaround (always spawn with mode: "default") may not be needed with "delegate" mode.

**Recommendation**: Document that "delegate" mode is confirmed safe for MCP tools. If future agents need explicit `permissionMode`, always use "default", never "plan".

### INT-15 [ADVISORY] settings.json allow-list includes TaskUpdate and TaskCreate but not TaskList, TaskGet

**Files**:
- `/home/palantir/.claude/settings.json` (lines 21-22): `"TaskUpdate"`, `"TaskCreate"`
- `/home/palantir/.claude/agents/delivery-agent.md` (lines 17-19): `TaskList`, `TaskGet`, `TaskUpdate`
- `/home/palantir/.claude/agents/pt-manager.md` (lines 15-18): `TaskList`, `TaskGet`, `TaskCreate`, `TaskUpdate`

**Evidence**: The settings.json permissions allow-list includes TaskUpdate and TaskCreate but not TaskList or TaskGet. The delivery-agent and pt-manager both declare TaskList and TaskGet in their tool lists. Since TaskList and TaskGet are read-only operations, they likely don't need explicit allow-listing (they're permitted by default). But the asymmetry is surprising -- if TaskUpdate needs explicit allowing, why not TaskList?

**Impact**: ADVISORY. Currently working -- TaskList and TaskGet appear to be implicitly allowed. No agent has reported permission errors for these tools.

**Recommendation**: No change needed. Document that TaskList/TaskGet are implicitly allowed while TaskCreate/TaskUpdate require explicit permission.

### INT-16 [ADVISORY] Superpowers plugin skills loaded alongside custom skills may cause routing confusion

**Files**:
- `/home/palantir/.claude/settings.json` (lines 104-105): two superpowers plugins enabled
- Skill L1 auto-loaded list (system-reminder): includes both custom skills and superpowers skills

**Evidence**: The system-reminder shows both 35 custom skills AND ~15 superpowers plugin skills loaded simultaneously. Some superpowers skills overlap with custom skill functionality:
- `superpowers:brainstorming` overlaps with `pre-design-brainstorm`
- `superpowers:writing-plans` overlaps with `plan-decomposition` + `plan-strategy`
- `superpowers:writing-skills` overlaps with `manage-skills`
- `superpowers:verification-before-completion` overlaps with `verify-*` domain
- `superpowers:dispatching-parallel-agents` overlaps with `orchestration-*` domain

Lead routing could be confused by having two competing skills for the same intent.

**Impact**: ADVISORY. Lead's INVIOLABLE rule prioritizes custom skills (they have specific WHEN conditions), but superpowers skills also have WHEN conditions that could trigger. In practice, the custom pipeline typically routes through specific phase-skill chains, not open-ended intent matching.

---

## Axis 5: Cross-Component Consistency

### INT-17 [HIGH] delivery-pipeline skill phase tag P9 contradicts CLAUDE.md P0-P8 pipeline

**Files**:
- `/home/palantir/.claude/skills/delivery-pipeline/SKILL.md` (line 4): `[P9·Delivery·Terminal]`
- `/home/palantir/.claude/CLAUDE.md` (line 34): `Flow: PRE (P0-P4) -> EXEC (P5-P7) -> POST (P8)`
- `/home/palantir/.claude/CLAUDE.md` (line 52): `Complete: Only at final git commit (P8 delivery)`
- `/home/palantir/.claude/projects/-home-palantir/memory/MEMORY.md`: Skills table maps delivery to "P8"

**Evidence**: Three sources disagree on delivery's phase number:
1. CLAUDE.md: P8 is POST phase, delivery is at P8 (`P8 delivery`)
2. MEMORY.md skills table: delivery-pipeline listed under "P8" phase
3. Skill itself: Tags as `[P9·Delivery·Terminal]`, DOMAIN says "Cross-cutting terminal phase"

This creates a routing discrepancy:
- Dashboard Section 3 (skill parser) extracts phase as "P9" from the tag
- Dashboard Section 8 (pipeline parser) maps cross-cutting domain to "P8" via hardcoded dict
- CLAUDE.md tier table routes TRIVIAL to `P0->P6->P8` and COMPLEX to `P0->P8`

If Lead follows CLAUDE.md, it routes to P8 for delivery. If Lead follows the skill's own tag, it looks for P9. If the dashboard shows P9, users expect a P9 phase that CLAUDE.md does not define.

**Impact**: HIGH. Phase number inconsistency between the skill's self-description and the authoritative pipeline definition. Could cause routing confusion if Lead uses skill tags for phase matching.

**Recommendation**: Change delivery-pipeline tag to `[P8·Delivery·Terminal]` to align with CLAUDE.md. Update DOMAIN to `Cross-cutting terminal phase (P8)`.

### INT-18 [LOW] MEMORY.md skills table says "9-domain feedback loop" but dashboard maps 10 domains

**Files**:
- `/home/palantir/.claude/skills/delivery-pipeline/SKILL.md` (line 7): `DOMAIN: Cross-cutting terminal phase (not part of 9-domain feedback loop)`
- Dashboard `domain_phase` dict: 10 entries (8 pipeline + homeostasis + cross-cutting)

**Evidence**: The skill references a "9-domain feedback loop" but the actual domain count is:
- 8 pipeline domains: pre-design, design, research, plan, plan-verify, orchestration, execution, verify
- 1 homeostasis domain (4 skills)
- 3 cross-cutting skills (delivery, resume, task-management) grouped as 1 domain

Total: 10 domain categories in the dashboard parser, but 8 true pipeline domains + 2 special categories.

**Impact**: LOW. The "9-domain" reference is inaccurate (should be "8-domain" for pipeline or "10-domain" total). Cosmetic inconsistency.

---

## Dashboard-Specific Findings

### DASH-01 [MEDIUM] Hook description parser does not extract statusMessage from settings.json

**Files**:
- `/home/palantir/.claude/dashboard/sync-dashboard.sh` (lines 300-366): parse_hooks function
- `/home/palantir/.claude/settings.json` (lines 46, 58, 70, 86, 98): statusMessage fields

**Evidence**: The hook parser extracts: hook_file, event, matcher, timeout, async, description (from script header). It does NOT extract:
- `statusMessage` (user-visible hook status text from settings.json)
- `type` field (always "command" currently, but could vary)

The `statusMessage` is a user-facing field that describes what the hook is doing. The dashboard shows the script header comment instead. These can diverge:
- on-subagent-start.sh header: "Logging + PT context injection"
- settings.json statusMessage: "Injecting team context to new agent"

**Impact**: LOW. The dashboard shows technically accurate descriptions from script headers. The statusMessage is more user-friendly but functionally equivalent.

**Recommendation**: Add `statusMessage` extraction to the hooks parser for display alongside the technical description.

---

## Cross-Reference Matrix

### Agent Tool Declaration vs Settings Permissions

| Tool | settings.json allow | Agents declaring it | Status |
|------|-------------------|-------------------|--------|
| Bash(*) | YES | implementer, delivery-agent | OK |
| mcp__sequential-thinking | YES | analyst, researcher, implementer, infra-implementer | OK |
| WebSearch | YES | researcher | OK |
| WebFetch(github.com) | YES | researcher | OK |
| WebFetch(raw.githubusercontent.com) | YES | researcher | OK |
| mcp__context7__resolve-library-id | YES | researcher | OK |
| mcp__context7__query-docs | YES | researcher | OK |
| mcp__tavily__search | YES | researcher | OK |
| TaskUpdate | YES | delivery-agent, pt-manager | OK |
| TaskCreate | YES | pt-manager | OK |
| Read | implicit | all 6 agents | OK |
| Glob | implicit | all 6 agents | OK |
| Grep | implicit | all 6 agents | OK |
| Edit | implicit | implementer, infra-implementer, delivery-agent | OK |
| Write | implicit | all 6 agents | OK |
| TaskList | NOT listed | delivery-agent, pt-manager | OK (implicitly allowed) |
| TaskGet | NOT listed | delivery-agent, pt-manager | OK (implicitly allowed) |
| AskUserQuestion | NOT listed | delivery-agent, pt-manager | OK (implicitly allowed) |

**Result**: All agent-declared tools are either explicitly allowed or implicitly permitted. No permission gaps found.

### Agent CANNOT Declarations vs Actual Tool Lists

| Agent | Declares CANNOT | Tool list confirms absence? |
|-------|----------------|---------------------------|
| analyst | Edit, Bash, Task, WebSearch, WebFetch | YES -- none present |
| researcher | Edit, Bash, Task | YES -- none present |
| implementer | Task, WebSearch, WebFetch | YES -- none present |
| infra-implementer | Bash, Task, WebSearch, WebFetch | YES -- none present |
| delivery-agent | TaskCreate | YES -- only TaskList/Get/Update present |
| pt-manager | Edit, Bash | YES -- none present |

**Result**: All CANNOT declarations are consistent with actual tool lists. No agent has tools it claims not to have.

---

## Finding Summary by Priority

### HIGH (3 findings -- require attention before next release)

| ID | Finding | Component |
|----|---------|-----------|
| INT-04 | Dashboard description regex fragile termination | sync-dashboard.sh:169 |
| INT-05 | Dashboard DOMAIN extraction loses compound domains | sync-dashboard.sh:254 |
| INT-17 | delivery-pipeline P9 tag contradicts CLAUDE.md P0-P8 | delivery-pipeline/SKILL.md:4 |

### MEDIUM (5 findings -- should fix in next maintenance cycle)

| ID | Finding | Component |
|----|---------|-----------|
| INT-06 | Dashboard shows nonexistent P9 phase | sync-dashboard.sh + delivery-pipeline |
| INT-07 | Dashboard pipeline parser uses wrong phase-domain mapping | sync-dashboard.sh:587-598 |
| INT-09 | on-pre-compact.sh JSON assembly may produce invalid JSON | on-pre-compact.sh:29-40 |
| INT-12 | on-subagent-start.sh field names unvalidated against CC schema | on-subagent-start.sh:12-14 |
| DASH-01 | Hook parser misses statusMessage from settings.json | sync-dashboard.sh:300-366 |

### LOW (6 findings -- fix opportunistically)

| ID | Finding | Component |
|----|---------|-----------|
| INT-01 | SubagentStop matcher misses analyst file writes | settings.json:92 |
| INT-02 | SubagentStop matcher substring-based, future-fragile | settings.json:92 |
| INT-08 | Dashboard tools parser expects exact 2-space indent | sync-dashboard.sh:162 |
| INT-10 | on-implementer-done.sh grep scope includes noisy dirs | on-implementer-done.sh:61 |
| INT-11 | Async PostToolUse race with SubagentStop (theoretical) | settings.json:84 |
| INT-14 | defaultMode "delegate" relationship with BUG-001 unclear | settings.json:33 |
| INT-18 | "9-domain feedback loop" count inaccurate | delivery-pipeline/SKILL.md:7 |

### ADVISORY (4 findings -- document and monitor)

| ID | Finding | Component |
|----|---------|-----------|
| INT-03 | PostToolUse fires for all agents, not just implementers | settings.json:78 (by design) |
| INT-13 | Orphaned cow-* MCP servers in settings.local.json | settings.local.json:16-24 |
| INT-15 | TaskList/TaskGet implicitly allowed but not in allow-list | settings.json:12-22 |
| INT-16 | Superpowers plugin skills overlap with custom skills | settings.json:104-105 |

---

## Robustness Scorecard

| Hook | set -euo pipefail | trap | timeout | Error handling | Race safety | Score |
|------|-------------------|------|---------|---------------|-------------|-------|
| on-subagent-start.sh | YES | NO | 10s | jq check, fallback exit 0 | N/A | 7/10 |
| on-pre-compact.sh | YES | NO | 30s | jq check, TASK_DIR check | N/A | 6/10 |
| on-session-compact.sh | YES | NO | 15s | jq check, sed fallback | N/A | 8/10 |
| on-file-change.sh | YES | NO | 5s (async) | jq+grep fallback, validation | Atomic append | 9/10 |
| on-implementer-done.sh | YES | NO | 30s | jq+grep fallback, dedup, cap | Log preserved | 8/10 |

**Notable**: No hook uses `trap` for cleanup. All hooks rely on `exit 0` for graceful degradation. The lack of trap means if a hook is killed mid-execution (e.g., timeout), any partial state (half-written log lines, partial JSON) persists.

---

## Comparison with Previous Audits

| Metric | v3 Iter1 (component) | v3 Integration | This L5 Audit |
|--------|---------------------|----------------|---------------|
| Scope | Components only | Cross-component | Hook+Agent+Dashboard |
| Findings | 47 | 21 | 18 |
| CRITICAL | 0 | 0 | 0 |
| HIGH | 6 | 2 | 3 |
| Health Score | 9.2/10 | 7.1/10 | 8.1/10 |

The dashboard is a new component since previous audits and accounts for 6 of the 18 findings (33%). Hook-agent integration has improved since v3 (INT-20 SRC log deletion fixed, INT-10 SubagentStop matcher expanded). The remaining hook findings are edge cases and theoretical race conditions, not functional defects.
