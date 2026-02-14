# SRC Risk Assessment

> Analyst output | 2026-02-14 | Design-Risk (P2)
> Scope: FMEA, security, performance, cascade, integration risks for SRC system
> Input: src-architecture.md (P2 architecture), cc-reference/*, existing hooks
> Method: Per-component FMEA, cross-cutting security/performance/integration analysis

---

## 1. FMEA Table (Per Component)

### Component 1: on-file-change.sh (PostToolUse Hook)

| # | Failure Mode | Effect | S | L | D | RPN | Mitigation |
|---|-------------|--------|---|---|---|-----|------------|
| 1.1 | jq unavailable on system | Hook silently exits 0, no changes logged, entire SRC chain breaks for session | 7 | 2 | 8 | 112 | Add jq check to manage-infra preflight; fallback to sed/awk parsing |
| 1.2 | /tmp filesystem full | Write fails silently, change log incomplete, impact analysis misses files | 6 | 2 | 7 | 84 | Check df before write; warn in stderr (non-blocking) |
| 1.3 | Malformed stdin JSON from CC | jq extraction fails, file_path is empty or "null", log entry corrupted | 5 | 2 | 6 | 60 | Validate jq output is non-empty before appending |
| 1.4 | Hook timeout (>5s) | Hook killed, change not logged | 4 | 1 | 9 | 36 | Script is ~3 operations (read stdin, jq, echo); timeout extremely unlikely |
| 1.5 | Concurrent writes from parallel implementers corrupt log | Interleaved partial lines in log file | 5 | 3 | 7 | 105 | Use lockfile or echo atomic write guarantee (lines <PIPE_BUF = 4KB on Linux) |
| 1.6 | session_id field missing or changed in CC update | Log file named with "null" or empty string, shared across sessions | 7 | 2 | 5 | 70 | Validate session_id before constructing filename; fallback to PID-based naming |
| 1.7 | Async hook result delivered on NEXT turn, not current | No direct effect (hook is silent), but timing mismatch if design changes | 2 | 3 | 3 | 18 | Document async delivery semantics in hook comments |
| 1.8 | Edit tool uses file_path but Write tool might use different field name | file_path extraction fails for one tool type, partial logging | 6 | 2 | 4 | 48 | Verify both Edit and Write tool_input schemas against CC reference; add fallback field check |

### Component 2: on-implementer-done.sh (SubagentStop Hook)

| # | Failure Mode | Effect | S | L | D | RPN | Mitigation |
|---|-------------|--------|---|---|---|-----|------------|
| 2.1 | Change log file does not exist (no edits made) | Hook outputs "SRC: No file changes detected" -- correct behavior, but Lead may still need to check | 2 | 4 | 1 | 8 | Already handled in design (expected case) |
| 2.2 | grep -rl takes >10s on large repo | Hook truncates results, impact analysis incomplete | 5 | 4 | 6 | 120 | Add grep timeout (timeout 8s grep -rl), limit search scope to .claude/ first |
| 2.3 | grep returns enormous result set (>500 chars) | Truncation loses important dependent information | 4 | 5 | 3 | 60 | Already designed with truncation + "Run /execution-impact for full list" |
| 2.4 | jq unavailable | Hook exits 0 with no output, Lead receives no SRC alert, falls back to No-SRC mode | 7 | 2 | 8 | 112 | Same as 1.1 -- jq is a hard dependency for both hooks |
| 2.5 | Hook blocks Lead for full 15s timeout | Lead waits 15s after each implementer finishes, pipeline delay | 4 | 3 | 4 | 48 | Profile grep execution time; consider reducing timeout to 10s |
| 2.6 | Multiple implementers stop in rapid succession | Each stop reads FULL accumulated log, runs grep for ALL files (redundant work) | 3 | 3 | 5 | 45 | Accept redundancy (correct behavior); consider tracking "last processed line" |
| 2.7 | additionalContext exceeds CC internal limit | Output silently truncated or rejected by CC runtime | 6 | 2 | 7 | 84 | Enforce 500-char limit strictly in script; test with maximum-length output |
| 2.8 | Hook stdout contains invalid JSON | CC ignores output, Lead receives no SRC alert | 7 | 2 | 5 | 70 | Validate JSON with jq before outputting; integration test |
| 2.9 | Non-implementer agent triggers hook (matcher regex issue) | Grep runs on unrelated agent's changes; false alert to Lead | 4 | 2 | 4 | 32 | Matcher "implementer" is exact match, not regex; verify CC matcher semantics |
| 2.10 | Change log contains duplicate file paths | Redundant grep runs, wasted time (but correct results after dedup) | 2 | 5 | 2 | 20 | sort -u on file paths before grepping (already in design) |

### Component 3: execution-impact (Skill)

| # | Failure Mode | Effect | S | L | D | RPN | Mitigation |
|---|-------------|--------|---|---|---|-----|------------|
| 3.1 | Researcher times out (30 maxTurns) mid-analysis | Partial impact report, low confidence, cascade may miss affected files | 6 | 3 | 5 | 90 | Design handles this (partial results + confidence: low); ensure cascade proceeds cautiously |
| 3.2 | Researcher misclassifies TRANSITIVE as DIRECT or vice versa | Cascade updates wrong files or with wrong priority | 4 | 4 | 6 | 96 | Require grep evidence in L2 output for every classification; execution-review validates |
| 3.3 | codebase-map.md is stale (>7 days old entries) | Impact analysis uses outdated dependency data, misses new dependencies | 5 | 4 | 5 | 100 | Degraded mode uses grep-only as supplement; staleness detection triggers regeneration |
| 3.4 | cascade_recommended: true for trivial change | Unnecessary cascade iteration wastes tokens and time | 3 | 4 | 4 | 48 | Threshold: only recommend cascade if impact_candidates > 0 with DIRECT type |
| 3.5 | cascade_recommended: false when cascade needed | Cross-file inconsistency slips through to review/verify | 7 | 3 | 5 | 105 | verify-consistency (P8) as safety net; researcher includes confidence in recommendation |
| 3.6 | L1 YAML output malformed | execution-cascade cannot parse input, cascade skipped | 7 | 2 | 4 | 56 | Researcher skill L2 includes strict output template; validate YAML in cascade skill |

### Component 4: execution-cascade (Skill)

| # | Failure Mode | Effect | S | L | D | RPN | Mitigation |
|---|-------------|--------|---|---|---|-----|------------|
| 4.1 | Infinite cascade loop (iteration cap bypassed) | Unbounded token consumption, session stalled | 9 | 1 | 3 | 27 | Hard 3-iteration cap in skill L2 methodology; Lead enforces externally |
| 4.2 | Cascade implementer introduces new bugs while fixing inconsistencies | Cascade amplifies damage rather than fixing it | 8 | 3 | 6 | 144 | Implementer maxTurns reduced to 30; execution-review examines cascade changes with extra scrutiny |
| 4.3 | False convergence: grep check finds no new impacts but inconsistency remains | Inconsistency escapes cascade, reaches delivery | 7 | 4 | 6 | 168 | verify-consistency (P8) as independent validation; grep patterns may miss semantic inconsistencies |
| 4.4 | Partial convergence after 3 iterations | Pipeline continues with known unresolved impacts | 5 | 3 | 3 | 45 | Designed behavior: warnings propagate to review and delivery |
| 4.5 | Cascade implementer modifies wrong file (misinterpreted impact) | Correct file untouched, wrong file corrupted | 8 | 2 | 5 | 80 | Implementer receives explicit file path + grep evidence + change description; review catches wrong edits |
| 4.6 | Race condition: two cascade implementers edit same file | File content corrupted or one edit overwritten | 8 | 2 | 4 | 64 | Max 2 implementers per iteration; assign non-overlapping file sets; each file to exactly one implementer |
| 4.7 | Cascade spawns implementer that triggers SubagentStop hook recursively | Lead receives nested SRC alerts during active cascade, confusion | 5 | 5 | 4 | 100 | Design notes "Lead ignores second alert during active cascade" -- must be enforced in Lead protocol or skill L2 |

### Component 5: manage-codebase (Skill)

| # | Failure Mode | Effect | S | L | D | RPN | Mitigation |
|---|-------------|--------|---|---|---|-----|------------|
| 5.1 | Full scan exceeds analyst maxTurns (25 turns for ~80 files) | Partial map generated, incomplete dependency data | 4 | 3 | 4 | 48 | Architecture specifies 30 maxTurns for analyst in this skill (override agent default) |
| 5.2 | Map exceeds 300-line limit | Map file grows unbounded, consumes analyst MEMORY.md budget | 4 | 2 | 3 | 24 | Pruning strategy defined; current scope (~80 files) well within limit |
| 5.3 | Stale entry references deleted file, causes grep error downstream | on-implementer-done.sh greps for non-existent file pattern, grep returns non-zero | 3 | 3 | 4 | 36 | Staleness detection removes deleted files; grep -rl ignores non-existent reference targets |
| 5.4 | Map format corrupted (bad markdown) | execution-impact cannot parse map, falls to grep-only mode | 4 | 2 | 4 | 32 | Degraded SRC mode handles this gracefully |
| 5.5 | Incremental update misses newly added files | New files have no map entry, invisible to map-assisted impact analysis | 3 | 3 | 5 | 45 | New file detection via `Glob .claude/**/*` minus existing entries |

### Component 6: codebase-map.md (Knowledge File)

| # | Failure Mode | Effect | S | L | D | RPN | Mitigation |
|---|-------------|--------|---|---|---|-----|------------|
| 6.1 | File accidentally deleted | Full SRC degrades to Degraded SRC (grep-only mode) | 4 | 2 | 2 | 16 | Version-controlled in .claude/; git restore recovers |
| 6.2 | refs/refd_by entries become bidirectionally inconsistent | File A lists B in refs, but B does not list A in refd_by | 4 | 3 | 6 | 72 | manage-codebase always rebuilds bidirectionally; verify step checks consistency |
| 6.3 | Hotspot scores inaccurate (wrong reference counts) | Misleading prioritization in impact analysis | 2 | 4 | 5 | 40 | Hotspot is advisory; impact decisions based on grep evidence, not hotspot alone |
| 6.4 | Map grows beyond analyst MEMORY.md 200-line budget | Analyst context overloaded, performance degraded | 3 | 2 | 5 | 30 | Map stored in agent-memory (separate from MEMORY.md); only MEMORY.md has 200-line limit |

### Component 7: execution-code SKILL.md (Modification)

| # | Failure Mode | Effect | S | L | D | RPN | Mitigation |
|---|-------------|--------|---|---|---|-----|------------|
| 7.1 | OUTPUT_TO update breaks existing routing | execution-review no longer receives expected input | 6 | 1 | 3 | 18 | Additive change only (append to list, not replace); verify-consistency checks |
| 7.2 | Step 5.5 note confuses implementer agent | Implementer tries to run execution-impact itself | 3 | 2 | 3 | 18 | Note targets Lead, not implementer; implementer sees only its assigned task |

### Component 8: implementer.md (Modification)

| # | Failure Mode | Effect | S | L | D | RPN | Mitigation |
|---|-------------|--------|---|---|---|-----|------------|
| 8.1 | No changes needed (per design) | N/A -- no risk from zero modification | 0 | 0 | 0 | 0 | -- |

### Component 9: CLAUDE.md (Modification)

| # | Failure Mode | Effect | S | L | D | RPN | Mitigation |
|---|-------------|--------|---|---|---|-----|------------|
| 9.1 | Skill count update inconsistent with actual count | Lead has wrong mental model of skill inventory | 3 | 2 | 2 | 12 | verify-consistency checks CLAUDE.md against actual skill directories |
| 9.2 | Domain count mismatch (homeostasis 3 vs 4) | Routing confusion in manage-skills | 3 | 2 | 3 | 18 | Same verify-consistency check |

---

## 2. Security Assessment

### 2.1 Malicious Content in Edited Files Exploiting Hook Scripts

**Risk: LOW**

The `on-file-change.sh` hook reads stdin JSON provided by CC, not file contents. It extracts only `tool_input.file_path` (a path string) and `tool_response.success` (a boolean). The file content itself is never read or executed by the hook.

However, the `on-implementer-done.sh` hook runs `grep -rl "{pattern}" .` where the pattern is derived from file paths in the change log. If a file path contains shell metacharacters, this creates an injection vector.

**Specific vectors:**
- File path containing backticks: `` /tmp/src-changes-abc.log `` with entry `` `rm -rf /` `` -- mitigated because jq `-r` outputs raw strings, not shell-interpreted, and the path comes from CC's own `tool_input.file_path` which CC validates
- File path containing regex metacharacters: `file[name].md` would cause grep pattern issues but not code execution
- File content is never passed through hooks (only paths)

**Verdict:** Low risk. CC controls the `tool_input.file_path` value; users cannot directly inject arbitrary paths. The attack surface requires compromising CC itself.

### 2.2 Command Injection in grep Patterns

**Risk: MEDIUM**

The `on-implementer-done.sh` constructs grep commands using file paths from the change log:
```bash
grep -rl "$FILE_PATH" .
```

If `$FILE_PATH` contains characters interpreted by grep as regex (`.`, `*`, `+`, `[`, `]`, `(`, `)`), grep will match unintended files. This is a correctness issue, not a security issue, since grep does not execute matched content.

However, if `$FILE_PATH` is inserted into the grep command without proper quoting and the script uses `eval` or unquoted variables in a subshell, shell injection becomes possible.

**Mitigations required:**
1. Always double-quote variables: `grep -rl "$FILE_PATH" .` (not `grep -rl $FILE_PATH .`)
2. Use `grep -Frl` (fixed string, not regex) to avoid regex metacharacter interpretation
3. Never use `eval` in either hook script
4. Validate that file paths contain only printable ASCII characters

### 2.3 File Path Traversal in Change Log Parsing

**Risk: LOW**

The change log at `/tmp/src-changes-{session_id}.log` contains file paths extracted from CC's `tool_input.file_path`. CC itself prevents path traversal in tool inputs (Edit/Write tools resolve paths before execution). The change log reader (`on-implementer-done.sh`) uses paths only as grep patterns, not as file read/write targets.

**Edge case:** If an attacker could write arbitrary lines to the change log (bypassing the PostToolUse hook), they could inject a path like `../../etc/passwd` which grep would then search for as a pattern. This would reveal which project files mention `/etc/passwd` but would not read or modify `/etc/passwd` itself.

**Verdict:** Low risk. Change log is append-only via the hook; no external write path exists during normal operation.

### 2.4 /tmp File Manipulation by External Processes

**Risk: MEDIUM-HIGH**

The `/tmp/` directory is world-readable/writable. Risks include:

1. **Symlink attack:** An attacker creates a symlink `/tmp/src-changes-{session_id}.log` pointing to a sensitive file before the hook runs. The hook's append operation would then write to the sensitive file. **Mitigation:** Use `mktemp` with a unique prefix, or check that the file is not a symlink before writing (`[ ! -L "$FILE" ]`).

2. **Content injection:** An attacker appends malicious lines to the change log between hook invocations. The SubagentStop hook would then grep for attacker-controlled patterns. **Mitigation:** Set restrictive permissions (`chmod 600`) on creation; validate log line format before processing.

3. **Denial of service:** An attacker fills the change log with millions of lines, causing the SubagentStop hook to time out during processing. **Mitigation:** Cap log size (e.g., max 1000 lines); truncate oldest entries if exceeded.

4. **Session ID prediction:** If session IDs are predictable, attacker can pre-create the log file. **Mitigation:** CC session IDs are UUIDs (unpredictable).

**Verdict:** Medium-high risk in shared multi-user environments. Low risk on single-user WSL2 (current environment). Should implement symlink check and restrictive permissions regardless.

### 2.5 Crafted File Names Breaking TSV Log Format

**Risk: LOW-MEDIUM**

The change log uses TSV format: `{timestamp}\t{tool_name}\t{file_path}`. If a file path contains tab characters or newline characters, it would corrupt the TSV structure:

- Tab in path: `/home/user/file\twith\ttabs.md` would create extra columns
- Newline in path: `/home/user/file\nwith\nnewlines.md` would create extra rows
- Both would cause the SubagentStop hook to misparse the log

**Mitigation:**
1. Sanitize file paths before logging (strip/escape tabs and newlines)
2. Use a more robust delimiter (e.g., NUL-separated records with `\0`)
3. CC's file_path field is unlikely to contain these characters (filesystem restrictions), but defense-in-depth requires sanitization

**Verdict:** Low-medium risk. Filesystem typically prevents these characters in paths, but the hook should sanitize defensively.

---

## 3. Performance Bottleneck Analysis

### 3.1 Hook Execution Time: grep -rl on Repository

**Bottleneck severity: MEDIUM**

The `on-implementer-done.sh` hook runs `grep -rl` for each changed file across the repository. With the current `.claude/` scope (~80 files), this is fast. But:

| Scenario | Changed Files | grep Runs | Estimated Time |
|----------|--------------|-----------|----------------|
| Trivial (1-2 files) | 2 | 2 x grep -rl | <1s |
| Standard (3-8 files) | 5 | 5 x grep -rl | ~2-3s |
| Complex (10+ files) | 15 | 15 x grep -rl | ~5-10s |
| Worst case (many files) | 30 | 30 x grep -rl | ~10-15s (hits 15s timeout) |

**Mitigation:**
- Scope grep to `.claude/` directory only (not full repo)
- Use `grep -Frl` (fixed string) which is faster than regex grep
- Deduplicate file paths before grepping (avoid redundant runs)
- Parallelize grep calls: `xargs -P4 -I{} grep -Frl {} .claude/`
- If codebase-map.md is available, use map lookup instead of grep in the hook

### 3.2 Change Log I/O During Heavy Editing Sessions

**Bottleneck severity: LOW**

Each Edit/Write call appends one ~100-byte line to the change log. Even in a COMPLEX pipeline with 100 edits, the file is ~10KB. I/O overhead is negligible on modern filesystems.

**Concern:** `/tmp` is typically tmpfs (RAM-backed) on Linux, making I/O even faster. On systems where `/tmp` is on disk, performance is still acceptable for append-only writes.

### 3.3 SubagentStop Hook Blocking Lead

**Bottleneck severity: MEDIUM-HIGH**

The SubagentStop hook is synchronous (blocking). Lead waits for the hook to complete before processing the implementer's return value. With a 15s timeout:

- **Best case:** 1-2 changed files, hook completes in <1s. Lead barely notices.
- **Typical case:** 5-8 changed files, hook completes in 2-5s. Noticeable but acceptable.
- **Worst case:** 15+ changed files with broad grep scope, hook hits 15s timeout. Lead is blocked for 15s with no progress.

**Impact:** In a COMPLEX pipeline with multiple sequential implementers, this blocking time accumulates: 3 implementers x 10s each = 30s of Lead idle time.

**Mitigation:**
- Reduce timeout to 10s
- Optimize grep (scoped, fixed-string, parallel)
- Consider making SubagentStop hook async with a follow-up polling mechanism (but this loses the injection-to-Lead-context benefit)
- Accept the tradeoff: 15s delay is small relative to implementer execution time (minutes)

### 3.4 Agent Spawn Overhead for Cascade Iterations

**Bottleneck severity: HIGH**

Each cascade iteration spawns 1-2 implementer agents. Each spawn:
- Creates a new 200K context window
- Loads CLAUDE.md + agent body + MEMORY.md (~5K tokens)
- Executes task (reads files, makes edits)
- Returns L1 summary to Lead

Worst-case COMPLEX scenario with 3 cascade iterations x 2 implementers = 6 agent spawns. Each spawn takes ~30-60s of wall clock time and ~50K API tokens.

| Scenario | Spawns | Est. Wall Time | Est. Tokens |
|----------|--------|----------------|-------------|
| No cascade needed | 0 | 0 | 0 |
| 1 iteration, 1 implementer | 1 | ~45s | ~50K |
| 2 iterations, 2 impl. each | 4 | ~3min | ~200K |
| 3 iterations, 2 impl. each | 6 | ~4.5min | ~300K |

Plus 1 researcher spawn for execution-impact (~45s, ~40K tokens).

**Total worst case: ~5-6 minutes, ~350K tokens beyond normal pipeline.** This is a significant cost amplification for COMPLEX tasks.

**Mitigation:**
- Reduced maxTurns for cascade implementers (30 vs normal 50) already in design
- Skip cascade entirely if impact_candidates == 0
- First iteration with single implementer; only add second if needed
- Consider batching multiple file updates into single implementer spawn

### 3.5 Context Budget Consumption Patterns

**Bottleneck severity: LOW** (Well-analyzed in architecture)

Lead context consumption: ~76K/200K (38%) in worst case. Each agent spawn operates in its own 200K window. No context budget risk identified.

**One concern:** If Lead conversation grows beyond expected bounds (e.g., user asks many questions between phases, or multiple pipeline iterations occur), the remaining 124K headroom could erode. Compaction would then be triggered, losing SRC state.

**Mitigation:** SRC state is partially recoverable: change log persists in /tmp, codebase-map persists on disk. Only the Lead's conversation memory of "where in the SRC flow we are" is lost on compaction. PreCompact hook could be extended to save SRC state.

---

## 4. Cascade-Specific Risks

### 4.1 Infinite Loop Prevention

**Question:** Is the 3-iteration cap sufficient?

**Analysis:** In the `.claude/` INFRA scope (~80 files), dependency chains are typically 2-3 hops deep at most. A change to a skill's SKILL.md may affect:
- Iteration 1: Direct dependents (files that reference the changed skill by name) -- typically 3-5 files
- Iteration 2: Files that reference iteration-1 changes -- typically 1-2 files
- Iteration 3: Almost never needed; 2 hops usually reaches convergence

**Verdict:** 3 iterations is sufficient for the current `.claude/` scope. For future application code scope (Phase 2), this limit may need revisiting as dependency chains can be deeper.

**Residual risk:** If a circular dependency exists (A references B, B references A), and the cascade update to A triggers an update to B which triggers an update to A, the 3-iteration cap prevents infinite looping but the cascade may oscillate without converging. **Mitigation:** Detect oscillation (same files modified in consecutive iterations) and flag as "oscillating dependency -- manual review required."

### 4.2 False Positive Cascades

**Risk: HIGH (RPN: 168 -- see 4.3)**

grep-based reference detection cannot distinguish:
- Active references: `INPUT_FROM: execution-code` (real dependency)
- Comments: `# Previously used execution-code here` (not a dependency)
- Documentation: `This skill replaces the old execution-code approach` (not a dependency)
- String literals: `"execution-code"` in a log message (not a dependency)

