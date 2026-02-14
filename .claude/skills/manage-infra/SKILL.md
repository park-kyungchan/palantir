---
name: manage-infra
description: |
  [Homeostasis·Manager·Infra] INFRA-wide health monitor and self-repair system. Monitors entire .claude/ directory integrity — agents, skills, references, CLAUDE.md, settings, hooks. Detects configuration drift, stale references, and structural decay.

  WHEN: After any .claude/ infrastructure modification, after pipeline completion, or periodically for health check. AI can auto-invoke.
  DOMAIN: Homeostasis (cross-cutting, operates on entire .claude/ directory).

  SCOPE: Agents (.claude/agents/), Skills (.claude/skills/), References (.claude/references/), Settings (.claude/settings.json), Hooks (.claude/hooks/), CLAUDE.md.
  METHODOLOGY: (1) Inventory all .claude/ files, (2) Check agent count matches CLAUDE.md tables, (3) Verify reference files are referenced by agents/skills, (4) Check settings.json schema validity, (5) Detect orphaned files (exist but unreferenced), (6) Propose cleanup actions.
  CLOSED_LOOP: Scan → Detect issues → Propose fixes → User approval → Apply → Re-scan → Done.
  OUTPUT_FORMAT: L1 YAML health report (component counts, orphan list, drift items), L2 markdown INFRA health narrative with repair recommendations.
user-invocable: true
disable-model-invocation: false
input_schema:
  type: object
  properties:
    scope:
      type: string
      enum: ["agents", "skills", "references", "settings", "hooks", "all"]
      description: "INFRA scope to monitor (default: all)"
  required: []
---

# Manage — INFRA

## Output

### L1
```yaml
domain: homeostasis
skill: manage-infra
status: healthy|degraded|critical
components:
  agents: {count: 0, orphans: 0}
  skills: {count: 0, orphans: 0}
  references: {count: 0, orphans: 0}
  settings: {valid: true}
  hooks: {count: 0}
drift_items: 0
```

### L2
- Component inventory with counts
- Orphaned file detection
- Drift analysis and repair recommendations
