---
name: design-architecture
description: |
  [P2·Design·Architecture] Component structure and module boundary designer. Produces component hierarchy, module boundaries, data flow, and technology choices as Architecture Decision Records.

  WHEN: pre-design domain complete (all 3 PASS). Feasibility-confirmed requirements ready.
  DOMAIN: design (skill 1 of 3). Parallel-capable: architecture || interface -> risk.
  INPUT_FROM: pre-design-feasibility (approved requirements + feasibility report), research-audit (if COMPLEX tier feedback loop).
  OUTPUT_TO: design-interface (for interface definition), design-risk (for risk assessment), research domain (for codebase validation).

  METHODOLOGY: (1) Read approved requirements, (2) Identify components (SRP), (3) Define module boundaries and data flow, (4) Select technology/patterns with rationale, (5) Document as ADRs.
  TIER_BEHAVIOR: TRIVIAL=Lead-only, STANDARD=analyst, COMPLEX=2-4 analysts.
  OUTPUT_FORMAT: L1 YAML component list, L2 markdown ADRs.
user-invocable: true
disable-model-invocation: false
---

# Design — Architecture

## Execution Model
- **TRIVIAL**: Lead-direct. Simple component identification, no formal ADR.
- **STANDARD**: Launch analyst (run_in_background). Formal component decomposition with ADRs.
- **COMPLEX**: Launch 2-4 background agents (run_in_background). Divide by module boundary or architectural concern.

## Methodology

### 1. Read Approved Requirements
Load feasibility-confirmed requirements from pre-design output.
Identify core capabilities, constraints, and integration points.

### 2. Identify Components (SRP)
For each capability, define a component with:
- Name (lowercase-hyphenated)
- Single responsibility description
- Input/output data types
- Dependencies on other components

### 3. Define Module Boundaries
Group related components into modules:
- Minimize cross-module dependencies
- Maximize intra-module cohesion
- Map to file system structure (.claude/agents/, .claude/skills/, etc.)

### 4. Make Technology/Pattern Choices
For each design decision, document as ADR:
- **Context**: What situation requires a decision?
- **Decision**: What was chosen?
- **Rationale**: Why this over alternatives?
- **Consequences**: What follows from this decision?

### 5. Document Data Flow
Map how data moves between components:
- Entry points (user input, skill invocation)
- Transformation steps
- Output destinations (files, Task API, user display)

## Quality Gate
- Every component has clear SRP
- No circular dependencies between modules
- Every design choice has documented ADR with rationale
- Data flow covers all input-to-output paths

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
