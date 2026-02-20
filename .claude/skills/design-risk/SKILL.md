---
name: design-risk
description: >-
  Assesses failure modes and security risks per component using
  FMEA with calibrated RPN, OWASP checks, CC boundary risks,
  and performance bottleneck analysis. Terminal design skill.
  Use after design-architecture and design-interface complete.
  Reads from design-architecture component structure and ADRs,
  plus design-interface API and error contracts. Produces risk
  matrix with mitigations and risk narrative for research-codebase
  and research-external. RPN thresholds: >=50 critical (mandatory
  mitigation), 25-49 high, 10-24 medium, <10 low. TRIVIAL:
  Lead-direct, 2-3 risks. STANDARD: 1 analyst FMEA (maxTurns:
  20). COMPLEX: 2-4 analysts split security/performance/
  reliability. Runs parallel with design-interface. On FAIL
  (unmitigable risk discovered), routes to Lead for D12 L4
  escalation to user. DPS needs design-architecture ADRs and
  design-interface contracts. Exclude raw feasibility data.
user-invocable: true
disable-model-invocation: true
---

# Design — Risk

## Execution Model
- **TRIVIAL**: Lead-direct. Quick risk scan, 2-3 top risks identified.
- **STANDARD**: Launch analyst (run_in_background). Systematic FMEA per component.
- **COMPLEX**: Launch 2-4 background agents (run_in_background). Divide: security vs performance vs reliability.

> Phase-aware routing and compaction survival: read `.claude/resources/phase-aware-execution.md`

## Decision Points

### Tier Assessment for Risk Analysis
- **TRIVIAL**: 1-2 components, no external dependencies. Lead identifies top 2-3 risks directly. No analyst spawn.
- **STANDARD**: 3-5 components, moderate complexity. 1 analyst for systematic FMEA with calibrated RPN scoring.
- **COMPLEX**: 6+ components, external integrations, security-sensitive operations. 2-4 analysts: failure modes vs security vs performance.

### Risk Analysis Depth
- **Quick scan** (TRIVIAL): Intuition-based, no formal FMEA. Suitable for straightforward architectures.
- **Standard FMEA** (STANDARD): Full FMEA table per component. Calibrated RPN. Cover failure modes, security, performance.
- **Deep analysis** (COMPLEX): FMEA + OWASP + performance modeling + propagation analysis. Dedicated analyst per concern.

### RPN Threshold for Mitigation
- **RPN ≥ 50**: Critical — mandatory mitigation, checkpoint in execution plan
- **RPN 25-49**: High — mitigation recommended, documented in plan-behavioral
- **RPN 10-24**: Medium — acknowledged, monitored during execution
- **RPN < 10**: Low — documented for awareness only

> FMEA calibration tables (S/L/D scoring): read `resources/methodology.md`

### When to Escalate to Architecture Revision
- Single component RPN ≥ 100
- 3+ components share the same high-RPN failure mode
- Security finding affects data flow design
- Performance bottleneck is architectural (not implementation-level)

## Methodology

### 1. Read Architecture and Interfaces
Load design outputs. Identify components, boundaries, and data flows.

### 2. Failure Mode Analysis (FMEA)
For each component: Failure Mode, Severity (1-5), Likelihood (1-5), Detection (1-5), RPN = S×L×D.
CC boundary risks: hooks timeout, description truncation (1024-char limit), agent context isolation, tool unavailability, compaction-induced data loss.

For STANDARD/COMPLEX, delegate to analysts.

> DPS construction guide: read `.claude/resources/dps-construction-guide.md`
> FMEA calibration, common .claude/ INFRA failure modes, DPS details: read `resources/methodology.md`

### 3. Security Assessment
Check OWASP: input validation (command injection, path traversal), access control, data exposure.

> Agent Teams security threat model: read `resources/methodology.md`

### 4. Performance Analysis
Bottlenecks: context window consumption (large reads, verbose output), agent spawn overhead, API rate limits.

### 5. Propose Mitigations
For each high-RPN risk: mitigation strategy, detection mechanism, fallback plan.

> Mitigation categories and completeness checklist: read `resources/methodology.md`

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Analyst tool error, timeout | L0 Retry | Re-invoke same analyst, same DPS |
| RPN scoring inconsistency or superficial analysis | L1 Nudge | Respawn with refined DPS targeting calibration guide and re-scoring request |
| Analyst exhausted turns | L2 Respawn | Kill → fresh analyst focused on critical-path components only |
| Critical security finding requiring architecture restructure | L3 Restructure | Route to design-architecture with vulnerability details |
| Unmitigable architectural risk after L0-L3 | L4 Escalate | AskUserQuestion: risk summary + redesign vs accept options |

> Escalation ladder details: read `.claude/resources/failure-escalation-ladder.md`
> Edge case handling: read `resources/methodology.md`

## Anti-Patterns

- **Score everything medium**: Inflation/deflation makes analysis useless. Use calibration guide for differentiated scoring.
- **Skip security**: Even for .claude/ INFRA. Scope escape, credential exposure, hook manipulation are real threats.
- **Unmaterializable mitigations**: "Manual testing" is invalid. Every mitigation must be a pipeline-implementable step (test, verification, checkpoint, rollback).
- **Risk without interfaces**: Most effective after design-interface. Without interfaces, integration risks and data flow vulnerabilities cannot be assessed.
- **Design risk vs implementation risk**: "Code might have bugs" = implementation risk (execution-review handles this). Design risk = structural issues, missing error contracts, architectural bottlenecks.
- **Ignore low-RPN risks**: Document them. Conditions change — "rare" becomes "likely" in different contexts.

## Transitions

### Receives From
| Source | Data | Format |
|--------|------|--------|
| design-architecture | Component structure, ADRs | L1: `components[]`, L2: ADRs with design rationale |
| design-interface | Interface contracts, integration points | L1: `interfaces[]`, L2: contract specifications |

### Sends To
| Target | Data | Trigger |
|--------|------|---------|
| research-codebase | Risk areas needing codebase validation | Always |
| research-external | Risk areas for community pattern validation | P2 Wave 1 |

> D17 Note: P0-P1 local mode — Lead reads via TaskOutput. 2-channel protocol applies P2+ only.
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

## Quality Gate
- Every component has ≥1 failure mode analyzed
- Top 3 RPN risks have documented mitigations
- Security assessment covers all external data flows
- No unmitigated critical (Severity=5) risks

## Output

### L1
```yaml
domain: design
skill: risk
risk_count: 0
critical_risks: 0
mitigated: 0
risks:
  - id: ""
    component: ""
    severity: 0
    likelihood: 0
    rpn: 0
    mitigation: ""
```

### L2
- Risk matrix with RPN rankings
- Security assessment summary
- Mitigation strategies for top risks
