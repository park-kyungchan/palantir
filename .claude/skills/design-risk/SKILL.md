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
  and research-external.
user-invocable: true
disable-model-invocation: false
allowed-tools: "Read Glob Grep Write"
metadata:
  category: design
  tags: [risk-assessment, fmea, security-analysis]
  version: 2.0.0
---

# Design — Risk

## Execution Model
- **TRIVIAL**: Lead-direct. Quick risk scan, 2-3 top risks identified.
- **STANDARD**: Launch analyst (run_in_background). Systematic FMEA per component.
- **COMPLEX**: Launch 2-4 background agents (run_in_background). Divide: security vs performance vs reliability.

## Decision Points

### Tier Assessment for Risk Analysis
- **TRIVIAL**: 1-2 components, no external dependencies, no data mutations. Lead identifies top 2-3 risks directly. No analyst spawn.
- **STANDARD**: 3-5 components with moderate complexity. Launch 1 analyst for systematic FMEA with calibrated scoring.
- **COMPLEX**: 6+ components, external integrations, data mutations, security-sensitive operations. Launch 2-4 background analysts: separate FMEA, security, and performance concerns.

### Risk Analysis Depth Selection
- **Quick scan** (TRIVIAL): Identify top risks by intuition. No formal FMEA table. Suitable when architecture is straightforward.
- **Standard FMEA** (STANDARD): Full FMEA table per component with calibrated RPN scoring. Cover failure modes, security, and performance.
- **Deep analysis** (COMPLEX): Full FMEA + OWASP security assessment + performance modeling + failure propagation analysis. Each concern gets a dedicated analyst.

### RPN Threshold for Mitigation
Not all risks need mitigation plans:
- **RPN >= 50**: Critical -- mandatory mitigation, checkpoint in execution plan
- **RPN 25-49**: High -- mitigation recommended, documented in plan-strategy
- **RPN 10-24**: Medium -- acknowledged, monitored during execution
- **RPN < 10**: Low -- documented for awareness only

### P0-P1 Execution Context
This skill runs in P0-P1:
- TRIVIAL/STANDARD: Lead with local agents (run_in_background), no Team infrastructure
- COMPLEX: Team infrastructure available (TeamCreate, TaskCreate/Update, SendMessage)
- Can run in parallel with design-interface (both depend on design-architecture)

### When to Escalate to Architecture Revision
Risk analysis may uncover fundamental architectural issues:
- **Single component has RPN >= 100**: Architecture likely flawed -- route back to design-architecture
- **3+ components share same high-RPN failure mode**: Systemic issue -- architecture restructuring needed
- **Security finding affects data flow design**: Requires design-architecture revision before proceeding
- **Performance bottleneck is architectural** (not implementation-level): Can't be mitigated at execution time

## Methodology

### 1. Read Architecture and Interfaces
Load design outputs. Identify components, boundaries, and data flows.

### 2. Failure Mode Analysis (FMEA)
For each component, identify failure modes. Include CC boundary risks such as hooks timeout, description truncation (1024-char limit), agent context isolation failures, tool unavailability per agent type, and compaction-induced data loss:

| Component | Failure Mode | Severity (1-5) | Likelihood (1-5) | Detection (1-5) | RPN |
|-----------|-------------|-----------------|-------------------|------------------|-----|
| {name} | {what fails} | {impact} | {probability} | {detectability} | S×L×D |

RPN (Risk Priority Number) = Severity × Likelihood × Detection.
Focus mitigation on highest RPN items.

