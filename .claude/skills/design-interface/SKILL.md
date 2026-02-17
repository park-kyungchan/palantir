---
name: design-interface
description: >-
  Specifies inter-component API contracts and error boundaries.
  Defines function signatures, data types, protocols, and error
  propagation rules per boundary. Use after design-architecture
  produces component structure, parallel with design-risk. Reads
  from design-architecture component structure, module boundaries,
  and data flow. Produces interface registry with protocols and
  per-boundary specs for design-risk.
user-invocable: true
disable-model-invocation: false
---

# Design — Interface

## Execution Model
- **TRIVIAL**: Lead-direct. Simple interface listing between 2-3 components.
- **STANDARD**: Launch analyst (run_in_background). Formal interface specification per component boundary.
- **COMPLEX**: Launch 2-4 background agents (run_in_background). Each covers non-overlapping component boundaries.

## Decision Points

### Tier Assessment for Interface Design
- **TRIVIAL**: 2-3 components with 1-2 boundaries. Lead lists interfaces directly — no formal specification needed.
- **STANDARD**: 4-5 components with 3-5 boundaries. Launch 1 analyst for formal interface specification per boundary.
- **COMPLEX**: 6+ components with 6+ boundaries, shared data structures, external integrations. Launch 2-4 background analysts divided by boundary clusters.

### Interface Formality Level
Match formality to downstream consumption:
- **Informal** (TRIVIAL): "Component A produces file X, Component B reads it." Just names and paths.
- **Semi-formal** (STANDARD): Function signatures, data types, basic error handling. Enough for independent implementation.
- **Formal** (COMPLEX): Complete type definitions, validation rules, example payloads, error propagation chains, versioning strategy. Required when components will be implemented by different agents.

### Protocol Selection
For each boundary, choose communication protocol:
- **Direct call** (sync): Component A calls a function in Component B. Best for tightly coupled components in the same module.
- **File-based** (async): Component A writes output file, Component B reads it. Best for loosely coupled components, typical in pipeline patterns.
- **Task API** (async): Component A creates/updates a Task, Component B reads it. Best for cross-agent communication in Agent Teams.
- **Hook-based** (event): Component A triggers a hook event, Component B responds. Best for reactive patterns (e.g., file change detection).

Selection heuristic: For .claude/ INFRA, prefer file-based (SKILL.md, agents, settings) or hook-based (event-driven). For application code, prefer direct call.

### P0-P1 Execution Context
This skill runs in P0-P1:
- TRIVIAL/STANDARD: Lead with local agents (run_in_background), no Team infrastructure
- COMPLEX: Team infrastructure available (TeamCreate, TaskCreate/Update, SendMessage)
- Can run in parallel with design-risk (both depend on design-architecture output)

### Error Contract Depth Decision
How detailed should error contracts be?
- **Minimal** (TRIVIAL): "Errors are propagated to caller." No specific error types.
- **Standard** (STANDARD): Name specific error types per boundary. Define whether errors are recoverable or fatal.
- **Full** (COMPLEX): Error type hierarchy, propagation rules (bubble up vs catch-and-translate), recovery strategies per error type, fallback behaviors.

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

For STANDARD/COMPLEX tiers, construct the delegation prompt for each analyst with:
- **Context**: Paste design-architecture L1 (components[] with names, responsibilities, dependencies) and relevant L2 ADR sections. Include existing codebase patterns for interface conventions.
- **Task**: "For each component boundary: define function signatures (input→output), protocol (sync/async), error contracts (types, propagation), versioning approach. Map design interfaces to task contracts. Determine implementation ordering."
- **Scope**: For COMPLEX, split by component boundary set — non-overlapping assignments.
- **Constraints**: Read-only analyst. Use Glob/Grep for existing interface patterns. No file modifications. maxTurns: 20.
- **Expected Output**: L1 YAML with interface_count, contracts[] (boundary, protocol, error_contract). L2 per-boundary specs and implementation ordering.
- **Delivery**: Lead reads output directly via TaskOutput (P0-P1 local mode, no SendMessage).

#### Interface Contract Template
```
Interface: {component_A} <-> {component_B}
Boundary: {what connects them}
Protocol: {direct_call | file_based | task_api | hook_based}

Component A provides:
  - Function/file: {name and location}
  - Output type: {concrete data structure}
  - Output validation: {how to verify correctness}

Component B expects:
  - Input type: {concrete data structure}
  - Required fields: {list of must-have fields}
  - Optional fields: {list of may-have fields}
  - Error handling: {what B does if A's output is invalid}

Error contract:
  - Error types: {specific error names}
  - Propagation: {bubble | catch-and-translate | swallow}
  - Recovery: {retry | fallback | fail-fast}
```

