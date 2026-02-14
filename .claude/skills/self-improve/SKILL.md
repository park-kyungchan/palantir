---
name: self-improve
description: |
  [Homeostasis·SelfImprove·Recursive] Autonomous INFRA self-improvement cycle. Researches CC native capabilities via claude-code-guide, diagnoses deficiencies across agents/skills/hooks/settings, implements fixes via infra-implementer, verifies full compliance, commits changes, records learnings.

  WHEN: User invokes for periodic INFRA evolution. After CC updates, after feature changes, before releases, or for drift detection. Not auto-invoked — user decides when to run improvement cycle.
  DOMAIN: Homeostasis (cross-cutting, self-improvement). Third homeostasis skill alongside manage-infra and manage-skills.

  METHODOLOGY: (1) Spawn claude-code-guide for latest CC native feature/field research, (2) Self-diagnose all .claude/ files against native field lists + routing + budget + features, (3) Spawn infra-implementer waves for fixes (parallel by category), (4) Full compliance verify (zero non-native fields), (5) Git commit + update MEMORY.md + context-engineering.md.
  PREREQUISITE: Clean branch or branch ready for INFRA changes.
  OUTPUT_FORMAT: L1 YAML improvement manifest, L2 markdown self-improvement report with commit hash.
user-invocable: true
disable-model-invocation: true
argument-hint: "[focus-area]"
---

# Self-Improve — Recursive INFRA Evolution

## Execution Model
- **TRIVIAL**: Lead-direct. Quick scan + fix for 1-2 specific areas.
- **STANDARD**: 1 claude-code-guide + 1-2 infra-implementer waves. Full cycle.
- **COMPLEX**: Multiple claude-code-guide rounds + 3-4 implementer waves + extended verification.

## Methodology

### 1. Research CC Native State
Spawn claude-code-guide agent for ground truth:
- Query: "What are ALL native frontmatter fields for Claude Code skills and agents?"
- Include focus-area from user arguments if provided
- Record findings as authoritative reference for diagnosis
- Check for NEW native features not yet used in INFRA
- Compare against `memory/context-engineering.md` for delta

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