**Impact:** False positives cause the cascade to update files that do not actually depend on the changed file. This wastes tokens and may introduce unintended changes to otherwise-correct files.

**Likelihood assessment:** In `.claude/` INFRA files, most references are active (SKILL.md frontmatter references, agent tool lists, CLAUDE.md protocol sections). Comments are minimal. False positive rate estimated at 10-15%.

**Mitigation:**
1. Use `grep -F` (fixed string) to avoid regex over-matching
2. Exclude comment lines where possible (lines starting with `#` or `<!--`)
3. Researcher in execution-impact should validate each grep match by reading surrounding context
4. execution-review explicitly checks cascade changes for necessity

### 4.3 Cascade Amplification

**Risk: MEDIUM**

A small change to a high-hotspot file (e.g., CLAUDE.md, which is referenced by many files) could trigger a cascade touching 10+ files. Each of those cascade updates then triggers the PostToolUse hook, which logs more changes, which the next SubagentStop hook reports.

**Worst-case scenario:**
1. Change CLAUDE.md skill count from 32 to 35
2. execution-impact finds 12 files referencing CLAUDE.md
3. Cascade iteration 1: update 12 files (skill descriptions, manage-skills, etc.)
4. Iteration 1 changes trigger impact check: 8 more files reference the updated files
5. Iteration 2: update 8 files
6. Iteration 3: still 3 more files detected, but cap reached

