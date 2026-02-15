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
Scan all `.claude/` files systematically:
- **Field compliance**: Extract frontmatter fields from all agents + skills, check against native lists
- **Routing integrity**: Verify no `disable-model-invocation: true` on pipeline skills
- **Budget analysis**: Calculate total L1 description chars vs SLASH_COMMAND_TOOL_CHAR_BUDGET
- **Feature gaps**: Check agent memory/maxTurns/hooks configuration
- **Hook validity**: Verify hook scripts use correct CC patterns (hookSpecificOutput, additionalContext)
- **Settings consistency**: Check permissions, env vars, model settings
- Produce categorized finding list with severity (CRITICAL, HIGH, LOW)

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
Post-implementation verification:
- Re-scan all files: zero non-native fields required
- Verify routing: all auto-loaded skills visible in system-reminder
- Verify budget: total description chars within SLASH_COMMAND_TOOL_CHAR_BUDGET
- Verify field value types: correct enums, booleans, strings
- If any FAIL: loop back to step 3 with targeted fixes

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
- Create structured commit message with change categories
- Report final ASCII status visualization

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
status: complete|partial
cc_guide_spawns: 0
findings_total: 0
findings_fixed: 0
findings_deferred: 0
files_changed: 0
commit_hash: ""
```

### L2
- claude-code-guide research summary (delta from last run)
- Categorized findings with severity
- Fix implementation summary per wave
- Compliance verification results
- Commit details and MEMORY.md updates
