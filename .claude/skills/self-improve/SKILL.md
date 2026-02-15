---
name: self-improve
description: |
  [Homeostasis·SelfImprove·Recursive] Autonomous INFRA self-improvement cycle. Researches CC native capabilities via claude-code-guide, diagnoses deficiencies across agents/skills/hooks/settings, implements fixes, verifies compliance, commits changes.

  WHEN: User invokes for periodic INFRA evolution. After CC updates, feature changes, or before releases. Requires clean branch. Not auto-invoked.
  DOMAIN: Homeostasis (cross-cutting, self-improvement). Third homeostasis skill alongside manage-infra and manage-skills.

  METHODOLOGY: (1) Spawn claude-code-guide for CC native feature research, (2) Self-diagnose all .claude/ files against native fields + routing + budget, (3) Spawn infra-implementer waves for fixes (parallel by category), (4) Full compliance verify (zero non-native fields), (5) Git commit + update MEMORY.md + context-engineering.md.
  OUTPUT_FORMAT: L1 YAML improvement manifest, L2 markdown self-improvement report with commit hash.
user-invocable: true
disable-model-invocation: false
argument-hint: "[focus-area]"
---

# Self-Improve — Recursive INFRA Evolution

## Execution Model
- **TRIVIAL**: Lead-direct. Quick scan + fix for 1-2 specific areas.
- **STANDARD**: 1 claude-code-guide + 1-2 infra-implementer waves. Full cycle.
- **COMPLEX**: Multiple claude-code-guide rounds + 3-4 implementer waves + extended verification.

## Methodology

### 1. Research CC Native State
First, read cached reference: `memory/cc-reference/` (4 files: native-fields, context-loading, hook-events, arguments-substitution).
- If reference exists and is recent: use as ground truth (skip claude-code-guide spawn)
- If reference outdated or focus-area requires new info: spawn claude-code-guide (if unavailable, use cc-reference cache in `memory/cc-reference/`) for delta only
- Query focus: "What NEW native features exist since last verification date?"
- Include focus-area from user arguments if provided
- Update cc-reference files with any new findings
- Compare against `memory/context-engineering.md` for decision history

### 2. Self-Diagnose INFRA
Scan all `.claude/` files systematically using the diagnostic category checklist below. Spawn analyst agents for parallel scanning when the scope is full (no focus-area). Each category maps to specific tools and has a pre-assigned severity if failed.

**Diagnostic Category Checklist:**

| Category | Check | Tool | Severity if Failed |
|---|---|---|---|
| Field compliance | Non-native frontmatter fields present | Read + compare to `memory/cc-reference/native-fields.md` | CRITICAL |
| Routing integrity | `disable-model-invocation: true` on pipeline skills | Grep across `.claude/skills/` | CRITICAL |
| L1 budget | Total description chars exceed 32000 (SLASH_COMMAND_TOOL_CHAR_BUDGET) | Read all skill descriptions + sum character counts | HIGH |
| Hook validity | Shell scripts have correct shebang, exit codes, JSON output format | Read each hook script, check structure | HIGH |
| Agent memory config | `memory` field is valid enum for each agent | Read `.claude/agents/*.md` frontmatter | MEDIUM |
| Settings permissions | All `allow` entries reference existing tools/skills | Read `settings.json`, cross-reference | MEDIUM |
| Description utilization | Each description uses more than 80% of 1024 chars | Read + measure per-skill char count | LOW |
| Color assignments | All agents have unique `color` fields | Read agents, check for duplicates | LOW |

**Procedure:**
- For focused scans (user-provided focus-area), run only the matching categories
- For full scans, run all 8 categories and compile into a single finding list
- Each finding includes: ID, category, severity, file path, current value, expected value
- Produce categorized finding list sorted by severity (CRITICAL first, then HIGH, MEDIUM, LOW)

### 3. Implement Fixes
Spawn infra-implementer agents in parallel waves:
- Group fixes by category (field removal, feature addition, routing fix, etc.)
- Max 2 infra-implementers per wave to avoid file conflicts