Total: 23 files updated for a 1-line change. Token cost: ~250K additional.

**Mitigation:**
1. Cascade only updates files where the reference is actually inconsistent (not just files that reference the changed file)
2. The convergence check verifies "needs updating" not just "has reference"
3. Lead can decide to skip cascade for changes that are self-contained (e.g., updating a number in CLAUDE.md that is informational, not functional)

### 4.4 Partial Convergence

**Risk: MEDIUM**

When cascade exits after 3 iterations without full convergence:
- Some files are updated, others are not
- The codebase is in a partially-consistent state
- execution-review must identify which files still need attention

**Impact:** If the unresolved files are critical (e.g., hook scripts with wrong paths), the pipeline may produce broken artifacts. If they are documentation-level (e.g., stale comments), impact is minimal.

**Mitigation:**
1. L1 output explicitly lists unresolved files and their expected changes
2. execution-review applies extra scrutiny to flagged files
3. verify-consistency (P8) independently checks cross-file consistency
4. Delivery commit message notes partial convergence
5. If unresolved files are critical: Lead can manually address or re-run cascade

---

## 5. Integration Risks

### 5.1 Conflict with Existing Hooks

**Risk: LOW**

Current hooks:
- **SubagentStart** (on-subagent-start.sh): Fires for ALL agents. SRC does not add a SubagentStart hook. No conflict.
- **PreCompact** (on-pre-compact.sh): Fires before compaction. SRC does not interact with compaction. No conflict.
- **SessionStart:compact** (on-session-compact.sh): Fires on compaction recovery. SRC does not interact with session start. No conflict.

