---
name: design-risk
description: |
  [P2·Design·Risk] Failure mode and mitigation strategy analyst. Examines architecture and interfaces for potential failure points, security implications, performance bottlenecks, and proposes mitigation strategies with priority ranking.

  WHEN: After design-architecture and design-interface complete. Architecture and interfaces exist but risk unassessed.
  DOMAIN: design (skill 3 of 3). Terminal skill in design domain. Runs after architecture and interface.
  INPUT_FROM: design-architecture (component structure), design-interface (API contracts).
  OUTPUT_TO: research domain (risk areas needing codebase validation), plan-strategy (risk mitigation for implementation strategy).

  METHODOLOGY: (1) Read architecture and interface specs, (2) Identify failure modes per component (FMEA approach), (3) Assess security implications (OWASP categories), (4) Identify performance bottlenecks and scalability limits, (5) Propose mitigation strategy for each risk with priority ranking.
  MAX_TEAMMATES: 4.
  OUTPUT_FORMAT: L1 YAML risk matrix (risk ID, severity, likelihood, mitigation), L2 markdown risk assessment narrative, L3 detailed FMEA tables.
user-invocable: true
disable-model-invocation: false
---

# Design — Risk

## Output

### L1
```yaml
domain: design
skill: risk
risk_count: 0
critical: 0
high: 0
medium: 0
low: 0
risks:
  - id: ""
    severity: critical|high|medium|low
    likelihood: high|medium|low
    mitigation: ""
```

### L2
- Risk matrix with severity and likelihood
- Mitigation strategies per risk
- FMEA analysis for critical risks
