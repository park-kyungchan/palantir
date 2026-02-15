---
name: design-architecture
description: |
  [P1·Design·Architecture] Component structure and module boundary designer. Produces component hierarchy, module boundaries, data flow, and technology choices as Architecture Decision Records.

  WHEN: pre-design domain complete (all 3 PASS). Feasibility-confirmed requirements ready.
  DOMAIN: design (skill 1 of 3). Parallel-capable: architecture || interface -> risk.
  INPUT_FROM: pre-design-feasibility (approved requirements + feasibility report), research-audit (if COMPLEX tier feedback loop).
  OUTPUT_TO: design-interface (for interface definition), design-risk (for risk assessment), research-codebase (for codebase validation).

  METHODOLOGY: (1) Read approved requirements, (2) Identify components (SRP), (3) Define module boundaries and data flow, (4) Select technology/patterns with rationale, (5) Document as ADRs.
  OUTPUT_FORMAT: L1 YAML component list, L2 markdown ADRs.
user-invocable: true
disable-model-invocation: false
---

# Design — Architecture

## Execution Model
- **TRIVIAL**: Lead-direct. Simple component identification, no formal ADR.
- **STANDARD**: Launch analyst (run_in_background). Formal component decomposition with ADRs.
- **COMPLEX**: Launch 2-4 background agents (run_in_background). Divide by module boundary or architectural concern.

## Decision Points

### Tier Assessment for Architecture Design
- **TRIVIAL**: 1-2 components, single module, no cross-module data flow. Lead defines architecture directly as a brief component list.
- **STANDARD**: 3-5 components, 1-2 modules, manageable data flow. Launch 1 analyst for formal ADR creation.
- **COMPLEX**: 6+ components, 3+ modules, complex data flow with multiple integration points. Launch 2-4 background analysts divided by module or architectural concern.

### Architecture Granularity Decision
How fine-grained should component decomposition be?
- **Too coarse** (1 component = entire system): No clear boundaries, impossible to parallelize implementation, monolithic failure mode
- **Too fine** (1 component = 1 function): Excessive interface overhead, over-engineering, implementation complexity explosion
- **Right granularity**: Each component has a single responsibility that requires 2-8 files to implement

Heuristic: If a component's responsibility can be described in one sentence, it's right-sized. If it needs a paragraph, split it. If it needs only a phrase, merge it with a related component.

### P0-P1 Phase Execution Context
This skill runs in the P0-P1 (PRE-DESIGN + DESIGN) phase:
- **Lead with local agents only** — no Team infrastructure (TeamCreate/SendMessage)
- Use `run_in_background: true` for analyst spawns
- Communication is one-way: Lead reads agent output, no back-and-forth messaging
- Multiple analysts run as independent background tasks, not as coordinated teammates

### Feedback Loop Decision (COMPLEX Only)
For COMPLEX tier, architecture may need validation against existing codebase:
- **No feedback loop** (default): Architecture based on requirements + feasibility only. Proceed to design-interface.
- **With feedback loop**: Route architecture to research-codebase for pattern validation. Research findings may trigger architecture revision.
- **When to use feedback loop**: When requirements reference existing codebase patterns that weren't fully explored in pre-design phase, OR when analyst flags uncertainty about existing code structure.
- **Max 1 feedback iteration**: Architecture -> research -> revised architecture. More iterations indicate requirements need re-examination.

### Technology Choice Strategy
- **Prefer existing patterns**: If codebase already uses a technology/pattern for similar purposes, prefer it unless there's a compelling reason to change
- **Justify new patterns**: Every new technology choice requires an ADR with explicit rationale for why existing patterns are insufficient
- **CC native preference**: For .claude/ INFRA changes, always prefer CC native features over custom implementations (per CC reference cache)

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

For STANDARD/COMPLEX tiers, construct the delegation prompt for each analyst with:
- **Context**: Paste pre-design-feasibility L1 (requirements + feasibility verdicts) and L2 (CC capability findings). If COMPLEX tier feedback from research-audit, include its L1 coverage matrix. Include workspace hint: "Target: /home/palantir, .claude/ for INFRA."
- **Task**: "Decompose requirements into components (SRP). Per component: lowercase-hyphenated name, single-responsibility description, input/output types, dependencies. Group into modules minimizing coupling. Per decision: ADR (Context, Decision, Rationale, Consequences)."
- **Scope**: For COMPLEX, split by module boundary — non-overlapping analyst assignments.
- **Constraints**: Read-only. Use Glob/Grep/Read for existing pattern reference. No file modifications.
- **Expected Output**: L1 YAML with component_count, decision_count, components[] (name, responsibility, dependencies). L2 ADRs and component hierarchy.

#### Component Definition Quality Checklist
For each component, verify:
- [ ] Name follows lowercase-hyphenated convention
- [ ] Responsibility is a single sentence (SRP)
- [ ] Input/output types are concrete (not "data" but "JSON with fields X, Y")
- [ ] Dependencies list is complete (no hidden dependencies)
- [ ] Component maps to 2-8 implementation files
- [ ] No circular dependencies with other components

