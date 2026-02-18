---
name: design-architecture
description: >-
  Structures component hierarchy with module boundaries and
  Architecture Decision Records. Decomposes requirements into
  SRP components, defines data flow, and selects technology
  patterns. Use after pre-design domain complete with all three
  skills PASS and feasibility-confirmed requirements ready. Reads
  from pre-design-feasibility approved requirements and CC
  capability mappings, plus research-coordinator feedback in
  COMPLEX tier. Produces component list with dependencies and
  ADRs for design-interface and design-risk. TRIVIAL: Lead-direct,
  no formal ADR. STANDARD: 1 analyst (maxTurns: 20). COMPLEX:
  2-4 analysts by module boundary. On FAIL (conflicting
  requirements or infeasible architecture), routes back to
  pre-design-brainstorm for scope renegotiation. DPS needs
  feasibility-confirmed requirements only. Exclude rejected
  alternatives and raw user conversation.
user-invocable: true
disable-model-invocation: false
---

# Design — Architecture

## Execution Model
- **TRIVIAL**: Lead-direct. Simple component list, no formal ADR.
- **STANDARD**: 1 analyst (run_in_background, maxTurns: 20). Formal decomposition with ADRs.
- **COMPLEX**: 2-4 analysts (run_in_background). Divide by module boundary.

## Decision Points

### Tier Assessment
- **TRIVIAL**: 1-2 components, single module, no cross-module data flow
- **STANDARD**: 3-5 components, 1-2 modules, manageable data flow
- **COMPLEX**: 6+ components, 3+ modules, complex integration points

### Architecture Granularity
- **Too coarse** (1 component = system): No boundaries, can't parallelize
- **Too fine** (1 component = function): Over-engineering
- **Right**: Each component = single responsibility requiring 2-8 files
- **Heuristic**: One-sentence description = right-sized. Paragraph = split. Phrase = merge.

### Feedback Loop (COMPLEX only)
- **Default**: No feedback. Architecture → design-interface.
- **With feedback**: Route to research-codebase for pattern validation. Max 1 iteration.
- **When**: Requirements reference unexplored codebase patterns OR analyst flags uncertainty.

### Technology Choice
- Prefer existing patterns over new ones
- New patterns require ADR with explicit rationale
- .claude/ INFRA: prefer CC native features over custom implementations

### P0-P1 Context
TRIVIAL/STANDARD: local agents (run_in_background). COMPLEX: Team infra available.

## Methodology
For detailed DPS, component checklist, ADR standards, and INFRA patterns: Read `resources/methodology.md`

Summary:
1. **Read** feasibility-confirmed requirements
2. **Identify** SRP components (name, responsibility, I/O, dependencies)
3. **Define** module boundaries (minimize cross-module coupling)
4. **Document** technology/pattern choices as ADRs (Context, Decision, Rationale, Consequences)
5. **Map** data flow (entry → transformation → output)

## Failure Handling
For D12 escalation ladder: Read `~/.claude/resources/failure-escalation-ladder.md`

| Failure | Level | Action |
|---------|-------|--------|
| Analyst error | L0 | Retry |
| Incomplete components | L1 | Nudge with scope |
| Analyst exhausted | L2 | Fresh analyst, narrower scope |
| Circular dependencies | L3 | Extract shared dependency |
| Requirements too vague | L4 | AskUserQuestion or return to brainstorm |

## Anti-Patterns

### DO NOT: Skip ADRs for "obvious" decisions
Every choice needs documented rationale. Prevents "why did we do this?" downstream.

### DO NOT: Design without reading existing code
Build on existing patterns. Vacuum design creates integration failures.

### DO NOT: Create components <2 files
Over-decomposed. Merge with related components.

### DO NOT: Introduce patterns without ADR
Undocumented = unreviewable.

### DO NOT: Design for future requirements
Current requirements only. Future needs trigger future revisions.

## Transitions

### Receives From
| Source | Data |
|--------|------|
| pre-design-feasibility | Approved requirements + CC capability mappings |
| research-audit | Codebase validation (COMPLEX feedback loop) |

### Sends To
| Target | Condition |
|--------|-----------|
| design-interface | Always |
| design-risk | Always (parallel with interface) |
| research-codebase | COMPLEX feedback loop only |

## Quality Gate
- Every component has clear SRP
- No circular dependencies
- Every design choice has ADR with rationale
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
- ADRs with rationale
- Component hierarchy and data flow
- Technology choices with justification
