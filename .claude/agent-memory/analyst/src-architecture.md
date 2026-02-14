# SRC Architecture Design Document

> Analyst output | 2026-02-14 | Design-Architecture (P2)
> Scope: SRC (Smart Reactive Codebase) — component architecture, data flow, ADRs
> Inputs: src-validate-report.md (P1), impact-analysis-gap-report.md (P0), cc-reference/*
> Gap Resolution: GAP-IP1, GAP-NF2, GAP-AC7, GAP-F1, GAP-F4, GAP-AC5, GAP-IP5, GAP-EH2

---

## 1. Component Architecture

### Component 1: on-file-change.sh

| Attribute | Value |
|-----------|-------|
| **Type** | Hook script (PostToolUse, matcher: `Edit\|Write`) |
| **Responsibility** | Silently log every file path modified by Edit or Write to a session-scoped change log. No context injection, no analysis. |
| **Inputs** | stdin JSON: `{ session_id, tool_name, tool_input: { file_path }, tool_response: { success } }` |
| **Outputs** | Appends one line per successful edit to `/tmp/src-changes-{session_id}.log`. Format: `{timestamp}\t{tool_name}\t{file_path}` |
| **Dependencies** | jq (for JSON parsing), /tmp filesystem |
| **Constraints** | Timeout: 5s. Async: true (non-blocking to implementer). No additionalContext output (silent). Must handle concurrent writes from parallel implementers (append-only, atomic line writes). Only logs on `tool_response.success == true`. |
| **Error Handling** | If jq unavailable: exit 0 (silent no-op). If /tmp write fails: exit 0 (silent no-op). Never blocks implementer execution. |
| **Size** | ~25 lines shell script |

**Acceptance Criteria (GAP-AC1):**
- Fires on both Edit and Write tool calls (single matcher: `Edit|Write`)
- Does NOT fire on Read, Glob, Grep, Bash calls
- Correctly extracts file_path from tool_input
- Appends to session-specific log file (not shared across sessions)
- Completes within 5s timeout
- Silent: no additionalContext output, no stderr visible to user
- Handles missing jq gracefully (exit 0)

---

### Component 2: on-implementer-done.sh

| Attribute | Value |
|-----------|-------|
| **Type** | Hook script (SubagentStop, matcher: `implementer`) |
| **Responsibility** | When an implementer agent finishes, read the accumulated change log, run reverse-reference grep for each changed file, and inject a consolidated impact summary into Lead's context via additionalContext. |
| **Inputs** | stdin JSON: `{ session_id, agent_type: "implementer", agent_id }`. Reads `/tmp/src-changes-{session_id}.log` from filesystem. |
| **Outputs** | stdout JSON: `{ hookSpecificOutput: { hookEventName: "SubagentStop", additionalContext: "<impact summary>" } }`. additionalContext max 500 chars. |
| **Dependencies** | jq, grep, /tmp/src-changes-{session_id}.log, project codebase |
| **Constraints** | Timeout: 15s. Sync (blocking, so Lead waits for result). additionalContext limited to 500 chars. Must deduplicate file paths from change log. Must exclude the changed files themselves from reverse-reference results. Grep scope: entire repo, but exclude `.git/`, `node_modules/`, `*.log`, `/tmp/`. |
| **Error Handling** | If change log does not exist or is empty: output additionalContext "SRC: No file changes detected." and exit 0. If grep takes >10s: truncate results, append "... analysis truncated". If no reverse references found: output "SRC: 0 impact candidates for N changed files." |
| **Size** | ~60 lines shell script |

**Output Format (additionalContext):**
```
SRC IMPACT ALERT: {N} files changed, {M} potential dependents detected.
Changed: {file1}, {file2}, ...
Dependents: {dep1} (refs {file1}), {dep2} (refs {file1}, {file2}), ...
Action: Consider running /execution-impact for full analysis.
```

If output exceeds 500 chars: truncate dependent list, append `... and {K} more. Run /execution-impact for full list.`

**Acceptance Criteria:**
- Fires only when implementer agents stop (not analyst, researcher, etc.)
- Fires in Lead's context (SubagentStop is global-scope, Lead receives additionalContext)
- Reads change log and produces correct file list
- Runs grep -rl for reverse references within timeout
- Output fits within 500 char limit
- Cleans up change log after reading (optional: leave for multi-implementer scenarios)

**Multi-Implementer Handling:**
- In COMPLEX tier, multiple implementers run in parallel or sequence
- Change log is shared across all implementers within a session
- Hook fires once per implementer stop
- Each firing reads the FULL accumulated log (not just that implementer's changes)
- Deduplication ensures no repeated file analysis
- Change log is NOT cleared between implementer stops (accumulates)
- Lead receives impact alerts after EACH implementer finishes
- Final cleanup: log cleared when execution-impact skill runs or at session end

---

### Component 3: execution-impact (Skill)

| Attribute | Value |
|-----------|-------|
| **Type** | Skill (execution domain, after code/infra, before cascade) |
| **Responsibility** | Full impact analysis of all files changed during execution-code/execution-infra. Classify dependents as DIRECT or TRANSITIVE (max 2-hop). Produce prioritized impact report. |
| **Inputs** | execution-code L1 (file change manifest), on-implementer-done.sh additionalContext (quick impact candidates), optionally codebase-map.md (if available) |
| **Outputs** | L1 YAML impact report, L2 markdown detailed analysis |
| **Dependencies** | researcher agent (spawned for analysis), codebase-map.md (optional, degrades gracefully) |
| **Constraints** | Researcher maxTurns: 30. Grep-only analysis (no AST). Max files to analyze: 50 changed files. Max dependents per file: 30. TRANSITIVE limited to 2-hop. |
| **Error Handling** | If no files changed: skip (output empty impact report). If researcher times out: report partial results with confidence: low. If codebase-map unavailable: proceed with grep-only (degraded mode). |

**L1 Output Schema:**
```yaml
domain: execution
skill: impact
status: complete|partial|skipped
confidence: high|medium|low
files_changed: 0
impact_candidates: 0
impacts:
  - changed_file: ""
    dependents:
      - file: ""
        type: DIRECT|TRANSITIVE
        reference_pattern: ""
    dependent_count: 0
cascade_recommended: true|false
```

**L2 Output:** Markdown report with per-file dependency chains, grep evidence (file:line), and cascade recommendation with rationale.

**Acceptance Criteria (GAP-AC2):**
- Correctly identifies DIRECT dependents (file A contains literal reference to changed file B's name/path)
- Correctly identifies TRANSITIVE dependents (file A references B, B references changed file C, max 2-hop)
- Produces valid L1 YAML parseable by downstream skills
- Researcher completes within maxTurns (30)
- Reports confidence level accurately (high if codebase-map used, medium if grep-only, low if truncated)

---

### Component 4: execution-cascade (Skill)

| Attribute | Value |
|-----------|-------|
| **Type** | Skill (execution domain, after impact, before review) |
| **Responsibility** | Update affected files identified by execution-impact. Spawn implementers for each update group. Iterate until convergence or max 3 iterations. |
| **Inputs** | execution-impact L1 (impact report with dependent file list and classification) |
| **Outputs** | L1 YAML cascade result, L2 markdown update log |
| **Dependencies** | implementer agent (spawned for updates), execution-impact (re-invoked per iteration for convergence check) |
| **Constraints** | Max 3 cascade iterations. Max 2 implementers per iteration. Each implementer maxTurns: 30 (reduced from normal 50 to bound cascade cost). Convergence = no new impacts detected after updates. |
| **Error Handling** | If max iterations reached without convergence: log warning, set status: partial, continue pipeline to execution-review with warning. If implementer fails: retry once, then skip that file and flag it. |

**L1 Output Schema:**
```yaml
domain: execution
skill: cascade
status: converged|partial|skipped
iterations: 0
max_iterations: 3
files_updated: 0
files_skipped: 0
convergence: true|false
warnings: []
```

**L2 Output:** Markdown log of each iteration: what was updated, by which implementer, what new impacts were detected, and final convergence status.

**Convergence Definition (GAP-AC3):**
- After iteration N, re-run grep-based impact check on files modified in iteration N
- If zero new dependents need updating: CONVERGED
- If new dependents detected but iteration count < 3: run iteration N+1
- If iteration count reaches 3 and still not converged: PARTIAL (proceed with warning)
- "Need updating" means: the dependent file contains a reference that is now inconsistent with the change made

**Acceptance Criteria (GAP-AC3):**
- Spawns implementers only for files identified by execution-impact
- Each implementer receives clear instructions on what changed and what to update
- Convergence detected correctly (no false positives)
- Max 3 iterations enforced
- Non-convergence produces explicit warning in L1 output
- Pipeline continues to execution-review after cascade (never blocks indefinitely)

---

### Component 5: manage-codebase (Skill)

| Attribute | Value |
|-----------|-------|
| **Type** | Skill (homeostasis domain, cross-cutting) |
| **Responsibility** | Generate and maintain codebase-map.md. Full regeneration on first run, incremental updates after pipeline execution. Detect stale entries, validate file existence, track hotspots. |
| **Inputs** | Codebase filesystem (Glob/Grep), existing codebase-map.md (if present), git log for recent changes |
| **Outputs** | Updated codebase-map.md, L1 YAML map health report |
| **Dependencies** | analyst agent (spawned for analysis), codebase filesystem |
| **Constraints** | Map size: max 300 lines (covers ~150 files at 2 lines each). Scope: `.claude/` directory primarily. If map exceeds 300 lines: prune least-referenced entries. Analyst maxTurns: 30. |
| **Error Handling** | If codebase-map.md corrupted: regenerate from scratch (full scan). If filesystem scan times out: produce partial map with warning. If map file locked: retry once, then skip update. |

**L1 Output Schema:**
```yaml
domain: homeostasis
skill: manage-codebase
status: complete|partial
mode: full-generation|incremental-update
entries: 0
stale_entries_removed: 0
new_entries_added: 0
map_path: ".claude/agent-memory/analyst/codebase-map.md"
```

**Acceptance Criteria (GAP-AC4):**
- Generates valid codebase-map.md on first run (full scan)
- Incremental updates add new files and remove deleted ones
- Stale entries (referencing non-existent files) detected and removed
- Map stays within 300-line limit
- Map parseable by grep/awk in hook scripts

---

### Component 6: codebase-map.md (Knowledge File)

| Attribute | Value |
|-----------|-------|
| **Type** | Persistent knowledge file (markdown) |
| **Responsibility** | Store per-file dependency data for the `.claude/` INFRA directory. Enable fast lookup of "what depends on file X" without full grep scan. |
| **Location** | `.claude/agent-memory/analyst/codebase-map.md` |
| **Format** | Compact markdown, one section per file, grep-parseable |
| **Size Limit** | Max 300 lines, ~15KB |
| **Lifecycle** | Created by manage-codebase (full scan). Updated incrementally after each pipeline execution. Read by on-implementer-done.sh (optional fast lookup) and execution-impact (enhanced analysis). |

**Schema Per Entry:**
```markdown
## {relative_path}
refs: {comma-separated list of files this file references}
refd_by: {comma-separated list of files that reference this file}
hotspot: {low|medium|high} (based on reference count and change frequency)
updated: {YYYY-MM-DD}
```

**Example:**
```markdown
## .claude/skills/execution-code/SKILL.md
refs: orchestration-verify, execution-review, implementer.md
refd_by: manage-skills/SKILL.md, verify-consistency/SKILL.md, CLAUDE.md
hotspot: medium
updated: 2026-02-14
```

**Design Decisions (GAP-AC5 resolution):**
- Markdown over JSON/YAML: grep-parseable by hook scripts without jq, human-readable
- One entry per file: enables `grep -A4 "## {filename}" codebase-map.md` for fast lookup
- `refs`/`refd_by` are basename-level (not full paths) for compactness
- `hotspot` scoring: high = refd_by count >= 10, medium = 4-9, low = 0-3
- `updated` field enables staleness detection: entries older than 7 days flagged for re-scan
- No MEMORY.md summary needed (map lives in agent-memory, read on demand, not auto-loaded)

**Staleness Detection:**
- Each entry has `updated` date
- manage-codebase compares `updated` dates against `git log --since` for each file
- Files modified after their `updated` date are re-scanned
- Files not found on filesystem are removed from map
- Full regeneration triggered if >30% of entries are stale

---

### Component 7: execution-code SKILL.md (Modification)

| Attribute | Value |
|-----------|-------|
| **Type** | Existing skill modification |
| **Changes** | Add Step 5.5 after consolidation to note that execution-impact should follow. Update OUTPUT_TO to include execution-impact. |

**Specific Changes:**

1. **L1 description**: Add `execution-impact` to OUTPUT_TO list
   - Before: `OUTPUT_TO: execution-review (implementation artifacts for review), verify domain (completed code).`
   - After: `OUTPUT_TO: execution-impact (file changes for impact analysis), execution-review (implementation artifacts for review), verify domain (completed code).`

2. **L2 Step 5 (Consolidate Results)**: Add note after file change manifest:
   ```
   Note: After consolidation, Lead should route to execution-impact
   for dependency analysis before proceeding to execution-review.
   ```

3. **L1 output schema**: No change needed (existing `files_changed` and `tasks[].files` already provide the data execution-impact needs)

---

### Component 8: implementer.md (Modification)

| Attribute | Value |
|-----------|-------|
| **Type** | Existing agent modification |
| **Changes** | Minimal. No behavioral changes needed because the PostToolUse hook captures changes silently. |

**Specific Changes:**

1. **No constraint changes**: The implementer does not need to self-report impact candidates. The two-stage hook architecture handles this externally.

2. **Memory note (optional)**: If implementer memory already mentions DIA/impact patterns, those vestigial notes are now operationally relevant again. No cleanup needed.

**Rationale:** The original gap report (Priority 2) suggested adding `impact_candidates` to implementer L1 output. The two-stage hook architecture eliminates this need. The implementer operates exactly as before; the hook infrastructure captures and analyzes changes transparently.

---

### Component 9: CLAUDE.md (Modification)

| Attribute | Value |
|-----------|-------|
| **Type** | Protocol modification |
| **Changes** | Update skill count (32 -> 35), add SRC awareness to Lead protocol |

**Specific Changes:**

1. **Section 1 Team Identity**: Update "32 skills" to "35 skills across 8 pipeline domains + 4 homeostasis + 3 cross-cutting" (manage-codebase adds 1 to homeostasis)

2. **Section 1 Team Identity**: Update skill domain count if needed (homeostasis grows from 3 to 4 with manage-codebase, or execution grows from 3 to 5 with impact+cascade)

3. **No new protocol section needed**: Lead's behavior change is driven by the SubagentStop hook's additionalContext injection. When Lead sees "SRC IMPACT ALERT", it knows to invoke execution-impact. This is event-driven, not protocol-prescribed.

---

## 2. Data Flow

### Complete Flow: Implementer Edits File to Codebase-Map Updated

```
                         STAGE 1: SILENT LOGGING
                         ========================
[Implementer calls Edit/Write]
    |
    v
[PostToolUse:Edit|Write hook fires]
    |
    v
[on-file-change.sh]
    |-- reads: stdin JSON (tool_input.file_path)
    |-- writes: /tmp/src-changes-{session_id}.log (append)
    |-- output: none (silent, async)
    v
[Implementer continues working... (unaware of hook)]
    |
    v  (repeats for each Edit/Write call)

                         STAGE 2: LEAD NOTIFICATION
                         ===========================
[Implementer finishes (maxTurns or task complete)]
    |
    v
[SubagentStop:implementer hook fires in Lead context]
    |
    v
[on-implementer-done.sh]
    |-- reads: /tmp/src-changes-{session_id}.log
    |-- runs: grep -rl for each changed file
    |-- runs: dedup + truncate to 500 chars
    |-- output: additionalContext -> Lead
    v
[Lead receives additionalContext with SRC IMPACT ALERT]
    |
    v

                         STAGE 3: IMPACT ANALYSIS
                         =========================
[Lead invokes execution-impact skill]
    |
    v
[Lead spawns researcher agent]
    |-- reads: execution-code L1 (file change manifest)
    |-- reads: codebase-map.md (if available)
    |-- runs: grep -rl for each changed file (comprehensive)
    |-- classifies: DIRECT vs TRANSITIVE (2-hop max)
    |-- writes: L1 impact report, L2 detailed analysis
    v
[Lead reads execution-impact L1]
    |-- if cascade_recommended: false -> skip to execution-review
    |-- if cascade_recommended: true -> proceed to cascade
    v

                         STAGE 4: CASCADE UPDATE
                         ========================
[Lead invokes execution-cascade skill]
    |
    v
[ITERATION 1]
    |-- Lead spawns implementer(s) for affected files
    |-- Implementers update files to reflect upstream changes
    |-- PostToolUse hook logs new changes (Stage 1 repeats)
    |-- Implementers finish -> SubagentStop fires (but Lead ignores
    |   second alert during active cascade)
    |-- Lead re-runs grep check on iteration-1 changed files
    |-- New impacts detected? -> ITERATION 2
    v
[ITERATION 2] (if needed)
    |-- Same as iteration 1, on newly-detected impacts
    |-- New impacts detected? -> ITERATION 3
    v
[ITERATION 3] (if needed, FINAL)
    |-- Same as above
    |-- If still not converged: set status: partial, log warning
    v
[Lead reads execution-cascade L1]
    |-- converged: true -> proceed normally
    |-- converged: false -> proceed with warning to execution-review
    v

                         STAGE 5: REVIEW + MAP UPDATE
                         ==============================
[Lead invokes execution-review]
    |-- Review scope includes both original AND cascade-updated files
    |-- Reviewer distinguishes "planned changes" vs "cascade changes"
    v
[Lead invokes manage-codebase (post-pipeline or on next homeostasis cycle)]
    |-- Reads all changed files from execution-code + execution-cascade
    |-- Updates codebase-map.md incrementally
    |-- Removes stale entries, adds new entries
    v
[Pipeline continues to verify -> delivery]
```

### Data Flow Summary Table

| Source | Data | Format | Destination |
|--------|------|--------|-------------|
| Edit/Write tool call | file_path | JSON stdin | on-file-change.sh |
| on-file-change.sh | changed file path | TSV line | /tmp/src-changes-{session_id}.log |
| /tmp change log | accumulated paths | text file | on-implementer-done.sh |
| on-implementer-done.sh | impact summary | additionalContext (500 chars) | Lead context |
| Lead context | SRC alert | natural language | execution-impact skill invocation |
| execution-code L1 | file manifest | YAML | execution-impact researcher |
| codebase-map.md | dependency data | markdown | execution-impact researcher |
| execution-impact L1 | impact report | YAML | execution-cascade skill |
| execution-cascade L1 | cascade result | YAML | execution-review skill |
| All changed files | update data | filesystem | manage-codebase skill |
| manage-codebase | updated map | markdown | codebase-map.md |

---

## 3. Architecture Decision Records

### ADR-SRC-1: Two-Stage Hook Architecture

**Context:**
PostToolUse hooks inject additionalContext into the CALLING AGENT's context, not the parent Lead's context. This means a PostToolUse:Edit hook on an implementer's Edit call injects context into the implementer, which Lead never sees. The original brainstorm design assumed hook output goes to Lead, which is architecturally impossible.

**Decision:**
Split change detection into two stages:
- **Stage 1 (PostToolUse:Edit|Write):** Silent file-based logging. No additionalContext injection. Runs async on the implementer side. Writes changed file paths to a shared temp file.
- **Stage 2 (SubagentStop:implementer):** Fires in Lead's context when the implementer finishes. Reads the accumulated change log, runs quick grep analysis, and injects a consolidated impact summary into Lead's context via additionalContext.

**Consequences:**
- (+) Correctly targets Lead's context for impact awareness
- (+) Batches all file changes into a single analysis (not per-edit noise)
- (+) Stage 1 is async and non-blocking (implementer performance unaffected)
- (-) Slight delay: impact detection happens only after implementer finishes, not in real-time
- (-) Two hook scripts to maintain instead of one
- (-) Change log file requires cleanup logic
- (neutral) Aligns with existing SubagentStart hook pattern (proven additionalContext injection to Lead)

**Resolves:** GAP-IP1 (CRITICAL)

---

### ADR-SRC-2: File-Based Inter-Hook Communication

**Context:**
Stage 1 (PostToolUse) and Stage 2 (SubagentStop) hooks run in different process contexts. There is no shared memory, no IPC mechanism, and no CC-provided inter-hook communication channel. The only shared state accessible to both hooks is the filesystem.

**Decision:**
Use `/tmp/src-changes-{session_id}.log` as the communication channel between hooks.
- Format: one line per change, tab-separated: `{ISO-timestamp}\t{tool_name}\t{file_path}`
- Session-scoped via `{session_id}` in filename (from hook stdin JSON)
- Append-only writes (atomic at line level on Linux for short lines)
- Reader (Stage 2) does NOT delete the file after reading (supports multi-implementer scenarios)
- Cleanup: file naturally expires in /tmp, or explicitly cleaned at session end

**Consequences:**
- (+) Simple, debuggable, no external dependencies
- (+) Survives implementer crashes (file persists)
- (+) Multiple parallel implementers can append concurrently (append-only is safe for short lines)
- (-) /tmp files are ephemeral; lost on system restart (acceptable: SRC is session-scoped)
- (-) No locking mechanism; theoretically possible (but practically negligible) for concurrent reads/writes to interleave
- (-) File grows unbounded within a session (mitigated: typical session has <100 edits = <5KB)

---

### ADR-SRC-3: Execution Domain Sub-Skill Pattern

**Context:**
The original design used phase numbers P7.5 and P7.6 for impact analysis and cascade update. This creates pipeline ambiguity: do sub-phases have their own iteration limits? How do they integrate with INPUT_FROM/OUTPUT_TO? The existing execution domain already has 3 skills (code, infra, review) following a consistent naming pattern.

**Decision:**
Add impact analysis and cascade update as execution domain sub-skills, NOT separate phases:
- `execution-impact` (skill 4 of 5 in execution domain)
- `execution-cascade` (skill 5 of 5 in execution domain, before review renumbers to 5 of 5... actually review becomes skill 5)

Corrected execution domain flow:
```
execution-code ──┐
execution-infra ─┘──> execution-impact ──> execution-cascade ──> execution-review
```

Phase remains P7 (execution). No new phase numbers. Pipeline tier definitions unchanged.

**Consequences:**
- (+) Consistent naming with existing execution-* pattern
- (+) No pipeline tier definition changes needed
- (+) INPUT_FROM/OUTPUT_TO integrates naturally (impact reads from code/infra, outputs to cascade; cascade outputs to review)
- (+) Review scope naturally expands to include cascade-updated files
- (-) Execution domain grows from 3 to 5 skills (largest domain, but manageable)
- (-) Total skill count increases from 32 to 35

**Resolves:** GAP-IP3, GAP-IP4

---

### ADR-SRC-4: Drop SEMANTIC Classification

**Context:**
The original brainstorm proposed classifying dependents as DIRECT, TRANSITIVE, or SEMANTIC. DIRECT and TRANSITIVE are grep-derivable (literal string matching and 2-hop tracing). SEMANTIC ("same interface") requires understanding code semantics, which is impossible with text-based grep alone (no AST parsing is available).

**Decision:**
Drop SEMANTIC classification entirely. Use only:
- **DIRECT**: File A contains a literal reference to changed file B's name, path, or key identifiers (grep match)
- **TRANSITIVE**: File A references file B, and file B references changed file C (2-hop max via sequential grep)

For `.claude/` INFRA files specifically, "reference" means:
- Skill descriptions: INPUT_FROM/OUTPUT_TO values, agent names, skill names
- Agent files: skill names, tool names, path references
- CLAUDE.md: agent names, skill counts, domain names
- Hooks: file paths, agent type names
- Settings: hook script paths, permission patterns

**Consequences:**
- (+) Every classification is mechanically verifiable (grep output as evidence)
- (+) No false positives from fuzzy semantic matching
- (+) Simpler implementation, faster execution
- (-) May miss "conceptual" dependencies (e.g., two skills that share a design pattern but never reference each other). Acceptable: these are maintenance concerns, not correctness issues.
- (-) For future application code extension: may need revisiting (e.g., Python import analysis could use `import` statement parsing). Deferred to when application code scope is activated.

**Resolves:** GAP-F4

---

### ADR-SRC-5: codebase-map.md Location and Format

**Context:**
The codebase-map.md needs a persistent location accessible to: (a) hook scripts (bash, grep), (b) execution-impact researcher (Read tool), (c) manage-codebase analyst (Read/Write tools), and optionally (d) Lead (for context-aware routing). The file must survive across sessions but should not pollute the main project directory. Three candidates: `.claude/project-knowledge/`, `.claude/agent-memory/analyst/`, or project root.

**Decision:**
Location: `.claude/agent-memory/analyst/codebase-map.md`

Rationale:
- analyst agent has `memory: project` configured, meaning `.claude/agent-memory/analyst/` is already auto-loaded into analyst's system prompt
- Hook scripts can read this path directly (absolute path known)
- File is version-controlled with `.claude/` (persists across sessions and branches)
- Does not create a new directory or convention
- analyst agent is the natural owner of codebase knowledge (read-only analysis agent)

Format: Compact markdown with grep-parseable structure (see Component 6 schema above).

NOT stored in MEMORY.md: The map is demand-loaded, not auto-loaded into every agent/session. This avoids consuming the 200-line MEMORY.md budget.

**Consequences:**
- (+) Leverages existing agent-memory infrastructure
- (+) Version-controlled (survives across sessions, branches)
- (+) grep-parseable by hook scripts without jq
- (+) Does not consume MEMORY.md space
- (-) analyst agent's system prompt includes this file (up to 200 lines of memory); codebase-map.md contributes to that 200-line budget. Mitigated: keep map under 300 lines, and analyst MEMORY.md is currently minimal.
- (-) Write access requires analyst or infra-implementer agent (not implementer). Acceptable: manage-codebase skill uses analyst.

**Resolves:** GAP-AC5, GAP-IP5

---

### ADR-SRC-6: Graceful Degradation Strategy

**Context:**
SRC introduces multiple interacting components (2 hooks, 3 skills, 1 knowledge file). Any component can fail independently. The system must degrade gracefully, never blocking the existing pipeline. Pre-SRC behavior (no impact awareness) must remain the fallback.

**Decision:**
Three degradation levels:

| Level | Condition | Behavior |
|-------|-----------|----------|
| **Full SRC** | All components operational, codebase-map.md available | Hook logs changes -> Lead gets impact alert -> execution-impact uses map + grep -> execution-cascade updates -> manage-codebase refreshes map |
| **Degraded SRC** | Hooks work, codebase-map.md unavailable or stale | Hook logs changes -> Lead gets impact alert -> execution-impact uses grep-only (no map) -> execution-cascade proceeds normally -> manage-codebase regenerates map |
| **No SRC** | Hooks fail or not configured | Pre-SRC behavior. Lead reads implementer L1 file_changed list. No impact analysis. No cascade. Pipeline proceeds P7 -> P8 directly. |

Transition triggers:
- Full -> Degraded: codebase-map.md not found, or >50% entries stale (updated date >7 days old), or map parse error
- Full/Degraded -> No SRC: on-file-change.sh errors on every invocation, or settings.json hooks misconfigured, or /tmp filesystem unavailable
- No SRC -> Degraded: Fix hooks, run any edit (change log starts accumulating)
- Degraded -> Full: Run manage-codebase to generate/refresh map

**Non-convergence behavior (GAP-EH2):**
When cascade reaches max 3 iterations without convergence:
1. Set `execution-cascade` L1 status: `partial`, convergence: `false`
2. Add warnings listing unresolved impact candidates
3. Pipeline CONTINUES to execution-review (does NOT abort)
4. execution-review receives the warnings and applies extra scrutiny to unresolved files
5. verify-* phase (P8) catches remaining inconsistencies
6. Delivery (P9) commit message notes "partial cascade convergence"

**Consequences:**
- (+) Pipeline never blocks due to SRC failure
- (+) Each component fails independently without cascading failure
- (+) Degradation is automatic (no manual intervention needed)
- (+) Recovery path is clear (fix component, re-run skill)
- (-) Degraded/No SRC modes lose the benefit of SRC (but this is acceptable since pre-SRC pipeline was functional)

**Resolves:** GAP-EH2

---

### ADR-SRC-7: Context Budget Allocation

**Context:**
The SRC system adds persistent context (3 new skill L1 descriptions) and per-invocation context (skill L2 bodies, researcher/implementer spawns, hook additionalContext). Must prove the full SRC flow fits within 200K token budget.

**Decision:**
SRC is context-budget-feasible. Proof follows.

#### Lead's Context Budget (200K tokens)

**Persistent costs (always loaded):**

| Item | Tokens | Source |
|------|--------|--------|
| CLAUDE.md + MEMORY.md | ~3,000 | Existing |
| Skill L1 aggregate (32 existing) | ~6,500 | Existing |
| Agent L1 aggregate (6 existing) | ~3,000 | Existing |
| 3 new skill L1s (impact, cascade, manage-codebase) | ~750 | **NEW** |
| **Persistent subtotal** | **~13,250** | |

**Per-pipeline conversation costs (through P7):**

| Item | Tokens | Source |
|------|--------|--------|
| P0-P6 conversation history | ~30,000-50,000 | Existing (varies by tier) |
| P7 execution-code invocation | ~2,000 | Existing |
| P7 implementer L1 summaries (1-4 implementers) | ~500-2,000 | Existing |
| **Pre-SRC P7 subtotal** | **~32,500-54,000** | |

**SRC-specific costs in Lead's context:**

| Item | Tokens | Frequency | Source |
|------|--------|-----------|--------|
| SubagentStop hook additionalContext | ~125 | Once per implementer stop | **NEW** |
| execution-impact skill L2 (loaded during invocation) | ~200 | Once | **NEW** |
| execution-impact researcher L1 output summary | ~300 | Once | **NEW** |
| execution-cascade skill L2 (loaded during invocation) | ~200 | Once | **NEW** |
| execution-cascade implementer L1 output summaries | ~300 per iteration | Up to 3x | **NEW** |
| manage-codebase skill L2 (if invoked) | ~200 | Once | **NEW** |
| **SRC subtotal (worst case: 3 iterations)** | **~1,925** | | |

**Total worst case in Lead's context:**
```
Persistent:           13,250 tokens
Pre-SRC pipeline:     54,000 tokens (COMPLEX tier upper bound)
SRC additions:         1,925 tokens
P8 verify phase:       5,000 tokens (existing)
P9 delivery:           2,000 tokens (existing)
───────────────────────────────────
TOTAL:               ~76,175 tokens
Available:           200,000 tokens
Remaining:           ~123,825 tokens (62% headroom)
```

**Critical insight: Agent spawns do NOT consume Lead's context.** Each researcher or implementer spawn creates a SEPARATE 200K context window. Only the L1 output summary (~300-500 tokens) returns to Lead's context. This is the key factor that makes SRC feasible.

#### Per-Spawn Context Budgets (separate 200K windows each)

| Agent Spawn | Est. Context Usage | Within 200K? |
|-------------|-------------------|--------------|
| execution-impact researcher | ~40K (agent body + CLAUDE.md + codebase-map + grep results + analysis) | YES (20%) |
| execution-cascade implementer (per iteration) | ~30K (agent body + CLAUDE.md + file reads + edits) | YES (15%) |
| manage-codebase analyst | ~35K (agent body + CLAUDE.md + full codebase scan + map generation) | YES (18%) |

#### Token Cost Estimate (total API tokens consumed, not context)

| Scenario | Agent Spawns | Estimated Total Tokens |
|----------|-------------|----------------------|
| TRIVIAL (no impact detected) | 0 additional | ~0 (hook runs, no cascade) |
| STANDARD (1 cascade iteration) | 1 researcher + 1 implementer | ~70K additional |
| COMPLEX (3 cascade iterations) | 1 researcher + 3 iterations * 2 implementers = 7 spawns | ~350K additional |

The COMPLEX worst case (350K additional tokens) is a cost concern but not a context-budget concern. Each spawn operates independently within its own 200K window.

#### L1 Budget Impact

Current: 27 auto-loaded skill L1s consuming ~26,315 of 32,000 chars (82%).
Adding 3 new skills: ~26,315 + 2,250 = ~28,565 chars (89%).
Headroom: ~3,435 chars remaining.

This is tight but feasible. If budget becomes an issue:
- execution-cascade and execution-impact could use shorter descriptions
- Or manage-codebase could set `disable-model-invocation: true` (user-invocable only) to save ~750 chars

**Resolves:** GAP-NF2, GAP-NF5

---

## 4. Context Budget Proof

(Detailed in ADR-SRC-7 above. Summary repeated here for completeness.)

**Feasibility Verdict: CONFIRMED.**

The SRC system adds ~1,925 tokens to Lead's worst-case context consumption (from ~74K to ~76K out of 200K). This leaves 62% headroom. The key architectural property enabling this is that agent spawns create separate context windows — only their L1 output summaries (~300-500 tokens each) return to Lead's context.

The persistent L1 budget impact is 89% utilization (28,565/32,000 chars). This is feasible with ~3.4K chars remaining. Monitor this metric; if future skills are added, budget pressure increases.

API token cost (not context budget) for worst-case COMPLEX cascade: ~350K tokens across 7 agent spawns. This is an operational cost, not a feasibility constraint.

---

## 5. codebase-map.md Design

### Location
`.claude/agent-memory/analyst/codebase-map.md`

### Format
Compact markdown with one `##` section per tracked file. Grep-parseable structure.

### Full Schema

```markdown
# Codebase Dependency Map
<!-- Generated by manage-codebase skill -->
<!-- Last full scan: {YYYY-MM-DD} -->
<!-- Entry count: {N} -->
<!-- Scope: .claude/ -->

## {relative/path/to/file}
refs: {file1}, {file2}, {file3}
refd_by: {file4}, {file5}
hotspot: {low|medium|high}
updated: {YYYY-MM-DD}

## {next/file}
...
```

### Field Definitions

| Field | Description | Example |
|-------|-------------|---------|
| `## {path}` | Relative path from project root | `## .claude/skills/execution-code/SKILL.md` |
| `refs` | Files this file references (basenames or relative paths) | `refs: orchestration-verify, execution-review, implementer.md` |
| `refd_by` | Files that reference this file | `refd_by: manage-skills/SKILL.md, CLAUDE.md` |
| `hotspot` | Reference density score | `hotspot: medium` |
| `updated` | Date of last dependency scan for this entry | `updated: 2026-02-14` |

### Hotspot Scoring

| Score | Criteria |
|-------|----------|
| `high` | `refd_by` count >= 10, OR file changed in last 3 sessions |
| `medium` | `refd_by` count 4-9 |
| `low` | `refd_by` count 0-3 |

### Size Limits
- **Max entries**: 150 files (at ~2 lines per entry = 300 lines)
- **Max file size**: ~15KB
- **Pruning strategy**: When exceeding 150 entries, remove entries with `hotspot: low` and oldest `updated` dates first
- **Current `.claude/` file count**: ~80 files (well within limit)

### Initial Generation Method
1. manage-codebase skill invoked manually or by Lead after pipeline
2. Analyst agent spawned with full scan task
3. Agent runs `Glob .claude/**/*` to list all files
4. For each file: `Grep` for references to other `.claude/` files
5. Build `refs` and `refd_by` bidirectionally
6. Calculate `hotspot` scores
7. Write complete map to `.claude/agent-memory/analyst/codebase-map.md`
8. Expected first-run time: ~5 minutes (analyst with 30 maxTurns)

### Incremental Update Method
1. manage-codebase invoked with list of recently changed files
2. For each changed file: re-scan its `refs` list
3. Update all `refd_by` entries that reference or de-reference changed files
4. Recalculate `hotspot` scores for affected entries
5. Update `updated` dates
6. Expected incremental time: ~1-2 minutes

### Staleness Detection
- **Per-entry**: Compare `updated` date against `git log --format=%cd --date=short -1 -- {file_path}`
- **Bulk**: If >30% of entries have `updated` older than 7 days, trigger full regeneration
- **Missing file**: If file in map does not exist on filesystem, remove entry immediately
- **New file**: If `.claude/` file exists but has no map entry, flag for addition on next update

### Scope Boundary (GAP-F1 resolution)

**Phase 1 (Current):** `.claude/` directory only.
- Explicit include: `.claude/agents/`, `.claude/skills/`, `.claude/hooks/`, `.claude/settings.json`, `.claude/CLAUDE.md`, `.claude/projects/*/memory/`
- Explicit exclude: `.claude/agent-memory/` (except codebase-map.md itself), `.claude/agent-memory-local/`

**Phase 2 (Future, deferred):** Application source code.
- Triggered by: User explicitly requesting application-code impact analysis, OR project configuration flag
- Would require: Separate map file (codebase-map-app.md), language-specific reference detection rules (Python imports, TypeScript imports, etc.), larger size limits
- NOT part of current SRC implementation scope

---

## 6. Degradation Strategy

### Level 1: Full SRC

**Conditions:**
- Both hooks configured in settings.json and scripts present
- on-file-change.sh executes successfully (exit 0)
- on-implementer-done.sh executes successfully and produces additionalContext
- codebase-map.md exists and has <30% stale entries
- execution-impact and execution-cascade skills present in `.claude/skills/`

**Behavior:**
Full pipeline: hooks -> impact analysis (map + grep) -> cascade update -> review -> map refresh

**Performance:**
Optimal. Map-assisted lookups reduce grep time. Full dependency coverage.

---

### Level 2: Degraded SRC

**Conditions (any one triggers degradation):**
- codebase-map.md does not exist
- codebase-map.md has >50% stale entries
- codebase-map.md fails to parse (malformed markdown)
- manage-codebase skill unavailable

**Behavior:**
Hooks still capture changes and alert Lead. execution-impact runs in grep-only mode (no map). execution-cascade proceeds normally. Impact analysis takes longer and may miss transitive dependencies that the map would have caught.

**Performance:**
Reduced accuracy for transitive dependencies. Slightly longer execution-impact run time (full grep scan instead of map lookup + targeted grep). Core value (DIRECT dependency detection) fully preserved.

**Recovery:**
Run manage-codebase skill to regenerate/refresh codebase-map.md. Automatically returns to Full SRC on next pipeline run.

---

### Level 3: No SRC

**Conditions (any one triggers full bypass):**
- PostToolUse hook not configured in settings.json
- on-file-change.sh missing or failing on every invocation
- SubagentStop hook not configured or on-implementer-done.sh missing
- /tmp filesystem unavailable
- Both execution-impact and execution-cascade skills missing

**Behavior:**
Pre-SRC pipeline behavior. Lead reads implementer L1 file_changed list. No impact analysis. No cascade updates. Pipeline proceeds directly from execution-code/infra -> execution-review -> verify.

This is the current (v10.2) behavior. SRC is a purely additive enhancement; its absence restores the baseline.

**Performance:**
No impact awareness. Cross-file inconsistencies caught only by verify-consistency (P8) after the fact, not proactively during execution.

**Recovery:**
Reinstall hooks in settings.json, verify scripts exist and are executable, verify skills exist. Run a test edit to confirm hooks fire. Run manage-codebase to generate map.

---

### Degradation Detection

Lead can detect current SRC level through signals:
- **Full SRC**: Lead receives "SRC IMPACT ALERT" with dependents list AND confidence: high in execution-impact output
- **Degraded SRC**: Lead receives "SRC IMPACT ALERT" BUT execution-impact reports confidence: medium and notes "codebase-map unavailable, grep-only mode"
- **No SRC**: Lead receives NO "SRC IMPACT ALERT" after implementer finishes (no hook output). Lead should note this in execution-review prompt for extra scrutiny.

---

## 7. Done Definition (GAP-AC7)

### SRC System is "Done" When ALL of the Following Are True:

#### A. Component Deployment (all 9 components)

| # | Component | Done Criterion |
|---|-----------|---------------|
| 1 | on-file-change.sh | Script exists at `.claude/hooks/on-file-change.sh`, configured in settings.json PostToolUse with matcher `Edit\|Write`, exits 0 on test Edit call |
| 2 | on-implementer-done.sh | Script exists at `.claude/hooks/on-implementer-done.sh`, configured in settings.json SubagentStop with matcher `implementer`, produces valid additionalContext JSON on test |
| 3 | execution-impact | SKILL.md exists at `.claude/skills/execution-impact/SKILL.md`, valid frontmatter, L2 body present, description within 1024 chars |
| 4 | execution-cascade | SKILL.md exists at `.claude/skills/execution-cascade/SKILL.md`, valid frontmatter, L2 body present, description within 1024 chars |
| 5 | manage-codebase | SKILL.md exists at `.claude/skills/manage-codebase/SKILL.md`, valid frontmatter, L2 body present, description within 1024 chars |
| 6 | codebase-map.md | File exists at `.claude/agent-memory/analyst/codebase-map.md`, generated by manage-codebase, parseable by grep |
| 7 | execution-code mod | OUTPUT_TO updated to include execution-impact |
| 8 | implementer.md mod | No changes needed (confirmed by ADR-SRC-1) |
| 9 | CLAUDE.md mod | Skill count updated to 35, domain counts correct |

#### B. Integration Verification

| Test | Method | Pass Criterion |
|------|--------|---------------|
| Hook fires on Edit | Manually edit a file, check /tmp/src-changes-*.log | Log line appears with correct file path |
| Hook fires on Write | Manually write a file, check /tmp/src-changes-*.log | Log line appears with correct file path |
| SubagentStop produces output | Spawn implementer with an edit task, check Lead context | Lead receives "SRC IMPACT ALERT" text |
| execution-impact finds dependents | Change a skill SKILL.md, run execution-impact | L1 reports at least 1 DIRECT dependent |
| execution-cascade updates files | Introduce a known inconsistency, run cascade | Cascade implementer fixes the inconsistency |
| Convergence works | Cascade with no downstream impact | L1 shows converged: true, iterations: 1 |
| Non-convergence handled | Force 3-iteration scenario | L1 shows converged: false, pipeline continues |
| manage-codebase generates map | Run on empty state | codebase-map.md created with >50 entries |
| Degraded mode works | Delete codebase-map.md, run pipeline | execution-impact runs in grep-only mode, reports confidence: medium |

#### C. Non-Regression

| Check | Method | Pass Criterion |
|-------|--------|---------------|
| Existing hooks unaffected | Run pipeline with SRC hooks active | SubagentStart, PreCompact, SessionStart hooks still fire correctly |
| Pipeline tiers unchanged | Check CLAUDE.md section 2 | Tier definitions identical to pre-SRC |
| L1 budget within limit | Count total L1 chars | <= 32,000 chars (target: <90%) |
| No context budget overflow | Run COMPLEX pipeline with SRC | Lead context stays below 200K, no unexpected compaction |
| Existing skills unmodified | Diff all skills except execution-code | Zero changes to non-SRC skills |

#### D. Documentation

| Item | Location | Content |
|------|----------|---------|
| Architecture doc | `.claude/agent-memory/analyst/src-architecture.md` | This document |
| MEMORY.md update | `.claude/projects/-home-palantir/memory/MEMORY.md` | SRC state added to "Current INFRA State" section |
| Hook documentation | In-script comments | Purpose, input/output, error handling |

### Overall "Done" Statement
> SRC is done when: (a) all 9 components are deployed, (b) end-to-end integration tests pass for both convergent and non-convergent scenarios, (c) the existing pipeline operates identically with SRC hooks active, and (d) the L1 budget is within 90% of the 32,000-char limit.

---

## Appendix A: settings.json Hook Configuration (Target State)

```json
{
  "hooks": {
    "SubagentStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "/home/palantir/.claude/hooks/on-subagent-start.sh",
            "timeout": 10,
            "statusMessage": "Injecting team context to new agent"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "/home/palantir/.claude/hooks/on-file-change.sh",
            "timeout": 5,
            "async": true,
            "statusMessage": "Logging file change"
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "matcher": "implementer",
        "hooks": [
          {
            "type": "command",
            "command": "/home/palantir/.claude/hooks/on-implementer-done.sh",
            "timeout": 15,
            "statusMessage": "Analyzing implementation impact"
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "/home/palantir/.claude/hooks/on-pre-compact.sh",
            "timeout": 30,
            "statusMessage": "Saving orchestration state before compaction"
          }
        ]
      }
    ],
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
  }
}
```

## Appendix B: Execution Domain Flow (Target State)

```
[orchestration-verify PASS]
    |
    v
[execution-code]  ──parallel──  [execution-infra]
    |                                |
    v                                v
    └──────────> [execution-impact] <┘
                      |
                      v
               [execution-cascade]
                      |
                      v
               [execution-review]
                      |
                      v
               [verify domain (P8)]
```

Execution domain: 5 skills (code, infra, impact, cascade, review).

## Appendix C: Gap Resolution Summary

| Gap ID | Severity | Resolution | ADR |
|--------|----------|------------|-----|
| GAP-IP1 | CRITICAL | Two-stage hook architecture | ADR-SRC-1 |
| GAP-NF2 | CRITICAL | Context budget proof: 76K/200K = 38% used | ADR-SRC-7 |
| GAP-AC7 | CRITICAL | Comprehensive done definition (Section 7) | -- |
| GAP-F1 | HIGH | Phase 1: .claude/ only, Phase 2: app code deferred | ADR-SRC-5 |
| GAP-F4 | HIGH | Drop SEMANTIC, keep DIRECT + TRANSITIVE only | ADR-SRC-4 |
| GAP-AC5 | HIGH | Markdown format, grep-parseable, per-entry schema | ADR-SRC-5 |
| GAP-IP5 | HIGH | .claude/agent-memory/analyst/codebase-map.md | ADR-SRC-5 |
| GAP-EH2 | HIGH | Continue with warning, partial status, P8 catches rest | ADR-SRC-6 |
| GAP-IP3 | MEDIUM | execution-impact/execution-cascade naming pattern | ADR-SRC-3 |
| GAP-IP4 | MEDIUM | 32 -> 35 skills, L1 budget at 89% | ADR-SRC-3 |
| GAP-NF5 | MEDIUM | 350K tokens worst case (cost, not context issue) | ADR-SRC-7 |
| GAP-AC1 | LOW | Acceptance criteria defined in Component 1 | -- |
| GAP-AC2 | LOW | Acceptance criteria defined in Component 3 | -- |
| GAP-AC3 | LOW | Convergence definition in Component 4 | -- |
| GAP-AC4 | LOW | Acceptance criteria defined in Component 5 | -- |
| GAP-NF1 | LOW | Timeout: 5s (Stage 1), 15s (Stage 2) | -- |
| GAP-NF3 | LOW | 150 files max in map, .claude/ scope = ~80 files | ADR-SRC-5 |
| GAP-NF4 | LOW | Stage 1 async + Stage 2 batched = minimal overhead | ADR-SRC-1 |
| GAP-EH1 | LOW | grep exit 1 = no matches (normal), timeout = truncate | Component 2 |
| GAP-EH3 | LOW | updated field + 30% staleness threshold -> full regen | Section 5 |
| GAP-EH4 | LOW | Truncate with "... and N more" suffix at 500 chars | Component 2 |
| GAP-EH5 | LOW | Cascade re-runs grep check (implicit verification) | Component 4 |
| GAP-EH6 | LOW | 3-iteration cap bounds expansion, partial status | ADR-SRC-6 |
| GAP-F2 | LOW | additionalContext invisible to user; Lead can mention in conversation | -- |
| GAP-F3 | LOW | Full scan initial, incremental thereafter | Section 5 |
| GAP-IP2 | LOW | Single matcher with regex: `Edit\|Write` | ADR-SRC-1 |
| GAP-AC6 | LOW | Integration tests defined in Section 7B | -- |