SRC adds:
- **PostToolUse:Edit|Write** (on-file-change.sh): New event type. No existing PostToolUse hooks. No conflict.
- **SubagentStop:implementer** (on-implementer-done.sh): New event type with matcher. No existing SubagentStop hooks. No conflict.

**One concern:** The SubagentStart hook fires for ALL agents (empty matcher), including implementers spawned by cascade. This means cascade implementers receive the team context injection. This is correct behavior (they need team context), but worth noting: the SubagentStart hook does NOT interfere with SRC because it operates at start time, while SRC's SubagentStop operates at stop time.

**Verdict:** No hook conflicts. SRC occupies previously unused event types.

### 5.2 L1 Budget Pressure

**Risk: HIGH**

Current L1 budget: ~26,315/32,000 chars (82%).
After SRC (+3 skills): ~28,565/32,000 chars (89%).
Headroom: ~3,435 chars.

This means only ~3 more auto-loaded skills can be added before hitting the budget ceiling. If any existing skill descriptions grow (e.g., during optimization), or if the SLASH_COMMAND_TOOL_CHAR_BUDGET changes, the budget could overflow.

**Overflow behavior (from CC reference):** Skills are likely excluded FIFO when budget is exceeded. Excluded skills become invisible to Lead (cannot auto-invoke), though users can still invoke via /slash-command.

