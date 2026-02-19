# plan-impact — Detailed Methodology Reference

Supplementary detail for SKILL.md. Loaded on invocation when deep methodology is needed.

---

## 1. Depth Calculation Steps (Propagation Path Analysis)

Load the audit-impact L3 file path provided via `$ARGUMENTS`. This file contains:
- Change propagation paths (which files are affected when file X changes)
- Impact classification: DIRECT (1-hop import/reference) vs TRANSITIVE (2+ hops)
- Propagation risk scores per path (likelihood of cascading failure)
- Blast radius estimates per change point

Validate the input exists and contains propagation data. If absent, route to Failure Handling (Missing Audit Input).

**Depth score per task:**
1. Count DIRECT paths originating from the task (each = depth +1)
2. Count TRANSITIVE paths (each = depth +2, weighted higher for cascading risk)
3. Assign blast radius: LOW (<2 DIRECT), MEDIUM (2-4 DIRECT or 1 TRANSITIVE), HIGH (5+ DIRECT or 2+ TRANSITIVE)
4. Flag circular propagation (bidirectional paths between tasks)

---

## 2. Wave Construction Format

**Group formation algorithm:**
1. Identify tasks with zero incoming propagation (root changes) — these form Wave 1
2. For remaining tasks, identify those whose ALL propagation sources are in completed waves
3. Group eligible tasks into the next wave (max 4 per wave)
4. Repeat until all tasks are assigned to a wave

**Propagation-safe parallelism check:**
| Condition | Parallel Safe? | Reason |
|-----------|----------------|--------|
| No propagation path between tasks | Yes | Independent changes |
| DIRECT propagation, same direction | No | Must sequence producer -> consumer |
| TRANSITIVE propagation only | Conditional | Safe if intermediate is stable |
| Bidirectional propagation | No | Must merge into same wave or sequence |

**Wave output format:**
```
Wave {N}:
  Tasks: [{task-id}, ...]        # max 4
  Parallel: true|false
  Propagation risk: low|medium|high
  Checkpoint after: true|false
```

---

## 3. Checkpoint Schedule Format

**Checkpoint protocol:**
```
Checkpoint CP-{N} (after Wave {M}):
  Verify: All Wave {M} changes are stable (no test failures, no unexpected side effects)
  Gate: Propagation targets of Wave {M} changes are unaffected OR expected
  On pass: Release Wave {M+1}
  On fail: Rollback Wave {M}, assess propagation damage
  Timeout: 5 minutes
```

**Checkpoint placement rules:**
- ALWAYS insert checkpoint after a wave containing high-risk propagation sources
- ALWAYS insert checkpoint before a wave that depends on multiple prior waves
- OPTIONAL checkpoint between low-risk sequential waves (speed vs safety tradeoff)

**Checkpoint density by tier:**
| Tier | Checkpoint Frequency | Rationale |
|------|---------------------|-----------|
| TRIVIAL | After final wave only | Low propagation risk |
| STANDARD | After waves with DIRECT propagation | Moderate containment |
| COMPLEX | After every wave with high-risk sources | Maximum containment |

---

## 4. DPS Templates

### TRIVIAL
Lead-direct. Linear sequence (1-2 groups). No propagation risk. Single final checkpoint only. Output inline (no file write required unless PT signal needed).

### STANDARD
Spawn analyst (maxTurns: 15). Systematic grouping across 3-8 tasks. Checkpoints after DIRECT propagation waves only. Skip efficiency metric if ≤ 3 waves.

### COMPLEX — Analyst Spawn Template
- **Context** (D11 priority: cognitive focus > token efficiency):
  INCLUDE:
    - research-coordinator audit-impact L3 from `tasks/{team}/p2-coordinator-audit-impact.md`
    - Pipeline tier and iteration count from PT
    - Task list from plan-static if available (for wave alignment)
  EXCLUDE:
    - Other plan dimension outputs (unless direct dependency for wave grouping)
    - Full research evidence detail (use L3 summaries only)
    - Pre-design and design conversation history
  Budget: Context field ≤ 30% of teammate effective context
- **Task**: "Group tasks into parallel execution waves (max 4 per wave) based on propagation containment. Insert checkpoints between waves with gate conditions. Define containment strategy per propagation path (isolation/ordered/blast-limit/rollback). Calculate parallel efficiency metric."
- **Constraints**: analyst agent. Read-only (Glob/Grep/Read only). No file modifications. maxTurns: 20. Focus on sequencing and containment, not teammate assignment.
- **Expected Output**: L1 YAML with wave_count, checkpoint_count, parallel_efficiency, groups[] and checkpoints[]. L2 sequencing rationale with containment strategy per path.
- **Delivery (Four-Channel)**:
  - Ch2: Write full result to `tasks/{team}/p3-plan-impact.md`
  - Ch3 micro-signal to Lead: `PASS|groups:{N}|checkpoints:{N}|ref:tasks/{team}/p3-plan-impact.md`
  - Ch4 P2P to plan-verify-impact teammate (Deferred Spawn — Lead spawns verifier after all 4 plan dimensions complete): signal sent only if verifier is already active