Construct each delegation prompt with:
- **Context**: Paste the specific findings for this wave (from Step 2 diagnosis) with severity and category. Include the CC native field reference: list which fields are valid for the file type being modified (from `memory/cc-reference/native-fields.md`). For description edits, include current character count and the 1024-char limit.
- **Task**: For each file in this wave, specify the exact change: "Remove field `X` from `.claude/agents/Y.md`", "Change `disable-model-invocation` from `true` to `false` in `.claude/skills/Z/SKILL.md`", or "Rewrite description to include WHEN/DOMAIN/INPUT_FROM/OUTPUT_TO within 1024 chars." Provide the target value or replacement text where possible.
- **Constraints**: Write and Edit tools only — no Bash. Files in this wave must not overlap with other concurrent infra-implementers. Only modify files listed in the finding — do not "fix" adjacent files not in scope. Preserve existing valid content (don't rewrite entire files for a single field change).
- **Expected Output**: Report as L1 YAML with `files_changed` (array), `findings_fixed` (count), `status` (complete|partial|failed). Provide L2 markdown with per-file change log: finding ID, what was changed, before→after values. Flag any findings that could not be fixed with reason.

Monitor completion. If a wave produces failures, re-spawn with corrected instructions (max 1 retry per wave).

### 4. Verify Full Compliance
Post-implementation verification pass. Re-run the diagnostic categories from Step 2, but only for files that were modified in Step 3. This targeted re-scan is faster than a full scan and catches regressions introduced during fixes.

**Verification checklist:**
- Re-scan modified files: zero non-native fields required (CRITICAL category from Step 2)
- Verify routing: all auto-loaded skills visible in system-reminder, no `disable-model-invocation: true` on pipeline skills
- Verify budget: total description chars within SLASH_COMMAND_TOOL_CHAR_BUDGET (recalculate after any description edits)
- Verify field value types: correct enums, booleans, strings (no type mismatches)
- Cross-reference check: INPUT_FROM/OUTPUT_TO bidirectionality still intact after any skill description rewrites
- Hook scripts: shebang line preserved, exit codes correct, JSON output format valid

**Iteration logic:**
- If zero findings remain: proceed to Step 5 (convergence achieved)
- If findings remain but count decreased: loop back to Step 3 with targeted fixes (max 3 total iterations)
- If findings remain and count did not decrease (plateau): evaluate severity of remaining findings. If all remaining are LOW, accept partial convergence. If MEDIUM+ remain, attempt one more targeted wave before accepting partial.

### 5a. Update Records (spawn infra-implementer)
**Executor: spawn infra-implementer** for file modifications (Lead NEVER edits files directly).

Update persistent memory with improvement cycle results:
- Update `memory/context-engineering.md` with new findings
- Update `MEMORY.md` session history

**DPS (infra-implementer spawn):**
- **Context**: Improvement cycle findings from Steps 2-4, list of files changed, cc-reference updates
- **Task**: Update memory/context-engineering.md with new CC native findings and decision rationale. Update MEMORY.md session history with cycle summary (findings count, files changed, commit intent).
- **Constraints**: Edit tool only — modify existing content sections, do not restructure files. Only update sections relevant to this cycle.
- **Expected Output**: L1 YAML with files_updated (array), status. L2 with per-file change summary.

### 5b. Commit (Lead-direct or /delivery-pipeline)
**Executor: Lead-direct** via Bash tool, or route to /delivery-pipeline skill for full delivery flow.

Finalize the improvement cycle:
- Stage changed files with `git add` (specific files, never `-A`)
- Create structured commit message following pattern: `feat(infra): RSI [scope] -- [summary]`
  - Include finding categories in commit body (e.g., "CRITICAL: 3 fixed, HIGH: 5 fixed, MEDIUM: 2 deferred")
  - Reference iteration count and convergence status
- Report final ASCII status visualization with: iteration count, findings breakdown by severity, files changed, convergence status

## Decision Points

### CC Reference Cache vs Live Research
- **Use cache only**: cc-reference files exist and were updated within the last RSI cycle. No focus-area requiring new CC features. Skip claude-code-guide spawn entirely (saves budget).
- **Delta research**: Cache exists but user-specified focus-area targets features not covered in cache, or CC platform has announced updates since last cycle. Spawn claude-code-guide with narrow query for delta only, merge into cache.
- **Full research**: No cc-reference cache exists, or cache is fundamentally stale (e.g., major CC version change). Spawn claude-code-guide for comprehensive feature inventory.

### Diagnosis Scope
- **Focused**: User provides `[focus-area]` argument (e.g., "hooks", "agent-fields"). Scan only the specified category. Faster cycle, fewer implementer waves.
- **Full scan**: No focus-area specified. Diagnose all .claude/ files: agents, skills, hooks, settings, CLAUDE.md. Comprehensive but heavier (3-4 implementer waves typical).

### Fix Wave Parallelism
- **Single wave**: 5 or fewer findings, all in non-overlapping files. One infra-implementer handles everything.
- **Parallel waves**: 6+ findings spanning multiple file categories. Group by category (field fixes, routing fixes, budget fixes) with max 2 concurrent infra-implementers per wave to avoid file conflicts.

### Convergence Threshold
- **Strict convergence**: Zero findings remaining after implementation. Required for pre-release cycles.
- **Partial convergence**: Severity plateau after 3 iterations (same finding count between iterations). Acceptable for incremental improvement cycles. Defer remaining LOW findings.

### Iteration Strategy
How many RSI iterations to plan based on scope and expected finding volume:
- **Quick fix** (1 iteration): User specifies a narrow focus-area, fewer than 5 findings expected. Single diagnose-fix-verify cycle. Example: `/self-improve hooks` targeting only hook scripts.
- **Standard cycle** (2-3 iterations): No focus-area specified, full scan. Expect 10-20 findings in first iteration, diminishing in subsequent. Standard convergence pattern. Most common invocation pattern.
- **Deep evolution** (3-5 iterations): Major CC version change or significant structural rework. Expect 30+ findings initially. May not fully converge -- accept partial status after 3 iterations if severity plateau reached. Example: after CC platform upgrade with new native fields.

### Fix Priority Ordering
When diagnosis produces many findings, fix in this strict priority order:
1. **CRITICAL**: Non-native fields, routing breaks, `disable-model-invocation: true` on pipeline skills (blocks pipeline entirely)
2. **HIGH**: Budget overflows, hook validity issues, agent memory config errors (degrades quality or causes silent failures)
3. **MEDIUM**: Settings inconsistencies, description utilization below 80%, stale references (cleanup, not blocking)
4. **LOW**: Color assignments, minor formatting, redundant content (cosmetic)

Higher severity fixes first because they may cascade -- fixing a CRITICAL routing issue may resolve a MEDIUM description issue downstream. Within the same severity level, group by file category for wave efficiency.

### Claude-code-guide Spawn Decision Tree
Determines whether to spawn a live claude-code-guide agent or use the cached cc-reference:
```
cc-reference cache exists? (memory/cc-reference/ has 4 files)
|-- NO --> Spawn claude-code-guide (full research). STOP if unavailable.
+-- YES --> Cache updated within 7 days?
    |-- YES --> Focus-area covered by cache?
    |   |-- YES --> Skip spawn (use cache only). Lowest cost path.
    |   +-- NO --> Spawn claude-code-guide (delta query for focus-area only)
    +-- NO --> CC version changed since cache?
        |-- YES --> Spawn claude-code-guide (full research, cache is stale)
        +-- NO --> Use cache (likely still valid, CC versions are stable)
```
Each claude-code-guide spawn costs significant context budget. The decision tree minimizes unnecessary spawns while ensuring ground truth accuracy. When in doubt, prefer delta query over full research.

## Anti-Patterns

### DO NOT: Skip Self-Diagnosis and Fix Blindly
Never apply fixes based on assumptions or memory of past issues without running the full diagnosis step. The INFRA state changes between cycles, and stale assumptions cause regressions (e.g., re-adding a field that was intentionally removed).

### DO NOT: Spawn claude-code-guide When Cache Is Sufficient
Each claude-code-guide spawn consumes significant context budget. If cc-reference cache is current and the focus-area is well-covered, use the cache. Reserve live research for genuine unknowns.

### DO NOT: Modify Files Outside .claude/ Directory
Self-improve scope is strictly .claude/ infrastructure. Application source code, documentation outside .claude/, and user project files are never in scope. If diagnosis reveals source code issues, document them as findings for a separate pipeline.

### DO NOT: Commit Partial Fixes Without Documenting Deferred Items
If convergence is not reached (partial status), every deferred finding must be recorded in MEMORY.md with severity and rationale. Silent deferral creates invisible tech debt that compounds across cycles.

### DO NOT: Run Multiple RSI Cycles Without Verifying Previous Cycle
Each cycle must verify the previous cycle's fixes are still intact before adding new changes. Running back-to-back cycles without verification can create oscillating fixes (cycle N fixes X, cycle N+1 breaks X while fixing Y).

### DO NOT: Fix Issues in Order of Discovery
Issues found first are not necessarily most important. Always sort findings by severity before creating implementer waves. A CRITICAL routing break found last in the scan should be fixed before a LOW color assignment found first. Discovery order is arbitrary (file scan order); severity order is principled.

### DO NOT: Update MEMORY.md With Every Iteration
MEMORY.md should only be updated once, at the final commit step (5a). Updating it mid-cycle creates noise and risks conflicts if the cycle is interrupted or aborted. Only the final converged state goes into MEMORY.md. Intermediate iteration results live only in Lead's working context.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| (User invocation) | Focus area or general improvement request | `$ARGUMENTS` text: focus-area string or empty |
| manage-infra | Health check findings suggesting deeper improvement | L1 YAML: `health_score`, `findings[]` with severity |
| manage-skills | Skill inventory gaps or compliance issues | L1 YAML: `actions[]` with CREATE/UPDATE/DELETE |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| delivery-pipeline | Committed improvement cycle (git commit) | Step 5b routes to delivery for formal commit flow |
| manage-skills | Updated skills needing inventory refresh | After skill frontmatter modifications in Step 3 |
| manage-infra | Updated INFRA needing health re-check | After any structural changes to .claude/ |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| cc-reference cache unavailable AND claude-code-guide fails | (Abort) | `status: blocked`, reason: no ground truth |
| Non-convergence after 3 iterations | (Terminate partial) | `status: partial`, remaining findings with severity |
| Infra-implementer wave failure (after 1 retry) | Self (continue with remaining waves) | Failed findings deferred, successful waves committed |

## Failure Handling

| Failure Type | Severity | Route To | Blocking? | Resolution |
|---|---|---|---|---|
| cc-reference cache missing + guide fails | CRITICAL | Abort | Yes | No ground truth. Cannot proceed without reference. Report `status: blocked`. |
| Budget overflow detected | HIGH | Fix | Yes | Must resolve before commit -- oversize descriptions truncate routing. Prioritize in next wave. |
| Non-convergence after 3 iterations | HIGH | Terminate partial | No | Commit successful fixes. Defer remaining in MEMORY.md with severity. Report `status: partial`. |
| Infra-implementer wave failure (all files) | HIGH | Retry once | Conditional | Re-spawn with corrected prompt. If retry fails, defer all findings from that wave. |
| Infra-implementer partial failure | MEDIUM | Continue | No | Some files fixed, others deferred. Continue with remaining waves. Log partial results. |
| Diagnosis finds 0 issues | INFO | Complete | N/A | INFRA is healthy. Report clean bill of health with `findings_total: 0`. |

**Pipeline impact**: Non-blocking (homeostasis is user-invoked). Partial improvements are committed; deferred items documented for next cycle.

## Quality Gate
- claude-code-guide research completed or cc-reference cache used (ground truth established)
- All findings addressed or explicitly deferred with severity and rationale
- Zero CRITICAL findings remaining (non-native fields, routing breaks)
- Zero HIGH findings remaining (budget overflow, hook validity)
- No routing breaks (all pipeline skills auto-loaded correctly)
- Budget usage under 90% of SLASH_COMMAND_TOOL_CHAR_BUDGET
- Changes committed with structured message including finding categories
- MEMORY.md updated with session history entry

## Output

### L1
```yaml
domain: homeostasis
skill: self-improve
status: complete|partial|blocked
iteration_count: 0
cc_guide_spawns: 0
cc_reference_source: cache|delta|full|none
findings_total: 0
findings_by_severity:
  critical: 0
  high: 0
  medium: 0
  low: 0
findings_fixed: 0
findings_deferred: 0
files_changed: 0
implementer_waves: 0
commit_hash: ""
```

### L2
Structured markdown report with the following sections:
- **CC Research Summary**: claude-code-guide research delta from last run, or cache-only note if no spawn was needed. Include any new native fields or features discovered.
- **Diagnosis Report**: Categorized findings table with columns: ID, category, severity, file, description, status (fixed/deferred). Total counts per severity level.
- **Implementation Log**: Per-wave summary showing which infra-implementer handled which findings, files changed, and any retries needed. Include before/after values for key changes.
- **Verification Results**: Post-fix compliance scan results. Confirm zero CRITICAL, zero HIGH remaining. Note any deferred items with severity and rationale.
- **Commit Details**: Git commit hash, structured commit message, list of staged files. Note branch name and any PR intent.
- **MEMORY.md Update**: Summary of what was added to session history (finding counts, files changed, key decisions).
