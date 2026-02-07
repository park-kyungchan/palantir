# Risk Matrix — DIA v4.0 Architecture

**Author:** architect-1 | **Date:** 2026-02-07

---

## Scoring

- **Likelihood:** 1 (Very Low) → 5 (Very High)
- **Impact:** 1 (Negligible) → 5 (Critical)
- **Risk Score:** Likelihood × Impact
- **Threshold:** Score ≥ 9 = mandatory mitigation, 6-8 = recommended, ≤ 5 = accepted

---

## Risk Register

### R-001: Edit Race Condition on TEAM-MEMORY.md
| Attribute | Value |
|-----------|-------|
| Component | Team Memory |
| Likelihood | 1 (Very Low) |
| Impact | 2 (Low — non-destructive failure, retry resolves) |
| Score | **2** (Accepted) |
| Description | Two teammates Edit TEAM-MEMORY.md simultaneously; one Edit fails due to old_string mismatch |
| Mitigation | Section header inclusion rule, IDLE-WAKE serialization, Edit is atomic and non-destructive |
| Residual Risk | Minimal — retry resolves within 1 second |

### R-002: Context Delta Version Gap Edge Case
| Attribute | Value |
|-----------|-------|
| Component | Context Delta |
| Likelihood | 2 (Low) |
| Impact | 3 (Medium — teammate works with stale context until detected) |
| Score | **6** (Recommended mitigation) |
| Description | Teammate misses delta due to compact recovery or rapid GC updates; version gap not detected immediately |
| Mitigation | 5-condition fallback tree (FC-1~FC-5), Gate blocks stale-context teammates, orchestration-plan.md version tracking |
| Residual Risk | Low — full fallback is comprehensive safety net |

