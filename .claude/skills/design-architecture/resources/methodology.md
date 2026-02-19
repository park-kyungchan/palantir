# Design Architecture — Detailed Methodology

> On-demand reference. Contains DPS specifics, component patterns, ADR standards, and quality checklist.

## DPS for Analysts
- **Context**: Pre-design-feasibility L1 (requirements + verdicts) and L2 (CC capability findings). COMPLEX: research-audit L1 coverage matrix. Workspace: `/home/palantir`, `.claude/` for INFRA.
- **Task**: "Decompose requirements into SRP components. Per component: lowercase-hyphenated name, single-responsibility, input/output types, dependencies. Group into modules minimizing coupling. Per decision: ADR."
- **Scope**: COMPLEX → split by module boundary, non-overlapping.
- **Constraints**: Read-only. Glob/Grep/Read for existing patterns. maxTurns: 20.
- **Delivery**: Lead reads via TaskOutput (P0-P1).

## Component Definition Checklist
- [ ] Name: lowercase-hyphenated
- [ ] Responsibility: single sentence (SRP)
- [ ] Input/output: concrete types (not "data")
- [ ] Dependencies: complete list
- [ ] Maps to 2-8 implementation files
- [ ] No circular dependencies

## Common .claude/ INFRA Component Patterns
| Pattern | Components | Example |
|---------|-----------|---------| 
| New skill | SKILL.md + possibly new agent | Adding execution-impact |
| Agent modification | Agent .md + settings.json | Changing agent model/memory |
| Hook system | Hook .sh + settings.json + CLAUDE.md | File change tracking |
| Pipeline change | Multiple SKILL.md + CLAUDE.md | Reordering phases |
| Cross-cutting | Skills + agents + settings | SRC system |

## ADR Quality Standards
Each ADR must include:
- **Title**: Concise decision summary (e.g., "ADR-1: Use analyst for impact analysis")
- **Status**: Proposed | Accepted | Deprecated
- **Context**: Problem/requirement driving the decision, including constraints
- **Decision**: Specific tool/pattern/approach chosen
- **Rationale**: Why over alternatives (list ≥2 alternatives considered)
- **Consequences**: Both positive and negative
- **Dependencies**: Related ADRs

### ADR Examples
Bad: "Use a good architecture" (vague), "Use React" (no rationale)
Good: "ADR-3: Use hook-based file tracking. Context: Need file change detection. Decision: PostToolUse hook logs changes. Rationale: Real-time vs polling missing intervals. Consequences: Hook overhead but <10ms."

## Failure Protocols (Detail)
**Requirements too vague**: Route to validate with specific questions. Never architect on assumptions.
**Inconsistent components (COMPLEX)**: Lead reconciles data flow. If irreconcilable: merge modules under one analyst.
**Circular dependencies**: Extract shared dependency (dependency inversion). Document in ADR.
**Novel pattern**: Document as ADR with "greenfield" rationale. Route to research-external if external libs involved.
**Analyst failed**: Read partial. >50% done → Lead completes. <50% → re-spawn narrower.