For STANDARD/COMPLEX tiers, construct the delegation prompt for each analyst with:
- **Context**: Paste design-architecture L1 (components) and design-interface L1 (interfaces). Include environment context: "Claude Code CLI on WSL2, tmux Agent Teams, Opus 4.6."
- **Task**: "FMEA per component: identify failure modes, score Severity/Likelihood/Detection (1-5 each), calculate RPN. FMEA Calibration: Severity: 1=cosmetic, 2=minor, 3=significant, 4=major, 5=pipeline-blocking. Likelihood: 1=rare, 2=unlikely, 3=possible, 4=likely, 5=certain. Detection: 1=obvious, 2=easy, 3=moderate, 4=hard, 5=hidden. Then security (OWASP) and performance analysis."
- **Scope**: For COMPLEX, split: analyst-1=failure modes+FMEA, analyst-2=security+performance.
- **Constraints**: Read-only analyst. Use sequential-thinking for calibrated scoring. No file modifications. maxTurns: 20.
- **Expected Output**: L1 YAML risk matrix with risk_count, critical_risks, risks[] (id, component, severity, likelihood, rpn, mitigation). L2 FMEA tables, security assessment, mitigations.
- **Delivery**: Lead reads output directly via TaskOutput (P0-P1 local mode, no SendMessage).

#### FMEA Scoring Calibration Guide
Use consistent scoring across all components:

**Severity (S):**
| Score | Pipeline Impact | Example |
|-------|----------------|---------|
| 1 | Cosmetic only | Formatting issue in output |
| 2 | Minor degradation | Slightly verbose output |
| 3 | Significant impact | Wrong file modified (recoverable) |
| 4 | Major failure | Agent produces incorrect code |
| 5 | Pipeline-blocking | Entire pipeline halts, no recovery |

**Likelihood (L):**
| Score | Probability | Example |
|-------|------------|---------|
| 1 | Rare (<5%) | CC platform bug |
| 2 | Unlikely (5-20%) | Complex regex fails on edge case |
| 3 | Possible (20-50%) | External API returns unexpected format |
| 4 | Likely (50-80%) | Large file exceeds context window |
| 5 | Certain (>80%) | Known limitation, always triggers |

**Detection (D):**
| Score | Detectability | Example |
|-------|--------------|---------|
| 1 | Obvious | Build fails immediately |
| 2 | Easy | Test suite catches it |
| 3 | Moderate | Review catches it |
| 4 | Hard | Only detected in production use |
| 5 | Hidden | Silent corruption, never caught |

#### Common Failure Modes for .claude/ INFRA
| Component Type | Common Failure | Typical RPN |
|---------------|---------------|-------------|
| Skill description | Exceeds 1024 chars (truncated) | S3xL3xD2 = 18 |
| Hook script | Shell syntax error | S4xL2xD1 = 8 |
| Agent definition | Wrong model specified | S3xL2xD2 = 12 |
| Settings.json | Invalid JSON | S5xL2xD1 = 10 |
| CLAUDE.md | Count mismatch with actual files | S2xL3xD3 = 18 |
| Frontmatter | Non-native field used | S3xL2xD2 = 12 |

### 3. Security Assessment
Check against relevant OWASP categories:
- Input validation (command injection, path traversal)
- Access control (agent tool restrictions, file permissions)
- Data exposure (sensitive files in commits, .env leaks)

#### Security Threat Model for Agent Teams
| Threat | Attack Vector | Mitigation |
|--------|-------------|------------|
| Agent scope escape | Agent modifies files outside assignment | File ownership enforcement in DPS |
| Tool over-provisioning | Agent has tools it shouldn't | Profile-based tool restriction |
| Context injection | Untrusted data in agent prompt | Sanitize all user input before DPS |
| Hook manipulation | Hook script modified by agent | Hooks in protected .claude/ scope |
| Credential exposure | API keys in file content/commits | Never include secrets in tracked files |
| Permission escalation | Agent spawns sub-agent with elevated perms | CC prevents sub-agent spawning |

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

#### Mitigation Strategy Categories
| Category | When to Use | Example |
|----------|-----------|---------|
| Prevention | Risk can be eliminated | Input validation, type checking |
| Detection | Risk cannot be prevented but can be caught | Tests, review stages, verify domain |
| Recovery | Risk may occur, need to handle it | Rollback strategy, retry mechanism |
| Acceptance | Risk is low-impact and unlikely | Document and monitor |
| Transfer | Risk belongs to another domain | Route to security review, external audit |

