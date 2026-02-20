---
name: design-interface
description: >-
  Specifies inter-component API contracts and error boundaries.
  Defines function signatures, data types, protocols, and error
  propagation rules per boundary. Use after design-architecture
  produces component structure; design-risk runs after both
  design-architecture AND design-interface complete. Reads from
  design-architecture component structure, module boundaries, and
  data flow. Produces interface registry with protocols and
  per-boundary specs consumed by design-risk. Protocol options:
  direct call (sync), file-based (async pipeline), Task API
  (cross-agent), hook-based (event). For .claude/ INFRA prefer
  file-based or hook-based. TRIVIAL: Lead-direct, informal
  listing. STANDARD: 1 analyst (maxTurns: 20). COMPLEX: 2-4
  analysts by boundary cluster. Runs parallel with design-risk
  (both depend on design-architecture). On FAIL (incompatible
  interface requirements), routes back to design-architecture for
  boundary re-evaluation. DPS needs design-architecture component
  list and module boundaries. Exclude ADR rationale and rejected
  patterns.
user-invocable: true
disable-model-invocation: true
---

# Design — Interface

## Execution Model
- **TRIVIAL**: Lead-direct. Simple interface listing between 2-3 components.
- **STANDARD**: Launch analyst (run_in_background). Formal interface specification per component boundary.
- **COMPLEX**: Launch 2-4 background agents (run_in_background). Each covers non-overlapping component boundaries.

> Phase-aware routing and compaction survival: read `.claude/resources/phase-aware-execution.md`

## Decision Points

### Tier Assessment for Interface Design
- **TRIVIAL**: 2-3 components, 1-2 boundaries. Lead lists interfaces directly — no formal spec needed.
- **STANDARD**: 4-5 components, 3-5 boundaries. 1 analyst for formal specification per boundary.
- **COMPLEX**: 6+ components, 6+ boundaries, shared data structures, external integrations. 2-4 background analysts split by boundary cluster.

### Interface Formality Level
- **Informal** (TRIVIAL): Names and paths only.
- **Semi-formal** (STANDARD): Function signatures, data types, basic error handling. Enough for independent implementation.
- **Formal** (COMPLEX): Complete type definitions, validation rules, error propagation chains, versioning strategy. Required when components implemented by different agents.

### Protocol Selection
For each boundary, choose:
- **Direct call** (sync): tightly coupled components in the same module.
- **File-based** (async): loosely coupled components, pipeline patterns. Preferred for .claude/ INFRA.
- **Task API** (async): cross-agent communication in Agent Teams.
- **Hook-based** (event): reactive patterns (file change detection). Preferred for .claude/ INFRA.

### Error Contract Depth
- **Minimal** (TRIVIAL): "Errors propagated to caller." No specific types.
- **Standard** (STANDARD): Named error types per boundary. Recoverable vs fatal.
- **Full** (COMPLEX): Error hierarchy, propagation rules (bubble/catch-translate/swallow), recovery strategies, fallback behaviors.

## Methodology

### 1. Read Architecture Output
Load component structure from design-architecture. List all boundaries requiring interface definition.

### 2. Define Interface Contracts
For each boundary: function signature, protocol, error contract, versioning approach.
For STANDARD/COMPLEX, delegate to analysts.

> DPS construction guide: read `.claude/resources/dps-construction-guide.md`
> Contract template, naming conventions, and DPS details: read `resources/methodology.md`

### 3. Specify Data Types
Shared types: field names, types, constraints, required vs optional. Define ONCE in shared registry, reference everywhere.

> Data type registry format and validation spec: read `resources/methodology.md`

### 4. Map Integration Points
External interactions: Task API, file system (.claude/), AskUserQuestion, MCP tools.

### 5. Document Dependency Order
No-dependency components → implement first. Break circular dependencies by extracting shared types.

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Analyst tool error, timeout | L0 Retry | Re-invoke same analyst, same DPS |
| Incomplete or conflicting contracts | L1 Nudge | Respawn with refined DPS targeting corrected boundary context |
| Analyst exhausted turns (too many boundaries) | L2 Respawn | Kill → fresh analyst with reduced boundary set |
| Circular interface dependencies | L3 Restructure | Extract shared type, route to design-architecture for boundary revision |
| Architecture fundamentally insufficient | L4 Escalate | AskUserQuestion with specific boundary gap questions |

> Escalation ladder details: read `.claude/resources/failure-escalation-ladder.md`
> Failure edge cases and protocols: read `resources/methodology.md`

## Anti-Patterns

- **No architecture first**: Interfaces must derive from established component boundaries. Never guess interface structures.
- **Vague types**: "any", "object", "data" are invalid. Use concrete named types with specific fields.
- **Missing error contracts**: Happy path is half the interface. Error types and propagation rules are equally critical.
- **Duplicated shared types**: Define once in shared registry. Duplication causes divergence when one copy updates.
- **Over-specified internal interfaces**: Same-module, same-agent boundaries need informal listing only. Save formality for cross-agent boundaries.
- **Future extensions**: Minimal and sufficient for current requirements. Future needs → interface revision then.

## Transitions

### Receives From
| Source | Data | Format |
|--------|------|--------|
| design-architecture | Component structure, module boundaries | L1: `components[].{name, responsibility, dependencies[]}`, L2: ADRs |

### Sends To
| Target | Data | Trigger |
|--------|------|---------|
| design-risk | Interface contracts for risk assessment | Always (sequential or parallel) |
| research-codebase | Interface patterns for codebase validation | P2 Wave 1 |
| research-external | API contracts for community validation | P2 Wave 1 |

> D17 Note: P0-P1 local mode — Lead reads via TaskOutput. 2-channel protocol applies P2+ only.
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

## Quality Gate
- Every component boundary has a defined interface contract
- All shared data types fully specified (no vague types)
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