### R-003: Hook Bypass via Minimal Valid Files
| Attribute | Value |
|-----------|-------|
| Component | Hook Enhancement |
| Likelihood | 1 (Very Low — teammate motivation to bypass is absent) |
| Impact | 2 (Low — caught by Lead's Gate review of L1/L2 content) |
| Score | **2** (Accepted) |
| Description | Teammate creates minimal L1/L2 files that pass hook's structural check but contain no meaningful content |
| Mitigation | Hook = Speed Bump (Layer 4); Lead Gate review = semantic check (Layer 2-3); minimum file size threshold |
| Residual Risk | Accepted — Speed Bump positioning acknowledged; LLM layers catch semantic issues |

### R-004: SubagentStart Team Directory Discovery Failure
| Attribute | Value |
|-----------|-------|
| Component | Hook Enhancement |
| Likelihood | 2 (Low) |
| Impact | 1 (Negligible — fallback is exit 0, no additionalContext) |
| Score | **2** (Accepted) |
| Description | Hook cannot find active team's global-context.md due to path convention change or multiple stale team dirs |
| Mitigation | Fallback to exit 0 (current behavior), one-team-per-session constraint (ISS-004), most-recent config.json selection |
| Residual Risk | Minimal — additionalContext is "nice to have", not enforcement |

### R-005: TEAM-MEMORY.md Size Bloat
| Attribute | Value |
|-----------|-------|
| Component | Team Memory |
| Likelihood | 3 (Medium — likely in long sessions with many teammates) |
| Impact | 2 (Low — performance impact, not data loss) |
| Score | **6** (Recommended mitigation) |
| Description | File exceeds 500 lines, making reads slow and sections hard to navigate |
| Mitigation | Lead curation at Gate time (ARCHIVED → deleted), 500-line trigger for cleanup, session-scoped lifecycle |
| Residual Risk | Moderate — depends on Lead's curation discipline |

### R-006: Lead Relay Bottleneck for Non-Edit Agents
| Attribute | Value |
|-----------|-------|
| Component | Team Memory |
| Likelihood | 3 (Medium — researcher/architect/tester generate many findings) |
| Impact | 2 (Low — delay in sharing, not data loss) |
| Score | **6** (Recommended mitigation) |
| Description | 4 out of 6 agent types can't directly Edit TEAM-MEMORY.md; Lead must relay, adding latency and context burden |
| Mitigation | Primary value is Phase 6 (implementers have Edit); other phases are typically sequential with single agents; Lead can batch relay at natural checkpoints |
| Residual Risk | Accepted — natural flow already routes through Lead; direct Edit is a bonus for implementer parallelism |

### R-007: Hook Timeout on Filesystem Scan
| Attribute | Value |
|-----------|-------|
| Component | Hook Enhancement |
| Likelihood | 1 (Very Low — team dirs are small) |
| Impact | 1 (Negligible — timeout = exit non-zero → non-blocking) |
| Score | **1** (Accepted) |
| Description | TeammateIdle or TaskCompleted hook exceeds 10-second timeout due to slow filesystem |
| Mitigation | Team directories are small (<100 files), direct path construction (not recursive find), timeout configured at 10s |
| Residual Risk | Minimal |

### R-008: Backward Compatibility — Sessions Without TEAM-MEMORY.md
| Attribute | Value |
|-----------|-------|
| Component | Team Memory |
| Likelihood | 3 (Medium — during migration period) |
| Impact | 1 (Negligible — read of non-existent file returns empty, not error) |
| Score | **3** (Accepted) |
| Description | Resumed or migrated sessions may not have TEAM-MEMORY.md; agents instructed to "read before work" encounter missing file |
| Mitigation | Agents handle missing file gracefully (Read tool returns error, agent continues); Lead creates on TeamCreate |
| Residual Risk | Minimal — agent instructions can include "if exists" qualifier |

### R-009: Delta Calculation Inaccuracy
| Attribute | Value |
|-----------|-------|
| Component | Context Delta |
| Likelihood | 2 (Low — Lead is aware of what was changed) |
| Impact | 3 (Medium — teammate gets partial/wrong context) |
| Score | **6** (Recommended mitigation) |
| Description | Lead's LLM-generated delta misses a changed field or incorrectly reports a change |
| Mitigation | Enhanced ACK with applied/total count enables detection; teammate can request full fallback (FC-5); Gate blocks stale context |
| Residual Risk | Low — ACK-based feedback loop catches most inaccuracies |

### R-010: TeammateIdle False Positive
| Attribute | Value |
|-----------|-------|
| Component | Hook Enhancement |
| Likelihood | 2 (Low) |
| Impact | 2 (Low — teammate receives feedback and can write L1/L2 then retry idle) |
| Score | **4** (Accepted) |
| Description | Hook blocks idle for a teammate who legitimately has no L1/L2 yet (e.g., just started, hasn't produced output) |
| Mitigation | Teammates should write L1/L2 proactively throughout execution (Pre-Compact Obligation); hook feedback message explains what's needed; teammate can write minimal L1/L2 and retry |
| Residual Risk | Low — Pre-Compact Obligation aligns with hook requirement |

---

## Risk Summary Matrix

| Score | Risk IDs | Count |
|-------|----------|-------|
| 1 (Accepted) | R-007 | 1 |
| 2 (Accepted) | R-001, R-003, R-004 | 3 |
| 3 (Accepted) | R-008 | 1 |
| 4 (Accepted) | R-010 | 1 |
| 6 (Recommended) | R-002, R-005, R-006, R-009 | 4 |
| ≥9 (Mandatory) | — | 0 |

**No mandatory-mitigation risks identified.** 4 risks at recommended level (score 6) all have defined mitigations with low residual risk.

---

## Heat Map

```
Impact →    1         2         3         4         5
Likelihood
    5      |         |         |         |         |
    4      |         |         |         |         |
    3      | R-008   | R-005   |         |         |
           |         | R-006   |         |         |
    2      | R-004   | R-010   | R-002   |         |
           |         |         | R-009   |         |
    1      | R-007   | R-001   |         |         |
           |         | R-003   |         |         |
```

All risks are in the **green zone** (bottom-left quadrant). No red (top-right) risks.
