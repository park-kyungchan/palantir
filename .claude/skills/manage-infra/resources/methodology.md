# Manage Infra — Detailed Methodology

> On-demand reference. Contains the orphan detection algorithm, settings.json validation checklist,
> health score calculation table and formula, scan trigger decision heuristics, cross-component
> drift detection patterns, and the failure severity routing matrix.

---

## Orphan Detection Algorithm

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

---

## Settings.json Validation Checklist

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

---

## Health Score Calculation

| Component | Weight | Healthy (3) | Degraded (2) | Critical (1) | Missing (0) |
|-----------|--------|-------------|--------------|--------------|-------------|
| Agents | 20% | Count matches CLAUDE.md | Count mismatch <=1 | Count mismatch >1 or orphaned | No agent files found |
| Skills | 30% | Count matches, all have SKILL.md | Count mismatch <=2 | Missing SKILL.md or count >2 off | No skill dirs found |
| Settings | 20% | Valid JSON, all refs exist | Minor warnings (unused entries) | Invalid JSON or broken refs | File missing |
| Hooks | 15% | All referenced in settings, valid shebang | Missing from settings but file exists | Syntax error or missing file | No hooks dir |
| CLAUDE.md | 15% | Counts match, version current | Minor drift (version string stale) | Major count mismatch (>2 off) | File missing |

**Formula**: `score = sum(component_weight * component_score) / 3.0 * 100`

Each component scores 0-3. Weighted sum divided by max possible (3.0) yields percentage.

**Thresholds**:
- `>85%` = `healthy` — no action needed, report for record
- `60-85%` = `degraded` — report findings, recommend targeted fixes
- `<60%` = `critical` — urgent report, recommend immediate intervention

Include the numeric score in L1 output (`health_score: 87`) so Lead can track trends across runs.

---

## Scan Trigger Decision Heuristics

Different triggers warrant different scan scopes:

- **Post-pipeline trigger**: After delivery-pipeline completes, run full scan. Most common trigger. Full pipeline may have added/modified/deleted agents, skills, or hooks. Full scan catches drift introduced during the pipeline.
- **Post-modification trigger**: After execution-infra modifies `.claude/` files, run targeted scan on the modified component type only. Example: if a new hook was added, scan only hooks + settings.json for reference integrity. Avoids unnecessary full scans after minor changes.
- **Periodic (user-invoked)**: User explicitly requests health check via `/manage-infra`. Always full scan regardless of recent activity. User may suspect drift that automated triggers missed.
- **Post-RSI trigger**: After self-diagnose + self-implement cycle completes, run full scan. RSI modifies multiple component types simultaneously; full scan is mandatory. Cross-reference modified files from self-diagnose/self-implement output against detected changes.

**Decision heuristic for Lead**: If the trigger source provides a list of modified files, use targeted scan. If no file list is available or the trigger is periodic/post-RSI, use full scan.

---

## Cross-Component Drift Detection Patterns

Some drift findings span multiple component types. Detect and report as unified findings:

- **Settings → Hook drift**: `settings.json` references a hook command path that does not exist in `.claude/hooks/`. Affects both settings and hooks components. Single finding, both components marked degraded.
- **CLAUDE.md → Agent drift**: CLAUDE.md lists an agent name in Section 1 that has no corresponding file in `.claude/agents/`. Affects both CLAUDE.md accuracy and agent inventory.
- **Skill → Agent drift**: A skill description's DPS template references an agent name (via `subagent_type`) that does not exist in `.claude/agents/`. Affects both skills and agents components.
- **Skill → Skill drift**: A skill's `INPUT_FROM` or `OUTPUT_TO` references a skill name that has no corresponding directory in `.claude/skills/`. Internal skill graph broken.
- **Hook → Settings drift**: A hook file exists in `.claude/hooks/` but is not referenced by any event in `settings.json`. The hook is effectively dead code.

Report cross-component drift as: `"[CROSS] settings+hooks: settings.json references nonexistent hook .claude/hooks/missing.sh"`. The `[CROSS]` prefix helps Lead distinguish these from single-component findings.

---

## Failure Severity and Routing Matrix

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

Note: manage-infra is homeostasis — it never blocks the pipeline. CRITICAL findings need urgent user attention but do not halt any running pipeline.