**Which skills would be excluded first?** Unknown -- CC documentation does not specify exclusion ordering. This is a critical uncertainty.

**Mitigation:**
1. Set `disable-model-invocation: true` on manage-codebase (user-invoked only, saves ~750 chars)
2. Monitor L1 budget after each skill addition (manage-skills already tracks this)
3. Consider increasing SLASH_COMMAND_TOOL_CHAR_BUDGET from 32K to 48K (untested -- CC may have internal limits)
4. Compress existing skill descriptions further (already optimized to 1024 chars each in v10.3)
5. If budget critical: execution-impact and execution-cascade could share a single skill with mode parameter

### 5.3 Existing Pipeline Regression

**Risk: MEDIUM**

SRC modifies the execution flow by inserting execution-impact and execution-cascade between execution-code/infra and execution-review. Potential regressions:

1. **execution-review scope expansion:** Review must now examine both original AND cascade-updated files. If the reviewer is not aware of cascade changes, it may miss reviewing them or apply wrong criteria.
   - **Mitigation:** execution-cascade L1 output explicitly lists cascade-updated files; reviewer L2 methodology includes "distinguish planned vs cascade changes"

2. **Pipeline timing:** Adding impact + cascade + potential 3 iterations extends P7 (execution) phase significantly. This may cause user impatience or context budget pressure in long-running pipelines.
   - **Mitigation:** Accept timing increase; skip cascade when impact_candidates == 0

