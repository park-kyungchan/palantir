---
name: design-architecture
description: |
  [P2·Design·Architecture] Component structure and module boundary designer. Produces architectural decisions including component hierarchy, module boundaries, data flow, and technology choices. Domain entry point for design phase.

  WHEN: pre-design domain complete (all 3 skills PASS). Feasibility-confirmed requirements ready for architecture.
  DOMAIN: design (skill 1 of 3). Parallel-capable: architecture ∥ interface → risk.
  INPUT_FROM: pre-design-feasibility (approved requirements with feasibility report).
  OUTPUT_TO: design-interface (architecture for interface definition), design-risk (architecture for risk assessment), research domain (architecture decisions needing codebase validation).

  METHODOLOGY: (1) Read approved requirements, (2) Identify components and responsibilities (SRP), (3) Define module boundaries and data flow, (4) Make technology/pattern choices with rationale, (5) Document as Architecture Decision Records.
  TIER_BEHAVIOR: TRIVIAL=Lead-only, STANDARD=architect agent, COMPLEX=architecture-coordinator+3.
  MAX_TEAMMATES: 4.
  OUTPUT_FORMAT: L1 YAML component list with relationships, L2 markdown ADRs with diagrams, L3 detailed component specs.
user-invocable: true
disable-model-invocation: true
---

# Design — Architecture

## Output

### L1
```yaml
domain: design
skill: architecture
component_count: 0
decision_count: 0
components:
  - name: ""
    responsibility: ""
    dependencies: []
```

### L2
- Architecture Decision Records (ADRs) with rationale
- Component hierarchy and data flow
- Technology choices with justification
