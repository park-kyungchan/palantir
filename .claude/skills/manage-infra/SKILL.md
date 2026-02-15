---
name: manage-infra
description: |
  [Homeostasis·Manager·Infra] INFRA-wide health monitor and self-repair. Monitors .claude/ directory integrity -- agents, skills, references, CLAUDE.md, settings, hooks. Detects configuration drift, stale references, structural decay.

  WHEN: After .claude/ modification, after pipeline completion, or periodic health check. AI can auto-invoke.
  DOMAIN: Homeostasis (cross-cutting, entire .claude/ directory).

  SCOPE: agents/, skills/, settings.json, hooks/, CLAUDE.md.
  METHODOLOGY: (1) Inventory all .claude/ files, (2) Check counts match CLAUDE.md tables, (3) Validate settings.json schema, (4) Detect orphaned/unreferenced files, (5) Propose cleanup actions.
  OUTPUT_FORMAT: L1 YAML health report (component counts, orphans, drift items), L2 markdown narrative with repair recommendations.
user-invocable: true
disable-model-invocation: false
---

# Manage — INFRA

## Execution Model
- **TRIVIAL**: Lead-direct. Quick health check on single component.
- **STANDARD**: Spawn analyst. Systematic inventory and drift detection.
- **COMPLEX**: Spawn 2 analysts. One for agents+skills, one for settings+hooks+CLAUDE.md.

## Methodology

### 1. Inventory All Components
Scan entire `.claude/` directory:
- Count agents: `Glob .claude/agents/*.md`
- Count skills: `Glob .claude/skills/*/SKILL.md`
- Read settings: `.claude/settings.json`
- List hooks: `Glob .claude/hooks/*`
- Read CLAUDE.md for declared counts

For STANDARD/COMPLEX tiers, construct the delegation prompt for each analyst with:
- **Context**: Expected component layout: agents in `.claude/agents/`, skills in `.claude/skills/*/SKILL.md`, hooks in `.claude/hooks/`, settings at `.claude/settings.json`, CLAUDE.md at `.claude/CLAUDE.md`. Include current declared counts from CLAUDE.md (agents: 6, skills: 35).
- **Task**: "Scan entire .claude/ directory. Count agents, skills, hooks. Read settings.json for validity. Compare filesystem counts against CLAUDE.md declarations. Find orphaned files (unreferenced agents, skills without SKILL.md, hooks not in settings). Find configuration drift (settings referencing nonexistent files, CLAUDE.md version mismatch)."
- **Constraints**: Read-only. Use Glob for discovery, Read for content. No modifications. Report findings with severity classification.
- **Expected Output**: L1 YAML health report with component counts, orphans, drift_items. L2 narrative with repair recommendations.

### 2. Check Count Consistency
Compare filesystem counts against CLAUDE.md declarations:
- Agent count in `§1 Team Identity` matches `.claude/agents/` file count
- Skill count matches `.claude/skills/` directory count
- Domain count matches unique domains across skill descriptions

### 3. Detect Orphaned Files
Find files that exist but are unreferenced:
- Agent files not matching any agent name in CLAUDE.md or skill descriptions
- Skill directories without valid SKILL.md
- Hook scripts not referenced in settings.json
- Agent-memory directories for non-existent agents

**Orphan Detection Algorithm**:
```
For each agent file in .claude/agents/:
  name = extract frontmatter "name" field
  referenced = grep(name, ".claude/CLAUDE.md") OR
               grep(name, ".claude/skills/*/SKILL.md")
  if not referenced: mark ORPHAN (severity: warning)

For each skill directory in .claude/skills/:
  if not exists(dir/SKILL.md): mark ORPHAN (severity: critical -- directory without skill definition)
  name = extract frontmatter "name" field from dir/SKILL.md
  if name not found in any other skill's INPUT_FROM/OUTPUT_TO:
    mark WARN "unreferenced skill" (severity: info -- may be user-invocable leaf)

For each hook file in .claude/hooks/:
  basename = filename without path
  referenced = grep(basename, ".claude/settings.json")
  if not referenced: mark ORPHAN (severity: warning -- dead code hook)

For agent-memory directories (.claude/agent-memory/*/):
  SKIP entirely -- these are volatile runtime data, not INFRA components
  Exception: if a directory name does not match any agent name, note as INFO only
```

