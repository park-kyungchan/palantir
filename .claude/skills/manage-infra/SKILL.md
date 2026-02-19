---
name: manage-infra
description: >-
  Monitors .claude/ directory integrity with weighted health
  scoring. Detects configuration drift, orphaned files, and
  cross-component inconsistencies. Use after .claude/
  modification, pipeline completion, or periodic health check.
  AI can auto-invoke. Reads from .claude/ directory including
  agents, skills, settings.json, hooks, and CLAUDE.md. Produces
  health report with scores, orphan count, drift count, and
  weighted health score percentage for self-diagnose category
  input and Lead repair routing. On FAIL (scan cannot complete),
  Lead applies L0 retry; 3+ failures escalate to L4.
  DPS needs CLAUDE.md declared counts and .claude/ filesystem
  paths. Exclude pipeline history and agent-memory data.
user-invocable: true
disable-model-invocation: true
---

# Manage — INFRA

## Current INFRA State
- Skills: !`ls .claude/skills/*/SKILL.md 2>/dev/null | wc -l` skill files
- Agents: !`ls .claude/agents/*.md 2>/dev/null | wc -l` agent files

## Execution Model
- **TRIVIAL**: Lead-direct. Quick health check on single component. No agent spawn.
- **STANDARD**: Spawn 1 analyst (maxTurns:20). Systematic inventory and drift detection.
- **COMPLEX**: Spawn 2 analysts (maxTurns:15 each). One for agents+skills, one for settings+hooks+CLAUDE.md.

## Phase-Aware Execution
Runs outside the linear pipeline (homeostasis). Team mode applies when called in P2+ context.
- Four-Channel Protocol: Ch2 (disk file) + Ch3 (micro-signal to Lead) + Ch4 (P2P to consumers).
- Write to `tasks/{team}/homeostasis-manage-infra.md`. Micro-signal: `{STATUS}|health:{score}|drift:{N}|ref:tasks/{team}/homeostasis-manage-infra.md`.
- For phase-aware routing details: read `.claude/resources/phase-aware-execution.md`

## Methodology

### 1. Inventory All Components
Scan entire `.claude/` directory:
- Count agents: `Glob .claude/agents/*.md`
- Count skills: `Glob .claude/skills/*/SKILL.md`
- Read settings: `.claude/settings.json` | List hooks: `Glob .claude/hooks/*`
- Read CLAUDE.md for declared counts

DPS context (D11): INCLUDE declared counts from CLAUDE.md, expected component layout, scan task.
EXCLUDE pipeline history, agent-memory runtime data, other homeostasis findings. Context ≤30% of analyst budget.

### 2. Check Count Consistency
Compare filesystem counts against CLAUDE.md declarations:
- Agent count in `§1 Team Identity` matches `.claude/agents/` file count
- Skill count matches `.claude/skills/` directory count
- Domain count matches unique domains across skill descriptions

### 3. Detect Orphaned Files
Find files that exist but are unreferenced (agents, skills without SKILL.md, unreferenced hooks).
Skip agent-memory directories — volatile runtime data, not INFRA components.
> For the full orphan detection algorithm: read `resources/methodology.md`

### 4. Detect Configuration Drift
Check settings.json validity, hook file references, and CLAUDE.md version consistency.
> For the settings.json validation checklist table: read `resources/methodology.md`

### 5. Propose Repair Actions
For each detected issue:
- Classify severity: critical (broken reference) / warning (orphan) / info (drift)
- Propose specific fix action with rationale
- Await user approval before applying any change

## Decision Points

### Scan Scope
- **Full scan** (default): All `.claude/` components — agents, skills, settings, hooks, CLAUDE.md. Use for periodic checks, post-pipeline, or when drift suspected.
- **Targeted scan**: Single component type only. Use when a specific modification just occurred.

### Orphan Handling
- **Report only** (default): List orphaned files with severity, await user approval. Preferred for safety.
- **Auto-propose cleanup script**: Generate removal commands for user review. Use when orphan count >5.

### Drift Classification Severity
- **Broken reference = critical**: settings.json entry references nonexistent file. Can cause runtime failures.
- **Count mismatch = warning**: CLAUDE.md declares wrong count. Functional but misleading.
- **Stale version info = info**: CLAUDE.md version string doesn't match recent changes. Cosmetic.

### Health Score
Weighted score across 5 components (Agents 20%, Skills 30%, Settings 20%, Hooks 15%, CLAUDE.md 15%).
Each component scores 0-3. Formula: `score = sum(weight * component_score) / 3.0 * 100`.
Thresholds: `>85%` = healthy | `60-85%` = degraded | `<60%` = critical.
> For the full calculation table with per-component scoring criteria: read `resources/methodology.md`