#### Mitigation Completeness Check
For each high-RPN risk, verify:
- [ ] Prevention mechanism exists (or documented as not feasible)
- [ ] Detection mechanism exists (how will we know if it happens?)
- [ ] Recovery plan exists (what do we do when it happens?)
- [ ] Responsibility assigned (which skill/phase handles it?)
- [ ] Checkpoint defined (where in pipeline do we check?)

## Failure Handling

### Architecture Output Insufficient for Risk Analysis
- **Cause**: design-architecture didn't define components in enough detail
- **Action**: Route back to design-architecture with specific questions about component interactions and data flows
- **Risk**: Proceeding with incomplete architecture produces incomplete risk assessment

### Analyst RPN Scoring Inconsistency
- **Cause**: Multiple COMPLEX-tier analysts use different severity calibration
- **Action**: Lead normalizes scores using the calibration guide. Adjust individual scores +/-1 level with documented rationale.
- **Prevention**: Include calibration guide in every analyst DPS prompt

### No Mitigable Risks Found (Suspicious Result)
- **Cause**: Either the architecture is genuinely simple OR the analysis was superficial
- **Action**: If TRIVIAL tier: acceptable. If STANDARD/COMPLEX: re-run with more adversarial prompt ("What could go WRONG?")
- **Heuristic**: Every system with >3 components has at least 1 risk with RPN > 10

### Critical Security Finding
- **Cause**: Security assessment found a design-level vulnerability
- **Action**: Immediate FAIL. Route to design-architecture for secure redesign. Include specific vulnerability details.
- **Never accept**: security findings as "known risk" without architectural mitigation

### Analyst Exhausted Turns
- **Cause**: Too many components for thorough FMEA in allocated turns
- **Action**: Report partial FMEA. Set `status: partial`. Focus completed analysis on critical-path components.
- **Routing**: plan-strategy can use partial risk data (better than none)

## Anti-Patterns

### DO NOT: Score All Risks as Medium
Risk inflation (everything is critical) or deflation (everything is low) makes the analysis useless. Use the calibration guide for consistent, differentiated scoring.

### DO NOT: Skip Security Assessment
Even for internal tools and .claude/ INFRA changes, security matters. Agent scope escape, credential exposure, and hook manipulation are real threats.

### DO NOT: Propose Mitigations That Don't Exist in the Pipeline
Mitigations like "manual testing" don't work in automated pipelines. Every mitigation must be implementable: a verification step, a test, a rollback, or a checkpoint.

### DO NOT: Assess Risk Without Interfaces
Risk analysis is most effective AFTER interface design. Without interfaces, you can't assess integration risks, data flow vulnerabilities, or contract violations.

### DO NOT: Conflate Implementation Risk with Design Risk
"The code might have bugs" is an implementation risk (handled by execution-review). Design risk is about structural issues: wrong component boundaries, missing error contracts, architectural bottlenecks.

### DO NOT: Ignore Low-RPN Risks Completely
Low-RPN risks should still be documented. Conditions change -- a "rare" risk may become "likely" in a different context. The risk matrix is a living document.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| design-architecture | Component structure with module boundaries | L1 YAML: `components[]`, L2: ADRs with design rationale |
| design-interface | Interface contracts and integration points | L1 YAML: `interfaces[]`, L2: contract specifications |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| research-codebase | Risk areas needing codebase validation | Always (risk informs research focus) |
| research-external | Risk areas for community pattern validation | After design phase complete (P2 Wave 1) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Architecture insufficient | design-architecture | Specific questions about components/data flow |
| Security finding | design-architecture | Vulnerability details + redesign recommendation |
| Partial analysis | plan-strategy (continue) | Completed risk data + unanalyzed component list |

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
