# Coordinator Optimization Targets (Detailed)

## Target 1: Template Unification (CRITICAL)

**Problem:** Two distinct templates exist — Template A (verbose, 5 coordinators) and Template B (lean, 3 coordinators). This creates inconsistency and maintenance burden.

**Template A (verbose):** research, verification, execution, testing, infra-quality
- 80-125 body lines
- Inlines content from coordinator-shared-protocol.md
- Does NOT reference coordinator-shared-protocol.md
- Has color/memory frontmatter

**Template B (lean):** architecture, planning, validation
- 39 body lines
- Delegates to coordinator-shared-protocol.md via reference
- References BOTH shared protocols
- Missing color/memory frontmatter

**Recommendation:** Converge to a hybrid approach:
- All 8 should reference coordinator-shared-protocol.md (eliminate inlined duplication)
- All 8 should have full frontmatter fields (color, memory, disallowedTools)
- Each should retain only role-specific unique logic in body
- Estimated reduction: Template A coordinators lose ~35L of boilerplate each → ~175L total savings

## Target 2: Missing `memory:` Field (HIGH)

**Problem:** 3/8 coordinators (architecture, planning, validation) lack `memory:` field.

**Current state:**
- 5/8 use `memory: user` — persists across all projects
- 3/8 have no memory configured

**Recommendation:**
- Add `memory: project` to all 8 for cross-session learning within the same project
- Consider `project` vs `user` scope — coordinators learn patterns specific to a project (file structures, naming conventions), so `project` may be more appropriate than `user`

## Target 3: Missing `color:` Field (MEDIUM)

**Problem:** 3/8 coordinators (architecture, planning, validation) lack `color:` field.

**Current colors in use:**
- research: cyan
- verification: yellow
- execution: green
- testing: magenta
- infra-quality: white

**Recommendation:** Assign colors to remaining 3:
- architecture: blue (design/structural connotation)
- planning: orange (planning/scheduling connotation)
- validation: red (challenge/validation connotation)

## Target 4: Incomplete `disallowedTools:` (HIGH)

**Problem:** 3/8 coordinators (architecture, planning, validation) only block TaskCreate + TaskUpdate. They do NOT block Edit or Bash.

**Risk:** These coordinators could accidentally modify code or run shell commands, violating the "coordinators write L1/L2/L3 only" principle.

**Recommendation:** Add Edit + Bash to disallowedTools for all 3:
```yaml
disallowedTools:
  - TaskCreate
  - TaskUpdate
  - Edit
  - Bash
```

## Target 5: Missing `skills:` Preload (HIGH)

**Problem:** 0/8 coordinators have skills preloaded.

**Analysis of candidates:**
| Coordinator | Candidate Skill | Benefit | Risk |
|-------------|----------------|---------|------|
| research | `/brainstorming-pipeline` | Knows P1-3 flow | Token cost, coordinator doesn't run skills |
| planning | `/agent-teams-write-plan` | Knows P4 expectations | Token cost |
| validation | `/plan-validation-pipeline` | Knows P5 flow | Token cost |
| execution | `/agent-teams-execution-plan` | Knows P6 protocol | Token cost |
| testing | `/verification-pipeline` | Knows P7-8 flow | Token cost |

**Key consideration:** Coordinators DON'T execute skills — Lead does. But preloading the skill for their phase gives coordinators context about what Lead expects, enabling better coordination.

**Recommendation:** This is a DESIGN DECISION, not a clear gap. The benefit (better phase-awareness) must be weighed against the token cost (skills are 400-600L each). May be better addressed through Dynamic Context Injection by Lead at spawn time.

## Target 6: Missing Agent-Scoped `hooks:` (LOW-MEDIUM)

**Problem:** 0/8 coordinators have agent-scoped hooks.

**Potential hooks:**
- Auto-write progress-state.yaml after each SendMessage (enforces coordinator-shared-protocol §7)
- L1 auto-update trigger (enforces incremental L1 writing)

**Recommendation:** Evaluate after CC hook capabilities are better understood. The constraint exists in body text already — hooks would enforce it mechanically.

## Target 7: Missing `coordinator-shared-protocol.md` Reference (HIGH)

**Problem:** 5/8 coordinators don't reference coordinator-shared-protocol.md (Template A group).

**Impact:** These coordinators may not follow coordinator-specific procedures (sub-gate protocol, progress-state.yaml, handoff protocol, error escalation matrix) unless the content is inlined — which it partially is but inconsistently.

**Recommendation:** All 8 MUST reference coordinator-shared-protocol.md. Remove inlined duplicates.

## Target 8: Timeout Threshold Inconsistency (LOW)

**Problem:** Different timeout thresholds across coordinators:
- research: 20/30 min
- verification: 15/25 min
- execution: 30/40 min
- testing: 20/30 min
- infra-quality: 15/25 min
- architecture, planning, validation: no timeouts specified (delegate to shared protocol defaults)

**Recommendation:** Either standardize in coordinator-shared-protocol.md (configurable per-coordinator, with defaults) or document the variance rationale explicitly.

## Target 9: `maxTurns` Adequacy (LOW)

**Current allocation:**
- 40: verification, architecture, planning, validation, infra-quality
- 50: research, testing
- 80: execution

**Assessment:** Execution at 80 is justified (two-stage review + fix loops can consume many turns). Research/testing at 50 are justified (parallel worker management). The 40-turn coordinators handle 3 workers each with limited fix loop complexity.

**Recommendation:** No change needed. Current values appear adequate.

## Priority Summary

| # | Target | Priority | Effort | Impact |
|---|--------|----------|--------|--------|
| 1 | Template Unification | CRITICAL | HIGH | ~175L reduction, consistency |
| 7 | Add coordinator-shared-protocol ref | HIGH | LOW | Protocol compliance |
| 4 | Complete disallowedTools | HIGH | LOW | Safety enforcement |
| 2 | Add memory: field | HIGH | LOW | Cross-session learning |
| 5 | Skills preload evaluation | HIGH | MEDIUM | Phase awareness (design decision) |
| 3 | Add color: field | MEDIUM | LOW | UI consistency |
| 6 | Agent-scoped hooks | LOW-MEDIUM | MEDIUM | Mechanical enforcement |
| 8 | Timeout standardization | LOW | LOW | Consistency |
| 9 | maxTurns review | LOW | LOW | N/A (adequate) |