3. **execution-code OUTPUT_TO change:** Adding execution-impact to OUTPUT_TO is additive, but if Lead routing logic is sensitive to OUTPUT_TO ordering, the new first entry might redirect flow unexpectedly.
   - **Mitigation:** Verify Lead routing is not order-sensitive in OUTPUT_TO (it should be context-aware, not positional)

### 5.4 Multi-Implementer Race Conditions on Change Log

**Risk: LOW-MEDIUM**

In COMPLEX tier, multiple implementers may run in parallel. Each triggers PostToolUse hooks that append to the same change log (`/tmp/src-changes-{session_id}.log`).

**Analysis:** On Linux, `echo "..." >> file` is atomic for writes smaller than PIPE_BUF (4096 bytes on Linux). Each log line is ~100 bytes, well under this limit. Therefore, concurrent appends will not interleave.

**Edge cases:**
- If the echo command is replaced with a multi-step write (open, write, close), atomicity is lost
- If the shell redirects via a file descriptor that buffers, interleaving is possible
- NFS or network filesystems may not guarantee atomic appends

**Verdict:** Safe on local `/tmp` (tmpfs) with simple echo-append. Script implementation must use a single `echo "..." >> file` statement, not multi-step writes.

### 5.5 Hook Configuration Complexity

**Risk: LOW**

