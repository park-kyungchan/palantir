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
- If reference outdated or focus-area requires new info: spawn claude-code-guide (if unavailable, use cc-reference cache in agent-memory) for delta only
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
- Each implementer receives: specific file list + exact changes + verification criteria
- Monitor completion, re-spawn if needed

### 4. Verify Full Compliance
Post-implementation verification:
- Re-scan all files: zero non-native fields required
- Verify routing: all auto-loaded skills visible in system-reminder
- Verify budget: total description chars within SLASH_COMMAND_TOOL_CHAR_BUDGET
- Verify field value types: correct enums, booleans, strings
- If any FAIL: loop back to step 3 with targeted fixes

### 5. Commit and Record
Finalize the improvement cycle:
- Stage changed files with `git add` (specific files, never `-A`)
- Create structured commit message with change categories
- Update `memory/context-engineering.md` with new findings
- Update `MEMORY.md` session history
- Report final ASCII status visualization

## Quality Gate
- claude-code-guide research completed (ground truth established)
- All findings addressed or explicitly deferred with rationale
- Zero non-native fields across all agents and skills
- No routing breaks (all pipeline skills auto-loaded)
- Budget usage under 90% of SLASH_COMMAND_TOOL_CHAR_BUDGET
- Changes committed with structured message

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