### Scan Triggers and Cross-Component Drift
> For scan trigger decision heuristics and cross-component drift detection patterns: read `resources/methodology.md`

## Failure Handling

### D12 Escalation Ladder

| Failure Type | Level | Action |
|---|---|---|
| File read error, tool timeout | L0 Retry | Re-invoke same analyst with same DPS |
| Analyst output missing component categories | L1 Nudge | SendMessage with refined scan scope |
| Analyst stuck or maxTurns exhausted | L2 Respawn | Kill → fresh analyst with refined DPS |
| Multiple component types unreadable | L3 Restructure | Split into targeted scans per component type |
| 3+ L2 failures or scan structurally blocked | L4 Escalate | AskUserQuestion with situation summary and options |

- **Unfixable issues**: Report with severity classification; never auto-fix without user approval
- **Scan cannot complete**: Report partial results with coverage percentage in L1
- **Pipeline impact**: Non-blocking (homeostasis is on-demand). Partial report is still actionable
- For the full failure severity routing matrix: read `resources/methodology.md`
- For escalation ladder details: read `.claude/resources/failure-escalation-ladder.md`

## Anti-Patterns

### DO NOT: Auto-Fix Without User Approval
Even "obvious" fixes should be reported and awaited. An orphaned file might be intentionally staged for a future pipeline. Always report, never auto-fix.

### DO NOT: Modify settings.json Structure
Reads and validates settings.json only — never restructures it. If drift detected, propose the minimal edit. Reformatting valid JSON can break ordering expectations.

### DO NOT: Ignore Hook Script Validation
Hooks are often overlooked. A broken hook (wrong path, missing shebang, bad exit code) can silently corrupt pipeline behavior. Always validate hook references match actual files.

### DO NOT: Trust CLAUDE.md Counts as Source of Truth
Filesystem is the source of truth. CLAUDE.md counts are derived documentation. If mismatch, update CLAUDE.md to match filesystem — not the reverse.

### DO NOT: Scan Agent-Memory as INFRA Components
Agent-memory directories are volatile runtime data. Including them produces false orphan alerts. Only scan declared component directories.

### DO NOT: Run Health Check During Active Pipeline
manage-infra reads files that execution-infra writes. Running during active pipeline produces false positives (mid-write state detected as drift). Wait for pipeline completion.

### DO NOT: Confuse Homeostasis with Verification
- **manage-infra**: Broad scan, all component types, detects drift over time (proactive)
- **verify-* skills**: Narrow scope, specific files just modified, validates conformance (reactive)

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| (self-triggered) | Health check request after .claude/ modification | No structured input — scans filesystem directly |
| delivery-pipeline | Post-delivery health check request | L1 YAML with pipeline completion status |
| self-implement | Post-RSI implementation results | L1 YAML with list of modified .claude/ files |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| (user) | Health report with repair recommendations | Always (terminal — report to user) |
| execution-infra | Repair task assignments | If user approves proposed repairs |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Scan cannot complete | (user) | Partial health report with coverage percentage |
| Critical broken references | (user) | Urgent report requiring immediate manual intervention |
| Unfixable structural issues | (user) | Findings with severity classification, no auto-fix |

> D17 Note: P2+ team mode — use 4-channel protocol (Ch1 PT, Ch2 tasks/{team}/, Ch3 micro-signal, Ch4 P2P).
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

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
health_score: 87          # percentage, see resources/methodology.md for calculation
pt_signal: "metadata.phase_signals.homeostasis"
signal_format: "{STATUS}|health:{score}|drift:{N}|ref:tasks/{team}/homeostasis-manage-infra.md"
trigger: post-pipeline|post-modification|periodic|post-rsi
components:
  agents: {count: 6, expected: 6, orphans: 0, score: 3}
  skills: {count: 40, expected: 40, orphans: 0, score: 3}
  settings: {valid: true, broken_refs: 0, score: 3}
  hooks: {count: 5, referenced: 5, score: 3}
  claude_md: {version: "v10.7", counts_match: true, score: 3}
drift_items: 0
cross_component_drift: 0
findings:
  - {component: skills, severity: WARNING, detail: "count mismatch: 41 vs 40"}
```

### L2
- Component inventory with counts and per-component health scores
- Orphaned file detection with classification (ORPHAN vs WARN vs INFO)
- Cross-component drift analysis with `[CROSS]` prefixed findings
- Settings.json validation checklist results
- Repair recommendations with severity classification and proposed fix actions
- Health score breakdown showing weight, raw score, and weighted contribution per component