#### Common Component Patterns for .claude/ INFRA
| Pattern | Components | Example |
|---------|-----------|---------|
| New skill | SKILL.md + possibly new agent | Adding execution-impact skill |
| Agent modification | Agent .md + settings.json | Changing agent model/memory |
| Hook system | Hook .sh + settings.json + possibly CLAUDE.md | Adding file change tracking |
| Pipeline change | Multiple SKILL.md descriptions + CLAUDE.md | Reordering pipeline phases |
| Cross-cutting | Multiple skills + agents + settings | SRC system (hooks + skills + agents) |

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

#### ADR Quality Standards
Each Architecture Decision Record must include:
- **Title**: Concise decision summary (e.g., "ADR-1: Use analyst for impact analysis instead of implementer")
- **Status**: Proposed | Accepted | Deprecated
- **Context**: What problem or requirement drove this decision? Include constraints.
- **Decision**: What was chosen? Be specific (tool/pattern/approach name).
- **Rationale**: Why this over alternatives? List at least 2 alternatives considered.
- **Consequences**: What follows from this decision? Include both positive and negative consequences.
- **Dependencies**: What other ADRs does this depend on or affect?

#### Anti-Pattern ADR Examples
Bad: "ADR: Use a good architecture" (too vague)
Bad: "ADR: Use React" (no rationale or alternatives)
Good: "ADR-3: Use hook-based file tracking instead of polling. Context: Need to detect file changes during pipeline. Decision: PostToolUse hook logs file changes. Rationale: Hooks are real-time, polling misses changes between intervals. Consequences: Hook overhead on every tool call, but latency is negligible (<10ms)."

### 5. Document Data Flow
Map how data moves between components:
- Entry points (user input, skill invocation)
- Transformation steps
- Output destinations (files, Task API, user display)

## Failure Handling

### Requirements Too Vague for Architecture
- **Cause**: Pre-design output lacks specificity for component identification
- **Action**: Route back to pre-design-validate with specific questions (e.g., "Is feature X synchronous or asynchronous?")
- **Never proceed**: with vague requirements — architecture built on assumptions creates cascading failures

### Analyst Produced Inconsistent Components
- **Cause**: COMPLEX tier analysts working on different modules produced conflicting data flow assumptions
- **Action**: Lead reconciles by comparing data flow diagrams. If irreconcilable: merge conflicting modules under one analyst for unified design.
- **Report in L2**: Reconciliation decisions and their rationale

### Circular Dependencies in Component Graph
- **Cause**: Component A depends on B which depends on A
- **Action**: Break cycle by extracting shared dependency into a new component (dependency inversion). Document in ADR.
- **Check**: Run dependency cycle detection on final component graph

### No Existing Patterns Match Requirements
- **Cause**: Requirements are novel for this codebase
- **Action**: Document as ADR with "greenfield" rationale. Include research recommendations for design-interface to validate approach.
- **Route**: To research-external for pattern validation if the approach involves external libraries/APIs

### Analyst Background Task Failed
- **Cause**: Background analyst exhausted turns or encountered error
- **Action**: Read partial output. If >50% of components defined: complete remaining with Lead-direct. If <50%: re-spawn with narrower scope.

## Anti-Patterns

### DO NOT: Skip ADRs for "Obvious" Decisions
Every technology and pattern choice needs documented rationale, even if it seems obvious. What's obvious now may be questioned during execution-review. ADRs prevent "why did we do this?" questions downstream.

### DO NOT: Design Without Reading Existing Code
If the codebase has existing patterns (discoverable via research-codebase), architecture should build on them. Designing in a vacuum creates integration failures.

### DO NOT: Create Components Smaller Than 2 Files
Components that map to a single file are over-decomposed. They create interface overhead without parallelization benefit. Merge with related components.

### DO NOT: Introduce New Patterns Without ADR
Using a new pattern (new hook type, new agent role, new skill domain) without an ADR means the decision is undocumented and unreviewable. Every novel pattern needs formal justification.

### DO NOT: Design Architecture for Future Requirements
Design for current requirements only. Over-engineering for hypothetical future needs adds complexity without immediate value. Future requirements should trigger future architecture revisions.

### DO NOT: Ignore P0-P1 Execution Context
This skill runs in P0-P1 (Lead with local agents, no Team infrastructure). Don't design communication patterns that require TeamCreate/SendMessage — those are only available in P2+.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| pre-design-feasibility | Approved requirements + feasibility report | L1 YAML: `requirements_met`, `feasibility_verdict`, L2: CC capability findings |
| research-audit | Codebase validation findings (COMPLEX feedback loop) | L1 YAML: `coverage_matrix`, L2: pattern matches and gaps |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| design-interface | Component structure with module boundaries | Always (architecture -> interface) |
| design-risk | Component structure for risk assessment | Always (architecture -> risk, parallel with interface) |
| research-codebase | Architecture decisions needing codebase validation | COMPLEX tier feedback loop only |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Requirements too vague | pre-design-validate | Specific questions needing answers |
| Analyst failed/partial | Self (re-spawn narrower scope) | Completed components + remaining scope |
| Circular dependencies | Self (restructure) | Cycle details |
| Novel pattern detected | research-external | Pattern details for validation |

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
