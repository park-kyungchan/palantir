# Gate Evaluation Standard v1.0

> Referenced by: CLAUDE.md §2 (Pipeline), Skills (Phase 0 blocks), coordinator .md files
> Source Decisions: D-008 (Gate Evaluation Standardization)

## 1. Universal Gate Structure

Every gate evaluation produces a **Gate Record** with 5 elements:

```yaml
# gate-record.yaml
gate: G{N}           # G0=Phase0, G2=Research, G2b=Verification, G3=Architecture...
phase_from: P{N}
phase_to: P{N+1}
tier: TRIVIAL | STANDARD | COMPLEX
timestamp: {ISO 8601}

evidence:             # What was produced
  - artifact: "{filename}"
    type: L1 | L2 | L3 | reference | code
    location: "{path}"

checklist:            # What was verified
  - item: "{criterion}"
    status: PASS | FAIL | SKIP
    evidence_ref: "{filename:line or description}"

verdict: PASS | CONDITIONAL_PASS | FAIL
justification: "{1-3 sentences explaining verdict}"

downstream:           # What the next phase needs to know
  decisions_made: []
  risks_identified: []
  open_questions: []
```

## 2. Pipeline Tier → Gate Depth (D-001 Alignment)

| Tier | When | Gate Checklist Size | Evidence Required |
|------|------|:---:|---|
| **TRIVIAL** | ≤2 files, single module, no cross-boundary | 3 items | L1 only |
| **STANDARD** | 3-8 files, 1-2 modules, limited cross-boundary | 5 items | L1 + L2 |
| **COMPLEX** | >8 files, 3+ modules, cross-boundary impact | 7-10 items | L1 + L2 + L3 spot-check |

## 3. Per-Gate Checklists

### G0: Phase 0 (PT Validation)
| # | Criterion | TRIVIAL | STANDARD | COMPLEX |
|---|-----------|:---:|:---:|:---:|
| 1 | PT exists with User Intent | ✅ | ✅ | ✅ |
| 2 | Pipeline tier determined | ✅ | ✅ | ✅ |
| 3 | Codebase Impact Map populated | — | ✅ | ✅ |
| 4 | Architecture Decisions listed | — | — | ✅ |
| 5 | Risk Registry initialized | — | — | ✅ |

### G2: Research Gate
| # | Criterion | TRIVIAL | STANDARD | COMPLEX |
|---|-----------|:---:|:---:|:---:|
| 1 | Research scope covers PT requirements | ✅ | ✅ | ✅ |
| 2 | Evidence count > 0 in coordinator L1 | ✅ | ✅ | ✅ |
| 3 | All PT-referenced modules investigated | — | ✅ | ✅ |
| 4 | External sources consulted (if applicable) | — | ✅ | ✅ |
| 5 | Cross-module dependencies mapped | — | — | ✅ |
| 6 | Contradictions flagged (if any) | — | — | ✅ |
| 7 | Research gaps explicitly listed | — | — | ✅ |

### G2b: Verification Gate (CONDITIONAL — skip for TRIVIAL)
| # | Criterion | STANDARD | COMPLEX |
|---|-----------|:---:|:---:|
| 1 | All claims verified against source | ✅ | ✅ |
| 2 | Correction count documented | ✅ | ✅ |
| 3 | Cross-dimension synthesis complete | — | ✅ |
| 4 | Impact analysis of corrections done | — | ✅ |

### G3: Architecture Gate
| # | Criterion | TRIVIAL | STANDARD | COMPLEX |
|---|-----------|:---:|:---:|:---:|
| 1 | Design addresses PT requirements | ✅ | ✅ | ✅ |
| 2 | ADRs documented (if architectural) | — | ✅ | ✅ |
| 3 | Risk matrix populated | — | ✅ | ✅ |
| 4 | Component interfaces defined | — | — | ✅ |
| 5 | Alternative approaches considered | — | — | ✅ |

### G4: Design Gate
| # | Criterion | TRIVIAL | STANDARD | COMPLEX |
|---|-----------|:---:|:---:|:---:|
| 1 | File assignments non-overlapping | ✅ | ✅ | ✅ |
| 2 | Interface contracts specified | — | ✅ | ✅ |
| 3 | Task breakdown complete | — | ✅ | ✅ |
| 4 | Dependency ordering correct | — | — | ✅ |
| 5 | Integration strategy defined | — | — | ✅ |

### G5: Validation Gate (CONDITIONAL — skip for TRIVIAL)
| # | Criterion | STANDARD | COMPLEX |
|---|-----------|:---:|:---:|
| 1 | Devil's advocate review complete | ✅ | ✅ |
| 2 | Critical flaws addressed | ✅ | ✅ |
| 3 | Mitigations documented for each flaw | — | ✅ |
| 4 | Design revised if needed | — | ✅ |

### G6: Implementation Gate
| # | Criterion | TRIVIAL | STANDARD | COMPLEX |
|---|-----------|:---:|:---:|:---:|
| 1 | All files created/modified per plan | ✅ | ✅ | ✅ |
| 2 | Self-review by implementer | ✅ | ✅ | ✅ |
| 3 | Spec-review complete | — | ✅ | ✅ |
| 4 | Code-review complete | — | ✅ | ✅ |
| 5 | No cross-boundary violations | — | ✅ | ✅ |
| 6 | Fix loops resolved (max 3x) | — | — | ✅ |
| 7 | Drift check by execution-monitor | — | — | ✅ |

### G7: Testing Gate (CONDITIONAL — skip for TRIVIAL)
| # | Criterion | STANDARD | COMPLEX |
|---|-----------|:---:|:---:|
| 1 | Tests created for changed code | ✅ | ✅ |
| 2 | Tests pass | ✅ | ✅ |
| 3 | Coverage adequate for changed areas | — | ✅ |
| 4 | Integration tests pass | — | ✅ |

### G8: Integration Gate (CONDITIONAL — skip for TRIVIAL)
| # | Criterion | STANDARD | COMPLEX |
|---|-----------|:---:|:---:|
| 1 | Cross-boundary merge complete | ✅ | ✅ |
| 2 | No merge conflicts | ✅ | ✅ |
| 3 | Integration tests pass post-merge | — | ✅ |
| 4 | Regression check | — | ✅ |

## 4. Coordinator Sub-Gate Protocol

Before reporting completion to Lead, coordinators verify:
1. All workers reported complete (or explained why not)
2. Worker L1 files exist and contain mandatory keys
3. Worker L2 files contain required sections
4. Cross-worker synthesis is complete (no contradictions)
5. Consolidated L1/L2 written to coordinator output directory

## 5. Post-Skill Validation (D-007 BN-007)

After each Skill invocation, Lead checks:
1. **Output exists:** L2 file written (Glob check)
2. **L1 parseable:** L1-index.yaml has mandatory keys (agent, phase, status)
3. **Evidence count > 0:** L1.evidence_count present
4. **No BLOCKED status:** All workers complete or in_progress

Failure → Tier 2/3 escalation per error handling protocol.

## 6. Shift-Left Gate Distribution

| Phase Range | Effort % | Gate Rigor |
|------------|:---:|---|
| PRE (P0-P5) | 70-80% | Highest — catch issues before code |
| EXEC (P6-P8) | 15-20% | Medium — verify implementation matches design |
| POST (P9) | 5-10% | Low — delivery checklist |
