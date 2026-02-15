---
name: audit-impact
description: |
  [P2·Research·Impact] Traces change propagation paths: DIRECT vs TRANSITIVE.

  WHEN: After research-codebase AND research-external complete. Wave 2 parallel audit.
  DOMAIN: research (skill 6 of 7). Parallel: static ∥ behavioral ∥ relational ∥ impact.
  INPUT_FROM: research-codebase (file inventory), research-external (constraints), design-risk (risk matrix from P1).
  OUTPUT_TO: research-coordinator (impact analysis), execution-impact (P6 predicted paths via Shift-Left).

  METHODOLOGY: (1) Ingest Wave 1 findings + design-risk matrix, (2) Trace change propagation paths (DIRECT=1-hop, TRANSITIVE=2-3 hops), (3) Classify impact severity per path, (4) Assess maintenance/scalability risk, (5) Report propagation paths + risk assessment with file:line evidence.
  OUTPUT_FORMAT: L1 YAML impact summary, L2 markdown propagation analysis with risk assessment.
user-invocable: false
disable-model-invocation: false
---

# Audit — Impact (Change Propagation Analysis)

## Execution Model
- **STANDARD**: Spawn analyst (maxTurns:25). Trace propagation paths from design change points through the codebase.
- **COMPLEX**: Spawn 2 analysts. Analyst-1 traces DIRECT impacts. Analyst-2 traces TRANSITIVE impacts using Analyst-1's edge list. Sequential.

## Phase-Aware Execution
- **P2+ (active Team)**: Spawn agent with `team_name` parameter. Agent delivers via SendMessage.
- **Delivery**: Agent writes result to `/tmp/pipeline/p2-audit-impact.md`, sends micro-signal: `PASS|direct:{N}|transitive:{N}|ref:/tmp/pipeline/p2-audit-impact.md`.

## Shift-Left Pattern
This skill produces L3 output that is reused by execution-impact in P6. The predicted propagation paths from P2 become the baseline for P6's actual impact verification. This avoids redundant analysis: P2 predicts, P6 validates predictions against real changes.

The L3 output is stored at `/tmp/pipeline/p2-audit-impact.md` and passed to execution-impact via `$ARGUMENTS` in the plan phase.

## Methodology

### 1. Ingest Wave 1 Findings and Risk Matrix
Read research-codebase L1/L2 to extract:
- File inventory with roles and module boundaries
- Existing dependency patterns (import chains, config references)
- Component interaction patterns

Read research-external L2 for:
- Known constraints on change propagation (e.g., breaking change rules, semver implications)
- Community-reported cascading failure patterns

Read design-risk L1/L2 for:
- Risk matrix with identified risk items
- Architecture decisions ranked by risk level
- Change scope boundaries defined by the design phase

### 2. Trace Change Propagation Paths
Starting from each design change point (component being added/modified/removed):

**DIRECT Impact** (1 hop):
- Files that directly import or reference the changed component
- Configuration files that directly configure the changed component
- Test files that directly test the changed component
- Record: `changed_file -> affected_file` with reference type and file:line

**TRANSITIVE Impact** (2+ hops):
- Files that depend on directly affected files (second-order effects)
- Follow chains up to 3 hops maximum (beyond 3 hops, impact is speculative)
- Record: `changed_file -> hop1 -> hop2 [-> hop3]` with chain evidence

For each path, document:
- Change origin (which design decision triggers this path)
- Each hop with file:line evidence of the dependency
- Terminal node (the final affected file in the chain)

### 3. Classify Impact Severity
For each propagation path:

| Severity | Criteria | Example |
|----------|---------|---------|
| CRITICAL | Change breaks existing interface contract, no backward compatibility | Removing a function that 5+ files call |
| HIGH | Change requires modifications in dependent files, significant rework | Changing a function signature used by 3+ callers |
| MEDIUM | Change requires minor updates in dependents, backward-compatible approach exists | Adding optional parameter to existing function |
| LOW | Change is self-contained, dependents unaffected | Internal refactor with stable public interface |

Severity escalators:
- Path crosses module boundaries: +1 severity level
- No test coverage for affected files: +1 severity level
- Multiple design decisions converge on the same propagation path: +1 severity level

### 4. Assess Maintenance and Scalability Risk
Beyond immediate change impact, assess long-term risks:

**Maintenance Risk**:
- Does this change increase coupling? (more edges in dependency graph)
- Does it create new single points of failure? (new hotspot nodes)
- Does it increase the blast radius of future changes?

**Scalability Risk**:
- Will this change pattern work if the codebase grows 2x? 5x?
- Are the propagation paths manageable at scale?
- Does the architecture decision create linear or exponential dependency growth?

Rate each risk dimension as HIGH/MEDIUM/LOW with justification.

### 5. Report Propagation Paths and Risk Assessment
Produce final output with:
- Propagation path table: origin, path (hops), terminal, severity, evidence
- DIRECT vs TRANSITIVE summary: counts and severity distribution
- Risk matrix: per-design-decision impact severity across all propagation paths
- Maintenance risk assessment per affected module
- Scalability risk assessment per architecture decision
- Shift-Left handoff: structured propagation data for execution-impact (P6)

## Failure Handling

### No Propagation Paths Found
- **Cause**: Design changes are entirely self-contained with no external dependencies
- **Action**: Report `direct: 0, transitive: 0`. This is valid for isolated additions.
- **Route**: research-coordinator with empty impact set

### Design-Risk Input Missing
- **Cause**: P1 design-risk did not produce risk matrix (TRIVIAL/STANDARD tier may skip P1 risk)
- **Action**: Proceed without risk matrix. Use design-architecture component scope as fallback for change points.
- **Route**: Continue normally. Note reduced confidence in risk assessment.

### Propagation Chain Too Deep
- **Cause**: Transitive chains exceed 3 hops, analysis becomes speculative
- **Action**: Cap at 3 hops. Report deeper chains as "potential deep impact" without tracing further.
- **Route**: research-coordinator with depth cap noted

## Anti-Patterns

### DO NOT: Trace Beyond 3 Hops
Transitive impact beyond 3 hops is speculative. Cap analysis at 3 hops and note potential deep impacts without tracing further. Deep chain analysis is diminishing returns.

### DO NOT: Recommend Mitigations
Impact audit describes what will be affected and how severely. It does not prescribe how to mitigate the impact. Mitigation strategies belong to plan-strategy. Keep findings descriptive.

### DO NOT: Confuse Impact with Dependency
audit-static maps structural dependencies (what references what). audit-impact traces change propagation (if X changes, what breaks). A dependency exists even when nothing changes. Impact analysis is change-triggered.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| research-codebase | File inventory, dependency patterns | L1 YAML: pattern inventory, L2: file:line findings |
| research-external | Change propagation constraints | L2: breaking change rules, cascading patterns |
| design-risk | Risk matrix from P1 | L1 YAML: risk items, L2: risk analysis (optional for STANDARD) |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| research-coordinator | Impact analysis for consolidation | Always (Wave 2 -> Wave 2.5) |
| execution-impact | Predicted propagation paths (Shift-Left) | Always (P2 -> P6 via $ARGUMENTS in plan) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| No propagation paths | research-coordinator | Empty impact set with explanation |
| Analyst exhausted | research-coordinator | Partial paths + coverage percentage |
| Design-risk missing | Continue (degraded) | Reduced confidence flag in output |

## Quality Gate
- Every propagation path has file:line evidence for each hop
- DIRECT vs TRANSITIVE classification applied to all paths
- Severity classification applied with criteria documented
- Maintenance and scalability risk assessed per affected module
- No paths traced beyond 3 hops (cap enforced)
- Shift-Left output structured for execution-impact consumption
- No prescriptive recommendations (descriptive findings only)

## Output

### L1
```yaml
domain: research
skill: audit-impact
direct_count: 0
transitive_count: 0
critical_paths: 0
high_paths: 0
medium_paths: 0
low_paths: 0
maintenance_risk: HIGH|MEDIUM|LOW
scalability_risk: HIGH|MEDIUM|LOW
propagation:
  - origin: ""
    type: DIRECT|TRANSITIVE
    hops: 1
    severity: CRITICAL|HIGH|MEDIUM|LOW
    terminal: ""
```

### L2
- Propagation path table with full hop chains and evidence
- DIRECT impact inventory with severity per path
- TRANSITIVE impact inventory (2-3 hops) with chain evidence
- Risk matrix: per-design-decision severity across all paths
- Maintenance risk narrative per affected module
- Scalability risk narrative per architecture decision
- Shift-Left handoff section: structured data for execution-impact (P6)
