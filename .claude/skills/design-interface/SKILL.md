---
name: design-interface
description: |
  [P2·Design·Interface] API contracts and integration point designer. Defines precise interfaces between components: function signatures, data types, protocols, and error contracts for all boundaries.

  WHEN: After design-architecture produces component structure. Components exist but interfaces undefined.
  DOMAIN: design (skill 2 of 3). Parallel with design-risk after architecture completes.
  INPUT_FROM: design-architecture (component structure, module boundaries).
  OUTPUT_TO: design-risk (interfaces for risk assessment), plan-interface (interface specs for planning).

  METHODOLOGY: (1) Read component structure from architecture, (2) For each boundary: define input/output types, (3) Define protocols (sync/async, message format), (4) Specify error contracts (types, propagation), (5) Document integration points with sequence diagrams.
  OUTPUT_FORMAT: L1 YAML interface registry with types, L2 markdown interface spec with examples, L3 type definitions and diagrams.
user-invocable: true
disable-model-invocation: false
---

# Design — Interface

## Execution Model
- **TRIVIAL**: Lead-direct. Simple interface listing between 2-3 components.
- **STANDARD**: Spawn analyst. Formal interface specification per component boundary.
- **COMPLEX**: Spawn 2-4 analysts. Each covers non-overlapping component boundaries.

## Methodology

### 1. Read Architecture Output
Load component structure from design-architecture.
List all component boundaries requiring interface definition.

### 2. Define Interface Contracts
For each component boundary:
- **Function signature**: Input types → output types
- **Protocol**: Sync (direct call) vs async (message/task)
- **Error contract**: Error types, propagation rules, recovery expectations
- **Versioning**: How the interface evolves without breaking consumers

### 3. Specify Data Types
For shared data structures:
- Field names, types, constraints
- Required vs optional fields
- Validation rules
- Example values

### 4. Map Integration Points
Identify where components interact with external systems:
- Task API (TaskCreate, TaskGet, etc.)
- File system (.claude/ directory structure)
- User interaction (AskUserQuestion)
- MCP tools (sequential-thinking, context7)

### 5. Document Dependency Order
Determine which components must be implemented first:
- Components with no dependencies → implement first
- Components depending on others → implement after dependencies
- Circular dependencies → refactor to break cycle

## Quality Gate
- Every component boundary has defined interface contract
- All shared data types fully specified
- No ambiguous or underspecified interfaces
- Dependency order is acyclic

## Output

### L1
```yaml
domain: design
skill: interface
interface_count: 0
data_type_count: 0
interfaces:
  - boundary: ""
    protocol: sync|async
    error_contract: defined|undefined
```

### L2
- Interface specifications per component boundary
- Shared data type definitions
- Dependency ordering with rationale
