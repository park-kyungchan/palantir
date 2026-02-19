# Design Risk — Detailed Methodology

> On-demand reference. Contains FMEA scoring calibration, common failure modes, security threat model, and mitigation strategies.

## FMEA Scoring Calibration

**Severity (S):**
| Score | Impact | Example |
|-------|--------|---------|
| 1 | Cosmetic | Formatting issue |
| 2 | Minor degradation | Verbose output |
| 3 | Significant (recoverable) | Wrong file modified |
| 4 | Major failure | Agent produces incorrect code |
| 5 | Pipeline-blocking | Entire pipeline halts |

**Likelihood (L):**
| Score | Probability | Example |
|-------|------------|---------|
| 1 | Rare (<5%) | CC platform bug |
| 2 | Unlikely (5-20%) | Regex edge case |
| 3 | Possible (20-50%) | Unexpected API response |
| 4 | Likely (50-80%) | File exceeds context |
| 5 | Certain (>80%) | Known limitation |

**Detection (D):**
| Score | Detectability | Example |
|-------|--------------|---------|
| 1 | Obvious | Build fails immediately |
| 2 | Easy | Test suite catches |
| 3 | Moderate | Review catches |
| 4 | Hard | Only in production |
| 5 | Hidden | Silent corruption |

## Common .claude/ INFRA Failure Modes
| Component | Failure | Typical RPN |
|-----------|---------|-------------|
| Skill description | Exceeds 1024 chars | S3×L3×D2=18 |
| Hook script | Shell syntax error | S4×L2×D1=8 |
| Agent definition | Wrong model | S3×L2×D2=12 |
| Settings.json | Invalid JSON | S5×L2×D1=10 |
| CLAUDE.md | Count mismatch | S2×L3×D3=18 |
| Frontmatter | Non-native field | S3×L2×D2=12 |

## Security Threat Model for Agent Teams
| Threat | Vector | Mitigation |
|--------|--------|------------|
| Scope escape | Agent modifies outside assignment | File ownership in DPS |
| Tool over-provisioning | Agent has wrong tools | Profile-based restriction |
| Context injection | Untrusted data in prompt | Sanitize input before DPS |
| Hook manipulation | Agent modifies hook script | Hooks in protected .claude/ |
| Credential exposure | Keys in file content | Never secrets in tracked files |
| Permission escalation | Sub-agent with elevated perms | CC prevents this |

## DPS for Risk Analysts
- **Context**: Design-architecture L1 (components) + design-interface L1 (interfaces). Environment: "CC CLI on WSL2, tmux Agent Teams, Opus 4.6."
- **Task**: "FMEA per component. Score S/L/D (1-5). Security (OWASP) + performance analysis."
- **Scope**: COMPLEX → analyst-1=failure modes, analyst-2=security+performance.
- **Constraints**: Read-only. Sequential-thinking for calibrated scoring. maxTurns: 20.
- **Delivery**: Lead reads via TaskOutput (P0-P1).

## Mitigation Strategy Categories
| Category | When | Example |
|----------|------|---------|
| Prevention | Risk eliminable | Input validation |
| Detection | Can't prevent, can catch | Tests, verify stages |
| Recovery | May occur, handle it | Rollback, retry |
| Acceptance | Low-impact, unlikely | Document and monitor |
| Transfer | Belongs elsewhere | Security review |

## Mitigation Completeness Checklist
- [ ] Prevention mechanism (or documented as not feasible)
- [ ] Detection mechanism
- [ ] Recovery plan
- [ ] Responsibility assigned (skill/phase)
- [ ] Checkpoint defined (pipeline location)

## Failure Protocols
**Architecture insufficient**: Route to design-architecture with specific questions.
**Scoring inconsistency**: Lead normalizes using calibration guide (±1 level with rationale).
**No risks found (suspicious)**: TRIVIAL acceptable. STANDARD/COMPLEX: re-run adversarial. Heuristic: >3 components → ≥1 risk with RPN >10.
**Critical security finding**: Immediate FAIL → design-architecture redesign. Never accept as "known risk."
**Analyst exhausted**: Report partial FMEA. Focus on critical-path components.
