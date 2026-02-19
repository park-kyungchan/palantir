# Design Interface — Detailed Methodology

> On-demand reference. Contains interface contract template, naming conventions, data type registry, and DPS specifics.

## DPS for Analysts
- **Context**: Design-architecture L1 (components[]) + relevant L2 ADRs. Existing codebase patterns.
- **Task**: "Per boundary: function signatures, protocol, error contracts, versioning. Map to task contracts. Determine implementation order."
- **Scope**: COMPLEX → split by boundary cluster.
- **Constraints**: Read-only. Glob/Grep for patterns. maxTurns: 20.
- **Delivery**: Lead reads via TaskOutput (P0-P1).

## Interface Contract Template
```
Interface: {component_A} <-> {component_B}
Boundary: {connector}
Protocol: {direct_call | file_based | task_api | hook_based}

Component A provides:
  - Function/file: {name}
  - Output type: {concrete structure}
  - Output validation: {verification method}

Component B expects:
  - Input type: {concrete structure}
  - Required fields: {list}
  - Optional fields: {list}
  - Error handling: {on invalid input}

Error contract:
  - Error types: {names}
  - Propagation: {bubble | catch-and-translate | swallow}
  - Recovery: {retry | fallback | fail-fast}
```

## Naming Conventions
| Element | Convention | Example |
|---------|-----------|---------| 
| Interface | `{producer}-to-{consumer}` | `architecture-to-interface` |
| Data type | PascalCase | `ComponentStructure` |
| Error type | PascalCase + Error | `ContractViolationError` |
| File output | lowercase-hyphenated | `architecture-output.yaml` |

## Shared Data Type Registry
Define shared types ONCE, reference from all interfaces:
```
Type: ComponentSpec
Fields:
  - name: string (required, lowercase-hyphenated)
  - responsibility: string (required, single sentence)
  - dependencies: string[] (required, may be empty)
Used by: architecture-to-interface, architecture-to-risk
```

## Validation Rule Specification
Per field: type constraint (string/number/etc), value constraint (min/max/regex/enum), presence (required/optional/conditional), cross-field constraints.

## Failure Protocols
**Architecture insufficient**: Route to design-architecture with specific boundary questions.
**Circular interface deps**: Extract shared type into common registry. Document in ADR.
**Conflicting interfaces (COMPLEX)**: Lead reconciles, selects more complete spec.
**External API unknown**: Define from available docs, flag `validated: false`, route to research-external.
**Too many boundaries**: Prioritize critical-path. `status: partial`. Second pass.
