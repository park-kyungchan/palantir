---
name: research-codebase
description: |
  [P3·Research·Codebase] Local codebase exploration specialist. Discovers existing patterns, structures, conventions, and artifacts within the workspace using Glob, Grep, and Read tools. Read-only analysis with no file modifications.

  WHEN: design domain complete. Architecture decisions need validation against existing codebase patterns and conventions.
  DOMAIN: research (skill 1 of 3). Parallel-capable: codebase ∥ external → audit.
  INPUT_FROM: design domain (architecture decisions, interface designs needing codebase validation).
  OUTPUT_TO: research-audit (findings for inventory), plan-decomposition (codebase patterns for task planning).

  METHODOLOGY: (1) Identify codebase areas relevant to architecture decisions, (2) Glob to find files matching patterns, (3) Grep to search for conventions and existing implementations, (4) Read key files for detailed understanding, (5) Document patterns, anti-patterns, and reusable components found.
  MAX_TEAMMATES: 4. Each researcher explores non-overlapping codebase areas.
  OUTPUT_FORMAT: L1 YAML pattern inventory, L2 markdown findings with file:line references, L3 detailed code excerpts and analysis.
user-invocable: true
disable-model-invocation: false
input_schema:
  type: object
  properties:
    focus:
      type: string
      description: "Specific area or question to research in codebase"
  required: []
---

# Research — Codebase

## Output

### L1
```yaml
domain: research
skill: codebase
pattern_count: 0
file_count: 0
patterns:
  - name: ""
    files: []
    relevance: high|medium|low
```

### L2
- Pattern inventory with file:line references
- Convention analysis and reusable components
- Anti-patterns and technical debt noted