### 4. Detect Configuration Drift
Check for inconsistencies:
- settings.json `permissions.allow` entries reference existing skills
- Hook scripts reference valid paths and tools
- CLAUDE.md version info matches actual state

**Settings.json Validation Checklist**:

| Check | Method | Expected | Severity if Fail |
|-------|--------|----------|------------------|
| JSON syntax | Read file, validate structure | Valid JSON (no trailing commas, balanced brackets) | CRITICAL |
| permissions.allow entries | For each entry: Glob for referenced skill path | Path exists in `.claude/skills/` | CRITICAL |
| Hook event references | For each hook command: check file path exists | File found in `.claude/hooks/` | CRITICAL |
| Hook event matchers | For each matcher regex: validate it compiles | Valid regex pattern | WARNING |
| model setting | Check value present and recognized | sonnet, opus, or haiku (aliases) | WARNING |
| teammateMode | Check value | `tmux` (expected for Agent Teams) | INFO |
| alwaysThinkingEnabled | Check value | `true` (expected for Opus 4.6) | INFO |

For each failed check, record the finding with: check name, actual value, expected value, severity, and recommended fix.

### 5. Propose Repair Actions
For each detected issue:
- Classify severity: critical (broken reference) / warning (orphan) / info (drift)
- Propose specific fix action
- Await user approval before applying

## Decision Points

### Scan Scope
- **Full scan** (default): Inventory all `.claude/` components -- agents, skills, settings, hooks, CLAUDE.md. Use for periodic health checks, after major pipeline completions, or when drift is suspected.
- **Targeted scan**: Focus on a single component type (e.g., only skills, only hooks). Use when a specific modification was just made and only that component type needs validation.

### Orphan Handling
- **Report only** (default): List orphaned files with severity classification and await user approval. Preferred for safety -- accidental deletion of a valid file is worse than keeping an orphan.
- **Auto-propose cleanup script**: Generate a list of removal commands for the user to review and execute. Use when orphan count is high (>5) and manual cleanup is tedious.

### Drift Classification Severity
- **Broken reference = critical**: A settings.json entry references a file that does not exist. This can cause runtime failures.
- **Count mismatch = warning**: CLAUDE.md declares "6 agents" but filesystem has 7. Functional but misleading.
- **Stale version info = info**: CLAUDE.md version string doesn't match recent changes. Cosmetic but confusing.

### Health Score Calculation
Compute a numeric health score across all INFRA components:

| Component | Weight | Healthy (3) | Degraded (2) | Critical (1) | Missing (0) |
|-----------|--------|-------------|---------------|---------------|-------------|
| Agents | 20% | Count matches CLAUDE.md | Count mismatch <=1 | Count mismatch >1 or orphaned | No agent files found |
| Skills | 30% | Count matches, all have SKILL.md | Count mismatch <=2 | Missing SKILL.md or count >2 off | No skill dirs found |
| Settings | 20% | Valid JSON, all refs exist | Minor warnings (unused entries) | Invalid JSON or broken refs | File missing |
| Hooks | 15% | All referenced in settings, valid shebang | Missing from settings but file exists | Syntax error or missing file | No hooks dir |
| CLAUDE.md | 15% | Counts match, version current | Minor drift (version string stale) | Major count mismatch (>2 off) | File missing |

Formula: `score = sum(component_weight * component_score) / 3.0 * 100`

Each component scores 0-3. Weighted sum divided by max possible (3.0) yields percentage.

Thresholds for overall status:
- **>85%** = `healthy` -- no action needed, report for record
- **60-85%** = `degraded` -- report findings, recommend targeted fixes
- **<60%** = `critical` -- urgent report, recommend immediate intervention

Include the numeric score in L1 output (`health_score: 87`) so Lead can track trends across runs.

### Periodic vs Triggered Scan Decision
Different triggers warrant different scan scopes:

