---
name: manage-infra
description: |
  [Homeostasis·Manager·Infra] INFRA-wide health monitor and self-repair system. Monitors entire .claude/ directory integrity — agents, skills, references, CLAUDE.md, settings, hooks. Detects configuration drift, stale references, and structural decay.

  WHEN: After any .claude/ infrastructure modification, after pipeline completion, or periodically for health check. AI can auto-invoke.
  DOMAIN: Homeostasis (cross-cutting, operates on entire .claude/ directory).

  SCOPE: Agents (.claude/agents/), Skills (.claude/skills/), Settings (.claude/settings.json), Hooks (.claude/hooks/), CLAUDE.md.
  METHODOLOGY: (1) Inventory all .claude/ files, (2) Check agent count matches CLAUDE.md tables, (3) Check settings.json schema validity, (4) Detect orphaned files (exist but unreferenced), (5) Propose cleanup actions.
  CLOSED_LOOP: Scan → Detect issues → Propose fixes → User approval → Apply → Re-scan → Done.
  OUTPUT_FORMAT: L1 YAML health report (component counts, orphan list, drift items), L2 markdown INFRA health narrative with repair recommendations.
user-invocable: true
disable-model-invocation: false
input_schema:
  type: object
  properties:
    scope:
      type: string
      enum: ["agents", "skills", "settings", "hooks", "all"]
      description: "INFRA scope to monitor (default: all)"
  required: []
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

### 4. Detect Configuration Drift
Check for inconsistencies:
- settings.json `permissions.allow` entries reference existing skills
- Hook scripts reference valid paths and tools
- CLAUDE.md version info matches actual state

### 5. Propose Repair Actions
For each detected issue:
- Classify severity: critical (broken reference) / warning (orphan) / info (drift)
- Propose specific fix action
- Await user approval before applying

## Quality Gate
- All component counts consistent between CLAUDE.md and filesystem
- Zero orphaned files
- Zero broken references
- settings.json and hooks valid

## Output

### L1
```yaml
domain: homeostasis
skill: manage-infra
status: healthy|degraded|critical
components:
  agents: {count: 0, orphans: 0}
  skills: {count: 0, orphans: 0}
  settings: {valid: true}
  hooks: {count: 0}
drift_items: 0
```

### L2
- Component inventory with counts
- Orphaned file detection
- Drift analysis and repair recommendations