#### Interface Naming Conventions
| Element | Convention | Example |
|---------|-----------|---------|
| Interface name | `{producer}-to-{consumer}` | `architecture-to-interface` |
| Data type name | PascalCase | `ComponentStructure`, `RiskMatrix` |
| Error type name | PascalCase + Error | `ContractViolationError`, `MissingFieldError` |
| File output | lowercase-hyphenated | `architecture-output.yaml` |

### 3. Specify Data Types
For shared data structures:
- Field names, types, constraints
- Required vs optional fields
- Validation rules
- Example values

#### Shared Data Type Registry
Central registry of data types used across multiple interfaces:
```
Type: ComponentSpec
Fields:
  - name: string (required, lowercase-hyphenated)
  - responsibility: string (required, single sentence)
  - dependencies: string[] (required, may be empty)
  - input_types: string[] (optional)
  - output_types: string[] (optional)
Used by: architecture-to-interface, architecture-to-risk, decomposition-to-interface
```

Shared types must be defined ONCE and referenced by all interfaces that use them. Avoid type duplication (same data structure with different names in different interfaces).

#### Validation Rule Specification
For each data type field, specify:
- **Type constraint**: string, number, boolean, array, object
- **Value constraint**: min/max, regex pattern, enum values
- **Presence constraint**: required, optional, conditional
- **Cross-field constraint**: "if field A is present, field B must also be present"

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

## Failure Handling

### Architecture Output Insufficient
- **Cause**: design-architecture didn't define component boundaries clearly enough for interface specification
- **Action**: Route back to design-architecture with specific questions about component interactions
- **Never guess**: at interfaces when component boundaries are unclear

### Circular Interface Dependencies
- **Cause**: Component A needs B's output type to define its input, but B needs A's output type similarly
- **Action**: Extract shared type into a common data type registry (defined independently of both components). Document in ADR.
- **Route**: If structural, route to design-architecture for component restructuring

### Analyst Produced Conflicting Interfaces
- **Cause**: COMPLEX tier analysts defined different interfaces for the same boundary
- **Action**: Lead reconciles by selecting the more complete specification. Flag inconsistency in L2.

### External Integration Interface Unknown
- **Cause**: Component interacts with external API whose interface isn't fully documented
- **Action**: Define interface based on available documentation. Flag as `validated: false`. Route to research-external for API documentation lookup.

### Too Many Boundaries for Analyst Turns
- **Cause**: COMPLEX architecture with 10+ boundaries
- **Action**: Prioritize critical-path boundaries. Set `status: partial` for unspecified boundaries. Second analyst pass for remaining.

## Anti-Patterns

### DO NOT: Define Interfaces Without Architecture
Interfaces must be derived from architecture component boundaries. Creating interfaces without established architecture produces interfaces that don't match actual component structures.

### DO NOT: Use Vague Types
"any", "object", "data" are not valid types. Every interface must use concrete, named types with specific fields. Vague types cause implementation-time interpretation differences.

### DO NOT: Ignore Error Contracts
The happy path is only half the interface. Error types, propagation rules, and recovery strategies are equally important. Missing error contracts cause silent failures during execution.

### DO NOT: Duplicate Shared Types
If two interfaces use the same data structure, define it once in the shared registry and reference it. Duplication leads to divergence when one copy is updated but not the other.

### DO NOT: Over-Specify Internal Interfaces
Interfaces between components in the SAME module that will be implemented by the SAME agent don't need full formal specification. Save formality for cross-agent boundaries.

### DO NOT: Design Interfaces for Future Extensions
Interfaces should be minimal and sufficient for current requirements. Adding "extension points" for hypothetical future needs adds complexity without value. Future extensions should trigger interface revision.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| design-architecture | Component structure with module boundaries | L1 YAML: `components[].{name, responsibility, dependencies[]}`, L2: ADRs |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| design-risk | Interface contracts for risk assessment | Always (interface → risk, or parallel) |
| research-codebase | Interface patterns for codebase validation | After design phase complete (P2 Wave 1) |
| research-external | API contracts for community validation | After design phase complete (P2 Wave 1) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Architecture insufficient | design-architecture | Specific questions about boundaries |
| Circular interfaces | design-architecture | Cycle details |
| External API unknown | research-external | API name + known information |
| Analyst incomplete | Self (second pass) | Remaining boundaries |

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