- **Post-pipeline trigger**: After delivery-pipeline completes, run full scan. This is the most common trigger. The full pipeline may have added/modified/deleted agents, skills, or hooks. Full scan catches any drift introduced during the pipeline.
- **Post-modification trigger**: After any execution-infra modifies `.claude/` files, run a targeted scan on the modified component type only. For example, if execution-infra added a new hook, scan only hooks + settings.json (for reference integrity). This avoids unnecessary full scans after minor changes.
- **Periodic (user-invoked)**: User explicitly requests health check via `/manage-infra`. Always full scan regardless of recent activity. User may suspect drift that automated triggers missed.
- **Post-RSI trigger**: After self-diagnose + self-implement cycle completes, run full scan to verify RSI changes did not introduce drift. RSI modifies multiple component types simultaneously, so full scan is mandatory. Cross-reference the list of modified files from self-diagnose/self-implement output against detected changes.

Decision heuristic for Lead: if the trigger source provides a list of modified files, use targeted scan. If no file list is available or the trigger is periodic/post-RSI, use full scan.

### Cross-Component Drift Detection
Some drift findings span multiple component types. Detect and report these as unified findings:

- **Settings -> Hook drift**: `settings.json` references a hook command path that does not exist in `.claude/hooks/`. Affects both settings and hooks components. Single finding, both components marked degraded.
- **CLAUDE.md -> Agent drift**: CLAUDE.md lists an agent name in Section 1 that has no corresponding file in `.claude/agents/`. Affects both CLAUDE.md accuracy and agent inventory. Single finding.
- **Skill -> Agent drift**: A skill description's DPS template references an agent name (via `subagent_type`) that does not exist in `.claude/agents/`. Affects both skills and agents components. Single finding.
- **Skill -> Skill drift**: A skill's `INPUT_FROM` or `OUTPUT_TO` references a skill name that has no corresponding directory in `.claude/skills/`. Internal skill graph broken.
- **Hook -> Settings drift**: A hook file exists in `.claude/hooks/` but is not referenced by any event in `settings.json`. The hook is effectively dead code. Single finding, hooks component marked degraded.

Report cross-component drift as: `"[CROSS] settings+hooks: settings.json references nonexistent hook .claude/hooks/missing.sh"`. The `[CROSS]` prefix helps Lead distinguish these from single-component findings.

## Failure Handling
- **Unfixable issues detected**: Report findings with severity classification but do NOT auto-fix; await user approval
- **Scan cannot complete** (e.g., file read errors): Report partial results with coverage percentage in L1
- **Safety**: Never auto-delete or auto-fix without explicit rationale per finding
- **Pipeline impact**: Non-blocking (homeostasis is on-demand). Partial health report is still actionable

### Failure Severity and Routing Matrix

| Failure Type | Severity | Route To | Data Passed |
|---|---|---|---|
| Invalid settings.json (parse error) | CRITICAL | User (urgent) | Parse error details, line number if available |
| Skill directory without SKILL.md | CRITICAL | User (urgent) | Directory path, expected SKILL.md location |
| Broken reference in settings.json | CRITICAL | User (urgent) | File path, reference string, expected target |
| CLAUDE.md count mismatch | WARNING | User (report) | Declared vs actual count per component type |
| Orphaned agent file | WARNING | User (report) | File path, reason "unreferenced in CLAUDE.md or skills" |
| Orphaned hook file | WARNING | User (report) | File path, reason "not in settings.json events" |
| Stale version info | INFO | User (report) | Current version string, suggested update |
| Scan incomplete (file errors) | MEDIUM | User (partial report) | Coverage percentage, list of skipped files |

Note: manage-infra is homeostasis -- it never blocks the pipeline. It reports findings for user action. CRITICAL findings need urgent user attention but do not halt any running pipeline. The distinction is urgency of human review, not pipeline gating.

## Anti-Patterns

### DO NOT: Auto-Fix Without User Approval
Even "obvious" fixes (deleting an orphaned file, correcting a count) should be reported and awaited. An orphaned file might be intentionally staged for a future pipeline. Always report, never auto-fix.

### DO NOT: Modify settings.json Structure
This skill reads and validates settings.json but should never restructure it. If settings drift is detected, propose the minimal edit needed. Reformatting valid JSON can break comment-like patterns or ordering expectations.