SRC increases settings.json hooks from 3 event groups to 5. The configuration structure is straightforward (one entry per event type with matcher). Maintenance concern is minimal.

**One risk:** If settings.json is manually edited and a syntax error is introduced, ALL hooks may fail to load (CC may reject malformed JSON). This would break existing hooks (SubagentStart, PreCompact, SessionStart) in addition to SRC hooks.

**Mitigation:** Always validate settings.json with `jq .` after edits; use manage-infra preflight to check hook configuration.

---

## 6. Top 10 Risks by RPN (Mitigation Priority)

| Rank | ID | Component | Failure Mode | RPN | Severity | Mitigation |
|------|-----|-----------|-------------|-----|----------|------------|
| 1 | 4.3 | execution-cascade | **False convergence:** grep check misses actual inconsistency | **168** | 7 | Add verify-consistency (P8) as independent safety net; researcher validates each grep match with context reading; consider adding semantic checks for INFRA file patterns (INPUT_FROM/OUTPUT_TO values, skill counts) |
| 2 | 4.2 | execution-cascade | **Cascade introduces new bugs** while fixing old inconsistencies | **144** | 8 | Reduce implementer maxTurns to 30 (already designed); execution-review applies extra scrutiny to cascade changes; cascade implementer prompt emphasizes "minimal change principle" -- only modify what is demonstrably inconsistent |
| 3 | 2.2 | on-implementer-done.sh | **grep timeout:** grep -rl takes >10s on large file set | **120** | 5 | Use `grep -Frl` (fixed string); scope to `.claude/` directory; parallelize with `xargs -P`; add per-grep `timeout 3s`; reduce hook timeout to 10s to fail fast |
| 4 | 1.1 | on-file-change.sh | **jq unavailable:** entire SRC chain silently breaks | **112** | 7 | Add jq availability check to manage-infra preflight; document jq as SRC hard dependency; consider pure-bash JSON parsing fallback for the simple field extraction needed |
| 5 | 2.4 | on-implementer-done.sh | **jq unavailable:** same as 1.1, affecting Stage 2 hook | **112** | 7 | Same mitigation as rank 4; both hooks share the jq dependency |
| 6 | 1.5 | on-file-change.sh | **Concurrent write corruption** from parallel implementers | **105** | 5 | Ensure script uses single `echo "..." >> file` (atomic for <PIPE_BUF); avoid multi-step writes; test with parallel implementer scenario |
| 7 | 3.5 | execution-impact | **False negative:** cascade_recommended: false when cascade actually needed | **105** | 7 | Researcher applies conservative threshold (recommend cascade if ANY direct dependent found); verify-consistency (P8) catches escapes; Lead can manually invoke execution-impact |
| 8 | 4.7 | execution-cascade | **Recursive hook alert:** cascade implementer triggers SubagentStop, Lead receives nested SRC alert | **100** | 5 | Skill L2 methodology must instruct Lead to ignore SRC alerts during active cascade execution; alternatively, use a flag file to suppress hook during cascade |
| 9 | 3.3 | execution-impact | **Stale codebase-map:** outdated dependency data leads to missed impacts | **100** | 5 | Auto-detect staleness (>7 day threshold); grep-only fallback preserves DIRECT detection; run manage-codebase after each pipeline to keep map fresh |
| 10 | 3.2 | execution-impact | **Misclassification:** TRANSITIVE labeled as DIRECT or vice versa | **96** | 4 | Require grep evidence chain in L2 output (file:line for each hop); execution-review validates classification; impact is limited since both types trigger cascade |

