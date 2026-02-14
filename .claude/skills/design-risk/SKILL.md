---
name: design-risk
description: |
  [P2·Design·Risk] Failure mode and mitigation strategy analyst. Examines architecture and interfaces for failure points, security issues, performance bottlenecks. Proposes mitigations with priority ranking.

  WHEN: After design-architecture and design-interface complete. Architecture and interfaces exist but risk unassessed.
  DOMAIN: design (skill 3 of 3). Terminal skill. Runs after architecture and interface.
  INPUT_FROM: design-architecture (component structure), design-interface (API contracts).
  OUTPUT_TO: research domain (risk areas for codebase validation), plan-strategy (risk mitigation for strategy).

  METHODOLOGY: (1) Read architecture and interface specs, (2) Identify failure modes per component (FMEA), (3) Assess security implications (OWASP), (4) Identify performance bottlenecks, (5) Propose mitigation per risk with priority ranking.
  OUTPUT_FORMAT: L1 YAML risk matrix (ID, severity, likelihood, mitigation), L2 markdown risk narrative, L3 FMEA tables.
user-invocable: true
disable-model-invocation: false
---

# Design — Risk

## Execution Model
- **TRIVIAL**: Lead-direct. Quick risk scan, 2-3 top risks identified.
- **STANDARD**: Spawn analyst. Systematic FMEA per component.
- **COMPLEX**: Spawn 2-4 analysts. Divide: security vs performance vs reliability.

## Methodology

### 1. Read Architecture and Interfaces
Load design outputs. Identify components, boundaries, and data flows.

### 2. Failure Mode Analysis (FMEA)
For each component, identify failure modes:

| Component | Failure Mode | Severity (1-5) | Likelihood (1-5) | Detection (1-5) | RPN |
|-----------|-------------|-----------------|-------------------|------------------|-----|
| {name} | {what fails} | {impact} | {probability} | {detectability} | S×L×D |

RPN (Risk Priority Number) = Severity × Likelihood × Detection.
Focus mitigation on highest RPN items.

### 3. Security Assessment
Check against relevant OWASP categories:
- Input validation (command injection, path traversal)
- Access control (agent tool restrictions, file permissions)
- Data exposure (sensitive files in commits, .env leaks)

### 4. Performance Analysis
Identify potential bottlenecks:
- Context window consumption (large file reads, verbose outputs)
- Agent spawn overhead (too many parallel agents)
- API rate limits (web search, MCP tool calls)

### 5. Propose Mitigations
For each high-RPN risk:
- **Mitigation strategy**: How to reduce severity/likelihood
- **Detection mechanism**: How to identify when risk materializes
- **Fallback plan**: What to do if mitigation fails

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