### DO NOT: Ignore Hook Script Validation
Hooks are often overlooked because they're shell scripts, not YAML. But a broken hook (wrong path, missing shebang, bad exit code) can silently corrupt pipeline behavior. Always validate hook references in settings.json match actual files.

### DO NOT: Trust CLAUDE.md Counts as Source of Truth
The filesystem is the source of truth. CLAUDE.md counts are derived documentation. If counts mismatch, the filesystem wins -- update CLAUDE.md to match filesystem, not the reverse.

### DO NOT: Scan Agent-Memory as INFRA Components
Agent-memory directories (`agent-memory/`, `agent-memory-local/`) are volatile runtime data, not INFRA components. Including them in health checks produces false orphan alerts. Only scan the declared component directories.

### DO NOT: Run Health Check During Active Pipeline
manage-infra reads the same files that execution-infra writes. Running a health check while a pipeline is actively modifying `.claude/` files produces false positives (mid-write state detected as drift). Always wait for pipeline completion before running manage-infra. The post-pipeline trigger exists precisely for this reason.

### DO NOT: Confuse Homeostasis with Verification
manage-infra is proactive health monitoring -- it detects drift before it causes problems. The verify-structural-content through verify-cc-feasibility skills are reactive verification -- they validate correctness after specific changes. Different triggers, different scopes:
- **manage-infra**: Broad scan, all component types, detects drift and decay over time
- **verify-* skills**: Narrow scope, specific files just modified, validates conformance to standards

Invoking manage-infra as a substitute for verify-structural-content after modifying a single skill file is wasteful. Invoking verify-structural-content as a substitute for manage-infra to check overall health misses cross-component drift.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| (self-triggered) | Health check request after .claude/ modification | No structured input -- scans filesystem directly |
| delivery-pipeline | Post-delivery health check request | L1 YAML with pipeline completion status |
| self-implement | Post-RSI implementation results | L1 YAML with list of modified .claude/ files |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| (user) | Health report with repair recommendations | Always (terminal -- report to user) |
| execution-infra | Repair task assignments | If user approves proposed repairs |
| manage-skills | Skill-specific drift detected | If skill count mismatch or orphaned skill directories found |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Scan cannot complete | (user) | Partial health report with coverage percentage |
| Critical broken references | (user) | Urgent report requiring immediate manual intervention |
| Unfixable structural issues | (user) | Findings with severity classification, no auto-fix |

## Quality Gate
All six criteria must be met for `status: healthy`:
1. All component counts consistent between CLAUDE.md declarations and filesystem reality
2. Zero orphaned files detected (or documented exceptions with rationale)
3. Zero broken references in settings.json (all permission paths, hook commands resolve)
4. settings.json is valid JSON with all fields in expected value types
5. All hook files in `.claude/hooks/` exist and are referenced by at least one event in settings.json
6. Health score calculated and reported in L1 output (numeric `health_score` field, percentage)

## Output

### L1
```yaml
domain: homeostasis
skill: manage-infra
status: healthy|degraded|critical
health_score: 87          # percentage, see Health Score Calculation
trigger: post-pipeline|post-modification|periodic|post-rsi
components:
  agents: {count: 6, expected: 6, orphans: 0, score: 3}
  skills: {count: 35, expected: 35, orphans: 0, score: 3}
  settings: {valid: true, broken_refs: 0, score: 3}
  hooks: {count: 5, referenced: 5, score: 3}
  claude_md: {version: "v10.7", counts_match: true, score: 3}
drift_items: 0
cross_component_drift: 0
findings:               # list of individual findings
  - {component: skills, severity: WARNING, detail: "count mismatch: 36 vs 35"}
```

### L2
- Component inventory with counts and per-component health scores
- Orphaned file detection with classification (ORPHAN vs WARN vs INFO)
- Cross-component drift analysis with `[CROSS]` prefixed findings
- Settings.json validation checklist results
- Repair recommendations with severity classification and proposed fix actions
- Health score breakdown showing weight, raw score, and weighted contribution per component