### Mitigation Priority Actions

**Immediate (implement during P4 planning):**
1. Use `grep -Frl` (fixed string) in both hooks -- prevents regex metacharacter issues AND is faster
2. Add symlink check and `chmod 600` to change log creation in on-file-change.sh
3. Add jq availability preflight to manage-infra or SRC deployment checklist
4. Document "ignore SRC alerts during active cascade" in execution-cascade L2

**During Implementation (P7):**
5. Test concurrent write scenario with parallel implementers
6. Test hook with maximum file count (30 changed files) and measure execution time
7. Implement per-grep timeout (`timeout 3s grep -Frl ...`)
8. Test cascade with circular dependency scenario to verify oscillation detection

**Post-Deployment (ongoing):**
9. Monitor L1 budget utilization after SRC skill addition (target: <90%)
10. Track false positive rate in cascade updates across 5 pipeline runs; tune grep patterns if >20%

---

## Risk Summary

### Overall Risk Level: **MEDIUM**

**Rationale:**

The SRC architecture is well-designed with graceful degradation that prevents any single failure from blocking the existing pipeline. The two-stage hook architecture correctly addresses the critical PostToolUse-context-injection misconception (GAP-IP1). Context budget analysis shows ample headroom (62% remaining).

**Primary risk cluster:** Cascade correctness (ranks 1, 2, 7, 8). The cascade mechanism is the most complex and least predictable component. False convergence (RPN 168) is the highest individual risk because grep-based consistency checking cannot detect semantic inconsistencies. The verify-consistency phase (P8) serves as an essential safety net.

**Secondary risk cluster:** Hook robustness (ranks 3, 4, 5, 6). The hooks are simple shell scripts with known failure modes. jq dependency (ranks 4-5) is a single point of failure for the entire SRC system. Performance under heavy load (rank 3) could degrade user experience but not correctness.

**Acceptable risks:**
- L1 budget at 89% is tight but manageable with documented mitigation options
- /tmp file security is low risk in the current single-user WSL2 environment
- API token cost for COMPLEX cascades (~350K tokens) is an operational concern, not a correctness or feasibility risk

**Unacceptable risks (must mitigate before implementation):**
- None identified. All risks have viable mitigations. The highest RPN (168) is addressed by the existing verify-consistency safety net plus proposed grep improvements.

### Risk Trend Forecast

| Phase | Risk Direction | Reason |
|-------|---------------|--------|
| Initial deployment | HIGHER | Untested in production, unknown edge cases |
| After 5 pipeline runs | MEDIUM | False positive rate calibrated, grep patterns tuned |
| After 20 pipeline runs | LOWER | Codebase-map mature, cascade patterns understood |
| Phase 2 (app code) | HIGHER | Larger scope, deeper dependency chains, new failure modes |
