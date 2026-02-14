---
name: design-architecture
description: |
  [P2·Design·Architecture] Component structure and module boundary designer. Produces architectural decisions including component hierarchy, module boundaries, data flow, and technology choices. Domain entry point for design phase.

  WHEN: pre-design domain complete (all 3 skills PASS). Feasibility-confirmed requirements ready for architecture.
  DOMAIN: design (skill 1 of 3). Parallel-capable: architecture ∥ interface → risk.
  INPUT_FROM: pre-design-feasibility (approved requirements with feasibility report).
  OUTPUT_TO: design-interface (architecture for interface definition), design-risk (architecture for risk assessment), research domain (architecture decisions needing codebase validation).

  METHODOLOGY: (1) Read approved requirements, (2) Identify components and responsibilities (SRP), (3) Define module boundaries and data flow, (4) Make technology/pattern choices with rationale, (5) Document as Architecture Decision Records.
  TIER_BEHAVIOR: TRIVIAL=Lead-only, STANDARD=analyst, COMPLEX=2-4 analysts.
  MAX_TEAMMATES: 4.
  OUTPUT_FORMAT: L1 YAML component list with relationships, L2 markdown ADRs with diagrams, L3 detailed component specs.
user-invocable: true
disable-model-invocation: true
---

# Design — Architecture

## Execution Model
- **TRIVIAL**: Lead-direct. Simple component identification, no formal ADR.
- **STANDARD**: Spawn analyst. Formal component decomposition with ADRs.
- **COMPLEX**: Spawn 2-4 analysts. Divide by module boundary or architectural concern.

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
